import json
from pathlib import Path

from roy_ai_editor.cli import main
from roy_ai_editor.lyrics import approve_lyrics
from roy_ai_editor.project import approve_rights, create_project, load_project


def test_cli_reconciles_and_approves_timing(tmp_path: Path, capsys) -> None:
    project_dir, _ = create_project("https://youtu.be/x3nrUagsaV4", tmp_path)
    approve_rights(project_dir, evidence_url="https://example.com/policy", note="approved")
    packet = tmp_path / "lyrics.json"
    packet.write_text(json.dumps({
        "packet_version": 1,
        "track_number": 1,
        "slug": "synthetic-song",
        "title": "Synthetic Song",
        "source": {"url": "https://example.com/lyrics"},
        "lines": [
            {"id": "L001", "japanese": "テスト", "translation": "測試"},
            {"id": "L002", "japanese": "う た", "translation": "歌曲"},
        ],
    }, ensure_ascii=False), encoding="utf-8")
    approve_lyrics(project_dir, packet, approved_by="Roy", note="approved")
    alignment = tmp_path / "alignment.json"
    alignment.write_text(json.dumps({
        "model": "synthetic-forced-alignment",
        "segments": [
            {"text": "テスト", "words": [
                {"word": "テ", "start": 0.0, "end": 0.5},
                {"word": "ス", "start": 0.5, "end": 0.5},
                {"word": "ト", "start": 0.5, "end": 1.0},
            ]},
            {"text": "うた", "words": [
                {"word": "う", "start": 0.95, "end": 1.4},
                {"word": "た", "start": 1.4, "end": 1.8},
            ]},
        ],
    }, ensure_ascii=False), encoding="utf-8")

    assert main([
        "concert", "approve-timing", str(project_dir), "001-synthetic-song", str(alignment),
        "--approved-by", "Roy", "--note", "Reviewed synthetic reconciliation",
    ]) == 0

    timing_ref = json.loads(capsys.readouterr().out)
    manifest = load_project(project_dir)
    timing = json.loads((project_dir / timing_ref["artifact"]).read_text(encoding="utf-8"))
    assert timing_ref["status"] == "approved"
    assert timing["lines"][0]["tokens"][1]["text"] == "スト"
    assert "".join(token["text"] for token in timing["lines"][1]["tokens"]) == "う た"
    assert timing["lines"][0]["end"] <= timing["lines"][1]["start"]
    assert all(token["end"] > token["start"] for line in timing["lines"] for token in line["tokens"])
    assert manifest["tracks"][0]["timing"] == timing_ref
    assert manifest["stage"] == "timing-approved"
    assert any(item["kind"] == "timing-approval" for item in manifest["evidence_artifacts"])
