import json
from pathlib import Path

from roy_ai_editor.cli import build_parser, main
from roy_ai_editor.project import approve_rights, create_project


def test_parser_exposes_concert_create_workflow() -> None:
    args = build_parser().parse_args(["concert", "create", "https://example.com/live"])
    assert args.command == "concert"
    assert args.concert_command == "create"
    assert args.url == "https://example.com/live"


def test_cli_creates_a_standard_media_project(tmp_path: Path, capsys) -> None:
    assert main([
        "concert",
        "create",
        "https://youtu.be/x3nrUagsaV4",
        "--workspace",
        str(tmp_path),
    ]) == 0

    output = json.loads(capsys.readouterr().out)
    project_dir = Path(output["project_dir"])
    assert output["manifest"]["schema_version"] == 2
    assert (project_dir / "videos" / "approved").is_dir()
    assert (project_dir / "subtitles" / "archive").is_dir()
    assert (project_dir / "approvals").is_dir()
    assert not (project_dir / "renders").exists()


def test_root_command_prints_help(capsys) -> None:
    assert main([]) == 0
    assert "Local-first AI video editing workflows" in capsys.readouterr().out


def test_download_requires_project_and_supports_approved_dry_run(tmp_path: Path, capsys) -> None:
    project_dir, _ = create_project("https://youtu.be/x3nrUagsaV4", tmp_path)
    approve_rights(project_dir, evidence_url="https://example.com/policy", note="Roy approved")

    assert main(["download", str(project_dir), "--dry-run"]) == 0
    command = json.loads(capsys.readouterr().out)
    assert command[-1] == "https://youtu.be/x3nrUagsaV4"
