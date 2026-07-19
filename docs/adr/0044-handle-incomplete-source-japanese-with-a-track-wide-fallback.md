---
status: accepted
supersedes: 0024-reuse-complete-source-japanese-with-safe-area-recovery.md
---

# Handle incomplete source Japanese with a track-wide fallback

Source Japanese Subtitle Mode 仍只接受 100% performed-line coverage、文字／順序／repeat／timing 與核准 Lyrics Packet 一致的來源日文；Safe-Area Recovery 只解決完整來源字幕的版面空間，不解決缺行或錯字。未達 100% 時必須先建立版本化 Source Subtitle Fallback Plan，且整首 Track Job 只能走一條路：不完整 soft subtitle track 必須停用，然後全曲使用 Normal Bilingual Subtitle Mode；不完整、錯誤或錯時的 burned-in 日文只有在固定 caption region 可被全曲 Caption Region Replacement 完整中和、重要構圖不受損，且每個 performed line 都由核准 Lyrics Packet／Ruby Map／繁中重新渲染時，才可自動走 Normal Bilingual Subtitle Mode。QA 必須逐行證明舊字幕不再可讀、新字幕完整、無重疊且無重要構圖損害。

若 burned caption region 會移動、與人物／重要資訊重疊，或 replacement 不能穩定消除舊字，該 Track Job 進入 Exception Review；提供「跳過此曲」與「Roy 核准此精確 render／source hashes 的版本限定例外」兩個選項及證據。流程不得把 98% 視為完整、只補缺行、逐行混用來源與新日文，或以 Safe-Area Recovery／content-aware patch 假裝問題不存在。這使部分來源字幕有合法且 fail-closed 的出路，同時保留 100% 的 Source Japanese Subtitle Mode 門檻。
