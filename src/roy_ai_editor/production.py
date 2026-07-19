"""Durable Concert Production Job lifecycle."""

from __future__ import annotations

import fcntl
import hashlib
import json
import re
from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from importlib import resources
from pathlib import Path
from typing import IO, Iterator, Literal, Protocol
from urllib.parse import parse_qs, urlparse

from .project import (
    create_project,
    load_project,
    record_evidence,
    save_project,
    write_immutable_json,
)


YOUTUBE_HOSTS = {
    "m.youtube.com",
    "music.youtube.com",
    "www.youtube.com",
    "youtu.be",
    "youtube.com",
}
YOUTUBE_VIDEO_ID = re.compile(r"[A-Za-z0-9_-]{6,64}")
TRACER_TOOLCHAIN_RELEASE = {
    "id": "concert-v1-tracer@1.0.0",
    "components": {
        "production_job_schema": 1,
        "synthetic_adapter_contract": 1,
    },
}
QUALITY_REGISTRY_ID = "concert-v1-quality@1.0.0"
QUALITY_REGISTRY_REPO_PATH = Path("docs/quality/concert-v1-quality-registry.md")


class LeaseUnavailable(RuntimeError):
    """Raised when another live worker owns a Production Job lease."""


@dataclass(frozen=True)
class CanonicalYoutubeSource:
    submitted_url: str
    canonical_url: str
    video_id: str


@dataclass(frozen=True)
class ProductionJobIntent:
    source_url: str
    selection_mode: Literal["all", "selected"] = "all"
    selected_tracks: tuple[str, ...] = ()
    profile_id: str = "roy-public-example"
    originating_task: str = "local"


@dataclass(frozen=True)
class ProductionSubmission:
    project_dir: Path
    job_id: str
    request_id: str
    manifest: dict


@dataclass(frozen=True)
class ReviewReplyIntent:
    reply_id: str
    originating_task: str
    review_id: str
    displayed_hashes: tuple[str, ...]
    outbox_cursor: int
    response: str
    received_at: datetime


class ProductionAdapter(Protocol):
    def prepare_lyrics_review(self, request: dict, *, idempotency_key: str) -> dict: ...

    def create_verified_delivery(
        self,
        request: dict,
        approved_hashes: list[str],
        *,
        idempotency_key: str,
    ) -> dict: ...


class SyntheticProductionAdapter:
    """Deterministic fake used by the lifecycle tracer and public CLI smoke."""

    def __init__(
        self,
        *,
        state_dir: Path | None = None,
        lose_response_once: set[str] | None = None,
    ) -> None:
        self._results: dict[str, dict] = {}
        self.effect_counts: dict[str, int] = {}
        self.state_dir = state_dir.expanduser().resolve() if state_dir else None
        self._lose_response_once = set(lose_response_once or ())
        if self.state_dir:
            self.state_dir.mkdir(parents=True, exist_ok=True)

    def _once(self, kind: str, idempotency_key: str, payload: dict) -> dict:
        created = False
        if self.state_dir:
            result_path = self.state_dir / (
                hashlib.sha256(idempotency_key.encode()).hexdigest() + ".json"
            )
            if result_path.exists():
                result = json.loads(result_path.read_text(encoding="utf-8"))
            else:
                write_immutable_json(result_path, payload)
                result = payload
                created = True
        elif idempotency_key in self._results:
            result = self._results[idempotency_key]
        else:
            self._results[idempotency_key] = payload
            result = payload
            created = True
        if created:
            self.effect_counts[kind] = self.effect_counts.get(kind, 0) + 1
            if kind in self._lose_response_once:
                self._lose_response_once.remove(kind)
                raise ConnectionError(
                    "response lost after the synthetic external service persisted the result"
                )
        return result

    def prepare_lyrics_review(self, request: dict, *, idempotency_key: str) -> dict:
        packet_sha = hashlib.sha256(
            f"{request['source_video_id']}:synthetic-lyrics-packet:v1".encode()
        ).hexdigest()
        return self._once("prepare-lyrics-review", idempotency_key, {
            "schema_version": 1,
            "kind": "concert-lyrics-review",
            "displayed_hashes": [packet_sha],
            "tracks": [{
                "track_id": "001-synthetic-song",
                "title": "Synthetic Song",
                "lyrics_packet_sha256": packet_sha,
            }],
        })

    def create_verified_delivery(
        self,
        request: dict,
        approved_hashes: list[str],
        *,
        idempotency_key: str,
    ) -> dict:
        video_id = hashlib.sha256(f"{idempotency_key}:video".encode()).hexdigest()[:11]
        return self._once("create-verified-delivery", idempotency_key, {
            "schema_version": 1,
            "kind": "synthetic-private-delivery",
            "approved_hashes": approved_hashes,
            "private_url": f"https://youtu.be/{video_id}",
            "remote_video_id": video_id,
            "visibility": "private",
        })


