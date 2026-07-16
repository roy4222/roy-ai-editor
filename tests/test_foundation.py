import importlib
from pathlib import Path

from roy_ai_editor.cli import main


REPO_ROOT = Path(__file__).resolve().parents[1]
FOUNDATION_MODULES = (
    "capcut_helpers",
    "longform_maker",
    "silent_vlog_maker",
    "platform_compat",
)


def test_autopilot_cli_locates_root_foundation(capsys) -> None:
    assert main(["autopilot", "--path-only"]) == 0

    foundation = Path(capsys.readouterr().out.strip()).resolve()
    assert foundation == REPO_ROOT
    assert (foundation / "SETUP.md").is_file()
    assert (foundation / "src" / "capcut_helpers").is_dir()
    assert not (foundation / "vendor" / "video-autopilot-kit").exists()


def test_root_foundation_modules_are_importable() -> None:
    for module_name in FOUNDATION_MODULES:
        assert importlib.import_module(module_name) is not None


def test_doctor_reports_upstream_foundation(capsys) -> None:
    assert main(["doctor"]) == 0
    output = capsys.readouterr().out
    assert "upstream foundation" in output
    assert "vendored video-autopilot-kit" not in output


def test_upstream_mit_attribution_is_preserved() -> None:
    license_text = (REPO_ROOT / "LICENSE").read_text(encoding="utf-8")
    notices = (REPO_ROOT / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")

    assert "Copyright (c) 2026 Hao0321 Studio" in license_text
    assert "fd45f0e876219d98fbcba11a38a8513b88309bdf" in notices
    assert "repository root" in notices
