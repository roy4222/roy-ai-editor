"""Independent verification for reconciled Legacy Media Projects."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from collections.abc import Callable, Iterable
from pathlib import Path

from .deliverables import hash_file
from .migration import SUBTITLE_EXTENSIONS, VIDEO_EXTENSIONS, _safe_relative
from .project import load_project, save_project, write_immutable_json

Probe = Callable[[Path], dict]
AUDIO_EXTENSIONS = {".aac", ".flac", ".m4a", ".mp3", ".ogg", ".opus", ".wav"}


def _contained(root: Path, value: str, *, field: str) -> Path:
    relative = _safe_relative(value, field=field)
    candidate = (root / relative).resolve()
    if not candidate.is_relative_to(root):
        raise ValueError(f"{field} escapes its declared root: {value!r}")
    return candidate


def _validate_project_ids(project_ids: Iterable[str]) -> list[str]:
    values = list(project_ids)
    if not values:
        raise ValueError("at least one project_id is required")
    if len(values) != len(set(values)):
        raise ValueError("project_id values must be unique")
    for value in values:
        path = _safe_relative(value, field="project_id")
        if len(path.parts) != 1 or not re.fullmatch(r"[a-z0-9][a-z0-9-]*", value):
            raise ValueError(f"project_id must be one stable slug: {value!r}")
    return values


def probe_media(path: Path) -> dict:
    completed = subprocess.run(
        [
            "ffprobe", "-v", "error", "-show_entries",
            "format=duration:stream=codec_type,codec_name,width,height,sample_rate,channels",
            "-of", "json", str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(completed.stdout)
    streams = payload.get("streams", [])
    video = next((item for item in streams if item.get("codec_type") == "video"), None)
    audio = next((item for item in streams if item.get("codec_type") == "audio"), None)
    duration = float(payload.get("format", {}).get("duration", 0))
    requires_video = path.suffix.lower() in VIDEO_EXTENSIONS
    if (requires_video and not video) or not audio or duration <= 0:
        raise ValueError("media requires readable audio, positive duration, and video for video containers")
    return {
        "duration": duration,
        "video_codec": video.get("codec_name") if video else None,
        "audio_codec": audio.get("codec_name"),
        "width": video.get("width") if video else None,
        "height": video.get("height") if video else None,
        "sample_rate": audio.get("sample_rate"),
        "channels": audio.get("channels"),
    }


def _subtitle_syntax(path: Path) -> dict:
    try:
        content = path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError as error:
        raise ValueError("subtitle is not UTF-8 text") from error
    suffix = path.suffix.lower()
    if suffix == ".ass":
        dialogues = [line for line in content.splitlines() if line.startswith("Dialogue:")]
        if "[Events]" not in content or not dialogues:
            raise ValueError("ASS subtitle requires [Events] and Dialogue lines")
        for line in dialogues:
            fields = line.split(",", 3)
            if len(fields) < 4:
                raise ValueError("ASS Dialogue line is malformed")
            start = _ass_seconds(fields[1])
            end = _ass_seconds(fields[2])
            if end <= start:
                raise ValueError("ASS Dialogue cue must have a positive interval")
        return {"format": "ass", "cue_count": len(dialogues)}
    if suffix == ".srt":
        cues = re.findall(
            r"(\d{2}:\d{2}:\d{2}[,.]\d{3})\s+-->\s+(\d{2}:\d{2}:\d{2}[,.]\d{3})",
            content,
        )
        if not cues:
            raise ValueError("SRT subtitle requires timestamp cues")
        if any(_clock_seconds(end) <= _clock_seconds(start) for start, end in cues):
            raise ValueError("SRT cue must have a positive interval")
        return {"format": "srt", "cue_count": len(cues)}
    if suffix == ".vtt":
        cues = re.findall(
            r"((?:\d{2}:)?\d{2}:\d{2}[.]\d{3})\s+-->\s+((?:\d{2}:)?\d{2}:\d{2}[.]\d{3})",
            content,
        )
        if not content.lstrip().startswith("WEBVTT") or not cues:
            raise ValueError("VTT subtitle requires WEBVTT and timestamp cues")
        if any(_clock_seconds(end) <= _clock_seconds(start) for start, end in cues):
            raise ValueError("VTT cue must have a positive interval")
        return {"format": "vtt", "cue_count": len(cues)}
    raise ValueError(f"unsupported subtitle extension: {suffix}")


def _ass_seconds(value: str) -> float:
    match = re.fullmatch(r"(\d+):(\d{2}):(\d{2})[.](\d{2})", value.strip())
    if not match:
        raise ValueError(f"invalid ASS timestamp: {value!r}")
    hours, minutes, seconds, centiseconds = map(int, match.groups())
    return hours * 3600 + minutes * 60 + seconds + centiseconds / 100


def _clock_seconds(value: str) -> float:
    parts = re.split(r"[:,.]", value.strip())
    if len(parts) == 4:
        hours, minutes, seconds, milliseconds = map(int, parts)
    elif len(parts) == 3:
        hours = 0
        minutes, seconds, milliseconds = map(int, parts)
    else:
        raise ValueError(f"invalid subtitle timestamp: {value!r}")
    return hours * 3600 + minutes * 60 + seconds + milliseconds / 1000


def _inventory_digest(items: list[dict]) -> str:
    canonical = json.dumps(sorted(items, key=lambda item: item["path"]), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _ordered_inventory_digest(items: list[dict]) -> str:
    canonical = json.dumps(items, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _same_filesystem_second(left_ns: int, right_ns: int) -> bool:
    return left_ns // 1_000_000_000 == right_ns // 1_000_000_000


def _asset_references(manifest: dict) -> list[dict]:
    references: list[dict] = []

    def walk(value: object) -> None:
        if isinstance(value, dict):
            if isinstance(value.get("path"), str):
                references.append(value)
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    for key in ("project_assets", "tracks", "evidence_artifacts", "gate_evidence", "approved_deliverables"):
        walk(manifest.get(key, []))
    for path in manifest.get("rights", {}).get("evidence", []):
        if isinstance(path, str):
            references.append({"path": path})
    migration_report = manifest.get("migration", {}).get("report")
    if isinstance(migration_report, str):
        references.append({"path": migration_report})
    return references


def _versioned_report(output: Path, stem: str, payload: dict) -> tuple[Path, str]:
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", stem):
        raise ValueError(f"report stem must be a stable slug: {stem!r}")
    serialized = (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    digest = hashlib.sha256(serialized).hexdigest()
    path = output / f"{stem}-{digest[:16]}.json"
    write_immutable_json(path, payload)
    return path, digest


def _verify_project(project_dir: Path, expected_project_id: str, production_root: Path, probe: Probe) -> dict:
    manifest = load_project(project_dir)
    migration = manifest.get("migration", {})
    errors: list[str] = []
    for path in project_dir.rglob("*"):
        if path.is_symlink():
            errors.append(f"destination symlink is not allowed: {path.relative_to(project_dir).as_posix()}")
    if manifest.get("project_id") != expected_project_id:
        errors.append("Project Manifest project_id does not match its directory")
    source_value = migration.get("source")
    if not isinstance(source_value, str) or not Path(source_value).is_absolute():
        errors.append("legacy source must be an absolute path")
        source = Path("/__invalid_legacy_source__")
    else:
        source = Path(source_value).resolve()
    report_value = migration.get("report")
    try:
        report_path = _contained(project_dir, report_value, field="migration report") if isinstance(report_value, str) else None
    except ValueError as error:
        errors.append(str(error))
        report_path = None
    if not source.is_dir():
        errors.append(f"legacy source missing: {source}")
    if report_path is None or not report_path.is_file():
        errors.append(f"migration report missing: {report_path}")
        actions: list[dict] = []
    else:
        try:
            actions = json.loads(report_path.read_text(encoding="utf-8"))["actions"]
            if not isinstance(actions, list):
                raise TypeError
        except (UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError):
            errors.append(f"migration report is invalid: {report_path}")
            actions = []

    source_items: list[dict] = []
    destination_items: list[dict] = []
    valid_actions: list[dict] = []
    seen_sources: set[str] = set()
    seen_destinations: set[str] = set()
    for action in actions:
        if not isinstance(action, dict) or not {"source", "destination", "size", "sha256"} <= set(action):
            errors.append("migration report contains an invalid action")
            continue
        try:
            _contained(source, action["source"], field="action source")
            _contained(project_dir, action["destination"], field="action destination")
        except (TypeError, ValueError) as error:
            errors.append(str(error))
            continue
        if action["source"] in seen_sources or action["destination"] in seen_destinations:
            errors.append("migration report contains duplicate source or destination paths")
            continue
        seen_sources.add(action["source"])
        seen_destinations.add(action["destination"])
        valid_actions.append(action)
    actions = valid_actions
    planned_source_paths = {action["source"] for action in actions}
    actual_source_paths: set[str] = set()
    if source.is_dir():
        for path in source.rglob("*"):
            if path.is_symlink():
                errors.append(f"legacy source symlink is not allowed: {path}")
            elif path.is_file():
                actual_source_paths.add(path.relative_to(source).as_posix())
        for path in sorted(actual_source_paths - planned_source_paths):
            errors.append(f"unplanned source file: {path}")
        for path in sorted(planned_source_paths - actual_source_paths):
            errors.append(f"planned source file missing from inventory: {path}")
    for action in actions:
        source_path = _contained(source, action["source"], field="action source")
        destination_path = _contained(project_dir, action["destination"], field="action destination")
        expected_size = action["size"]
        expected_hash = action["sha256"]
        if not source_path.is_file():
            errors.append(f"source file missing: {action['source']}")
        else:
            actual_hash = hash_file(source_path)
            source_items.append({
                "path": action["source"],
                "class": action.get("source_class", Path(action["source"]).parts[0] if len(Path(action["source"]).parts) > 1 else "root"),
                "size": source_path.stat().st_size,
                "mtime_ns": source_path.stat().st_mtime_ns,
                "sha256": actual_hash,
            })
            if source_path.stat().st_size != expected_size:
                errors.append(f"source size mismatch: {action['source']}")
            if actual_hash != expected_hash:
                errors.append(f"source hash mismatch: {action['source']}")
            expected_mtime = action.get("mtime_ns")
            if expected_mtime is not None and source_path.stat().st_mtime_ns != expected_mtime:
                errors.append(f"source mtime mismatch: {action['source']}")
        if not destination_path.is_file():
            errors.append(f"destination file missing: {action['destination']}")
        else:
            actual_hash = hash_file(destination_path)
            destination_items.append({
                "path": action["destination"],
                "size": destination_path.stat().st_size,
                "mtime_ns": destination_path.stat().st_mtime_ns,
                "sha256": actual_hash,
            })
            if destination_path.stat().st_size != expected_size:
                errors.append(f"destination size mismatch: {action['destination']}")
            if actual_hash != expected_hash:
                errors.append(f"destination hash mismatch: {action['destination']}")
            expected_mtime = action.get("mtime_ns")
            if expected_mtime is not None and not _same_filesystem_second(
                destination_path.stat().st_mtime_ns,
                expected_mtime,
            ):
                errors.append(f"destination mtime mismatch: {action['destination']}")
            if source_path.is_file() and not _same_filesystem_second(
                destination_path.stat().st_mtime_ns,
                source_path.stat().st_mtime_ns,
            ):
                errors.append(f"source/destination mtime mismatch: {action['destination']}")

    references = _asset_references(manifest)
    reference_hashes: dict[str, set[str]] = {}
    for reference in references:
        if reference.get("sha256"):
            reference_hashes.setdefault(reference["path"], set()).add(reference["sha256"])
    for path, hashes in reference_hashes.items():
        if len(hashes) > 1:
            errors.append(f"manifest references disagree on hash: {path}")
    for reference in references:
        try:
            path = _contained(project_dir, reference["path"], field="manifest reference")
        except ValueError as error:
            errors.append(str(error))
            continue
        if not path.is_file():
            errors.append(f"manifest reference missing: {reference['path']}")
        elif reference.get("sha256") and hash_file(path) != reference["sha256"]:
            errors.append(f"manifest reference hash mismatch: {reference['path']}")

    verification = migration.get("verification", {})
    if isinstance(verification, dict):
        for path_key, hash_key in (
            ("report", "report_sha256"),
            ("aggregate_report", "aggregate_sha256"),
            ("boundary_registry", "boundary_registry_sha256"),
        ):
            value = verification.get(path_key)
            if not value:
                continue
            try:
                path = _contained(production_root, value, field=f"migration verification {path_key}")
            except ValueError as error:
                errors.append(str(error))
                continue
            if not path.is_file():
                errors.append(f"migration verification reference missing: {value}")
            elif verification.get(hash_key) and hash_file(path) != verification[hash_key]:
                errors.append(f"migration verification reference hash mismatch: {value}")

    expected_paths = {item["destination"] for item in actions}
    generated_files = sorted(
        path.relative_to(project_dir).as_posix()
        for path in project_dir.rglob("*")
        if path.is_file() and path.relative_to(project_dir).as_posix() not in expected_paths
    )
    unknown_destination_files = [
        path for path in generated_files
        if path != "project.json" and not re.fullmatch(r"qa/legacy-migration-[0-9a-f]{16}\.json", path)
    ]
    for path in unknown_destination_files:
        errors.append(f"unknown destination file outside migration plan: {path}")
    full_destination_items = [
        {
            "path": path.relative_to(project_dir).as_posix(),
            "size": path.stat().st_size,
            "mtime_ns": path.stat().st_mtime_ns,
            "sha256": hash_file(path),
            "class": "copied" if path.relative_to(project_dir).as_posix() in expected_paths else "generated",
        }
        for path in sorted(project_dir.rglob("*"))
        if path.is_file() and not path.is_symlink()
    ]
    media_results: list[dict] = []
    audio_results: list[dict] = []
    subtitle_results: list[dict] = []
    for item in destination_items:
        path = project_dir / item["path"]
        if path.suffix.lower() in VIDEO_EXTENSIONS:
            try:
                media_results.append({"path": item["path"], **probe(path)})
            except (OSError, ValueError, subprocess.SubprocessError, json.JSONDecodeError) as error:
                errors.append(f"media probe failed: {item['path']}: {error}")
        if path.suffix.lower() in AUDIO_EXTENSIONS:
            try:
                audio_results.append({"path": item["path"], **probe(path)})
            except (OSError, ValueError, subprocess.SubprocessError, json.JSONDecodeError) as error:
                errors.append(f"audio probe failed: {item['path']}: {error}")
        if path.suffix.lower() in SUBTITLE_EXTENSIONS:
            try:
                subtitle_results.append({"path": item["path"], **_subtitle_syntax(path)})
            except (OSError, ValueError) as error:
                errors.append(f"subtitle syntax failed: {item['path']}: {error}")

    referenced_subtitles = {
        reference["path"] for reference in references
        if Path(reference["path"]).suffix.lower() in SUBTITLE_EXTENSIONS
    }
    subtitle_paths = {item["path"] for item in subtitle_results}
    unreferenced_subtitles = sorted(subtitle_paths - referenced_subtitles)
    for path in unreferenced_subtitles:
        if not path.startswith("subtitles/archive/"):
            errors.append(f"subtitle is not mapped to a track or explicit archive: {path}")
    source_inventory_sha = _inventory_digest(source_items)
    migration_order_inventory_sha = _ordered_inventory_digest(source_items)
    recorded_inventory_sha = migration.get("source_inventory_sha256")
    if recorded_inventory_sha and migration_order_inventory_sha != recorded_inventory_sha:
        errors.append("source inventory digest does not match Project Manifest")
    return {
        "project_id": expected_project_id,
        "status": "PASS" if not errors else "FAIL",
        "source": {
            "root": str(source),
            "file_count": len(source_items),
            "total_size": sum(item["size"] for item in source_items),
            "inventory_sha256": source_inventory_sha,
            "migration_order_inventory_sha256": migration_order_inventory_sha,
        },
        "destination": {
            "root": str(project_dir),
            "snapshot_phase": "before-boundary-writeback",
            "file_count": len(full_destination_items),
            "total_size": sum(item["size"] for item in full_destination_items),
            "inventory_sha256": _inventory_digest(full_destination_items),
            "copied_file_count": len(destination_items),
            "copied_total_size": sum(item["size"] for item in destination_items),
            "copied_inventory_sha256": _inventory_digest(destination_items),
            "generated_file_count": len(generated_files),
            "generated_files": generated_files,
            "unknown_file_count": len(unknown_destination_files),
            "count_difference_explanation": "Generated Project Manifest and immutable verification/migration evidence are excluded from copied-file parity.",
            "mtime_comparison": "Source inventory retains nanoseconds; source/destination parity is normalized to whole seconds across the Windows NTFS/WSL copy boundary.",
        },
        "manifest_references": {"count": len(references), "verified": len(references) - sum(error.startswith("manifest reference") for error in errors)},
        "media": {"count": len(media_results), "files": media_results},
        "audio": {"count": len(audio_results), "files": audio_results},
        "subtitles": {"count": len(subtitle_results), "files": subtitle_results, "unreferenced": unreferenced_subtitles},
        "review_gates": manifest.get("review_gates", {}),
        "rights": manifest.get("rights", {}),
        "unresolved_conflicts": manifest.get("unresolved_conflicts", []),
        "errors": errors,
    }


PRODUCTION_MIGRATION_COHORT = frozenset({
    "shishigami-7-f7b0uizxe",
    "ruri-birthday-live-2025",
    "hachi-birthday-live-2025",
})


def _source_snapshot(source: Path) -> dict:
    items: list[dict] = []
    for path in sorted(source.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"legacy source symlink is not allowed: {path}")
        if path.is_file():
            relative = path.relative_to(source)
            items.append({
                "path": relative.as_posix(),
                "class": relative.parts[0] if len(relative.parts) > 1 else "root",
                "size": path.stat().st_size,
                "mtime_ns": path.stat().st_mtime_ns,
                "sha256": hash_file(path),
            })
    return {
        "file_count": len(items),
        "total_size": sum(item["size"] for item in items),
        "inventory_sha256": _inventory_digest(items),
    }


def _destination_snapshot(project_dir: Path) -> dict:
    items: list[dict] = []
    for path in sorted(project_dir.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"destination symlink is not allowed: {path}")
        if path.is_file():
            items.append({
                "path": path.relative_to(project_dir).as_posix(),
                "size": path.stat().st_size,
                "mtime_ns": path.stat().st_mtime_ns,
                "sha256": hash_file(path),
            })
    return {
        "file_count": len(items),
        "total_size": sum(item["size"] for item in items),
        "inventory_sha256": _inventory_digest(items),
    }


def verify_migrated_projects(
    projects_root: Path,
    project_ids: Iterable[str],
    output: Path,
    *,
    probe: Probe = probe_media,
    finalize_boundaries: bool = False,
    expected_cohort: frozenset[str] | None = None,
) -> dict:
    raw_projects_root = projects_root.expanduser()
    if raw_projects_root.is_symlink():
        raise ValueError("projects_root must not be a symlink")
    projects_root = raw_projects_root.resolve()
    output = output.expanduser().resolve()
    ids = _validate_project_ids(project_ids)
    cohort = expected_cohort if expected_cohort is not None else PRODUCTION_MIGRATION_COHORT
    if finalize_boundaries and set(ids) != set(cohort):
        raise ValueError("boundary finalization requires the complete migration cohort")
    if output == projects_root or output.is_relative_to(projects_root):
        raise ValueError("verification output must be outside projects_root")
    production_root = projects_root.parent
    if finalize_boundaries and not output.is_relative_to(production_root):
        raise ValueError("boundary finalization output must be inside the Production Data Root")

    project_dirs: dict[str, Path] = {}
    legacy_sources: dict[str, Path] = {}
    for project_id in ids:
        unresolved = projects_root / project_id
        if unresolved.is_symlink():
            raise ValueError(f"project directory must not be a symlink: {project_id}")
        project_dir = _contained(projects_root, project_id, field="project_id")
        manifest = load_project(project_dir)
        source_value = manifest.get("migration", {}).get("source")
        if not isinstance(source_value, str) or not Path(source_value).is_absolute():
            raise ValueError(f"legacy source must be absolute for {project_id}")
        source = Path(source_value).resolve()
        if output == source or output.is_relative_to(source):
            raise ValueError(f"verification output cannot be inside legacy source: {source}")
        project_dirs[project_id] = project_dir
        legacy_sources[project_id] = source

    source_values = list(legacy_sources.values())
    for index, source in enumerate(source_values):
        for other in source_values[index + 1:]:
            if source == other or source.is_relative_to(other) or other.is_relative_to(source):
                raise ValueError("migration cohort legacy sources must be distinct and non-overlapping")

    reports = [
        _verify_project(project_dirs[project_id], project_id, production_root, probe)
        for project_id in ids
    ]
    status = "PASS" if all(report["status"] == "PASS" for report in reports) else "FAIL"
    individual_paths: dict[str, Path] = {}
    individual_hashes: dict[str, str] = {}
    for report in reports:
        path, digest = _versioned_report(output, report["project_id"], report)
        individual_paths[report["project_id"]] = path
        individual_hashes[report["project_id"]] = digest
        report["report"] = str(path)
    aggregate = {
        "status": status,
        "project_count": len(reports),
        "projects_root": str(projects_root),
        "projects": reports,
        "totals": {
            "source_files": sum(report["source"]["file_count"] for report in reports),
            "source_size": sum(report["source"]["total_size"] for report in reports),
            "destination_files": sum(report["destination"]["file_count"] for report in reports),
            "destination_size": sum(report["destination"]["total_size"] for report in reports),
            "copied_files": sum(report["destination"]["copied_file_count"] for report in reports),
            "media_files": sum(report["media"]["count"] for report in reports),
            "audio_files": sum(report["audio"]["count"] for report in reports),
            "subtitle_files": sum(report["subtitles"]["count"] for report in reports),
        },
        "unresolved_conflicts": [
            {"project_id": report["project_id"], "conflict": conflict}
            for report in reports for conflict in report["unresolved_conflicts"]
        ],
        "pending_gates": [
            {"project_id": report["project_id"], "gate": gate, "status": gate_status}
            for report in reports
            for gate, gate_status in report["review_gates"].items()
            if gate_status != "approved"
        ],
        "rights_risks": [
            {
                "project_id": report["project_id"],
                "status": report["rights"].get("status", "pending"),
                "limitation": limitation,
            }
            for report in reports
            for limitation in report["rights"].get("limitations", ["No explicit rights limitation ledger was recorded."])
        ],
    }
    aggregate_path, aggregate_sha = _versioned_report(output, "migration-verification", aggregate)
    aggregate["aggregate_report"] = str(aggregate_path)

    if finalize_boundaries and status == "PASS":
        post_report_changed: list[str] = []
        for report in reports:
            try:
                current = _source_snapshot(legacy_sources[report["project_id"]])
            except (OSError, ValueError):
                post_report_changed.append(report["project_id"])
                continue
            if current != {
                "file_count": report["source"]["file_count"],
                "total_size": report["source"]["total_size"],
                "inventory_sha256": report["source"]["inventory_sha256"],
            }:
                post_report_changed.append(report["project_id"])
        if post_report_changed:
            aggregate["status"] = "FAIL"
            aggregate["post_report_source_changes"] = post_report_changed
            failure_path, _ = _versioned_report(output, "migration-verification-failed", aggregate)
            aggregate["aggregate_report"] = str(failure_path)
            return aggregate

        registry = {
            "status": "verified",
            "new_write_root": str(projects_root),
            "policy": "All new Media Project writes go to new_write_root; legacy sources are logical read-only recovery boundaries.",
            "projects": [
                {
                    "project_id": report["project_id"],
                    "legacy_source": report["source"]["root"],
                    "boundary": "logical-read-only",
                    "source_inventory_sha256": report["source"]["inventory_sha256"],
                    "verification_report": individual_paths[report["project_id"]].relative_to(production_root).as_posix(),
                    "verification_sha256": individual_hashes[report["project_id"]],
                }
                for report in reports
            ],
            "aggregate_verification": aggregate_path.relative_to(production_root).as_posix(),
            "aggregate_sha256": aggregate_sha,
        }
        registry_path, registry_sha = _versioned_report(output, "legacy-boundaries", registry)
        original_manifests = {
            report["project_id"]: load_project(project_dirs[report["project_id"]])
            for report in reports
        }
        final_manifests: dict[str, dict] = {}
        for report in reports:
            project_id = report["project_id"]
            manifest = json.loads(json.dumps(original_manifests[project_id]))
            manifest["migration"]["source_legacy_boundary"] = "logical-read-only"
            manifest["migration"]["verification"] = {
                "status": "PASS",
                "report": individual_paths[project_id].relative_to(production_root).as_posix(),
                "report_sha256": individual_hashes[project_id],
                "aggregate_report": aggregate_path.relative_to(production_root).as_posix(),
                "aggregate_sha256": aggregate_sha,
                "boundary_registry": registry_path.relative_to(production_root).as_posix(),
                "boundary_registry_sha256": registry_sha,
            }
            final_manifests[project_id] = manifest

        written: list[str] = []
        try:
            for project_id in ids:
                save_project(project_dirs[project_id], final_manifests[project_id])
                written.append(project_id)
            attestation = {
                "status": "verified",
                "boundary_registry": registry_path.relative_to(production_root).as_posix(),
                "boundary_registry_sha256": registry_sha,
                "projects": [
                    {
                        "project_id": project_id,
                        "final_destination": _destination_snapshot(project_dirs[project_id]),
                        "final_manifest_sha256": hash_file(project_dirs[project_id] / "project.json"),
                    }
                    for project_id in ids
                ],
            }
            attestation_path, _ = _versioned_report(output, "finalized-destinations", attestation)
        except Exception:
            rollback_errors: list[str] = []
            for project_id in written:
                try:
                    save_project(project_dirs[project_id], original_manifests[project_id])
                except Exception as error:
                    rollback_errors.append(f"{project_id}: {error}")
            if rollback_errors:
                raise RuntimeError(f"boundary finalization failed and rollback was incomplete: {rollback_errors}")
            raise
        aggregate["boundary_registry"] = str(registry_path)
        aggregate["final_destination_attestation"] = str(attestation_path)
    return aggregate
