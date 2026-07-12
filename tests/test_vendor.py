from roy_ai_editor.cli import VENDORED_AUTOPILOT_COMMIT, _vendor_dir, _vendor_is_complete


def test_vendored_autopilot_snapshot_is_complete_and_pinned() -> None:
    vendor = _vendor_dir()
    assert _vendor_is_complete()
    assert (vendor / "LICENSE").is_file()
    assert (vendor / "README.md").is_file()
    assert (vendor / "VENDORED_COMMIT").read_text(encoding="utf-8").strip() == VENDORED_AUTOPILOT_COMMIT
