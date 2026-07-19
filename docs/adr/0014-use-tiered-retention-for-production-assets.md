---
status: accepted
---

# Use tiered retention for Production Assets

RoyMedia 採用 manifest-driven 的三層 Retention Class。可重新產生的 cache、proxy、抽幀、暫存音訊、下載碎片與失敗 render，在所屬階段成功後保留 7 天；可重新下載的來源影片、分離音軌／stems、歌曲 clips、review renders、舊版成片，以及已完成並驗證 private Publish Job 的本機 Verified Render／Approved Deliverable，自 Retention Eligibility 起保留 30 天。`project.json`、來源 URL／metadata／hash、歌詞／翻譯／credits／reuse terms、timing、字幕、approvals、QA、Evidence Artifacts、Render Manifest、Publish Job、YouTube ID、Roy Translation／Editing Notebooks、Preference Rules 與回收紀錄長期保留；Roy 直接提供且無法重新取得的唯一原始素材也不得自動刪除，除非已有獨立備份或 Roy 明確改變其 Retention Class。Concert Golden Corpus 的私人真實短片在 RoyMedia `shared` 中最多占 5 GiB，具有長期 Retention Hold，不受一般 30 天回收；其 annotations、來源 URL 與 hashes 進 Recovery Vault，真實片段不進公開 Git。模型與其他共用素材使用獨立 shared-cache 容量政策，Retention Hold 可以暫停特定專案或資產的回收。
