# Roy AI Editor

Roy AI Editor 是建立在既有開源影片製作框架之上的專屬 AI 剪輯師。它以 Roy 的品味、素材、工作方式與核准責任為中心，逐步支援多種影片製作情境。

## Language

**Roy AI Editor**:
Roy 的專屬 AI 剪輯師產品；以 **Upstream Foundation** 為起點，再加入 Roy 自己的能力、偏好與 **Editing Workflow**。
_Avoid_: 卡拉 OK 工具、vendored toolkit

**Upstream Foundation**:
Roy AI Editor 所建立其上的 `Hao0321/video-autopilot-kit` 開源框架。它是產品的基礎，不是擺在旁邊、可有可無的參考快照。
_Avoid_: 參考 Repo、被動 vendor、獨立工具包

**Roy Customization**:
讓 **Upstream Foundation** 成為 Roy 專屬剪輯師的能力、偏好、知識與工作流程。它應能被重複使用與持續改進，而不是只服務單一影片的一次性做法。
_Avoid_: 臨時腳本、專案特例

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

**Media Project**:
一次影片製作工作的完整資料集合，包含輸入、核准資料、中間產物、品質證據與交付成品。Media Project 不持有可跨專案重用的程式碼。
_Avoid_: 程式碼 Repo、Editing Workflow

**Project Manifest**:
一個 **Media Project** 目前狀態的唯一真相，記錄曲目、階段、核准狀態與各項 **Evidence Artifact** 的引用。其他報告不得各自宣稱不同的專案狀態。
_Avoid_: 最終交付報告、零散狀態檔

**Evidence Artifact**:
某次處理、檢查或核准所留下的不可覆寫證據，由 **Project Manifest** 引用。它證明發生過什麼，但不單獨決定 Media Project 的目前狀態。
_Avoid_: Project Manifest、可反覆覆寫的暫存檔

**Approved Deliverable**:
已通過 Roy 核准並由 **Project Manifest** 選定為目前交付版本的影片、字幕或發布資產。檔名含有 `final`、`approved` 或版本號本身不構成核准。
_Avoid_: final 檔案、最新修改檔、review 版本

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
> **Roy**：九支成片和測試素材都要放 D 槽嗎？
> **Developer**：九支成片屬於 Production Asset，留在 D 槽的 Media Project；只有小型、合成且可安全公開的 Test Fixture 跟著 WSL 程式碼版控。
> **Roy**：下一場 Live 可以直接放在 D 槽根目錄嗎？
> **Developer**：所有 Media Project 都進同一個 Production Data Root，不再讓程式預設路徑與實際專案位置分叉。
> **Roy**：QA 報告說完成，但 project.json 還顯示 pending，要看哪個？
> **Developer**：Project Manifest 是目前狀態的唯一真相；QA 報告是它引用的 Evidence Artifact，兩者不再各自維護狀態。
> **Roy**：檔名有 `final`，所以它就是可上傳版本嗎？
> **Developer**：不一定。只有 Project Manifest 選定且 Roy 核准的版本是 Approved Deliverable；舊版是 Archived Revision，中間檔是 Work Artifact。
> **Roy**：整理完成後，原本亂掉的專案可以直接刪除嗎？
> **Developer**：不行。先把它保留為 Legacy Media Project，等新專案的數量、大小、hash、Manifest 與 Approved Deliverable 全部驗證通過後，再另行核准退役。
