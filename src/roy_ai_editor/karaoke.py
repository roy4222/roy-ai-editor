"""Generate bilingual ASS karaoke subtitles with kanji-only furigana."""

from __future__ import annotations

import json
import math
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

KANJI_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff々〆ヵヶ]")
LYRIC_READING_OVERRIDES = {
    "君": "きみ",
}
KARAOKE_FONT_SIZE = 68
KARAOKE_SPACING = 1.0
LIBASS_EM_FACTOR = 0.691176


@dataclass(frozen=True)
class Token:
    text: str
    start: float
    end: float


@dataclass(frozen=True)
class RubySpan:
    start_index: int
    end_index: int
    reading: str


@dataclass(frozen=True)
class Line:
    start: float
    end: float
    japanese: str
    translation: str
    tokens: tuple[Token, ...]
    ruby: tuple[RubySpan, ...]
    timing_mode: str


def ass_time(seconds: float) -> str:
    total_cs = max(0, round(seconds * 100))
    hours, rem = divmod(total_cs, 360000)
    minutes, rem = divmod(rem, 6000)
    secs, cs = divmod(rem, 100)
    return f"{hours}:{minutes:02d}:{secs:02d}.{cs:02d}"


def escape_ass(text: str) -> str:
    return text.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}").replace("\n", "\\N")


def display_units(text: str) -> float:
    return sum(1.0 if unicodedata.east_asian_width(char) in "WFA" else 0.55 for char in text)


def display_advance(text: str, *, font_size: float, spacing: float = 0.0) -> float:
    """Estimate libass advance using an empirically calibrated Noto Sans JP em."""
    if not text:
        return 0.0
    return display_units(text) * font_size * LIBASS_EM_FACTOR + max(0, len(text) - 1) * spacing


def _katakana_to_hiragana(text: str) -> str:
    return "".join(chr(ord(ch) - 0x60) if "ァ" <= ch <= "ヶ" else ch for ch in text)


def auto_ruby(text: str) -> tuple[RubySpan, ...]:
    try:
        from pykakasi import kakasi
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("Install project dependencies with `uv sync` to generate furigana") from exc

    result: list[RubySpan] = []
    cursor = 0
    for item in kakasi().convert(text):
        surface = item["orig"]
        end = cursor + len(surface)
        if KANJI_RE.search(surface):
            reading = _katakana_to_hiragana(item.get("hira") or item.get("kana") or "")
            reading = LYRIC_READING_OVERRIDES.get(surface, reading)
            if reading and reading != surface:
                result.append(RubySpan(cursor, end, reading))
        cursor = end
    return tuple(result)


def _distributed_tokens(text: str, start: float, end: float) -> tuple[Token, ...]:
    chunks = re.findall(r"\s+|[^\s]", text)
    weights = [0.35 if chunk.isspace() else max(0.55, display_units(chunk)) for chunk in chunks]
    total = sum(weights) or 1.0
    cursor = start
    tokens: list[Token] = []
    for index, (chunk, weight) in enumerate(zip(chunks, weights, strict=True)):
        token_end = end if index == len(chunks) - 1 else cursor + (end - start) * weight / total
        tokens.append(Token(chunk, cursor, token_end))
        cursor = token_end
    return tuple(tokens)


def load_timing(path: Path) -> list[Line]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    lines: list[Line] = []
    for raw in payload["lines"]:
        start, end = float(raw["start"]), float(raw["end"])
        if end <= start:
            raise ValueError("Every lyric line must end after it starts")
        japanese = str(raw["japanese"])
        supplied_tokens = tuple(
            Token(str(token["text"]), float(token["start"]), float(token["end"]))
            for token in raw.get("tokens", [])
        )
        tokens = supplied_tokens or _distributed_tokens(japanese, start, end)
        _validate_tokens(japanese, start, end, tokens)
        ruby = tuple(
            RubySpan(int(span["start_index"]), int(span["end_index"]), str(span["reading"]))
            for span in raw.get("ruby", [])
        ) or auto_ruby(japanese)
        lines.append(
            Line(
                start,
                end,
                japanese,
                str(raw.get("translation", "")),
                tokens,
                ruby,
                "exact" if supplied_tokens else "draft-distributed",
            )
        )
    return lines


def _validate_tokens(japanese: str, line_start: float, line_end: float, tokens: tuple[Token, ...]) -> None:
    cursor = line_start
    for token in tokens:
        if token.end <= token.start:
            raise ValueError(f"Token must end after it starts: {token.text!r}")
        if token.start < line_start or token.end > line_end:
            raise ValueError(f"Token is outside its lyric line: {token.text!r}")
        if token.start < cursor:
            raise ValueError(f"Token timing overlaps or is out of order: {token.text!r}")
        cursor = token.end
    if "".join(token.text for token in tokens) != japanese:
        raise ValueError("Token text must concatenate exactly to the Japanese lyric line")


