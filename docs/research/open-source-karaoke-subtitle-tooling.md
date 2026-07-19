# Open-source karaoke and subtitle tooling for Roy AI Editor

**Date:** 2026-07-18
**Scope:** Concert Live source-subtitle discovery, Japanese/Chinese subtitle production, lyric-to-audio alignment, furigana, ASS karaoke rendering, and pixel-level QA on an Apple Silicon Mac mini.
**Method:** Primary project repositories and their linked documentation were reviewed. No package, model, or media was downloaded and no candidate was installed.

## Executive recommendation

Do not replace the Concert Live workflow with another end-to-end karaoke application. The repo already owns the parts that are specific to Roy: approved lyrics as Workflow Text Authority, source-Japanese-subtitle reuse, Traditional Chinese placement, Ruby Map evidence, approval gates, project manifests, deliverables, and retention. None of the surveyed projects provides that complete policy.

Instead, keep Roy AI Editor as the headless orchestrator and add small, replaceable adapters around mature components:

1. **Adopt directly:** continue using [FFmpeg/ffprobe](https://github.com/FFmpeg/FFmpeg) and [libass](https://github.com/libass/libass); add [pysubs2](https://github.com/tkarabela/pysubs2) for soft-subtitle parsing and normalization if its ASS round-trip spike passes.
2. **Adapter candidates:** use [Video Subtitle Extractor (VSE)](https://github.com/YaoFANGUK/video-subtitle-extractor) only for burned-in-subtitle discovery; benchmark [audio-separator](https://github.com/nomadkaraoke/python-audio-separator) as an optional vocal-isolation preprocessor; keep alignment engines behind the existing Alignment Adapter seam.
3. **Optional human recovery tools:** [Aegisub](https://github.com/TypesettingTools/Aegisub) and [Subtitle Edit](https://github.com/SubtitleEdit/subtitleedit) are useful review/editing workbenches, but neither should become the production core or project source of truth.
4. **Reference, do not import wholesale:** [karaoke-gen](https://github.com/nomadkaraoke/karaoke-gen), [Karaoke Mugen](https://github.com/karaokemugen), and [Vilm Lyrics Aligner](https://github.com/banjuman/vilm-lyrics-aligner) contain good ideas, but their product boundaries do not match Roy's Live-video, bilingual, source-subtitle-first workflow.
5. **Reject for new integration:** archived `python-lyrics-transcriber`, archived `sc0ty/subsync`, and stale demo repos. Their maintained successors or narrower alternatives are better choices.

The immediate payoff is not another editor. It is a deterministic source-subtitle audit before lyrics generation: inspect streams, sample the burned pixels, detect whether Japanese is already present, and route either to “reuse Japanese + add Chinese” or to the existing generated Japanese/ruby path.

## Current repo baseline and actual gaps

| Stage | Already present in Roy AI Editor | Gap worth filling | Avoid duplicating |
|---|---|---|---|
| Source inspection | The Concert Live skill requires a Source Subtitle Audit and screenshot validation | Machine-readable stream inventory; soft-subtitle extraction; hard-subtitle OCR candidates | Do not create a new video demuxer or OCR engine |
| Lyrics authority | Approved Lyrics Packet, provenance, translation and Ruby Evidence Policy | Better discovery inputs and disagreement reporting | Do not allow OCR/ASR/online lyrics to silently replace approved text |
| Alignment | `alignment.py` exposes stable-ts transcription/forced alignment and preserves approved text | Engine benchmark, singing robustness, confidence/fallback semantics | Do not bind the workflow directly to one model's JSON schema |
| Furigana | `karaoke.py` has pykakasi draft generation, Ruby Map override and evidence rules | A maintained second analyzer and explicit OOV/disagreement signals | Do not treat morphological analysis as authoritative for ateji, names, or lyric-specific readings |
| Subtitle authoring | `karaoke.py` creates bilingual ASS, `\\kf` timing, Japanese/Chinese styles and layout | Safe parsing/normalization of existing subtitle tracks; robust ASS round-trip | Do not replace Roy's layout, Ruby Map, or approval semantics with a generic editor |
| Rendering | FFmpeg burns ASS; libass is already the effective renderer | Record renderer/font versions and make the QA render use the same build | Do not add a second production renderer |
| Visual QA | `karaoke_visual_qa.py` samples the burned MP4 and creates full-width crops/contact sheets | Source-video preflight; automated text-change/OCR evidence; per-line verdict manifest | Do not validate only the ASS source or an editor preview |

## Recommended shortlist

Status and activity are observations as of the research date, not guarantees. License compatibility should be rechecked at the exact version pinned for distribution.

| Project | Primary role | macOS / Apple Silicon | Headless surface | License / maintenance | Decision |
|---|---|---|---|---|---|
| [FFmpeg/ffprobe](https://github.com/FFmpeg/FFmpeg) | Stream inspection/extraction, frame sampling, render pipeline | Mature native builds | CLI | LGPL with optional GPL components; highly active | **Adopt directly; already foundational** |
| [libass](https://github.com/libass/libass) | Canonical ASS/SSA renderer | Native; used by FFmpeg builds | C library / FFmpeg filter | ISC; active | **Adopt directly; already effective renderer** |
| [pysubs2](https://github.com/tkarabela/pysubs2) | SRT/VTT/ASS parsing, retiming, normalization | Pure Python | Python API + small CLI | MIT; active | **Adopt if round-trip spike passes** |
| [Video Subtitle Extractor](https://github.com/YaoFANGUK/video-subtitle-extractor) | Hard-subtitle region detection, OCR, SRT candidates | CPU path documented; CoreML/Apple Silicon path is explicitly untested | Python CLI plus GUI | Apache-2.0; active | **Thin external adapter after Mac spike** |
| [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) | Japanese OCR engine underlying video/OCR systems | Cross-platform, but packaging must be verified on target | Python/API/CLI | Apache-2.0; active | **Use through an adapter; do not rebuild video dedup/timing first** |
| [audio-separator](https://github.com/nomadkaraoke/python-audio-separator) | Vocal/instrumental separation before alignment | Official Apple Silicon/CoreML path for Sonoma+ | Python API + CLI + JSON model listing | MIT; active | **Optional alignment preprocessor spike** |
| [stable-ts](https://github.com/jianfch/stable-ts) | Existing word timing/forced alignment baseline | macOS installation documented | Python API + CLI | MIT; archived 2026-05-30 and development indefinitely paused | **Freeze as legacy benchmark; replace production default** |
| [WhisperX](https://github.com/m-bain/whisperX) | Speech transcription plus phoneme alignment | CPU mode can run on Mac; performance is CUDA-oriented | Python API + CLI | BSD-2-Clause; active | **Benchmark candidate, not presumed singing solution** |
| [ffsubsync](https://github.com/smacke/ffsubsync) | Coarse global subtitle offset/framerate correction | Homebrew FFmpeg + Python works on Mac | CLI / Python | MIT; active | **Narrow optional adapter for existing soft subtitles** |
| [Sudachi](https://github.com/WorksApplications/sudachi.rs) | Japanese morphology and dictionary reading/OOV evidence | macOS ARM64/universal Python wheels are published; target install still needs a spike | Python API / Rust | Apache-2.0; active | **Preferred primary furigana evidence analyzer** |
| [fugashi](https://github.com/polm/fugashi) | Independent MeCab/UniDic reading cross-check | Project has shipped Apple Silicon wheels | Python API | MIT; bundled MeCab is BSD; lower activity | **Bounded second-analyzer candidate** |
| [Aegisub](https://github.com/TypesettingTools/Aegisub) | Waveform timing, ASS typesetting, karaoke templating | Upstream documents Apple Silicon/Homebrew build path | GUI; Lua automation, not a production service API | GPL-compatible mix; official macOS build is GPLv2; maintained but fragmented across forks | **Optional Exception Review GUI only** |
| [Subtitle Edit](https://github.com/SubtitleEdit/subtitleedit) | OCR, visual sync, bilingual editing, format conversion | macOS 12+ self-contained build; unsigned-app setup caveat | GUI plus .NET CLI capabilities | MIT; very active | **Optional OCR/format/recovery GUI** |
| [karaoke-gen](https://github.com/nomadkaraoke/karaoke-gen) | End-to-end karaoke generation, separation, transcription/review, publishing | Apple Silicon CPU is a recommended local option | CLI, Python, remote job API | MIT; very active | **Architecture/reference source; do not adopt wholesale** |
| [Vilm Lyrics Aligner](https://github.com/banjuman/vilm-lyrics-aligner) | Supplied-lyrics-to-live-singing line alignment | Explicit Apple Silicon Metal/CPU support | Python engine plus GUI/Resolve panel | MIT; brand-new, very small project | **Experimental reference/spike only** |
| [Karaoke Mugen GitHub mirror](https://github.com/karaokemugen) | Karaoke catalog/player ecosystem and authoring conventions | Apple Silicon releases exist; main development is on GitLab | Primarily application/editor ecosystem | Repository licenses must be checked per component; active | **Reference metadata/ASS conventions only** |

## Findings by workflow stage

### 1. Detect and reuse source Japanese subtitles

There are two different problems and they should stay separate.

**Soft subtitle streams:** use `ffprobe` JSON as the canonical inventory and FFmpeg `-map` extraction for each subtitle stream. This is already in the repo's dependency family and is more deterministic than launching an editor. Parse extracted SRT/VTT/ASS with pysubs2 into a normalized candidate record containing stream index, codec, language tag, title, event count, time coverage and original artifact hash. Keep the untouched extracted file as evidence.

**Burned-in subtitles:** VSE is the strongest purpose-built candidate reviewed. It combines subtitle-region detection, OCR, non-subtitle/watermark filtering and SRT generation, supports Japanese among many languages, and exposes a Python CLI. Its current documentation says macOS CPU mode works but Apple Silicon/CoreML is untested; it also documents restrictive path handling. Therefore run it as a subprocess adapter in a simple ASCII/no-space scratch directory and treat all output as a candidate, never Workflow Text Authority.

For both paths, the decision still comes from the pixels. Sample opening, verse, chorus, bridge and closing frames; preserve crops and timestamps; measure text presence/continuity; then route:

- complete, validated Japanese source subtitles → preserve Japanese pixels/text and render Chinese below;
- incomplete, unreadable, badly timed, or absent source Japanese → use the approved Lyrics Packet and Roy's generated Japanese/ruby path;
- ambiguous → Exception Review with crops, extracted/OCR text and confidence, not a generic “what should I do?” pause.

[VideOCR](https://github.com/timminator/VideOCR) is a reasonable backup/reference because it combines PaddleOCR, SSIM filtering and event merging, but its official setup focuses on Windows/Linux/Docker and its Google Lens mode adds a cloud/privacy boundary. [SubtitleOCR](https://github.com/nhjydywd/SubtitleOCR) has a Mac GUI and Apple Silicon claims, but lacks a clear headless API and uses GPL-3.0; keep it as a manual comparison tool, not a core adapter.

### 2. Align approved Japanese lyrics to live singing

No surveyed general ASR or forced aligner is trustworthy enough to directly publish mora-level karaoke timing for a live performance. Speech-oriented models face vibrato, long vowels, ad-libs, crowd noise, band bleed, repeated choruses and lyric deviations. The repo's existing rule remains correct: approved text is immutable input; an aligner proposes spans; confidence and coverage decide whether to use fine timing or fall back to line-level timing.

- **stable-ts:** freeze as a reproducible legacy baseline because it is already integrated, but do not keep it as the production default: the repository was archived on 2026-05-30 and development is indefinitely paused.
- **Qwen3-ASR/ForcedAligner:** keep the separately documented bounded Mac benchmark. Qwen's ASR claims Japanese, singing and background-music capability are especially relevant; the ForcedAligner is still officially described for speech and short inputs, so it must earn use on the golden Live set.
- **WhisperX:** useful comparator for word alignment and active maintenance. Its language-specific alignment models, unalignable characters and speech-centric limitations mean it is not an automatic upgrade for Japanese singing.
- **audio-separator:** a promising optional preprocessor rather than an editor. It has CLI/API integration and an official Apple Silicon CoreML route. Benchmark raw-mix alignment against isolated-vocal alignment; keep separation only when it improves timing without damaging syllable onsets.
- **Vilm Lyrics Aligner:** unusually relevant because it explicitly targets live singing while preserving supplied lyrics and supports Apple Silicon. However, its documented language focus is Korean/English, output is line-level, and the project is very new. Use it only as an experimental line-timing comparator until Japanese results and maintenance mature.

`ffsubsync` can estimate a global offset for an existing soft subtitle track by correlating voice activity, but it does not solve split/merge changes or word/mora timing and music can confuse VAD. It belongs in a narrow “repair imported subtitles” adapter, not the lyric aligner.

### 3. Build Japanese readings and bilingual ASS

Keep the current Ruby Map and evidence policy. An analyzer should produce evidence fields, not silently overwrite readings.

- Replace pykakasi as the sole draft source with **Sudachi** dictionary readings plus explicit OOV status. Sudachi is actively maintained under Apache-2.0 and exposes a modern Python path from the Rust implementation.
- Evaluate **fugashi + UniDic** as the independent second analyzer. Agreement between Sudachi and UniDic is useful evidence; disagreement, OOV, names, ateji and lyric-specific pronunciation must go to the Ruby Map/Exception Review.
- Keep **pykakasi** only as a fallback/draft source unless its GPL-3.0 distribution implications are explicitly accepted. Its transliteration output is not production truth.

For subtitle data structures, pysubs2 can remove hand-written SRT/VTT/ASS parsing and routine retiming. It should not own Roy's furigana layout or karaoke timing tags until a round-trip test proves it preserves styles, unknown ASS override tags, `\\kf`, Unicode, BOM/encoding and event ordering. Continue generating the final visual policy in `karaoke.py` and rendering it through the same libass build used in QA.

Aegisub is the best optional human workbench for waveform timing, ASS positioning and karaoke templates. It also provides established furigana/karaoke authoring conventions. But it is GUI-first, its active development is split between upstream and forks such as [arch1t3cht/Aegisub](https://github.com/arch1t3cht/Aegisub), and Lua automation is not an appropriate headless service boundary. Import/export ASS only; never let its project file become the manifest.

Subtitle Edit is broader for OCR, format cleanup, visual sync and bilingual/original-column editing. It is valuable for difficult exceptions and cross-checks, but its breadth does not replace Roy's policy layer. Keep it outside the unattended happy path.

### 4. Render and verify the pixels

The existing production direction is sound: libass through FFmpeg should remain the single canonical renderer, and `karaoke_visual_qa.py` should inspect the actually burned MP4. Strengthen it rather than adding an editor renderer:

- record FFmpeg/libass version, fonts and hashes in the QA manifest;
- run the source-subtitle audit before any new subtitle render;
- sample boundaries as well as midpoints so disappearing/reappearing source text is caught;
- retain full-width bottom crops/contact sheets and add per-line verdicts;
- optionally OCR the burned result only as a mismatch signal; compare against approved text but do not equate OCR failure with render failure;
- route low-confidence rows to screenshot/Computer Use review with timestamped evidence.

This avoids the common preview mismatch where an editor looks correct but the final libass/font environment differs.

## What to borrow from end-to-end projects

`karaoke-gen` is the most useful architectural reference, but adopting it as the editor would duplicate the repo's orchestration. Borrow these patterns instead:

- resumable jobs with explicit states and review checkpoints;
- isolated adapters for source acquisition, separation, transcription, correction, rendering and upload;
- machine-readable artifacts between stages;
- idempotent publishing and recoverable review links.

Do not inherit its assumptions that the goal is a new karaoke backing video, that online lyrics/transcription may be the primary text, or that its review UI owns the final data. Roy's target is an existing Live video, often with Japanese already burned in, plus approved Traditional Chinese and strict provenance.

Karaoke Mugen is valuable as a reference for durable karaoke metadata and community ASS authoring conventions, not as a generator. Its player/catalog/application boundary is different. `python-lyrics-transcriber` is archived and explicitly consolidated into karaoke-gen, so integrating it separately would create dead-end coupling.

## Bounded spikes and acceptance criteria

Only these three spikes are justified before changing the production workflow.

### Spike A — source-subtitle audit adapter

Use FFmpeg/ffprobe + pysubs2 for soft streams and VSE CPU mode for burned-in candidates on a small fixture set: no subtitles, soft Japanese, burned Japanese, bilingual burned subtitles, persistent watermark/chat, and partial-song subtitles.

**Pass criteria:**

- stream inventory/extraction is deterministic and preserves original artifacts/hashes;
- Japanese presence/absence classification is correct on every fixture;
- complete-vs-partial coverage routes correctly on every fixture;
- OCR never becomes authoritative and every candidate line links to source timestamp/crop;
- the Apple Silicon CPU run completes without a GUI, works from the managed ASCII scratch path, and reports runtime/peak disk/RAM;
- a VSE failure degrades to screenshot review rather than blocking the whole project.

### Spike B — Japanese Live alignment benchmark

Run the same approved lyrics and gold annotations through current stable-ts, the planned Qwen candidate, and WhisperX; compare raw mix and one audio-separator vocal stem. Use short clips containing verse, chorus, crowd noise, long vowels, ad-libs and a lyric deviation.

**Pass criteria:**

- line-boundary median absolute error ≤ 250 ms and 95th percentile ≤ 600 ms for automatic line-level use;
- fine timing is enabled only if token coverage ≥ 98%, no approved characters are rewritten, and the existing human screenshot/audio review passes;
- any engine that changes text, invents spans, or crosses line order is rejected for that clip;
- separation is retained only if it improves the preregistered timing metrics on the majority of clips without increasing catastrophic misses;
- runtime, memory, model/cache size and fallback reason are recorded in one normalized Alignment Adapter result.

These thresholds are initial engineering gates, not claims about perceptual perfection; tune them only from the gold set, not from a single successful song.

### Spike C — ASS/furigana interoperability and pixel QA

Parse and re-emit representative Roy ASS with pysubs2; generate reading evidence with Sudachi and fugashi; burn with the pinned FFmpeg/libass environment; compare to existing output and review contact sheets.

**Pass criteria:**

- ASS event count, timestamps, styles, layer/order, Unicode, `\\kf` values and unknown override tags survive a semantic round-trip;
- no generated reading is accepted when analyzers disagree, the token is OOV, or an approved Ruby Map value exists;
- a gold set of kanji+okurigana, names, ateji, repeated lyrics and punctuation yields the expected ruby span boundaries;
- burned-frame image comparison shows no unexpected layout change; all Japanese/Chinese baselines, safe areas and overlap rules pass at target resolution;
- output remains reproducible headlessly; Aegisub/Subtitle Edit are optional inspection tools only.

## Integration boundary

The stable architecture is:

```text
Project Manifest / approved Lyrics Packet
  -> Source Subtitle Audit Adapter
       -> ffprobe/FFmpeg (soft streams + frame evidence)
       -> VSE/PaddleOCR candidate (hard subtitles, optional)
  -> Workflow Text Authority decision
  -> Alignment Adapter
       -> stable-ts | Qwen | WhisperX | experimental Vilm
       -> optional audio-separator preprocessor
  -> Ruby Evidence Adapter
       -> approved Ruby Map > official source > Sudachi/fugashi agreement > review
  -> Roy ASS generator
  -> pinned FFmpeg + libass render
  -> burned-pixel QA manifest / Exception Review
  -> deliverable and idempotent publish adapter
```

Every external tool should receive explicit input artifacts and return normalized JSON plus output hashes, tool/model version, command/configuration, confidence and logs. It must be killable, retryable and replaceable. No tool may mutate the approved Lyrics Packet or project manifest in place.

## Explicit reject/reference list

- [sc0ty/subsync](https://github.com/sc0ty/subsync): archived and deprecated; reject for new work. Use ffsubsync only for its narrow global-offset role.
- [python-lyrics-transcriber](https://github.com/nomadkaraoke/python-lyrics-transcriber): archived and consolidated into karaoke-gen; reject standalone integration.
- [Kuroshiro](https://github.com/hexenq/kuroshiro): useful furigana concepts but stale compared with Sudachi and adds a JavaScript analysis stack; reference only.
- [VideOCR](https://github.com/timminator/VideOCR): useful OCR/dedup reference and backup Docker candidate, not first Apple Silicon adapter.
- [SubtitleOCR](https://github.com/nhjydywd/SubtitleOCR): optional manual Mac validator; GUI-first and GPL-3.0, so not a headless core dependency.
- Generic Spleeter/Gentle karaoke demos: useful historical examples, but stale and less relevant than maintained audio-separator/alignment candidates.

## Decision

Proceed with Spike A first because it directly enforces the user's newest requirement: if Japanese subtitles already exist, preserve them and add Chinese below. Then run Spike B against the same small golden Live corpus. Spike C can land independently if pysubs2 and the reading analyzers meet the no-regression gates.

This sequence gains mature OCR, parsing, alignment, separation and subtitle-editing capabilities without surrendering the repo's strongest asset: a traceable, review-gated, headless Roy-specific workflow.
