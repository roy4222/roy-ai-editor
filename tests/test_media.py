from pathlib import Path

import pytest

from roy_ai_editor.media import burn_ass, cut, download


def test_download_dry_run_uses_module_and_metadata(tmp_path: Path) -> None:
    command = download("https://youtu.be/example", tmp_path, dry_run=True)
    assert command[1:3] == ["-m", "yt_dlp"]
    assert "--write-info-json" in command


def test_cut_dry_run_is_exact_reencode(tmp_path: Path) -> None:
    command = cut(Path("source.mp4"), tmp_path / "song.mp4", 10.0, 20.5, dry_run=True)
    assert command[0] == "ffmpeg"
    assert "10.500" in command
    assert "libx264" in command


def test_cut_rejects_invalid_range(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        cut(Path("source.mp4"), tmp_path / "song.mp4", 5.0, 5.0, dry_run=True)


def test_burn_dry_run_uses_ass_filter(tmp_path: Path) -> None:
    command = burn_ass(Path("source.mp4"), Path("lyrics.ass"), tmp_path / "final.mp4", dry_run=True)
    assert any(part.startswith("subtitles=filename=") for part in command)
    assert command[command.index("-c:a") + 1] == "aac"
