#!/usr/bin/env python3
"""Fail closed when repository-only policy boundaries are violated."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path


UPSTREAM_FOUNDATION_COMMIT = "fd45f0e876219d98fbcba11a38a8513b88309bdf"
ROY_BASE_COMMIT = "57a663273bc309e1548825169b11a5c68f8f4109"
UPSTREAM_LICENSE_SHA256 = "7f29ea8ecc9473502a2d3c70c0931dce2c5543ce7f2bd154d654f9844aad5f07"
MAX_TRACKED_FILE_BYTES = 10 * 1024 * 1024
PRODUCTION_MEDIA_EXTENSIONS = {
    ".7z", ".ass", ".flac", ".gif", ".gz", ".jpeg", ".jpg", ".m4a",
    ".mkv", ".mov", ".mp3", ".mp4", ".png", ".srt", ".tar", ".vtt",
    ".wav", ".webm", ".zip",
}
SECRET_PATTERNS = {
    "aws-access-key": re.compile(r"AKIA[0-9A-Z]{16}"),
    "github-token": re.compile(r"(?:github_pat_[A-Za-z0-9_]{20,}|gh[pousr]_[A-Za-z0-9]{20,})"),
    "private-key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "openai-style-key": re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
}


def _git(repo: Path, *arguments: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", *arguments],
        cwd=repo,
        check=False,
        capture_output=True,
    )


def _is_private_path(path: Path) -> bool:
    text = path.as_posix()
    return (
        text == "config.py"
        or text == ".env"
        or text.startswith(".env.")
        or text.startswith("profiles/private/")
        or "/private/" in text
        or ".local." in path.name
    )


def main() -> int:
    repo = Path(__file__).resolve().parents[1]
    errors: list[str] = []
    for label, commit in (
        ("upstream foundation", UPSTREAM_FOUNDATION_COMMIT),
        ("Roy base", ROY_BASE_COMMIT),
    ):
        result = _git(repo, "merge-base", "--is-ancestor", commit, "HEAD")
        if result.returncode != 0:
            errors.append(f"missing required {label} ancestor: {commit}")

    tracked_result = _git(repo, "ls-files", "-z")
    if tracked_result.returncode != 0:
        errors.append("unable to enumerate tracked files")
        tracked: list[Path] = []
    else:
        tracked = [Path(item.decode()) for item in tracked_result.stdout.split(b"\0") if item]

    largest_file_bytes = 0
    for relative in tracked:
        path = repo / relative
        if not path.is_file():
            continue
        size = path.stat().st_size
        largest_file_bytes = max(largest_file_bytes, size)
        if size >= MAX_TRACKED_FILE_BYTES:
            errors.append(f"tracked file is at least 10 MiB: {relative} ({size} bytes)")
        if relative.suffix.lower() in PRODUCTION_MEDIA_EXTENSIONS:
            errors.append(f"production media must stay outside Git: {relative}")
        if _is_private_path(relative):
            errors.append(f"private/local path is tracked: {relative}")

        content = path.read_bytes()
        if b"\0" in content:
            continue
        text = content.decode("utf-8", errors="ignore")
        for label, pattern in SECRET_PATTERNS.items():
            if pattern.search(text):
                errors.append(f"possible {label} in tracked file: {relative}")

    license_path = repo / "LICENSES" / "video-autopilot-kit-MIT.txt"
    if not license_path.is_file():
        errors.append("upstream MIT license copy is missing")
    elif hashlib.sha256(license_path.read_bytes()).hexdigest() != UPSTREAM_LICENSE_SHA256:
        errors.append("upstream MIT license copy differs from the pinned upstream commit")

    report = {
        "status": "passed" if not errors else "failed",
        "tracked_files": len(tracked),
        "largest_file_bytes": largest_file_bytes,
        "required_ancestors": [UPSTREAM_FOUNDATION_COMMIT, ROY_BASE_COMMIT],
        "errors": errors,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
