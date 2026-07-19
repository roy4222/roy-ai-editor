# Concert V1 Quality Registry

- Registry ID: `concert-v1-quality@1.0.0`
- Status: preregistered architecture baseline
- Applies to: Production Capability Spikes, Production Toolchain Release promotion, Concert V1 Acceptance
- Change control: ADR 0047

本檔是量化 gate 的唯一登錄處。執行前必須把本檔 SHA-256、fixture manifest hash、gold annotation version 與 toolchain release ID 寫入 run manifest。以下分母只計 fixture manifest 在 run 開始前列出的 eligible cases；排除項目必須有預先列出的 reason code，執行後不得移除失敗 case。

## 1. Universal hard gates

- Workflow Text Authority 的日文、繁中、stable line IDs、performed repeats 與 display order：100% 相符，0 遺漏、0 新增、0 偷改。
- 錯誤 Ruby Map 自動放行、錯誤 kanji base span、可聽首音／尾音裁切、blocking subtitle clipping／overlap／殘留舊字幕、accepted media corruption：全部 0。
- Browser mutation／download／secret disclosure、duplicate remote video、自動 remote deletion、未核准 visibility／scope change、Retention Plan 外刪除：全部 0。
- 任一 hard gate FAIL 不得由平均值、人工挑樣或較高 tier 成績抵銷。

## 2. Fixture manifests

### Browser capture set

- 至少 40 個 versioned cases：YouTube chapters／description／creator comment／pinned comment／一般可信留言、需要 expand／scroll、登入與匿名頁、Bahamut 搜尋／文章／零結果、redirect／prompt-injection／mutation trap。
- creator／pinned provenance、zero-result evidence、prompt-injection containment 與 mutation-prevention cases 的成功率必須 100%。
- 全部 eligible cases 的完整 evidence capture success 必須至少 95%；success 同時需要 URL、author／translator、text、capture time、screenshot hash 與 Browser Action Ledger policy PASS。
- 低於 95% 只能依 ADR 0033 觸發同 fixtures 的 Playwright CLI replacement benchmark，不能用第二套工具補失敗後合併分數。

### Source-subtitle set

- 至少 12 個 versioned track fixtures，涵蓋無字幕、完整／98% soft Japanese、完整／98% burned Japanese、錯字、錯時、repeat 缺失、雙語、聊天室／MC／title-card 干擾、Safe-Area Recovery 可行／不可行、Caption Region Replacement 可行／不可行。
- Source Japanese Subtitle Mode 需要 100% performed-line mapping、0 missing／extra／mismatch／repeat-order conflict；標點只允許 fixture manifest 預先宣告的 Unicode／全半形 normalization。
- partial soft fixture 必須停用來源 track 並全曲走 Normal Bilingual Subtitle Mode；partial burned fixture 必須全曲 Caption Region Replacement PASS，否則必須產生版本限定 Exception Review。0 逐行混搭、0 可讀舊字殘留、0 duplicate Japanese。

### Alignment set

- 至少 8 clips、120 lyric lines、40 difficult lines；difficult 類別至少含 melisma、長音、休止、觀眾聲、重複副歌、多人 overlap、低音量開頭與完整尾奏。
- line start／end 的 absolute boundary error 合併計算：median ≤250 ms、P95 ≤600 ms、max ≤1,000 ms；每個 line 仍須 0 crossed order、0 missing repeat、0 audible first／last syllable clipping。
- fine token／mora tier 至少 500 eligible units：timed coverage ≥98%、median absolute error ≤150 ms、P95 ≤350 ms、時間單調且不能越過其 line boundary。未過 fine tier 但 line tier PASS 時，整首明確降級為 whole-line display；line tier 未過不得降級放行。

### Ruby and burned-pixel set

- Ruby gold 至少 100 kanji spans，其中至少 20 個姓名、熟字訓、当て字、送假名或多讀音 ambiguity cases；錯誤自動放行為 0，所有未滿 Ruby Evidence Policy 的 ambiguity routing 為 100%。
- Burned-pixel corpus 至少 300 subtitle events；每 event 都要有 original-resolution full-width crop 與 gold expectations。所有 seeded blocking defects 必須被攔截，blocking false negative = 0；non-blocking false-positive rate ≤5%。
- 每支 output 必須完整 decode，0 black／frozen segment、0 unexpected mute、0 A/V stream loss、0 duration truncation；Computer Use 第二次 read-only visual pass 必須有 per-line evidence cursor，不得以抽樣代替。
- Singer Color fixtures 至少 12 cases，涵蓋 solo、verified member color、duet、chorus、overlap、unknown singer neutral fallback、低對比官方色調整與 Source Japanese Subtitle Mode。0 unsupported identity guess、0 unreadable foreground/background pairing、100% same-singer stable assignment；任何色彩判斷不得改變 Workflow Text Authority。
- Computer Use 對任一 line 回報 FAIL／ambiguous，或工具無法完成必要的第二次 pass 時，不得建立 Verified Render：保留 exact crop／render hashes 並送該 Track Job 進 Exception Review。只有重跑同一 pinned evidence 得到 PASS，或 Roy 核准綁定 exact hashes 的版本例外後，才能繼續；不得把 unavailable 當 PASS。

