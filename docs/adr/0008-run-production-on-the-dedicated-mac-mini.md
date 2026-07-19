---
status: accepted
supersedes: 0003-separate-source-code-from-production-assets.md
---

# Run production on the dedicated Mac mini

Roy AI Editor 的 canonical source checkout 與自動化執行環境移至專用 Apple Silicon
Mac mini。真實 Media Projects、Production Assets、中間產物、QA 證據、模型、cache、
renders 與交付影片集中保存於外接 APFS SSD；唯一 Production Data Root 為
`/Volumes/RoyMedia/RoyAIEditor/`，其下以 `projects/` 保存各 Media Project、`shared/`
保存共用大型資產、`cache/` 保存可重建資料。程式碼、Skills、profiles、文件、schemas、
測試與小型合成 Test Fixtures 留在 canonical source checkout，Production Assets 不進 Git。

macOS 的預設 Media Project workspace 為
`/Volumes/RoyMedia/RoyAIEditor/projects`，且仍可用 `ROY_EDITOR_WORKSPACE` 明確覆寫。
流程不得在 RoyMedia 未掛載時靜默改存內接碟或建立另一個 Production Data Root；應停止並
回報儲存空間未就緒。這項決策取代 ADR 0003 的 WSL／D 槽實體位置，但保留程式碼與
Production Assets 分離的架構邊界。內接碟可以依 ADR 0028 保存受限容量、加密且只供災難
復原的 Recovery Vault；它不得成為可切換的工作資料根或媒體落地備援。ADR 0043 的
Host Health Supervisor 必須以 volume identity 與 filesystem／capacity evidence 驗證 RoyMedia，
不能只因同名路徑存在就判定 Dedicated Editor Host 已可生產。
