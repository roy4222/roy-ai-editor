---
status: accepted
---

# Supervise host health with stage-specific safe recovery

Dedicated Editor Host 以獨立 launchd Host Health Supervisor 在開機、每六小時與每個 job 開始前執行結構化 health checks，產生不含秘密的 Host Health Snapshot。檢查涵蓋 RoyMedia volume identity／filesystem／capacity、Production Toolchain Release checksum、models／fonts、worker／queue／lease／manifest integrity、Discovery Browser Profile、Keychain credential 與 Channel Binding Profile、網路、YouTube quota 及 Recovery Vault freshness。結果按 capability／stage 標記 PASS、DEGRADED 或 BLOCKED：斷網只等待 discovery／research／publish，OAuth 問題只阻擋 publish，Recovery Vault 失敗只阻擋 deletion／migration，Storage Preflight 失敗只阻擋大型寫入；不以單一全域紅燈浪費仍可安全進行的工作。Supervisor 在版本化 recovery budget 內只能執行 Safe Self-Healing Action：重啟 worker、從 checkpoint 續跑、退避重試、重建可再生 cache、讓新 jobs 回退 last-known-good release，或執行已符合原精確授權的 Retention Plan。它不得格式化磁碟、改 OAuth scope、以瀏覽器補登入／上傳、刪除遠端影片、修改核准文字、改變 retention class 或繞過存取控制。自修成功只保存 evidence；recovery budget 耗盡、需要 Roy 重新驗證或資料完整性有風險時，才經 Review Outbox 產生一個去重 shared blocker。`roy-editor doctor` 必須演進為 supervisor 共用的 read-only、machine-readable checks，而不是把任意 mutating repair 藏在健康檢查內。
