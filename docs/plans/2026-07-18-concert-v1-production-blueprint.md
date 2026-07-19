# Concert V1 production blueprint

Status: accepted implementation baseline; published as GitHub Issue [#18](https://github.com/roy4222/roy-ai-editor/issues/18).

## Outcome

把目前的人工輔助 CLI 變成 Mac mini 上可長時間運作的第一條 Production Golden Path：Roy 只需提交一個 YouTube Concert URL；Roy AI Editor 自動找章節／留言時間軸、選歌、研究歌詞與翻譯、準備一次 Concert Lyrics Review，通過後獨立製作每首 Track Job、做字幕與 burned-pixel QA、上傳成 private YouTube videos，最後回傳一次 Delivery Review。

正常路徑只保留一個固定人工 gate：Concert Lyrics Review。若有真正無法安全判斷的歌曲級問題，其他歌曲先繼續，最後集中成一份 Exception Digest。Roy 可用歌曲／時間點／自然語言／截圖修改；新版重新 QA 與 private upload，舊版保持 private，不自動刪除。

## Current baseline

目前 Repo 是可測的人工輔助原型，不是 Concert V1：

- 已有 Project Manifest、標準專案目錄、Evidence hashes、基本 URL idempotency。
- 已有 yt-dlp ingest、FFmpeg cut／burn／probe、雙語 ASS、基礎 `\kf`／ruby／layout QA。
- 已有 versioned Lyrics Packet、timing／deliverable 人工核准與 hash-verified local publish package。
- 已有 legacy migration、repo integrity、bootstrap locator、`pyproject.toml`、`uv.lock` 與 60 個測試。
- 目前 56 個測試通過；4 個 media tests 因 Dedicated Editor Host 尚缺 FFmpeg／FFprobe 而失敗。
- `/Volumes/RoyMedia` 已掛載且 Production Data Root 結構存在；`agent-browser` 已安裝。
- 目前 publishing 明確是 `upload_performed: false` 的人工發布 package；沒有 YouTube upload。
- 現有 `roy-editor doctor` 只檢查 FFmpeg、FFprobe、yt-dlp、pykakasi 與 Upstream Foundation。

## User-facing contract

### Normal Concert job

1. Roy 貼 URL；未指定歌曲時處理可信時間軸上的全部歌曲，指定時只處理點名歌曲。
2. 系統保存 Intake Authorization，完成 Rights Audit、Timeline Discovery、Source Subtitle Audit、歌詞／翻譯／讀音研究與 boundary candidates。
3. 系統一次顯示整場 Concert Lyrics Review；畫面中只有這個 gate 時，緊接的 `ok` 核准所有可見 packet hashes。
4. Production Worker 從 checkpoint 自動完成 alignment、render、QA、private upload 與 Publish Verification；關閉 Codex 或重啟 Mac 不會中止或重做已完成 stage。
5. 系統一次回傳 private links、QA、platform verdict、provisional metadata／thumbnail；只有完整 Delivery Review 是唯一 pending review 時，緊接的 `ok` 選定可見 Approved Deliverables，但不公開。
6. Roy 以歌名／時間點／自然語言／截圖要求修改；只重跑受影響 stages。Workflow Text Authority 改變時只重審受影響 Lyrics Packet。

### Exception behavior

- 一首歌失敗只暫停自己的 Track Job；其他歌曲繼續。
- 歌曲級問題在可自動工作完成後集中為一份 Exception Digest。
- RoyMedia、共享憑證、channel mismatch 或資料完整性等整場 blocker 才立即通知。
- 暫時性網路／worker／cache 問題在 Safe Self-Healing Action 成功後不打擾 Roy。

## Implementation order

### Phase 0 — Reproducible Mac mini foundation

Deliverables:

- 建立第一個 pinned Production Toolchain Release 與 machine-readable release manifest。
- 透過可重跑 bootstrap 安裝／驗證 FFmpeg＋FFprobe（含 libass、fontconfig、freetype）、Noto CJK fonts、Python／uv、yt-dlp＋Deno、agent-browser 與現階段必要 library。
- 把 `roy-editor doctor` 擴充成 read-only JSON checks：RoyMedia identity／APFS／25 GiB floor、tool versions／checksums、fonts／libass、browser、models、Keychain availability 與 repo integrity。
- 修復 Dedicated Editor Host 的 4 個 media test failures；從 clean checkout 重建並跑完整 tests。
- 不安裝 actionbook、browser-use、Agent-Reach、CapCut、BaoCut 或其他重複／GUI production dependencies。

Exit criteria:

- clean bootstrap 可重跑且不依賴手工安裝筆記。
- unit／integration tests 全綠。
- toolchain release 與 last-known-good rollback 可被 doctor 驗證。

### Phase 1 — Durable control plane

Deliverables:

- versioned Production Job Request、Project Manifest migrations、stage state machine 與 immutable Evidence Artifact schema。
- durable queue、job／stage idempotency keys、leases、heartbeats、retry evidence 與 crash-safe checkpoints。
- launchd Production Worker；同時只給一個 Media Project heavy slot，場內 Track Jobs 依 benchmarked resource profile 平行。
- Review Outbox、Codex monitor cursor 與不含秘密的 macOS notifications。
- 獨立 launchd Host Health Supervisor：開機、每六小時與 pre-job health snapshots；stage-specific PASS／DEGRADED／BLOCKED 與 bounded Safe Self-Healing Actions。

Exit criteria:

- kill worker、關閉 Codex、登出與重啟 Mac 後能續跑，不重複核准、下載或建立 remote side effect。
- queue／lease／outbox 重送 tests 全綠；任何 state 都可由 manifest 重建。

### Phase 2 — Storage, retention, and recovery safety

Deliverables:

- RoyMedia volume identity pin、Storage Preflight、per-stage space estimate 與 25 GiB hard floor。
- manifest-driven Retention Class：可再生 cache 7 天、可替代大型媒體自 Retention Eligibility 起 30 天、專案真相長期保存。
- 三天前建立精確 Retention Plan；到期時重新驗證 path、hash、lease、hold、remote playability 與 recovery snapshot，再逐檔永久刪除並寫 Retention Tombstone。
- 內接碟最多 10 GiB、加密／hash-verified、restore-only Recovery Vault；每日與刪除／migration／profile promotion 前 snapshot。

Exit criteria:

- dry-run、wrong-volume、symlink、changed-hash、active-job、Retention Hold、failed-backup 與 restore drills 全綠。
- 不使用 wildcard／project-directory recursive deletion，不以 mtime／atime 決定期限。

### Phase 3 — Browser discovery, rights, and text authority

Deliverables:

- 隔離、持久化的 `roy-concert-discovery` 與 `roy-studio-verify` browser profiles；兩者各自綁定 default-deny Browser Read-Only Enforcement Profile，強制 content boundaries、domain/path allowlist、action policy、output limit 與 Browser Action Ledger，且不得共用 Roy 日常 profile／publisher credential。
- Timeline Discovery 依序讀 chapters、description、creator／pinned／credible comments，保存 permalink、author、text、capture time 與 screenshot。
- automated Rights Audit；明確禁止／access-control bypass 停止，缺失或衝突才進 Exception Review。
- official-Japanese-first、Bahamut-first Traditional Chinese research、translation reuse terms 與 provenance capture。
- Song Interpretation Brief、Roy Translation Notebook、contextual cases／explicit Translation Rules。
- 全曲一次 Concert Lyrics Review 與精確 packet-hash approval semantics。

Exit criteria:

- 依 `concert-v1-quality@1.0.0` 的至少 40 個 YouTube／Bahamut／prompt-injection／mutation fixtures 計算 evidence capture；critical provenance 與 mutation prevention 100%、整體至少 95%。低於門檻且 locator／engine 是主因時，才 benchmark Playwright CLI。
- 沒有可信時間軸時才使用 ASR／影音推測，且 comment timestamp 永遠只是 Boundary Anchor。

### Phase 4 — Three bounded production capability spikes

Spike A — Source Subtitle Audit:

- ffprobe soft-track detection、burned subtitle OCR／visual scene evidence、pysubs2 normalization 與 full-song coverage classification。
- 驗證 Source Japanese Subtitle Mode 與 Safe-Area Recovery；部分／錯字／錯時 soft subtitle 必須停用後全曲 Normal Bilingual Subtitle Mode，burned subtitle 必須建立 Source Subtitle Fallback Plan 並通過全曲 Caption Region Replacement，否則只允許 skip／version-bound exception，絕不逐行混搭。

Spike B — Live Alignment:

- 在 M4／24 GiB 上比較 Qwen3-ASR、WhisperX／frozen stable-ts adapter，測 raw mix 與 separated vocal。
- 衡量 line boundary、token／mora timing、長音／melisma／觀眾聲、runtime、memory、model cache 與失敗降級。
- 本機通過但過慢不算失敗；沒有核准 Cloud Compute Profile 時不得上傳 media 到 external GPU。

Spike C — ASS, Ruby, and pixel QA:

- pysubs2／libass、Sudachi／fugashi 等候選形成統一 adapter artifacts。
- 官方讀音或兩個獨立解析器一致且無歧義才自動放行；姓名、熟字訓、当て字、送假名與 acoustic conflict 進 Exception Review。
- 逐行 original-resolution full-width subtitle-band crops，加上自動 OCR／layout checks 與 Computer Use 第二次 read-only visual pass。

Exit criteria:

- 三個 spike 都在 candidate run 前釘選 `docs/quality/concert-v1-quality-registry.md` version/hash 與 fixture manifest，並通過其中已登錄的 quality、resource、license、failure-degradation 與 artifact-contract thresholds；事後改門檻必須升版並完整重跑。
- 公開 Git 只有 synthetic fixtures；私人真實 corpus 留在 RoyMedia shared Retention Hold，最多 5 GiB。

### Phase 5 — Independent Track production and automated QA

Deliverables:

- Lyrics Review 後每首先建立獨立 Track Job；切段使用 Boundary Anchor 加 waveform／vocal／applause／MC／visual evidence，保留 intro 與完整尾奏。
- Alignment Adapter、Timing Fidelity Tiers 與 Automated Quality Verdict；fine timing 可降級到 passing line timing，錯誤 line boundary 不得放行。
- Source Japanese Subtitle Mode、Safe-Area Recovery、Source Subtitle Fallback Plan／Caption Region Replacement、Normal Bilingual Subtitle Mode 與 versioned Concert Subtitle Profile。
- Singer Color Policy：只用可信官方 colors；不確定且不影響語意／credit 時使用 neutral。
- render、decode、audio／frame integrity、逐行 Burned-Pixel Review 與 Computer Use visual QA，產生 Verified Render。

Exit criteria:

- 不再需要固定 `approve-timing` 或 `approve-deliverable` gate。
- 任一文字、ruby、order、boundary、clipping、media integrity 或 duplicate-output error 都能被測試阻止。

### Phase 6 — Private publishing, delivery, and revisions

Deliverables:

- one-time native OAuth／PKCE setup；Production Publisher Credential 只有 `youtube.upload + youtube.readonly`，refresh token 只在 macOS Keychain。
- Channel Binding Profile 固定唯一 expected channel ID；每次 insert 前後雙重核對，強制 private、`notifySubscribers=false`。
- crash-safe resumable Publish Intent／Attempt：network 前 fsync deterministic key、session URI 只存 Keychain/encrypted private state、first byte 前保存 opaque reference；任何 uncertain outcome 先做 exact-marker own-channel Orphan Upload Reconciliation，再決定 adopt／block／new insert。
- YouTube processing polling 與 `roy-studio-verify` 的 separate default-deny read-only restriction check；角色以 registry fixture 證明的最低可行 viewer permission 為準。
- Publish Verification：unrestricted PASS；可播放、只影響追蹤／營利的 Content ID claim 為 WARN；blocked／muted／removed／failed／unplayable 為 FAIL。
- Delivery Review、timestamped Revision Request、new-video-per-revision lineage、Superseded Remote Revision 與 immutable Remote Cleanup Plan。

Exit criteria:

- `concert-v1-quality@1.0.0` 至少 50 個 fault-injection boundaries 全綠：retry、response loss、session expiry、network interruption 與 reboot 不建立 duplicate upload，unique orphan 100% adopt，ambiguous 100% fail closed。
- Production Worker 無 `videos.update`／`videos.delete` 能力；不使用 browser upload／dispute／Studio edit。
- V1 只承諾 private upload。Visibility Promotion 與 remote deletion 留給 compliance-audited、隔離的 Privileged YouTube Executor 與精確顯式核准。

### Phase 7 — Concert V1 acceptance and activation

Acceptance set:

- 三個 representative real Media Projects、至少 12 Track Jobs：
  - 單人／來源無完整日文字幕；
  - 多人／完整來源日文字幕，包含 Safe-Area Recovery；
  - cover／翻譯主軸／ruby／alignment 困難案例。
- 演練 host reboot、worker kill、stage retry、duplicate URL、upload retry、network／quota／OAuth failures、channel mismatch、wrong／low-space RoyMedia、Retention Plan dry-run、Recovery Vault backup／restore 與 last-known-good toolchain rollback。
- 正常路徑不得要求人工改 JSON、搬檔、臨時 shell repair 或必要 editing GUI。
- 固定人工 gate 只有 Concert Lyrics Review；歌曲級 exceptions 最多集中一份 digest。

Activation:

- acceptance 全綠後產生一次 Production Activation Review，列出 corpus／real-project metrics、已知限制、rollback 與目前 Production Toolchain Release。
- Roy 最後一次確認後才把 URL intake 預設切到 production mode；之前所有輸出標記為 development／acceptance candidate。

### Phase 8 — Maintain and expand

- Maintenance Train 每週發現更新、通常每月建立候選；只有符合 pinned Concert V1 Quality Registry 明列 exact normalization 的 maintenance 可自動升格，其他輸出差異即使品質仍 PASS 也進一次 Toolchain Promotion Review。
- Concert V1 完成後，第二條 Production Golden Path 是 Directed Footage Workflow：本機／Drive 素材＋Editing Brief → Asset Inventory／proxy／understanding → Edit Plan／EDL → render／QA → private link。
- Reels／Shorts 優先作為核准長片或素材庫衍生物；再做 talking-head localization 並評估 BaoCut／VideoLingo adapter；其他專門 Workflow 後續組合已驗證能力。
- Roy Editing Notebook 保存 contextual Editing Cases；只有 Roy 明確的 always／never 才成為有作用域 Editing Preference Rule。

## Human input schedule

實作可以先進行 Phase 0–5，不需要 Roy 提供帳密或真實頻道資料。只有下列時點需要 Roy：

1. Phase 6 第一次 OAuth consent 與 expected YouTube channel ID 綁定。
2. Phase 7 提供／確認三個 representative real Concert URLs；每個 project 仍有一次正常 Concert Lyrics Review。
3. Concert V1 Production Activation Review。
4. 未來 Visibility Promotion、Remote Cleanup Plan、quality-changing Toolchain Promotion Review 或真正的 Exception Digest。

## Explicitly deferred

- public／unlisted 自動 promotion 與 YouTube remote deletion executor，直到 compliance audit 與獨立驗收完成。
- Cloud GPU，直到 M4 benchmarks 證明 local operationally impossible 且 Roy 核准 Cloud Compute Profile。
- actionbook、browser-use、Agent-Reach；Playwright CLI 只有 agent-browser 同 fixtures success 低於 95% 且原因符合門檻時才 benchmark。
- CapCut／DaVinci／Kdenlive／BaoCut 作為 Production Golden Path 必要依賴。
- Directed Footage、Reels、talking-head localization 與其他影片類型的正式實作，直到 Concert V1 Acceptance。

## First implementation slice after confirmation

1. 保存目前文件基線並建立 implementation issues／milestones。
2. 補齊 Brewfile／bootstrap 與 pinned tool manifest，安裝 FFmpeg／FFprobe／fonts，讓 60 tests 全綠。
3. 把 `roy-editor doctor` 改成 machine-readable read-only health checks。
4. 先以 synthetic jobs 建立 Production Job Request、queue／lease／checkpoint、launchd worker、Review Outbox 與 Host Health Supervisor 骨架。
5. 在任何真實自動下載、上傳或永久回收之前，通過 crash／restart／duplicate-side-effect tests。

## Decision sources

此藍圖受 [CONTEXT.md](../../CONTEXT.md)、[ADR 0001–0047](../adr/) 與 [Concert V1 Quality Registry](../quality/concert-v1-quality-registry.md) 約束；若實作發現衝突，先新增或修訂 ADR／registry version，不得悄悄偏離已核准的 domain vocabulary、review gates、retention、publishing、quality thresholds 或 safety boundaries。
