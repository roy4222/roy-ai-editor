from __future__ import annotations

import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from threading import Barrier, Event

import pytest

import roy_ai_editor.production as production_module
from roy_ai_editor.cli import main
from roy_ai_editor.production import (
    LeaseUnavailable,
    ProductionJobIntent,
    ReviewReplyIntent,
    SyntheticProductionAdapter,
    acknowledge_outbox_event,
    acquire_job_lease,
    canonicalize_youtube_url,
    heartbeat_job_lease,
    list_outbox_events,
    run_production_job,
    submit_review_reply,
    submit_production_job,
)
from roy_ai_editor.project import load_project


@pytest.mark.parametrize(
    "submitted",
    [
        "https://www.youtube.com/watch?v=x3nrUagsaV4&utm_source=test",
        "https://youtu.be/x3nrUagsaV4?t=42",
        "https://www.youtube.com/embed/x3nrUagsaV4?start=42",
        "https://www.youtube.com/shorts/x3nrUagsaV4?feature=share",
        "https://www.youtube.com/live/x3nrUagsaV4?si=fixture",
    ],
)
def test_canonicalize_youtube_url_preserves_submission_and_unifies_supported_forms(
    submitted: str,
) -> None:
    source = canonicalize_youtube_url(submitted)

    assert source.submitted_url == submitted
    assert source.video_id == "x3nrUagsaV4"
    assert source.canonical_url == "https://www.youtube.com/watch?v=x3nrUagsaV4"


@pytest.mark.parametrize(
    "submitted",
    [
        "https://youtube.com.example.test/watch?v=x3nrUagsaV4",
        "https://notyoutube.com/watch?v=x3nrUagsaV4",
        "https://evil.test@www.youtube.com/watch?v=x3nrUagsaV4",
        "http://www.youtube.com/watch?v=x3nrUagsaV4",
        "https://www.youtube.com/channel/x3nrUagsaV4",
        "https://youtu.be/x3nrUagsaV4/extra",
    ],
)
def test_canonicalize_youtube_url_rejects_lookalike_hosts_and_unsupported_paths(
    submitted: str,
) -> None:
    with pytest.raises(ValueError):
        canonicalize_youtube_url(submitted)


def test_submit_production_job_deduplicates_canonical_intent_and_preserves_requests(
    tmp_path: Path,
) -> None:
    submitted_at = datetime(2026, 7, 19, 8, 0, tzinfo=UTC)
    first = submit_production_job(
        ProductionJobIntent(
            source_url="https://youtu.be/x3nrUagsaV4?t=42",
            selection_mode="selected",
            selected_tracks=("Song B", "Song A"),
            profile_id="roy-public-example",
            originating_task="codex-task-123",
        ),
        workspace=tmp_path,
        submitted_at=submitted_at,
    )
    duplicate = submit_production_job(
        ProductionJobIntent(
            source_url="https://www.youtube.com/watch?v=x3nrUagsaV4&utm_source=test",
            selection_mode="selected",
            selected_tracks=("Song A", "Song B"),
            profile_id="roy-public-example",
            originating_task="codex-task-123",
        ),
        workspace=tmp_path,
        submitted_at=submitted_at,
    )
    different_selection = submit_production_job(
        ProductionJobIntent(
            source_url="https://youtu.be/x3nrUagsaV4",
            selection_mode="selected",
            selected_tracks=("Song C",),
            profile_id="roy-public-example",
            originating_task="codex-task-123",
        ),
        workspace=tmp_path,
        submitted_at=submitted_at,
    )

    assert duplicate.project_dir == first.project_dir
    assert duplicate.job_id == first.job_id
    assert different_selection.project_dir != first.project_dir
    assert first.manifest["production_job"]["state"] == "queued"
    assert first.manifest["production_job"]["track_selection"] == {
        "mode": "selected",
        "tracks": ["Song A", "Song B"],
    }
    request = json.loads(
        (first.project_dir / first.manifest["production_job"]["requests"][0]["path"])
        .read_text(encoding="utf-8")
    )
    assert request["intake_authorization"]["scope"] == [
        "local-processing",
        "private-youtube-upload",
    ]
    assert request["toolchain_release"]["id"] == "concert-v1-tracer@1.0.0"
    assert len(request["toolchain_release"]["sha256"]) == 64
    assert request["quality_registry"]["id"] == "concert-v1-quality@1.0.0"
    assert len(request["quality_registry"]["sha256"]) == 64

    request_references = duplicate.manifest["production_job"]["requests"]
    assert len(request_references) == 2
    submitted_urls = []
    for reference in request_references:
        content = (duplicate.project_dir / reference["path"]).read_bytes()
        assert hashlib.sha256(content).hexdigest() == reference["sha256"]
        submitted_urls.append(json.loads(content)["source_url"])
    assert submitted_urls == [
        "https://youtu.be/x3nrUagsaV4?t=42",
        "https://www.youtube.com/watch?v=x3nrUagsaV4&utm_source=test",
    ]


