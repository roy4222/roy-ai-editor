---
type: investigation
status: draft
date: 2026-07-18
subject: JimLiu/baocut adoption review
---

# BaoCut adoption review

## Executive decision

**Do not make BaoCut the foundation, canonical project store, or renderer of Roy AI Editor.**
Treat it as a future **optional macOS adapter for talking-head transcription/localization** and,
before even doing that, run the bounded spike specified below. For Concert Live, do not insert
BaoCut into the approved-lyrics-to-karaoke path.

The most valuable part is not a component we can presently vendor. It is the workflow design:
file-referenced Agent calls, claim/lease/submit workers, synchronous answer lint, resumable stage
checkpoints, reversible cuts, stale-only recomputation, separate performance and quality reports,
and a bounded repair budget. Reimplement those patterns in Roy's own domain and keep Roy's
`project.json`, Evidence Artifacts, OTIO plan, and FFmpeg/libass renderer authoritative.

The key licensing fact is easy to miss: the GitHub repository's MIT license covers the public
Agent Skill and its shell resolver. The repository explicitly says the skill **does not ship the
engines**; it invokes `baocut-cli` bundled inside the BaoCut Mac app. The inspected repository at
commit [`010dbca`](https://github.com/JimLiu/baocut/tree/010dbca041452a6043e5008d4a463b71ad74655e)
contains Markdown instructions plus a 46-line shell resolver, not the app/CLI engine source.
The app is advertised as free and no-account, but no app/CLI source or separate redistribution/
derivative-work license was found in the official repo, website, privacy page, app bundle, or
appcast. Therefore the safe engineering assumption is: **MIT skill; black-box app/CLI; no right
to copy its engine code inferred.** [Repo README](https://github.com/JimLiu/baocut/blob/010dbca041452a6043e5008d4a463b71ad74655e/README.md),
[MIT license](https://github.com/JimLiu/baocut/blob/010dbca041452a6043e5008d4a463b71ad74655e/LICENSE),
[resolver source](https://github.com/JimLiu/baocut/blob/010dbca041452a6043e5008d4a463b71ad74655e/skills/baocut/bin/baocut)

## What was actually inspected

- Official GitHub repository, all seven commits, tags, MIT license, and all 2,379 lines of the
  public skill/reference material. The repository was created on 2026-07-13 and the inspected
  head was committed on 2026-07-16; this is active but extremely young, not yet a mature
  dependency signal. [GitHub repository metadata](https://api.github.com/repos/JimLiu/baocut)
- Official BaoCut website and privacy policy. [Product page](https://baocut.app/),
  [privacy policy v3](https://baocut.app/privacy/)
- Official stable appcast and its BaoCut 0.4.0 arm64 DMG. The download's size and SHA-256 matched
  the appcast; read-only inspection found a native arm64 app and CLI requiring macOS 15.0. No app
  was installed and no BaoCut project was created. [Official appcast](https://baocut.app/appcast.json)
- `baocut-cli 0.4.0 --help` from that verified bundle, to compare the real public interface with
  the v0.3.2 skill. This exposed one freshness warning: `known-errors.md` still says cloud STT is
  GUI-only, while the 0.4.0 CLI help and appcast say the CLI now supports cloud STT. The version
  contract is good practice, but the public instructions can still lag the binary.

## Architecture and data flow

BaoCut's public operating model is:

```text
local file or yt-dlp URL
  -> local/cloud ASR + word timing + optional diarization
  -> segment / polish / repunct
  -> whole-sentence translation
  -> over-fit-only splitting and alignment
  -> optional reversible A-roll cuts and B-roll attachments
  -> audit + finish-check
  -> SRT / VTT / ASS / Markdown / burned video
```

The GUI and CLI share one BaoCut project. Words are the primary text/timing truth; cues and
translation groups are projections. Translation deliberately separates source cue IDs from
target group IDs, so one natural target sentence may span multiple source cues. This is a strong
localization model and is better than assuming one source cue equals one translated cue.
[Product model](https://baocut.app/#features),
[subtitle address model](https://github.com/JimLiu/baocut/blob/010dbca041452a6043e5008d4a463b71ad74655e/skills/baocut/references/subtitles.md),
[two-phase alignment](https://github.com/JimLiu/baocut/blob/010dbca041452a6043e5008d4a463b71ad74655e/skills/baocut/references/alignment.md)

The LLM seam is unusually good. The CLI does not call an LLM in the Agent path. A worker emits
contract and payload file references; persistent Agent workers atomically claim a call, receive a
lease, write an answer file, and submit it. Submission is fenced by the lease and synchronously
linted; stale or duplicate workers cannot overwrite the accepted response. The root orchestrator
does not ingest every prompt body, which limits context growth. This is worth recreating as a Roy
`AgentTask` protocol rather than coupling to BaoCut project internals.
[Orchestration protocol](https://github.com/JimLiu/baocut/blob/010dbca041452a6043e5008d4a463b71ad74655e/skills/baocut/references/orchestration.md),
[CLI task contract](https://github.com/JimLiu/baocut/blob/010dbca041452a6043e5008d4a463b71ad74655e/skills/baocut/references/commands.md)

BaoCut persists its projects under its app library and says not to write directly into
`~/Library/Application Support/BaoCut/`. URL media may be redirected with `--save-dir`, but no
documented flag relocates the whole project store to RoyMedia. That conflicts with Roy's one
Production Data Root and one Project Manifest unless BaoCut is kept behind an adapter. A BaoCut
project ID may be recorded as external provenance, but BaoCut state must not become a second
current-state authority.

## Capability review

| Area | Official behavior | Fit for Roy |
|---|---|---|
| Download | Accepts yt-dlp-supported URLs, probes metadata first, supports `--save-dir`; on a YouTube bot challenge it may retry with cookies from the macOS default browser. | Reuses a known dependency but is less controllable than Roy's rights-gated ingest. Do not let its cookie fallback silently bind production to Roy's personal browser session. |
| ASR | Local Qwen3-ASR or Whisper on MLX, Silero VAD/forced alignment, optional pyannote speaker work; 0.4.0 adds several cloud STT providers. | Promising Apple-Silicon talking-head baseline. It is not evidence that sung lyrics or mora timing are production-ready. |
| Polish | Terms pre-scan, locked terminology, coverage lint, deterministic term repair, structured `PolishQuality`. | Strong pattern. Preserve the distinction between correction and cutting. |
| Translation | Whole-sentence translation followed by only the necessary split/alignment review; stale-only refresh and protected terms. | Useful for speech localization. Exact `zh` applies a PRC-oriented display policy, so Traditional Chinese must be explicitly proven in a spike. It cannot replace sourced/approved Concert translations. |
| Subtitles | Original cues and target groups are independently addressable; deterministic set/find/replace/retime/split/merge/hide; SRT/VTT/ASS export. | Good model to borrow. BaoCut does not expose Roy's lyrics approval unit, performed repeats, singer colors, kanji-only ruby, or phoneme/mora karaoke contract. |
| Editing | One talking-head A-roll, reversible pause/filler/retake cuts, simple full-screen/PiP B-roll, preview from the export compositor. | Useful optional rough-cut tool for speech. The skill explicitly excludes music, multicam, motion graphics, and arbitrary multitrack compositing, so it is not Roy's general timeline. |
| Dubbing | No TTS, voice selection, voice cloning, mix, or dubbed-video workflow was found in current official skill, CLI help, exports, or product page. | No adoption value here. VideoLingo remains the more relevant dubbing/localization reference. |
| Rendering | Sidecars, Markdown, and a captioned MP4/MOV; cuts and B-roll are applied and captions retimed. | Keep FFmpeg/libass as Roy's deterministic conformance renderer. BaoCut's closed renderer cannot replace golden-frame tests or carry Roy's karaoke layout. |
| UI/headless | Native macOS GUI and a CLI using the same project; CLI supports machine-readable JSON. macOS 15+ and Apple Silicon only. | Nice optional review UI on the Dedicated Editor Host; unacceptable as a cross-platform core or canonical data model. |
| Resume/versioning | Worker resume from page checkpoints, per-stage tasks, project locks, snapshots, branches for partition-changing edits, and stale-only translation refresh. | Highly reusable pattern. Roy should attach its own stage cache keys and Evidence Artifacts to `project.json`; do not mirror BaoCut's private `doc.json`. |
| QA | `task report` for performance, `audit` for quality, `finish-check` for deliverable readiness, synchronous submit lint, exact failure codes, one targeted repair then re-audit. | Best part to borrow. The app's audit is useful evidence but cannot be the sole gate because its rules target speech subtitles and some PRC layout constraints, not Roy's rights, lyrics, ruby, singer, full-width crop, or publish gates. |

Sources for the table: [main skill contract](https://github.com/JimLiu/baocut/blob/010dbca041452a6043e5008d4a463b71ad74655e/skills/baocut/SKILL.md),
[editing reference](https://github.com/JimLiu/baocut/blob/010dbca041452a6043e5008d4a463b71ad74655e/skills/baocut/references/editing.md),
[export reference](https://github.com/JimLiu/baocut/blob/010dbca041452a6043e5008d4a463b71ad74655e/skills/baocut/references/export.md),
[recovery and audit](https://github.com/JimLiu/baocut/blob/010dbca041452a6043e5008d4a463b71ad74655e/skills/baocut/references/recovery.md),
[version/staleness](https://github.com/JimLiu/baocut/blob/010dbca041452a6043e5008d4a463b71ad74655e/skills/baocut/references/versions.md).

## Provider, privacy, and credential boundary

There are two different provider seams:

1. In Agent mode, Codex/Claude supplies LLM answers through files and the CLI never needs an LLM
   key. This is the seam Roy should emulate.
2. BaoCut's GUI also supports cloud LLM providers; app 0.4.0 supports local or cloud
   transcription. The CLI documents `BAOCUT_API_KEY_<PROVIDERID>` for cloud STT, while the app
   settings can retain keys. Treat these as Private Configuration and never place them in the
   public repo or command logs.

The privacy policy says local transcription/media stay on-device; explicitly enabled cloud AI
receives selected transcript text under the user's provider agreement. Anonymous product usage is
enabled by default but requires an onboarding decision before the first send, and can be disabled;
update checks are separate
and run automatically unless disabled. The policy also says no account is required and BaoCut does
not receive API keys, media, prompts, transcripts, file paths, or source URLs. These are useful
claims, but a production spike must verify outbound behavior and settings rather than convert a
policy statement into an architecture guarantee. [Privacy policy](https://baocut.app/privacy/)

Security rules for any spike:

- local fixture only; no cloud model, API key, YouTube cookie, or personal browser profile;
- disable analytics and automatic crash upload; record whether update checks remain enabled;
- never write BaoCut's app-support files directly or expose them through Git;
- record the exact app build, skill commit, model IDs, commands, and output hashes;
- do not install the skill globally until the spike is approved; invoke a pinned adapter path.

## Relationship to the current plan

### Concert Live

BaoCut's word-first transcript is the wrong truth source for songs. Concert Live correctly treats
the versioned official lyrics, Traditional Chinese translation provenance, performed repeats, and
display line map as one approval unit. ASR is timing evidence only. BaoCut also lacks rights
research, Bahamut evidence, multi-singer lyric attribution, furigana/ruby layout, karaoke tags,
full-width burned-pixel crop inspection, YouTube packaging, and Roy's approval semantics.

**Decision:** no BaoCut stage between lyrics approval and render. At most, a future isolated
experiment may compare its ASR word timings against stable-ts on a synthetic singing fixture; it
must never overwrite approved lyrics or timing.

### VideoLingo

There is substantial overlap in download, ASR, subtitle segmentation, terminology, translation,
alignment, resume, and export. VideoLingo is Apache-2.0 and exposes implementation source; BaoCut
offers a cleaner native-Mac UX and stronger Agent task/audit contracts but hides the engine.

**Decision:** keep VideoLingo as the inspectable localization/dubbing reference. Borrow BaoCut's
orchestration and QA patterns. Only an evidence-backed spike can justify BaoCut as an external
runtime adapter for speech projects; do not build two canonical localization pipelines.

### FFmpeg/libass and OTIO

BaoCut's internal timeline covers one A-roll plus soft cuts and B-roll. Roy's planned OTIO layer
must remain the renderer-neutral editorial interchange for multi-source work, and FFmpeg/libass
must remain default conformance. If a BaoCut adapter is adopted, it should translate exported word
timings/cuts into Roy `Artifact`/`EditPlan`/OTIO structures and hand rendering back to Roy. Never
make `.baocut`/`doc.json` or a BaoCut project ID the timeline IR.

## Build vs adopt

### Adopt directly, but only behind a future optional adapter

- The official Mac app and CLI as an external executable for a narrow talking-head spike.
- Its local MLX ASR/diarization result if measured better or materially easier than Roy's baseline.
- Its GUI as an optional human review surface, never as the only inspection path.

### Rebuild as Roy-owned patterns

- `AgentTask`: contract/payload file references, persistent pull workers, leases, idempotent submit,
  synchronous schema/semantic lint, late-answer quarantine.
- `StageCheckpoint`: input fingerprint, engine/model/config versions, completed pages, resume token,
  explicit stale downstream artifacts.
- `EditProposal`: reversible soft cut/B-roll suggestion with rationale and provenance, compiled into
  Roy `EditPlan` and later OTIO.
- `QualityReport` versus `PerformanceReport`, plus deliverable-specific `FinishCheck`.
- One bounded targeted repair and one re-audit, rather than recursive “fix everything” loops.
- Version handshake between an installed skill/adapter and its executable.

### Do not adopt

- BaoCut app state as Project Manifest or Production Data Root.
- The app/CLI binary as a redistributed or vendored dependency until the owner supplies an explicit
  app/CLI redistribution/integration license.
- Its word-first model for Concert lyrics, its exact-`zh` layout rules as Traditional Chinese
  policy, or its audit as sufficient release evidence.
- Automatic default-browser cookie access, cloud-provider credentials in shell history, or opaque
  cloud calls in the default workflow.
- Its renderer as a substitute for OTIO plus FFmpeg/libass, or its basic B-roll model as a general
  editor.

## Minimum adoption spike

Run this only after Roy approves installing the official app. Pin app 0.4.0/build 14, skill commit
`010dbca`, and the local ASR model. Use a 3–5 minute, public/synthetic, single-speaker test fixture
with named entities, code-switching, pauses, a false start, and prepared gold English/Japanese and
Traditional Chinese text. Keep it inside one Media Project on RoyMedia; import with a local path.

### Procedure

1. Inventory every BaoCut-created path before/after; disable analytics and cloud providers. Do not
   permit network after the local model is present.
2. Transcribe locally, then deliberately terminate after at least one completed page and resume.
3. Drive polish/translate with one persistent Agent worker and the JSON claim/lease/submit protocol.
4. Correct one locked term, change one source cue, and prove only dependent translation becomes
   stale and only that range refreshes.
5. Produce one reversible pause cut, one context-dependent filler decision, and one PiP B-roll;
   restore and reapply them.
6. Export Markdown, source SRT, Traditional Chinese SRT/ASS, and a short video preview. Register
   commands, hashes, model/app versions, BaoCut project ID, audit JSON, and finish-check JSON as
   Roy Evidence Artifacts. Do not copy private app state into Git.
7. Convert exported timings and edit decisions into Roy structures and render the same preview via
   the existing FFmpeg/libass path; compare outputs, not just screenshots of the BaoCut GUI.

### Pass criteria

- No network transmission of media/transcript and no credential/browser-cookie access; all
  unexpected outbound attempts are recorded and fail the spike.
- The interrupted run resumes without redoing completed ASR/pages; duplicate/stale Agent submits
  cannot overwrite the accepted result.
- JSON output is parseable and stable for every scripted command; no prompt or answer body appears
  in stdout, analytics, or the public repo.
- Gold transcript word coverage is 100%; named entities and locked terms are exact; no source word
  is silently dropped/duplicated. Traditional Chinese output is actually supported and does not
  silently apply Simplified-Chinese wording.
- On 20 gold timing anchors, median absolute boundary error is at most 120 ms and p95 at most
  250 ms; every worse sample is inspectable. This criterion is for speech only, not singing.
- Restore returns byte-equivalent edit state; stale-only refresh leaves unrelated target groups
  byte-identical; source/cut/B-roll/version provenance is present.
- BaoCut audit and finish-check pass for the requested preview, and Roy's independent probe,
  subtitle, pixel, duration, and hash checks also pass.
- Peak resident memory stays below 18 GB on the 24 GB Mac mini, the run leaves at least 25 GB free,
  and every app-library/model/cache location is inventoried. Large reusable models may live outside
  the Media Project only if Roy explicitly accepts that storage exception.
- The adapter can copy/export evidence into `/Volumes/RoyMedia/RoyAIEditor/projects/...` without
  making BaoCut's internal project the current-state authority.

### Go/no-go

**Go** only as an optional `BaoCutAdapter` for speech projects if every pass criterion holds and it
beats the inspectable baseline on either measured quality, operator time, or reliability. **No-go**
for production dependency if Traditional Chinese cannot be controlled, project state cannot be
externalized, outbound behavior cannot be bounded, output contracts drift without compatibility
tests, or the closed app becomes necessary to render an Approved Deliverable.

## Final recommendation

BaoCut is a very good source of workflow ideas and a plausible future convenience tool for the
Mac mini. It is not a replacement for the Upstream Foundation, VideoLingo research baseline,
Concert Live Workflow, OTIO, or FFmpeg/libass. The next product move should be to copy the **deep
contracts**—task leases, checkpoint fingerprints, reversible proposals, staleness, evidence, and
bounded QA—into Roy-owned modules. Defer BaoCut installation/adoption until the talking-head
workflow is ready for the spike; it does not unblock the current Concert Live Phase 0.
