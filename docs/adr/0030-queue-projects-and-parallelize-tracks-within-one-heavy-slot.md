---
status: accepted
---

# Queue projects and parallelize tracks within one heavy slot

Roy 可以連續提交任意數量的 Production Job Requests；Resource-Aware Scheduler 將它們持久化排隊，但在目前 Apple M4／24 GB Dedicated Editor Host 與約 223 GiB RoyMedia 上，同時只允許一個 Media Project 執行大量下載、音軌分離或正式 render。該 project 內的 Track Jobs 依實測 CPU／GPU／RAM resource profile 平行，以使用可用火力但保留 OS 安全餘量；project 等待 Concert Lyrics Review 或其他人工 gate 時釋放 heavy slot，下一個 project 可先做 Timeline Discovery、Rights Audit 與歌詞研究。Storage Preflight 與 25 GB RoyMedia hard floor 優先於併發，scheduler 不得為了多跑工作而提前刪除未到期媒體或建立第二個 Production Data Root；未來硬體升級只調整 resource profile，不改 workflow 語義。
