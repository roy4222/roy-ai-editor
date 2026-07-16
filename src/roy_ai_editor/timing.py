"""Reconcile forced-alignment evidence with approved lyrics."""

from __future__ import annotations

import json
import shutil
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from . import alignment
from .deliverables import hash_file
from .project import load_project, record_evidence, save_project, write_immutable_json


def create_timing_candidate(
    project_dir: Path,
    track_id: str,
    audio_path: Path,
    *,
    model_name: str,
    language: str,
) -> dict:
    project_dir = project_dir.expanduser().resolve()
    manifest = load_project(project_dir)
    track = next((item for item in manifest.get("tracks", []) if item.get("track_id") == track_id), None)
    if not track or track.get("lyrics", {}).get("status") != "approved":
        raise PermissionError("forced alignment requires an approved lyrics track")
    audio_path = audio_path.expanduser().resolve()
    if not audio_path.is_file():
        raise FileNotFoundError(audio_path)
    audio_sha = hash_file(audio_path)
    audio_relative = (
        Path("videos") / "clips" /
        f"{track_id}-alignment-audio-{audio_sha[:8]}{audio_path.suffix.lower() or '.wav'}"
    )
    project_audio = project_dir / audio_relative
    created_audio = False
    if project_audio.exists():
        if hash_file(project_audio) != audio_sha:
            raise RuntimeError(f"alignment audio conflict: {project_audio}")
    else:
        shutil.copy2(audio_path, project_audio)
        created_audio = True

    work_dir = project_dir / "work"
    work_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        dir=work_dir,
        prefix=f".{track_id}-alignment-",
        suffix=".json",
        delete=False,
    ) as handle:
        temporary = Path(handle.name)
    try:
        alignment.transcribe(
            project_audio,
            temporary,
            model_name=model_name,
            language=language,
        )
        alignment_payload = json.loads(temporary.read_text(encoding="utf-8"))
        if not isinstance(alignment_payload.get("segments"), list) or not alignment_payload["segments"]:
            raise ValueError("forced alignment produced no segments")
        alignment_sha = hash_file(temporary)
        alignment_relative = Path("timing") / "alignment" / f"{track_id}-{alignment_sha[:16]}.json"
        alignment_artifact = project_dir / alignment_relative
        if alignment_artifact.exists():
            if hash_file(alignment_artifact) != alignment_sha:
                raise RuntimeError(f"alignment artifact conflict: {alignment_artifact}")
        else:
            shutil.copy2(temporary, alignment_artifact)
    except Exception:
        if created_audio:
            project_audio.unlink(missing_ok=True)
        raise
    finally:
        temporary.unlink(missing_ok=True)

    evidence = record_evidence(project_dir, "forced-alignment", {
        "created_at": datetime.now(UTC).isoformat(),
        "track_id": track_id,
        "tool": "stable-ts",
        "model": model_name,
        "language": language,
        "audio": {"path": audio_relative.as_posix(), "sha256": audio_sha},
        "artifact": alignment_relative.as_posix(),
        "sha256": alignment_sha,
    }, directory="qa")
    candidate = {
        "status": "review-required",
        "artifact": alignment_relative.as_posix(),
        "sha256": alignment_sha,
        "audio": {"path": audio_relative.as_posix(), "sha256": audio_sha},
        "tool": "stable-ts",
        "model": model_name,
        "language": language,
        "evidence_id": evidence["id"],
    }
    track["timing_candidate"] = candidate
    manifest.setdefault("evidence_artifacts", []).append(evidence)
    manifest["stage"] = "timing-review-required"
    manifest["status"] = "timing-review-required"
    save_project(project_dir, manifest)
    return candidate


def _without_space(text: str) -> str:
    return "".join(character for character in text if not character.isspace())


def _merge_zero_words(raw_words: list[dict]) -> tuple[list[dict], list[str]]:
    words = [
        {"text": str(word.get("word", "")), "start": float(word["start"]), "end": float(word["end"])}
        for word in raw_words
    ]
    merged: list[str] = []
    index = 0
    while index < len(words):
        word = words[index]
        if word["end"] > word["start"]:
            index += 1
            continue
        text = word["text"]
        merged.append(text)
        following = next((candidate for candidate in range(index + 1, len(words)) if words[candidate]["end"] > words[candidate]["start"]), None)
        previous = next((candidate for candidate in range(index - 1, -1, -1) if words[candidate]["end"] > words[candidate]["start"]), None)
        if following is not None and abs(words[following]["start"] - word["start"]) <= 0.03:
            words[following]["text"] = text + words[following]["text"]
        elif previous is not None:
            words[previous]["text"] += text
        elif following is not None:
            words[following]["text"] = text + words[following]["text"]
        else:
            raise ValueError("alignment line contains no positive-duration token")
        words.pop(index)
    return [word for word in words if word["text"]], merged


def _remap_approved_text(words: list[dict], approved: str) -> tuple[list[dict], bool]:
    aligned = "".join(word["text"] for word in words)
    if _without_space(aligned) != _without_space(approved):
        raise ValueError(f"alignment text differs from approved lyrics: {aligned!r} != {approved!r}")
    cursor = 0
    remapped: list[dict] = []
    for word in words:
        target_count = len(_without_space(word["text"]))
        begin = cursor
        consumed = 0
        while cursor < len(approved) and consumed < target_count:
            if not approved[cursor].isspace():
                consumed += 1
            cursor += 1
        if consumed != target_count:
            raise ValueError(f"unable to map alignment token {word['text']!r} into approved lyrics")
        remapped.append({"text": approved[begin:cursor], "start": word["start"], "end": word["end"]})
    if cursor < len(approved):
        remapped[-1]["text"] += approved[cursor:]
    return remapped, aligned != approved


