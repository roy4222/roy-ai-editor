"""Approve trusted lyric packets as traceable Media Project tracks."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse

from .project import record_evidence, require_rights_approval, save_project, write_immutable_json

APPROVABLE_REUSE_STATUSES = {"approved", "approved-for-test", "user-provided-approved"}


def _validate_packet(packet: dict) -> tuple[int, str]:
    if packet.get("packet_version") != 1:
        raise ValueError("lyrics packet_version must be 1")
    track_number = packet.get("track_number")
    if not isinstance(track_number, int) or not 1 <= track_number <= 999:
        raise ValueError("track_number must be an integer from 1 to 999")
    slug = packet.get("slug", "")
    if not isinstance(slug, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
        raise ValueError("slug must contain lowercase letters, numbers, and single hyphens")
    if not str(packet.get("title", "")).strip():
        raise ValueError("lyrics packet title must not be blank")

    source_url = str(packet.get("source", {}).get("url", ""))
    parsed = urlparse(source_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("lyrics packet requires an HTTP(S) source URL")

    lines = packet.get("lines")
    if not isinstance(lines, list) or not lines:
        raise ValueError("lyrics packet requires at least one line")
    line_ids = [line.get("id") for line in lines if isinstance(line, dict)]
    if len(line_ids) != len(lines) or len(set(line_ids)) != len(lines):
        raise ValueError("lyrics packet line IDs must be present and unique")
    if any(not re.fullmatch(r"L\d{3,}", str(line_id)) for line_id in line_ids):
        raise ValueError("lyrics packet line IDs must use the L001 format")
    if any(not str(line.get("japanese", "")).strip() for line in lines):
        raise ValueError("every lyrics line requires Japanese source text")
    return track_number, slug


def _validate_source_metadata(packet: dict, *, require_approvable: bool) -> None:
    source = packet.get("source", {})
    if not str(source.get("captured_at", "")).strip():
        raise ValueError("lyrics packet source requires captured_at")
    if not isinstance(source.get("rights_warnings"), list):
        raise ValueError("lyrics packet source requires rights_warnings as a list")
    reuse_status = str(source.get("reuse_status", "")).strip()
    if require_approvable and reuse_status not in APPROVABLE_REUSE_STATUSES:
        raise PermissionError("lyrics packet reuse status is not approvable")


def prepare_lyrics_packet(project_dir: Path, packet_path: Path) -> dict:
    project_dir = project_dir.expanduser().resolve()
    manifest = require_rights_approval(project_dir)
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    packet.setdefault("source", {}).setdefault("captured_at", datetime.now(UTC).isoformat())
    track_number, slug = _validate_packet(packet)
    _validate_source_metadata(packet, require_approvable=False)
    track_id = f"{track_number:03d}-{slug}"
    packet_bytes = (
        json.dumps(packet, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    packet_sha = hashlib.sha256(packet_bytes).hexdigest()
    relative = Path("lyrics") / "sources" / f"{track_id}-{packet_sha[:16]}.json"
    write_immutable_json(project_dir / relative, packet)
    reuse_status = str(packet["source"].get("reuse_status", "")).strip()
    status = "review-required" if reuse_status in APPROVABLE_REUSE_STATUSES else "blocked"
    evidence = record_evidence(project_dir, "lyrics-packet-prepared", {
        "created_at": datetime.now(UTC).isoformat(),
        "track_id": track_id,
        "artifact": relative.as_posix(),
        "sha256": packet_sha,
        "source_url": packet["source"]["url"],
        "captured_at": packet["source"]["captured_at"],
        "reuse_status": reuse_status,
        "rights_warnings": packet["source"]["rights_warnings"],
    })
    candidate = {
        "status": status,
        "artifact": relative.as_posix(),
        "sha256": packet_sha,
        "captured_at": packet["source"]["captured_at"],
        "reuse_status": reuse_status,
        "rights_warnings": packet["source"]["rights_warnings"],
        "evidence_id": evidence["id"],
    }
    track = next((item for item in manifest.get("tracks", []) if item.get("track_id") == track_id), None)
    if track is None:
        track = {
            "track_id": track_id,
            "number": track_number,
            "slug": slug,
            "title": packet["title"],
        }
        manifest.setdefault("tracks", []).append(track)
        manifest["tracks"].sort(key=lambda item: item["number"])
    track["lyrics_candidate"] = candidate
    manifest.setdefault("evidence_artifacts", []).append(evidence)
    manifest["stage"] = "lyrics-review-required" if status == "review-required" else "lyrics-blocked"
    manifest["status"] = manifest["stage"]
    save_project(project_dir, manifest)
    return candidate


def approve_lyrics(
    project_dir: Path,
    packet_path: Path,
    *,
    approved_by: str,
    note: str,
) -> dict:
    project_dir = project_dir.expanduser().resolve()
    manifest = require_rights_approval(project_dir)
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    track_number, slug = _validate_packet(packet)
    _validate_source_metadata(packet, require_approvable=True)
    if not approved_by.strip() or not note.strip():
        raise ValueError("approved_by and note must not be blank")

    track_id = f"{track_number:03d}-{slug}"
    relative_artifact = Path("lyrics") / "approved" / f"{track_id}.json"
    lyrics_sha = write_immutable_json(project_dir / relative_artifact, packet)
    approval = {
        "approved_at": datetime.now(UTC).isoformat(),
        "approved_by": approved_by.strip(),
        "kind": "lyrics-approval",
        "note": note.strip(),
        "packet_sha256": lyrics_sha,
        "captured_at": packet["source"]["captured_at"],
        "reuse_status": packet["source"]["reuse_status"],
        "rights_warnings": packet["source"]["rights_warnings"],
        "source_url": packet["source"]["url"],
        "track_id": track_id,
    }
    evidence = record_evidence(project_dir, "lyrics-approval", approval)
    existing_track = next(
        (item for item in manifest.get("tracks", []) if item.get("track_id") == track_id),
        None,
    )
    track = {
        **(existing_track or {}),
        "track_id": track_id,
        "number": track_number,
        "slug": slug,
        "title": packet["title"],
        "lyrics": {
            "status": "approved",
            "artifact": relative_artifact.as_posix(),
            "sha256": lyrics_sha,
            "approval_evidence_id": evidence["id"],
        },
    }
    if existing_track and "lyrics_candidate" in existing_track:
        track["lyrics_candidate"] = {**existing_track["lyrics_candidate"], "status": "approved"}

    tracks = [existing for existing in manifest.get("tracks", []) if existing.get("track_id") != track_id]
    tracks.append(track)
    manifest["tracks"] = sorted(tracks, key=lambda item: item["number"])
    manifest.setdefault("evidence_artifacts", []).append(evidence)
    all_tracks_approved = bool(manifest["tracks"]) and all(
        item.get("lyrics", {}).get("status") == "approved" for item in manifest["tracks"]
    )
    manifest["review_gates"]["lyrics"] = "approved" if all_tracks_approved else "pending"
    manifest["stage"] = "lyrics-approved" if all_tracks_approved else "partially-lyrics-approved"
    manifest["status"] = manifest["stage"]
    save_project(project_dir, manifest)
    return track
