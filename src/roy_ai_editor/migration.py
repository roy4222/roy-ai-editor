"""Non-destructive Legacy Media Project migration."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
from pathlib import Path

from .deliverables import hash_file
from .project import STANDARD_PROJECT_DIRECTORIES, record_evidence, save_project

VIDEO_EXTENSIONS = {".mp4", ".mkv", ".mov", ".webm"}
SUBTITLE_EXTENSIONS = {".ass", ".srt", ".vtt"}


def _inventory(root: Path) -> list[dict]:
    files: list[dict] = []
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"legacy migration does not follow symlinks: {path}")
        if path.is_file():
            relative = path.relative_to(root)
            files.append({
                "path": relative.as_posix(),
                "class": relative.parts[0] if len(relative.parts) > 1 else "root",
                "size": path.stat().st_size,
                "mtime_ns": path.stat().st_mtime_ns,
                "sha256": hash_file(path),
            })
    return files


def _safe_relative(value: str, *, field: str) -> Path:
    path = Path(value)
    if path.is_absolute() or not value or any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError(f"{field} must be a clean relative path: {value!r}")
    return path


def _load_reconciliation(path: Path | None, destination: Path) -> tuple[dict | None, str | None]:
    if path is None:
        return None, None
    path = path.expanduser()
    if not path.is_file() or path.is_symlink():
        raise ValueError(f"reconciliation profile must be a regular file: {path}")
    path = path.resolve()
    raw = path.read_bytes()
    try:
        profile = json.loads(raw.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("reconciliation profile must be valid UTF-8 JSON") from error
    if profile.get("schema_version") != 1:
        raise ValueError("reconciliation profile schema_version must be 1")
    if profile.get("project_id") != destination.name:
        raise ValueError("reconciliation project_id must match destination directory")
    tracks = profile.get("tracks")
    if not isinstance(tracks, list) or not tracks:
        raise ValueError("reconciliation profile requires at least one track")
    track_ids = [item.get("track_id") for item in tracks]
    if len(set(track_ids)) != len(track_ids):
        raise ValueError("reconciliation track_id values must be unique")
    numbers = [item.get("number") for item in tracks]
    if any(not isinstance(number, int) or number < 1 for number in numbers) or len(set(numbers)) != len(numbers):
        raise ValueError("reconciliation track numbers must be unique positive integers")
    if any(not isinstance(track_id, str) or not re.fullmatch(r"\d{2,3}-[a-z0-9][a-z0-9-]*", track_id) for track_id in track_ids):
        raise ValueError("reconciliation track_id values must use stable numbered slugs")
    gates = profile.get("review_gates")
    required_gates = {"rights", "lyrics", "edit", "publish"}
    if not isinstance(gates, dict) or set(gates) != required_gates:
        raise ValueError("reconciliation review_gates must define rights, lyrics, edit, and publish")
    if any(status not in {"pending", "approved"} for status in gates.values()):
        raise ValueError("reconciliation review gates must be pending or approved")
    if profile.get("approved_deliverables"):
        raise ValueError("legacy approved deliverables require a dedicated explicit approval workflow")
    return profile, hashlib.sha256(raw).hexdigest()


def _route_destination(relative: Path, routes: list[dict]) -> Path:
    matches: list[tuple[int, Path]] = []
    for index, route in enumerate(routes):
        if not isinstance(route, dict):
            raise ValueError(f"reconciliation route {index} must be an object")
        source_prefix = _safe_relative(str(route.get("source_prefix", "")), field="source_prefix")
        destination_prefix = _safe_relative(str(route.get("destination_prefix", "")), field="destination_prefix")
        if relative == source_prefix or relative.is_relative_to(source_prefix):
            suffix = relative.relative_to(source_prefix)
            matches.append((len(source_prefix.parts), destination_prefix / suffix))
    if matches:
        matches.sort(key=lambda item: item[0], reverse=True)
        if len(matches) > 1 and matches[0][0] == matches[1][0]:
            raise ValueError(f"ambiguous reconciliation routes for {relative.as_posix()}")
        return matches[0][1]
    return _destination(relative)


def _destination(relative: Path) -> Path:
    if relative.suffix.lower() in VIDEO_EXTENSIONS:
        return Path("videos/archive") / relative
    if relative.suffix.lower() in SUBTITLE_EXTENSIONS:
        return Path("subtitles/archive") / relative
    return Path("work/legacy-import") / relative


def _validate_asset_destination(relative: Path) -> None:
    allowed_directories = [Path(directory) for directory in STANDARD_PROJECT_DIRECTORIES]
    if not any(relative != directory and relative.is_relative_to(directory) for directory in allowed_directories):
        raise ValueError(f"migration destination must be inside a standard asset directory: {relative}")
    if relative.as_posix() == "project.json" or (
        relative.parts[0] == "qa" and relative.name.startswith("legacy-migration-")
    ):
        raise ValueError(f"migration destination is reserved for generated control data: {relative}")


def _destination_state(destination: Path, expected: set[str]) -> tuple[str, list[str], dict | None]:
    if not destination.exists():
        return "absent", [], None
    manifest_path = destination / "project.json"
    manifest: dict | None = None
    conflicts: list[str] = []
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            conflicts.append("project.json is not valid UTF-8 JSON")
        else:
            if manifest.get("workflow") not in {"legacy-migration", "concert-live"} or (
                manifest.get("workflow") == "concert-live" and "migration" not in manifest
            ):
                conflicts.append("destination project.json belongs to another workflow")
            if manifest.get("project_id") not in {None, destination.name}:
                conflicts.append("destination project_id does not match its directory")

    for path in destination.rglob("*"):
        if path.is_symlink():
            conflicts.append(f"destination symlink is not allowed: {path.relative_to(destination).as_posix()}")
            continue
        if not path.is_file():
            continue
        relative = path.relative_to(destination).as_posix()
        internal = relative == "project.json" or relative.startswith("qa/legacy-migration-")
        if relative not in expected and not internal:
            conflicts.append(f"unknown destination file: {relative}")
    return ("conflict" if conflicts else "resumable"), conflicts, manifest


def _plan(before: list[dict], destination: Path, routes: list[dict] | None = None) -> list[dict]:
    actions: list[dict] = []
    seen_destinations: set[str] = set()
    for item in before:
        relative = _route_destination(Path(item["path"]), routes or []).as_posix()
        _validate_asset_destination(Path(relative))
        if relative in seen_destinations:
            raise ValueError(f"multiple legacy files map to the same destination: {relative}")
        seen_destinations.add(relative)
        destination_path = destination / relative
        if not destination_path.exists():
            action = "copy"
        elif destination_path.is_file() and hash_file(destination_path) == item["sha256"]:
            action = "skip"
        else:
            action = "conflict"
        actions.append({
            "source": item["path"],
            "destination": relative,
            "source_class": item["class"],
            "destination_class": "/".join(Path(relative).parts[:2]),
            "size": item["size"],
            "mtime_ns": item["mtime_ns"],
            "sha256": item["sha256"],
            "action": action,
        })
    return actions


def _validate_reconciliation_references(profile: dict, expected: set[str]) -> None:
    project_assets = profile.get("project_assets", {})
    if not isinstance(project_assets, dict):
        raise ValueError("project_assets must be an object")
    for kind, paths in project_assets.items():
        if not isinstance(paths, list) or not all(isinstance(path, str) for path in paths):
            raise ValueError(f"project asset list is invalid for {kind}")
        for path in paths:
            _safe_relative(path, field="project asset")
            if path not in expected:
                raise ValueError(f"project asset does not exist in migration plan: {path}")
    for track in profile["tracks"]:
        assets = track.get("legacy_assets", {})
        if not isinstance(assets, dict):
            raise ValueError(f"legacy_assets must be an object for {track['track_id']}")
        for kind, paths in assets.items():
            if not isinstance(paths, list) or not all(isinstance(path, str) for path in paths):
                raise ValueError(f"legacy asset list is invalid for {track['track_id']}:{kind}")
            for path in paths:
                _safe_relative(path, field="legacy asset")
                if path not in expected:
                    raise ValueError(f"legacy asset does not exist in migration plan: {path}")
    gate_evidence = profile.get("gate_evidence", {})
    if not isinstance(gate_evidence, dict):
        raise ValueError("gate_evidence must be an object")
    for gate, status in profile["review_gates"].items():
        evidence_paths = gate_evidence.get(gate, [])
        if status == "approved" and not evidence_paths:
            raise ValueError(f"approved {gate} gate requires explicit evidence")
        for path in evidence_paths:
            _safe_relative(path, field=f"{gate} gate evidence")
            if path not in expected:
                raise ValueError(f"approved {gate} gate evidence does not exist: {path}")


def _manifest_from_reconciliation(
    profile: dict,
    destination: Path,
    evidence: dict,
    existing_manifest: dict | None,
) -> dict:
    project_assets = {
        kind: [
            {
                "path": path,
                "size": (destination / path).stat().st_size,
                "sha256": hash_file(destination / path),
            }
            for path in paths
        ]
        for kind, paths in profile.get("project_assets", {}).items()
    }
    tracks: list[dict] = []
    artifact_refs: list[dict] = []
    for source_track in profile["tracks"]:
        track = {key: value for key, value in source_track.items() if key != "legacy_assets"}
        materialized_assets: dict[str, list[dict]] = {}
        for kind, paths in source_track.get("legacy_assets", {}).items():
            materialized_assets[kind] = [
                {
                    "path": path,
                    "size": (destination / path).stat().st_size,
                    "sha256": hash_file(destination / path),
                }
                for path in paths
            ]
        track["legacy_assets"] = materialized_assets
        tracks.append(track)

    gate_refs: dict[str, list[dict]] = {}
    for gate, paths in profile.get("gate_evidence", {}).items():
        gate_refs[gate] = []
        for path in paths:
            reference = {
                "id": f"legacy-{gate}-{hash_file(destination / path)[:16]}",
                "kind": f"legacy-{gate}-evidence",
                "path": path,
                "sha256": hash_file(destination / path),
            }
            gate_refs[gate].append(reference)
            artifact_refs.append(reference)

    manifest = existing_manifest or {}
    manifest.update({
        "schema_version": 2,
        "project_id": profile["project_id"],
        "workflow": "concert-live",
        "source_url": profile.get("source_url"),
        "stage": "migrated-pending-review",
        "status": "migrated-pending-review",
        "rights": profile.get("rights", {"status": "pending", "evidence": []}),
        "project_assets": project_assets,
        "tracks": sorted(tracks, key=lambda item: item["number"]),
        "approved_deliverables": [],
        "review_gates": profile["review_gates"],
        "gate_evidence": gate_refs,
        "unresolved_conflicts": profile.get("unresolved_conflicts", []),
        "migration_notes": profile.get("migration_notes", []),
    })
    prior = [
        item for item in manifest.get("evidence_artifacts", [])
        if item.get("id") not in {evidence["id"], *(item["id"] for item in artifact_refs)}
    ]
    manifest["evidence_artifacts"] = prior + artifact_refs + [evidence]
    return manifest


def migrate_legacy(
    source: Path,
    destination: Path,
    *,
    execute: bool,
    reconciliation: Path | None = None,
) -> dict:
    source = source.expanduser().resolve()
    destination = destination.expanduser().resolve()
    if not source.is_dir():
        raise FileNotFoundError(source)
    if destination == source or destination.is_relative_to(source):
        raise ValueError("destination cannot be inside legacy source")
    profile, profile_sha = _load_reconciliation(reconciliation, destination)
    before = _inventory(source)
    actions = _plan(before, destination, profile.get("routes", []) if profile else None)
    expected = {action["destination"] for action in actions}
    if profile:
        _validate_reconciliation_references(profile, expected)
    destination_state, destination_conflicts, existing_manifest = _destination_state(destination, expected)
    if existing_manifest:
        existing_migration = existing_manifest.get("migration", {})
        if existing_migration.get("source") not in {None, str(source)}:
            destination_conflicts.append("destination migration belongs to another legacy source")
        existing_profile_sha = existing_migration.get("reconciliation_profile_sha256")
        if profile_sha and existing_profile_sha not in {None, profile_sha}:
            destination_conflicts.append("destination migration used a different reconciliation profile")
        if destination_conflicts:
            destination_state = "conflict"
    summary = {name: sum(action["action"] == name for action in actions) for name in ("copy", "skip", "conflict")}
    plan = {
        "mode": "execute" if execute else "dry-run",
        "source_file_count": len(before),
        "source_total_size": sum(item["size"] for item in before),
        "destination_state": destination_state,
        "destination_conflicts": destination_conflicts,
        "summary": summary,
        "actions": actions,
    }
    if profile:
        plan["reconciliation"] = {
            "profile_sha256": profile_sha,
            "track_count": len(profile["tracks"]),
            "review_gates": profile["review_gates"],
        }
    if not execute:
        return plan
    if destination_state == "conflict" or summary["conflict"]:
        raise RuntimeError("migration conflicts require review before execution")

    for directory in STANDARD_PROJECT_DIRECTORIES:
        (destination / directory).mkdir(parents=True, exist_ok=True)
    for action in actions:
        source_path = source / action["source"]
        destination_path = destination / action["destination"]
        if action["action"] == "skip":
            continue
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, destination_path)
        if hash_file(destination_path) != action["sha256"]:
            raise RuntimeError(f"copy verification failed: {destination_path}")

    after = _inventory(source)
    source_unchanged = before == after
    if not source_unchanged:
        raise RuntimeError("legacy source changed during migration")
    for action in actions:
        if hash_file(destination / action["destination"]) != action["sha256"]:
            raise RuntimeError(f"destination verification failed: {action['destination']}")
    report = {
        **plan,
        "status": "verified",
        "source_unchanged": True,
        "legacy_boundary": "logical-read-only-candidate",
    }
    evidence = record_evidence(destination, "legacy-migration", report, directory="qa")
    inventory_sha = hashlib.sha256(
        json.dumps(before, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    if profile:
        manifest = _manifest_from_reconciliation(profile, destination, evidence, existing_manifest)
    else:
        manifest = existing_manifest or {
            "schema_version": 2,
            "project_id": destination.name,
            "workflow": "legacy-migration",
            "stage": "migrated-pending-review",
            "status": "migrated-pending-review",
            "tracks": [],
            "approved_deliverables": [],
            "evidence_artifacts": [],
            "review_gates": {"rights": "pending", "lyrics": "pending", "edit": "pending", "publish": "pending"},
        }
        manifest["evidence_artifacts"] = [
            item for item in manifest.get("evidence_artifacts", []) if item.get("id") != evidence["id"]
        ] + [evidence]
    manifest["migration"] = {
        "status": "verified",
        "report": evidence["path"],
        "source": str(source),
        "source_inventory_sha256": inventory_sha,
        "source_legacy_boundary": "logical-read-only-candidate",
    }
    if profile_sha:
        manifest["migration"]["reconciliation_profile_sha256"] = profile_sha
    save_project(destination, manifest)
    return report
