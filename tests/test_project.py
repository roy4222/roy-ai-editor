from pathlib import Path

import pytest

from roy_ai_editor.project import approve_rights, create_project, require_rights_approval, source_id


def test_source_id_reads_youtube_urls() -> None:
    assert source_id("https://www.youtube.com/watch?v=x3nrUagsaV4") == "x3nrUagsaV4"
    assert source_id("https://youtu.be/x3nrUagsaV4") == "x3nrUagsaV4"


def test_create_project_is_idempotent(tmp_path: Path) -> None:
    first_dir, first = create_project("https://youtu.be/x3nrUagsaV4", tmp_path)
    second_dir, second = create_project("https://youtu.be/x3nrUagsaV4", tmp_path)

    assert first_dir == second_dir
    assert first == second
    assert (first_dir / "project.json").exists()
    assert (first_dir / "subtitles").is_dir()


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
