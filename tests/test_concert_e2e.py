import json
import subprocess
from pathlib import Path

from roy_ai_editor.cli import main
from roy_ai_editor.deliverables import hash_file
from roy_ai_editor.project import load_project


def _run_cli(capsys, *arguments: str) -> dict:
    assert main(list(arguments)) == 0
    return json.loads(capsys.readouterr().out)


def test_synthetic_concert_reaches_local_publish_package(tmp_path: Path, capsys) -> None:
    created = _run_cli(
        capsys,
        "concert", "create", "https://youtu.be/e2eFixture01", "--workspace", str(tmp_path / "projects"),
    )
    project = Path(created["project_dir"])
    _run_cli(
        capsys,
        "concert", "approve-rights", str(project),
        "--evidence-url", "https://example.com/synthetic-rights",
        "--note", "Synthetic fixture approved for local testing",
    )

    lyrics = tmp_path / "lyrics.json"
    lyrics.write_text(json.dumps({
        "packet_version": 1,
        "track_number": 1,
        "slug": "synthetic-song",
        "title": "Synthetic Song",
        "source": {"url": "https://example.com/synthetic-lyrics"},
        "lines": [
            {"id": "L001", "japanese": "テスト", "translation": "測試"},
            {"id": "L002", "japanese": "うた", "translation": "歌曲"},
        ],
    }, ensure_ascii=False), encoding="utf-8")
    track = _run_cli(
        capsys,
        "concert", "approve-lyrics", str(project), str(lyrics),
        "--approved-by", "Roy", "--note", "Synthetic lyrics reviewed",
    )

    alignment = tmp_path / "alignment.json"
    alignment.write_text(json.dumps({
        "model": "synthetic-e2e",
        "segments": [
            {"text": "テスト", "words": [
                {"word": "テ", "start": 0.1, "end": 0.4},
                {"word": "スト", "start": 0.4, "end": 0.9},
            ]},
            {"text": "うた", "words": [
                {"word": "う", "start": 1.0, "end": 1.4},
                {"word": "た", "start": 1.4, "end": 1.8},
            ]},
        ],
    }, ensure_ascii=False), encoding="utf-8")
    _run_cli(
        capsys,
        "concert", "approve-timing", str(project), track["track_id"], str(alignment),
        "--approved-by", "Roy", "--note", "Synthetic timing reviewed",
    )

    source = tmp_path / "source.mp4"
    subprocess.run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-f", "lavfi", "-i", "color=c=black:s=320x240:d=2",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", str(source),
    ], check=True)
    candidate = _run_cli(
        capsys,
        "concert", "render-track", str(project), track["track_id"], str(source),
    )
    assert candidate["status"] == "review-required"
    deliverable = _run_cli(
        capsys,
        "concert", "approve-deliverable", str(project), track["track_id"],
        "--approved-by", "Roy", "--note", "Synthetic pixels reviewed",
    )

    metadata = tmp_path / "metadata.json"
    metadata.write_text(json.dumps({
        "title": "Synthetic Karaoke Clip",
        "description": "Local end-to-end fixture; do not upload.",
        "credits": ["Synthetic fixture"],
        "rights": {"status": "reviewed", "warnings": ["Do not upload"]},
    }), encoding="utf-8")
    thumbnail = tmp_path / "thumbnail.png"
    thumbnail.write_bytes(b"synthetic thumbnail")
    package = _run_cli(
        capsys,
        "concert", "package-deliverable", str(project), track["track_id"],
        "--metadata", str(metadata), "--thumbnail", str(thumbnail),
    )

    package_dir = project / package["path"]
    package_manifest = json.loads((package_dir / "package.json").read_text(encoding="utf-8"))
    manifest = load_project(project)
    assert package_manifest["upload_performed"] is False
    assert package_manifest["source_deliverable_id"] == deliverable["deliverable_id"]
    assert package_manifest["files"]["video.mp4"] == hash_file(package_dir / "video.mp4")
    assert manifest["stage"] == "publish-ready"
    assert manifest["review_gates"] == {
        "rights": "approved",
        "lyrics": "approved",
        "edit": "approved",
        "publish": "pending",
    }
