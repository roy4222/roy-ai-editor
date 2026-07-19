---
status: accepted
---

# Keep a small private Concert Golden Corpus

Concert Live 的品質驗證使用雙層 Concert Golden Corpus：公開 Repo 只保存合成 Test Fixtures，測試 manifest、state machine、retry、ASS 與 renderer；RoyMedia `shared` 長期保留最多 5 GiB 的私人真實短片與人工 gold annotations，設定 Retention Hold 且不進 Git。私人 corpus 至少涵蓋無字幕、soft／完整／部分／錯字／錯時 burned 日文、聊天室／浮水印、Safe-Area Recovery、單人／多人／合唱、cover／翻譯主軸困難、performed repeats、長音／顫音／ad-lib／觀眾聲／樂團 bleed，以及姓名／熟字訓／当て字／送假名／讀音衝突。工具、模型、External Capability Adapter 或 Concert Subtitle Profile 必須通過整套 corpus 才能升格；annotations、來源 URL、hash 與預期結果備份到 Recovery Vault，真實 clips 本身維持在 5 GiB cap 內，不受一般 30 天 Media Project 回收。
