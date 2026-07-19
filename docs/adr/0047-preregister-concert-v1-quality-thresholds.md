---
status: accepted
---

# Preregister Concert V1 quality thresholds

Concert V1 所有 Production Capability Spike、Production Toolchain Release promotion 與 Production Activation 都必須釘選 `docs/quality/concert-v1-quality-registry.md` 的精確 registry version。registry 在候選結果產生前固定 fixture／annotation 母體、樣本數、metric 計算、hard gates、資源邊界、normalized-output 等價與 degradation；每個 Evidence Artifact、Render Manifest 與 activation report 都記錄 version 與 file hash。沒有釘選 registry、fixture manifest 或 gold annotation version 的測試結果一律不可作為 promotion／acceptance 證據。

門檻可以因更多 evidence 變嚴或修正，但看過 candidate／acceptance 結果後不得覆寫原 registry 來讓既有結果過關。任何放寬、metric 定義改變、fixture 移除或 equivalence normalization 改變，都必須建立新版本、說明理由、保留舊版，並對完整 Concert Golden Corpus 與適用 real-project acceptance set 重跑。零容忍契約——文字／repeat／order 錯誤、錯誤 ruby 自動放行、可聽首尾裁切、blocking burned-pixel／media defect、瀏覽器 mutation、重複 upload、未授權刪除／可見性變更——不得被平均分數抵銷。
