---
status: accepted
---

# Reconcile resumable YouTube uploads before retrying

每個 private upload 在任何 network side effect 前先 fsync 一個 immutable Publish Intent；`publish_key = SHA-256(channel_binding_version || track_revision_id || verified_render_hash || channel_publish_profile_version || "private")`。每次嘗試建立獨立 Publish Attempt。worker 先提交 resumable-session initialization，收到 `Location` 後立即把完整 session URI 寫入 macOS Keychain 或同等加密 private state，再把 opaque Keychain reference 與 URI hash 原子寫入 Project Manifest；只有 reference 已 durable 後才能送第一個 media byte。session URI 與 OAuth token 都不得進 log、manifest、Recovery Vault 或 review artifact。

初始化 metadata 在 private description 內包含不面向觀眾的唯一 `roy-publish-key:<publish_key>` reconciliation marker，並限制為 private／`notifySubscribers=false`；marker 只有在另行核准 Visibility Promotion 時才由 Privileged YouTube Executor 與正式 metadata 一起移除。任一 interruption／5xx／worker crash 後，worker 先用 stored session URI 送空 PUT 查詢 upload status：`308` 依 server `Range` 續傳；terminal success 採用同一 video ID；terminal non-creation 才進下一步。response 遺失、session `404`／過期或本機已無 terminal response 時，readonly path 先用 `channels.list(mine=true)` 取得同一 channel 的 uploads playlist，再以 `playlistItems.list`／`videos.list` 枚舉有界時間窗內該 channel 自己可見的 recent uploads，最後以 exact marker、channel ID、預期 duration、render-derived metadata 與 creation time 對帳；不得依賴公開搜尋索引或 title-only matching。

對帳結果恰有一支時原子保存 video ID 並採用；多支或證據矛盾時建立 shared blocker，不能挑最新、重傳或自動刪除；零支時只有 session terminal failure／expiry 加上 API scan 均證明沒有已建立遠端影片，才可建立新的 Publish Attempt／resumable session。取得 `201` response 後，video ID 必須在 thumbnail、verification 或通知前 durable。所有 retry 都在同一 Publish Intent 下進行，且新的 `videos.insert` 必須有前一 attempt 的 Orphan Upload Reconciliation PASS。官方 resumable protocol 明定 session URI 必須保存、interruption 後應查 status，且完成後重查會回傳同一 completion response；本協議把這些步驟提升為 crash-safe idempotency gate。參考：<https://developers.google.com/youtube/v3/guides/using_resumable_upload_protocol>。