def canonicalize_youtube_url(submitted_url: str) -> CanonicalYoutubeSource:
    parsed = urlparse(submitted_url)
    hostname = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or hostname not in YOUTUBE_HOSTS or parsed.username or parsed.password:
        raise ValueError("Concert source must be an HTTPS YouTube URL on an allowed host")

    path_parts = [part for part in parsed.path.split("/") if part]
    if hostname == "youtu.be":
        candidate = path_parts[0] if len(path_parts) == 1 else ""
    elif parsed.path == "/watch":
        candidate = parse_qs(parsed.query).get("v", [""])[0]
    elif len(path_parts) == 2 and path_parts[0] in {"embed", "live", "shorts"}:
        candidate = path_parts[1]
    else:
        candidate = ""

    if not YOUTUBE_VIDEO_ID.fullmatch(candidate):
        raise ValueError("Concert source does not contain a valid YouTube video ID")
    return CanonicalYoutubeSource(
        submitted_url=submitted_url,
        canonical_url=f"https://www.youtube.com/watch?v={candidate}",
        video_id=candidate,
    )


def _canonical_json(payload: object) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()


@contextmanager
def _production_job_lock(project_dir: Path) -> Iterator[IO[str]]:
    lock_path = project_dir.expanduser().resolve() / ".production-job.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield handle
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _quality_registry_pin() -> dict:
    checkout_path = Path(__file__).resolve().parents[2] / QUALITY_REGISTRY_REPO_PATH
    if checkout_path.is_file():
        content = checkout_path.read_bytes()
    else:
        content = resources.files("roy_ai_editor").joinpath(
            "resources",
            "quality",
            "concert-v1-quality-registry.md",
        ).read_bytes()
    return {
        "id": QUALITY_REGISTRY_ID,
        "path": QUALITY_REGISTRY_REPO_PATH.as_posix(),
        "sha256": hashlib.sha256(content).hexdigest(),
    }


def _toolchain_release_pin() -> dict:
    return {
        **TRACER_TOOLCHAIN_RELEASE,
        "sha256": hashlib.sha256(_canonical_json(TRACER_TOOLCHAIN_RELEASE)).hexdigest(),
    }


def _normalize_intent(intent: ProductionJobIntent) -> tuple[CanonicalYoutubeSource, dict]:
    source = canonicalize_youtube_url(intent.source_url)
    if intent.selection_mode not in {"all", "selected"}:
        raise ValueError("selection_mode must be 'all' or 'selected'")
    tracks = sorted({track.strip() for track in intent.selected_tracks if track.strip()})
    if intent.selection_mode == "all" and tracks:
        raise ValueError("selected_tracks must be empty when selection_mode is 'all'")
    if intent.selection_mode == "selected" and not tracks:
        raise ValueError("selected_tracks are required when selection_mode is 'selected'")
    if not intent.profile_id.strip() or not intent.originating_task.strip():
        raise ValueError("profile_id and originating_task must not be blank")
    return source, {
        "source_video_id": source.video_id,
        "track_selection": {"mode": intent.selection_mode, "tracks": tracks},
        "profile_id": intent.profile_id.strip(),
    }


