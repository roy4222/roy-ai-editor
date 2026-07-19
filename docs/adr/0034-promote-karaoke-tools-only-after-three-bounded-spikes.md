---
status: accepted
---

# Promote karaoke tools only after three bounded spikes

V1 不整套 fork 或採用任何外部卡拉 OK application，而依序執行三個 Production Capability Spikes。A：FFmpeg／ffprobe＋pysubs2 處理軟字幕、VSE／PaddleOCR 只產生 burned-in 候選，必須讓無字幕、完整日文、部分日文、雙語與浮水印／聊天室 fixtures 全部分流正確，OCR 不得成為 Workflow Text Authority；部分來源字幕依 ADR 0044 產生 track-wide fallback。B：Qwen3-ASR／ForcedAligner 對比 WhisperX 與 frozen stable-ts baseline，並比較 raw mix／audio-separator stem，不得改寫或跨越核准文字。C：pysubs2 semantic round-trip 保留 ASS styles、event order、Unicode、unknown tags 與 `\kf`，Sudachi＋fugashi 提供讀音交叉證據，最後由同一 FFmpeg＋libass environment 做 burned-pixel regression。三個 spike 的 fixture 母體、timing／coverage／ruby／pixel／resource／failure-degradation 門檻只以 ADR 0047 的 Concert V1 Quality Registry 為準，且在 candidate results 前釘選。通過者才以 External Capability Adapter 或 pinned core library 升格；Aegisub／Subtitle Edit 只供人工例外，karaoke-gen／Karaoke Mugen／Vilm／BaoCut 等只借鑑 architecture、metadata、review 或 UX，不接管 Roy workflow。
