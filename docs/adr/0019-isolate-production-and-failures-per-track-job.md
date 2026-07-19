---
status: accepted
---

# Isolate production and failures per Track Job

同一場 Concert Lyrics Review 通過後，每首已核准歌曲以獨立 Track Job 執行切段、對軸、渲染、QA 與 private Publish Job；Resource-Aware Scheduler 依 benchmarked resource profile 讓場內 jobs 平行，但不允許另一個 Media Project 同時佔用 heavy media slot。單一歌曲的失敗只暫停該 job 並累積到 Exception Digest；其他 jobs 繼續執行並可先交付通過門檻的 YouTube 連結。等所有仍可自動前進的工作完成後，系統把各歌曲問題、證據、建議答案與影響範圍一次呈現，Roy 一次回覆後只恢復受影響 jobs；只有瀏覽器／YouTube 重新驗證、共享憑證失效或 Storage Preflight 等阻塞整場的問題立即通知。整場報告只聚合已完成連結與 digest，不以 all-or-nothing 狀態浪費已完成工作，也不反向接管各 Track Job 的真實狀態。
