---
status: superseded
superseded_by: 0045-enforce-read-only-browser-operation-with-isolated-profiles.md
---

# Use a persistent read-only browser profile for discovery

Timeline Discovery 使用 Dedicated Editor Host 上持久化的 `roy-concert-discovery` Discovery Browser Profile；需要登入時由 Roy 完成首次驗證，之後 Roy AI Editor 可以自行打開 YouTube、展開並捲動留言。這個 profile 嚴格唯讀，不得留言、按讚、訂閱或修改帳號，cookies 與登入狀態視為 Private Configuration 且不得進 Git；遇到 CAPTCHA、重新驗證或權限失效時進入 Exception Review，不嘗試繞過。影片上傳使用 ADR 0041 的 Production Publisher Credential，Visibility Promotion 使用隔離的 Privileged YouTube Executor；兩者都走可稽核且 idempotent 的正式 API，不得重用 Discovery Browser cookies 或透過 browser clicks 繞過 scope 邊界。
