---
status: accepted
---

# Maintain upstream Git lineage

Roy AI Editor 保留自己的 `origin`，同時以 `Hao0321/video-autopilot-kit` 作為 `upstream` remote，讓 Roy 的提交建立在 upstream Git 歷史之上。上游更新先 fetch 並檢視差異，再於獨立同步分支整合、測試，最後合回 Roy 的主分支與推送 origin；不在含有未確認客製修改的主分支上直接執行盲目 pull。這保留持續吸收 upstream 修正與功能的能力，也讓衝突、授權聲明和 Roy Customization 的相容性可以在進入主線前被審查。首次連接兩套既有歷史的方式由 [ADR 0007](./0007-reconcile-histories-without-rewriting-main.md) 決定。
