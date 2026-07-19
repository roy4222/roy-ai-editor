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
  --workspace /Volumes/RoyMedia/RoyAIEditor/projects
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

### 4. Approve a versioned lyrics packet

Prepare a JSON packet containing a stable track number/slug, trusted source URL,
translator/reuse status, rights warnings, and `L001`-style paired lyric lines. After
the rights gate, first persist a review candidate (the command adds `captured_at` when
the draft omits it):

```bash
uv run roy-editor concert prepare-lyrics PROJECT_DIR lyrics-packet.json
```

Unknown reuse status produces a blocked candidate. Approve only the prepared artifact
after reviewing its exact source, translation, line map, and warnings:

```bash
uv run roy-editor concert approve-lyrics PROJECT_DIR PROJECT_DIR/lyrics/sources/TRACK-HASH.json \
  --approved-by Roy --note "Approved this exact source, translation, and line map"
```

This writes a content-verified artifact under `lyrics/approved/`, records immutable
approval evidence, and updates the Project Manifest. A changed packet requires a new
approval; the command never silently overwrites an approved track artifact.

### 5. Prepare timing JSON

Copy [examples/karaoke-timing.example.json](examples/karaoke-timing.example.json). Each line accepts exact token timing and explicit ruby spans. If tokens or ruby are omitted, the renderer produces a usable draft by distributing time and generating kanji readings; human review is still required for singing.

Create a manifest-tracked stable-ts forced-alignment candidate from the approved track
and its audio:

```bash
uv sync --extra alignment
uv run roy-editor concert align-timing PROJECT_DIR TRACK_ID vocals.wav \
  --model large-v3 --language ja
```

The audio, model, language, raw alignment hash, and candidate are recorded as Evidence.
Stable-ts timestamps are not authoritative lyrics; review mora timing before approval.

Reconcile the forced-alignment JSON against the approved lyric artifact and explicitly
approve the result:

```bash
uv run roy-editor concert approve-timing PROJECT_DIR TRACK_ID aligned.json \
  --approved-by Roy --note "Reviewed token, whitespace, and line boundaries"
```

Zero-duration tokens and small cross-line overlaps are repaired within bounded rules.
Any text mismatch or unresolved timing fault stops the command instead of changing the
approved lyrics.

### 6. Render and burn karaoke

```bash
uv run roy-editor karaoke render timing.json lyrics.ass --font "Noto Sans CJK JP"
uv run roy-editor karaoke burn song.mp4 lyrics.ass final.mp4
uv run roy-editor probe final.mp4
```

For a manifest-managed track, create a review candidate and then approve the exact
video/subtitle pair only after inspecting the burned pixels and QA evidence:

```bash
uv run roy-editor concert render-track PROJECT_DIR TRACK_ID source.mp4
uv run roy-editor concert approve-deliverable PROJECT_DIR TRACK_ID \
  --approved-by Roy --note "Reviewed burned pixels, ruby, framing, and subtitles"
```

Rendering alone leaves the candidate in `videos/review/` and `subtitles/draft/`.
It also writes full-width burned-pixel crops plus automatic width, overlap, boundary,
and ruby safe-area checks under `qa/`. A failed automatic check cannot be approved.
Only the second command selects the hash-verified content under the approved directories
and updates `approved_deliverables` in the Project Manifest.

Build a local publish package from that Approved Deliverable:

```bash
uv run roy-editor concert package-deliverable PROJECT_DIR TRACK_ID \
  --metadata publish-metadata.json --thumbnail thumbnail.png
```

The metadata must include title, description, credits, and rights status/warnings.
The package contains verified copies and explicitly records `upload_performed: false`;
this command never contacts YouTube or another publishing service.

## Legacy project migration

Legacy folders remain the source of truth until a copy has been verified. Preview the
complete file map first; dry-run mode does not create the destination:

```bash
uv run roy-editor migrate legacy \
  /path/to/LEGACY_PROJECT \
  /Volumes/RoyMedia/RoyAIEditor/projects/PROJECT_ID
```

After reviewing the JSON plan, execute the copy-and-verify pass explicitly:

```bash
uv run roy-editor migrate legacy SOURCE_DIR DESTINATION_DIR --execute
```

The command never deletes or moves source files, rejects symlinks and destinations
inside the source tree, verifies every copied SHA-256, and records immutable migration
evidence. Imported media and subtitles remain archived and unapproved until their
project-specific tracks and review gates are reconciled.

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

Before publishing an integration branch, run the repository boundary gate:

```bash
python scripts/check_repo_integrity.py
```

It verifies both required Git ancestors, the pinned upstream MIT license, tracked-file
size limits, secret signatures, and the rule that private settings and Production
Assets stay outside Git.

## Public Customization

Safe, versioned customization lives in [profiles](profiles) and [workflows](workflows).
The example profile contains Roy's reusable editing preferences but no credentials,
private analytics, restricted lyrics, or Production Assets. Local-only values belong
under `profiles/private/`, a `*.local.*` overlay, `config.py`, or environment variables;
those paths are ignored by Git.

Inspect a standard Media Project through the versioned Concert Live Workflow:

```bash
uv run roy-editor workflow concert-live \
  /Volumes/RoyMedia/RoyAIEditor/projects/PROJECT_ID
```

The command reports the next explicit review gate from `project.json`. It never treats
a filename such as `final-v2.mp4` as an Approved Deliverable.

## Codex Skill

The source of truth is [skills/roy-edit-concert-live](skills/roy-edit-concert-live). On the Dedicated Editor Host, link that canonical source into Codex so repo updates are immediately available:

```bash
mkdir -p "$HOME/.codex/skills"
ln -s "$(pwd)/skills/roy-edit-concert-live" "$HOME/.codex/skills/roy-edit-concert-live"
```

For the legacy Windows Codex Desktop setup:

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

The current integration branch combines the root Upstream Foundation with Roy's
deterministic toolkit for project creation, rights-gated download, exact cuts, lyrics
packet review, optional stable-ts forced-alignment candidates, bounded timing
reconciliation, ASS generation, subtitle burn-in, pixel QA, explicit deliverable
approval, and local publish packages. Fully automatic song discovery, lyrics
acquisition/permission decisions, translation evaluation, multi-singer attribution,
and YouTube upload remain planned modules. The Skill must not claim those stages are
implemented until their CLI and tests exist.

## Third-party code

See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). The Upstream Foundation remains under its original MIT license and preserves Hao0321 Studio attribution in the root [LICENSE](LICENSE).

Roy AI Editor's original code is also released under the MIT License.
