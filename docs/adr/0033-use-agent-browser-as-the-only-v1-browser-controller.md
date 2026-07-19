---
status: accepted
---

# Use agent-browser as the only V1 browser controller

V1 Production Toolchain 只維護 `agent-browser` 作為 Timeline Discovery、歌詞研究、動態頁讀取、截圖與 provenance capture 的 browser controller，並由 Roy AI Editor 自己把結果轉成 Evidence Artifact。所有 production runs 必須套用 ADR 0045 的 Browser Read-Only Enforcement Profile，不能只靠 prompt 宣告唯讀。以 Concert V1 Quality Registry 的固定 YouTube／Bahamut fixtures 衡量公開頁 capture、provenance、零結果留證、prompt-injection containment、重跑一致性與 mutation prevention；只有 registry 的 capture threshold 未通過，且失敗主因確定是 locator 或 browser engine 時，才用同一組 fixtures benchmark `playwright-cli` 作 replacement candidate。`actionbook`、`browser-use` 與 Agent-Reach 暫不安裝：分別等待介面穩定／目標站 manual coverage、真正需要嵌入式 autonomous browser runtime、或確定要擴張到 Twitter／Reddit／Bilibili 等跨社群研究。不得為了「多一套比較安心」同時維護重複 profiles、cookies、selectors 與 browser downloads。
