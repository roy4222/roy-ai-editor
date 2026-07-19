# Roy AI Editor

Roy AI Editor 是建立在既有開源影片製作框架之上的專屬 AI 剪輯師。它以 Roy 的品味、素材、工作方式與核准責任為中心，逐步支援多種影片製作情境。

## Language

**Roy AI Editor**:
Roy 的專屬 AI 剪輯師產品；以 **Upstream Foundation** 為起點，再加入 Roy 自己的能力、偏好與 **Editing Workflow**。
_Avoid_: 卡拉 OK 工具、vendored toolkit

**Upstream Foundation**:
Roy AI Editor 所建立其上的 `Hao0321/video-autopilot-kit` 開源框架。它是產品的基礎，不是擺在旁邊、可有可無的參考快照。
_Avoid_: 參考 Repo、被動 vendor、獨立工具包

**External Capability Adapter**:
把 BaoCut 等第三方工具封裝在 Roy 自有契約後面的可替換整合；它可以產生 Work Artifact 與 Evidence Artifact，但不擁有 Project Manifest、核准狀態或正式時間線。
_Avoid_: 第二個 Upstream Foundation、外部工具的專案檔就是 source of truth、不可替換核心

**Production Capability Spike**:
第三方工具或模型進入 Production Toolchain 前，在固定 golden fixtures 上執行的有界驗證，預先定義品質、headless／Apple Silicon、資源、失敗降級、license、版本與 artifact 契約門檻。只有全部通過的能力才能透過 External Capability Adapter 升格；「能啟動」或單一成功案例不算通過。
_Avoid_: 先裝再說、star 數就是品質、整套 fork、沒有驗收門檻的試用

**Concert Golden Corpus**:
用來驗證 Concert Live 的雙層固定品質基準：公開 Repo 保存小型合成 Test Fixtures，RoyMedia `shared` 保存最多 5 GiB、具長期 Retention Hold 的私人真實短片與人工 gold annotations。它涵蓋字幕模式、Safe-Area Recovery、單／多人、對軸困難、翻譯主軸與 Ruby 歧義；工具、模型或 profile 未通過整套 corpus 不得升格。
_Avoid_: 單一成功影片、把真實 Live 放進公開 Git、普通 30 天 Media Project、只保存輸出沒有 gold annotation

**Roy Customization**:
讓 **Upstream Foundation** 成為 Roy 專屬剪輯師的能力、偏好、知識與工作流程。它應能被重複使用與持續改進，而不是只服務單一影片的一次性做法。
_Avoid_: 臨時腳本、專案特例

**Roy Editing Notebook**:
跨 Media Projects 累積的私人剪輯案例庫，保存 Editing Brief、素材特徵、Edit Plan、候選版本、Roy 的保留／刪除／移動／節奏／字幕修正、選擇理由與最終結果。每筆預設是帶有 Editing Workflow、頻道、片型、受眾與畫幅語境的 Editing Case，只影響 retrieval、候選排序與 regression，不自動成為規則。
_Avoid_: 單一專案 notes、把一次修改當永恆風格、無來源的偏好向量、未核准模型訓練集

**Editing Preference Rule**:
Roy 明確表示「以後都這樣」或「永遠不要這樣」後建立的版本化剪輯規則，必須限定適用 Editing Workflow、頻道、片型、受眾或畫幅。重複 Editing Cases 可以產生升級建議，但系統不得自行建立永久規則或自動 fine-tune。
_Avoid_: 跨片型全域套用、從沉默推測偏好、模型自行改 profile、沒有作用域的 always／never

**Public Customization**:
可以公開重用且不包含秘密、私人資料或授權受限內容的 **Roy Customization**。它可以與 Roy AI Editor 的公開程式碼一起版控與發布。
_Avoid_: Private Configuration、Production Asset

**Private Configuration**:
讓 Roy AI Editor 在本機運作、但不得進入公開 Repo 的秘密或私人值，例如 credentials、私人聯絡資訊與未公開分析資料。公開 Repo 只保存其 schema 或安全範例。
_Avoid_: Public Customization、授權受限 Production Asset

**Editing Workflow**:
針對一類影片製作需求，組合可重用能力、品質標準與 Roy 核准點的完整路徑。一個 **Roy AI Editor** 可以擁有多個 Editing Workflow。
_Avoid_: 單支影片專案、一次性操作步驟

**Concert Live Workflow**:
處理 Live／3D Live／歌回切歌、多語歌詞、卡拉 OK、品質檢查與發布準備的第一個 **Editing Workflow**。它是 Roy AI Editor 的第一個產品切片，不等於整個產品。
_Avoid_: Roy AI Editor 本身、通用剪輯核心

**Directed Footage Workflow**:
Concert V1 後的第二條 Production Golden Path；Roy 提供本機／Drive 素材集合與自然語言 Editing Brief，流程建立 Asset Inventory、內容理解、結構化 Edit Plan／EDL、render、QA 與 private link。它是通用素材剪輯核心，Reels／Shorts 優先作為其核准長片或素材庫的衍生 Workflow。
_Avoid_: 一鍵短片拼接器、CapCut project 就是 source of truth、Concert Live 的隱藏擴張、沒有 Editing Brief 的自由剪輯

**Setlist Timeline Evidence**:
從影片章節、說明欄、創作者／置頂／可信留言或 Roy 提供內容取得的歌曲名稱與時間錨點集合；每筆保留來源、作者、permalink、擷取時間與可重播截圖。它用來建立 Track Selection 與 Boundary Anchor，不是正式精確剪點。
_Avoid_: 未附來源的模型曲目表、留言秒數就是下刀點、最終 timing

