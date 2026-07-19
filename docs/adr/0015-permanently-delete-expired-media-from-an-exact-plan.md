---
status: accepted
---

# Permanently delete expired media from an exact Retention Plan

到期媒體不移入仍占用 RoyMedia 空間的 macOS Trash；系統在到期前三天建立不可覆寫的 Retention Plan，並在到期時重新驗證每個 manifest 列出的精確檔案。只有 resolved path 位於 `/Volumes/RoyMedia/RoyAIEditor`、不是 symlink、沒有執行中 job／Exception Review／Retention Hold、private 遠端影片仍可播放、Publish Job 與檔案 hash 未改變，且 Recovery Vault 已成功保存並驗證該專案最新長期資料 snapshot 時，才逐檔永久刪除；禁止 wildcard、依副檔名推測或遞迴刪除整個專案目錄。完成後保存 Retention Tombstone，記錄原路徑、hash、時間、釋放空間、來源可否重取、Recovery snapshot ID 與對應計畫；任一檢查失敗即 fail closed、不刪除並觸發 Exception Review。
