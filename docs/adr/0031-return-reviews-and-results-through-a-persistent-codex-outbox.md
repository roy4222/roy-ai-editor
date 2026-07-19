---
status: accepted
---

# Return reviews and results through a persistent Codex outbox

V1 的所有 Concert Lyrics Review、共享 blocker、Exception Digest 與 private links ready 都由 Production Worker 或 Host Health Supervisor 寫入持久化 Review Outbox；Codex monitor 依 event ID 與 Project Manifest cursor 去重，送回建立該 Production Job Request 的同一個 Codex task。Host Health Supervisor 的短暫 DEGRADED 狀態在 Safe Self-Healing Action 成功後只留 Host Health Snapshot，不通知 Roy；只有 recovery budget 耗盡、需要重新登入、資料完整性風險或會阻塞所有相關 stages 的狀態才建立 shared blocker。macOS Notification Center 可以同步顯示不含完整歌詞、credentials 或其他敏感內容的短通知，但回覆與核准仍只在原 task 處理；Codex 關閉時 outbox 事件不得遺失，重送也不得重複核准、恢復 job 或建立 Publish Job。Email、Slack、Telegram 等外部 Notification Adapter 不是 V1 Production Toolchain 的必要依賴，只有未來有明確需求時才透過可替換 adapter 加入。