def submit_production_job(
    intent: ProductionJobIntent,
    *,
    workspace: Path,
    submitted_at: datetime | None = None,
) -> ProductionSubmission:
    source, identity_payload = _normalize_intent(intent)
    identity_sha = hashlib.sha256(_canonical_json(identity_payload)).hexdigest()
    job_id = f"job-{identity_sha[:16]}"
    project_id = f"{source.video_id}-{identity_sha[:12]}"
    project_dir, _ = create_project(source.canonical_url, workspace, project_id=project_id)
    with _production_job_lock(project_dir):
        manifest = load_project(project_dir)
        return _persist_production_submission(
            project_dir,
            manifest,
            intent,
            source,
            identity_payload,
            identity_sha,
            job_id,
            submitted_at,
        )


def _persist_production_submission(
    project_dir: Path,
    manifest: dict,
    intent: ProductionJobIntent,
    source: CanonicalYoutubeSource,
    identity_payload: dict,
    identity_sha: str,
    job_id: str,
    submitted_at: datetime | None,
) -> ProductionSubmission:
    timestamp = _utc_now(submitted_at).isoformat()
    toolchain_release = _toolchain_release_pin()
    quality_registry = _quality_registry_pin()
    request_payload = {
        "schema_version": 1,
        "job_id": job_id,
        "source_url": source.submitted_url,
        "canonical_source_url": source.canonical_url,
        "source_video_id": source.video_id,
        "track_selection": identity_payload["track_selection"],
        "profile_id": identity_payload["profile_id"],
        "originating_task": intent.originating_task.strip(),
        "intake_authorization": {
            "authorization_version": 1,
            "granted_via": "source-url-submission",
            "scope": ["local-processing", "private-youtube-upload"],
            "granted_at": timestamp,
        },
        "toolchain_release": toolchain_release,
        "quality_registry": quality_registry,
        "submitted_at": timestamp,
    }
    request_sha = hashlib.sha256(_canonical_json(request_payload)).hexdigest()
    request_id = f"request-{request_sha[:16]}"
    request_payload["request_id"] = request_id
    request_reference = record_evidence(
        project_dir,
        "production-job-request",
        request_payload,
        directory="requests",
    )
    production_job = manifest.setdefault("production_job", {
        "schema_version": 1,
        "job_id": job_id,
        "identity_sha256": identity_sha,
        "originating_task": intent.originating_task.strip(),
        "profile_id": identity_payload["profile_id"],
        "toolchain_release": toolchain_release,
        "quality_registry": quality_registry,
        "source_video_id": source.video_id,
        "track_selection": identity_payload["track_selection"],
        "state": "queued",
        "lease": None,
        "lease_policy": {
            "policy_version": 1,
            "heartbeat_seconds": 15,
            "ttl_seconds": 60,
        },
        "checkpoints": [],
        "retry_evidence": [],
        "requests": [],
        "review_replies": [],
        "consumed_reply_ids": [],
        "verified_results": [],
        "review_outbox": {
            "events": [],
            "acknowledged_event_ids": [],
            "delivery_receipts": [],
            "cursor": 0,
        },
        "side_effect_ledger": [],
    })
    if production_job.get("identity_sha256") != identity_sha:
        raise RuntimeError("Production Job identity conflicts with the existing Media Project")
    if production_job.get("toolchain_release") != toolchain_release:
        raise RuntimeError("Production Job is pinned to a different Toolchain Release")
    if production_job.get("quality_registry") != quality_registry:
        raise RuntimeError("Production Job is pinned to a different Concert V1 Quality Registry")
    if not any(item["id"] == request_reference["id"] for item in production_job["requests"]):
        production_job["requests"].append(request_reference)
        manifest.setdefault("evidence_artifacts", []).append(request_reference)
        save_project(project_dir, manifest)
    return ProductionSubmission(project_dir, job_id, request_id, manifest)