**Provided Setlist Timeline**:
Roy 隨 Concert URL 主動提供的留言區時間軸截圖或文字，是最高優先的 Setlist Timeline Evidence，但不是啟動 Concert Live Workflow 的必要輸入。
_Avoid_: 唯一允許的曲目輸入、沒有截圖就拒絕啟動、最終精確剪點

**Timeline Discovery**:
透過 Discovery Browser Profile 自動打開來源影片，依序檢查章節、說明欄、創作者／置頂／高可信留言並保存 Setlist Timeline Evidence 的流程。找不到可信時間軸時才使用音訊、畫面、歌詞與 ASR 建立候選，人機驗證或存取限制不得被繞過。
_Avoid_: 要 Roy 先截留言、只靠 ASR 猜歌、無證據地抓第一則留言、匿名 session 是唯一模式

**Discovery Browser Profile**:
Dedicated Editor Host 上只供 Timeline Discovery 使用的持久化登入瀏覽器身分；Roy 必要時完成首次登入，之後流程只能讀取公開／帳號可見影片與留言，不得留言、按讚、訂閱或修改帳號。登入狀態屬於 Private Configuration，上傳仍由 Publish Job 使用正式 API。
_Avoid_: Roy 日常瀏覽器 profile、瀏覽器上傳機器人、可寫入社群互動的帳號代理、Git 內的 cookies

**Browser Read-Only Enforcement Profile**:
把瀏覽器唯讀承諾轉成 controller 可執行的版本化政策：隔離 profile、domain／path allowlist、靜態 action policy、content-boundary 標記、禁止輸入／表單／下載／eval／社群互動／Studio 編輯，以及不可覆寫 Browser Action Ledger。頁面、留言與 OCR 內容一律是 untrusted data，不能改寫 policy 或授權新動作。
_Avoid_: 只靠 prompt 說不要按、使用 Roy 日常 profile、允許任意 JavaScript、看見網頁指令就執行、沒有 action evidence

**Browser Action Ledger**:
每次自動瀏覽的不可覆寫 Evidence Artifact，記錄 browser profile／policy 版本、動作分類、URL、locator、結果、截圖／snapshot hash、redirect 與被拒絕的 mutation／download 嘗試；unexpected navigation 或不在 allowlist 的動作必須 fail closed。
_Avoid_: 只有最後截圖、瀏覽器歷史紀錄、含 cookies 的 debug log、事後聲稱全程唯讀

**Boundary Anchor**:
Setlist Timeline Evidence 中用來導航到歌曲邊界附近的時間點，不是直接下刀的精確 frame。流程在錨點前後驗證音樂、MC、掌聲與畫面訊號後，才產生正式 start／end。
_Avoid_: 精確剪點、留言秒數直接硬切、ASR 自動決定的最終邊界

**Track Selection**:
一次 Concert Live Media Project 要製作的歌曲集合；Roy 未特別指定時包含已驗證 Setlist Timeline Evidence 的全部歌曲項目，明確點名時只包含指定歌曲。
_Avoid_: 每次逐首詢問、預設只剪精華、把 MC／雜談當歌曲

**Track Job**:
Track Selection 中單一歌曲在 Lyrics Packet 核准後的獨立製作生命週期，擁有自己的切段、對軸、渲染、QA、Publish Job 與例外狀態。一首歌失敗時只停住該 Track Job，其他已通過門檻的歌曲繼續生產與交付。
_Avoid_: 整場單一巨型 job、一首 QA 失敗卡住全部歌曲、只有全數成功才能交付

**Intake Authorization**:
Roy 主動提交來源 URL 時，授權 Roy AI Editor 下載並進行本機處理與 private 上傳。它不表示 Roy 聲稱擁有來源權利，也不授權繞過存取控制或進行 Visibility Promotion。
_Avoid_: rights approval、copyright ownership、public permission、URL 只是未確認線索

**Rights Audit**:
對來源影片、頻道／公司二創規範、歌曲限制與翻譯重用條件所做的版本化證據檢查。明確允許時自動繼續，明確禁止或需要繞過存取控制時停止，證據缺失或矛盾時才觸發 Exception Review；它提供風險分流，不宣稱法律確定性。
_Avoid_: Roy 每次手動 approve-rights、法律意見、找到來源就等於可重用

**Production Golden Path**:
一條已在代表性真實案例上證明可重跑、可續跑且不依賴臨時人工檔案操作的端到端製作路徑。Roy AI Editor 的第一條 Production Golden Path 是由 YouTube Concert URL 到 private YouTube 連結的 Concert Live 流程。
_Avoid_: 能成功一次的 demo、人工拼接 SOP、尚未驗收的 happy path

**Concert V1 Acceptance**:
Concert Live 成為 Production Golden Path 的完成門檻：三個 Production Capability Spikes 與 Concert Golden Corpus 全部通過，並在三類真實 Media Projects、至少 12 個 Track Jobs 上完成 URL 到 private links；同時驗證重啟續跑、retry／重複提交 idempotency、Publish Verification、Retention Plan dry-run 與 Recovery Vault restore，且無人工改 JSON、搬檔或必要 GUI 操作。
_Avoid_: 一支影片成功就完成、只有 happy path、測試通過但不能 restore、人工補救後宣稱全自動

**Media Project**:
一次影片製作工作的完整資料集合，包含輸入、核准資料、中間產物、品質證據與交付成品。Media Project 不持有可跨專案重用的程式碼。
_Avoid_: 程式碼 Repo、Editing Workflow

