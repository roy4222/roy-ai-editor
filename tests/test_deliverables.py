import json
import subprocess
from pathlib import Path

import pytest

from roy_ai_editor.cli import main
from roy_ai_editor.deliverables import approve_deliverable, check_subtitle_layout, hash_file, render_track
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
    imported_input = project_dir / candidate["input"]["path"]
    assert imported_input.parent == project_dir / "videos" / "clips"
    assert imported_input.is_file()
    assert candidate["input"]["sha256"]
    assert candidate["video_sha256"]
    assert candidate["subtitle_sha256"]
    assert candidate["qa_status"] == "passed"
    assert candidate["visual_qa"]["frames"]
    assert all((project_dir / frame["path"]).is_file() for frame in candidate["visual_qa"]["frames"])

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


def test_deliverable_approval_rejects_candidate_changed_after_qa(tmp_path: Path) -> None:
    project_dir, manifest = create_project("https://youtu.be/x3nrUagsaV4", tmp_path)
    video = project_dir / "videos" / "review" / "001-first-karaoke.mp4"
    subtitle = project_dir / "subtitles" / "draft" / "001-first.ass"
    video.write_bytes(b"qa-reviewed video")
    subtitle.write_text("qa-reviewed subtitle", encoding="utf-8")
    manifest["tracks"] = [{
        "track_id": "001-first",
        "number": 1,
        "render_candidate": {
            "candidate_id": "001-first-karaoke-v1",
            "status": "review-required",
            "video": str(video.relative_to(project_dir)),
            "subtitle": str(subtitle.relative_to(project_dir)),
            "video_sha256": hash_file(video),
            "subtitle_sha256": hash_file(subtitle),
            "qa_status": "passed",
            "qa_evidence_id": "evidence-fixture",
        },
    }]
    save_project(project_dir, manifest)
    video.write_bytes(b"changed after QA")

    with pytest.raises(RuntimeError, match="changed after render QA"):
        approve_deliverable(project_dir, "001-first", approved_by="Roy", note="Reviewed")


def test_one_approved_track_does_not_approve_a_multi_track_project(tmp_path: Path) -> None:
    project_dir, manifest = create_project("https://youtu.be/x3nrUagsaV4", tmp_path)
    review_video = project_dir / "videos" / "review" / "001-first-karaoke.mp4"
    review_subtitle = project_dir / "subtitles" / "draft" / "001-first.ass"
    review_video.write_bytes(b"review video")
    review_subtitle.write_text("review subtitle", encoding="utf-8")
    manifest["tracks"] = [
        {
            "track_id": "001-first",
            "number": 1,
            "render_candidate": {
                "candidate_id": "001-first-karaoke-v1",
                "status": "review-required",
                "video": str(review_video.relative_to(project_dir)),
                "subtitle": str(review_subtitle.relative_to(project_dir)),
                "video_sha256": hash_file(review_video),
                "subtitle_sha256": hash_file(review_subtitle),
                "qa_status": "passed",
                "qa_evidence_id": "evidence-fixture",
            },
        },
        {"track_id": "002-second", "number": 2},
    ]
    save_project(project_dir, manifest)

    approve_deliverable(project_dir, "001-first", approved_by="Roy", note="First track reviewed")

    current = load_project(project_dir)
    assert current["review_gates"]["edit"] == "pending"
    assert current["stage"] == "partially-deliverable-approved"


def test_one_rendered_track_does_not_mark_a_multi_track_project_rendered(tmp_path: Path) -> None:
    project_dir, manifest = create_project("https://youtu.be/x3nrUagsaV4", tmp_path)
    timing = json.loads(TIMING_FIXTURE.read_text(encoding="utf-8"))
    timing_path = project_dir / "timing" / "approved" / "001-first.json"
    timing_sha = write_immutable_json(timing_path, timing)
    manifest["tracks"] = [
        {
            "track_id": "001-first",
            "number": 1,
            "timing": {
                "status": "approved",
                "artifact": "timing/approved/001-first.json",
                "sha256": timing_sha,
            },
        },
        {"track_id": "002-second", "number": 2, "timing": {"status": "approved"}},
    ]
    save_project(project_dir, manifest)
    source = tmp_path / "source.mp4"
    subprocess.run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-f", "lavfi", "-i", "color=c=black:s=320x240:d=4",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", str(source),
    ], check=True)

    render_track(project_dir, "001-first", source, font="Noto Sans CJK JP")
    assert load_project(project_dir)["stage"] == "partially-rendered"


def test_qa_failed_candidate_cannot_be_approved(tmp_path: Path) -> None:
    project_dir, manifest = create_project("https://youtu.be/x3nrUagsaV4", tmp_path)
    video = project_dir / "videos" / "review" / "001-first-karaoke.mp4"
    subtitle = project_dir / "subtitles" / "draft" / "001-first.ass"
    video.write_bytes(b"review video")
    subtitle.write_text("review subtitle", encoding="utf-8")
    manifest["tracks"] = [{
        "track_id": "001-first",
        "number": 1,
        "render_candidate": {
            "candidate_id": "001-first-karaoke-v1",
            "status": "qa-failed",
            "qa_status": "failed",
            "video": str(video.relative_to(project_dir)),
            "subtitle": str(subtitle.relative_to(project_dir)),
            "video_sha256": hash_file(video),
            "subtitle_sha256": hash_file(subtitle),
            "qa_evidence_id": "evidence-fixture",
        },
    }]
    save_project(project_dir, manifest)

    with pytest.raises(PermissionError, match="passing render QA"):
        approve_deliverable(project_dir, "001-first", approved_by="Roy", note="Reviewed")


def test_subtitle_layout_gate_rejects_overwide_fullwidth_text(tmp_path: Path) -> None:
    timing = tmp_path / "timing.json"
    japanese = "星" * 40
    timing.write_text(json.dumps({
        "schema_version": 1,
        "lines": [{
            "start": 0.1,
            "end": 1.0,
            "japanese": japanese,
            "translation": "測試",
            "tokens": [{"text": japanese, "start": 0.1, "end": 1.0}],
            "ruby": [],
        }],
    }, ensure_ascii=False), encoding="utf-8")

    result = check_subtitle_layout(timing)
    assert result["status"] == "failed"
    assert any(failure["kind"] == "japanese-safe-width" for failure in result["failures"])
