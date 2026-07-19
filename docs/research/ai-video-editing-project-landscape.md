---
type: investigation
status: draft
date: 2026-07-18
tags:
  - topic/ai-video-editing
  - topic/architecture
  - workflow/short-form
---

# 開源 AI 自動剪輯專案：Roy AI Editor 架構借鏡

## 問題與範圍

Roy AI Editor 下一階段不只要剪 Concert Live，還要能接收多種類素材與自然語言意圖，完成素材理解、選段、時間線、字幕、渲染、品質檢查，最後以低人工介入方式交付或發布。本研究調查截至 2026-07-18 的一手資料，只使用專案自己的 GitHub repository、source、release、license 與官方文件。

這不是星數排行榜，也不把「文字生成一支影片」等同於剪輯。本研究選出的 10 個 repository，至少在下列其中一層提供可驗證的設計借鏡：

1. long-form 轉 Shorts／Reels；
2. transcript、scene、speaker、face、motion 等素材理解與選段；
3. timeline／edit-decision 的結構化表示；
4. 轉錄、字幕切分、翻譯、對軸；
5. headless／程式化渲染；
6. QA、重跑、發布與失敗復原。

## 結論先行

**不要 fork 任一個 end-to-end AI Shorts 專案來取代 Roy AI Editor。** 現有專案多半把模型、選段、renderer、UI、API provider 與發布綁成一條產品特定 pipeline；這能快速做 demo，卻不適合作為 Roy 長期的 domain model。Roy 應採用穩定的底層元件，借用上層專案的可測 pattern，並自行擁有 `Asset Analysis → Candidate → Edit Plan → Timeline → Render → QA → Publish` 的 artifact contract。

最值得立刻採用的是：

