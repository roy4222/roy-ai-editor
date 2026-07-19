# Concert V1 architecture re-review

Date: 2026-07-19
Scope: complete working tree including untracked files, Issue #18 amendment, ticket draft
Result: **PASS**
Publication gate: **PASS FOR TICKET APPROVAL**

This copy records the FABle reviewer handoff returned to Roy after the read-only review worktree was closed. The reviewer approved the proposed ticket granularity, Ticket 9 placement, and dependency graph.

## Original findings

| Finding | Result | Closing evidence |
| --- | --- | --- |
| F-01 governance/vocabulary | CLOSED | ADR 0008–0047, `CONTEXT.md`, blueprint and Issue #18 amendment |
| F-02 Mac production root | CLOSED | ADR 0003 → ADR 0008 supersession; `/Volumes/RoyMedia/RoyAIEditor` |
| F-03 review/gate semantics | CLOSED | ADR 0011/0018 and skill implementation-gap labels |
| F-04 incomplete source subtitles | CLOSED | ADR 0044 track-wide fallback decision tree |
| F-05 technical browser read-only | CLOSED | ADR 0045 default-deny policies, isolated identities and Action Ledger |
| F-06 upload idempotency | CLOSED | ADR 0046 durable session/reconciliation protocol |
| F-07 preregistered thresholds | CLOSED | ADR 0047 and `concert-v1-quality@1.0.0` |

The reviewer replayed 20 failure scenarios: 19 PASS and one PARTIAL concerning a same-name fake volume. Additional adversarial cases—98% burned captions over moving faces, malicious comments, allowlist-external redirects, expired upload sessions with multiple candidates, and encoder pixel drift—had explicit closing mechanisms.

## Ticket-scoped follow-ups

- N-01: Ticket 1 must define durable inbound Review Reply hash binding, single consumption and replay rejection.
- N-02: Ticket 2 must pin a concrete APFS Volume UUID, not only a label/mount point.
- N-04: Tickets 1/11 must fix lease heartbeat/TTL and health/recovery thresholds.
- N-05: Ticket 9 must technically enforce Recovery Vault restore-only behavior.
- N-06/N-07/N-08: tickets must cover Singer Color fixtures, URL canonicalization and explicit Computer Use FAIL handling.

These requirements were added to `docs/plans/2026-07-19-concert-v1-ticket-breakdown-draft.md` before publication. Ticket 3 remains one approved Issue but contains ordered milestone 3A (enforced browsing/capture) followed by 3B (lyrics research/review), limiting risk without changing the approved issue graph.

## Publication hygiene

Before child Issues are created, the architecture sources must be committed and pushed so agents can resolve every referenced ADR/registry path. Documentation and `src/project.py`/tests should be separate commits. Remaining runtime implementation—such as fail-closed RoyMedia mount checks—belongs to the corresponding child ticket rather than this architecture patch.
