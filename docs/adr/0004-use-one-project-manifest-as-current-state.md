---
status: accepted
---

# Use one Project Manifest as current state

每個 Media Project 以根目錄的 `project.json` 作為目前狀態的唯一真相，集中記錄曲目、處理階段、review gates 與 Evidence Artifact 引用。Alignment、render、QA、delivery 與 approval 報告保留為不可覆寫的證據，但不得各自維護互相矛盾的目前狀態；每個成功的 workflow stage 必須以同一次受控更新把新 evidence 連回 Project Manifest。既有 HACHI、RURI 與獅子神專案在整合時都要建立或校正 Project Manifest，不以檔名中的 `final`、`v2` 或資料夾位置猜測完成狀態。
