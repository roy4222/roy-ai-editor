---
type: investigation
status: draft
date: 2026-07-12
tags:
  - topic/ai-agent
  - topic/video-editing
  - topic/generative-ai
---

# Roy AI Editor：開源 AI 剪輯師 landscape

> 調查日期：2026-07-12。活躍度與 star 數是當日快照，會隨時間變動。來源優先採專案 GitHub、LICENSE、README 與官方 API 文件；使用者附上的 Seedance 2.5 文章只作為需求背景，不作 API 事實依據。

## 結論先行

GitHub 上已經有多個「AI 剪影片」專案，但**沒有一個專案完整覆蓋 Roy 的北極星**：素材庫接入、自然語言導演、長片理解、歌曲級精準切割、字幕與多語翻譯、振假名／卡拉 OK、生成式補鏡、品質評估、版權 gate、YouTube 發布。

最接近整體產品形狀的是 [browser-use/video-use](https://github.com/browser-use/video-use)；最值得直接抽入第一版能力的是 [VideoLingo](https://github.com/Huanshere/VideoLingo)、[WhisperX](https://github.com/m-bain/whisperX)、[auto-editor](https://github.com/WyattBlue/auto-editor) 與 Google 官方 API client。渲染層可先維持 FFmpeg／ASS，等 GUI 與模板需求成熟後，再評估 Remotion；不要一開始把整個系統綁在 Remotion 或 VideoDB 上。

建議的參考組合：

```text
video-use 的 agent/EDL/review-loop 設計
        +
VideoLingo 的字幕切分、翻譯與配音管線
        +
WhisperX 的逐字時間戳／forced alignment
        +
auto-editor + FFmpeg 的切割與 dead-space pass
        +
ASS/FFmpeg（第一版）或 Remotion（模板成熟後）的渲染
        +
Google Drive / YouTube 官方 API clients
        +
OpenRouter Image/Video API、ComfyUI 等生成素材 provider adapters
```

## 分級總表

| 分級 | Repo | License | 活躍度快照 | 擅長 | 主要缺口 | Roy 可借用點 |
|---|---|---|---|---|---|---|
| **可直接採用** | [browser-use/video-use](https://github.com/browser-use/video-use) | MIT | 約 16.6k stars、18 commits、尚無 release | 素材盤點、逐字稿、EDL、FFmpeg render、cut-boundary self-eval、agent skill | 目前依賴 ElevenLabs；偏 talking-head，不含歌曲翻譯、版權與發布 | 第一個 workflow 骨架、project memory、review gate、文字＋按需視覺而非全片塞給模型 |
| **可直接採用** | [Huanshere/VideoLingo](https://github.com/Huanshere/VideoLingo) | Apache-2.0 | 約 17.7k stars、975 commits、v3.0.1（2026-02-28） | yt-dlp、WhisperX、字幕切分、翻譯、對齊、配音 | 目標是影片 localization，不是素材選擇與敘事剪輯；未解決歌唱音素對軸 | `subtitle/translate/dub` capability 的主要參考與可拆模組 |
| **可直接採用** | [m-bain/whisperX](https://github.com/m-bain/whisperX) | BSD-2-Clause | 約 24k stars、557 commits | ASR、逐字時間戳、forced alignment、speaker diarization | 歌唱聲、拉長音、伴奏覆蓋下仍需專門評測；不是 renderer | 通用 speech alignment baseline、逐字字幕與切點候選 |
| **可直接採用** | [WyattBlue/auto-editor](https://github.com/WyattBlue/auto-editor) | Unlicense／Public Domain | 約 4.5k stars、2,392 commits、v31.2.0（2026-07-10） | 依音量等訊號自動去除 silence/dead space，輸出剪輯結果 | 不理解敘事、歌尾與表演意圖 | dead-space detector、第一輪粗剪、EDL/時間段測試 oracle |
| **可直接採用** | [googleapis/google-api-python-client](https://github.com/googleapis/google-api-python-client) | Apache-2.0 | 約 8.9k stars、v2.198.0（2026-06-25）；官方維護模式 | Google Drive 與 YouTube Discovery APIs 的官方 Python client | 通用 client 較重；OAuth、quota、resumable upload 仍要自己包裝 | `connectors/google_drive`、`publishers/youtube` 共用底座 |
| **抽模組** | [video-db/Director](https://github.com/video-db/Director) | MIT | 約 1.4k stars、499 commits | 自然語言 video agents、search、highlight、clip、generation、subtitle/translate、chat UI | 核心建立在 VideoDB 雲端 infrastructure，上游綁定與成本較高 | agent registry、content types、progress events、chat review UI 的領域設計 |
| **抽模組** | [remotion-dev/remotion](https://github.com/remotion-dev/remotion) | **特殊授權**，部分公司情境需付費 license | 約 52.9k stars、647 releases、v4.0.488（2026-07-11） | React 程式化影片、動態排版、可重用品牌模板 | 不是剪輯決策器；Node/React 第二 runtime；商用授權需先審查 | 字幕樣式、片頭片尾、數據動畫、比賽影片品牌模板 |
| **抽模組** | [Comfy-Org/ComfyUI](https://github.com/Comfy-Org/ComfyUI) | GPL-3.0（需依實際 LICENSE 再做發行審查） | 約 120k stars、5,577 commits | node graph、圖片/影片 diffusion workflow、本機 API/backend | 重 GPU、模型 license 各自不同；不是 NLE | 本機生成式素材 provider，保存可重現 workflow JSON，不讓核心綁死單一模型 |
| **抽模組** | [harry0703/MoneyPrinterTurbo](https://github.com/harry0703/MoneyPrinterTurbo) | MIT | 約 51k stars、648 commits | 主題→文案→素材→字幕→BGM→短片；Web/API | 偏素材拼接式短影音，無長片精剪、來源權利與人工 review gate | 「script→asset search→render」workflow、provider abstraction、批次短片 UI |
| **僅參考** | [video-db/Director](https://github.com/video-db/Director) 的完整 runtime | MIT，但依賴 VideoDB service | 同上 | 最像 ChatGPT for video 的產品展示 | 難以維持真正 local-first，媒體索引與運算依賴外部服務 | 借介面與 agent 分工，不照搬基礎設施 |
| **僅參考** | [jianfch/stable-ts](https://github.com/jianfch/stable-ts) | MIT | 約 2.3k stars；README 明示 indefinitely paused | Whisper 時間戳穩定化、silence suppression、refinement/regrouping | 已暫停開發 | 對齊後處理的演算法與 QA 概念；不作主依賴 |
| **僅參考** | [OpenCut-app/OpenCut](https://github.com/OpenCut-app/OpenCut) | 以 repo 當下 LICENSE 為準 | 快速發展中的 open-source CapCut alternative | 瀏覽器時間軸 UI、典型 NLE 操作 | AI pipeline 與 backend 尚不是 Roy 的主線，專案 maturity 需另驗證 | 未來人工微調 timeline GUI 的 UX 參考 |
| **上游基礎** | [Hao0321/video-autopilot-kit](https://github.com/Hao0321/video-autopilot-kit) | MIT；整合時保留原始授權聲明 | 可客製化的影片製作框架 | FFmpeg／Python 自動製片、字幕 QA、CapCut 草稿、模板、profiles 與製作知識 | 不是完整 orchestration runtime；Roy 仍需補上 URL→權利→剪輯→翻譯→發布的產品流程 | 作為 Roy AI Editor 的 Upstream Foundation；在其骨架上加入 Roy Customization 與多個 Workflow |

## 最值得優先閱讀的三個 repo

### 1. video-use：最像「Roy 的專屬剪輯師」

[README](https://github.com/browser-use/video-use#readme) 的流程是 `Transcribe → Pack → LLM Reasons → EDL → Render → Self-Eval`。它把逐字稿當作主要閱讀介面，只在模糊切點產生 filmstrip＋waveform＋word labels 的 timeline view，避免把數萬幀全塞給模型。剪輯前先提出策略、等待人類確認，渲染後對每個 cut boundary 自評，最多修正重渲染。

這與 Roy 已確認的原則高度一致：**自動做到可發布，最後由 Roy 核准**。最重要的不是照搬 ElevenLabs，而是採用這四個產品概念：

1. `ProjectManifest`：來源、逐字稿、使用者意圖、EDL、產物與決策都可重播。
2. `EditDecisionList`：LLM 只產生結構化剪輯決策，不直接拼 shell command。
3. `ReviewGate`：策略、版權、歌詞來源、成片、公開發布各有明確 gate。
4. `Evaluator`：cut boundary、音訊 pop、字幕遮擋、空白／黑幀自動檢查。

缺點是它目前更適合談話、產品影片與旅遊 montage；演唱內容需要另外的 music-aware alignment、尾奏偵測和歌詞先驗。

### 2. VideoLingo：翻譯與 localization 能力庫

[VideoLingo README](https://github.com/Huanshere/VideoLingo#readme) 明確列出 yt-dlp、WhisperX 逐字辨識、NLP/AI 字幕切分、翻譯、對齊與配音，並採 Apache-2.0。這很適合拿來定義 `LocalizationJob`：來源語言、目標語言、歌詞／逐字稿來源、譯文候選、分行、時間軸、配音與 burn-in。

但 Roy 的「有品味翻譯」不能只靠一鍵翻譯。應把 VideoLingo 當 baseline，另建立：

- `TranslationCandidate`：自翻、官方、授權譯者版本並存。
- `ReferenceProvenance`：URL、作者、可否轉載、署名要求。
- `TranslationEval`：忠實、自然、可唱、上下文一致、文化語感五軸評分。
- `PreferenceDataset`：保存 Roy 選 A/B、逐句修訂與理由；未來先做 reranking／prompt regression，資料夠多才考慮微調模型。

### 3. Director：agent 架構與 UI，不宜整套依賴

[Director README](https://github.com/video-db/Director#readme) 已展示自然語言指令驅動 highlight、search、clip、generation、字幕翻譯與配音，並提供 20+ agents、chat UI、content types 與 progress updates。它證明「AI 剪輯師同時調用生成式影音」是可行的產品形狀。

但 Director 建立在 VideoDB 的 video-as-data 雲端服務上。Roy 的目標包含本機素材、Google Drive 與可替換 provider，因此應借用 agent registry 和進度事件設計，不把核心 asset model 綁在 VideoDB。

## 長影片、highlight 與歌回的差異

常見開源工具解的是三種不同問題：

1. **Silence removal**：auto-editor 很強，但「音量低」不等於「該剪掉」；歌曲尾奏恰好是最危險的反例。
2. **Transcript highlights**：video-use／Director 可由逐字稿推理，但音樂段落沒有足夠 speech semantics。
3. **Music segmentation**：Roy 需要時間軸留言／章節、歌名資料、歌詞先驗、音訊 onset/offset、掌聲與 MC 分類共同決定。

因此 concert workflow 應採多訊號，而不是單一模型：

```text
章節／留言時間軸
  + 曲名與官方 metadata
  + 人聲／音樂／掌聲／MC 音訊分類
  + 歌詞 forced alignment
  + 尾奏衰減與下一段語音 onset
  → start/end candidates + confidence + evidence
```

低 confidence 才請 Roy 看 10–20 秒 preview。這會比「全片交給最貴模型看」更便宜，也更能換成較小模型。

## 字幕、翻譯與卡拉 OK 對軸

### 推薦分層

- **ASR baseline**：[WhisperX](https://github.com/m-bain/whisperX)；BSD-2-Clause、逐字 timestamps、forced alignment、diarization。
- **對齊後處理參考**：[stable-ts](https://github.com/jianfch/stable-ts)；有 silence suppression、refinement、word regrouping，但 README 已標記暫停開發，不能當主依賴。
- **翻譯／分行 baseline**：[VideoLingo](https://github.com/Huanshere/VideoLingo)。
- **卡拉 OK renderer**：第一版保留 ASS karaoke tags＋FFmpeg；振假名採可測量字形 layout，而不是以等寬字猜 X 位置。

對歌唱字幕，ASR 只用來估計音素時間，不應取代官方歌詞。較穩健的次序是：取得可信歌詞→正規化漢字／假名／重複段→分離人聲（可選）→forced align→按音節修正→視覺 QA。要把「字跑完但歌手停頓」「長音」「吸氣」「尾奏無字幕」加入 regression fixtures。

## 程式化 timeline 與渲染選擇

### 第一版：FFmpeg＋ASS

優點是目前已有成片、速度快、輸出可控、Python workflow 單一 runtime。先建立自己的 `Timeline`／`Track`／`Clip`／`CaptionCue`／`RenderPlan`，由 adapter 轉成 FFmpeg command；不要讓 domain model 等同 command string。

### 模板成熟後：Remotion

[Remotion](https://github.com/remotion-dev/remotion) 很適合 React 元件化的片頭、字幕、數據 overlay、機器人比賽 score card 與旅遊地圖動畫。它高度活躍，但官方 README 明示特殊 license，部分公司情境需要 company license。因此它適合作為可選 renderer adapter，而非 Repo 的不可替換核心。

### 人工微調 GUI

[OpenCut](https://github.com/OpenCut-app/OpenCut) 可作 CapCut-like timeline UX 參考。若未來自己做 Web GUI，先支援 review、trim handle、caption correction、approve/reject；不要第一階段重造完整 NLE。

## 生成式圖片與影片

### OpenRouter Seedance 2.0 已有正式 API

OpenRouter 官方模型頁確認模型 slug 是 [`bytedance/seedance-2.0`](https://openrouter.ai/bytedance/seedance-2.0/api)，支援：

- text-to-video；
- image-to-video；
- first/last frame control；
- multimodal reference-to-video；
- 公示價格從 **US$0.06726/秒**起（2026-07-12 快照，需在送出任務前重新查價）。

官方 [video generation cookbook](https://openrouter.ai/docs/cookbook/video-generation/choose-video-model) 顯示流程為：先查 `GET /api/v1/videos/models`，再向 `POST /api/v1/videos` 送出非同步工作，取得 `id` 與 `polling_url` 後輪詢並下載影片。文件明確警告送出工作會花費 credits，應先用 model metadata 驗證 duration、resolution、aspect ratio、audio、first-frame 等能力。

因此不能把 Seedance 參數寫死。正確介面應是：

```python
class VideoGenerator(Protocol):
    def capabilities(self) -> VideoGenerationCapabilities: ...
    def estimate_cost(self, request) -> Money: ...
    def preview_request(self, request) -> ProviderRequest: ...
    def submit(self, approved_request) -> GenerationJob: ...
    def poll(self, job) -> GenerationResult: ...
```

### 能做什麼、不該做什麼

Seedance／Sora／Veo 類 API 適合補 B-roll、片頭、轉場、概念示意、缺失鏡頭與宣傳短片；它們**不是既有素材的精準時間軸剪輯器**。生成鏡頭必須保留 prompt、reference、provider、model version、cost、rights/terms snapshot 與人工核准。

GPT 圖片生成同樣應走 `ImageGenerator` provider adapter，產物先進 Asset Library，再由 timeline 引用。若希望本機與可重現 graph，可抽接 [ComfyUI](https://github.com/Comfy-Org/ComfyUI) API；但核心不得假設使用者一定有 GPU，模型權重授權也要逐一記錄。

## Google Drive 素材與 YouTube 發布

- Drive、YouTube 都可用 Google 官方 [google-api-python-client](https://github.com/googleapis/google-api-python-client)；其 README 說明它是官方 discovery-based API client、Apache-2.0、目前 maintenance mode，仍處理 critical bugs/security。對 Roy 這個 Python/uv 專案足夠。
- [PyDrive2](https://github.com/iterative/PyDrive2) 讓常見 Drive API V2 操作更簡單，但它是較高層第三方 wrapper；新產品優先直接包官方 client，避免把 asset model 綁在 V2 wrapper。
- Google 官方 [youtube/api-samples](https://github.com/youtube/api-samples) 包含 Data API、Analytics API 與 Live Streaming API 多語言範例，可參考 resumable upload/OAuth 流程；正式程式仍應依 YouTube Data API 當下文件與 quota 規則。

發布需要獨立 gate：`rendered → rights-approved → metadata-approved → uploaded-private → platform-checks-reviewed → publish-approved`。預設只自動上傳為 private/unlisted；公開發布永遠是另外的明確批准。

## 建議的 Repo 邊界

```text
roy-ai-editor/
├─ core/
│  ├─ projects/          # ProjectManifest、intent、artifacts、audit log
│  ├─ assets/            # local/Drive/URL 統一 AssetRef 與 provenance
│  ├─ timeline/          # EDL、tracks、clips、captions、generated assets
│  ├─ jobs/              # resumable state machine、cache、retry
│  └─ review/            # gates、evidence、approve/reject
├─ capabilities/
│  ├─ ingest/            # yt-dlp、Drive
│  ├─ understand/        # transcript、scene/music/activity analysis
│  ├─ edit/              # cut candidates、highlight、EDL
│  ├─ localize/          # lyrics、translation、ruby、karaoke alignment
│  ├─ generate/          # image/video/voice provider protocols
│  ├─ render/            # FFmpeg/ASS first；Remotion optional
│  ├─ evaluate/          # boundary/audio/subtitle/translation QA
│  └─ publish/           # YouTube
├─ workflows/
│  ├─ concert-clips/
│  ├─ robot-competition/
│  ├─ travel-video/
│  └─ shorts/
├─ profiles/             # Roy style/translation/channel presets
├─ evaluations/          # fixtures、golden EDL、A/B preferences、scores
└─ apps/                 # CLI first；Web review GUI later
```

核心原則：workflow 只組合 capability；provider 是 adapter；所有模型都可替換；LLM 產生的是結構化 plan，不是直接改影片；每一個昂貴或不可逆步驟都有 preview、成本估算與 gate。

## 建議採用順序

### V0：把今天的原型變成可重播 pipeline

1. 建立 uv mono-repo、`ProjectManifest`、`AssetRef`、`EditDecisionList`、artifact cache。
2. 將現有 HACHI 成片與字幕變成 golden fixtures，不先重寫演算法。
3. 封裝 yt-dlp、FFmpeg/ASS、WhisperX、VideoLingo-like translation stages。
4. 產生 review package，而不是直接公開。

### V1：Concert Live Workflow

1. 版權 evidence collector（只給 evidence＋風險，不宣稱法律判決）。
2. 章節／留言／音訊多訊號切歌，保留 end candidate previews。
3. 官方歌詞優先、翻譯 provenance、Roy A/B preference dataset。
4. music-aware alignment、振假名 layout、karaoke regression tests。
5. private YouTube upload＋人工 publish gate。

### V2：通用私人剪輯師

1. Google Drive asset library 與增量同步。
2. 參考 video-use 的自然語言 strategy→approval→EDL→self-eval。
3. `robot-competition` 與 `travel-video` workflows。
4. Web review GUI：素材、transcript、timeline、修改建議與批准。

### V3：生成式剪輯

1. OpenRouter `VideoGenerator`、`ImageGenerator` adapters。
2. Seedance 等 provider capability discovery、成本 preview、非同步 job persistence。
3. AI B-roll／片頭／示意動畫只作候選素材，人工核准後進 timeline。
4. 逐步評估本機 ComfyUI 與 Remotion templates，保持 optional。

## 不建議的捷徑

- 不 fork 某個「一鍵短影音」repo 後硬塞所有需求；產品領域模型會被 demo workflow 綁死。
- 不讓 LLM 直接自由生成 FFmpeg shell；先產 EDL，再由 deterministic renderer 執行。
- 不用單一 ASR 的 confidence 宣稱卡拉 OK 已精準；必須有逐字／音節 alignment 和視覺 QA。
- 不把「網路找到翻譯」等同可轉載；來源、授權、署名是不同欄位。
- 不將生成式影音當既有鏡頭的修復真相；必須標示 AI-generated provenance。
- 不在沒有 cost preview 與人工批准時自動呼叫付費生成 API。

## 最終判斷

**Go：建立通用 `roy-ai-editor` repo，Concert Live Workflow 是第一個 Editing Workflow。**

第一版最值得借用的是 video-use 的 agent/EDL/review-loop 心智模型與 VideoLingo/WhisperX 的字幕能力；FFmpeg/ASS 保持主 renderer。Director、MoneyPrinterTurbo、Remotion、ComfyUI 則各借 agent UI、短片 generation workflow、模板渲染、生成式 graph，但都不應成為核心依賴。

Seedance 2.0 可以經 OpenRouter 正式 API 接入，適合成為生成 B-roll 的 provider；它不是剪輯器，也不應取代 Roy 對最終成片的核准。
