---
name: roy-edit-concert-live
description: Orchestrate a review-gated, manual-assisted concert workflow. The deterministic tools create projects, rights-gated downloads, exact cuts, traceable lyrics and timing candidates, bilingual ASS with kanji furigana, burned-pixel QA, explicit deliverables, and local publish packages. Use when Roy asks Codex to 剪 Live、切歌、做歌回精華、翻譯演唱影片、製作卡拉 OK 字幕，or invokes $roy-edit-concert-live with a concert URL.
---

# Roy Edit Concert Live

Produce review-ready song clips through the `roy-ai-editor` project. Treat Codex as the director and the CLI as the deterministic executor.

## Start

1. Read `references/workflow.md` before processing a new URL.
2. Read `references/quality-standard.md` before cutting, aligning, rendering, or approving output.
3. Read `references/lyrics-approval-gate.md` before searching, selecting, translating, splitting, or aligning lyrics.
4. Run `python scripts/bootstrap_repo.py` from this skill. If the Repo is missing, ask before running it again with `--install`; never clone silently.
5. Work from the resolved Repo. Respect `ROY_AI_EDITOR_REPO` when set.
6. Store large media outside Git. On Roy's Windows/WSL setup, default to `/mnt/d/VideoProjects/RoyAIEditor/`; otherwise ask for a workspace.
7. Run `uv sync` and inspect `uv run roy-editor --help` before assuming a command exists.

The CLI implements project creation, yt-dlp download, exact FFmpeg cuts, lyrics packet preparation/approval, optional stable-ts forced-alignment candidates, bounded timing reconciliation, bilingual ASS generation, subtitle burn-in, burned-pixel QA, explicit Approved Deliverables, and local publish packages. Fully automatic rights decisions, track discovery, lyrics acquisition, translation evaluation, multi-singer attribution, and YouTube upload are not implemented. Never claim a missing stage is automatic; prepare evidence/artifacts and stop at its review gate.

## CLI sequence

```bash
uv run roy-editor doctor
uv run roy-editor concert create "URL" --workspace /mnt/d/VideoProjects/RoyAIEditor/projects
uv run roy-editor concert approve-rights PROJECT --evidence-url "URL" --note "Roy approval note"
uv run roy-editor download PROJECT
uv run roy-editor cut SOURCE OUTPUT --start SECONDS --end SECONDS
# STOP: present the versioned lyrics/translation/line-break approval packet.
# Continue only after Roy explicitly approves that exact packet.
uv run roy-editor concert prepare-lyrics PROJECT lyrics-packet.json
uv run roy-editor concert approve-lyrics PROJECT PROJECT/lyrics/sources/TRACK-HASH.json --note "Roy approval note"
uv sync --extra alignment
uv run roy-editor concert align-timing PROJECT TRACK_ID VOCALS.wav --model large-v3 --language ja
uv run roy-editor concert approve-timing PROJECT TRACK_ID PROJECT/timing/alignment/TRACK-HASH.json --note "Roy timing review"
uv run roy-editor concert render-track PROJECT TRACK_ID CLIP.mp4
# STOP: inspect every full-width crop referenced by the render QA evidence.
uv run roy-editor concert approve-deliverable PROJECT TRACK_ID --note "Roy pixel review"
uv run roy-editor concert package-deliverable PROJECT TRACK_ID --metadata metadata.json --thumbnail thumbnail.png
```

Use `examples/karaoke-timing.example.json` as the timing schema. Exact token timing is preferred. Automatically distributed timing is only a draft and must not be presented as precise singing alignment.

Treat Roy's explicit approval of the exact lyrics packet as a hard gate. Before approval, do not align lyrics, create or modify song timing JSON, render ASS, burn a review/final video, or prepare upload metadata that claims a translation source. If any lyric source, translation, repeat, or display line break changes later, invalidate the approval and present a new packet.

Do not approve ruby from ASS coordinates or a scaled full-frame screenshot. `render-track` records full-width subtitle-band crops from the actually burned MP4 and blocks automatic layout failures. Inspect every numbered crop. Any clipped line, wrong reading, kana included in a ruby base span, or visibly off-center ruby fails the manual render gate.

## Operating contract

- Turn model output into structured decisions and artifacts; do not let an LLM freely assemble destructive shell commands.
- Keep source URL, timestamps, lyrics, translations, credits, licenses, model versions, prompts, and approvals traceable.
- Prefer official lyrics and creator/company guidelines. A found translation is not automatically reusable.
- Always perform the Bahamut-first Traditional Chinese search and show Roy the candidate URLs, translator, concrete line map, reuse terms, and uncertainties. Never silently substitute an AI translation.
- Default to one approved source lyric line per on-screen subtitle event. Never merge three source lines into one event. Merge two only when the source phrasing requires it and Roy approves that exact line map.
- Present evidence and risk; do not claim legal certainty.
- Preserve intros and full musical endings. Low volume is not permission to cut a song tail.
- Mark low-confidence singer identity, translation, timing, and rights findings for review instead of guessing.
- Keep paid generation, upload, public release, and deletion behind explicit approval gates.
- Upload private or unlisted first. Public release is a separate approval.
- Never delete source media merely because an upload request completed.

## Invocation result

For a new URL, return or persist:

- rights evidence and status;
- track list and timestamp sources;
- proposed start/end candidates with confidence;
- lyrics and translation provenance;
- the versioned lyrics/translation/line-break approval packet and Roy's approval status;
- the approved source-line-to-display-line map, including repeats and any allowed two-line joins;
- subtitle/alignment artifacts;
- rendered clips and hash-verified QA evidence;
- YouTube title, description, credits, sources, and hashtags;
- unresolved decisions and the next review gate.

Do not expand into vlog, travel, robot competition, or tech-explainer workflows inside this skill. Those belong to future skills that reuse the same CLI modules.
