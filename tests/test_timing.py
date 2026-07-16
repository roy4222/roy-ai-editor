import json
from pathlib import Path

import pytest

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
        "source": {
            "url": "https://example.com/lyrics",
            "reuse_status": "approved-for-test",
            "captured_at": "2026-07-16T00:00:00+00:00",
            "rights_warnings": [],
        },
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


def test_cli_creates_a_traceable_forced_alignment_candidate(tmp_path: Path, capsys, monkeypatch) -> None:
    project_dir, _ = create_project("https://youtu.be/x3nrUagsaV4", tmp_path)
    approve_rights(project_dir, evidence_url="https://example.com/policy", note="approved")
    packet = tmp_path / "lyrics.json"
    packet.write_text(json.dumps({
        "packet_version": 1,
        "track_number": 1,
        "slug": "synthetic-song",
        "title": "Synthetic Song",
        "source": {
            "url": "https://example.com/lyrics",
            "reuse_status": "approved-for-test",
            "captured_at": "2026-07-16T00:00:00+00:00",
            "rights_warnings": [],
        },
        "lines": [{"id": "L001", "japanese": "テスト", "translation": "測試"}],
    }, ensure_ascii=False), encoding="utf-8")
    approve_lyrics(project_dir, packet, approved_by="Roy", note="approved")
    audio = tmp_path / "vocals.wav"
    audio.write_bytes(b"synthetic audio fixture")

    def fake_force_align(
        audio_path: Path,
        approved_text: str,
        output: Path,
        *,
        model_name: str,
        language: str,
    ) -> None:
        assert audio_path.is_file()
        assert approved_text == "テスト"
        output.write_text(json.dumps({
            "segments": [{"text": "テスト", "words": [
                {"word": "テ", "start": 0.0, "end": 0.4},
                {"word": "スト", "start": 0.4, "end": 0.9},
            ]}],
        }, ensure_ascii=False), encoding="utf-8")

    monkeypatch.setattr("roy_ai_editor.timing.alignment.force_align", fake_force_align)
    assert main([
        "concert", "align-timing", str(project_dir), "001-synthetic-song", str(audio),
        "--model", "synthetic-model", "--language", "ja",
    ]) == 0

    candidate = json.loads(capsys.readouterr().out)
    manifest = load_project(project_dir)
    assert candidate["status"] == "review-required"
    assert candidate["tool"] == "stable-ts"
    assert candidate["model"] == "synthetic-model"
    assert candidate["language"] == "ja"
    assert (project_dir / candidate["artifact"]).is_file()
    assert (project_dir / candidate["audio"]["path"]).is_file()
    assert manifest["tracks"][0]["timing_candidate"] == candidate
    evidence = next(item for item in manifest["evidence_artifacts"] if item["kind"] == "forced-alignment")
    assert (project_dir / evidence["path"]).is_file()

    assert main([
        "concert", "approve-timing", str(project_dir), "001-synthetic-song",
        str(project_dir / candidate["artifact"]),
        "--approved-by", "Roy", "--note", "Reviewed synthetic forced alignment",
    ]) == 0
    capsys.readouterr()
    approved = load_project(project_dir)
    assert approved["tracks"][0]["timing_candidate"]["status"] == "approved"
    timing_evidence = next(
        item for item in approved["evidence_artifacts"] if item["kind"] == "timing-approval"
    )
    timing_payload = json.loads((project_dir / timing_evidence["path"]).read_text(encoding="utf-8"))
    assert timing_payload["alignment_parameters"] == {
        "tool": "stable-ts",
        "model": "synthetic-model",
        "language": "ja",
    }


def test_failed_forced_alignment_does_not_create_a_candidate(tmp_path: Path, monkeypatch) -> None:
    project_dir, manifest = create_project("https://youtu.be/x3nrUagsaV4", tmp_path)
    from roy_ai_editor.project import save_project, write_immutable_json
    lyrics_path = project_dir / "lyrics" / "approved" / "001-synthetic-song.json"
    lyrics_sha = write_immutable_json(lyrics_path, {
        "lines": [{"id": "L001", "japanese": "テスト", "translation": "測試"}],
    })
    manifest["tracks"] = [{
        "track_id": "001-synthetic-song",
        "number": 1,
        "lyrics": {
            "status": "approved",
            "artifact": "lyrics/approved/001-synthetic-song.json",
            "sha256": lyrics_sha,
        },
    }]
    save_project(project_dir, manifest)
    audio = tmp_path / "vocals.wav"
    audio.write_bytes(b"synthetic audio fixture")

    def fail_alignment(*args, **kwargs) -> None:
        raise RuntimeError("alignment failed")

    monkeypatch.setattr("roy_ai_editor.timing.alignment.force_align", fail_alignment)
    with pytest.raises(RuntimeError, match="alignment failed"):
        main(["concert", "align-timing", str(project_dir), "001-synthetic-song", str(audio)])
    assert "timing_candidate" not in load_project(project_dir)["tracks"][0]
    assert not any((project_dir / "videos" / "clips").iterdir())


def test_one_timed_track_does_not_mark_a_multi_track_project_timing_complete(tmp_path: Path) -> None:
    from roy_ai_editor.project import save_project, write_immutable_json

    project_dir, manifest = create_project("https://youtu.be/x3nrUagsaV4", tmp_path)
    lyrics = {
        "packet_version": 1,
        "track_number": 1,
        "slug": "first",
        "title": "First",
        "source": {
            "url": "https://example.com/lyrics",
            "reuse_status": "approved-for-test",
            "captured_at": "2026-07-16T00:00:00+00:00",
            "rights_warnings": [],
        },
        "lines": [{"id": "L001", "japanese": "歌", "translation": "歌"}],
    }
    lyrics_path = project_dir / "lyrics" / "approved" / "001-first.json"
    lyrics_sha = write_immutable_json(lyrics_path, lyrics)
    manifest["tracks"] = [
        {
            "track_id": "001-first",
            "number": 1,
            "lyrics": {
                "status": "approved",
                "artifact": "lyrics/approved/001-first.json",
                "sha256": lyrics_sha,
            },
        },
        {"track_id": "002-second", "number": 2, "lyrics": {"status": "approved"}},
    ]
    save_project(project_dir, manifest)
    alignment = tmp_path / "alignment.json"
    alignment.write_text(json.dumps({
        "model": "synthetic",
        "segments": [{"text": "歌", "words": [{"word": "歌", "start": 0.1, "end": 0.8}]}],
    }, ensure_ascii=False), encoding="utf-8")

    from roy_ai_editor.timing import approve_timing
    approve_timing(project_dir, "001-first", alignment, approved_by="Roy", note="Reviewed")
    current = load_project(project_dir)
    assert current["stage"] == "partially-timing-approved"
