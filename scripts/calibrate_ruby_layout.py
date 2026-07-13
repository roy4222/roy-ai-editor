"""Measure libass glyph advance for the font/style used by karaoke rendering."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import tempfile
from pathlib import Path


BBOX_RE = re.compile(r"\bx1:\d+\s+x2:\d+\s+y1:\d+\s+y2:\d+\s+w:(\d+)\s+h:\d+")


def filter_path(path: Path) -> str:
    value = str(path.resolve()).replace("\\", "/")
    return value.replace(":", "\\:").replace("'", "\\'")


def ass_document(text: str, *, font: str, font_size: int, spacing: float) -> str:
    return f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Calibration,{font},{font_size},&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,{spacing},0,1,0,0,2,0,0,105,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:00.00,0:00:01.00,Calibration,,0,0,0,,{text}
"""


def rendered_width(text: str, *, font: str, font_size: int, spacing: float, temp: Path) -> int:
    ass = temp / "calibration.ass"
    ass.write_text(ass_document(text, font=font, font_size=font_size, spacing=spacing), encoding="utf-8-sig")
    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "info",
        "-f",
        "lavfi",
        "-i",
        "color=c=black:s=1920x1080:d=0.1",
        "-vf",
        f"subtitles=filename='{filter_path(ass)}',bbox",
        "-frames:v",
        "1",
        "-f",
        "null",
        "-",
    ]
    result = subprocess.run(command, check=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
    matches = BBOX_RE.findall(result.stderr)
    if not matches:
        raise RuntimeError(f"ffmpeg bbox did not detect rendered text: {result.stderr[-1000:]}")
    return int(matches[-1])


def slope(samples: list[tuple[int, int]]) -> float:
    count = len(samples)
    mean_x = sum(x for x, _ in samples) / count
    mean_y = sum(y for _, y in samples) / count
    numerator = sum((x - mean_x) * (y - mean_y) for x, y in samples)
    denominator = sum((x - mean_x) ** 2 for x, _ in samples)
    return numerator / denominator


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--font", default="Noto Sans JP")
    parser.add_argument("--font-size", type=int, default=68)
    parser.add_argument("--spacing", type=float, default=1.0)
    args = parser.parse_args()

    with tempfile.TemporaryDirectory(prefix="roy-ruby-calibration-") as directory:
        temp = Path(directory)
        samples = [
            (length, rendered_width("国" * length, font=args.font, font_size=args.font_size, spacing=args.spacing, temp=temp))
            for length in range(4, 17)
        ]
    measured_step = slope(samples)
    glyph_advance = measured_step - args.spacing
    payload = {
        "font": args.font,
        "font_size": args.font_size,
        "spacing": args.spacing,
        "samples": [{"characters": length, "bbox_width": width} for length, width in samples],
        "measured_step_px": round(measured_step, 4),
        "glyph_advance_px": round(glyph_advance, 4),
        "fullwidth_em_factor": round(glyph_advance / args.font_size, 6),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
