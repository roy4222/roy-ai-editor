"""Project manifests and external workspace layout."""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import parse_qs, urlparse

DEFAULT_WORKSPACE = Path(
    os.environ.get(
        "ROY_EDITOR_WORKSPACE",
        "/mnt/d/VideoProjects/RoyAIEditor/projects",
    )
)

STANDARD_PROJECT_DIRECTORIES = (
    "videos/source",
    "videos/clips",
    "videos/review",
    "videos/approved",
    "videos/archive",
    "lyrics/sources",
    "lyrics/approved",
    "timing/alignment",
    "timing/approved",
    "subtitles/draft",
    "subtitles/approved",
    "subtitles/archive",
    "approvals",
    "qa",
    "publish",
    "work",
)


def _json_bytes(payload: object) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _write_json_atomic(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = _json_bytes(payload)
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp", delete=False) as handle:
            temp_path = Path(handle.name)
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
    finally:
        if temp_path and temp_path.exists():
            temp_path.unlink()


def write_immutable_json(path: Path, payload: object) -> str:
    data = _json_bytes(payload)
    digest = hashlib.sha256(data).hexdigest()
    if path.exists():
        if path.read_bytes() != data:
            raise RuntimeError(f"Immutable artifact already exists with different content: {path}")
    else:
        _write_json_atomic(path, payload)
    return digest


def record_evidence(project_dir: Path, kind: str, payload: object, *, directory: str = "approvals") -> dict:
    data = _json_bytes(payload)
    digest = hashlib.sha256(data).hexdigest()
    relative_path = Path(directory) / f"{kind}-{digest[:16]}.json"
    evidence_path = project_dir / relative_path
    write_immutable_json(evidence_path, payload)
    return {
        "id": f"evidence-{digest[:16]}",
        "kind": kind,
        "path": relative_path.as_posix(),
        "sha256": digest,
    }


def save_project(project_dir: Path, manifest: dict) -> None:
    _write_json_atomic(project_dir.expanduser().resolve() / "project.json", manifest)


def source_id(url: str) -> str:
    parsed = urlparse(url)
    if parsed.hostname in {"youtu.be", "www.youtu.be"}:
        candidate = parsed.path.strip("/")
    else:
        candidate = parse_qs(parsed.query).get("v", [""])[0]
    if candidate and re.fullmatch(r"[A-Za-z0-9_-]{6,64}", candidate):
        return candidate
    fallback = re.sub(r"[^a-z0-9]+", "-", parsed.netloc + parsed.path, flags=re.I)
    return fallback.strip("-").lower()[:64] or "concert"


def create_project(url: str, workspace: Path | None = None) -> tuple[Path, dict]:
    root = (workspace or DEFAULT_WORKSPACE).expanduser().resolve()
    project_dir = root / source_id(url)
    for child in STANDARD_PROJECT_DIRECTORIES:
        (project_dir / child).mkdir(parents=True, exist_ok=True)

    manifest_path = project_dir / "project.json"
    if manifest_path.exists():
        return project_dir, json.loads(manifest_path.read_text(encoding="utf-8"))

    manifest = {
        "schema_version": 2,
        "project_id": project_dir.name,
        "workflow": "concert-live",
        "source_url": url,
        "created_at": datetime.now(UTC).isoformat(),
        "stage": "intake",
        "status": "intake",
        "rights": {"status": "pending", "evidence": []},
        "tracks": [],
        "evidence_artifacts": [],
        "approved_deliverables": [],
        "review_gates": {
            "rights": "pending",
            "lyrics": "pending",
            "edit": "pending",
            "publish": "pending",
        },
    }
    _write_json_atomic(manifest_path, manifest)
    return project_dir, manifest


def load_project(project_dir: Path) -> dict:
    manifest_path = project_dir.expanduser().resolve() / "project.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Project manifest not found: {manifest_path}")
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def approve_rights(
    project_dir: Path,
    *,
    evidence_url: str,
    note: str,
    approved_by: str = "Roy",
) -> dict:
    project_dir = project_dir.expanduser().resolve()
    manifest = load_project(project_dir)
    parsed = urlparse(evidence_url.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("evidence_url must be a non-empty HTTP(S) URL")
    if not note.strip():
        raise ValueError("approval note must not be blank")
    if not approved_by.strip():
        raise ValueError("approved_by must not be blank")

    rights = manifest.setdefault("rights", {"status": "pending", "evidence": []})
    approvals = rights.setdefault("approvals", [])
    approval = {
        "approved_at": datetime.now(UTC).isoformat(),
        "approved_by": approved_by.strip(),
        "evidence_url": evidence_url.strip(),
        "note": note.strip(),
    }
    reference = record_evidence(project_dir, "rights-approval", approval)
    approvals.append(approval)
    rights.update({
        "status": "approved",
        "evidence": [*rights.get("evidence", []), reference],
        "latest_approval": approvals[-1],
    })
    manifest.setdefault("evidence_artifacts", []).append(reference)
    manifest["review_gates"]["rights"] = "approved"
    manifest["stage"] = "rights-approved"
    manifest["status"] = "rights-approved"
    save_project(project_dir, manifest)
    return manifest


def require_rights_approval(project_dir: Path) -> dict:
    manifest = load_project(project_dir)
    if manifest.get("review_gates", {}).get("rights") != "approved":
        raise PermissionError(
            "Rights gate is not approved. Run `roy-editor concert approve-rights` "
            "after Roy reviews the saved evidence."
        )
    return manifest
