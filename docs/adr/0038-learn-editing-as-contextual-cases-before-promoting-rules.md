---
status: accepted
---

# Learn editing as contextual cases before promoting rules

Roy AI Editor 把每次 Editing Brief、素材特徵、Edit Plan、候選版本、Roy 的保留／刪除／移動／節奏／字幕修正、版本選擇理由與最終結果寫入 Roy Editing Notebook。每筆預設只是帶有 Editing Workflow、頻道、片型、受眾與畫幅語境的 Editing Case，用於 retrieval、候選排序與 regression evaluation；一次核准、沉默或重複行為都不能自動變成永久偏好。只有 Roy 明確表示「以後都這樣」或「永遠不要這樣」才能建立有作用域的 Editing Preference Rule；多個相似 cases 可以讓系統提出升級建議，但不得自行定案或在資料不足時自動 fine-tune。完整案例與受限素材保持私人並進 Recovery Vault 的小型真相範圍，公開 Repo 只保存安全抽象原則、schemas 與合成 examples。