**Production Job Request**:
Roy 從 Codex Control Surface 提交的不可覆寫製作意圖，至少記錄來源 URL、Track Selection 規則、Intake Authorization、提交時間與 request ID。它建立或引用 Media Project，讓 Production Worker 可在對話關閉或主機重啟後從 Project Manifest checkpoint 繼續。
_Avoid_: 暫時 shell command、聊天訊息就是 queue、重開機後重新猜需求

**Codex Control Surface**:
Roy 提交 Production Job Request、處理 Concert Lyrics Review／Exception Digest／Visibility Promotion 並接收 private links 的互動介面。它不承擔長時間媒體 process 的存活，也不是 Project Manifest 的替代狀態來源。
_Avoid_: 背景 daemon、本次對話記憶就是專案真相、關閉聊天就取消工作

**Review Outbox**:
Production Worker 寫入並由 Project Manifest 引用的持久化待通知事件流，承載 Concert Lyrics Review ready、共享 blocker、Exception Digest 與 private links ready。V1 由 Codex monitor 去重後送回原 Production Job Request 的 Codex task，並只用 macOS Notification Center 顯示無敏感內容摘要；通知重送不得重複核准或觸發動作。
_Avoid_: 終端輸出就是通知、未保存的 push message、Email／Slack 是必要依賴、重送事件重新執行 gate

**Project Manifest**:
一個 **Media Project** 目前狀態的唯一真相，記錄曲目、階段、核准狀態、Review Outbox cursor 與各項 **Evidence Artifact** 的引用。其他報告不得各自宣稱不同的專案狀態。
_Avoid_: 最終交付報告、零散狀態檔

**Evidence Artifact**:
某次處理、檢查或核准所留下的不可覆寫證據，由 **Project Manifest** 引用。它證明發生過什麼，但不單獨決定 Media Project 的目前狀態。
_Avoid_: Project Manifest、可反覆覆寫的暫存檔

**Workflow Text Authority**:
一個 Editing Workflow 中允許決定正式文字內容的已核准來源；Concert Live 使用核准歌詞包，未來口播流程使用經驗證逐字稿，ASR 候選本身不自動成為文字真相。
_Avoid_: 原始 ASR 輸出、任一工具的最新文字、未核准模型答案

**Song Interpretation Brief**:
逐行翻譯前建立的整首歌語意框架，記錄敘事主體、對象、核心主軸、情緒弧線、反覆意象、跨行關係、關鍵詞與歧義證據。它約束翻譯必須服務整體原意，但本身不取代日文歌詞或 Lyrics Packet 核准。
_Avoid_: 單句字典翻譯、自由創作摘要、沒有來源的故事腦補、逐詞對照表

**Roy Translation Notebook**:
跨 Media Projects 累積的日文歌曲翻譯記錄簿，由有來源的外部譯例研究、Song Interpretation Brief、候選譯法、採用理由、Roy 修正與已核准結果形成。每筆預設是帶有歌曲語境、provenance 與 reuse terms 的案例，只影響研究與候選排序，不因重複出現就自動成為 Translation Rule。
_Avoid_: 抄錄整站翻譯、無來源 phrase table、單純模型 fine-tuning corpus、每筆案例都是字典規則

**Translation Rule**:
可在相容語境中自動套用的穩定翻譯偏好，只能來自官方固定譯名或 Roy 明確指定的「以後固定這樣翻」。重複案例可以產生升級建議，但不能自行建立規則；每次套用仍須驗證歌手、敘事視角、主軸與意象語境。
_Avoid_: 模型從頻率自行歸納的永久規則、跨歌曲無條件字串替換、沒有 provenance 的 glossary

**Lyrics Packet**:
每首歌在對軸前一次交給 Roy 核准的版本化文字單位，包含日文原詞與來源、performed repeats、Song Interpretation Brief、Roy Translation Notebook 引用、來源譯文的作者／重用條件或獨立 AI 繁中翻譯草稿的產生證據、不確定標記、line map 與內容 hash。只有 Roy 核准的精確版本才能成為 Concert Live 的 Workflow Text Authority，任一文字、整體詮釋或斷行變更都使舊核准失效。
_Avoid_: 零散 URL 清單、未標來源的 AI 翻譯、逐句核准、核准後靜默修字

**Concert Lyrics Review**:
把一場 Live 中所有 Track Selection 的 Lyrics Packet 集中成唯一固定核准介面；每首先顯示 Song Interpretation Brief，再顯示完整日中配對文字與醒目例外，自動通過的技術證據預設收合。每首仍保有獨立版本與 hash，Roy 可一次全數通過或只指出歌曲／行號；當它是畫面中唯一待處理 gate 且完整 review 已顯示時，緊接其後的 `ok` 即核准當下所有可見 briefs 與 packet hashes，修改後只重審受影響 packet。
_Avoid_: 每首歌停一次、要求手打固定核准句、一行修改使整場核准失效、其他對話中的 ok 被誤當核准

**Ruby Map**:
根據 Lyrics Packet 中已核准日文行建立的假名映射，以穩定 line ID 記錄每個漢字 base span、平假名讀音、來源與信心狀態。它決定要顯示什麼讀音與放在哪段漢字上，不包含畫面座標。
_Avoid_: 未審查的 pykakasi 輸出、全句假名、把送假名含進 base span、ASS 座標表

**Ruby Evidence Policy**:
Ruby Map 項目的自動放行規則：官方讀音證據可直接支持；否則必須兩個獨立日文解析證據一致、沒有姓名／熟字訓／當て字等歧義，且不與演唱聲學證據衝突。任一條件不足的行才進入 Exception Review。
_Avoid_: 單一解析器即正確、截圖位置正確等於讀音正確、把所有漢字交給 Roy 重審