def _repair_boundary(previous: dict, following: dict) -> dict:
    overlap = previous["end"] - following["start"]
    boundary = (previous["end"] + following["start"]) / 2
    previous_token = previous["tokens"][-1]
    following_token = following["tokens"][0]
    if not previous_token["start"] < boundary < following_token["end"]:
        raise ValueError("line overlap is too large for bounded boundary repair")
    previous_token["end"] = boundary
    following_token["start"] = boundary
    previous["end"] = boundary
    following["start"] = boundary
    return {"from": previous["id"], "to": following["id"], "overlap_seconds": round(overlap, 4)}


def approve_timing(
    project_dir: Path,
    track_id: str,
    alignment_path: Path,
    *,
    approved_by: str,
    note: str,
) -> dict:
    project_dir = project_dir.expanduser().resolve()
    manifest = load_project(project_dir)
    track = next((item for item in manifest.get("tracks", []) if item.get("track_id") == track_id), None)
    if not track or track.get("lyrics", {}).get("status") != "approved":
        raise PermissionError("timing requires an approved lyrics track")
    if not approved_by.strip() or not note.strip():
        raise ValueError("approved_by and note must not be blank")

    lyrics = json.loads((project_dir / track["lyrics"]["artifact"]).read_text(encoding="utf-8"))
    input_alignment_sha = hash_file(alignment_path)
    alignment = json.loads(alignment_path.read_text(encoding="utf-8"))
    segments = alignment.get("segments") or []
    if len(segments) != len(lyrics["lines"]):
        raise ValueError("approved lyrics and alignment segment counts differ")

    alignment_relative = Path("timing") / "alignment" / f"{track_id}.json"
    alignment_sha = write_immutable_json(project_dir / alignment_relative, alignment)
    lines: list[dict] = []
    zero_repairs: list[dict] = []
    text_repairs: list[str] = []
    for approved_line, segment in zip(lyrics["lines"], segments, strict=True):
        words, merged = _merge_zero_words(segment.get("words") or [])
        tokens, remapped = _remap_approved_text(words, approved_line["japanese"])
        if not tokens or any(token["end"] <= token["start"] for token in tokens):
            raise ValueError(f"{approved_line['id']} contains invalid token timing")
        line = {
            "id": approved_line["id"],
            "start": tokens[0]["start"],
            "end": tokens[-1]["end"],
            "japanese": approved_line["japanese"],
            "translation": approved_line.get("translation", ""),
            "tokens": tokens,
        }
        lines.append(line)
        if merged:
            zero_repairs.append({"line_id": line["id"], "merged_tokens": merged})
        if remapped:
            text_repairs.append(line["id"])

    boundary_repairs = [
        _repair_boundary(before, after)
        for before, after in zip(lines, lines[1:])
        if after["start"] < before["end"]
    ]
    for line in lines:
        for token in line["tokens"]:
            token["start"] = round(token["start"], 4)
            token["end"] = round(token["end"], 4)
        line["start"] = round(line["tokens"][0]["start"], 4)
        line["end"] = round(line["tokens"][-1]["end"], 4)
        if "".join(token["text"] for token in line["tokens"]) != line["japanese"]:
            raise AssertionError("reconciled tokens do not reproduce approved lyrics")

    timing = {"schema_version": 1, "track_id": track_id, "lines": lines}
    timing_relative = Path("timing") / "approved" / f"{track_id}.json"
    timing_sha = write_immutable_json(project_dir / timing_relative, timing)
    candidate = track.get("timing_candidate", {})
    candidate_matches = candidate.get("sha256") == input_alignment_sha
    evidence = record_evidence(project_dir, "timing-approval", {
        "alignment_artifact": alignment_relative.as_posix(),
        "alignment_sha256": alignment_sha,
        "input_alignment_sha256": input_alignment_sha,
        "alignment_parameters": {
            "tool": candidate.get("tool", "external") if candidate_matches else "external",
            "model": candidate.get("model", "unknown") if candidate_matches else alignment.get("model", "unknown"),
            "language": (
                candidate.get("language", "unknown")
                if candidate_matches
                else alignment.get("language", "unknown")
            ),
        },
        "approved_at": datetime.now(UTC).isoformat(),
        "approved_by": approved_by.strip(),
        "boundary_repairs": boundary_repairs,
        "note": note.strip(),
        "text_slot_repairs": text_repairs,
        "timing_sha256": timing_sha,
        "track_id": track_id,
        "zero_duration_repairs": zero_repairs,
        "unresolved_differences": [],
    }, directory="qa")
    timing_reference = {
        "status": "approved",
        "artifact": timing_relative.as_posix(),
        "sha256": timing_sha,
        "alignment_artifact": alignment_relative.as_posix(),
        "approval_evidence_id": evidence["id"],
    }
    track["timing"] = timing_reference
    if candidate_matches:
        track["timing_candidate"]["status"] = "approved"
    manifest.setdefault("evidence_artifacts", []).append(evidence)
    manifest["stage"] = "timing-approved"
    manifest["status"] = "timing-approved"
    save_project(project_dir, manifest)
    return timing_reference
