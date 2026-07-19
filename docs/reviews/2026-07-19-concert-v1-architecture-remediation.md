# Concert V1 architecture remediation

Date: 2026-07-19
Input: FABle conditional-pass summary for Issue #18
Scope: architecture/spec only; no child implementation Issues created

The review report path quoted in the handoff, `docs/reviews/2026-07-19-concert-v1-architecture-review.md`, was not present in this working tree. This remediation therefore maps the seven findings exactly as quoted by Roy and asks the next reviewer to verify the underlying evidence directly.

## Result

All seven quoted P1 findings now have an explicit governing source in the current working tree, and Issue #18 contains an appended architecture amendment covering ADR 0044–0047. This is a remediation claim, not the second reviewer’s PASS; ticket publication remains gated on both FABle approval and Roy’s approval of ticket granularity/dependencies.

| Finding | Remediation | Verification sources |
| --- | --- | --- |
| F-01 governance sources missing | The working tree contains ADR 0008–0047, the production blueprint, complete domain vocabulary, and a single canonical product-slice term. The earlier review likely inspected only tracked/remote files; the next review must inspect untracked working-tree files. | `CONTEXT.md`; `NORTH_STAR.md`; `docs/adr/0008-*` through `0047-*`; `docs/plans/2026-07-18-concert-v1-production-blueprint.md`; Issue #18 amendment |
| F-02 Windows data root conflicts with Mac mini | ADR 0003 is `superseded`; ADR 0008 is accepted and fixes the host/root to the dedicated Mac mini and `/Volumes/RoyMedia/RoyAIEditor`. | `docs/adr/0003-separate-source-code-from-production-assets.md`; `docs/adr/0008-run-production-on-the-dedicated-mac-mini.md` |
| F-03 `ok` and fixed-gate contradictions | ADR 0011 defines sole-review, directly-following `ok`; ADR 0018 removes a fixed timing gate; the skill labels existing CLI timing/deliverable commands as temporary implementation gaps. | `docs/adr/0011-use-exception-based-review-after-lyrics-approval.md`; `docs/adr/0018-use-tiered-timing-fidelity-for-karaoke-subtitles.md`; `skills/roy-edit-concert-live/SKILL.md`; `skills/roy-edit-concert-live/references/lyrics-approval-gate.md` |
| F-04 98% source-Japanese dead end | ADR 0044 introduces one track-wide Source Subtitle Fallback Plan: incomplete soft tracks are disabled; incomplete burned text requires deterministic whole-track Caption Region Replacement; unsafe replacement yields an exact skip/version exception instead of mixed modes. | `docs/adr/0044-handle-incomplete-source-japanese-with-a-track-wide-fallback.md`; `CONTEXT.md`; source-subtitle audit, workflow, quality standard, registry |
| F-05 browser read-only is only aspirational | ADR 0045 requires isolated discovery/Studio identities, domain/path allowlists, default-deny action policy, content boundaries, output limits, Browser Action Ledger, untrusted-content handling, and fail-closed mutation/navigation. Studio uses the least role proven by fixtures. | `docs/adr/0045-enforce-read-only-browser-operation-with-isolated-profiles.md`; ADR 0033; skill/workflow; registry §3 |
| F-06 upload idempotency protocol missing | ADR 0046 defines a pre-network deterministic Publish Intent, durable secret session reference before media bytes, exact private marker, session-status recovery, own-channel orphan reconciliation, atomic video-ID persistence, and fail-closed zero/multiple-match behavior. | `docs/adr/0046-reconcile-resumable-youtube-uploads-before-retrying.md`; ADR 0012/0041; skill/workflow; registry §4 |
| F-07 quantitative thresholds unregistered | ADR 0047 makes one versioned registry authoritative and prevents post-result weakening without versioning/full rerun. Registry 1.0.0 fixes fixture populations, timing/ruby/pixel/browser/publish/resource gates, normalization, and acceptance counts. | `docs/adr/0047-preregister-concert-v1-quality-thresholds.md`; `docs/quality/concert-v1-quality-registry.md`; ADR 0034/0042; blueprint |

## Security and protocol basis

- agent-browser documents opt-in encrypted auth, content boundaries, domain allowlists, action policies, confirmations, and output limits. Because these controls are opt-in, ADR 0045 requires pinned production configuration rather than relying on defaults: <https://github.com/vercel-labs/agent-browser#security>.
- YouTube channel permissions provide viewer-style delegated roles but do not cover every feature; therefore Studio restriction visibility is a fixture-tested capability, not an assumed role property: <https://support.google.com/youtube/answer/9481328>.
- YouTube’s resumable protocol returns a session URI, requires clients to retain it, supports status queries after interruption, and returns the completion response when a completed session is queried. ADR 0046 makes that sequence crash-safe and adds orphan reconciliation: <https://developers.google.com/youtube/v3/guides/using_resumable_upload_protocol>.

## Remaining gate

The current source/architecture changes are still local working-tree changes. The second FABle review must inspect the complete working tree, including untracked ADRs and plans, and compare the Issue #18 amendment. Child Issue publication remains intentionally blocked until:

1. FABle returns architecture PASS and ticket decomposition READY.
2. Roy confirms the numbered ticket granularity and blocking edges in the draft breakdown.
