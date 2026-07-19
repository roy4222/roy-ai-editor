---
status: accepted
---

# Use tiered timing fidelity for karaoke subtitles

Concert Live Workflow 把通過 QA 的逐行起訖時間視為正式產出必達門檻，逐字／逐 mora 動態上色則是只在細粒度對軸證據與 burned-pixel QA 通過時啟用的增強。Alignment Adapter 產生 timing Evidence Artifact，由 Automated Quality Verdict 自動選擇最高通過的 Timing Fidelity Tier，不設固定 `approve-timing` 人工關卡。細粒度信心不足時，該產出可記錄原因後降級為整行字幕，不以平均分配或推測時間假裝精準，也不因此詢問 Roy 或停住其他已通過品質門檻的歌曲。一首歌只使用一種主要 Timing Fidelity Tier，以免普通演唱句在動態與靜態模式間跳轉；口白、喊聲與非正式歌詞 ad-lib 可作單句靜態例外。逐行邊界錯誤、切掉首字、遺漏 performed repeat、過早結束長尾音、改寫 Workflow Text Authority 或跨越行序仍是正式 QA 失敗，必須進入 Exception Review，不得用整行 fallback 遮蔽。