**Source Subtitle Audit**:
每個 Track Job 在字幕設計前對來源影片進行的字幕證據檢查，區分可選字幕軌、已燒錄日文歌詞、零星演出文字與無字幕，並記錄覆蓋率、文字／時間一致性、畫面位置與截圖證據。來源字幕可支持模式選擇，但不取代 Lyrics Packet 的 Workflow Text Authority。
_Avoid_: 看到一張日文截圖就假設整首完整、把歌名卡當歌詞字幕、忽略可選字幕軌

**Source Japanese Subtitle Mode**:
Source Subtitle Audit 證明一首歌 100% performed lines 都有日文字幕，文字／順序／時間與核准 Lyrics Packet 一致，且原生或經 Safe-Area Recovery 後保有安全繁中區域時使用的畫面模式；保留來源日文，不重複燒錄日文或平假名。任一缺行、錯字或時間不符都屬 Track-level Exception Review，不自動混搭模式。
_Avoid_: 雙重日文字幕、用新 ruby 蓋在原字幕上、接受 99% 覆蓋率、逐行混搭兩種日文樣式、空間不足就改放日文上方

**Source Subtitle Fallback Plan**:
Source Subtitle Audit 未達 Source Japanese Subtitle Mode 的 100% 門檻時，對整首 Track Job 選定且保存的單一處理計畫：可停用不完整 soft track 後全曲使用 Normal Bilingual Subtitle Mode；或對固定 burned-caption region 執行全曲 Caption Region Replacement，再全曲使用 Normal Bilingual Subtitle Mode。不能安全、完整替換時才建立帶證據的 Track-level Exception Review，選項只能是跳過該曲或核准精確版本例外。
_Avoid_: 98% 就當完整、逐行混搭、只補缺的兩行、偷偷遮住重要畫面、無證據地放行

**Caption Region Replacement**:
針對不完整或錯誤 burned-in 日文字幕，在整首歌固定區域採取的決定性中和與重排轉換；必須完整消除舊字幕可讀像素、保留重要構圖，並為每個 performed line 重新渲染核准的日文／Ruby Map／繁中。無法滿足任一條件就不得自動使用。
_Avoid_: content-aware 靜默修補、只蓋錯字、逐行切換來源／新字幕、把殘留舊字當裝飾

**Normal Bilingual Subtitle Mode**:
來源沒有可完整沿用的日文歌詞時，對整首 Track Job 由核准 Lyrics Packet、Ruby Map 與繁中配對重新渲染日文／平假名／繁中的標準模式；來源 soft track 必須停用，來源 burned-in 字幕則必須先通過 Caption Region Replacement。
_Avoid_: 和來源字幕重疊、部分沿用來源日文、未核准 ASR 文字、只補繁中

**Safe-Area Recovery**:
來源日文字幕完整但下方空間不足時，在維持原輸出解析度與長寬比下等比例縮小並靠上放置來源畫面，以底部字幕帶建立繁中安全區的決定性版面轉換。只有來源日文仍清晰、繁中不裁切且重要畫面構圖未受損時才能自動通過，否則進入 Exception Review。
_Avoid_: 拉伸畫面、裁掉重要內容、改變輸出長寬比、把繁中放在日文上方、用底條遮住來源日文

**Burned-Pixel Review**:
從實際燒錄後 MP4 對每個歌詞行取得的原尺寸、全寬字幕帶審查，以 Ruby Map、日文／繁中 line map 與安全區為比對證據。可使用自動畫面檢查與 Computer Use 視覺複核，但不得用未燒錄預覽、ASS 座標或縮小全畫面代替。
_Avoid_: 編輯器預覽、只看模型文字回報、只抽樣少數句、以座標推斷已對齊

**Alignment Adapter**:
把 stable-ts、Qwen 或未來本機／遠端對齊後端藏在統一契約後的可替換邊界；後端只根據 Workflow Text Authority 產生版本化 timing Evidence Artifact，必須通過代表性演唱基準與 QA 才能加入 Production Toolchain。
_Avoid_: Qwen 是正式歌詞來源、ASR timestamp 就是核准對軸、寫死特定模型或 GPU

**Local-First Compute Policy**:
Concert Live 的 ASR／alignment、OCR、音軌分離與 render 優先在 Dedicated Editor Host 執行；品質通過但速度較慢仍視為可生產。只有本機品質已證明、卻因記憶體或 runtime 無法穩定完成時，才可提出 External GPU Adapter，且不得在 Cloud Compute Profile 核准前上傳媒體。
_Avoid_: 雲端比較快就自動上傳、慢等於失敗、未核准 provider、整支來源影片預設外送

**Cloud Compute Profile**:
Roy 明確核准後才允許 External GPU Adapter 使用的版本化 Private Configuration，定義 provider、資料保留／刪除條件、允許上傳的最小 artifact、模型版本、單 job／月費用上限與 audit evidence。沒有 profile 時本機無法完成的 job 進入 Exception Digest，不得靜默 offload。
_Avoid_: API key 就代表授權、無費用上限 GPU、把完整 Production Data Root 同步到雲端、provider 預設值

**Timing Fidelity Tier**:
Concert Live 字幕的對軸層級：通過 QA 的逐行起訖時間是正式產出必達門檻；逐字／逐 mora 動態上色只在細粒度證據通過時啟用，否則明確降級為整行字幕。每首歌保持同一主要層級，只有口白、喊聲或非正式歌詞 ad-lib 可作單句靜態例外。逐行失準、切掉首字或尾音不屬於可降級情況，必須觸發 Exception Review。
_Avoid_: 平均分配假裝精準對軸、用整行字幕遮蔽邊界錯誤、一首歌在主要字幕模式間反覆跳轉、因細粒度不足停住整個專案

