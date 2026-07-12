from pathlib import Path

import json

import pytest

from roy_ai_editor.karaoke import ass_time, load_timing, render_ass, render_file


FIXTURE = Path(__file__).parent / "fixtures" / "timing.json"


def test_ass_time_uses_centiseconds() -> None:
    assert ass_time(65.129) == "0:01:05.13"


def test_render_ass_contains_bilingual_karaoke_and_ruby() -> None:
    rendered = render_ass(load_timing(FIXTURE))

    assert "Style: Karaoke" in rendered
    assert "Style: Chinese" in rendered
    assert "Style: Ruby" in rendered
    assert "{\\kf50}星" in rendered
    assert "一起仰望星星吧" in rendered
    assert "ほし" in rendered
    assert "み" in rendered
    assert "Dialogue: 0,0:00:00.00,0:00:01.00,Countdown" not in rendered


def test_token_gaps_become_non_highlighting_ass_time(tmp_path: Path) -> None:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    payload["lines"][0]["tokens"][1]["start"] = 1.7
    source = tmp_path / "timing.json"
    source.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    rendered = render_ass(load_timing(source))
    assert "{\\k20}{\\kf10}を" in rendered


def test_invalid_overlapping_tokens_are_rejected(tmp_path: Path) -> None:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    payload["lines"][0]["tokens"][1]["start"] = 1.4
    source = tmp_path / "timing.json"
    source.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(ValueError, match="overlaps"):
        load_timing(source)


def test_distributed_timing_creates_review_required_qa(tmp_path: Path) -> None:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    del payload["lines"][0]["tokens"]
    source = tmp_path / "timing.json"
    output = tmp_path / "lyrics.ass"
    source.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    qa = render_file(source, output)
    assert qa["timing_status"] == "review-required"
    assert (tmp_path / "lyrics.qa.json").exists()
