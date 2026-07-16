import hashlib
import json
from pathlib import Path

import pytest

from roy_ai_editor.cli import main
from roy_ai_editor.lyrics import prepare_lyrics_packet
from roy_ai_editor.project import approve_rights, create_project, load_project


def write_packet(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "packet_version": 1,
                "track_number": 1,
                "slug": "synthetic-song",
                "title": "Synthetic Song",
                "source": {
                    "url": "https://example.com/official-lyrics",
                    "translator": "Synthetic Fixture",
                    "reuse_status": "approved-for-test",
                    "captured_at": "2026-07-16T00:00:00+00:00",
                    "rights_warnings": [],
                },
                "lines": [
                    {"id": "L001", "japanese": "テスト", "translation": "合成測試"},
                    {"id": "L002", "japanese": "うた", "translation": "歌曲"},
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def test_cli_approves_a_traceable_lyrics_track(tmp_path: Path, capsys) -> None:
    project_dir, _ = create_project("https://youtu.be/x3nrUagsaV4", tmp_path)
    packet = tmp_path / "lyrics-packet.json"
    write_packet(packet)

    with pytest.raises(PermissionError):
        main([
            "concert", "approve-lyrics", str(project_dir), str(packet),
            "--approved-by", "Roy", "--note", "Synthetic fixture approved",
        ])

    approve_rights(project_dir, evidence_url="https://example.com/policy", note="Roy approved")
    assert main([
        "concert", "approve-lyrics", str(project_dir), str(packet),
        "--approved-by", "Roy", "--note", "Synthetic fixture approved",
    ]) == 0

    track = json.loads(capsys.readouterr().out)
    manifest = load_project(project_dir)
    lyrics_path = project_dir / track["lyrics"]["artifact"]
    lyrics_content = lyrics_path.read_bytes()

    assert track["track_id"] == "001-synthetic-song"
    assert track["lyrics"]["status"] == "approved"
    assert hashlib.sha256(lyrics_content).hexdigest() == track["lyrics"]["sha256"]
    assert manifest["tracks"] == [track]
    assert manifest["review_gates"]["lyrics"] == "approved"
    assert manifest["stage"] == "lyrics-approved"
    assert any(item["kind"] == "lyrics-approval" for item in manifest["evidence_artifacts"])

    assert main([
        "concert", "approve-lyrics", str(project_dir), str(packet),
        "--approved-by", "Roy", "--note", "Synthetic fixture approved",
    ]) == 0
    before_repeat = load_project(project_dir)
    before_repeat["tracks"][0]["timing"] = {"status": "approved", "artifact": "timing/approved/existing.json"}
    before_repeat["tracks"][0]["render_candidate"] = {"status": "review-required"}
    before_repeat["tracks"][0]["approved_deliverable_id"] = "existing-deliverable"
    from roy_ai_editor.project import save_project
    save_project(project_dir, before_repeat)

    assert main([
        "concert", "approve-lyrics", str(project_dir), str(packet),
        "--approved-by", "Roy", "--note", "Repeated approval of identical content",
    ]) == 0
    repeated = load_project(project_dir)
    assert len(repeated["tracks"]) == 1
    assert repeated["tracks"][0]["timing"]["status"] == "approved"
    assert repeated["tracks"][0]["render_candidate"]["status"] == "review-required"
    assert repeated["tracks"][0]["approved_deliverable_id"] == "existing-deliverable"


def test_cli_prepares_but_blocks_a_lyrics_packet_with_unknown_rights(tmp_path: Path, capsys) -> None:
    project_dir, _ = create_project("https://youtu.be/x3nrUagsaV4", tmp_path)
    approve_rights(project_dir, evidence_url="https://example.com/policy", note="Roy approved")
    draft = tmp_path / "draft.json"
    draft.write_text(json.dumps({
        "packet_version": 1,
        "track_number": 2,
        "slug": "blocked-song",
        "title": "Blocked Song",
        "source": {
            "url": "https://example.com/lyrics",
            "reuse_status": "unknown",
            "rights_warnings": ["Permission has not been confirmed"],
        },
        "lines": [{"id": "L001", "japanese": "歌", "translation": "歌"}],
    }, ensure_ascii=False), encoding="utf-8")

    assert main(["concert", "prepare-lyrics", str(project_dir), str(draft)]) == 0
    candidate = json.loads(capsys.readouterr().out)
    assert candidate["status"] == "blocked"
    assert candidate["captured_at"]
    prepared = project_dir / candidate["artifact"]
    assert prepared.is_file()
    manifest = load_project(project_dir)
    assert manifest["tracks"][0]["lyrics_candidate"] == candidate
    assert manifest["stage"] == "lyrics-blocked"

    with pytest.raises(PermissionError, match="reuse status"):
        main([
            "concert", "approve-lyrics", str(project_dir), str(prepared),
            "--approved-by", "Roy", "--note", "Do not approve unknown rights",
        ])


def test_adding_a_track_invalidates_project_wide_downstream_gates(tmp_path: Path) -> None:
    from roy_ai_editor.project import save_project

    project_dir, _ = create_project("https://youtu.be/x3nrUagsaV4", tmp_path)
    manifest = approve_rights(project_dir, evidence_url="https://example.com/policy", note="Roy approved")
    manifest["tracks"] = [{
        "track_id": "001-existing",
        "number": 1,
        "lyrics": {"status": "approved"},
        "approved_deliverable_id": "001-existing-karaoke-v1",
    }]
    manifest["approved_deliverables"] = [{
        "deliverable_id": "001-existing-karaoke-v1",
        "track_id": "001-existing",
        "status": "approved",
    }]
    manifest["review_gates"].update({"lyrics": "approved", "edit": "approved", "publish": "approved"})
    save_project(project_dir, manifest)
    draft = tmp_path / "new-track.json"
    draft.write_text(json.dumps({
        "packet_version": 1,
        "track_number": 2,
        "slug": "new-track",
        "title": "New Track",
        "source": {
            "url": "https://example.com/new-lyrics",
            "reuse_status": "unknown",
            "rights_warnings": ["Needs review"],
        },
        "lines": [{"id": "L001", "japanese": "新曲", "translation": "新歌"}],
    }, ensure_ascii=False), encoding="utf-8")

    prepare_lyrics_packet(project_dir, draft)
    current = load_project(project_dir)
    assert current["review_gates"]["lyrics"] == "pending"
    assert current["review_gates"]["edit"] == "pending"
    assert current["review_gates"]["publish"] == "pending"
