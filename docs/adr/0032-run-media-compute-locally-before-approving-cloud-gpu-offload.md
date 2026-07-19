---
status: accepted
---

# Run media compute locally before approving cloud GPU offload

V1 對 Qwen3-ASR／ForcedAligner、OCR、音軌分離、FFmpeg／libass render 與其他媒體運算採 Local-First Compute Policy：先在 Apple M4／24 GB Dedicated Editor Host 以 representative Live golden set 驗證品質、runtime、記憶體與模型／cache 空間；只要品質達標且能穩定完成，速度較慢不構成 offload 理由。只有本機品質已通過、卻因記憶體或 runtime 無法可靠運行時，Exception Digest 才提出 External GPU Adapter、最小必要上傳 artifact、provider 資料政策、估計費用與替代方案。任何自動外部 GPU 使用都必須等 Roy 核准版本化 Cloud Compute Profile，包含 provider、retention/deletion、資料最小化、模型版本及單 job／月費用上限；在此之前不得把完整影片、音訊或其他 Production Assets 靜默上傳。
