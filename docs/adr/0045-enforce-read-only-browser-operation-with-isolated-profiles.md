---
status: accepted
supersedes: 0023-use-a-persistent-read-only-browser-profile-for-discovery.md
---

# Enforce read-only browser operation with isolated profiles

Concert V1 使用兩個彼此隔離、不得與 Roy 日常瀏覽器或 API publisher credential 共用 cookies／storage／Keychain items 的 browser identities：`roy-concert-discovery` 只讀 YouTube／歌詞研究來源，`roy-studio-verify` 只讀 Roy 自有影片的 YouTube Studio restriction 狀態。每個 identity 都綁定版本化 Browser Read-Only Enforcement Profile。controller 啟動時必須開啟 content-boundary markers、固定 output limit、domain／path allowlist 與 default-deny static action policy；只允許 navigate、read、snapshot、screenshot、scroll，以及經 locator allowlist 的展開留言／說明動作。type、form submit、upload、download、clipboard write、generic `eval`／JavaScript、social interaction、settings、Studio editor 與所有 mutation action 一律拒絕。頁面／留言／OCR 內容只是不可信資料，不能修改 action policy、要求秘密、擴張 domain 或授權工具動作。

每次 run 產生 Browser Action Ledger，記錄 profile／policy version、URL、redirect、動作分類、locator、結果與 screenshot／snapshot hash；unexpected navigation、download、mutation 或 policy mismatch 立即 fail closed，不能靠 prompt 指示繼續。`roy-studio-verify` 先以 YouTube channel permission 的最低可行 viewer role 做 fixture 驗證；若 restriction 欄位只有更高角色可見，仍使用獨立 account/profile 與同一 default-deny controller，不得改用 owner 的日常 session。重新驗證、CAPTCHA 或頁面變更造成政策無法證明唯讀時，只建立 shared blocker／Exception Review；browser 永遠不能 fallback 到 upload、metadata edit、dispute、visibility change 或 deletion。

此決策依賴 agent-browser 官方提供的 opt-in encrypted auth vault、content boundaries、domain allowlist、action policy 與 action confirmation；因為安全功能不是預設開啟，Production Toolchain 必須以 pinned config 強制啟用，而不能把 CLI 預設值當作安全邊界。YouTube 官方 channel permissions 說明 viewer 類角色可限制更新能力，但部分功能不支援 delegated access，因此 Studio restriction 可見性必須以 versioned fixture 實測，不得假設角色矩陣。參考：<https://github.com/vercel-labs/agent-browser#security>、<https://support.google.com/youtube/answer/9481328>。
