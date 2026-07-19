---
status: accepted
---

# Promote pinned toolchain releases through a Maintenance Train

Production 不直接使用浮動最新版；程式碼、Brew／Python／browser dependencies、字型、模型、prompts 與 profiles 必須以精確版本／checksum 組成不可變的 Production Toolchain Release。Production Job Request 建立時同時釘選 release 與 Concert V1 Quality Registry version／hash，Render Manifest 記錄其完整證據，執行中禁止 `brew upgrade`、runtime package install、浮動 model tag 或切換 release。Maintenance Train 每週自動偵測 `video-autopilot-kit` upstream、依賴、模型與安全更新，通常每月在獨立 branch 合併成候選；重大安全修補立即建立候選，但仍須通過 CI、完整 Concert Golden Corpus、Dedicated Editor Host media smoke、重啟續跑與 rollback 演練。只有沒有擴大 capability／OAuth scope，且符合 ADR 0047 registry 所列 exact normalized-output equivalence 的維護候選可以自動升格；任何未列入 normalization 的受治理輸出差異，即使仍達品質門檻，也集中成一次 Toolchain Promotion Review，以新舊 A/B、metrics、風險與 rollback 證據等待 Roy 的 `ok`。activation 只在安全 stage boundary 進行，新 jobs 使用新版，已開始的 jobs 繼續其 pinned release；active 與 last-known-good releases 至少保留到所有引用 jobs 完成。Host Health Supervisor 發現 activation 後的 health regression 時，可以把新 jobs 原子回退到 last-known-good，但不得把進行中的 job 中途換 release。無法安全修補的重大漏洞必須停用受影響 capability 並進 shared blocker，不能為趕更新跳過驗證。
