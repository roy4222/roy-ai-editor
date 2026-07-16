"""Build local publish packages from Approved Deliverables."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from .deliverables import hash_file
from .project import load_project, save_project, write_immutable_json


def _copy_verified(source: Path, destination: Path) -> str:
    source_sha = hash_file(source)
    if destination.exists():
        if hash_file(destination) != source_sha:
            raise RuntimeError(f"Publish artifact conflict: {destination}")
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    return source_sha


def package_deliverable(
    project_dir: Path,
    track_id: str,
    metadata_path: Path,
    thumbnail_path: Path,
) -> dict:
    project_dir = project_dir.expanduser().resolve()
    manifest = load_project(project_dir)
    deliverable = next(
        (
            item for item in manifest.get("approved_deliverables", [])
            if item.get("track_id") == track_id and item.get("status") == "approved"
        ),
        None,
    )
    if not deliverable:
        raise PermissionError("publish packaging requires an Approved Deliverable")
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    if not all(str(metadata.get(field, "")).strip() for field in ("title", "description")):
        raise ValueError("publish metadata requires title and description")
    if not isinstance(metadata.get("credits"), list) or not metadata["credits"]:
        raise ValueError("publish metadata requires credits")
    rights = metadata.get("rights", {})
    if not str(rights.get("status", "")).strip() or not isinstance(rights.get("warnings"), list):
        raise ValueError("publish metadata requires rights status and warnings")
    if not thumbnail_path.is_file():
        raise FileNotFoundError(thumbnail_path)

    package_id = f"{deliverable['deliverable_id']}-publish-v1"
    relative_dir = Path("publish") / package_id
    package_dir = project_dir / relative_dir
    files = {
        "video.mp4": _copy_verified(project_dir / deliverable["video"]["path"], package_dir / "video.mp4"),
        "subtitles.ass": _copy_verified(project_dir / deliverable["subtitle"]["path"], package_dir / "subtitles.ass"),
        "thumbnail.png": _copy_verified(thumbnail_path, package_dir / "thumbnail.png"),
    }
    metadata_sha = write_immutable_json(package_dir / "metadata.json", metadata)
    package_manifest = {
        "schema_version": 1,
        "package_id": package_id,
        "source_deliverable_id": deliverable["deliverable_id"],
        "track_id": track_id,
        "files": files,
        "metadata_sha256": metadata_sha,
        "upload_performed": False,
    }
    write_immutable_json(package_dir / "package.json", package_manifest)
    package_reference = {
        "package_id": package_id,
        "source_deliverable_id": deliverable["deliverable_id"],
        "track_id": track_id,
        "path": relative_dir.as_posix(),
        "status": "ready-for-human-publish",
    }
    manifest["publish_packages"] = [
        item for item in manifest.get("publish_packages", []) if item.get("track_id") != track_id
    ] + [package_reference]
    manifest["review_gates"]["publish"] = "pending"
    manifest["stage"] = "publish-ready"
    manifest["status"] = "publish-ready"
    save_project(project_dir, manifest)
    return package_reference
