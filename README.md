# roy-ai-editor

Roy 的 local-first AI 剪輯師。第一個 workflow 將 YouTube Concert／3D Live 轉成可審核的逐歌曲、多語卡拉 OK 影片。

## Included

- Repo-local Codex Skill：`$roy-edit-concert-live`
- YouTube 下載與 metadata：yt-dlp
- 精準分段與字幕燒錄：FFmpeg
- 雙語 ASS 卡拉 OK：逐 token `\\kf`、繁中翻譯、漢字上方振假名、等待點
- 專案 manifest 與 rights/edit/publish review gates
- FFprobe 輸出檢查
- 完整 vendored [Hao0321/video-autopilot-kit](https://github.com/Hao0321/video-autopilot-kit)（MIT），包含 CapCut helpers、delivery QA、longform/silent-vlog tools 與知識庫

歌詞、翻譯、商業字型與原始演唱會影片不包含在公開 Repo；使用者必須提供有權使用的內容。

## Install

Requirements：Python 3.11+、[uv](https://docs.astral.sh/uv/)、FFmpeg／FFprobe。

```bash
git clone https://github.com/roy4222/roy-ai-editor.git
cd roy-ai-editor
uv sync
uv run roy-editor doctor
uv run pytest
```

## Concert workflow

### 1. Create a review-gated project

```bash
uv run roy-editor concert create "YOUTUBE_URL" \
  --workspace /mnt/d/VideoProjects/roy-ai-editor/projects
```

### 2. Record explicit rights approval, then download

```bash
uv run roy-editor concert approve-rights PROJECT_DIR \
  --evidence-url "POLICY_OR_SOURCE_URL" \
  --note "Roy reviewed and approved this use"
uv run roy-editor download PROJECT_DIR
```

### 3. Cut a song with a complete ending

```bash
uv run roy-editor cut source.mp4 song.mp4 --start 2174.0 --end 2426.0
```

### 4. Prepare timing JSON

Copy [examples/karaoke-timing.example.json](examples/karaoke-timing.example.json). Each line accepts exact token timing and explicit ruby spans. If tokens or ruby are omitted, the renderer produces a usable draft by distributing time and generating kanji readings; human review is still required for singing.

Optional stable-ts transcription/alignment baseline:

```bash
uv sync --extra alignment
uv run roy-editor align vocals.wav aligned.json --model large-v3 --language ja
```

Stable-ts timestamps are evidence, not authoritative lyrics. Map them to a trusted lyric source and review mora timing before release.

### 5. Render and burn karaoke

```bash
uv run roy-editor karaoke render timing.json lyrics.ass --font "Noto Sans CJK JP"
uv run roy-editor karaoke burn song.mp4 lyrics.ass final.mp4
uv run roy-editor probe final.mp4
```

## Codex Skill

The source of truth is [skills/roy-edit-concert-live](skills/roy-edit-concert-live). To install it into Windows Codex Desktop:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "scripts/sync_skill_to_windows.ps1"
```

Then invoke:

```text
Use $roy-edit-concert-live to edit this concert URL: ...
```

The Skill keeps rights research, paid generation, uploads, public release, and deletion behind explicit review gates.

If only the Skill folder is installed, its `scripts/bootstrap_repo.py` locates an existing checkout. With user approval, `python scripts/bootstrap_repo.py --install` clones the public Repo to a portable user-data directory.

## Vendored video-autopilot-kit

The entire pinned MIT snapshot is under `vendor/video-autopilot-kit/`:

```bash
uv run roy-editor autopilot --path-only
cd vendor/video-autopilot-kit
python examples/01_vertical_short.py
python examples/02_caption_broll_match.py
```

Read its [README](vendor/video-autopilot-kit/README.md), [SETUP](vendor/video-autopilot-kit/SETUP.md), and [TROUBLESHOOTING](vendor/video-autopilot-kit/TROUBLESHOOTING.md). CapCut helpers remain Windows/version-sensitive; programmatic FFmpeg tools and QA gates are the portable default.

## Current boundary

Version 0.2 is a working deterministic toolkit for project creation, rights-gated download, exact cuts, optional stable-ts timestamps, ASS generation, subtitle burn-in, probing, and access to the complete vendored upstream toolkit. Fully automatic song discovery, lyrics acquisition/permission decisions, trusted-lyrics-to-singing alignment, translation evaluation, multi-singer attribution, and YouTube upload remain planned modules. The Skill must not claim those stages are implemented until their CLI and tests exist.

## Third-party code

See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). The upstream toolkit remains under its original MIT license in `vendor/video-autopilot-kit/LICENSE`.

Roy AI Editor's original code is released under the root [MIT License](LICENSE).
