import hashlib
import json
from pathlib import Path

import pytest

from roy_ai_editor.cli import main
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
    assert len(load_project(project_dir)["tracks"]) == 1
