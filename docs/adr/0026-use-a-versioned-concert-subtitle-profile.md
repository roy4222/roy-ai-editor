---
status: accepted
---

# Use a versioned Concert Subtitle Profile

Concert Live 不依來源影片任意更換字幕風格，而使用版本化的 Concert Subtitle Profile 統一日文、平假名、繁中、卡拉 OK、Singer Color Policy、字體比例、間距、描邊與安全區。HACHI《万華鏡》v3 作為 v1 的約 80/100 基線，不是品質上限；後續改善先以 representative golden fixtures 做 profile 級 A/B 與 burned-pixel 回歸，Roy 接受後才發布新版本。Render Manifest 必須記錄實際 profile 版本，舊成片不因 profile 升級而靜默改變；Source Japanese Subtitle Mode 保留來源日文，只對新增繁中及必要 Safe-Area Recovery 套用相容部分。