def test_job_lease_takeover_requires_ttl_after_the_unchanged_durable_heartbeat(
    tmp_path: Path,
) -> None:
    submitted = submit_production_job(
        ProductionJobIntent(
            source_url="https://youtu.be/x3nrUagsaV4",
            originating_task="codex-task-123",
        ),
        workspace=tmp_path,
        submitted_at=datetime(2026, 7, 19, 8, 0, tzinfo=UTC),
    )
    acquired_at = datetime(2026, 7, 19, 8, 1, tzinfo=UTC)

    first = acquire_job_lease(submitted.project_dir, "worker-a", now=acquired_at)
    assert submitted.manifest["production_job"]["lease_policy"] == {
        "policy_version": 1,
        "heartbeat_seconds": 15,
        "ttl_seconds": 60,
    }
    assert first["worker_id"] == "worker-a"
    assert first["heartbeat_at"] == "2026-07-19T08:01:00+00:00"

    with pytest.raises(LeaseUnavailable):
        acquire_job_lease(
            submitted.project_dir,
            "worker-b",
            now=datetime(2026, 7, 19, 8, 1, 59, tzinfo=UTC),
        )

    heartbeat_job_lease(
        submitted.project_dir,
        "worker-a",
        generation=first["generation"],
        now=datetime(2026, 7, 19, 8, 1, 30, tzinfo=UTC),
    )
    with pytest.raises(LeaseUnavailable):
        acquire_job_lease(
            submitted.project_dir,
            "worker-b",
            now=datetime(2026, 7, 19, 8, 2, 29, tzinfo=UTC),
        )

    takeover = acquire_job_lease(
        submitted.project_dir,
        "worker-b",
        now=datetime(2026, 7, 19, 8, 2, 30, tzinfo=UTC),
    )
    assert takeover["worker_id"] == "worker-b"
    manifest = load_project(submitted.project_dir)
    assert manifest["production_job"]["lease"] == takeover
    assert manifest["production_job"]["checkpoints"][-1]["kind"] == "lease-takeover"


def test_concurrent_workers_cannot_both_acquire_the_job_lease(tmp_path: Path) -> None:
    submitted = submit_production_job(
        ProductionJobIntent(
            source_url="https://youtu.be/x3nrUagsaV4",
            originating_task="codex-task-123",
        ),
        workspace=tmp_path,
        submitted_at=datetime(2026, 7, 19, 8, 0, tzinfo=UTC),
    )
    start = Barrier(2)

    def acquire(worker_id: str) -> str:
        start.wait()
        try:
            acquire_job_lease(
                submitted.project_dir,
                worker_id,
                now=datetime(2026, 7, 19, 8, 1, tzinfo=UTC),
            )
        except LeaseUnavailable:
            return "unavailable"
        return "acquired"

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = sorted(executor.map(acquire, ("worker-a", "worker-b")))

    assert outcomes == ["acquired", "unavailable"]
    assert load_project(submitted.project_dir)["production_job"]["lease"]["worker_id"] in {
        "worker-a",
        "worker-b",
    }


