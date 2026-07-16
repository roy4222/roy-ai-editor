# Upstream foundation integration plan

## Goal

將現有 Roy AI Editor 從「獨立小型 CLI 加被動 vendor snapshot」轉成以 `Hao0321/video-autopilot-kit` 為 Upstream Foundation、可持續同步 upstream、並完整保存 Roy Customization 的公開程式碼專案。

## Safety boundary

- 不 force-push、不改寫或直接在公開 `main` 上整合。
- 不修改、reset 或清理 D 槽 Git working copy。
- 不把 CRLF-only working-tree noise 當成功能修改。
- 不把 Private Configuration、Production Assets 或授權受限內容加入 Git。
- push integration branch 前執行完整 diff、秘密／大型檔案檢查與測試。

## Inputs to preserve

- WSL `main` 的兩個既有 Roy commits 與 `v0.2.0` tag。
- D 槽 branch 的五個 post-v0.2.0 commits：alignment numba、ruby calibration、kanji-only visual QA、Bahamut discovery gate、lyrics approval gate。
- 三個 Legacy Media Projects 中 15 支未版控生產腳本所包含的可重用能力；不得原樣搬入硬編碼專案路徑。
- 本次 grilling 產生的 CONTEXT、ADRs、North Star 修正與 migration plans。

## Integration stages

1. **Create integration branch**：由現有 WSL `main` 建立 `codex/upstream-foundation`，先保存本次架構文件。
2. **Connect upstream**：新增 `upstream` remote、fetch 官方 `main`，在 integration branch 進行保留雙方歷史的 reconciliation merge。
3. **Promote the foundation**：讓 upstream 的 `src/`、`knowledge/`、`templates/`、examples 與 setup surfaces 成為 root foundation；確認 parity 後移除重複的 `vendor/video-autopilot-kit` snapshot，保留必要 MIT attribution。
4. **Recover versioned Roy work**：從 D 槽 Git object 匯入五個功能提交，按新 foundation 結構解決衝突並維持小型、可審查 commits。
5. **Recover unversioned capabilities**：分析 15 支 project-specific scripts，把歌詞核准包解析、forced alignment、bounded repair、timing reconciliation、GDI/libass ruby layout 與 full-width visual QA 抽成參數化 modules、CLI commands 與 regression tests。
6. **Establish customization**：建立可公開的 profiles、workflow configuration 與 Concert Live Workflow；私密值只提供 schema／example 並保持 Git ignored。
7. **Verify**：執行 unit、integration、CLI smoke、upstream examples、golden synthetic fixtures、license attribution、secret scan、large-file scan 與 clean-checkout test。
8. **Publish for review**：檢查 commit scope 後推送 `codex/upstream-foundation`，建立 draft PR；`main` 在 Roy 核准與 checks 通過前保持不變。

## Production-data follow-up

程式碼與遷移工具完成後，才依 [Production data migration plan](./2026-07-16-production-data-migration.md) 對 D 槽三個 Legacy Media Projects 執行 copy、verify、legacy。這兩條工作流不得混成同一個危險操作。