def _utc_now(value: datetime | None = None) -> datetime:
    result = value or datetime.now(UTC)
    if result.tzinfo is None:
        raise ValueError("Production lifecycle timestamps must include a timezone")
    return result.astimezone(UTC)


def acquire_job_lease(
    project_dir: Path,
    worker_id: str,
    *,
    now: datetime | None = None,
) -> dict:
    project_dir = project_dir.expanduser().resolve()
    with _production_job_lock(project_dir):
        return _acquire_job_lease_unlocked(project_dir, worker_id, now=now)


def _acquire_job_lease_unlocked(
    project_dir: Path,
    worker_id: str,
    *,
    now: datetime | None = None,
) -> dict:
    if not worker_id.strip():
        raise ValueError("worker_id must not be blank")
    current_time = _utc_now(now)
    manifest = load_project(project_dir)
    job = manifest["production_job"]
    current = job.get("lease")
    checkpoint_kind = "lease-acquired"
    if current:
        heartbeat_at = datetime.fromisoformat(current["heartbeat_at"])
        ttl = timedelta(seconds=int(job["lease_policy"]["ttl_seconds"]))
        if current_time < heartbeat_at + ttl:
            raise LeaseUnavailable(
                f"Production Job lease is held by {current['worker_id']} until its heartbeat TTL expires"
            )
        checkpoint_kind = "lease-takeover"

    lease = {
        "worker_id": worker_id.strip(),
        "acquired_at": current_time.isoformat(),
        "heartbeat_at": current_time.isoformat(),
        "generation": int(current.get("generation", 0) if current else 0) + 1,
    }
    job["lease"] = lease
    job["checkpoints"].append({
        "kind": checkpoint_kind,
        "at": current_time.isoformat(),
        "worker_id": worker_id.strip(),
        "previous_worker_id": current.get("worker_id") if current else None,
        "previous_heartbeat_at": current.get("heartbeat_at") if current else None,
    })
    save_project(project_dir, manifest)
    return lease


def heartbeat_job_lease(
    project_dir: Path,
    worker_id: str,
    *,
    generation: int,
    now: datetime | None = None,
) -> dict:
    project_dir = project_dir.expanduser().resolve()
    with _production_job_lock(project_dir):
        return _heartbeat_job_lease_unlocked(
            project_dir,
            worker_id,
            generation=generation,
            now=now,
        )


def _heartbeat_job_lease_unlocked(
    project_dir: Path,
    worker_id: str,
    *,
    generation: int,
    now: datetime | None = None,
) -> dict:
    current_time = _utc_now(now)
    manifest = load_project(project_dir)
    job = manifest["production_job"]
    lease = job.get("lease")
    _assert_lease_owner(job, worker_id, generation)
    if current_time < datetime.fromisoformat(lease["heartbeat_at"]):
        raise ValueError("heartbeat time cannot move backwards")
    lease["heartbeat_at"] = current_time.isoformat()
    save_project(project_dir, manifest)
    return lease


def release_job_lease(
    project_dir: Path,
    worker_id: str,
    *,
    generation: int | None = None,
) -> None:
    project_dir = project_dir.expanduser().resolve()
    with _production_job_lock(project_dir):
        _release_job_lease_unlocked(project_dir, worker_id, generation=generation)


def _release_job_lease_unlocked(
    project_dir: Path,
    worker_id: str,
    *,
    generation: int | None = None,
) -> None:
    manifest = load_project(project_dir)
    job = manifest["production_job"]
    lease = job.get("lease")
    if not lease and generation is None:
        return
    _assert_lease_owner(job, worker_id, generation)
    job["lease"] = None
    save_project(project_dir, manifest)