def test_same_worker_label_restart_requires_ttl_and_gets_a_new_generation(
    tmp_path: Path,
) -> None:
    submitted = submit_production_job(
        ProductionJobIntent(
            source_url="https://youtu.be/x3nrUagsaV4",
            originating_task="codex-task-123",
        ),
        workspace=tmp_path,
        submitted_at=datetime(2026, 7, 19, 8, 0, tzinfo=UTC),
    )
    first = acquire_job_lease(
        submitted.project_dir,
        "launchd-worker",
        now=datetime(2026, 7, 19, 8, 1, tzinfo=UTC),
    )
    with pytest.raises(LeaseUnavailable):
        acquire_job_lease(
            submitted.project_dir,
            "launchd-worker",
            now=datetime(2026, 7, 19, 8, 1, 59, tzinfo=UTC),
        )

    restarted = acquire_job_lease(
        submitted.project_dir,
        "launchd-worker",
        now=datetime(2026, 7, 19, 8, 2, tzinfo=UTC),
    )
    assert restarted["generation"] == first["generation"] + 1
    with pytest.raises(LeaseUnavailable):
        heartbeat_job_lease(
            submitted.project_dir,
            "launchd-worker",
            generation=first["generation"],
            now=datetime(2026, 7, 19, 8, 2, 1, tzinfo=UTC),
        )


def test_resumed_stale_worker_is_fenced_after_lease_takeover(tmp_path: Path) -> None:
    started = Event()
    resume = Event()
    fake_service = tmp_path / "external-fake-service"

    class PausingAdapter(SyntheticProductionAdapter):
        def prepare_lyrics_review(self, request: dict, *, idempotency_key: str) -> dict:
            result = super().prepare_lyrics_review(request, idempotency_key=idempotency_key)
            started.set()
            if not resume.wait(timeout=5):
                raise TimeoutError("test did not resume the paused worker")
            return result

    submitted = submit_production_job(
        ProductionJobIntent(
            source_url="https://youtu.be/x3nrUagsaV4",
            originating_task="codex-task-123",
        ),
        workspace=tmp_path,
        submitted_at=datetime(2026, 7, 19, 8, 0, tzinfo=UTC),
    )
    stale_adapter = PausingAdapter(state_dir=fake_service)
    takeover_adapter = SyntheticProductionAdapter(state_dir=fake_service)

    with ThreadPoolExecutor(max_workers=2) as executor:
        stale_run = executor.submit(
            run_production_job,
            submitted.project_dir,
            stale_adapter,
            worker_id="launchd-worker",
            now=datetime(2026, 7, 19, 8, 5, tzinfo=UTC),
        )
        assert started.wait(timeout=5)
        taken_over = run_production_job(
            submitted.project_dir,
            takeover_adapter,
            worker_id="launchd-worker",
            now=datetime(2026, 7, 19, 8, 6, tzinfo=UTC),
        )
        resume.set()
        with pytest.raises(LeaseUnavailable):
            stale_run.result(timeout=5)

    assert taken_over["production_job"]["state"] == "awaiting-lyrics-review"
    assert stale_adapter.effect_counts == {"prepare-lyrics-review": 1}
    assert takeover_adapter.effect_counts == {}
    assert len(list_outbox_events(submitted.project_dir)) == 1


def test_worker_stops_at_one_hash_bound_lyrics_review_without_duplicate_effects(
    tmp_path: Path,
) -> None:
    submitted = submit_production_job(
        ProductionJobIntent(
            source_url="https://youtu.be/x3nrUagsaV4",
            originating_task="codex-task-123",
        ),
        workspace=tmp_path,
        submitted_at=datetime(2026, 7, 19, 8, 0, tzinfo=UTC),
    )
    adapter = SyntheticProductionAdapter()
    run_at = datetime(2026, 7, 19, 8, 5, tzinfo=UTC)

    first = run_production_job(
        submitted.project_dir,
        adapter,
        worker_id="worker-a",
        now=run_at,
    )
    replay = run_production_job(
        submitted.project_dir,
        adapter,
        worker_id="worker-b",
        now=datetime(2026, 7, 19, 8, 6, tzinfo=UTC),
    )

    assert first["production_job"]["state"] == "awaiting-lyrics-review"
    assert replay["production_job"]["state"] == "awaiting-lyrics-review"
    assert first["production_job"]["lease"] is None
    assert adapter.effect_counts == {"prepare-lyrics-review": 1}
    assert len(first["production_job"]["side_effect_ledger"]) == 1
    assert first["production_job"]["side_effect_ledger"][0]["status"] == "completed"
    assert first["review_gates"]["rights"] == "pending"

    events = list_outbox_events(submitted.project_dir)
    assert len(events) == 1
    assert events[0]["kind"] == "concert-lyrics-review-ready"
    assert events[0]["originating_task"] == "codex-task-123"
    assert events[0]["review_id"] == first["production_job"]["pending_review"]["review_id"]
    assert events[0]["displayed_hashes"] == first["production_job"]["pending_review"]["displayed_hashes"]
    assert (submitted.project_dir / events[0]["path"]).is_file()


