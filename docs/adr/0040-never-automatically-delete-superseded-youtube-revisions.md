---
status: accepted
---

# Never automatically delete superseded YouTube revisions

YouTube 不支援以新媒體覆寫既有影片；每個 Revision Request 通過本機 QA 後都建立新的 idempotent private Publish Job 與 video ID，重試同一 job 不得重複上傳。舊 Approved Deliverable 在 Roy 選定新版前仍是目前交付版本；新版在 Delivery Review 被選定後，舊片才標記為 Superseded Remote Revision、保持 private、保留完整 revision／render／Publish Job lineage，並從 active Delivery Review 隱藏。Production Publisher Credential 沒有刪除 scope；workflow 永不自動刪除遠端影片，也不使用 Studio 裁切、靜音或替換來重用舊 URL。需要清理時，系統只能產生不可覆寫的 Remote Cleanup Plan，逐筆列出 channel ID、video ID、Project／Track／render hash、可見性、取代它且仍可播放的 Approved Deliverable 與最新 Publish Verification；只有 Roy 對該批精確清單明確核准後，隔離的 Privileged YouTube Executor 才可永久刪除，新增、替換或狀態改變任何項目都使原核准失效。
