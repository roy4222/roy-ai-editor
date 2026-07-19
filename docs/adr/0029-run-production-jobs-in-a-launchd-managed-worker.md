---
status: accepted
---

# Run production jobs in a launchd-managed worker

Codex 是 Roy AI Editor 的 Control Surface，不承擔長時間媒體 process 的生命週期。Roy 提交 URL 時先建立不可覆寫的 Production Job Request 與 Media Project；Dedicated Editor Host 上由 macOS launchd 管理的 Production Worker 取得 job lease，執行可重試且 idempotent 的 stages，並把 checkpoint、artifact hashes、retry evidence 與等待中的 gate 寫入唯一 Project Manifest。獨立 launchd Host Health Supervisor 在開機、每六小時與 job 開始前驗證 stage-specific readiness，並可在 recovery budget 內重啟 worker／續跑 checkpoint；supervisor 自己不得持有 job lease 或改寫核准狀態。關閉 Codex、登出或重啟 Mac 後，worker 必須從最後成功 checkpoint 續跑，不得重複下載、重做已核准工作或建立第二個 YouTube upload；review／blocker／result 寫入 Review Outbox，由 Codex monitor 去重後送回原 task，Codex 只呈現 Concert Lyrics Review、Exception Digest、Visibility Promotion 與 private links。
