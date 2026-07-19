---
status: accepted
---

# Upload private before Visibility Promotion

Concert Live Production Golden Path 對 Automated Quality Verdict 全部 PASS 的 Verified Render 自動建立 private YouTube 影片，不要求另一個固定人工成片、metadata 或縮圖核准；Channel Publish Profile 自動產生足以辨識與平台檢查的 provisional 標題、說明、來源、credits、hashtags 與縮圖。Production Worker 只使用 ADR 0041 的 Production Publisher Credential，依 Channel Binding Profile 前後核對預期 channel ID、固定 private 與 `notifySubscribers=false`；它沒有更新可見性或刪除影片的 scope。流程依 ADR 0046 在任何 network side effect 前保存 Publish Intent，持久化 resumable session，並在任何新 `videos.insert` 前完成 Orphan Upload Reconciliation；等待平台處理與 Publish Verification 完成後，以一次 Delivery Review 集中顯示 private links、verdicts、metadata／thumbnail previews 與 QA 摘要。當完整 Delivery Review 是唯一待處理 review 時，緊接的 `ok` 綁定可見 render hashes／video IDs 並選為 Approved Deliverables；指定歌曲／時間點則建立 Revision Request，只重開受影響 Track Job。修訂版必須建立新的 private video ID；新版被選定後，舊版成為 Superseded Remote Revision，保持 private 且不得自動刪除，只能依 ADR 0040 的精確 Remote Cleanup Plan 另行處理。Approved Deliverable 與 provisional metadata 都不構成 Visibility Promotion；unlisted 與 public 必須由 Roy 另行明確指示、核准當下正式標題／說明／縮圖／可見性，並由完成 compliance audit 的隔離 Privileged YouTube Executor 執行。
