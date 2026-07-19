---
status: accepted
---

# Maintain upstream Git lineage

Roy AI Editor 保留自己的 `origin`，同時以 `Hao0321/video-autopilot-kit` 作為 `upstream` remote，讓 Roy 的提交建立在 upstream Git 歷史之上。Maintenance Train 每週發現 upstream 變動，但只在獨立同步分支 fetch、檢視差異、整合與測試；合併後仍須依 ADR 0042 形成候選 Production Toolchain Release，不能直接改變 production。不得在含有未確認客製修改的主分支上執行盲目 pull。這保留持續吸收 upstream 修正與功能的能力，也讓衝突、授權聲明、Roy Customization 相容性與輸出差異在進入主線前被審查。首次連接兩套既有歷史的方式由 [ADR 0007](./0007-reconcile-histories-without-rewriting-main.md) 決定。