def test_review_reply_is_hash_bound_consumed_once_and_rejects_unrelated_ok(
    tmp_path: Path,
) -> None:
    submitted = submit_production_job(
        ProductionJobIntent(
            source_url="https://youtu.be/x3nrUagsaV4",
            originating_task="codex-task-123",
        ),
        workspace=tmp_path,
        submitted_at=datetime(2026, 7, 19, 8, 0, tzinfo=UTC),
    )
    reviewed = run_production_job(
        submitted.project_dir,
        SyntheticProductionAdapter(),
        worker_id="worker-a",
        now=datetime(2026, 7, 19, 8, 5, tzinfo=UTC),
    )
    pending = reviewed["production_job"]["pending_review"]
    assert pending["outbox_cursor"] == 1

    with pytest.raises(PermissionError):
        submit_review_reply(
            submitted.project_dir,
            ReviewReplyIntent(
                reply_id="reply-unrelated",
                originating_task="another-task",
                review_id=pending["review_id"],
                displayed_hashes=tuple(pending["displayed_hashes"]),
                outbox_cursor=pending["outbox_cursor"],
                response="ok",
                received_at=datetime(2026, 7, 19, 8, 6, tzinfo=UTC),
            ),
        )
    with pytest.raises(PermissionError):
        submit_review_reply(
            submitted.project_dir,
            ReviewReplyIntent(
                reply_id="reply-wrong-cursor",
                originating_task="codex-task-123",
                review_id=pending["review_id"],
                displayed_hashes=tuple(pending["displayed_hashes"]),
                outbox_cursor=pending["outbox_cursor"] + 1,
                response="ok",
                received_at=datetime(2026, 7, 19, 8, 6, tzinfo=UTC),
            ),
        )
    with pytest.raises(PermissionError):
        submit_review_reply(
            submitted.project_dir,
            ReviewReplyIntent(
                reply_id="reply-wrong-hash",
                originating_task="codex-task-123",
                review_id=pending["review_id"],
                displayed_hashes=("0" * 64,),
                outbox_cursor=pending["outbox_cursor"],
                response="ok",
                received_at=datetime(2026, 7, 19, 8, 6, tzinfo=UTC),
            ),
        )

    reply = ReviewReplyIntent(
        reply_id="reply-approved-001",
        originating_task="codex-task-123",
        review_id=pending["review_id"],
        displayed_hashes=tuple(pending["displayed_hashes"]),
        outbox_cursor=pending["outbox_cursor"],
        response="  OK  ",
        received_at=datetime(2026, 7, 19, 8, 6, tzinfo=UTC),
    )
    consumed = submit_review_reply(submitted.project_dir, reply)
    replayed = submit_review_reply(submitted.project_dir, reply)

    assert consumed["status"] == "consumed"
    assert replayed["status"] == "already-consumed"
    manifest = load_project(submitted.project_dir)
    job = manifest["production_job"]
    assert job["state"] == "lyrics-approved"
    assert job["pending_review"] is None
    assert job["consumed_reply_ids"] == ["reply-approved-001"]
    assert len(job["review_replies"]) == 1
    reply_reference = job["review_replies"][0]
    reply_content = (submitted.project_dir / reply_reference["path"]).read_bytes()
    assert hashlib.sha256(reply_content).hexdigest() == reply_reference["sha256"]
    assert json.loads(reply_content)["outbox_cursor"] == pending["outbox_cursor"]
    assert manifest["review_gates"]["lyrics"] == "approved"


