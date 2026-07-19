import hashlib
import json
import os
import sys
from pathlib import Path

import pytest

from roy_ai_editor.project import DEFAULT_WORKSPACE, approve_rights, create_project, require_rights_approval, source_id


STANDARD_PROJECT_DIRECTORIES = {
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
}


def test_source_id_reads_youtube_urls() -> None:
    assert source_id("https://www.youtube.com/watch?v=x3nrUagsaV4") == "x3nrUagsaV4"
    assert source_id("https://youtu.be/x3nrUagsaV4") == "x3nrUagsaV4"


def test_default_workspace_uses_the_production_data_root() -> None:
    if sys.platform == "darwin":
        expected = Path("/Volumes/RoyMedia/RoyAIEditor/projects")
    elif os.name == "nt":
        expected = Path("D:/VideoProjects/RoyAIEditor/projects")
    else:
        expected = Path("/mnt/d/VideoProjects/RoyAIEditor/projects")
    assert DEFAULT_WORKSPACE == expected


def test_create_project_is_idempotent(tmp_path: Path) -> None:
    first_dir, first = create_project("https://youtu.be/x3nrUagsaV4", tmp_path)

    manifest_path = first_dir / "project.json"
    persisted = json.loads(manifest_path.read_text(encoding="utf-8"))
    persisted["operator_note"] = "preserve this current state"
    manifest_path.write_text(json.dumps(persisted), encoding="utf-8")

    second_dir, second = create_project("https://youtu.be/x3nrUagsaV4", tmp_path)

    assert first_dir == second_dir
    assert second["operator_note"] == "preserve this current state"
    assert manifest_path.exists()
    assert STANDARD_PROJECT_DIRECTORIES <= {
        str(path.relative_to(first_dir))
        for path in first_dir.rglob("*")
        if path.is_dir()
    }
    assert first["schema_version"] == 2
    assert first["workflow"] == "concert-live"
    assert first["stage"] == "intake"
    assert first["tracks"] == []
    assert first["evidence_artifacts"] == []
    assert first["approved_deliverables"] == []
    assert first["review_gates"] == {
        "rights": "pending",
        "lyrics": "pending",
        "edit": "pending",
        "publish": "pending",
    }


def test_rights_gate_requires_explicit_approval(tmp_path: Path) -> None:
    project_dir, _ = create_project("https://youtu.be/x3nrUagsaV4", tmp_path)
    with pytest.raises(PermissionError):
        require_rights_approval(project_dir)

    approve_rights(project_dir, evidence_url="https://example.com/policy", note="Roy approved")
    assert require_rights_approval(project_dir)["review_gates"]["rights"] == "approved"


def test_rights_approval_rejects_blank_and_preserves_history(tmp_path: Path) -> None:
    project_dir, _ = create_project("https://youtu.be/x3nrUagsaV4", tmp_path)
    with pytest.raises(ValueError):
        approve_rights(project_dir, evidence_url="", note="")

    first = approve_rights(project_dir, evidence_url="https://example.com/policy", note="First review")
    second = approve_rights(project_dir, evidence_url="https://example.com/update", note="Updated review")
    assert len(first["rights"]["approvals"]) == 1
    assert len(second["rights"]["approvals"]) == 2
    assert second["rights"]["approvals"][0]["note"] == "First review"


def test_rights_approval_creates_content_verified_evidence(tmp_path: Path) -> None:
    project_dir, _ = create_project("https://youtu.be/x3nrUagsaV4", tmp_path)

    manifest = approve_rights(
        project_dir,
        evidence_url="https://example.com/policy",
        note="Roy approved",
    )

    reference = manifest["evidence_artifacts"][-1]
    evidence_path = project_dir / reference["path"]
    content = evidence_path.read_bytes()
    assert reference["id"].startswith("evidence-")
    assert reference["kind"] == "rights-approval"
    assert hashlib.sha256(content).hexdigest() == reference["sha256"]
    assert json.loads(content)["approved_by"] == "Roy"
