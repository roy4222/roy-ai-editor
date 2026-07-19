---
status: accepted
---

# Start retention from a project state event

Production Assets 的自動回收期限從 Project Manifest 記錄的 `retention_eligible_at` 開始，不使用檔案 mtime、atime 或目錄掃描時間。只有本機 Automated Quality Verdict 為 PASS、private Publish Job 已完成、Publish Verification 證明遠端影片可播放且沒有 blocking restriction，並且沒有未解決 Exception Review 時，Media Project 才取得 Retention Eligibility；可播放且只影響追蹤／營利的 Content ID WARN 不阻止資格。歌詞／翻譯／切點／字幕變更、重新渲染或上傳、本機 QA 轉為 WARN／FAIL、Publish Verification 轉為 FAIL、Roy 要求修改或設定保留，以及遠端影片失效，都會暫停或重新建立期限。讀取檔案、播放、探測 metadata 或背景掃描不延長期限，避免自動工作讓大型媒體永遠無法回收。
