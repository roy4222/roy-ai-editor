"""Render candidate karaoke media and explicitly approve deliverables."""

from __future__ import annotations

import hashlib
import shutil
import unicodedata
from datetime import UTC, datetime
from pathlib import Path

from . import media
from .karaoke import (
    KARAOKE_FONT_SIZE,
    KARAOKE_SPACING,
    display_advance,
    load_timing,
    render_file,
    ruby_position,
)
from .project import load_project, record_evidence, save_project


def hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def check_subtitle_layout(timing_path: Path) -> dict:
    lines = load_timing(timing_path)
    failures: list[dict] = []
    fullwidth_characters = 0
    previous_end = 0.0
    for line_number, line in enumerate(lines, start=1):
        if line.start < previous_end:
            failures.append({"kind": "line-overlap", "line": line_number})
        previous_end = line.end
        japanese_width = display_advance(
            line.japanese,
            font_size=KARAOKE_FONT_SIZE,
            spacing=KARAOKE_SPACING,
        )
        translation_width = display_advance(line.translation, font_size=44, spacing=1.0)
        fullwidth_characters += sum(
            1 for character in f"{line.japanese}{line.translation}"
            if unicodedata.east_asian_width(character) in "WFA"
        )
        if japanese_width > 1680:
            failures.append({
                "kind": "japanese-safe-width",
                "line": line_number,
                "estimated_width": round(japanese_width, 2),
                "safe_width": 1680,
            })
        if translation_width > 1680:
            failures.append({
                "kind": "translation-safe-width",
                "line": line_number,
                "estimated_width": round(translation_width, 2),
                "safe_width": 1680,
            })
        for span in line.ruby:
            x, _ = ruby_position(line.japanese, span)
            if not 120 <= x <= 1800:
                failures.append({"kind": "ruby-safe-area", "line": line_number, "x": x})
    return {
        "status": "failed" if failures else "passed",
        "line_count": len(lines),
        "fullwidth_character_count": fullwidth_characters,
        "failures": failures,
    }


