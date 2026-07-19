---
status: accepted
---

# Keep the Production Core headless

Concert Live Production Golden Path 必須由 Headless Production Core 從 URL 完成到 private YouTube link，不依賴 CapCut、DaVinci Resolve、Kdenlive、BaoCut、Blender 或其他 GUI 點擊。Production Toolchain 由 repo 的 Brewfile／bootstrap、強化後的 `roy-editor doctor`、CI Test Fixtures、Production Capability Spikes 與 Dedicated Editor Host media smoke tests 管理，並依 ADR 0042 打包成鎖定精確版本／checksum 的 Production Toolchain Release；每個 job 與 Render Manifest 記錄 release ID，runtime 不得抓取浮動 `latest`。核心包含固定 Python／uv、具 libass／fontconfig／freetype 的 FFmpeg／FFprobe、Noto CJK 字型、`yt-dlp[default]` 與 Deno、作為 V1 唯一 browser controller 的 agent-browser、可替換 alignment adapter、YouTube Data API／OAuth，以及 macOS launchd 管理的持久化 Production Worker。其他 browser controllers 只能依 ADR 0033 的量化替代 benchmark 進入，不得同時成為重複必備工具；其他卡拉 OK／subtitle candidates 只能依 ADR 0034 的三個 bounded spikes 升格。媒體運算遵守 Local-First Compute Policy；沒有 Roy 核准的 Cloud Compute Profile 時，External GPU 不得成為隱藏依賴。Codex Control Surface 建立 Production Job Request、呈現 review／結果並把 timestamped natural-language feedback 轉為 Revision Request；worker 以 idempotent stages、job lease 與 Project Manifest checkpoints 執行，關閉對話、登出或重啟後都能續跑且不得重複下載／上傳。GUI timeline 只可作未來可選的檢視／精修 surface，其他 GUI 工具只可透過 External Capability Adapter 提供實驗或人工 finishing；移除後不得使正式流程失去重建或修改能力。