**Singer Color Policy**:
多人演唱字幕的穩定配色規則；身份與官方代表色有足夠證據時使用經可讀性調整的成員色，合唱使用群體樣式，身份不確定時自動降級為中性色。Source Japanese Subtitle Mode 保留來源日文顏色，新增繁中不從來源色彩猜測歌手。
_Avoid_: 猜測歌手顏色、低信心就停工、犧牲對比度的精確色碼、重畫來源日文樣式

**Concert Subtitle Profile**:
版本化的 Roy Customization，定義 Concert Live 的日文、平假名、繁中、卡拉 OK 與 Singer Color Policy 之字體、比例、間距、描邊、安全區及狀態色。HACHI《万華鏡》v3 是 v1 基線而非品質上限；每次 render 記錄 profile 版本，Source Japanese Subtitle Mode 只把 profile 套用到新增繁中與必要的 Safe-Area Recovery。
_Avoid_: 每支影片臨時調樣式、未記錄的 ASS 常數、CapCut preset 就是正式 profile、更新 profile 靜默改寫舊成片

**Exception Review**:
只在證據衝突、低信心、品質失敗或正式來源變更時要求 Roy 介入的審查；Track Job 層級的問題先暫停自己並進入 Exception Digest，不立即逐題打斷 Roy。
_Avoid_: 每一步都停下來、每首歌各問一次、把沉默當核准、遇到異常仍自動放行

**Exception Digest**:
同一 Media Project 中各 Track Job 在其他可自動工作都完成後集中呈現的例外批次，包含問題、證據、建議答案與影響範圍。只有會阻塞整場的共享驗證、憑證或 Storage Preflight 問題可以在 digest 前立即通知；Roy 一次回覆後只恢復受影響 jobs。
_Avoid_: 即時錯誤洗版、整場 all-or-nothing、沒有建議答案的問題清單、單曲問題阻塞其他歌曲

**Automated Quality Verdict**:
由可重播檢查產生並附有 Evidence Artifact 的 PASS、WARN 或 FAIL 結果。它可以讓流程自動前進或觸發 Exception Review，但不冒充 Roy 的人工核准。
_Avoid_: machine-approved、Roy 看過、自動檢查等於人工簽字

**Verified Render**:
已完成最終編碼，且逐行 Burned-Pixel Review、影音完整性與發布前自動檢查均取得 PASS 的成片候選。它可以不經另一個固定人工關卡自動上傳為 private，但在 Roy 明確選定前不是 Approved Deliverable。
_Avoid_: machine-approved deliverable、final 檔、Roy 已驗收、public-ready

**Delivery Review**:
一次集中顯示已完成 Track Jobs 的 private links、Publish Verification、provisional metadata／縮圖與 QA 摘要的交付介面。當它是唯一待處理 review 且完整內容已顯示時，緊接其後的 `ok` 只把可見 versions／hashes 選為 Approved Deliverables；它不構成 Visibility Promotion。
_Avoid_: 每首成片分開核准、看見連結就算核准、ok 自動公開、沒有綁定 render hash 的口頭通過

**Revision Request**:
Roy 在 Codex Control Surface 以歌曲 ID／歌名、時間點、自然語言與可選截圖提出的版本化修改意圖；系統綁定原 render hash、private video ID，自動擷取前後畫面／音訊／字幕證據並正規化受影響範圍與 stages。能明確解讀的切點、節奏、位置、顏色或 timing 修改直接重跑；只有改變 Workflow Text Authority 才重審受影響 Lyrics Packet。
_Avoid_: 必須開時間軸 GUI、直接覆寫 final、整場全部重跑、沒有版本基準的「再修一下」、影片修了但 manifest 沒變

**Approved Deliverable**:
Roy 在 Delivery Review 明確選定，並由 **Project Manifest** 記錄為目前交付版本的影片、字幕或發布資產；當完整 Delivery Review 是唯一 pending review 時，直接跟隨的 `ok` 可綁定並選定所有可見 versions／hashes。Verified Render、private link、檔名含有 `final`／`approved` 或版本號本身都不構成核准，Approved Deliverable 也不自動取得較高可見性。
_Avoid_: final 檔案、最新修改檔、review 版本

**Publish Job**:
一次可續跑且具 idempotency 的遠端上傳生命週期，記錄 Verified Render 或 Approved Deliverable、遠端影片 ID、處理狀態、可見性、Publish Verification 與重試證據。重試同一個 Publish Job 不得建立重複影片。
_Avoid_: 單次 upload command、只保存 YouTube URL、重試就重新上傳

**Publish Intent**:
在任何 YouTube network side effect 前持久化的不可覆寫上傳意圖，以 channel binding version、Track Job／revision ID、render hash、Channel Publish Profile version 與 private visibility 產生 deterministic publish key；同一意圖可有多次 Publish Attempts，但只能採用一個 remote video ID。
_Avoid_: request 開始後才記錄、隨機 retry key、只用檔名去重、每次重試都是新 job

**Publish Attempt**:
Publish Intent 底下的一次 resumable upload 嘗試，記錄 attempt ID、resumable session 的 Keychain reference／URI hash、已確認 byte range、terminal response、remote video ID 與 reconciliation evidence。session URI 視同秘密，只能保存於 Keychain／加密 private state，Project Manifest 不得保存明文。
_Avoid_: log 裡的 upload URL、拿不到 response 就直接再 insert、不同 render 共用 session、未 fsync 就送第一個 media byte

