"""Deterministic yt-dlp and FFmpeg adapters."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path


class MissingToolError(RuntimeError):
    pass


def require_tool(name: str) -> str:
    path = shutil.which(name)
    if path is None:
        raise MissingToolError(f"Required executable is not on PATH: {name}")
    return path


def run(command: list[str], *, dry_run: bool = False) -> subprocess.CompletedProcess[str] | list[str]:
    if dry_run:
        return command
    return subprocess.run(command, check=True, text=True, capture_output=True)


def download(url: str, output_dir: Path, *, dry_run: bool = False):
    output_dir.mkdir(parents=True, exist_ok=True)
    command = [
        sys.executable,
        "-m",
        "yt_dlp",
        "--no-playlist",
        "--write-info-json",
        "--write-thumbnail",
        "--merge-output-format",
        "mp4",
        "-o",
        str(output_dir / "source.%(ext)s"),
        url,
    ]
    return run(command, dry_run=dry_run)


def cut(
    source: Path,
    output: Path,
    start: float,
    end: float,
    *,
    stream_copy: bool = False,
    dry_run: bool = False,
):
    if end <= start:
        raise ValueError("end must be greater than start")
    ffmpeg = require_tool("ffmpeg") if not dry_run else "ffmpeg"
    output.parent.mkdir(parents=True, exist_ok=True)
    command = [ffmpeg, "-hide_banner", "-y", "-ss", f"{start:.3f}", "-i", str(source)]
    command += ["-t", f"{end - start:.3f}"]
    if stream_copy:
        command += ["-c", "copy"]
    else:
        command += [
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "18",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-movflags",
            "+faststart",
        ]
    command.append(str(output))
    return run(command, dry_run=dry_run)


def _filter_path(path: Path) -> str:
    value = str(path.resolve()).replace("\\", "/")
    return value.replace(":", "\\:").replace("'", "\\'")


def burn_ass(source: Path, subtitles: Path, output: Path, *, dry_run: bool = False):
    ffmpeg = require_tool("ffmpeg") if not dry_run else "ffmpeg"
    output.parent.mkdir(parents=True, exist_ok=True)
    command = [
        ffmpeg,
        "-hide_banner",
        "-y",
        "-i",
        str(source),
        "-vf",
        f"subtitles=filename='{_filter_path(subtitles)}'",
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-crf",
        "18",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-movflags",
        "+faststart",
        str(output),
    ]
    return run(command, dry_run=dry_run)


def probe(path: Path) -> dict:
    ffprobe = require_tool("ffprobe")
    result = run(
        [
            ffprobe,
            "-v",
            "error",
            "-show_format",
            "-show_streams",
            "-of",
            "json",
            str(path),
        ]
    )
    assert isinstance(result, subprocess.CompletedProcess)
    return json.loads(result.stdout)
