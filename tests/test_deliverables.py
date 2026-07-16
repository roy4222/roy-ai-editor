import json
import subprocess
from pathlib import Path

from roy_ai_editor.cli import main
from roy_ai_editor.project import create_project, load_project, save_project, write_immutable_json


TIMING_FIXTURE = Path(__file__).parent / "fixtures" / "timing.json"


def test_render_candidate_requires_explicit_deliverable_approval(tmp_path: Path, capsys) -> None:
    project_dir, manifest = create_project("https://youtu.be/x3nrUagsaV4", tmp_path)
    track_id = "001-synthetic-song"
    timing = json.loads(TIMING_FIXTURE.read_text(encoding="utf-8"))
    timing_path = project_dir / "timing" / "approved" / f"{track_id}.json"
    timing_sha = write_immutable_json(timing_path, timing)
    manifest["tracks"] = [{
        "track_id": track_id,
        "number": 1,
        "slug": "synthetic-song",
        "title": "Synthetic Song",
        "lyrics": {"status": "approved"},
        "timing": {"status": "approved", "artifact": f"timing/approved/{track_id}.json", "sha256": timing_sha},
    }]
    save_project(project_dir, manifest)
    source = tmp_path / "source.mp4"
    subprocess.run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-f", "lavfi", "-i", "color=c=black:s=320x240:d=4",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", str(source),
    ], check=True)

    assert main(["concert", "render-track", str(project_dir), track_id, str(source)]) == 0
    candidate = json.loads(capsys.readouterr().out)
    pending = load_project(project_dir)
    assert pending["approved_deliverables"] == []
    assert Path(project_dir / candidate["video"]).is_file()
    assert Path(project_dir / candidate["subtitle"]).is_file()

    assert main([
        "concert", "approve-deliverable", str(project_dir), track_id,
        "--approved-by", "Roy", "--note", "Reviewed burned pixels and subtitle",
    ]) == 0
    deliverable = json.loads(capsys.readouterr().out)
    approved = load_project(project_dir)
    assert deliverable["deliverable_id"] == "001-synthetic-song-karaoke-v1"
    assert (project_dir / deliverable["video"]["path"]).is_file()
    assert (project_dir / deliverable["subtitle"]["path"]).is_file()
    assert approved["approved_deliverables"] == [deliverable]
    assert approved["review_gates"]["edit"] == "approved"
    assert approved["stage"] == "deliverable-approved"
