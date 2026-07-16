"""Locate or install roy-ai-editor for the Codex skill."""

from __future__ import annotations

import argparse
import os
import subprocess
from pathlib import Path

REPOSITORY = "https://github.com/roy4222/roy-ai-editor.git"
RELEASE = "main"
FOUNDATION_COMMIT = "fd45f0e876219d98fbcba11a38a8513b88309bdf"


def candidates() -> list[Path]:
    values: list[Path] = []
    if configured := os.environ.get("ROY_AI_EDITOR_REPO"):
        values.append(Path(configured))
    values.extend(
        [
            Path.cwd(),
            Path.home() / "newLife" / "roy-ai-editor",
            Path.home() / ".local" / "share" / "roy-ai-editor",
        ]
    )
    return values


def is_repo(path: Path) -> bool:
    notices = path / "THIRD_PARTY_NOTICES.md"
    return (
        (path / "pyproject.toml").exists()
        and (path / "skills" / "roy-edit-concert-live" / "SKILL.md").exists()
        and (path / "SETUP.md").exists()
        and (path / "src" / "capcut_helpers").is_dir()
        and (path / "src" / "longform_maker").is_dir()
        and (path / "src" / "silent_vlog_maker").is_dir()
        and notices.exists()
        and FOUNDATION_COMMIT in notices.read_text(encoding="utf-8")
    )


def find_repo() -> Path | None:
    return next((path.resolve() for path in candidates() if is_repo(path)), None)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--install", action="store_true", help="Clone the public repository when it is missing.")
    parser.add_argument("--destination", type=Path, default=Path.home() / ".local" / "share" / "roy-ai-editor")
    args = parser.parse_args()

    if repo := find_repo():
        print(repo)
        return 0
    if not args.install:
        parser.error("roy-ai-editor was not found; rerun with --install after user approval")
    if args.destination.exists():
        parser.error(f"destination already exists but is not a valid repo: {args.destination}")
    args.destination.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["git", "clone", "--branch", RELEASE, "--depth", "1", REPOSITORY, str(args.destination)],
        check=True,
    )
    if not is_repo(args.destination):
        raise RuntimeError("Installed release failed the Skill/foundation integrity check")
    print(args.destination.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
