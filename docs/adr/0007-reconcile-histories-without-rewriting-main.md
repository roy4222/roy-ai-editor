---
status: accepted
---

# Reconcile histories without rewriting main

首次採用 Upstream Foundation 時，Roy AI Editor 在獨立 integration branch 以 reconciliation merge 連接現有 Roy 歷史與 `Hao0321/video-autopilot-kit` 歷史，不 force-push 或改寫公開 `main`。整合分支以 upstream root 作為基礎結構，保留 Roy 現有提交與 tag，移除重複的被動 vendor snapshot，再整併 D 槽五個本機功能提交與回收後的製作能力。只有在完整測試、公開內容檢查與 Roy review 通過後，integration branch 才能經 PR 合回 `main`。
