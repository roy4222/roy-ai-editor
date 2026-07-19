---
status: accepted
---

# Back up irreplaceable project truth to an internal Recovery Vault

Dedicated Editor Host 在內接碟維護最多 10 GiB、加密且 hash-verified 的 Recovery Vault，金鑰由 macOS Keychain 管理。它每日增量保存 Project Manifest、核准、來源／權利／翻譯 provenance、Roy Translation／Editing Notebooks、Translation／Editing Preference Rules、timing、字幕、QA、Publish Job／YouTube ID、profile 版本與 Retention Tombstone，並在永久刪除、資料遷移或 profile 升級前建立額外 snapshot；來源影片、stems、renders、模型與 cache 不進 vault。Recovery Vault 是 restore-only 災難復原副本，不是第二個 Production Data Root，正常 workflow 不得從中讀寫目前狀態；恢復必須明確啟動並驗證 snapshot。備份失敗不阻止一般剪輯，但必須 fail closed 阻止永久刪除與資料遷移，避免外接碟故障讓不可替代的專案真相與學習紀錄一起消失。
