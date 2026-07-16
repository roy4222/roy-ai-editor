# roy-ai-editor

Roy 的 local-first AI 剪輯師。專案以 [Hao0321/video-autopilot-kit](https://github.com/Hao0321/video-autopilot-kit) 作為 Upstream Foundation，再加入 Roy 可持續版控的能力、偏好與 Editing Workflows。第一個產品切片是把 YouTube Concert／3D Live 轉成可審核的逐歌曲、多語卡拉 OK 影片。

## Included

- Upstream Foundation 的 programmatic、CapCut-assisted、QA、templates、knowledge 與 examples
- Repo-local Codex Skill：`$roy-edit-concert-live`
- YouTube 下載與 metadata：yt-dlp
- 精準分段與字幕燒錄：FFmpeg
- 雙語 ASS 卡拉 OK：逐 token `\\kf`、繁中翻譯、漢字上方振假名、等待點
- Project Manifest 與 rights/edit/publish review gates
- FFprobe 輸出檢查

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
  --workspace /mnt/d/VideoProjects/RoyAIEditor/projects
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

## Upstream Foundation

The upstream framework now lives at the repository root. Start with:

- [SETUP.md](SETUP.md) for the customization questionnaire
- [templates](templates) for safe blank customization profiles
- [knowledge](knowledge) for editing and publishing guidance
- [examples](examples) for runnable synthetic pipelines
- `src/capcut_helpers`, `src/longform_maker`, and `src/silent_vlog_maker` for reusable editing capabilities

Run the upstream synthetic examples directly from the repo root:

```bash
python examples/01_vertical_short.py
python examples/02_caption_broll_match.py
```

To review future upstream updates safely:

```bash
git fetch upstream
git log --oneline HEAD..upstream/main
```

Integrate reviewed updates on a dedicated branch; do not blindly pull them into a customized main branch.

## Public Customization

Safe, versioned customization lives in [profiles](profiles) and [workflows](workflows).
The example profile contains Roy's reusable editing preferences but no credentials,
private analytics, restricted lyrics, or Production Assets. Local-only values belong
under `profiles/private/`, a `*.local.*` overlay, `config.py`, or environment variables;
those paths are ignored by Git.

Inspect a standard Media Project through the versioned Concert Live Workflow:

```bash
uv run roy-editor workflow concert-live \
  /mnt/d/VideoProjects/RoyAIEditor/projects/PROJECT_ID
```

The command reports the next explicit review gate from `project.json`. It never treats
a filename such as `final-v2.mp4` as an Approved Deliverable.

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

## Current boundary

The current integration branch combines the root Upstream Foundation with Roy's deterministic toolkit for project creation, rights-gated download, exact cuts, optional stable-ts timestamps, ASS generation, subtitle burn-in, and probing. Fully automatic song discovery, lyrics acquisition/permission decisions, trusted-lyrics-to-singing alignment, translation evaluation, multi-singer attribution, and YouTube upload remain planned modules. The Skill must not claim those stages are implemented until their CLI and tests exist.

## Third-party code

See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). The Upstream Foundation remains under its original MIT license and preserves Hao0321 Studio attribution in the root [LICENSE](LICENSE).

Roy AI Editor's original code is also released under the MIT License.
