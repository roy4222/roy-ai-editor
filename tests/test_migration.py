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
    assert dry_run["summary"] == {"copy": 3, "skip": 0, "conflict": 0}
    assert {action["action"] for action in dry_run["actions"]} == {"copy"}
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

    assert main(["migrate", "legacy", str(source), str(destination), "--execute"]) == 0
    rerun = json.loads(capsys.readouterr().out)
    assert rerun["status"] == "verified"
    assert rerun["summary"] == {"copy": 0, "skip": 3, "conflict": 0}


def test_legacy_migration_reports_and_stops_on_conflict(tmp_path: Path) -> None:
    source = tmp_path / "legacy-show"
    source.mkdir()
    (source / "song.mp4").write_bytes(b"source bytes")
    destination = tmp_path / "standard" / "legacy-show"
    conflict = destination / "videos" / "archive" / "song.mp4"
    conflict.parent.mkdir(parents=True)
    conflict.write_bytes(b"different bytes")

    plan = migrate_legacy(source, destination, execute=False)
    assert plan["summary"] == {"copy": 0, "skip": 0, "conflict": 1}
    assert plan["actions"][0]["action"] == "conflict"
    with pytest.raises(RuntimeError, match="migration conflicts require review"):
        migrate_legacy(source, destination, execute=True)
    assert conflict.read_bytes() == b"different bytes"


def test_legacy_migration_refuses_an_existing_standard_project(tmp_path: Path) -> None:
    source = tmp_path / "legacy-show"
    source.mkdir()
    (source / "song.mp4").write_bytes(b"source bytes")
    destination = tmp_path / "standard" / "legacy-show"
    destination.mkdir(parents=True)
    (destination / "project.json").write_text(
        json.dumps({"workflow": "concert-live", "operator_note": "preserve me"}),
        encoding="utf-8",
    )

    plan = migrate_legacy(source, destination, execute=False)
    assert plan["destination_state"] == "conflict"
    with pytest.raises(RuntimeError, match="migration conflicts require review"):
        migrate_legacy(source, destination, execute=True)
    assert json.loads((destination / "project.json").read_text())["operator_note"] == "preserve me"


def test_legacy_migration_refuses_destination_symlinks(tmp_path: Path) -> None:
    source = tmp_path / "legacy-show"
    source.mkdir()
    (source / "song.mp4").write_bytes(b"source bytes")
    destination = tmp_path / "standard" / "legacy-show"
    mapped = destination / "videos" / "archive" / "song.mp4"
    mapped.parent.mkdir(parents=True)
    mapped.symlink_to(tmp_path / "outside.mp4")

    plan = migrate_legacy(source, destination, execute=False)
    assert plan["destination_state"] == "conflict"
    with pytest.raises(RuntimeError, match="migration conflicts require review"):
        migrate_legacy(source, destination, execute=True)
    assert not (tmp_path / "outside.mp4").exists()


def test_legacy_migration_rejects_destination_inside_source(tmp_path: Path) -> None:
    source = tmp_path / "legacy-show"
    source.mkdir()
    (source / "song.mp4").write_bytes(b"synthetic video")

    with pytest.raises(ValueError, match="destination cannot be inside legacy source"):
        migrate_legacy(source, source / "migrated", execute=False)