- **OpenTimelineIO** 作為 editorial timeline／interchange 層，但由 Roy 的 Project Manifest 保存 rights、provenance、approval、QA 與發布狀態；OTIO 官方也明確說它只保存 cut information 與 media reference，不是 media container 或 renderer。[OpenTimelineIO overview](https://github.com/AcademySoftwareFoundation/OpenTimelineIO#overview)
- **PySceneDetect** 作為 deterministic scene-boundary analyzer。它的 0.7 release 改善 VFR 與 PTS timebase，並能輸出 OTIO、EDL、FCP7／FCPXML，適合把 scene evidence 送進同一時間座標系。[PySceneDetect v0.7 release](https://github.com/Breakthrough/PySceneDetect/releases/tag/v0.7-release)
- **既有 FFmpeg／libass 路徑**繼續當預設 renderer 與 conformance engine。自然語言或 LLM 只產生受 schema 限制的 edit decision；不可直接產生任意 shell 或 FFmpeg filter。
- **auto-editor** 作為可替換的 deterministic rough-cut／editor-export baseline，不作 canonical timeline。它持續維護 audio、motion、subtitle、word 等 edit method，能輸出多種 NLE 格式；近期 v3 JSON timeline 也已支援多層影片與 overlays。[auto-editor README](https://github.com/WyattBlue/auto-editor#methods-for-making-automatic-cuts)、[31.3.0 release](https://github.com/WyattBlue/auto-editor/releases/tag/31.3.0)

最值得借 pattern、但不應整套採用的是：

- **OpenShorts**：重疊 transcript windows、word-boundary snapping、LLM 只決定 WHAT／WHEN、deterministic normalizer clamp effects。
- **claude-shorts**：內容型態分類、五維選段評分、自然語言 skill orchestrator、caption style props。
- **VideoLingo**：可續跑的分段 pipeline、術語表、Translate → Reflect → Adapt 與嚴格結構化回應。
- **ClipsAI／FunClip**：transcript segmentation、speaker-aware clipping 與 vertical reframe 的局部演算法。

程式化 motion graphics 要做小型 A/B：**Remotion** 成熟、模板生態完整，但使用特殊雙層 license；**Revideo** 是 MIT、明確以 headless TypeScript scene 為核心，但較年輕且沒有 GitHub releases。兩者都只應是 renderer adapter，不應成為 Roy 的 timeline source of truth。[Remotion license](https://github.com/remotion-dev/remotion/blob/main/LICENSE.md)、[Revideo README](https://github.com/midrender/revideo#revideo)

## 十個最值得比較的 repository

| Repository | 截至 2026-07-18 狀態 | License | 技術棧／覆蓋層 | 對 Roy 的價值 | 主要風險與判定 |
|---|---|---|---|---|---|
| [mutonby/openshorts](https://github.com/mutonby/openshorts) | 活躍、但仍無正式 GitHub release | Core MIT；`cloud/` 為限制 hosted resale 的 Commercial License | Python 3.11、FastAPI、React、Gemini、faster-whisper、PySceneDetect、YOLOv8／MediaPipe、FFmpeg、Remotion、第三方 publishing API | 最完整的 long-form → vertical clip → captions → publish 參考實作 | Fork 起家、模型／provider／UI 耦合高；CI 不跑重型 E2E；整套不採用，只移植 pattern。[LICENSE](https://github.com/mutonby/openshorts/blob/main/LICENSE)、[CI](https://github.com/mutonby/openshorts/blob/main/.github/workflows/ci.yml) |
| [AgriciDaniel/claude-shorts](https://github.com/AgriciDaniel/claude-shorts) | 活躍；v1.0.0 於 2026-02-16 發布 | MIT；但依賴 Remotion 特殊 license | Claude Code skill、Python、faster-whisper、MediaPipe／OpenCV、Remotion、FFmpeg | 最接近「agent skill 驅動剪輯」；評分 rubric、boundary snap、type-specific reframe 很有借鏡價值 | 仍是互動式 10-step pipeline，README demo 未完成；沒有 production QA／publish state machine。借 skill 結構，不 fork。[README](https://github.com/AgriciDaniel/claude-shorts#how-it-works) |
| [ClipsAI/clipsai](https://github.com/ClipsAI/clipsai) | 未封存但 dormant；GitHub `pushed_at` 為 2024-01-17 | MIT | Python、WhisperX、sentence embeddings／TextTiling、Pyannote、MTCNN、MediaPipe、KMeans、FFmpeg | 清楚拆分 `Transcriber`、`ClipFinder`、`Resizer`；適合作為 podcast candidate segmentation／speaker crop 研究基準 | 不是 viral ranker；依賴與模型整合老化。不要納入 production dependency，只重製演算法 fixture。[repo metadata](https://api.github.com/repos/ClipsAI/clipsai)、[ClipFinder source](https://github.com/ClipsAI/clipsai/blob/main/clipsai/clip/clipfinder.py) |
| [modelscope/FunClip](https://github.com/modelscope/FunClip) | 活躍；README 記錄 2026-05 新增 Fun-ASR-Nano／SenseVoice | MIT | Python、FunASR／Paraformer、SenseVoice、speaker diarization、LLM providers、Gradio、MoviePy、FFmpeg | 以 text、speaker 或 LLM time range 選段，並輸出全文與片段 SRT；中文語音基準很有用 | UI/state 與剪輯耦合；MoviePy／ImageMagick／內附字型不是 Roy 想要的 deterministic renderer。只評估 ASR／speaker result，不採 UI。[README](https://github.com/modelscope/FunClip#highlights)、[video clipper](https://github.com/modelscope/FunClip/blob/main/funclip/videoclipper.py) |
| [WyattBlue/auto-editor](https://github.com/WyattBlue/auto-editor) | 高度活躍；31.3.0 於 2026-07-16 發布 | Unlicense／public domain；release binaries 可能包含其他 OSS licenses | Nim、FFmpeg stack、audio／motion／black／subtitle／word analyzers、actions、v3 JSON timeline、NLE exports | 可作 deterministic first-pass baseline、silence/motion labels、字幕 retime 與 NLE export adapter | 沒有 narrative／visual semantics；內部 timeline 隨功能快速演進。以 subprocess adapter 隔離，不把 v3 當 domain model。[README](https://github.com/WyattBlue/auto-editor)、[releases](https://github.com/WyattBlue/auto-editor/releases) |
| [AcademySoftwareFoundation/OpenTimelineIO](https://github.com/AcademySoftwareFoundation/OpenTimelineIO) | 成熟且持續維護；官方稱 API stable | Apache-2.0 | C++ core、Python bindings、JSON `.otio`、Timeline／Track／Clip／MediaReference、adapter plugins | 最適合做可檢視、可 diff、renderer-neutral 的 editorial IR 與 NLE interchange | 不攜帶媒體、不渲染；不是所有特效／字幕／metadata 都可被每個 adapter 無損表達。Roy 必須包一層 domain contract 與 round-trip tests。[development status](https://github.com/AcademySoftwareFoundation/OpenTimelineIO#development-status)、[file format](https://github.com/AcademySoftwareFoundation/OpenTimelineIO/blob/main/docs/tutorials/otio-file-format-specification.md) |
| [Breakthrough/PySceneDetect](https://github.com/Breakthrough/PySceneDetect) | 活躍；0.7 為 breaking release | BSD-3-Clause | Python、OpenCV／PyAV／MoviePy backends、content／adaptive detectors、OTIO／EDL／FCP outputs | scene cuts 是 transcript 之外的第二種穩定 evidence；可協助 B-roll、鏡位變化、highlight boundary 與 contact sheet | Scene change 不等於故事段落或精彩時刻；threshold 需依素材類型校準。採用 analyzer，不採其 split-video 當唯一 renderer。[v0.7 release](https://github.com/Breakthrough/PySceneDetect/releases/tag/v0.7-release) |
| [Huanshere/VideoLingo](https://github.com/Huanshere/VideoLingo) | 活躍；v3.0.1 於 2026-02-28 發布 | Apache-2.0 | Python、WhisperX、Demucs、LLM、TTS、Streamlit、yt-dlp、FFmpeg | 轉錄、單行字幕切分、術語、三階段翻譯、resume/logging 的工程流程值得移植 | 官方列出背景音樂影響對軸、多語影片只保留主語言、多人配音仍不可靠；不適合直接取代 Concert lyrics evidence／approval。[README limitations](https://github.com/Huanshere/VideoLingo#current-limitations)、[releases](https://github.com/Huanshere/VideoLingo/releases) |
| [remotion-dev/remotion](https://github.com/remotion-dev/remotion) | 成熟且高頻發布；v4.0.477 於 2026-06-13 發布 | 特殊雙層 license：個人、非營利與最多 3 人營利組織可免費；其他營利組織需 Company License | TypeScript／React、Chromium、FFmpeg、JSON props、caption／transition／font packages、CLI／Node render | branded title、animated captions、hook、progress bar、頻道模板的成熟 renderer | License 需持續核對；React scene 不是 editorial interchange；瀏覽器與字型要做 golden-frame QA。只做 optional adapter。[render CLI](https://www.remotion.dev/docs/cli/render)、[license](https://github.com/remotion-dev/remotion/blob/main/LICENSE.md) |
| [midrender/revideo](https://github.com/midrender/revideo) | 活躍；由 `redotvideo` 搬到 `midrender`，有 tags 但無 GitHub releases | MIT | TypeScript generator scenes、headless `renderVideo()`、React Player、parallel workers、Video／Audio components | permissive、code-first，官方直接把 Claude／Codex 產生 TypeScript scene 列為 use case；適合和 Remotion 做模板 renderer A/B | 較年輕、repo／品牌剛遷移、預設匿名 telemetry；不可讓 agent 直接執行未驗證任意 TS。只在 sandbox 中以受限 template props 測試。[README](https://github.com/midrender/revideo#revideo)、[telemetry](https://github.com/midrender/revideo#telemetry) |

## 最有價值的架構 pattern

### 1. LLM 只提案，deterministic compiler 決定可執行內容

OpenShorts 曾讓 Gemini 直接寫 FFmpeg filter，現在改成讓模型只輸出 effect type、start、end、strength；`normalize_edits()` 再 whitelist effect、clamp 時間與強度、限制數量、消除重疊 zoom，最後由 deterministic builder 生成 filter。[OpenShorts `edit_builder.py`](https://github.com/mutonby/openshorts/blob/main/edit_builder.py)

這應成為 Roy 的核心規則：

```text
Natural-language brief
  → structured EditPlan proposal
  → schema + domain validation
  → policy / rights / approval validation
  → deterministic timeline compiler
  → renderer adapter
```

模型不得直接產 shell command、任意 FFmpeg filtergraph、未核准網路 URL、任意 TypeScript／Python code，或自行把 `reuse_status=unknown` 變成可發布。

### 2. Candidate generation 與 ranking 分開

不同專案證明了 candidate generation 可以是可重播的：PySceneDetect 產 scene boundaries；auto-editor 產 audio／motion／subtitle labels；ClipsAI 用 sentence embeddings 與 TextTiling 產 topic segments；FunClip 用 ASR、speaker 與指定文字回推 timestamp。[ClipsAI `clipfinder.py`](https://github.com/ClipsAI/clipsai/blob/main/clipsai/clip/clipfinder.py)、[FunClip README](https://github.com/modelscope/FunClip#use-funclip)

只有在這之後，才由模型做 narrative ranking。`claude-shorts` 的五維 rubric——hook strength、standalone coherence、emotional intensity、value density、payoff quality——比單一「viral score」更可審計，但 Roy 應保存各維分數、引用的 transcript／scene evidence、prompt／model version，而不是只存總分。[claude-shorts scoring rubric](https://github.com/AgriciDaniel/claude-shorts#how-segment-scoring-works)

OpenShorts 還提供兩個可直接重製的 deterministic pattern：把長 transcript 切成對齊 ASR segment 的重疊 windows，避免精彩段落落在 chunk 邊界；模型提議的 timecode 再 snap 到 word boundaries 與鄰近 silence，並修復 duration bounds。[OpenShorts `clip_selection.py`](https://github.com/mutonby/openshorts/blob/main/clip_selection.py)

### 3. Timeline 是產品資產，不是 renderer 的暫存參數

OpenTimelineIO 的 tree model、per-object schema version 與 namespaced metadata 適合 source control、diff、migration 與 NLE interchange；它也明確建議用 library 讀寫 `.otio`，而非自行仿做 parser。[OTIO file-format specification](https://github.com/AcademySoftwareFoundation/OpenTimelineIO/blob/main/docs/tutorials/otio-file-format-specification.md)

但是 Roy 不能只存 OTIO。建議關係為：

```text
Roy Project Manifest
  ├── source assets + hashes + rights/provenance
  ├── Asset Analysis artifacts
  ├── Candidate Moments + evidence
  ├── approved EditPlan
  ├── editorial.otio
  ├── renderer-specific props / generated commands
  ├── Render Manifest
  ├── QA Manifest
  └── Publish Job / remote video id
```

`editorial.otio` 表達 clips、ranges、tracks、markers、transitions 與 media references；歌詞版本、translator、reuse terms、人工／機器 gate、model provenance、QA 結果與發布憑證 reference 留在 Roy domain。OTIO metadata 可放 stable IDs 與摘要，但不能成為唯一資料庫。

### 4. 字幕 pipeline 要分成 transcript、semantic lines 與 render cues

VideoLingo 把 word-level ASR、NLP／LLM subtitle segmentation、terminology、translation refinement 與 dubbing 分階段；它也提供 progress resumption，而不是每次失敗重跑全部。[VideoLingo overview](https://github.com/Huanshere/VideoLingo#overview)

Roy 應明確分三層：

- `TranscriptWord`：ASR word、source time、confidence、speaker／language；
- `SemanticLine`：經核准的文字、翻譯、譯者、斷行、與 source words 的 alignment；
- `RenderCue`：特定版型所需的頁面、字級、位置、karaoke highlight 與 frame range。

Concert Live 的核准歌詞不可被 Whisper 或翻譯模型靜默覆寫。ASR 只提供 timing evidence；若背景音樂、多語或多人造成低 confidence，應升級為 exception，而不是把錯誤文字送進 renderer。VideoLingo 官方限制也支持這個邊界。[VideoLingo current limitations](https://github.com/Huanshere/VideoLingo#current-limitations)

### 5. Renderer 可插拔，template props 必須受 schema 約束

Remotion CLI 能以 JSON file 傳入 props，並控制 fps、duration、codec、color space、hardware acceleration、concurrency 與 frame subset；這使它適合 parameterized channel template，而不是讓 agent 每次寫新 React component。[Remotion render CLI](https://www.remotion.dev/docs/cli/render)

Revideo的 generator scene、headless API、browser Player 與 parallel rendering，提供較 permissive 的替代實驗；官方雖提到 Claude／Codex 能從 prompt 產 scene，Production 仍應限制為「選 template + validated props」，不能執行模型生成的任意 TypeScript。[Revideo capabilities](https://github.com/midrender/revideo#capabilities)

兩者的輸出最後都必須回到 Roy 的 FFprobe／decode／audio／subtitle／pixel QA。renderer 成功 exit 不代表影片可交付。

### 6. 發布是一個可恢復 job，不是 renderer 的最後一行

OpenShorts 把社群發布接到 Upload-Post，展示了 render 與 distribution 可串接；但它同時引入第三方帳號、API key、外部服務與 public gallery 邊界，不適合原樣採用。[OpenShorts technical pipeline](https://github.com/mutonby/openshorts#technical-pipeline)、[environment and publishing setup](https://github.com/mutonby/openshorts#environment-variables)

Roy 只需要 YouTube 時，應優先直連官方 YouTube Data API `videos.insert`，以最小 `youtube.upload` OAuth scope、resumable upload、private／unlisted 預設、idempotency record 與 processing-status polling 實作。官方 API 支援設定 `public`、`private`、`unlisted`，也明示未通過 audit 的新 API project 上傳會被限制為 private。[YouTube `videos.insert`](https://developers.google.com/youtube/v3/docs/videos/insert)、[processing status guide](https://developers.google.com/youtube/v3/guides/implementation/videos)

## Roy 的 build-vs-adopt 判定

### Adopt：直接依賴，但包在 adapter 後面

1. **OpenTimelineIO**：serialize editorial cut；固定版本；建立 schema migration 與 round-trip fixture。
2. **PySceneDetect**：產 scene evidence，不直接決定最終 highlight。
3. **FFmpeg／FFprobe／libass**：現有 deterministic render、probe 與 subtitle conformance 核心。
4. **auto-editor CLI**：optional analyzer／rough-cut baseline；所有輸出先轉為 Roy `CandidateMoment`／OTIO，不能讓它直接覆蓋核准 timeline。

### Borrow：重製 pattern，不帶入整個產品

1. OpenShorts 的 overlapping windows、word snap、effect whitelist／clamp 與 stdlib-only pure helpers。
2. claude-shorts 的 content-type strategy、五維 score 與 caption template props。
3. VideoLingo 的 checkpoint／resume、術語 artifact、分階段翻譯與 response validation。
4. ClipsAI 的 transcript topic segmentation 與 speaker-aware crop test cases。
5. FunClip 的 text／speaker → timestamp selection 與 full／clip SRT separation。

### Experiment：用 golden fixtures 決定

1. **Remotion vs Revideo**：只做同一個 branded subtitle／hook template，比較 render time、記憶體、首幀與抽樣幀一致性、字型、音訊同步、可移除性與 license。
2. **subject reframe**：比較 project-owned MediaPipe tracking 與 ClipsAI-style speaker crop；需要談話、雙人 podcast、screen recording、舞台 live 四類 fixture。
3. **LLM segment ranker**：用 provider-neutral structured output，和純 deterministic baseline 做 blinded comparison；不能用 README 宣稱的 viral quality 當驗收。

### Do not adopt wholesale

- OpenShorts：它是極佳的 architecture specimen，不是 Roy 的基底。core／cloud 混合 license、第三方 publishing、公開 gallery、Gemini／fal.ai／ElevenLabs 等 provider coupling，以及只測輕量模組的 CI 都提高長期成本。[OpenShorts README](https://github.com/mutonby/openshorts)、[CI workflow](https://github.com/mutonby/openshorts/blob/main/.github/workflows/ci.yml)
- claude-shorts：保留互動式 approval 與單一 short-form use case；沒有 render QA／rights／publish artifact chain。
- ClipsAI：最後 push 停在 2024，不能承擔 production dependency。
- FunClip／VideoLingo：可以當功能參考或 isolated evaluator，不能把 Gradio／Streamlit app state 當 Roy 的 workflow state。

## 建議的 Roy artifact contracts

### Asset Analysis Artifact

```json
{
  "schema_version": 1,
  "asset_id": "asset_...",
  "source_sha256": "...",
  "media": {"duration": 0, "time_base": "1/30000", "streams": []},
  "transcript": {"language": "ja", "words": [], "warnings": []},
  "scenes": [{"start": 0, "end": 0, "detector": "adaptive", "score": 0}],
  "audio": {"speech_ranges": [], "silence_ranges": [], "loudness": {}},
  "subjects": [{"track_id": "subject_1", "boxes": [], "confidence": 0}],
  "candidates": [],
  "tool_versions": {},
  "created_at": "<ISO-8601>"
}
```

每個 analyzer 只新增自己的 namespaced result。結果要帶 source hash、tool／model version、參數與 warnings，讓後續 ranking 和 QA 可重播。

### Candidate Moment

```json
{
  "candidate_id": "candidate_...",
  "asset_id": "asset_...",
  "source_range": {"start": 0, "end": 0},
  "evidence": {
    "transcript_word_ids": [],
    "scene_ids": [],
    "speaker_ids": [],
    "audio_features": []
  },
  "scores": {
    "hook": 0,
    "standalone_coherence": 0,
    "emotion": 0,
    "value_density": 0,
    "payoff": 0
  },
  "rationale": "...",
  "model_provenance": {},
  "warnings": []
}
```

分數是建議，不是 approval。來源 range 仍要由 word、silence、scene boundary validator 修整。

### Edit Plan

`EditPlan` 應是自然語言與 OTIO 中間的 typed command model，只允許已實作的 operation，例如 `trim`、`sequence`、`overlay`、`caption_template`、`audio_gain`、`duck`、`transition`、`reframe_track`。每項 operation 都要有 source range、timeline range、constraint 與 rationale；unsupported intent 必須回報，而不是生成任意 code。

## 兩階段實驗

### 第一階段：先證明 renderer-neutral edit plan

建立至少 6 個短型 golden projects：Concert Live、單人口播／訪談、雙人 podcast、screen recording、手機 B-roll vlog、多鏡位或混合素材。素材可用合成／可公開測試 fixture，不把私人影片放進 Git。

交付內容：

1. `AssetAnalysis v1` 與 `EditPlan v1` JSON Schema；
2. PySceneDetect analyzer；既有 transcript／timing 轉換器；optional auto-editor analyzer；
3. `EditPlan → OTIO` compiler 與 `OTIO → existing FFmpeg renderer` adapter；
4. natural-language planner 只能輸出 schema-valid EditPlan；所有時間範圍、asset ID、operation、rights gate 都經 deterministic validator；
5. Render Manifest 記錄 source／plan／timeline hash、完整 tool versions、command argv、output hash；
6. 重跑測試：同一 plan 在相同 toolchain 產生同一 timeline 與相同 normalized render manifest。

第一階段通過標準：

- 6 種 fixture 全部能在無 GUI、無手動改 project file 下重建；
- invalid asset／range／operation／未通過 rights gate 一律 fail closed；
- OTIO round-trip 不遺失 clip range、track order、marker IDs；renderer-specific metadata 的 loss 被明示；
- 既有 Concert Live workflow 的核准歌詞、line map 與 QA 不因引入 OTIO 而改變語意；
- 任一 analyzer 或 optional renderer 可移除，而不會失去 Project Manifest 或核准 EditPlan。

### 第二階段：用一條 Shorts pipeline 驗證自動化閉環

在第一階段 artifact contract 上，做一條 16:9 talking-head／podcast → 9:16 Shorts pipeline：

1. deterministic candidates：transcript sentences + scene cuts + silence + duration bounds；
2. LLM structured ranker：採五維分數與 evidence IDs，禁止直接改 timeline；
3. boundary snap：word／sentence／silence 優先，scene boundary 只在不切斷語意時採用；
4. subject reframe：face／speaker tracking，低 confidence 時 fallback blurred background 或 center crop；
5. 同一個 approved EditPlan 分別餵 FFmpeg／libass base template，以及 Remotion 或 Revideo motion template；
6. QA：FFprobe、全片 decode、duration／A/V sync、loudness／peak、black／freeze、字幕 safe area、抽樣幀 contact sheet、golden-frame perceptual diff；
7. QA 通過才建立 Publish Job；先用官方 YouTube API private／unlisted upload，保存 resumable session state、remote video ID、processing status 與最終 URL；public 是另一個明確 gate。

第二階段通過標準：

- 至少 10 支不同內容的 fixture，candidate recall、選段 pairwise preference、boundary error、crop tracking error 與人工介入次數皆有量化；
- 候選為空、模型回應壞掉、subject lost、字幕溢出、upload retry 都有 deterministic fallback 或明確 exception；
- median research／analysis intervention 為 0；初期只在候選／文字或發布 gate 要求 Roy 核准；
- renderer 成功但 QA 失敗時絕不 publish；retry 不重複建立同一支 YouTube upload；
- 預設只上傳 private／unlisted，回傳 URL 與 QA／publish manifest；公開發布需另行授權。

## 不應過早做的事

- 不建立「一個超大型 prompt 讀完整支影片後直接吐 FFmpeg command」。
- 不把 viral score 當客觀真值；它只能用 Roy 的 pairwise review 與實際內容表現逐步校準。
- 不讓每種影片類型各自發明 timeline JSON；差異應落在 analyzer、candidate policy、template 與 renderer adapter。
- 不因為 Mac mini 專用就關閉 resource limits。模型下載、Chromium render、Whisper、OpenCV 和多支 FFmpeg 同時執行仍需 job queue、disk budget 與 temp cleanup。
- 不先做 TikTok／Instagram 多平台帳號整合。先把 YouTube private／unlisted 的官方 API、idempotency、QA gate 與 OAuth secret boundary做完整。

## Watchlist，不列入本次十個核心比較

[OpenCut](https://github.com/OpenCut-app/OpenCut) 的 rewrite 明確規劃 Editor API、plugin-first architecture、MCP server、headless mode 與 scripting tab，方向和 Roy 很接近；但官方同時說目前仍在重寫、today 應使用 classic，而且尚未準備接受外部 contribution。現階段適合追蹤其 project／timeline schema，不適合成為依賴。[OpenCut status](https://github.com/OpenCut-app/OpenCut#status)

其他以 script → stock／AI media → TTS 為主的 short generator 並未優先列入，因為它們主要解決內容生成，而不是 Roy 目前最需要的多來源素材理解、可核准 edit decision、renderer interchange 與 production QA。

## 最終建議

Roy AI Editor 的差異化不應是再做一個 OpenShorts UI，而是把現有 Concert Live 已開始建立的 rights、lyrics approval、timing、render、pixel QA 與 deliverable gate，提升為通用且可重播的編集 artifact chain：

```text
Source Assets
  → Asset Analysis
  → Evidence-backed Candidates
  → Natural-language EditPlan
  → deterministic validation
  → OTIO editorial timeline
  → FFmpeg / optional motion renderer
  → automated QA manifest
  → private/unlisted Publish Job
  → URL + evidence
```

這條路徑能直接借用開源社群已驗證的 analyzer、timeline、字幕與 renderer，同時把最需要 Roy 專屬化的部分——審美偏好、rights、核准、證據、失敗復原與發布政策——留在自己的 domain model。最先做的不是安裝十個專案，而是實作第一階段的三個 contract：`AssetAnalysis v1`、`EditPlan v1`、`Render/QA Manifest v1`。