def _assert_lease_owner(job: dict, worker_id: str, generation: int | None) -> None:
    lease = job.get("lease")
    if not lease or lease.get("worker_id") != worker_id:
        raise LeaseUnavailable("Production Job worker has been fenced by lease takeover")
    if generation is not None and lease.get("generation") != generation:
        raise LeaseUnavailable("Production Job worker has been fenced by lease generation")


def _request_payload(project_dir: Path, job: dict) -> dict:
    reference = job["requests"][0]
    return json.loads((project_dir / reference["path"]).read_text(encoding="utf-8"))


def _effect_result(project_dir: Path, reference: dict) -> dict:
    return json.loads((project_dir / reference["path"]).read_text(encoding="utf-8"))


def _run_adapter_effect(
    project_dir: Path,
    *,
    worker_id: str,
    lease_generation: int,
    kind: str,
    idempotency_key: str,
    now: datetime,
    invoke: Callable[[], dict],
) -> tuple[dict, dict]:
    with _production_job_lock(project_dir):
        manifest = load_project(project_dir)
        job = manifest["production_job"]
        _assert_lease_owner(job, worker_id, lease_generation)
        entry = next(
            (
                item
                for item in job["side_effect_ledger"]
                if item["idempotency_key"] == idempotency_key
            ),
            None,
        )
        if entry and entry["status"] == "completed":
            reference = entry["result_evidence"]
            return _effect_result(project_dir, reference), reference
        if entry is None:
            entry = {
                "effect_id": f"effect-{hashlib.sha256(idempotency_key.encode()).hexdigest()[:16]}",
                "kind": kind,
                "idempotency_key": idempotency_key,
                "status": "planned",
                "planned_at": now.isoformat(),
                "attempts": 0,
            }
            job["side_effect_ledger"].append(entry)
        entry["attempts"] += 1
        save_project(project_dir, manifest)
    try:
        result = invoke()
    except Exception as exc:
        with _production_job_lock(project_dir):
            manifest = load_project(project_dir)
            job = manifest["production_job"]
            _assert_lease_owner(job, worker_id, lease_generation)
            job["retry_evidence"].append({
                "kind": kind,
                "idempotency_key": idempotency_key,
                "attempted_at": now.isoformat(),
                "error_type": type(exc).__name__,
            })
            save_project(project_dir, manifest)
        raise

    with _production_job_lock(project_dir):
        manifest = load_project(project_dir)
        job = manifest["production_job"]
        _assert_lease_owner(job, worker_id, lease_generation)
        reference = record_evidence(project_dir, f"{kind}-result", result, directory="work")
        entry = next(
            item
            for item in job["side_effect_ledger"]
            if item["idempotency_key"] == idempotency_key
        )
        entry.update({
            "status": "completed",
            "completed_at": now.isoformat(),
            "result_evidence": reference,
        })
        if not any(item["id"] == reference["id"] for item in manifest["evidence_artifacts"]):
            manifest["evidence_artifacts"].append(reference)
        save_project(project_dir, manifest)
    return result, reference


def _adopt_or_write_immutable_json(
    path: Path,
    payload: dict,
    *,
    retry_variant_fields: tuple[str, ...] = (),
) -> tuple[dict, str]:
    if not path.exists():
        return payload, write_immutable_json(path, payload)
    existing_bytes = path.read_bytes()
    existing = json.loads(existing_bytes)
    expected_stable = dict(payload)
    existing_stable = dict(existing)
    for field in retry_variant_fields:
        expected_stable.pop(field, None)
        existing_stable.pop(field, None)
    if existing_stable != expected_stable:
        raise RuntimeError(f"Immutable artifact conflicts with durable retry identity: {path}")
    return existing, hashlib.sha256(existing_bytes).hexdigest()


