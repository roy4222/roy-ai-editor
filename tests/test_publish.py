import json
from pathlib import Path

from roy_ai_editor.cli import main
from roy_ai_editor.project import create_project, load_project, save_project


def test_cli_builds_publish_package_without_uploading(tmp_path: Path, capsys) -> None:
    project_dir, manifest = create_project("https://youtu.be/x3nrUagsaV4", tmp_path)
    track_id = "001-synthetic-song"
    deliverable_id = f"{track_id}-karaoke-v1"
    video = project_dir / "videos" / "approved" / f"{deliverable_id}.mp4"
    subtitle = project_dir / "subtitles" / "approved" / f"{deliverable_id}.ass"
    video.write_bytes(b"synthetic approved video")
    subtitle.write_text("synthetic approved subtitle", encoding="utf-8")
    manifest["approved_deliverables"] = [{
        "deliverable_id": deliverable_id,
        "track_id": track_id,
        "status": "approved",
        "video": {"path": str(video.relative_to(project_dir)), "sha256": "fixture"},
        "subtitle": {"path": str(subtitle.relative_to(project_dir)), "sha256": "fixture"},
    }]
    save_project(project_dir, manifest)
    metadata = tmp_path / "metadata.json"
    metadata.write_text(json.dumps({
        "title": "Synthetic Karaoke Clip",
        "description": "Synthetic fixture only.",
        "credits": ["Synthetic performer", "Synthetic translator"],
        "rights": {"status": "reviewed", "warnings": ["Fixture must not be uploaded"]},
    }), encoding="utf-8")
    thumbnail = tmp_path / "thumbnail.png"
    thumbnail.write_bytes(b"synthetic thumbnail")

    assert main([
        "concert", "package-deliverable", str(project_dir), track_id,
        "--metadata", str(metadata), "--thumbnail", str(thumbnail),
    ]) == 0

    package = json.loads(capsys.readouterr().out)
    package_dir = project_dir / package["path"]
    package_metadata = json.loads((package_dir / "metadata.json").read_text(encoding="utf-8"))
    assert package["source_deliverable_id"] == deliverable_id
    assert (package_dir / "video.mp4").is_file()
    assert (package_dir / "subtitles.ass").is_file()
    assert (package_dir / "thumbnail.png").is_file()
    assert package_metadata["rights"]["warnings"] == ["Fixture must not be uploaded"]
    assert load_project(project_dir)["publish_packages"] == [package]
    assert not (package_dir / "upload.json").exists()
