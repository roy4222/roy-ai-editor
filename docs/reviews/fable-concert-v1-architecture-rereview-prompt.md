# Prompt for FABle — Concert V1 architecture re-review

Perform a strictly read-only second architecture review of Concert V1 in:

- local repo: `/Users/beimian/Documents/Codex/2026-07-18/d/roy-ai-editor`
- parent spec: <https://github.com/roy4222/roy-ai-editor/issues/18>
- remediation map: `docs/reviews/2026-07-19-concert-v1-architecture-remediation.md`
- ticket draft: `docs/plans/2026-07-19-concert-v1-ticket-breakdown-draft.md`

Important visibility instruction: inspect the complete local working tree, not only `git ls-files`, the default branch, remote branches, or committed files. Start with `git status --short`, enumerate `docs/adr/0001-*` through `docs/adr/0047-*` from the filesystem, and open the local production blueprint and quality registry. ADR 0008–0047 and the blueprint may still be untracked; treating untracked architecture files as nonexistent would repeat the first review’s scope error. Do not modify files, Issues, labels, branches, or tickets.

## Review task

Re-evaluate the original F-01 through F-07 findings against current evidence:

1. Governance completeness and canonical vocabulary, including `Concert Live Workflow`, all runtime concepts in `CONTEXT.md`, the blueprint, and Issue #18’s appended architecture amendment.
2. ADR 0003 → ADR 0008 supersession and the Mac mini `/Volumes/RoyMedia/RoyAIEditor` production root.
3. Sole-review directly-following `ok` semantics, packet/hash binding, and the target removal of fixed timing/deliverable gates versus explicitly labeled current CLI implementation gaps.
4. The formerly impossible 98% source-Japanese cases: partial soft, partial burned, moving/unsafe burned region, fallback/skip/version-bound exception, and the prohibition on line-by-line mixed modes.
5. Technical read-only browser enforcement, credential/profile separation, prompt-injection containment, action logging, Studio least-role proof, unexpected navigation, and the absence of browser upload/edit fallbacks.
6. Crash-safe YouTube resumable upload idempotency: pre-network intent, session secret persistence order, first-byte barrier, completion response loss, session expiry, exact-marker own-channel reconciliation, zero/one/multiple candidate outcomes, and atomic video-ID persistence.
7. `concert-v1-quality@1.0.0`: preregistered fixture populations, denominators, timing tiers, ruby/pixel/browser/publish/resource gates, exact normalized-output rules, post-result change control, and final acceptance counts.

Then rerun the report’s original failure-scenario reasoning, or reconstruct all 20 scenarios if the original report is unavailable. Pay special attention to adversarial cases: 98% burned captions over a moving face; malicious timeline comments instructing tool use; redirect to an unlisted domain; Studio restriction visibility requiring a stronger role; upload completion response lost after remote creation; expired session with zero/multiple reconciliation candidates; Mac memory pressure while local alignment is slow; and a maintenance candidate whose encoder changes pixels while metrics still pass.

Finally review the 12-ticket draft as a tracer-bullet decomposition of Issue #18. Check that each ticket delivers observable end-to-end behavior, has enough context/acceptance criteria for an AFK agent, does not create component-layer tickets, does not duplicate scope, respects the dependency graph, delays secrets/real URLs until necessary, and cannot claim Production Golden Path before ticket 12. Flag missing parent-story coverage or any ticket that is too broad/small.

## Required output

- Overall architecture verdict: `PASS`, `CONDITIONAL PASS`, or `FAIL`.
- Publication gate: `PASS FOR TICKET APPROVAL` or `NOT READY`.
- A table mapping F-01 through F-07 to `CLOSED`, `PARTIAL`, or `OPEN`, with exact file/line or Issue-section evidence.
- New findings ranked P0/P1/P2, separating architecture defects from working-tree publication/commit hygiene.
- A 20-scenario matrix with pass/fail and the exact mechanism that closes each scenario.
- Ticket review: per-ticket verdict, missing acceptance criteria, suggested split/merge, and corrected blocking edges.
- A final checklist stating whether it is safe for Roy to approve child-Issue publication.

Do not mark a finding open merely because the remediation is uncommitted; report that separately as publication hygiene. Do mark it open if the current local sources conflict, leave an undefined mechanism, rely only on prompt intent, or cannot be tested objectively.
