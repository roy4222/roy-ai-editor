"""Non-destructive Legacy Media Project migration."""

from __future__ import annotations

import shutil
from pathlib import Path

from .deliverables import hash_file
from .project import STANDARD_PROJECT_DIRECTORIES, save_project, write_immutable_json

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


def migrate_legacy(source: Path, destination: Path, *, execute: bool) -> dict:
    source = source.expanduser().resolve()
    destination = destination.expanduser().resolve()
    if not source.is_dir():
        raise FileNotFoundError(source)
    if destination == source or destination.is_relative_to(source):
        raise ValueError("destination cannot be inside legacy source")
    before = _inventory(source)
    actions = [
        {"source": item["path"], "destination": _destination(Path(item["path"])).as_posix(), "sha256": item["sha256"]}
        for item in before
    ]
    if not execute:
        return {"mode": "dry-run", "source_file_count": len(before), "actions": actions}

    for directory in STANDARD_PROJECT_DIRECTORIES:
        (destination / directory).mkdir(parents=True, exist_ok=True)
    for item, action in zip(before, actions, strict=True):
        source_path = source / item["path"]
        destination_path = destination / action["destination"]
        if destination_path.exists():
            if hash_file(destination_path) != item["sha256"]:
                raise RuntimeError(f"destination conflict: {destination_path}")
            continue
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, destination_path)
        if hash_file(destination_path) != item["sha256"]:
            raise RuntimeError(f"copy verification failed: {destination_path}")

    after = _inventory(source)
    source_unchanged = before == after
    if not source_unchanged:
        raise RuntimeError("legacy source changed during migration")
    report = {
        "mode": "execute",
        "status": "verified",
        "source_file_count": len(before),
        "source_total_size": sum(item["size"] for item in before),
        "source_unchanged": True,
        "legacy_boundary": "logical-read-only-candidate",
        "actions": actions,
    }
    report_relative = Path("qa/legacy-migration.json")
    report_sha = write_immutable_json(destination / report_relative, report)
    manifest = {
        "schema_version": 2,
        "project_id": destination.name,
        "workflow": "legacy-migration",
        "stage": "migrated-pending-review",
        "status": "migrated-pending-review",
        "tracks": [],
        "approved_deliverables": [],
        "evidence_artifacts": [{
            "id": f"evidence-{report_sha[:16]}",
            "kind": "legacy-migration",
            "path": report_relative.as_posix(),
            "sha256": report_sha,
        }],
        "review_gates": {"rights": "pending", "lyrics": "pending", "edit": "pending", "publish": "pending"},
        "migration": {"status": "verified", "report": report_relative.as_posix(), "source_legacy_boundary": "logical-read-only-candidate"},
    }
    save_project(destination, manifest)
    return report
