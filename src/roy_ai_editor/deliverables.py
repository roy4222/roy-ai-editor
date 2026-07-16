"""Render candidate karaoke media and explicitly approve deliverables."""

from __future__ import annotations

import hashlib
import shutil
from datetime import UTC, datetime
from pathlib import Path

from . import media
from .karaoke import render_file
from .project import load_project, record_evidence, save_project


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _copy_immutable(source: Path, destination: Path) -> str:
    source_sha = _sha256(source)
    if destination.exists():
        if _sha256(destination) != source_sha:
            raise RuntimeError(f"Approved artifact already exists with different content: {destination}")
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    return source_sha


def render_track(project_dir: Path, track_id: str, source_video: Path, *, font: str) -> dict:
    project_dir = project_dir.expanduser().resolve()
    manifest = load_project(project_dir)
    track = next((item for item in manifest.get("tracks", []) if item.get("track_id") == track_id), None)
    if not track or track.get("timing", {}).get("status") != "approved":
        raise PermissionError("rendering requires approved timing")
    if not source_video.is_file():
        raise FileNotFoundError(source_video)

    subtitle_relative = Path("subtitles") / "draft" / f"{track_id}.ass"
    video_relative = Path("videos") / "review" / f"{track_id}-karaoke.mp4"
    subtitle_path = project_dir / subtitle_relative
    video_path = project_dir / video_relative
    qa = render_file(project_dir / track["timing"]["artifact"], subtitle_path, font=font)
    if qa["timing_status"] != "exact-input":
        raise ValueError("candidate rendering requires exact approved timing")
    media.burn_ass(source_video, subtitle_path, video_path)
    probe = media.probe(video_path)
    evidence = record_evidence(project_dir, "render-qa", {
        "created_at": datetime.now(UTC).isoformat(),
        "probe": probe,
        "qa": qa,
        "subtitle_sha256": _sha256(subtitle_path),
        "track_id": track_id,
        "video_sha256": _sha256(video_path),
        "visual_review_required": True,
    }, directory="qa")
    candidate = {
        "candidate_id": f"{track_id}-karaoke-v1",
        "status": "review-required",
        "video": video_relative.as_posix(),
        "subtitle": subtitle_relative.as_posix(),
        "qa_evidence_id": evidence["id"],
    }
    track["render_candidate"] = candidate
    manifest.setdefault("evidence_artifacts", []).append(evidence)
    manifest["stage"] = "rendered"
    manifest["status"] = "rendered"
    save_project(project_dir, manifest)
    return candidate


def approve_deliverable(
    project_dir: Path,
    track_id: str,
    *,
    approved_by: str,
    note: str,
) -> dict:
    project_dir = project_dir.expanduser().resolve()
    manifest = load_project(project_dir)
    track = next((item for item in manifest.get("tracks", []) if item.get("track_id") == track_id), None)
    candidate = track.get("render_candidate") if track else None
    if not candidate or candidate.get("status") != "review-required":
        raise PermissionError("deliverable approval requires a rendered review candidate")
    if not approved_by.strip() or not note.strip():
        raise ValueError("approved_by and note must not be blank")

    deliverable_id = candidate["candidate_id"]
    source_video = project_dir / candidate["video"]
    source_subtitle = project_dir / candidate["subtitle"]
    video_relative = Path("videos") / "approved" / f"{deliverable_id}.mp4"
    subtitle_relative = Path("subtitles") / "approved" / f"{deliverable_id}.ass"
    video_sha = _copy_immutable(source_video, project_dir / video_relative)
    subtitle_sha = _copy_immutable(source_subtitle, project_dir / subtitle_relative)
    approval = record_evidence(project_dir, "deliverable-approval", {
        "approved_at": datetime.now(UTC).isoformat(),
        "approved_by": approved_by.strip(),
        "candidate_id": candidate["candidate_id"],
        "note": note.strip(),
        "qa_evidence_id": candidate["qa_evidence_id"],
        "subtitle_sha256": subtitle_sha,
        "track_id": track_id,
        "video_sha256": video_sha,
    })
    deliverable = {
        "deliverable_id": deliverable_id,
        "track_id": track_id,
        "status": "approved",
        "video": {"path": video_relative.as_posix(), "sha256": video_sha},
        "subtitle": {"path": subtitle_relative.as_posix(), "sha256": subtitle_sha},
        "approval_evidence_id": approval["id"],
    }
    manifest["approved_deliverables"] = [
        item for item in manifest.get("approved_deliverables", []) if item.get("track_id") != track_id
    ] + [deliverable]
    track["approved_deliverable_id"] = deliverable_id
    candidate["status"] = "approved"
    manifest.setdefault("evidence_artifacts", []).append(approval)
    manifest["review_gates"]["edit"] = "approved"
    manifest["stage"] = "deliverable-approved"
    manifest["status"] = "deliverable-approved"
    save_project(project_dir, manifest)
    return deliverable
