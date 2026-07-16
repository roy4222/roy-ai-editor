# SETUP — 先回答這些問題，讓這套系統變成「你的」

> **這個 repo 不是要你直接套用某個人的設定，而是一個「框架 + 問卷」。**
> 它把一套實戰過的 YouTube / 短影音自動化系統抽成模板 —— 你回答下面的問題，
> 就生成**屬於你自己**的 voice / 品牌 / 策略 / 社群檔。
> 程式碼是通用的；**個人化 100% 來自你的答案，沒有任何原作者的私人數據**。

---

## 🧭 平台需求（先看這個再往下）

這個 kit 有**兩條 first-class path**，需求不同：

- **Path 1 — Programmatic（推薦採用者預設；Win / Mac / Linux）**：只要 Python 3.9+ 和 `ffmpeg`/`ffprobe`。

  **安裝 ffmpeg（一次搞定，三平台都有）**：
  | 平台 | 指令 |
  |---|---|
  | macOS | `brew install ffmpeg`（需 [Homebrew](https://brew.sh)；裝完 `ffmpeg -version` 驗證）|
  | Windows | `winget install ffmpeg` 或到 [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) 下載 full build 加入 PATH |
  | Linux | `sudo apt install ffmpeg`（Debian/Ubuntu）|

  > 常見誤會：「Mac 沒有 ffmpeg」——ffmpeg 本來就是跨平台的，Mac 裝起來反而最簡單（一行 brew）。MoviePy / editly 這類「替代方案」底層其實還是在呼叫 ffmpeg。**不需要 CapCut、不需要 Computer Use**。Mac/Linux 的系統路徑與 CJK 字型由 `src/platform_compat.py` 自動探測。
- **Path 2 — CapCut-assisted（作者本人主用；Windows-first）**：額外需要 CapCut Desktop 國際版 + AI 助手的 Computer Use。**版本敏感** —— 動草稿 JSON 前先讀 [TROUBLESHOOTING](TROUBLESHOOTING.md) 的版本相容矩陣。
- **Mac 用戶** → 直接走 Path 1（CapCut 的 GUI 自動化在 Mac 上沒有可用的等效機制）。

---

## ⚡ 最快上手（不用一次填完！）

> **覺得問卷很長？不用全部填完才能開始。** 下面 6 區只有 **3 區是 ★必答**，其餘**邊做邊補**就好。

**推薦做法 —— 讓 AI 訪談你（最省力）：**
把整個 repo 丟給 Claude / ChatGPT，貼這句：
> 「照 `SETUP.md` 的 **★必答 3 區先問我**（品牌、Niche、製作設定），用我的答案生成 `profiles/`。其餘選填區之後再問。」

AI 會一題一題問、自動幫你填，你**只要用講的回答**，不用自己動手寫檔案。

**5 分鐘最小啟動（只回答這 3 題就能開跑）：**
1. 你的頻道叫什麼？**你會露臉嗎？**（決定開頭/結尾要不要排露臉 cue）
2. 你做什麼類型、主打哪個平台？（教學/vlog…、YT長片/Shorts/Reels）
3. 你走 **Path 1（純程式，跨平台）**還是 **Path 2（CapCut，Windows-first）**？素材/匯出路徑在哪？

→ 填完這 3 題就能開始剪。Voice / 演算法 / 社群（4️⃣5️⃣6️⃣）**之後想優化再補**。

**手動做法（3 步）：**
1. 把 `templates/` 複製成 `profiles/`，照此對照命名（不是單純去 `.template`）：
   `brand_profile`→`brand.md`、`voice_profile`→`voice.md`、`algorithm_context`→`algorithm.md`、
   `community_mobilization`→`community.md`、`content_pipeline`→`content_pipeline.md`、`your_context`→`your_context.md`
2. 先填 **★必答** 區（1️⃣2️⃣4️⃣），其餘留白
3. 複製 `config.example.py` → `config.py`，填你自己的路徑

---

## 1️⃣ 品牌 / 頻道 → 生成 `profiles/brand.md`　★必答
- 你的頻道名稱 + handle？
- 網站 / 主要連結？
- **招牌結尾怎麼收？**（口播 / 字卡 / 露臉？）這會變成你每支片的 signature outro
- ⚠️ **你會錄 talking-head / 露臉嗎？**（很重要 —— 不露臉的話，開頭/結尾規劃要改用 b-roll + 字卡，不能排「自拍 cue」）
- 品牌色 / 偏好字體？訂閱 CTA 怎麼放？

## 2️⃣ 內容類型 / Niche → 決定 pipeline 路由　★必答
- 你做什麼類型？（教學 / vlog / 開箱 / 評論 / 遊戲 …）
- 主戰場？（YT 長片 / Shorts / Reels / TikTok）
- 語言？（中 / 英 / 雙語）

## 3️⃣ 你的聲音 / Voice → 生成 `profiles/voice.md`　⭕選填（之後優化腳本再補）
- **貼 5–10 篇你「自己寫過」的腳本 / 貼文** —— 系統學的是**你的**語氣，不是套別人的
- 你的開場習慣？口頭禪？收尾方式？
- **絕對不要的詞 / 語氣？**（anti-patterns —— 例如不講髒話、不裝熟、不用某些網路用語）

## 4️⃣ 製作設定 / Production → 生成 `config.py`　★必答
- **你走哪條 path？**（見最上面「平台需求」）
  - **Path 1 Programmatic**（推薦預設；Win/Mac/Linux）—— 純程式 pipeline，只要 Python + ffmpeg，**不需要 CapCut**
  - **Path 2 CapCut-assisted**（Windows-first）—— 要用 CapCut 的花字 / 雲端模板才選這條
- 走 Path 2 的話：**CapCut Desktop 國際版**裝了嗎？⚠️ **AI 助手有開 Computer Use 嗎？** CapCut 沒有公開 API，GUI 自動化是靠 **AI 透過 Computer Use 實際操作 CapCut 視窗**（套模板 / 匯出）——沒開就跑不了。草稿 JSON 直改**版本敏感**，先跑 `detect_draft_format()` + 讀 [TROUBLESHOOTING](TROUBLESHOOTING.md)
- 你的**字體檔**放哪？**BGM** 放哪？**b-roll 庫存**放哪？專案 / 匯出路徑？
- （這些會填進 `config.py`，取代範例路徑 —— 範例**不含任何人的帳號名**）

## 5️⃣ 演算法現況 / Algorithm → 填進 `profiles/algorithm.md`　⭕選填（發片要衝數據再補）
- 你頻道現在的數字？（訂閱 / 平均觀看 / CTR / 平均觀看時長 AVD）
- 主要 traffic source？（Browse / Suggested / Search / External …）
- 最大痛點？（觸及掉 / 留存差 / CTR 低 …）
- （框架給你「**該看哪些指標、怎麼補**」的 checklist；**數字填你自己的**）

## 6️⃣ 社群 / 外部流量 / Community → 填進 `profiles/community.md`　⭕選填（要做社群動員再補）
- 你有哪些社群？各多少人？（Discord / Line / FB / IG …）
- 發片時能動員的管道有哪些？
- （給你「外部流量動員 SOP」的**結構**；你的社群、你的數字）

---

## 📦 你會得到什麼

| 填完 | 你就有 |
|---|---|
| 1️⃣ 品牌 | 你的 outro signature + 露臉/不露臉規劃規則 |
| 2️⃣ Niche | 自動 pipeline 路由 |
| 3️⃣ Voice | **你的**語氣 profile（腳本/文案套你的調）|
| 4️⃣ Production | `config.py`（你的路徑/字體/BGM）|
| 5️⃣ Algorithm | 演算法 checklist（填你的數字）|
| 6️⃣ Community | 外部流量動員 SOP（套你的社群）|

→ 然後用 `src/` 的工具跑**你的**流程：**Path 1** = 純程式 pipeline（`longform_maker` / `silent_vlog_maker` + QA gates，跨平台）；**Path 2** = CapCut 自動化（AI + Computer Use 操作 CapCut，Windows-first）。

---

## ❓ 為什麼是「問卷」不是「現成設定」？

因為一套創作系統最值錢的是**結構與方法論**，不是某個人的私人數字。
直接抄別人的 voice / 策略 / 社群數據，對你沒用，還可能誤導。
所以這個 repo 給你**骨架**，你用自己的血肉填滿 —— 這樣它才真的是**你的**系統。
