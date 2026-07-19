---
status: accepted
---

# Use Exception Review after lyrics approval

Concert Live Workflow 採用 Exception Review，而不是在每個階段固定停下來。Roy 主動提交來源 URL 即建立只涵蓋本機處理與 private 上傳的 Intake Authorization；Rights Audit 自動研究來源與曲目證據，明確禁止或需要繞過存取控制時停止，只有矛盾、不確定或缺少可支持結論的證據時才要求 Roy 介入。每首歌的日文原詞、來源譯文或明確標記的獨立 AI 繁中草稿、performed repeats 與 line map 組成獨立版本化 Lyrics Packet，但所有 Track Selection 的 packets 要合併為一次 Concert Lyrics Review，是初期唯一固定製作核准點。Roy 可一次全數通過或只指出歌曲／行號；當完整 review 是唯一待處理 gate 時，緊接其後的 `ok` 明確綁定並核准當下顯示的 review 版本與 packet hashes，不要求手打固定句型。修改時只使受影響 packet 失效，不重審未變更歌曲。找不到可重用繁中譯文時，流程在保存失敗查詢後自動產生有來源證據與不確定標記的獨立草稿，不另拆逐句詢問。Roy 核准精確 packets 後，對軸、字幕、渲染、逐行 Burned-Pixel Review 與影音 QA 可以在 Automated Quality Verdict 通過時自動前進；全部取得 PASS 的成片成為 Verified Render，無需另一個固定人工成片核准即可自動上傳 private。任何來源或文字變更、低信心歌手／切點、QA WARN／FAIL 都觸發 Exception Review；Track Job 層級的例外先暫停自己並累積到 Exception Digest，等其他可自動工作完成後一次呈現，只有阻塞整場的共享驗證、憑證或 Storage Preflight 問題立即通知。自動檢查不得記成 Roy 人工核准，Verified Render 也不得冒充 Approved Deliverable。Roy 看過 private 連結後可以另行選定 Approved Deliverable，unlisted／public Visibility Promotion 永遠需要明確決定。
