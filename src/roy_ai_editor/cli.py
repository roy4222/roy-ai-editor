"""Command-line entry point for Roy AI Editor."""

from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
from collections.abc import Sequence
from pathlib import Path

from . import media
from .alignment import transcribe
from .customization import concert_live_status
from .karaoke import render_file
from .lyrics import approve_lyrics
from .project import DEFAULT_WORKSPACE, approve_rights, create_project, load_project, require_rights_approval

UPSTREAM_FOUNDATION_COMMIT = "fd45f0e876219d98fbcba11a38a8513b88309bdf"
FOUNDATION_MODULES = (
    "capcut_helpers",
    "longform_maker",
    "silent_vlog_maker",
    "platform_compat",
)


def _foundation_root() -> Path:
    checkout = Path(__file__).resolve().parents[2]
    if (checkout / "SETUP.md").is_file():
        return checkout

    capcut_spec = importlib.util.find_spec("capcut_helpers")
    if capcut_spec and capcut_spec.origin:
        return Path(capcut_spec.origin).resolve().parents[1]
    return checkout


def _foundation_is_complete() -> bool:
    return all(importlib.util.find_spec(module_name) is not None for module_name in FOUNDATION_MODULES)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="roy-editor", description="Local-first AI video editing workflows.")
    parser.add_argument("--version", action="version", version="%(prog)s 0.2.0")
    commands = parser.add_subparsers(dest="command")

    commands.add_parser("doctor", help="Check required executables and the Upstream Foundation.")

    concert = commands.add_parser("concert", help="Create a review-gated concert project.")
    concert_commands = concert.add_subparsers(dest="concert_command")
    create = concert_commands.add_parser("create", help="Create a project manifest from a concert URL.")
    create.add_argument("url")
    create.add_argument("--workspace", type=Path, default=DEFAULT_WORKSPACE)
    approve = concert_commands.add_parser("approve-rights", help="Record Roy's explicit rights approval.")
    approve.add_argument("project", type=Path)
    approve.add_argument("--evidence-url", required=True)
    approve.add_argument("--note", required=True)
    approve.add_argument("--approved-by", default="Roy")
    lyrics = concert_commands.add_parser("approve-lyrics", help="Approve a versioned lyrics packet as a track.")
    lyrics.add_argument("project", type=Path)
    lyrics.add_argument("packet", type=Path)
    lyrics.add_argument("--approved-by", default="Roy")
    lyrics.add_argument("--note", required=True)

    workflow = commands.add_parser("workflow", help="Inspect or run a versioned Editing Workflow.")
    workflow_commands = workflow.add_subparsers(dest="workflow_command")
    concert_live = workflow_commands.add_parser("concert-live", help="Inspect a Concert Live Media Project.")
    concert_live.add_argument("project", type=Path)

    download = commands.add_parser("download", help="Download an approved project's source with yt-dlp.")
    download.add_argument("project", type=Path)
    download.add_argument("--dry-run", action="store_true")

    cut = commands.add_parser("cut", help="Cut an exact song segment with FFmpeg.")
    cut.add_argument("source", type=Path)
    cut.add_argument("output", type=Path)
    cut.add_argument("--start", type=float, required=True)
    cut.add_argument("--end", type=float, required=True)
    cut.add_argument("--stream-copy", action="store_true")
    cut.add_argument("--dry-run", action="store_true")

    karaoke = commands.add_parser("karaoke", help="Render or burn bilingual ASS karaoke subtitles.")
    karaoke_commands = karaoke.add_subparsers(dest="karaoke_command")
    render = karaoke_commands.add_parser("render", help="Render ASS from a timing JSON file.")
    render.add_argument("timing", type=Path)
    render.add_argument("output", type=Path)
    render.add_argument("--font", default="Noto Sans CJK JP")
    burn = karaoke_commands.add_parser("burn", help="Burn an ASS subtitle file into a video.")
    burn.add_argument("source", type=Path)
    burn.add_argument("subtitles", type=Path)
    burn.add_argument("output", type=Path)
    burn.add_argument("--dry-run", action="store_true")

    align = commands.add_parser("align", help="Create stable-ts word timestamps (optional extra).")
    align.add_argument("audio", type=Path)
    align.add_argument("output", type=Path)
    align.add_argument("--model", default="large-v3")
    align.add_argument("--language", default="ja")

    autopilot = commands.add_parser("autopilot", help="Locate the installed Upstream Foundation.")
    autopilot.add_argument("--path-only", action="store_true")

    probe = commands.add_parser("probe", help="Print FFprobe JSON for an output file.")
    probe.add_argument("path", type=Path)
    return parser