def test_concurrent_review_reply_redelivery_is_consumed_only_once(tmp_path: Path) -> None:
    submitted = submit_production_job(
        ProductionJobIntent(
            source_url="https://youtu.be/x3nrUagsaV4",
            originating_task="codex-task-123",
        ),
        workspace=tmp_path,
        submitted_at=datetime(2026, 7, 19, 8, 0, tzinfo=UTC),
    )
    reviewed = run_production_job(
        submitted.project_dir,
        SyntheticProductionAdapter(),
        worker_id="worker-a",
        now=datetime(2026, 7, 19, 8, 5, tzinfo=UTC),
    )
    pending = reviewed["production_job"]["pending_review"]
    reply = ReviewReplyIntent(
        reply_id="reply-concurrent-001",
        originating_task="codex-task-123",
        review_id=pending["review_id"],
        displayed_hashes=tuple(pending["displayed_hashes"]),
        outbox_cursor=pending["outbox_cursor"],
        response="ok",
        received_at=datetime(2026, 7, 19, 8, 6, tzinfo=UTC),
    )
    start = Barrier(2)

    def redeliver() -> str:
        start.wait()
        return submit_review_reply(submitted.project_dir, reply)["status"]

    with ThreadPoolExecutor(max_workers=2) as executor:
        statuses = sorted(executor.map(lambda _: redeliver(), range(2)))

    assert statuses == ["already-consumed", "consumed"]
    job = load_project(submitted.project_dir)["production_job"]
    assert job["consumed_reply_ids"] == [reply.reply_id]
    assert len(job["review_replies"]) == 1


def test_outbox_acknowledgement_is_durable_and_replay_safe(tmp_path: Path) -> None:
    submitted = submit_production_job(
        ProductionJobIntent(
            source_url="https://youtu.be/x3nrUagsaV4",
            originating_task="codex-task-123",
        ),
        workspace=tmp_path,
        submitted_at=datetime(2026, 7, 19, 8, 0, tzinfo=UTC),
    )
    run_production_job(
        submitted.project_dir,
        SyntheticProductionAdapter(),
        worker_id="worker-a",
        now=datetime(2026, 7, 19, 8, 5, tzinfo=UTC),
    )
    event = list_outbox_events(submitted.project_dir)[0]

    with pytest.raises(PermissionError):
        acknowledge_outbox_event(
            submitted.project_dir,
            event["event_id"],
            originating_task="wrong-task",
            acknowledged_at=datetime(2026, 7, 19, 8, 5, 30, tzinfo=UTC),
        )
    acknowledged = acknowledge_outbox_event(
        submitted.project_dir,
        event["event_id"],
        originating_task="codex-task-123",
        acknowledged_at=datetime(2026, 7, 19, 8, 5, 30, tzinfo=UTC),
    )
    replayed = acknowledge_outbox_event(
        submitted.project_dir,
        event["event_id"],
        originating_task="codex-task-123",
        acknowledged_at=datetime(2026, 7, 19, 8, 5, 30, tzinfo=UTC),
    )

    assert acknowledged["status"] == "acknowledged"
    assert replayed["status"] == "already-acknowledged"
    assert list_outbox_events(submitted.project_dir) == []
    assert len(list_outbox_events(submitted.project_dir, include_acknowledged=True)) == 1
    manifest = load_project(submitted.project_dir)
    outbox = manifest["production_job"]["review_outbox"]
    assert outbox["acknowledged_event_ids"] == [event["event_id"]]
    assert outbox["cursor"] == 1
    assert len(outbox["delivery_receipts"]) == 1
    receipt = outbox["delivery_receipts"][0]
    assert (submitted.project_dir / receipt["path"]).is_file()


