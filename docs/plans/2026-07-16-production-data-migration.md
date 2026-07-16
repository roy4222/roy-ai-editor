# Production data migration plan

## Goal

將 D 槽三個既有 Live 專案整理到標準 Production Data Root 與 Media Project 目錄契約，同時保留可回復的 Legacy Media Projects。遷移不得遺失、覆寫或自動刪除任何既有檔案。

## Legacy sources

- `D:\VideoProjects\HACHI_Birthday_LIVE_2025`
- `D:\VideoProjects\RURI_Birthday_LIVE_2025`
- `D:\VideoProjects\7-F7B0UiZXE`

盤點基線為至少 27 首不同歌曲、33 個位於 final／review／preview 位置的影片版本、32 個 ASS、1 個 SRT，以及 15 支位於專案 `work/` 的未版控製作腳本。這些數字是遷移前的最低證據，不代表所有檔案的最終分類。

## Destination

`D:\VideoProjects\RoyAIEditor\projects\<project-id>\`

每個 destination project 必須遵守 [ADR 0005](../adr/0005-standardize-media-project-layout.md)，並以 [ADR 0004](../adr/0004-use-one-project-manifest-as-current-state.md) 定義的 `project.json` 作為目前狀態的唯一真相。

## Migration stages

1. **Inventory**：為每個 legacy source 建立完整相對路徑、大小、修改時間與 content hash 清單。
2. **Recover reusable code**：將 15 支專案腳本分類；可重用邏輯先移植到 WSL canonical source checkout、參數化並加入測試。D 槽原檔不修改。
3. **Create destinations**：建立三個標準 Media Projects 與初始 Project Manifests。
4. **Copy and classify**：依固定目錄契約複製 Production Assets、Evidence Artifacts、Work Artifacts、Approved Deliverables 與 Archived Revisions。
5. **Reconcile state**：由實際核准紀錄、QA 與交付證據建立或校正 tracks、review gates 與目前 Approved Deliverables；不得從 `final`、`v2` 或資料夾名稱猜測狀態。
6. **Verify**：比對來源與目的地的檔案數量、總大小、逐檔 hash、媒體 probe、字幕可讀性及 Project Manifest 引用完整性。
7. **Legacy gate**：驗證通過後，舊目錄才可標為唯讀 Legacy Media Projects。移動、封存或刪除 legacy sources 需要 Roy 另一次明確核准。

## Safety rules

- 不進行 in-place reorganize。
- 不覆寫同名 destination；衝突必須產生明確 revision 或停止等待處理。
- 不以 deduplication 為由刪除來源或舊版本。
- 不把 Production Assets、授權受限歌詞／翻譯、模型或 cache 加入 Git。
- 任一步驗證失敗時，保留來源與已複製資料，修正分類或工具後續跑。

## Reconciliation profiles

真實專案的曲目與狀態透過 D 槽外部 JSON profile 傳給遷移器，不進公開 Repo：

```console
roy-editor migrate legacy LEGACY_SOURCE STANDARD_DESTINATION \
  --reconciliation RECONCILIATION.json
roy-editor migrate legacy LEGACY_SOURCE STANDARD_DESTINATION \
  --reconciliation RECONCILIATION.json --execute
```

第一個命令只做完整 inventory、hash、route、reference 與 conflict 檢查；人工核對後才可執行第二個命令。Profile schema version 1 包含：

- `project_id`、可選的 `source_url`；
- `routes`：legacy source prefix 到標準 destination prefix 的決定性映射；
- `project_assets` 與 `tracks[].legacy_assets`：目的地相對路徑引用；
- 四個 `review_gates` 與 `gate_evidence`；任何 `approved` gate 都必須引用本次 plan 實際包含的 evidence；
- 可選的 `rights`、`unresolved_conflicts` 與 `migration_notes`。

遷移器會把每個 asset reference 補上 size 與 SHA-256，並拒絕 path traversal、重複 track ID、重複 destination、缺失 evidence、不同來源續跑與不同 profile 覆蓋。Legacy profile 不能直接宣告 Approved Deliverables；這仍須走獨立的 Roy 明確核准流程。