def _print_command(result: object) -> None:
    if isinstance(result, list):
        print(json.dumps(result, ensure_ascii=False, indent=2))


def _doctor() -> int:
    checks = {
        "ffmpeg": shutil.which("ffmpeg"),
        "ffprobe": shutil.which("ffprobe"),
        "yt-dlp module": True,
        "pykakasi": True,
        "upstream foundation": _foundation_is_complete(),
    }
    try:
        import yt_dlp  # noqa: F401
    except ImportError:
        checks["yt-dlp module"] = False
    try:
        import pykakasi  # noqa: F401
    except ImportError:
        checks["pykakasi"] = False

    for name, value in checks.items():
        print(f"{'OK' if value else 'MISSING':7} {name}" + (f": {value}" if isinstance(value, str) else ""))
    return 0 if all(checks.values()) else 1


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "doctor":
        return _doctor()
    if args.command == "concert" and args.concert_command == "create":
        project_dir, manifest = create_project(args.url, args.workspace)
        print(json.dumps({"project_dir": str(project_dir), "manifest": manifest}, ensure_ascii=False, indent=2))
        return 0
    if args.command == "concert" and args.concert_command == "approve-rights":
        manifest = approve_rights(
            args.project,
            evidence_url=args.evidence_url,
            note=args.note,
            approved_by=args.approved_by,
        )
        print(json.dumps(manifest["rights"], ensure_ascii=False, indent=2))
        return 0
    if args.command == "concert" and args.concert_command == "approve-lyrics":
        track = approve_lyrics(
            args.project,
            args.packet,
            approved_by=args.approved_by,
            note=args.note,
        )
        print(json.dumps(track, ensure_ascii=False, indent=2))
        return 0
    if args.command == "workflow" and args.workflow_command == "concert-live":
        print(json.dumps(concert_live_status(args.project), ensure_ascii=False, indent=2))
        return 0
    if args.command == "download":
        manifest = load_project(args.project) if args.dry_run else require_rights_approval(args.project)
        _print_command(
            media.download(
                manifest["source_url"],
                args.project.expanduser().resolve() / "source",
                dry_run=args.dry_run,
            )
        )
        return 0
    if args.command == "cut":
        _print_command(media.cut(args.source, args.output, args.start, args.end, stream_copy=args.stream_copy, dry_run=args.dry_run))
        return 0
    if args.command == "karaoke" and args.karaoke_command == "render":
        qa = render_file(args.timing, args.output, font=args.font)
        print(json.dumps(qa, ensure_ascii=False, indent=2))
        return 0
    if args.command == "karaoke" and args.karaoke_command == "burn":
        _print_command(media.burn_ass(args.source, args.subtitles, args.output, dry_run=args.dry_run))
        return 0
    if args.command == "probe":
        print(json.dumps(media.probe(args.path), ensure_ascii=False, indent=2))
        return 0
    if args.command == "align":
        transcribe(args.audio, args.output, model_name=args.model, language=args.language)
        print(args.output)
        return 0
    if args.command == "autopilot":
        foundation = _foundation_root()
        if not _foundation_is_complete():
            parser.error(
                "Upstream Foundation modules are missing; reinstall roy-ai-editor from a complete build "
                f"based on {UPSTREAM_FOUNDATION_COMMIT}"
            )
        readme = foundation / "README.md"
        print(foundation if args.path_only or not readme.is_file() else readme)
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