def _karaoke_text(tokens: tuple[Token, ...], line_start: float) -> str:
    parts: list[str] = []
    cursor = line_start
    for token in tokens:
        gap = round((token.start - cursor) * 100)
        if gap > 0:
            parts.append(f"{{\\k{gap}}}")
        centiseconds = max(1, round((token.end - token.start) * 100))
        parts.append(f"{{\\kf{centiseconds}}}{escape_ass(token.text)}")
        cursor = token.end
    return "".join(parts)


def _dialogue(layer: int, start: float, end: float, style: str, text: str) -> str:
    return f"Dialogue: {layer},{ass_time(start)},{ass_time(end)},{style},,0,0,0,,{text}"


def ruby_position(
    japanese: str,
    span: RubySpan,
    *,
    width: int = 1920,
    height: int = 1080,
) -> tuple[int, int]:
    total_advance = display_advance(
        japanese,
        font_size=KARAOKE_FONT_SIZE,
        spacing=KARAOKE_SPACING,
    )
    left = width / 2 - total_advance / 2
    before_text = japanese[: span.start_index]
    base_text = japanese[span.start_index : span.end_index]
    before = display_advance(
        before_text,
        font_size=KARAOKE_FONT_SIZE,
        spacing=KARAOKE_SPACING,
    )
    if before_text and base_text:
        before += KARAOKE_SPACING
    base = display_advance(
        base_text,
        font_size=KARAOKE_FONT_SIZE,
        spacing=KARAOKE_SPACING,
    )
    return math.floor(left + before + base / 2), height - 205


def ruby_layout_report(lines: list[Line], *, width: int = 1920, height: int = 1080) -> list[dict]:
    report: list[dict] = []
    for line_index, line in enumerate(lines, start=1):
        for span in line.ruby:
            x, y = ruby_position(line.japanese, span, width=width, height=height)
            report.append(
                {
                    "line": line_index,
                    "japanese": line.japanese,
                    "base_text": line.japanese[span.start_index : span.end_index],
                    "reading": span.reading,
                    "start_index": span.start_index,
                    "end_index": span.end_index,
                    "x": x,
                    "y": y,
                }
            )
    return report


def render_ass(lines: list[Line], *, width: int = 1920, height: int = 1080, font: str = "Noto Sans CJK JP") -> str:
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Ruby,{font},30,&H0000D7FF,&H00FFFFFF,&HDD000000,&H00000000,-1,0,0,0,100,100,0,0,1,3,0,5,0,0,0,1
Style: Karaoke,{font},68,&H0000D7FF,&H00FFFFFF,&HDD000000,&H00000000,-1,0,0,0,100,100,1,0,1,4,0,2,120,120,105,1
Style: Chinese,{font},44,&H00FFFFFF,&H00FFFFFF,&HDD000000,&H00000000,-1,0,0,0,100,100,1,0,1,3,0,2,120,120,42,1
Style: Countdown,{font},52,&H0000D7FF,&H00FFFFFF,&HDD000000,&H00000000,-1,0,0,0,100,100,5,0,1,4,0,2,120,120,110,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events: list[str] = []
    previous_end = 0.0
    for line in lines:
        if line.start - previous_end >= 1.5:
            dot_start = max(previous_end, line.start - 1.2)
            events.append(_dialogue(0, dot_start, line.start, "Countdown", "..."))
        events.append(_dialogue(1, line.start, line.end, "Karaoke", _karaoke_text(line.tokens, line.start)))
        if line.translation:
            events.append(_dialogue(1, line.start, line.end, "Chinese", escape_ass(line.translation)))

        for span in line.ruby:
            x, y = ruby_position(line.japanese, span, width=width, height=height)
            ruby_text = f"{{\\pos({x},{y})}}{escape_ass(span.reading)}"
            events.append(_dialogue(2, line.start, line.end, "Ruby", ruby_text))
        previous_end = line.end
    return header + "\n".join(events) + "\n"


def render_file(input_path: Path, output_path: Path, *, font: str = "Noto Sans CJK JP") -> dict:
    lines = load_timing(input_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_ass(lines, font=font), encoding="utf-8-sig")
    draft_lines = [index for index, line in enumerate(lines, start=1) if line.timing_mode != "exact"]
    ruby_spans = ruby_layout_report(lines)
    qa = {
        "schema_version": 1,
        "subtitle": str(output_path),
        "line_count": len(lines),
        "timing_status": "review-required" if draft_lines else "exact-input",
        "draft_timing_lines": draft_lines,
        "ruby_status": "review-required" if ruby_spans else "not-applicable",
        "ruby_layout_model": "libass-calibrated-v2",
        "ruby_spans": ruby_spans,
        "ruby_warning": (
            "Review every ruby span for reading and visual centering before release."
            if ruby_spans
            else None
        ),
        "warning": (
            "Distributed timing is a draft and requires singing alignment review."
            if draft_lines
            else None
        ),
    }
    qa_path = output_path.with_suffix(".qa.json")
    qa_path.write_text(json.dumps(qa, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return qa