def test_outbox_acknowledgement_adopts_a_receipt_after_manifest_save_loss(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    submitted = submit_production_job(
        ProductionJobIntent(
            source_url="https://youtu.be/x3nrUagsaV4",
            originating_task="codex-task-123",
        ),
        workspace=tmp_path,
        submitted_at=datetime(2026, 7, 19, 8, 0, tzinfo=UTC),
    )
    run_production_job(
        submitted.project_dir,
        SyntheticProductionAdapter(),
        worker_id="worker-a",
        now=datetime(2026, 7, 19, 8, 5, tzinfo=UTC),
    )
    event = list_outbox_events(submitted.project_dir)[0]
    real_save = production_module.save_project
    failed = False

    def lose_manifest_save(project_dir: Path, manifest: dict) -> None:
        nonlocal failed
        receipts = manifest.get("production_job", {}).get("review_outbox", {}).get(
            "delivery_receipts",
            [],
        )
        if not failed and receipts:
            failed = True
            raise OSError("simulated crash after the immutable receipt write")
        real_save(project_dir, manifest)

    monkeypatch.setattr(production_module, "save_project", lose_manifest_save)
    first_ack_at = datetime(2026, 7, 19, 8, 5, 30, tzinfo=UTC)
    with pytest.raises(OSError):
        acknowledge_outbox_event(
            submitted.project_dir,
            event["event_id"],
            originating_task="codex-task-123",
            acknowledged_at=first_ack_at,
        )

    recovered = acknowledge_outbox_event(
        submitted.project_dir,
        event["event_id"],
        originating_task="codex-task-123",
        acknowledged_at=datetime(2026, 7, 19, 8, 6, tzinfo=UTC),
    )
    assert recovered["status"] == "acknowledged"
    assert recovered["receipt"]["acknowledged_at"] == first_ack_at.isoformat()
    assert load_project(submitted.project_dir)["production_job"]["review_outbox"]["cursor"] == 1


def test_approved_job_reaches_one_deduplicated_delivery_review_after_restart(
    tmp_path: Path,
) -> None:
    submitted = submit_production_job(
        ProductionJobIntent(
            source_url="https://youtu.be/x3nrUagsaV4",
            originating_task="codex-task-123",
        ),
        workspace=tmp_path,
        submitted_at=datetime(2026, 7, 19, 8, 0, tzinfo=UTC),
    )
    first_process = SyntheticProductionAdapter()
    review_manifest = run_production_job(
        submitted.project_dir,
        first_process,
        worker_id="worker-a",
        now=datetime(2026, 7, 19, 8, 5, tzinfo=UTC),
    )
    pending = review_manifest["production_job"]["pending_review"]
    review_event = list_outbox_events(submitted.project_dir)[0]
    acknowledge_outbox_event(
        submitted.project_dir,
        review_event["event_id"],
        originating_task="codex-task-123",
        acknowledged_at=datetime(2026, 7, 19, 8, 5, 30, tzinfo=UTC),
    )
    submit_review_reply(
        submitted.project_dir,
        ReviewReplyIntent(
            reply_id="reply-approved-001",
            originating_task="codex-task-123",
            review_id=pending["review_id"],
            displayed_hashes=tuple(pending["displayed_hashes"]),
            outbox_cursor=pending["outbox_cursor"],
            response="ok",
            received_at=datetime(2026, 7, 19, 8, 6, tzinfo=UTC),
        ),
    )

    restarted_process = SyntheticProductionAdapter()
    delivered = run_production_job(
        submitted.project_dir,
        restarted_process,
        worker_id="worker-b",
        now=datetime(2026, 7, 19, 8, 7, tzinfo=UTC),
    )
    replay_process = SyntheticProductionAdapter()
    replayed = run_production_job(
        submitted.project_dir,
        replay_process,
        worker_id="worker-c",
        now=datetime(2026, 7, 19, 8, 8, tzinfo=UTC),
    )

    assert delivered["production_job"]["state"] == "delivery-review-ready"
    assert replayed["production_job"]["state"] == "delivery-review-ready"
    assert restarted_process.effect_counts == {"create-verified-delivery": 1}
    assert replay_process.effect_counts == {}
    assert len(delivered["production_job"]["side_effect_ledger"]) == 2
    assert all(
        effect["status"] == "completed"
        for effect in delivered["production_job"]["side_effect_ledger"]
    )
    assert len(delivered["production_job"]["verified_results"]) == 1
    delivery = delivered["production_job"]["delivery_review"]
    assert delivery["visibility"] == "private"
    assert delivery["approved_hashes"] == list(pending["displayed_hashes"])

    events = list_outbox_events(submitted.project_dir)
    assert len(events) == 1
    assert events[0]["kind"] == "delivery-review-ready"
    assert events[0]["private_url"] == delivery["private_url"]
    assert events[0]["remote_video_id"] == delivery["remote_video_id"]


def test_cli_drives_the_public_synthetic_production_lifecycle(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main([
        "concert",
        "submit-job",
        "https://youtu.be/x3nrUagsaV4?t=42",
        "--workspace",
        str(tmp_path),
        "--originating-task",
        "codex-task-123",
    ]) == 0
    submission = json.loads(capsys.readouterr().out)
    project_dir = submission["project_dir"]

    assert main([
        "concert", "run-job", project_dir, "--worker-id", "worker-a",
    ]) == 0
    waiting = json.loads(capsys.readouterr().out)
    pending = waiting["production_job"]["pending_review"]

    assert main(["concert", "outbox", project_dir]) == 0
    review_events = json.loads(capsys.readouterr().out)
    assert [event["kind"] for event in review_events] == ["concert-lyrics-review-ready"]

    reply_args = [
        "concert", "review-reply", project_dir,
        "--reply-id", "reply-cli-001",
        "--originating-task", "codex-task-123",
        "--review-id", pending["review_id"],
        "--outbox-cursor", str(pending["outbox_cursor"]),
        "--response", "ok",
    ]
    for displayed_hash in pending["displayed_hashes"]:
        reply_args.extend(["--displayed-hash", displayed_hash])
    assert main(reply_args) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "consumed"

    assert main([
        "concert", "run-job", project_dir, "--worker-id", "worker-b",
    ]) == 0
    delivered = json.loads(capsys.readouterr().out)
    assert delivered["production_job"]["state"] == "delivery-review-ready"
    assert len(delivered["production_job"]["side_effect_ledger"]) == 2
    assert delivered["review_gates"]["edit"] == "pending"


def test_worker_recovers_an_idempotent_external_effect_after_response_loss(
    tmp_path: Path,
) -> None:
    submitted = submit_production_job(
        ProductionJobIntent(
            source_url="https://youtu.be/x3nrUagsaV4",
            originating_task="codex-task-123",
        ),
        workspace=tmp_path,
        submitted_at=datetime(2026, 7, 19, 8, 0, tzinfo=UTC),
    )
    fake_service = tmp_path / "external-fake-service"
    first_process = SyntheticProductionAdapter(
        state_dir=fake_service,
        lose_response_once={"prepare-lyrics-review"},
    )

    with pytest.raises(ConnectionError):
        run_production_job(
            submitted.project_dir,
            first_process,
            worker_id="worker-a",
            now=datetime(2026, 7, 19, 8, 5, tzinfo=UTC),
        )
    restarted_process = SyntheticProductionAdapter(state_dir=fake_service)
    recovered = run_production_job(
        submitted.project_dir,
        restarted_process,
        worker_id="worker-b",
        now=datetime(2026, 7, 19, 8, 6, tzinfo=UTC),
    )

    assert recovered["production_job"]["state"] == "awaiting-lyrics-review"
    assert first_process.effect_counts == {"prepare-lyrics-review": 1}
    assert restarted_process.effect_counts == {}
    assert len(list(fake_service.glob("*.json"))) == 1
    assert len(recovered["production_job"]["retry_evidence"]) == 1
    assert recovered["production_job"]["side_effect_ledger"][0]["attempts"] == 2
    assert len(list_outbox_events(submitted.project_dir)) == 1


def test_worker_adopts_an_orphaned_outbox_event_after_manifest_save_loss(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    submitted = submit_production_job(
        ProductionJobIntent(
            source_url="https://youtu.be/x3nrUagsaV4",
            originating_task="codex-task-123",
        ),
        workspace=tmp_path,
        submitted_at=datetime(2026, 7, 19, 8, 0, tzinfo=UTC),
    )
    real_save = production_module.save_project
    failed = False

    def lose_manifest_save(project_dir: Path, manifest: dict) -> None:
        nonlocal failed
        job = manifest.get("production_job", {})
        if not failed and job.get("state") == "awaiting-lyrics-review" and job["review_outbox"]["events"]:
            failed = True
            raise OSError("simulated crash after the immutable outbox write")
        real_save(project_dir, manifest)

    monkeypatch.setattr(production_module, "save_project", lose_manifest_save)
    with pytest.raises(OSError):
        run_production_job(
            submitted.project_dir,
            SyntheticProductionAdapter(),
            worker_id="worker-a",
            now=datetime(2026, 7, 19, 8, 5, tzinfo=UTC),
        )

    recovered = run_production_job(
        submitted.project_dir,
        SyntheticProductionAdapter(),
        worker_id="worker-b",
        now=datetime(2026, 7, 19, 8, 6, tzinfo=UTC),
    )
    assert recovered["production_job"]["state"] == "awaiting-lyrics-review"
    assert len(list_outbox_events(submitted.project_dir)) == 1
