---
name: roy-edit-concert-live
description: Turn a YouTube concert, 3D live, or singing-stream URL into review-ready per-song clips with rights evidence, complete musical endings, sourced lyrics and translations, kanji furigana, karaoke timing, QA, and YouTube metadata. Use when Roy asks Codex to 剪 Live、切歌、做歌回精華、翻譯演唱影片、製作卡拉 OK 字幕，or invokes $roy-edit-concert-live with a concert URL.
---

# Roy Edit Concert Live

Produce review-ready song clips through the `roy-ai-editor` project. Treat Codex as the director and the CLI as the deterministic executor.

## Start

1. Read `references/workflow.md` before processing a new URL.
2. Read `references/quality-standard.md` before cutting, aligning, rendering, or approving output.
3. Work from `/home/roy422/newLife/roy-ai-editor`.
4. Store large media outside Git under `/mnt/d/VideoProjects/roy-ai-editor/` unless Roy specifies another workspace.
5. Run `uv sync` and inspect `uv run roy-editor --help` before assuming a command exists.

> The V0 CLI is currently scaffolded only. Never claim that download, rights research, segmentation, alignment, rendering, or upload is implemented unless the current CLI and tests prove it. When a stage is missing, prepare its evidence and project artifacts, report the exact missing capability, and stop at the relevant review gate.

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