**Orphan Upload Reconciliation**:
Publish Attempt 在 response 遺失、worker crash 或 session expiry 後的 fail-closed 對帳協議：先查持久化 session 與既有 video ID，再以只有該 authenticated channel 可見的 publish-key marker、時間窗、duration 與預期 metadata 尋找唯一遠端候選。唯一候選可採用、零候選且有 terminal non-creation evidence 才能新建、零或多個無法確定時進 shared blocker；不得自動再上傳或刪除候選。
_Avoid_: timeout 就重傳、靠 title 猜、找到多支挑最新、清理疑似 orphan、公開暴露內部 key

**Superseded Remote Revision**:
新版在 Delivery Review 被選為 Approved Deliverable 後，先前對應同一 Track Job、仍留在 YouTube 的舊 private video。它不再是目前交付版本並從 active Delivery Review 隱藏，但必須保持 private、保留完整 Publish Job／video ID 關聯，且不得由 workflow 自動刪除。
_Avoid_: 自動刪掉舊片、覆寫 YouTube 影片、把舊版誤當目前交付、未記錄的孤兒 upload

**Remote Cleanup Plan**:
針對 Superseded Remote Revisions 產生的不可覆寫批次刪除提案，逐筆列出 channel、video ID、Project／Track／render hash、目前可見性、取代它的 Approved Deliverable 與最新 Publish Verification。只有 Roy 對該批精確清單明確核准後才可永久刪除；新增或改變任何項目都必須建立新 plan 並重新核准。
_Avoid_: 依日期或搜尋結果批量刪除、wildcard cleanup、核准後偷加項目、把本機 Retention Plan 當成遠端刪除授權

**Channel Binding Profile**:
把 YouTube API client 與唯一預期 channel ID 綁定的版本化 Private Configuration；Production Worker 必須在每次上傳前以 OAuth 身分查得同一 ID，並在上傳回應後再次核對 channel ID、private visibility 與 `notifySubscribers=false`。任何不符都是共享驗證 blocker，不能靠帳號名稱、Brand Account default 或事後猜測繼續。
_Avoid_: 只記頻道名稱、相信 default channel、可上傳到任一 Roy 管理頻道、上傳後才人工找錯片

**Production Publisher Credential**:
Production Worker 用於自動 private 發布的最小 OAuth grant，只包含 `youtube.upload` 與 `youtube.readonly`，以 native OAuth／PKCE 取得 refresh token 並只存 macOS Keychain。它可以上傳、設縮圖、讀取頻道與驗證影片，但不能更新 metadata／visibility 或刪除影片。
_Avoid_: `youtube` 全權 token、repo 內的 client secret／refresh token、環境變數 bearer token、Discovery Browser cookies、可執行遠端刪除的背景 worker

**Privileged YouTube Executor**:
與 Production Worker 隔離的一次性高權限執行器；只有已核准的 Visibility Promotion 或 Remote Cleanup Plan 才能取得／使用獨立 `youtube.force-ssl` credential，並且只能操作核准 artifact 中的精確 channel／video IDs。它不是 Concert V1 private-upload 路徑的一部分，啟用 Visibility Promotion 前還必須完成適用的 YouTube API compliance audit。
_Avoid_: 把高權限 token 交給常駐 worker、核准一個動作卻能操作整個頻道、用 browser clicks 繞過 scope 隔離

**Channel Publish Profile**:
版本化的 Roy Customization，定義 private 上傳所需的 provisional 標題、說明、來源、演唱者／原唱、翻譯聲明、credits、hashtags 與縮圖生成規則。private metadata 可自動產生並隨連結交付預覽；要進行 Visibility Promotion 時，Roy 才核准當下正式文案與縮圖。
_Avoid_: 每首歌手填 metadata、private 文案就是公開定稿、無版本的 title prompt、先公開再補 credits

**Publish Verification**:
private 上傳後以 YouTube API 驗證處理、可見性、播放與地區限制，再以獨立唯讀 Studio session 檢查 copyright restrictions 的平台 QA。無限制為 PASS；Content ID claim 但實際可播放且只有追蹤／營利影響為 WARN；封鎖、靜音、下架、處理失敗或不可播放為 FAIL。流程不得自行申訴、裁切、靜音、換歌或刪除。
_Avoid_: 上傳完成就算可交付、claim 一律失敗、自動 dispute、用 Studio 編輯器改壞唯一遠端版本

**Visibility Promotion**:
把已驗證的 private 遠端影片明確提升為 unlisted 或 public 的發布決定。自動上傳本身不構成 Visibility Promotion。
_Avoid_: private 上傳等於發布、知道連結就算 unlisted、自動公開

**Retention Eligibility**:
Media Project 在自動品質通過、private Publish Job 已驗證且沒有未解決 Exception Review 後進入的可開始計算保留期限狀態。期限由 Project Manifest 的狀態事件決定，不由檔案 mtime、atime 或背景掃描推測。
_Avoid_: 檔案三十天沒打開、目錄最後修改時間、上傳指令成功就開始倒數

**Retention Class**:
Production Asset 的保存層級：可重建暫存保留 7 天、可替代大型媒體自 Retention Eligibility 起保留 30 天、專案真相與不可替代素材長期保留。類別由 manifest 記錄，不靠副檔名或所在資料夾猜測。
_Avoid_: 所有檔案一律三十天、看起來很大就刪、用檔名判斷可重建

**Retention Hold**:
明確暫停 Media Project 或特定 Production Asset 自動回收的狀態，直到 Roy 解除或指定期限到期。讀取或播放檔案本身不等於 Retention Hold。
_Avoid_: 最近開過所以保留、口頭可能還會用、永久停用回收器

