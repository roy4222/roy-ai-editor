"""Approve trusted lyric packets as traceable Media Project tracks."""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse

from .project import record_evidence, require_rights_approval, save_project, write_immutable_json


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
        "source_url": packet["source"]["url"],
        "track_id": track_id,
    }
    evidence = record_evidence(project_dir, "lyrics-approval", approval)
    track = {
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

    tracks = [existing for existing in manifest.get("tracks", []) if existing.get("track_id") != track_id]
    tracks.append(track)
    manifest["tracks"] = sorted(tracks, key=lambda item: item["number"])
    manifest.setdefault("evidence_artifacts", []).append(evidence)
    manifest["review_gates"]["lyrics"] = "approved"
    manifest["stage"] = "lyrics-approved"
    manifest["status"] = "lyrics-approved"
    save_project(project_dir, manifest)
    return track
