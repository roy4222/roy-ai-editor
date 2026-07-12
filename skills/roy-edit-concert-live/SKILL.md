---
name: roy-edit-concert-live
description: Orchestrate a review-gated, manual-assisted concert workflow. The current deterministic tools create projects, rights-gated downloads, exact cuts, optional stable-ts timestamps, bilingual ASS with kanji furigana, burn-in, and probing; Codex manually researches rights/lyrics/translations and prepares metadata. Use when Roy asks Codex to 剪 Live、切歌、做歌回精華、翻譯演唱影片、製作卡拉 OK 字幕，or invokes $roy-edit-concert-live with a concert URL.
---

# Roy Edit Concert Live

Produce review-ready song clips through the `roy-ai-editor` project. Treat Codex as the director and the CLI as the deterministic executor.

## Start

1. Read `references/workflow.md` before processing a new URL.
2. Read `references/quality-standard.md` before cutting, aligning, rendering, or approving output.
3. Run `python scripts/bootstrap_repo.py` from this skill. If the Repo is missing, ask before running it again with `--install`; never clone silently.
4. Work from the resolved Repo. Respect `ROY_AI_EDITOR_REPO` when set.
5. Store large media outside Git. On Roy's Windows/WSL setup, default to `/mnt/d/VideoProjects/roy-ai-editor/`; otherwise ask for a workspace.
6. Run `uv sync` and inspect `uv run roy-editor --help` before assuming a command exists.

The CLI currently implements project creation, yt-dlp download, exact FFmpeg cuts, bilingual ASS generation with kanji-only furigana, subtitle burn-in, and FFprobe inspection. Fully automatic rights decisions, track discovery, lyrics acquisition, singing forced alignment, translation evaluation, multi-singer attribution, and YouTube upload are not implemented yet. Never claim a missing stage is automatic; prepare evidence/artifacts and stop at its review gate.

## CLI sequence

```bash
uv run roy-editor doctor
uv run roy-editor concert create "URL" --workspace /mnt/d/VideoProjects/roy-ai-editor/projects
uv run roy-editor concert approve-rights PROJECT --evidence-url "URL" --note "Roy approval note"
uv run roy-editor download PROJECT
uv run roy-editor cut SOURCE OUTPUT --start SECONDS --end SECONDS
uv sync --extra alignment
uv run roy-editor align VOCALS.wav aligned.json --language ja
uv run roy-editor karaoke render TIMING.json LYRICS.ass
uv run roy-editor karaoke burn CLIP.mp4 LYRICS.ass FINAL.mp4
uv run roy-editor probe FINAL.mp4
```

Use `examples/karaoke-timing.example.json` as the timing schema. Exact token timing is preferred. Automatically distributed timing is only a draft and must not be presented as precise singing alignment.

## Operating contract

- Turn model output into structured decisions and artifacts; do not let an LLM freely assemble destructive shell commands.
- Keep source URL, timestamps, lyrics, translations, credits, licenses, model versions, prompts, and approvals traceable.
- Prefer official lyrics and creator/company guidelines. A found translation is not automatically reusable.
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
- subtitle/alignment artifacts;
- rendered clips and QA report when implemented;
- YouTube title, description, credits, sources, and hashtags;
- unresolved decisions and the next review gate.

Do not expand into vlog, travel, robot competition, or tech-explainer workflows inside this skill. Those belong to future skills that reuse the same CLI modules.
