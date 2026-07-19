---
status: superseded
supersedes: 0020-reuse-only-complete-source-japanese-subtitles.md
superseded_by: 0044-handle-incomplete-source-japanese-with-a-track-wide-fallback.md
---

# Reuse complete source Japanese with safe-area recovery

Concert Live 在 Source Subtitle Audit 證明日文字幕覆蓋 100% performed lines、與核准 Lyrics Packet 的文字／順序／時間一致時，進入 Source Japanese Subtitle Mode：沿用來源日文並只新增其下方繁中。若原畫面下方空間不足，系統先自動執行 Safe-Area Recovery，在維持原輸出解析度與長寬比下等比例縮小並靠上放置來源畫面、建立底部字幕帶；來源日文仍清晰、繁中不裁切且重要構圖未受損時即可繼續。任一缺行、錯字、時間不符，或 Safe-Area Recovery 未通過 QA，才將該 Track Job 送進 Exception Review；不得逐行混搭、重複燒錄日文、把繁中改放到日文上方，或用底條遮住來源字幕。
