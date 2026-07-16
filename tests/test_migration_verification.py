import json
import os
from pathlib import Path

from roy_ai_editor.deliverables import hash_file
from roy_ai_editor.migration_verification import verify_migrated_projects
from roy_ai_editor.project import load_project, save_project


def test_final_migration_verification_checks_refs_media_subtitles_and_boundaries(tmp_path: Path) -> None:
    source = tmp_path / "legacy"
    source.mkdir()
    (source / "song.mp4").write_bytes(b"source-video")
    (source / "song.ass").write_text(
        "[Script Info]\nTitle: test\n[Events]\nDialogue: 0,0:00:00.00,0:00:01.00,Default,,0,0,0,,Hi\n",
        encoding="utf-8",
    )
    projects = tmp_path / "RoyAIEditor" / "projects"
    project = projects / "show"
    video = project / "videos" / "review" / "song.mp4"
    subtitle = project / "subtitles" / "draft" / "song.ass"
    video.parent.mkdir(parents=True)
    subtitle.parent.mkdir(parents=True)
    video.write_bytes((source / "song.mp4").read_bytes())
    subtitle.write_bytes((source / "song.ass").read_bytes())
    actions = [
        {"source": "song.mp4", "destination": "videos/review/song.mp4", "size": video.stat().st_size, "sha256": hash_file(video), "action": "copy"},
        {"source": "song.ass", "destination": "subtitles/draft/song.ass", "size": subtitle.stat().st_size, "sha256": hash_file(subtitle), "action": "copy"},
    ]
    evidence = project / "qa" / "legacy-migration-0123456789abcdef.json"
    evidence.parent.mkdir(parents=True)
    evidence.write_text(json.dumps({"actions": actions}), encoding="utf-8")
    manifest = {
        "schema_version": 2,
        "project_id": "show",
        "workflow": "concert-live",
        "tracks": [{
            "track_id": "01-song",
            "number": 1,
            "legacy_assets": {
                "review_video": [{"path": "videos/review/song.mp4", "sha256": hash_file(video), "size": video.stat().st_size}],
                "subtitle_candidate": [{"path": "subtitles/draft/song.ass", "sha256": hash_file(subtitle), "size": subtitle.stat().st_size}],
            },
        }],
        "project_assets": {},
        "evidence_artifacts": [],
        "approved_deliverables": [],
        "review_gates": {"rights": "pending", "lyrics": "pending", "edit": "pending", "publish": "pending"},
        "unresolved_conflicts": ["publication rights unknown"],
        "migration": {
            "status": "verified",
            "source": str(source),
            "report": "qa/legacy-migration-0123456789abcdef.json",
            "source_legacy_boundary": "logical-read-only-candidate",
        },
    }
    save_project(project, manifest)

    def probe(path: Path) -> dict:
        assert path == video
        return {"duration": 1.0, "video_codec": "h264", "audio_codec": "aac", "width": 1920, "height": 1080}

    output = tmp_path / "RoyAIEditor" / "verification"
    result = verify_migrated_projects(
        projects,
        ["show"],
        output,
        probe=probe,
        finalize_boundaries=True,
        expected_cohort=frozenset({"show"}),
    )

    assert result["status"] == "PASS"
    assert result["project_count"] == 1
    assert result["totals"]["source_files"] == 2
    assert result["totals"]["destination_files"] == 4
    assert result["totals"]["media_files"] == 1
    assert result["totals"]["subtitle_files"] == 1
    assert result["projects"][0]["unresolved_conflicts"] == ["publication rights unknown"]
    current = load_project(project)
    assert current["migration"]["source_legacy_boundary"] == "logical-read-only"
    assert current["migration"]["verification"]["status"] == "PASS"
    assert current["migration"]["verification"]["boundary_registry_sha256"]
    assert Path(result["aggregate_report"]).is_file()
    assert Path(result["boundary_registry"]).is_file()
    assert Path(result["final_destination_attestation"]).is_file()


def test_final_migration_verification_does_not_finalize_when_hash_changed(tmp_path: Path) -> None:
    source = tmp_path / "legacy"
    source.mkdir()
    (source / "song.ass").write_text("[Events]\nDialogue: x\n", encoding="utf-8")
    projects = tmp_path / "projects"
    project = projects / "show"
    copied = project / "subtitles" / "draft" / "song.ass"
    copied.parent.mkdir(parents=True)
    copied.write_text("changed", encoding="utf-8")
    report = project / "qa" / "migration.json"
    report.parent.mkdir()
    report.write_text(json.dumps({"actions": [{
        "source": "song.ass",
        "destination": "subtitles/draft/song.ass",
        "size": (source / "song.ass").stat().st_size,
        "sha256": hash_file(source / "song.ass"),
        "action": "copy",
    }]}), encoding="utf-8")
    save_project(project, {
        "project_id": "show",
        "tracks": [],
        "project_assets": {},
        "evidence_artifacts": [],
        "approved_deliverables": [],
        "review_gates": {"rights": "pending", "lyrics": "pending", "edit": "pending", "publish": "pending"},
        "migration": {"source": str(source), "report": "qa/migration.json", "source_legacy_boundary": "logical-read-only-candidate"},
    })

    result = verify_migrated_projects(
        projects,
        ["show"],
        tmp_path / "verification",
        finalize_boundaries=True,
        expected_cohort=frozenset({"show"}),
    )

    assert result["status"] == "FAIL"
    assert any("destination hash mismatch" in error for error in result["projects"][0]["errors"])
    assert load_project(project)["migration"]["source_legacy_boundary"] == "logical-read-only-candidate"
    assert "boundary_registry" not in result


def test_final_verifier_accepts_ntfs_subsecond_mtime_truncation(tmp_path: Path) -> None:
    source = tmp_path / "legacy"
    destination = tmp_path / "projects" / "show"
    source.mkdir()
    copied = destination / "work" / "asset.txt"
    copied.parent.mkdir(parents=True)
    original = source / "asset.txt"
    original.write_text("same bytes", encoding="utf-8")
    copied.write_bytes(original.read_bytes())
    second = 1_700_000_000
    os.utime(original, ns=(second * 1_000_000_000 + 900_000_000,) * 2)
    os.utime(copied, ns=(second * 1_000_000_000,) * 2)
    report = destination / "qa" / "legacy-migration-0123456789abcdef.json"
    report.parent.mkdir()
    action = {
        "source": "asset.txt",
        "destination": "work/asset.txt",
        "source_class": "root",
        "destination_class": "work",
        "size": original.stat().st_size,
        "mtime_ns": original.stat().st_mtime_ns,
        "sha256": hash_file(original),
        "action": "skip",
    }
    report.write_text(json.dumps({"actions": [action]}), encoding="utf-8")
    save_project(destination, {
        "project_id": "show",
        "tracks": [],
        "project_assets": {},
        "evidence_artifacts": [],
        "approved_deliverables": [],
        "review_gates": {"rights": "pending", "lyrics": "pending", "edit": "pending", "publish": "pending"},
        "migration": {
            "source": str(source),
            "report": "qa/legacy-migration-0123456789abcdef.json",
            "source_inventory_sha256": "ignored-for-this-fixture",
            "source_legacy_boundary": "logical-read-only-candidate",
        },
    })
    manifest = load_project(destination)
    manifest["migration"].pop("source_inventory_sha256")
    save_project(destination, manifest)

    result = verify_migrated_projects(
        tmp_path / "projects",
        ["show"],
        tmp_path / "verification",
        finalize_boundaries=False,
    )

    assert result["status"] == "PASS"
