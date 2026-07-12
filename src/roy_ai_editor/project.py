"""Project manifests and external workspace layout."""

from __future__ import annotations

import json
import os
import re
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import parse_qs, urlparse

DEFAULT_WORKSPACE = Path(
    os.environ.get(
        "ROY_EDITOR_WORKSPACE",
        "/mnt/d/VideoProjects/roy-ai-editor/projects",
    )
)


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
    for child in ("source", "lyrics", "timing", "subtitles", "renders", "qa", "publish"):
        (project_dir / child).mkdir(parents=True, exist_ok=True)

    manifest_path = project_dir / "project.json"
    if manifest_path.exists():
        return project_dir, json.loads(manifest_path.read_text(encoding="utf-8"))

    manifest = {
        "schema_version": 1,
        "project_id": project_dir.name,
        "source_url": url,
        "created_at": datetime.now(UTC).isoformat(),
        "status": "intake",
        "rights": {"status": "pending", "evidence": []},
        "tracks": [],
        "review_gates": {
            "rights": "pending",
            "edit": "pending",
            "publish": "pending",
        },
    }
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
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
    approvals.append(
        {
            "approved_at": datetime.now(UTC).isoformat(),
            "approved_by": approved_by.strip(),
            "evidence_url": evidence_url.strip(),
            "note": note.strip(),
        }
    )
    rights.update({
        "status": "approved",
        "evidence": [*rights.get("evidence", []), {"url": evidence_url.strip(), "note": note.strip()}],
        "latest_approval": approvals[-1],
    })
    manifest["review_gates"]["rights"] = "approved"
    manifest["status"] = "rights-approved"
    (project_dir / "project.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest


def require_rights_approval(project_dir: Path) -> dict:
    manifest = load_project(project_dir)
    if manifest.get("review_gates", {}).get("rights") != "approved":
        raise PermissionError(
            "Rights gate is not approved. Run `roy-editor concert approve-rights` "
            "after Roy reviews the saved evidence."
        )
    return manifest
