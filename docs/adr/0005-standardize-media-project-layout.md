---
status: accepted
---

# Standardize the Media Project layout

每個 Media Project 採用相同的 type-oriented 目錄契約：根目錄保存 `project.json`；`videos/` 固定分為 `source/`、`clips/`、`review/`、`approved/`、`archive/`；`lyrics/` 分為 `sources/`、`approved/`；`timing/` 分為 `alignment/`、`approved/`；`subtitles/` 分為 `draft/`、`approved/`、`archive/`；另以 `approvals/`、`qa/`、`publish/` 與 `work/` 分別保存核准、品質證據、發布資產與可重建中間產物。所有歌曲產物使用穩定的 `<track-number>-<slug>` 識別，Project Manifest 明確指向目前 Approved Deliverable；檔名中的 `final`、`v2` 或資料夾批次名稱不再代表狀態，可重用程式碼也不得留在 `work/`。
