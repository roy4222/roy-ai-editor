---
status: accepted
---

# Fail Storage Preflight before shortening retention

每個大型下載、分析與 render 工作在開始前執行 Storage Preflight，依來源與輸出估算預留工作空間，且 RoyMedia 至少維持 25GB hard floor；Host Health Supervisor 另在開機與週期檢查 volume identity／容量，但不能用較舊 snapshot 取代當下 preflight。Resource-Aware Scheduler 同時只允許一個 Media Project 取得大量下載、音軌分離或正式 render 的 heavy slot；排隊數量與場內 Track Job 平行度不得繞過容量閘門。容量不足時可以提早淘汰已完成階段、可重建且沒有執行中 job 引用的 cache，並照既有 Retention Plan 回收已正式到期媒體；不得提前刪除尚未滿 30 天的來源或 Approved Deliverable，也不得靜默改存 Mac 內接碟。清除可重建 cache 後仍不足時，只把新下載／render 標記為 BLOCKED，已安全落盤且不再大量寫入的研究／review stages 可以繼續；shared blocker 經 Review Outbox 通知，避免中途磁碟寫滿或產生第二個 Production Data Root。
