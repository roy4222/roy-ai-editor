"""Non-destructive Legacy Media Project migration."""

from __future__ import annotations

import hashlib
import json
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
            files.append({
                "path": path.relative_to(root).as_posix(),
                "size": path.stat().st_size,
                "sha256": hash_file(path),
            })
    return files


def _destination(relative: Path) -> Path:
    if relative.suffix.lower() in VIDEO_EXTENSIONS:
        return Path("videos/archive") / relative
    if relative.suffix.lower() in SUBTITLE_EXTENSIONS:
        return Path("subtitles/archive") / relative
    return Path("work/legacy-import") / relative


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
            if manifest.get("workflow") != "legacy-migration":
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


def _plan(before: list[dict], destination: Path) -> list[dict]:
    actions: list[dict] = []
    for item in before:
        relative = _destination(Path(item["path"])).as_posix()
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
            "size": item["size"],
            "sha256": item["sha256"],
            "action": action,
        })
    return actions


def migrate_legacy(source: Path, destination: Path, *, execute: bool) -> dict:
    source = source.expanduser().resolve()
    destination = destination.expanduser().resolve()
    if not source.is_dir():
        raise FileNotFoundError(source)
    if destination == source or destination.is_relative_to(source):
        raise ValueError("destination cannot be inside legacy source")
    before = _inventory(source)
    actions = _plan(before, destination)
    expected = {action["destination"] for action in actions}
    destination_state, destination_conflicts, existing_manifest = _destination_state(destination, expected)
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
    save_project(destination, manifest)
    return report
