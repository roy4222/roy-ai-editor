"""Locate or install roy-ai-editor for the Codex skill."""

from __future__ import annotations

import argparse
import os
import subprocess
from pathlib import Path

REPOSITORY = "https://github.com/roy4222/roy-ai-editor.git"
RELEASE = "v0.2.0"
AUTOPILOT_COMMIT = "f15a5f99d58cbaedffb2590e76218bb85765331c"


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
    marker = path / "vendor" / "video-autopilot-kit" / "VENDORED_COMMIT"
    return (
        (path / "pyproject.toml").exists()
        and (path / "skills" / "roy-edit-concert-live" / "SKILL.md").exists()
        and (path / "vendor" / "video-autopilot-kit" / "LICENSE").exists()
        and marker.exists()
        and marker.read_text(encoding="utf-8").strip() == AUTOPILOT_COMMIT
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
        raise RuntimeError("Installed release failed the Skill/vendor integrity check")
    print(args.destination.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
