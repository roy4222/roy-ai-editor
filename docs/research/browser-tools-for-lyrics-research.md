---
type: investigation
status: draft
date: 2026-07-18
tags:
  - topic/browser-automation
  - topic/lyrics
  - workflow/concert-live
---

# Concert Live Workflow：歌詞研究瀏覽器工具評估

> 調查日期：2026-07-18。只採用五個專案自己的 README、文件、source manifest、license 與 release 資料。使用者稱「瀏覽器六劍客」，但訊息實際只列出五個專案；本文不臆測缺少的第六個工具，也沒有安裝任何工具。

## 結論先行

**先只採用 `agent-browser` 作為 Concert Live Workflow 的主瀏覽器控制器。不要同時安裝五套。**

它已覆蓋這個 Workflow 真正需要的能力：以 accessibility snapshot／semantic locator 操作動態頁、讀取 rendered DOM、保留 screenshot／PDF／HAR、隔離 session、重用登入狀態，以及把 credentials 留在本機。它同時有 Codex skill 與 MCP 路徑；其 `read` command 可先做低成本 HTTP 讀取，失敗後再升級到完整 Chrome。更重要的是，五個候選中只有它的官方 README 同時明確提供 encrypted auth vault、content boundary、domain allowlist、action policy 與 output limit；這些控制能降低網頁 prompt injection、誤操作和憑證外洩面積。[官方 README：commands、Codex integration、auth 與 security](https://github.com/vercel-labs/agent-browser/blob/main/README.md)

其他四套的定位如下：

- `playwright-cli` 是最合理的**替代品／基準組**，不是第二套常駐工具。若 `agent-browser` 在 Bahamut golden fixture 上不穩，再用相同 fixture A/B 測試它。
- `Actionbook` 的 action manual 概念適合未來重複性很高的 YouTube 上傳，但沒有一手資料保證 Bahamut manual coverage；而且最新 repo README 已把 standalone CLI 標為 deprecated，官方文件仍以 CLI 為主，現階段不宜成為 Production dependency。[最新 repo README](https://github.com/actionbook/actionbook#installation)、[仍描述 CLI 的官方文件](https://actionbook.dev/docs/guides/installation)
- `browser-use` 適合未來把 autonomous browser agent 嵌進產品程式，不適合在 Codex 外再疊一個 LLM browser loop。CLI／local Chrome 可用，但與 `agent-browser` 高度重疊；Python library 還會增加模型 provider、API key、成本與不確定性。[官方 README](https://github.com/browser-use/browser-use#python-library-the-easiest-way-to-automate-the-web)
- `Agent-Reach` 是跨平台搜尋／讀取工具的 installer、router 與 doctor，不是瀏覽器操作器。它對 Twitter、Reddit、Bilibili 等未來社群研究有價值，但現階段的 Jina Reader、Exa、yt-dlp、gh 路徑與既有能力重疊，也不能取代動態頁與 provenance capture。[官方 README：能力邊界與設計理念](https://github.com/Panniantong/Agent-Reach#%E8%83%BD%E5%8A%9B%E8%BE%B9%E7%95%8C%E8%AF%BB%E5%86%85%E5%AE%B9-vs-%E6%93%8D%E4%BD%9C%E7%BD%91%E9%A1%B5)

**最小工具組不是「五選二」，而是「一個瀏覽器＋Roy AI Editor 自己的 evidence collector」。** 瀏覽器只負責 discovery 和 capture；source／translator／reuse evidence 必須轉成結構化 Evidence Artifact，且任何工具都不得把「找到翻譯」自動提升成「可重用」。

## 需求基準

現有 [`roy-edit-concert-live` skill](../../skills/roy-edit-concert-live/SKILL.md) 要求每首歌先找官方日文歌詞，再執行精確曲名、歌手、`巴哈`、`site:home.gamer.com.tw` 及別名查詢；找到頁面後，還要記錄 URL、標題、translator、reuse permission、署名、修改限制與不確定性。這不是單純的「網搜」問題，而是以下完整鏈：

1. **Discovery**：精確 query、site query、日文／羅馬字／翻唱原唱變體，可重試且能記錄零結果。
2. **Dynamic capture**：處理 SPA、展開全文、lazy load、登入牆與搜尋結果頁。
3. **Provenance extraction**：把頁面作者、譯者、發布標題、最終 URL、發布／擷取時間和內容 hash 結構化。
4. **Rights evidence**：擷取明示 reuse terms；沒有條款時只能標示 `unknown`，不能推測授權。
5. **Review handoff**：形成版本化 lyrics／translation／line-break approval packet，讓 Roy 只在真正必要的 gate 做一次有資訊的判斷。

瀏覽器工具只能改善前 1–3 項並協助收集第 4 項證據。它不能取代歌詞核准 gate，也不能自行作法律判斷。

## 比較總表

| 工具 | 本質／介面 | 動態頁與擷取 | 登入／狀態 | Codex 適配 | 安全與憑證風險 | 安裝／維護 | 本案判定 |
|---|---|---|---|---|---|---|---|
| [`agent-browser`](https://github.com/vercel-labs/agent-browser) | Native Rust CLI；另有 skill、typed MCP | snapshot refs、semantic find、rendered DOM `read`、screenshot、PDF、network/HAR | Chrome profile copy、persistent profile、session restore、state file、encrypted auth vault | 官方明列 Codex skill；CLI 與 MCP 都可用 | state file 預設含明文 token；remote debugging port 可被本機 process 控制；security flags 多為 opt-in | macOS ARM64 native；Homebrew/npm/Cargo；需 Chrome for Testing | **採用，唯一主 browser** |
| [`playwright-cli`](https://github.com/microsoft/playwright-cli) | Microsoft Playwright CLI＋skill | snapshot refs、`find`、CSS／role／test-id locator、screenshot、network／console、三 browser engines | session 內 cookies；`--persistent`／user data dir 可跨重啟 | 官方定位 coding-agent CLI；可安裝 skill | Reviewed README 未描述 encrypted vault、content boundary 或 action policy；persistent profile 需自行保護 | Node 18+；`@playwright/cli`；目前 manifest 為早期 `0.1.x` 且 pin alpha Playwright build | **只作 fallback benchmark** |
| [`Actionbook`](https://github.com/actionbook/actionbook) | action manuals＋browser control；最新 README 改為 hosted MCP＋Chrome extension | manuals、snapshot、text/html、screenshot、PDF、network/HAR；舊 CLI docs 有 local/cloud/extension | extension 可操作已登入的 real Chrome；cloud profiles | MCP 可接 agent；舊 docs 提供 Codex setup target | hosted connector／extension 擴大 trust boundary；manual coverage 是外部服務資料；官方 repo 與 docs 現況矛盾 | 最新 README 說 CLI deprecated，但 docs 仍要求 Node 18+ CLI；高漂移 | **暫不採用** |
| [`browser-use`](https://github.com/browser-use/browser-use) | Python library 的 LLM agent；另有 browser CLI／skill | local Chrome/CDP、cloud browser、任意 Python browser action；Agent 可做自主多步驟任務 | 可直接接 running Chrome；cloud 有 persistent profiles | 官方明列 Codex skill；CLI 適合 one-off，Python library 適合產品嵌入 | local CDP 能取得既有 tabs/cookies/extensions；cloud profile 會把 auth state 交給服務；Python surface 權限很大 | Python 3.11+；官方 setup 建議 Python 3.12；library dependency 與模型 provider 較重 | **未來嵌入式 agent 候選，現在不裝** |
| [`Agent-Reach`](https://github.com/Panniantong/Agent-Reach) | 多渠道 selector／installer／router／doctor；實際由 upstream CLIs 執行 | Jina Reader 讀頁、Exa 搜尋、yt-dlp 取字幕；官方明說高摩擦網頁操作要配別的 browser tool | 部分渠道用 OpenCLI／cookie；核心不是 browser session manager | 任何可 exec shell 的 agent；可安裝 skill | config 權限 600，但 docs 未聲稱加密；官方警告 cookie 等同完整登入權並有封號風險 | Python 3.10+，但 core install 還會裝／改 gh、Node、mcporter、Exa、yt-dlp config；surface 最大 | **未來社群研究候選，歌詞流程不裝** |

## 逐項判讀

### 1. agent-browser：最符合本案的單一主工具

`agent-browser` 的核心 loop 是 `open → snapshot → click/fill → re-snapshot`；同時支援 traditional selector 和 ARIA role／text／label 等 semantic locators。`read URL` 不啟動 Chrome，會優先要求 Markdown、探索 `llms.txt`，最後 fallback 到 HTML readable text；無 URL 時則讀目前 active tab 的 rendered DOM，包含 auth state 與 client-side update。這恰好可以形成「先便宜抓、動態頁才開瀏覽器」的 escalation path。[官方 commands](https://github.com/vercel-labs/agent-browser/blob/main/README.md#commands)

它還能輸出 screenshot、PDF、network requests、HAR、trace 與 page errors，適合把「搜尋到了什麼」變成可重播的 Evidence Artifact，而不是只保留 agent 摘要。CLI 的 `--json` 和 typed MCP 也比自由文字 scraping 更容易接入 Project Manifest。[官方 MCP surface](https://github.com/vercel-labs/agent-browser/blob/main/README.md#mcp-server)

登入方面，官方支援 Chrome profile 的 read-only snapshot、獨立 persistent profile、session restore、state file 與 auth vault。auth vault 永遠加密，session restore 可用 AES-256-GCM；但官方也明確警告：一般 state file 含 plaintext session token，而 `--remote-debugging-port` 讓任何本機 process 都可能取得完整 browser control。[官方 authentication 與 warnings](https://github.com/vercel-labs/agent-browser/blob/main/README.md#authentication)

安全功能符合 Production 流程需要，但不是預設全部開啟：content boundary、domain allowlist、action policy、action confirmation 和 output limit 都要主動配置。domain allowlist 又不能與 pre-existing CDP、Chrome profile、restore/state replay 等模式混用，因此 discovery session 與 authenticated capture session 應拆開，不要幻想用一個 session 同時取得最大登入便利和最大網路隔離。[官方 security limitations](https://github.com/vercel-labs/agent-browser/blob/main/README.md#security)

安裝面是五項中最適合 Mac mini 的：官方提供 macOS ARM64 native binary、Homebrew／npm／Cargo，下載 Chrome for Testing 後 daemon 不需要 Node 或 Playwright；只有從 source build 才要求 Node 24、pnpm 11、Rust。License 為 Apache-2.0。[官方 installation／platforms](https://github.com/vercel-labs/agent-browser/blob/main/README.md#installation)、[package manifest](https://github.com/vercel-labs/agent-browser/blob/main/package.json)

### 2. playwright-cli：可靠替代路徑，但不要和主工具雙持

Microsoft 把 `playwright-cli` 定位為 coding agents 的 token-efficient CLI，提供 snapshot refs、snapshot depth、snapshot search、CSS selector、role locator、test-id locator、named sessions、persistent profile、visual monitoring dashboard，以及 Chromium／Firefox／WebKit／CDP configuration。對「搜尋、打開動態頁、擷取文字、截圖」而言，它與 `agent-browser` 高度重疊。[官方 README](https://github.com/microsoft/playwright-cli/blob/main/README.md)

它的優勢是 Playwright 生態成熟、三 engine 與 locator 模型熟悉；缺點是本工具本身仍早期：main branch manifest 目前為 `0.1.17`，並 pin 一個 Playwright alpha build。Reviewed README 也沒有記載 `agent-browser` 等級的 encrypted credential vault、prompt-injection content boundary 或 action policy；若採用，需要 Roy AI Editor 自己補 security wrapper。[package manifest](https://github.com/microsoft/playwright-cli/blob/main/package.json)

因此不要同時維護兩套 selectors、profiles、sessions 與 browser downloads。只有當 golden fixture 顯示 `agent-browser` 在目標站的成功率不足時，才把 `playwright-cli` 當 replacement candidate。其 License 為 Apache-2.0，runtime 要 Node 18+。[官方 install／requirements](https://github.com/microsoft/playwright-cli/blob/main/README.md#installation)、[LICENSE](https://github.com/microsoft/playwright-cli/blob/main/LICENSE)

### 3. Actionbook：manual layer 有吸引力，但官方 surface 正在轉向

Actionbook 的差異化不是另一個 click CLI，而是「先 search/get action manual，再用維護過的 selector 操作網站」。對固定且高頻的 YouTube upload flow，若官方有該站 manual，這種 layer 可能比每次探索 DOM 更省 token、更抗 UI 變更。[Actionbook introduction](https://actionbook.dev/docs)

但目前有兩個阻塞：

1. 公開文件只用 Airbnb、Google、YouTube 等例子說明 `actionbook search/manual`，沒有承諾 `home.gamer.com.tw` coverage。採用前必須實際查 manual inventory，不能只依產品宣稱推論它能處理巴哈。[CLI reference](https://actionbook.dev/docs/api-reference/cli)
2. 最新 GitHub README 說 standalone `@actionbookdev/cli` 已 deprecated，改用 hosted remote MCP＋Chrome extension；同時官方 installation／browser docs 仍教 Node 18+ CLI、local/cloud/extension 三種模式。這個一手來源衝突代表介面正在快速遷移，不適合現在寫進 Concert Live Workflow 的 deterministic dependency。[最新 repo README](https://github.com/actionbook/actionbook#installation)、[CLI installation docs](https://actionbook.dev/docs/guides/installation)、[browser docs](https://actionbook.dev/docs/guides/browser)

extension mode 會操作使用者已登入的 real Chrome，hosted MCP／dashboard 又引入外部 service trust boundary。它不是必然不安全，但要先完成資料流、extension permissions、logged-in page content 與 retention 審查。Repo 採 Apache-2.0。[repo license metadata](https://github.com/actionbook/actionbook)

### 4. browser-use：等產品需要自己的 autonomous browsing runtime 再評估

Browser Use 有兩個不要混淆的 surface：

- Browser Use CLI 給既有 coding agent 直接控制 browser；可接本機 running Chrome、Browser Use Cloud 或任意 CDP，並能重用現有 tabs、cookies、extensions 與 logins。它實際允許 agent 傳 Python browser commands，權限範圍很大。[官方 CLI docs](https://docs.browser-use.com/open-source/browser-use-cli)
- Python library 建立另一個 `Agent(task, llm)` loop，需要 Browser Use 或其他模型 provider key；可自訂 tools、structured output 與 agent behavior，適合嵌入自己的產品。[官方 README](https://github.com/browser-use/browser-use#python-library-the-easiest-way-to-automate-the-web)

Roy 現在已由 Codex 做 director，因此再疊 Python `Agent` 會產生兩層規劃、兩份 prompt、額外模型成本與較難重播的決策。CLI 又與 `agent-browser` 重疊。等未來 Roy AI Editor 需要在沒有 Codex session 時自行執行排程研究，或需要 Python custom tools／structured-output agent 時，再用 bounded evaluation 評估 library，不先把它加進 repo dependency。

本機模式的 CDP 會接觸現有登入狀態；cloud mode 提供 proxy、CAPTCHA、persistent profile，但 remote browser 會持續計費直到停止，且 auth state 進入外部服務邊界。官方還表示 CAPTCHA handling 需要 cloud stealth/proxy；Concert lyrics research 不應為了繞 challenge 預設啟用這條路。[CLI cloud notes](https://docs.browser-use.com/open-source/browser-use-cli#cloud-browsers)、[README CAPTCHA／production notes](https://github.com/browser-use/browser-use#faq)

Library 為 MIT，Python 要 `>=3.11`；目前 manifest 包含多個模型 SDK、telemetry client 與 Google APIs，維護面顯著大於單一 browser CLI。[LICENSE](https://github.com/browser-use/browser-use/blob/main/LICENSE)、[pyproject](https://github.com/browser-use/browser-use/blob/main/pyproject.toml)

### 5. Agent-Reach：廣度工具，不是本次動態歌詞頁的解法

Agent-Reach 官方自己把產品定義為 capability layer：負責選型、安裝、doctor 與 backend routing，實際讀取由 Jina Reader、Exa、yt-dlp、gh、OpenCLI 等 upstream tools 完成。它也明確把登入後網頁操作、表單、多帳號、風控接手列為另一類 browser automation 問題。[官方設計理念／能力邊界](https://github.com/Panniantong/Agent-Reach#%E8%83%BD%E5%8A%9B%E8%BE%B9%E7%95%8C%E8%AF%BB%E5%86%85%E5%AE%B9-vs-%E6%93%8D%E4%BD%9C%E7%BD%91%E9%A1%B5)

它能補強跨平台 discovery：Exa 全網語義搜尋、Jina Reader、YouTube 字幕與 Bilibili／Twitter／Reddit 等渠道。但 Concert Live 現階段已有 yt-dlp，Codex 有搜尋能力，主瀏覽器也能開搜尋引擎和讀頁；安裝 core 還會配置 gh、Node、mcporter、Exa 與 yt-dlp，增加不必要的重疊與變動。[官方 support matrix／installer actions](https://github.com/Panniantong/Agent-Reach#%E6%94%AF%E6%8C%81%E7%9A%84%E5%B9%B3%E5%8F%B0)

安全方面有 `--safe` 和 `--dry-run`，config/token 權限設為 600；但官方沒有說這些 cookie 是加密保存，並明確警告 cookie 等同完整登入權、非正常 API 行為可能封號，建議使用專用小號。這不適合為單純查歌詞擴大 credential surface。[官方 safety guidance](https://github.com/Panniantong/Agent-Reach#%E5%AE%89%E5%85%A8%E6%80%A7)、[install safe mode](https://github.com/Panniantong/Agent-Reach/blob/main/docs/install.md)

Agent-Reach 為 MIT、Python 3.10+，但其價值是未來要同時研究 Twitter／Reddit／Bilibili 社群訊號時再導入，不是目前的 Bahamut dynamic page capture。[pyproject](https://github.com/Panniantong/Agent-Reach/blob/main/pyproject.toml)、[LICENSE](https://github.com/Panniantong/Agent-Reach/blob/main/LICENSE)

## 建議的最小實作

### 1. 兩層 browser escalation

```text
精確 query / site query
  → 保存 query、時間、engine、result URL/title/rank
  → agent-browser read URL（無 Chrome、低成本）
  → 若內容缺失／JS／登入牆：獨立 Chrome session 開頁
  → rendered DOM + screenshot + resolved URL
  → provenance parser
  → Evidence Artifact
  → lyrics approval packet
```

Anonymous discovery 與 authenticated capture 要分成兩個 session：

- **Discovery session**：無登入、fresh profile，啟用 content boundaries、output limit 與可行的 domain allowlist。
- **Authenticated capture session**：只在確有必要時使用專用 `roy-lyrics` profile；不複製 Roy 的日常主 profile。session state 加密，repo 只保存 opaque reference，不保存 cookie/token。

### 2. Evidence Artifact 最小欄位

每次 search attempt 至少記錄：

```json
{
  "query": "site:home.gamer.com.tw <song> <singer>",
  "engine": "<search engine>",
  "searched_at": "<ISO-8601>",
  "results": [
    {"rank": 1, "url": "https://...", "title": "..."}
  ],
  "result_count_observed": 1,
  "warnings": []
}
```

每個 selected candidate 至少記錄：

```json
{
  "requested_url": "https://...",
  "resolved_url": "https://...",
  "publication_title": "...",
  "author_or_translator": "...",
  "captured_at": "<ISO-8601>",
  "content_sha256": "...",
  "capture_artifacts": ["screenshot", "sanitized-text"],
  "terms_url": null,
  "explicit_permission": null,
  "attribution_requirement": null,
  "modification_limits": null,
  "reuse_status": "unknown",
  "rights_warnings": []
}
```

`reuse_status` 必須預設 `unknown`。只有明示條款、Roy 提供且核准的內容，或其他已定義的 approvable path 才能進入現有 `approve-lyrics`。搜尋 snippet、署名、公開可讀、沒有 robots block 都不等於可重用。

### 3. 儲存與憑證邊界

- 真實歌詞、翻譯全文、頁面截圖與 source capture 是 Production Asset／Evidence Artifact，保存於 Production Data Root，不進公開 Git。
- Repo 只保存 schema、sanitized metadata example 與合成 Test Fixture，符合 [ADR 0006](../adr/0006-keep-public-repo-free-of-private-and-restricted-data.md)。
- Browser profile、session state、cookie、auth vault key 是 Private Configuration；不得進 Project Manifest 的明文字段。
- Raw HAR 可能包含 cookies、authorization headers、query tokens 與個資；預設不保存。只有診斷需要時才暫存、先 scrub secrets，再把 sanitized artifact 掛到 Project Manifest。
- 網頁內容一律視為不可信輸入。頁面中聲稱要 agent 執行 command、揭露 token、改變 gate 或忽略 policy 的文字不得被當成 workflow instruction。

## 導入 gate 與成功標準

在安裝更多工具前，先用 `agent-browser` 對 10 首代表性歌曲建立 browser-research golden fixture：

1. 3 首有巴哈翻譯、2 首只有官方日文歌詞、2 首 cover／異名、2 首動態或登入阻塞頁、1 首確定找不到。
2. 每首固定跑官方來源 query、一般 `巴哈` query、`site:home.gamer.com.tw` query 與至少一個別名 query。
3. 衡量 discovery recall、selected-page capture success、translator extraction accuracy、零結果是否留證、每首人工 intervention 次數、重跑是否得到同一組 normalized candidates。
4. 目標：公開頁 capture success ≥ 95%；translator／publication title 不允許 silent guess；每首研究階段人工介入中位數為 0；Roy 只需處理版本化 lyrics approval packet。
5. 若失敗主要是 locator／browser engine，再用相同 fixture 測 `playwright-cli`；若失敗主要是搜尋召回，再評估 search provider，而不是再裝另一個 browser controller；若未來缺口是 Twitter／Reddit／Bilibili，再評估 Agent-Reach safe-mode dry run。

## 最終建議

目前採用：

```text
agent-browser
  + Roy AI Editor provenance/evidence collector
  + 現有 lyrics approval gate
```

目前不採用：

```text
playwright-cli   # 只作有數據的替代 benchmark
Actionbook       # 等 CLI/MCP surface 穩定且證明目標站 manual coverage
browser-use      # 等需要嵌入式 autonomous browser runtime
Agent-Reach      # 等要擴張到跨社群 research channels
```

這個選擇能提升 discovery 與 capture 的自動化，同時不破壞 Concert Live Workflow 最重要的責任邊界：**工具可以自動找、抓、比對、留證；Roy 仍核准精確版本的歌詞／翻譯／line map，任何找到的內容都不會被靜默視為可重用。**