def _append_outbox_event(project_dir: Path, manifest: dict, event: dict) -> dict:
    outbox = manifest["production_job"]["review_outbox"]
    events = outbox["events"]
    dedupe_key = event["dedupe_key"]
    event_id = f"outbox-{hashlib.sha256(dedupe_key.encode()).hexdigest()[:16]}"
    existing = next((item for item in events if item["event_id"] == event_id), None)
    if existing:
        return existing
    payload = {
        "schema_version": 1,
        "event_id": event_id,
        "outbox_cursor": len(events) + 1,
        **event,
    }
    relative = Path("outbox") / "events" / f"{event_id}.json"
    durable_payload, sha = _adopt_or_write_immutable_json(
        project_dir / relative,
        payload,
        retry_variant_fields=("created_at",),
    )
    reference = {**durable_payload, "path": relative.as_posix(), "sha256": sha}
    events.append(reference)
    return reference


def list_outbox_events(project_dir: Path, *, include_acknowledged: bool = False) -> list[dict]:
    outbox = load_project(project_dir)["production_job"]["review_outbox"]
    if include_acknowledged:
        return list(outbox["events"])
    acknowledged = set(outbox["acknowledged_event_ids"])
    return [event for event in outbox["events"] if event["event_id"] not in acknowledged]


def acknowledge_outbox_event(
    project_dir: Path,
    event_id: str,
    *,
    originating_task: str,
    acknowledged_at: datetime | None = None,
) -> dict:
    project_dir = project_dir.expanduser().resolve()
    with _production_job_lock(project_dir):
        return _acknowledge_outbox_event_unlocked(
            project_dir,
            event_id,
            originating_task=originating_task,
            acknowledged_at=acknowledged_at,
        )


def _acknowledge_outbox_event_unlocked(
    project_dir: Path,
    event_id: str,
    *,
    originating_task: str,
    acknowledged_at: datetime | None = None,
) -> dict:
    manifest = load_project(project_dir)
    outbox = manifest["production_job"]["review_outbox"]
    event = next((item for item in outbox["events"] if item["event_id"] == event_id), None)
    if not event:
        raise KeyError(f"Unknown Review Outbox event: {event_id}")
    if event["originating_task"] != originating_task:
        raise PermissionError("Review Outbox event belongs to a different Codex task")
    acknowledged_ids = outbox["acknowledged_event_ids"]
    if event_id in acknowledged_ids:
        receipt = next(
            item for item in outbox.get("delivery_receipts", []) if item["event_id"] == event_id
        )
        return {"status": "already-acknowledged", "receipt": receipt}

    timestamp = _utc_now(acknowledged_at).isoformat()
    receipt_payload = {
        "schema_version": 1,
        "event_id": event_id,
        "originating_task": originating_task,
        "acknowledged_at": timestamp,
        "event_sha256": event["sha256"],
    }
    relative = Path("outbox") / "receipts" / f"{event_id}.json"
    durable_receipt, sha = _adopt_or_write_immutable_json(
        project_dir / relative,
        receipt_payload,
        retry_variant_fields=("acknowledged_at",),
    )
    receipt = {
        "id": f"receipt-{sha[:16]}",
        "kind": "outbox-delivery-receipt",
        "event_id": event_id,
        "path": relative.as_posix(),
        "sha256": sha,
        "acknowledged_at": durable_receipt["acknowledged_at"],
    }
    acknowledged_ids.append(event_id)
    outbox.setdefault("delivery_receipts", []).append(receipt)
    acknowledged = set(acknowledged_ids)
    cursor = 0
    for candidate in outbox["events"]:
        if candidate["event_id"] not in acknowledged:
            break
        cursor += 1
    outbox["cursor"] = cursor
    manifest["evidence_artifacts"].append(receipt)
    save_project(project_dir, manifest)
    return {"status": "acknowledged", "receipt": receipt}


def submit_review_reply(project_dir: Path, reply: ReviewReplyIntent) -> dict:
    project_dir = project_dir.expanduser().resolve()
    with _production_job_lock(project_dir):
        return _submit_review_reply_unlocked(project_dir, reply)


