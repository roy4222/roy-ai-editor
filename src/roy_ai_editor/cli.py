"""Command-line entry point for Roy AI Editor."""

from __future__ import annotations

import argparse
from collections.abc import Sequence


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="roy-editor",
        description="Local-first AI video editing workflows.",
    )
    parser.add_argument("--version", action="version", version="%(prog)s 0.1.0")

    subcommands = parser.add_subparsers(dest="command")
    concert = subcommands.add_parser(
        "concert",
        help="Create review-ready song clips from a concert or live stream.",
    )
    concert.add_argument(
        "url",
        nargs="?",
        help="Source video URL. Execution is not implemented in V0 yet.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "concert":
        parser.error("concert workflow is scaffolded but not implemented yet")
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