**Retention Plan**:
在永久回收前列出精確資產路徑、hash、大小、Retention Class、理由與預計時間的不可覆寫 Evidence Artifact。它是刪除白名單與預告，不是以 wildcard 推測目標的掃描結果。
_Avoid_: rm 指令草稿、整個專案資料夾、依目錄年齡產生的候選

**Retention Tombstone**:
永久回收完成後保留的不可覆寫證據，記錄被刪資產、原 hash、時間、釋放空間、Retention Plan 與可否重新取得。Tombstone 不包含已刪媒體內容。
_Avoid_: 空資料夾、刪除成功訊息、可用來恢復的備份

**Storage Preflight**:
在下載、轉錄、分離音軌或渲染前，依工作估算與 RoyMedia hard floor 判斷能否安全開始的容量閘門。空間不足時只可提早淘汰可重建 cache；仍不足則停止新工作，不改存其他磁碟或縮短正式媒體期限。
_Avoid_: 跑到磁碟滿才失敗、自動改存內接碟、為了騰空間提前刪正式媒體

**Work Artifact**:
製作過程中可由來源與已記錄參數重新建立的中間產物。它可以支援除錯與續跑，但不是 Approved Deliverable，也不持有可跨專案重用的程式碼。
_Avoid_: 原始碼、Approved Deliverable

**Archived Revision**:
已被較新版本取代、但為了追溯與比較而保留的產物版本。它不是目前交付版本，且不得由檔案位置自行恢復成 Approved Deliverable。
_Avoid_: 備份 Repo、目前核准版本

**Legacy Media Project**:
採用舊目錄或舊狀態規則、已由標準 **Media Project** 取代但暫時完整保留的唯讀專案。它只用於遷移驗證與回復，不再接受新的製作修改。
_Avoid_: Archived Revision、目前 Media Project

**Production Data Root**:
集中保存所有 **Media Project**、共用大型資產與製作 cache 的唯一資料根目錄。它與 Roy AI Editor 的 canonical source checkout 分離。
_Avoid_: 程式碼 Repo、零散專案資料夾

**Recovery Vault**:
Dedicated Editor Host 內接碟上最多 10 GiB、加密且 hash-verified 的 restore-only 小型資料備份，保存 Project Manifest、核准、provenance、Roy Translation／Editing Notebooks、Preference Rules、timing／字幕、QA、Publish Job、profile 版本與回收紀錄，不保存影片、stems、renders、模型或 cache。它不是第二個 Production Data Root；正常流程不得從中讀寫狀態，只有明確的災難復原可以使用。
_Avoid_: 可切換的工作資料夾、內接碟媒體備份、另一份 current state、Git 內的私人備份

**Dedicated Editor Host**:
專門執行 Roy AI Editor、保存 canonical source checkout 並協調 Production Data Root 的 Apple Silicon Mac mini。它是目前唯一正式執行環境；其他電腦不各自維護互相分叉的生產狀態。
_Avoid_: WSL 主機、臨時剪輯電腦、另一份 source of truth

**Host Health Supervisor**:
獨立於 Production Worker、由 launchd 在開機、每六小時與 job 啟動前執行的健康監督器。它產生結構化 Host Health Snapshot，檢查 RoyMedia 實體身分／容量、pinned toolchain、models／fonts、worker／queue／manifests、browser profile、Keychain credential／channel binding、網路／API quota 與 Recovery Vault，並以 stage-specific readiness 決定只暫停真正受影響的工作。
_Avoid_: 只有人手執行的 doctor、任一 WARN 停掉整台機器、終端輸出就是健康紀錄、把 supervisor 跟可能故障的 worker 綁成同一 process

**Host Health Snapshot**:
Host Health Supervisor 產生的不可覆寫 Evidence Artifact，記錄各 capability 的 PASS／DEGRADED／BLOCKED、檢查版本、時間、證據、允許繼續的 stages、已嘗試自修與剩餘 recovery budget；不得包含 token、cookies 或其他秘密。
_Avoid_: 單一健康布林值、含 credentials 的 debug dump、只顯示紅燈沒有影響範圍、未版本化的 status page

**Safe Self-Healing Action**:
Host Health Supervisor 可在 recovery budget 內靜默執行、可重播且不改變 Roy 核准意圖的可逆修復：重啟 worker、從 checkpoint 續跑、退避重試、重建可再生 cache、回退 last-known-good toolchain，或執行本來就已符合精確規則的 Retention Plan。格式化磁碟、改 OAuth scope、刪除遠端影片、修改 Workflow Text Authority 或繞過存取控制永遠不屬於此類。
_Avoid_: doctor 自動修一切、未授權的 destructive repair、為了恢復服務改資料真相、browser login fallback

**Headless Production Core**:
不依賴 GUI 點擊即可從輸入、處理、渲染、QA 到 private 上傳完整重建的正式執行核心；由 macOS launchd 管理的 Production Worker 消費 Production Job Request，將每個 stage 以 idempotent checkpoint 寫回 Project Manifest。GUI 與桌面剪輯器可以提供檢視或 finishing，但不能承擔 job 存活或成為 Production Golden Path 的必要條件。
_Avoid_: UI automation 就是核心、Codex 對話 process 就是 worker、必須開啟某個剪輯 App、重啟後從頭跑

**Production Worker**:
Dedicated Editor Host 上由 launchd 管理的持久化 Headless Production Core 執行程序，負責領取 Production Job Request、取得單一 job lease、執行／重試 stages、續跑 checkpoint 並更新 Project Manifest。它不得把記憶體或終端輸出當成唯一狀態，也不得因重試重複下載、核准或上傳。
_Avoid_: 手動終端 session、Codex agent 回合、無 lease 的多重 runner、重啟即失憶的腳本