def _submit_review_reply_unlocked(project_dir: Path, reply: ReviewReplyIntent) -> dict:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{2,127}", reply.reply_id):
        raise ValueError("reply_id must be a stable identifier")
    received_at = _utc_now(reply.received_at)
    payload = {
        "schema_version": 1,
        "reply_id": reply.reply_id,
        "originating_task": reply.originating_task.strip(),
        "review_id": reply.review_id,
        "displayed_hashes": list(reply.displayed_hashes),
        "outbox_cursor": reply.outbox_cursor,
        "response": reply.response.strip().lower(),
        "received_at": received_at.isoformat(),
    }
    relative = Path("replies") / f"{reply.reply_id}.json"
    sha = write_immutable_json(project_dir / relative, payload)
    reference = {
        "id": f"reply-{sha[:16]}",
        "kind": "review-reply",
        "path": relative.as_posix(),
        "sha256": sha,
    }

    manifest = load_project(project_dir)
    job = manifest["production_job"]
    consumed_ids = job.setdefault("consumed_reply_ids", [])
    if reply.reply_id in consumed_ids:
        return {"status": "already-consumed", "reply": reference}
    pending = job.get("pending_review")
    if not pending or pending.get("kind") != "concert-lyrics-review":
        raise PermissionError("No Concert Lyrics Review is pending")
    if payload["originating_task"] != pending["originating_task"]:
        raise PermissionError("Review Reply belongs to a different Codex task")
    if payload["review_id"] != pending["review_id"]:
        raise PermissionError("Review Reply is stale or targets a different review")
    if payload["displayed_hashes"] != pending["displayed_hashes"]:
        raise PermissionError("Review Reply hashes do not match the displayed review")
    if payload["outbox_cursor"] != pending["outbox_cursor"]:
        raise PermissionError("Review Reply cursor does not match the displayed review")
    if payload["response"] != "ok":
        raise PermissionError("Only a sole-review directly-following 'ok' approves this tracer review")

    if not any(item["id"] == reference["id"] for item in job["review_replies"]):
        job["review_replies"].append(reference)
        manifest["evidence_artifacts"].append(reference)
    consumed_ids.append(reply.reply_id)
    job["pending_review"] = None
    job["state"] = "lyrics-approved"
    job["approved_review"] = {
        "review_id": pending["review_id"],
        "displayed_hashes": pending["displayed_hashes"],
        "reply_id": reply.reply_id,
        "reply_sha256": sha,
    }
    job["checkpoints"].append({
        "kind": "lyrics-review-approved",
        "at": received_at.isoformat(),
        "review_id": pending["review_id"],
        "reply_id": reply.reply_id,
    })
    manifest["review_gates"]["lyrics"] = "approved"
    manifest["stage"] = "lyrics-approved"
    manifest["status"] = manifest["stage"]
    save_project(project_dir, manifest)
    return {"status": "consumed", "reply": reference}


