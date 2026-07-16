---
status: accepted
---

# Separate source code from production assets

Roy AI Editor 的 canonical source checkout 位於 WSL，保存程式碼、Skills、profiles、文件、schemas、測試與小型合成 Test Fixtures；D 槽保存真實 Media Projects、Production Assets、中間產物、QA 證據、模型、cache、renders 與交付影片。唯一 Production Data Root 為 `D:\VideoProjects\RoyAIEditor\`，其下以 `projects\` 保存各 Media Project、`shared\` 保存共用大型資產、`cache\` 保存可重建資料。D 槽不再作為另一個可修改的程式碼工作副本。這讓所有可重用行為都能被 Git 追蹤，同時避免大型、私人或有授權限制的製作資料進入程式碼 Repo，並防止程式預設路徑與實際專案位置再次分叉。