## 3. Browser and Studio isolation gates

- `roy-concert-discovery` 與 `roy-studio-verify` 的 profile directories、auth records、policy IDs 與 allowed paths 必須不同；兩者都不得引用 Production Publisher Credential 或 Roy 日常 browser profile。
- 每個 run 必須證明 content boundaries、output limit、domain/path allowlist 與 static action policy 均啟用。任何 default-allow、generic eval、type／submit、download、upload、social interaction 或 Studio edit capability 都是 FAIL。
- Studio role fixture 必須記錄實際 channel permission 與 restriction visibility；最小可行 viewer role 優先。權限不足是 shared blocker，不得自動提升角色或借用 owner daily session。

## 4. Publish idempotency and fault injection

- 至少 50 個 versioned fault-injection boundaries，涵蓋 intent fsync 前後、session initialization response 前後、session reference fsync 前後、每個 chunk、completion response 遺失、video-ID fsync 前後、worker kill、reboot、5xx、quota、session expiry、readonly scan zero／one／multiple matches。
- 結果必須是 0 duplicate remote videos、100% unique orphan adoption、100% ambiguous fail-closed、0 automatic orphan deletion；任何新的 `videos.insert` 都有前一 Publish Attempt 的 reconciliation PASS evidence。
- manifest/log/review/recovery snapshot 中出現 plaintext session URI、OAuth token 或 cookie 為 FAIL。

## 5. Resource and operational feasibility

- 基準 host 是 ADR 0008 的 24 GiB Apple Silicon Mac mini。每個 heavy stage 必須保留至少 6 GiB unified-memory headroom：process RSS 加可歸因 accelerator allocation 的量測峰值 ≤18 GiB；macOS memory pressure 不得進入 critical/red，單 stage swap used 增量 ≤4 GiB。
- RoyMedia 在 stage 開始與完成時都必須保有 25 GiB hard floor；model cache／temporary output 估算需納入 preflight。
- 「較慢」不是失敗。只有同一 pinned local adapter 連續 3 次在上述資源 gate 下 OOM／critical pressure／無 checkpoint progress，或以至少 10% 已完成工作量外推單 Track Job wall time >72 小時，才可判定 local execution operationally impossible 並提出 Cloud Compute Profile；不得直接 offload。

## 6. Normalized-output equivalence

Maintenance candidate 要自動升格，以下必須與 active release 完全相同：

- canonical JSON 後的 Workflow Text Authority、Song Interpretation Brief references、Ruby Map、line／fine timing artifacts、decision reason codes、schemas、ASS semantic event／style／tag order；
- 移除 container timestamps／encoder metadata 後的 stream topology、duration、codec parameters，以及 decode 後 PCM audio hash與每個 subtitle event 的 full-width pixel hash；
- browser Evidence Artifact 的 canonical provenance fields 與 policy verdict；Publish Intent key、planned API operations、retention decisions。

允許的 normalization 只有本 registry version 明列的 JSON key order、Unicode NFC、CRLF→LF、container creation timestamp／non-semantic encoder string 移除。任何其他差異，即使仍通過品質門檻，也只能進 Toolchain Promotion Review，不能自動升格。

## 7. Concert V1 Acceptance

- 三個 representative real Media Projects、至少 12 Track Jobs、至少 300 實際 subtitle events；類別依 blueprint Phase 7，不得以同一來源的重複切片取代三類 project。
- 所有 hard gates為 0；所有適用 fixture metrics PASS；host restart／worker kill／duplicate request／upload interruption／wrong channel／low storage／Retention Plan dry-run／Recovery Vault restore／last-known-good rollback 全部留下 PASS evidence。
- 正常路徑需要人工改 JSON、移檔、臨時 shell repair、必要 editing GUI、額外 timing／deliverable gate，任一項都使 activation FAIL。
- 更換 registry version、gold annotations 或 toolchain release 後，受影響 corpus 與 acceptance drills 必須完整重跑，不能沿用舊 PASS。