def run_production_job(
    project_dir: Path,
    adapter: ProductionAdapter,
    *,
    worker_id: str,
    now: datetime | None = None,
) -> dict:
    project_dir = project_dir.expanduser().resolve()
    current_time = _utc_now(now)
    lease = acquire_job_lease(project_dir, worker_id, now=current_time)
    lease_generation = int(lease["generation"])
    succeeded = False
    try:
        manifest = load_project(project_dir)
        job = manifest["production_job"]
        if job["state"] == "queued":
            request = _request_payload(project_dir, job)
            idempotency_key = f"{job['job_id']}:prepare-lyrics-review:v1"
            result, reference = _run_adapter_effect(
                project_dir,
                worker_id=worker_id,
                lease_generation=lease_generation,
                kind="prepare-lyrics-review",
                idempotency_key=idempotency_key,
                now=current_time,
                invoke=lambda: adapter.prepare_lyrics_review(
                    request,
                    idempotency_key=idempotency_key,
                ),
            )
            review_id = f"review-{reference['sha256'][:16]}"
            pending_review = {
                "kind": "concert-lyrics-review",
                "review_id": review_id,
                "displayed_hashes": list(result["displayed_hashes"]),
                "artifact": reference,
                "originating_task": job["originating_task"],
            }
            with _production_job_lock(project_dir):
                manifest = load_project(project_dir)
                job = manifest["production_job"]
                _assert_lease_owner(job, worker_id, lease_generation)
                outbox_event = _append_outbox_event(project_dir, manifest, {
                    "dedupe_key": f"{job['job_id']}:lyrics-review:{review_id}",
                    "kind": "concert-lyrics-review-ready",
                    "job_id": job["job_id"],
                    "originating_task": job["originating_task"],
                    "review_id": review_id,
                    "displayed_hashes": list(result["displayed_hashes"]),
                    "artifact_sha256": reference["sha256"],
                    "created_at": current_time.isoformat(),
                })
                pending_review["outbox_cursor"] = outbox_event["outbox_cursor"]
                job["pending_review"] = pending_review
                job["state"] = "awaiting-lyrics-review"
                job["checkpoints"].append({
                    "kind": "lyrics-review-prepared",
                    "at": current_time.isoformat(),
                    "review_id": review_id,
                    "artifact_sha256": reference["sha256"],
                })
                manifest["stage"] = "lyrics-review-required"
                manifest["status"] = manifest["stage"]
                save_project(project_dir, manifest)
        elif job["state"] == "lyrics-approved":
            request = _request_payload(project_dir, job)
            approved_hashes = list(job["approved_review"]["displayed_hashes"])
            idempotency_key = f"{job['job_id']}:create-verified-delivery:v1"
            result, reference = _run_adapter_effect(
                project_dir,
                worker_id=worker_id,
                lease_generation=lease_generation,
                kind="create-verified-delivery",
                idempotency_key=idempotency_key,
                now=current_time,
                invoke=lambda: adapter.create_verified_delivery(
                    request,
                    approved_hashes,
                    idempotency_key=idempotency_key,
                ),
            )
            with _production_job_lock(project_dir):
                manifest = load_project(project_dir)
                job = manifest["production_job"]
                _assert_lease_owner(job, worker_id, lease_generation)
                if not any(item["id"] == reference["id"] for item in job["verified_results"]):
                    job["verified_results"].append(reference)
                job["delivery_review"] = {
                    "kind": "delivery-review",
                    "artifact": reference,
                    "approved_hashes": approved_hashes,
                    "private_url": result["private_url"],
                    "remote_video_id": result["remote_video_id"],
                    "visibility": result["visibility"],
                }
                job["state"] = "delivery-review-ready"
                job["checkpoints"].append({
                    "kind": "delivery-review-prepared",
                    "at": current_time.isoformat(),
                    "artifact_sha256": reference["sha256"],
                    "remote_video_id": result["remote_video_id"],
                })
                manifest["stage"] = "delivery-review-ready"
                manifest["status"] = manifest["stage"]
                _append_outbox_event(project_dir, manifest, {
                    "dedupe_key": f"{job['job_id']}:delivery-review:{reference['sha256']}",
                    "kind": "delivery-review-ready",
                    "job_id": job["job_id"],
                    "originating_task": job["originating_task"],
                    "approved_hashes": approved_hashes,
                    "private_url": result["private_url"],
                    "remote_video_id": result["remote_video_id"],
                    "visibility": result["visibility"],
                    "artifact_sha256": reference["sha256"],
                    "created_at": current_time.isoformat(),
                })
                save_project(project_dir, manifest)
        succeeded = True
    finally:
        if succeeded:
            release_job_lease(
                project_dir,
                worker_id,
                generation=lease_generation,
            )
    return load_project(project_dir)
