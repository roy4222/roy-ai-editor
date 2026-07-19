---
status: accepted
---

# Separate minimal private upload from privileged YouTube actions

Concert V1 的常駐 Production Worker 只取得 `youtube.upload` 與 `youtube.readonly` 組成的 Production Publisher Credential：前者可 `videos.insert`／`thumbnails.set`，後者可在上傳前以 `channels.list(mine=true)` 驗證 OAuth 身分、執行 ADR 0046 的 own-channel orphan reconciliation，並在上傳後以 `videos.list` 輪詢 private 影片狀態；兩者都不能呼叫需要 `youtube`／`youtube.force-ssl` 的 `videos.update` 或 `videos.delete`。使用 native desktop OAuth、PKCE 與 offline refresh token，token 與 resumable session URI 只存 macOS Keychain／加密 private state，不進 Git、環境變數、log、Project Manifest 或 Recovery Vault；開發與正式 OAuth project 分離。Channel Binding Profile 固定唯一 expected channel ID，每次上傳前精確比對，`videos.insert` 明確指定 private 與 `notifySubscribers=false`，回應後再核對 channel ID／visibility；不符、撤銷或重新驗證需求是共享 blocker，禁止 browser fallback。一般 API 沒有可把 `videos.insert` 直接鎖定任意 channel ID 的參數，Brand Account default 只能作輔助而不能代替這些 fail-closed checks。Visibility Promotion 與核准的 Remote Cleanup Plan 改由不常駐、與 worker 隔離的 Privileged YouTube Executor 使用獨立 `youtube.force-ssl` credential，且只能執行核准 artifact 列出的精確動作；因未通過 YouTube API audit 的新 project 上傳會被限制為 private，這個 privileged path 在完成適用 compliance audit 與獨立驗收前不得啟用。
