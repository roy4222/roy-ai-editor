"""Create tight, line-by-line subtitle crops from an actually burned video.

This deliberately inspects pixels from the encoded preview instead of trusting
ASS coordinates or full-frame screenshots.  Each lyric line is sampled at its
midpoint, cropped to the subtitle band, and arranged into numbered contact
sheets for human visual review.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path


def run(command: list[str]) -> None:
    subprocess.run(command, check=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("video", type=Path, help="burned preview MP4")
    parser.add_argument("timing", type=Path, help="karaoke timing JSON")
    parser.add_argument("output", type=Path, help="QA output directory")
    parser.add_argument("--crop", default="1920:280:0:790", help="FFmpeg w:h:x:y crop")
    parser.add_argument("--page-size", type=int, default=8)
    args = parser.parse_args()

    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise SystemExit("ffmpeg is required")
    payload = json.loads(args.timing.read_text(encoding="utf-8"))
    lines = payload["lines"]
    crop_width, crop_height, _, _ = (int(value) for value in args.crop.split(":"))
    tile_height = 140
    tile_width = round(crop_width * tile_height / crop_height)
    args.output.mkdir(parents=True, exist_ok=True)
    frames = args.output / "lines"
    frames.mkdir(parents=True, exist_ok=True)

    manifest: list[dict] = []
    for line_number, line in enumerate(lines, 1):
        midpoint = (float(line["start"]) + float(line["end"])) / 2
        target = frames / f"line-{line_number:03d}.png"
        label = (
            "drawtext=fontfile='C\\:/Windows/Fonts/arial.ttf':"
            f"text='Line {line_number:02d}':x=12:y=10:fontsize=28:"
            "fontcolor=white:box=1:boxcolor=black@0.72"
        )
        run(
            [
                ffmpeg,
                "-hide_banner",
                "-loglevel",
                "error",
                "-ss",
                f"{midpoint:.4f}",
                "-i",
                str(args.video),
                "-frames:v",
                "1",
                "-vf",
                f"crop={args.crop},{label}",
                "-y",
                str(target),
            ]
        )
        manifest.append(
            {
                "line": line_number,
                "sample_time": round(midpoint, 4),
                "japanese": line["japanese"],
                "translation": line["translation"],
                "crop": str(target),
            }
        )

    pages: list[str] = []
    for page_index, start in enumerate(range(1, len(lines) + 1, args.page_size), 1):
        count = min(args.page_size, len(lines) - start + 1)
        page = args.output / f"contact-sheet-{page_index:02d}.png"
        tile_rows = (args.page_size + 1) // 2
        run(
            [
                ffmpeg,
                "-hide_banner",
                "-loglevel",
                "error",
                "-start_number",
                str(start),
                "-i",
                str(frames / "line-%03d.png"),
                "-frames:v",
                str(count),
                "-vf",
                f"scale={tile_width}:{tile_height},tile=2x{tile_rows}:nb_frames={count}:padding=8:margin=12:color=black",
                "-frames:v",
                "1",
                "-y",
                str(page),
            ]
        )
        pages.append(str(page))

    (args.output / "manifest.json").write_text(
        json.dumps(
            {
                "video": str(args.video),
                "timing": str(args.timing),
                "crop": args.crop,
                "review_policy": "inspect every tight crop; full-frame screenshots are not acceptable evidence",
                "lines": manifest,
                "contact_sheets": pages,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Created {len(lines)} line crops and {len(pages)} contact sheets in {args.output}")


if __name__ == "__main__":
    main()
