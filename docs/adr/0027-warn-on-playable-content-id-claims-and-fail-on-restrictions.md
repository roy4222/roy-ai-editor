---
status: accepted
---

# Warn on playable Content ID claims and fail on restrictions

每個 private Publish Job 完成上傳後必須執行 Publish Verification：YouTube API 等待處理完成並檢查可見性、播放與地區限制，ADR 0045 的隔離 `roy-studio-verify` profile 在 default-deny Browser Read-Only Enforcement Profile 下補查一般 Data API 未完整提供的 copyright restrictions；角色必須是 registry fixture 證明可讀該欄位的最低權限。沒有平台限制為 PASS；有 Content ID claim 但 private 影片實際可播放，且影響只限追蹤或營利時記為 WARN，仍交付連結並可取得 Retention Eligibility；封鎖、靜音、下架、處理失敗或不可播放則為 FAIL 並進入 Exception Digest。Roy AI Editor 不得自動提出申訴、使用 Studio 裁切／靜音／換歌、刪除遠端影片或採取其他會改變內容或法律立場的行動；Visibility Promotion 前必須重新驗證一次。
