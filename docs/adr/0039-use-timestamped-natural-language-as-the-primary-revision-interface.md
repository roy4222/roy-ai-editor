---
status: accepted
---

# Use timestamped natural language as the primary revision interface

V1 不要求 Roy 進入 timeline GUI；Delivery Review 後的主要修改介面是 Codex Control Surface 中的歌曲 ID／歌名、時間點、自然語言與可選截圖。系統把回覆綁定原 private video ID 與 render hash，自動擷取時間點前後的畫面、音訊、字幕與 QA evidence，正規化成 Revision Request；能明確解讀的切點、節奏、位置、顏色或 timing 修改直接只重跑受影響 stages，若輸入本身歧義才進 Exception Digest。日文、繁中、斷行、performed repeats、Song Interpretation Brief 或 Ruby Map 等 Workflow Text Authority 變更仍須重審該 Lyrics Packet，不影響其他歌曲。新版本必須重新完成相關 QA、建立新的 private Publish Job／video ID、完成 Publish Verification 與 Delivery Review；新版本被選為 Approved Deliverable 後，前一個遠端版本依 ADR 0040 成為保持 private 的 Superseded Remote Revision，而不是被覆寫或自動刪除。未來可增加 review timeline UI 提供精細拖曳，但它不得成為 Headless Production Core 或 Production Golden Path 的必要條件。