def test_reconciliation_profile_routes_assets_and_builds_traceable_tracks(tmp_path: Path) -> None:
    source = tmp_path / "legacy-show"
    (source / "clips").mkdir(parents=True)
    (source / "review").mkdir()
    (source / "clips" / "01-song.mp4").write_bytes(b"source clip")
    (source / "review" / "01-song.ass").write_text("synthetic subtitle", encoding="utf-8")
    (source / "review" / "approval.md").write_text("Roy approved lyrics", encoding="utf-8")
    destination = tmp_path / "standard" / "show"
    profile = tmp_path / "reconciliation.json"
    profile.write_text(json.dumps({
        "schema_version": 1,
        "project_id": "show",
        "source_url": "https://example.com/show",
        "routes": [
            {"source_prefix": "clips", "destination_prefix": "videos/clips"},
            {"source_prefix": "review", "destination_prefix": "qa/legacy"},
        ],
        "project_assets": {"technical_report": ["qa/legacy/approval.md"]},
        "tracks": [{
            "track_id": "01-song",
            "number": 1,
            "title": "Song",
            "legacy_assets": {
                "clip": ["videos/clips/01-song.mp4"],
                "subtitle": ["qa/legacy/01-song.ass"],
            },
        }],
        "review_gates": {
            "rights": "pending",
            "lyrics": "approved",
            "edit": "pending",
            "publish": "pending",
        },
        "gate_evidence": {"lyrics": ["qa/legacy/approval.md"]},
        "rights": {"status": "pending", "limitations": ["public release unknown"]},
    }), encoding="utf-8")

    dry_run = migrate_legacy(source, destination, execute=False, reconciliation=profile)
    assert dry_run["reconciliation"]["track_count"] == 1
    assert dry_run["summary"] == {"copy": 3, "skip": 0, "conflict": 0}
    assert {action["destination"] for action in dry_run["actions"]} == {
        "videos/clips/01-song.mp4",
        "qa/legacy/01-song.ass",
        "qa/legacy/approval.md",
    }

    migrate_legacy(source, destination, execute=True, reconciliation=profile)
    manifest = json.loads((destination / "project.json").read_text(encoding="utf-8"))
    assert manifest["workflow"] == "concert-live"
    assert manifest["project_assets"]["technical_report"][0]["sha256"]
    assert manifest["tracks"][0]["track_id"] == "01-song"
    assert manifest["tracks"][0]["legacy_assets"]["clip"][0]["path"] == "videos/clips/01-song.mp4"
    assert manifest["tracks"][0]["legacy_assets"]["clip"][0]["sha256"]
    assert manifest["review_gates"]["lyrics"] == "approved"
    assert manifest["approved_deliverables"] == []
    assert manifest["migration"]["reconciliation_profile_sha256"]


def test_reconciliation_rejects_approved_gate_without_existing_evidence(tmp_path: Path) -> None:
    source = tmp_path / "legacy-show"
    source.mkdir()
    (source / "song.mp4").write_bytes(b"source")
    destination = tmp_path / "standard" / "show"
    profile = tmp_path / "reconciliation.json"
    profile.write_text(json.dumps({
        "schema_version": 1,
        "project_id": "show",
        "routes": [],
        "tracks": [{"track_id": "01-song", "number": 1, "legacy_assets": {}}],
        "review_gates": {"rights": "pending", "lyrics": "approved", "edit": "pending", "publish": "pending"},
        "gate_evidence": {"lyrics": ["qa/missing-approval.md"]},
    }), encoding="utf-8")

    with pytest.raises(ValueError, match="approved lyrics gate evidence does not exist"):
        migrate_legacy(source, destination, execute=False, reconciliation=profile)


def test_reconciliation_rejects_duplicate_track_ids_and_destination_paths(tmp_path: Path) -> None:
    source = tmp_path / "legacy-show"
    (source / "a").mkdir(parents=True)
    (source / "b").mkdir()
    (source / "a" / "song.mp4").write_bytes(b"one")
    (source / "b" / "song.mp4").write_bytes(b"two")
    destination = tmp_path / "standard" / "show"
    profile = tmp_path / "reconciliation.json"
    profile.write_text(json.dumps({
        "schema_version": 1,
        "project_id": "show",
        "routes": [
            {"source_prefix": "a", "destination_prefix": "videos/review"},
            {"source_prefix": "b", "destination_prefix": "videos/review"},
        ],
        "tracks": [
            {"track_id": "01-song", "number": 1, "legacy_assets": {}},
            {"track_id": "01-song", "number": 2, "legacy_assets": {}},
        ],
        "review_gates": {"rights": "pending", "lyrics": "pending", "edit": "pending", "publish": "pending"},
        "gate_evidence": {},
    }), encoding="utf-8")

    with pytest.raises(ValueError, match="track_id values must be unique"):
        migrate_legacy(source, destination, execute=False, reconciliation=profile)