def _burned_pixel_qa(
    project_dir: Path,
    track_id: str,
    video_path: Path,
    timing_path: Path,
    probe: dict,
) -> dict:
    layout = check_subtitle_layout(timing_path)
    video_stream = next(
        (stream for stream in probe.get("streams", []) if stream.get("codec_type") == "video"),
        None,
    )
    if not video_stream:
        raise RuntimeError("rendered candidate has no video stream")
    width, height = int(video_stream["width"]), int(video_stream["height"])
    crop_height = max(2, int(height * 0.35) // 2 * 2)
    crop_y = height - crop_height
    crop = f"{width}:{crop_height}:0:{crop_y}"
    timing_sha = hash_file(timing_path)
    video_sha = hash_file(video_path)
    relative_root = Path("qa") / "visual" / f"{track_id}-{video_sha[:8]}-{timing_sha[:8]}"
    output_root = project_dir / relative_root
    output_root.mkdir(parents=True, exist_ok=True)
    ffmpeg = media.require_tool("ffmpeg")
    frames: list[dict] = []
    for line_number, line in enumerate(load_timing(timing_path), start=1):
        relative = relative_root / f"line-{line_number:03d}.png"
        target = project_dir / relative
        if not target.exists():
            media.run([
                ffmpeg,
                "-hide_banner",
                "-loglevel", "error",
                "-ss", f"{(line.start + line.end) / 2:.4f}",
                "-i", str(video_path),
                "-frames:v", "1",
                "-vf", f"crop={crop}",
                "-y", str(target),
            ])
        frames.append({
            "line": line_number,
            "sample_time": round((line.start + line.end) / 2, 4),
            "path": relative.as_posix(),
            "sha256": hash_file(target),
        })
    return {
        "status": layout["status"],
        "review_policy": "inspect every full-width burned-pixel crop before approval",
        "crop": crop,
        "layout": layout,
        "frames": frames,
    }


def _copy_immutable(source: Path, destination: Path) -> str:
    source_sha = hash_file(source)
    if destination.exists():
        if hash_file(destination) != source_sha:
            raise RuntimeError(f"Approved artifact already exists with different content: {destination}")
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    return source_sha


def _import_track_input(project_dir: Path, track_id: str, source_video: Path) -> dict:
    source_video = source_video.expanduser().resolve()
    if not source_video.is_file():
        raise FileNotFoundError(source_video)
    try:
        relative = source_video.relative_to(project_dir)
    except ValueError:
        relative = Path("videos") / "clips" / f"{track_id}-input{source_video.suffix.lower() or '.mp4'}"
        source_sha = _copy_immutable(source_video, project_dir / relative)
    else:
        if relative.parts[:2] not in {("videos", "source"), ("videos", "clips")}:
            relative = Path("videos") / "clips" / f"{track_id}-input{source_video.suffix.lower() or '.mp4'}"
            source_sha = _copy_immutable(source_video, project_dir / relative)
        else:
            source_sha = hash_file(source_video)
    return {"path": relative.as_posix(), "sha256": source_sha}


def render_track(project_dir: Path, track_id: str, source_video: Path, *, font: str) -> dict:
    project_dir = project_dir.expanduser().resolve()
    manifest = load_project(project_dir)
    track = next((item for item in manifest.get("tracks", []) if item.get("track_id") == track_id), None)
    if not track or track.get("timing", {}).get("status") != "approved":
        raise PermissionError("rendering requires approved timing")
    input_reference = _import_track_input(project_dir, track_id, source_video)
    project_input = project_dir / input_reference["path"]

    subtitle_relative = Path("subtitles") / "draft" / f"{track_id}.ass"
    video_relative = Path("videos") / "review" / f"{track_id}-karaoke.mp4"
    subtitle_path = project_dir / subtitle_relative
    video_path = project_dir / video_relative
    qa = render_file(project_dir / track["timing"]["artifact"], subtitle_path, font=font)
    if qa["timing_status"] != "exact-input":
        raise ValueError("candidate rendering requires exact approved timing")
    media.burn_ass(project_input, subtitle_path, video_path)
    probe = media.probe(video_path)
    visual_qa = _burned_pixel_qa(
        project_dir,
        track_id,
        video_path,
        project_dir / track["timing"]["artifact"],
        probe,
    )
    subtitle_sha = hash_file(subtitle_path)
    video_sha = hash_file(video_path)
    evidence = record_evidence(project_dir, "render-qa", {
        "created_at": datetime.now(UTC).isoformat(),
        "probe": probe,
        "qa": qa,
        "input": input_reference,
        "subtitle_sha256": subtitle_sha,
        "track_id": track_id,
        "video_sha256": video_sha,
        "visual_qa": visual_qa,
        "visual_review_required": True,
    }, directory="qa")
    candidate = {
        "candidate_id": f"{track_id}-karaoke-v1",
        "status": "review-required" if visual_qa["status"] == "passed" else "qa-failed",
        "video": video_relative.as_posix(),
        "subtitle": subtitle_relative.as_posix(),
        "video_sha256": video_sha,
        "subtitle_sha256": subtitle_sha,
        "qa_evidence_id": evidence["id"],
        "qa_status": visual_qa["status"],
        "visual_qa": visual_qa,
        "input": input_reference,
    }
    track["render_candidate"] = candidate
    manifest.setdefault("evidence_artifacts", []).append(evidence)
    all_tracks_rendered = bool(manifest.get("tracks")) and all(
        item.get("render_candidate", {}).get("qa_status") == "passed"
        for item in manifest["tracks"]
    )
    if visual_qa["status"] != "passed":
        manifest["stage"] = "render-qa-failed"
    else:
        manifest["stage"] = "rendered" if all_tracks_rendered else "partially-rendered"
    manifest["status"] = manifest["stage"]
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
    if not candidate:
        raise PermissionError("deliverable approval requires a rendered review candidate")
    if candidate.get("qa_status") != "passed":
        raise PermissionError("deliverable approval requires passing render QA")
    if candidate.get("status") != "review-required":
        raise PermissionError("deliverable approval requires a rendered review candidate")
    if not approved_by.strip() or not note.strip():
        raise ValueError("approved_by and note must not be blank")

    deliverable_id = candidate["candidate_id"]
    source_video = project_dir / candidate["video"]
    source_subtitle = project_dir / candidate["subtitle"]
    if (
        not candidate.get("video_sha256")
        or not candidate.get("subtitle_sha256")
        or hash_file(source_video) != candidate["video_sha256"]
        or hash_file(source_subtitle) != candidate["subtitle_sha256"]
    ):
        raise RuntimeError("render candidate changed after render QA")
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
    approved_track_ids = {
        item["track_id"]
        for item in manifest["approved_deliverables"]
        if item.get("status") == "approved"
    }
    all_tracks_approved = bool(manifest.get("tracks")) and all(
        item.get("track_id") in approved_track_ids for item in manifest["tracks"]
    )
    manifest["review_gates"]["edit"] = "approved" if all_tracks_approved else "pending"
    manifest["stage"] = "deliverable-approved" if all_tracks_approved else "partially-deliverable-approved"
    manifest["status"] = manifest["stage"]
    save_project(project_dir, manifest)
    return deliverable
