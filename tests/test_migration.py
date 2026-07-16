import hashlib
import json
from pathlib import Path

import pytest

from roy_ai_editor.cli import main
from roy_ai_editor.migration import migrate_legacy


def tree_hashes(root: Path) -> dict[str, str]:
    return {
        str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in root.rglob("*") if path.is_file()
    }


def test_legacy_migration_is_copy_verify_and_source_preserving(tmp_path: Path, capsys) -> None:
    source = tmp_path / "legacy-show"
    (source / "final").mkdir(parents=True)
    (source / "subs").mkdir()
    (source / "notes.txt").write_text("legacy note", encoding="utf-8")
    (source / "final" / "song.mp4").write_bytes(b"synthetic video")
    (source / "subs" / "song.ass").write_text("synthetic subtitle", encoding="utf-8")
    destination = tmp_path / "standard" / "legacy-show"
    before = tree_hashes(source)

    assert main(["migrate", "legacy", str(source), str(destination)]) == 0
    dry_run = json.loads(capsys.readouterr().out)
    assert dry_run["mode"] == "dry-run"
    assert not destination.exists()

    assert main(["migrate", "legacy", str(source), str(destination), "--execute"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["status"] == "verified"
    assert report["source_unchanged"] is True
    assert tree_hashes(source) == before
    assert (destination / "videos" / "archive" / "final" / "song.mp4").is_file()
    assert (destination / "subtitles" / "archive" / "subs" / "song.ass").is_file()
    assert (destination / "work" / "legacy-import" / "notes.txt").is_file()
    manifest = json.loads((destination / "project.json").read_text(encoding="utf-8"))
    assert manifest["migration"]["status"] == "verified"
    assert manifest["approved_deliverables"] == []


def test_legacy_migration_rejects_destination_inside_source(tmp_path: Path) -> None:
    source = tmp_path / "legacy-show"
    source.mkdir()
    (source / "song.mp4").write_bytes(b"synthetic video")

    with pytest.raises(ValueError, match="destination cannot be inside legacy source"):
        migrate_legacy(source, source / "migrated", execute=False)