**Resource-Aware Scheduler**:
Production Worker 的資源仲裁器；Production Job Requests 可持續排隊，但同時只給一個 Media Project 大量下載、分離音軌或正式 render 的 heavy slot，場內 Track Jobs 則依 Dedicated Editor Host benchmarked CPU／GPU／RAM resource profile 平行。等待人工 gate 的 project 釋放 heavy slot，Storage Preflight 與 RoyMedia hard floor 永遠優先。
_Avoid_: 一次只能收一個 URL、每首歌完全序列執行、無限制多場並行、為了併發縮短 Retention Class

**Production Toolchain**:
Dedicated Editor Host 上由 repo bootstrap、doctor 與版本證據管理的必要執行工具集合。未列入此集合的 GUI、模型或外部工具不得被流程暗中當成必要依賴。
_Avoid_: 這台機器剛好有的工具、手動安裝清單、未記錄版本的執行環境

**Production Toolchain Release**:
可重建、不可變且有版本號的正式工具環境，鎖定程式碼、Brew／Python／browser 依賴、字型、模型與 profile 的精確版本／checksum，並保存 corpus、host smoke、rollback 與相容性證據。每個 Production Job Request 釘選一個 release；job 執行途中不得被 `latest` 或系統升級悄悄改變。
_Avoid_: production 直接 `brew upgrade`、runtime `pip install`、浮動 model tag、只記 major version、同一 job 中途換環境

**Maintenance Train**:
每週自動發現 upstream、依賴、模型與安全更新，通常按月整批建立候選 Production Toolchain Release 的維護節奏；重大安全修補可立即建立候選，但仍須通過 CI、完整 Concert Golden Corpus、Dedicated Editor Host smoke、重啟續跑與 rollback 演練。它不直接修改正在工作的 release。
_Avoid_: 每個套件各自打斷 Roy、偵測到更新就部署、跳過 corpus 的緊急升級、production branch 直接 pull upstream

**Toolchain Promotion Review**:
候選 Production Toolchain Release 會改變文字、timing、字幕像素、媒體編碼、模型判斷或其他受治理輸出時，集中呈現新舊 A/B、metric 差異、風險與 rollback 的單次維護核准。只有正規化輸出等價、完整測試全綠且沒有擴大 capability／scope 的維護版可自動升格。
_Avoid_: 每次 patch 都問 Roy、輸出變了卻靜默升級、只看單支影片、沒有 rollback 的 promotion

**Concert V1 Quality Registry**:
在候選工具或 acceptance 結果產生前版本化、釘選於 Production Toolchain Release 與 Render Manifest 的量化品質契約，定義 fixture 母體、timing／ruby／pixel／browser／publish／resource 門檻、normalized-output 等價規則與 failure-degradation。看過結果後要放寬門檻必須建立新 registry version、留下決策理由並完整重跑，不能改寫原結果。
_Avoid_: 文件寫「95%」但沒有分母、跑完才調門檻、每次測試換 corpus、只報平均、口頭定義等價

**Production Asset**:
Media Project 使用或產生的真實影片、音訊、歌詞、翻譯、字幕、截圖、模型與其他製作資料。Production Asset 留在大型媒體儲存空間，不進入程式碼版控。
_Avoid_: Test Fixture、原始碼

**Test Fixture**:
用來重現與驗證行為的小型、可公開、無私人或授權疑慮的合成資料。Test Fixture 是程式碼品質契約的一部分，可以跟隨程式碼版控。
_Avoid_: 真實製作素材、Production Asset

## Example dialogue

> **Roy**：這次九支 Live 成片累積的對軸和振假名修正，要留下來給下一場使用。
> **Developer**：我會把可重用部分整理成 Roy Customization，讓 Concert Live Workflow 使用它，而不是把做法留在單一影片專案裡。
> **Roy**：那 Hao 的 Repo 呢？
> **Developer**：它是 Upstream Foundation；Roy AI Editor 站在它上面繼續擴充，而不是在旁邊另做一套互不相干的工具。
> **Roy**：我的客製設定都要推到公開 GitHub 嗎？
> **Developer**：可安全重用的部分是 Public Customization；credentials、私人資訊與受限制內容留在 Private Configuration 或 Production Assets。
>
> **Roy**：九支成片和測試素材都要放外接碟嗎？
> **Developer**：九支成片屬於 Production Asset，留在 RoyMedia 的 Media Project；只有小型、合成且可安全公開的 Test Fixture 跟著 Dedicated Editor Host 上的程式碼版控。
> **Roy**：下一場 Live 可以直接放在外接碟根目錄嗎？
> **Developer**：所有 Media Project 都進同一個 Production Data Root，不再讓程式預設路徑與實際專案位置分叉。
> **Roy**：QA 報告說完成，但 project.json 還顯示 pending，要看哪個？
> **Developer**：Project Manifest 是目前狀態的唯一真相；QA 報告是它引用的 Evidence Artifact，兩者不再各自維護狀態。
> **Roy**：檔名有 `final`，所以它就是可上傳版本嗎？
> **Developer**：不一定。只有 Project Manifest 選定且 Roy 核准的版本是 Approved Deliverable；舊版是 Archived Revision，中間檔是 Work Artifact。
> **Roy**：整理完成後，原本亂掉的專案可以直接刪除嗎？
> **Developer**：不行。先把它保留為 Legacy Media Project，等新專案的數量、大小、hash、Manifest 與 Approved Deliverable 全部驗證通過後，再另行核准退役。
