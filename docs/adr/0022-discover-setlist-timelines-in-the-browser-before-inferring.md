---
status: accepted
---

# Discover setlist timelines in the browser before inferring

Concert Live Workflow 只收到 YouTube URL 也必須能啟動；系統先以隔離的 browser session 執行 Timeline Discovery，實際打開影片並依序檢查章節、說明欄、創作者／置頂／高可信留言，保存 permalink、作者、文字、擷取時間與截圖作為 Setlist Timeline Evidence。Roy 提供的 Provided Setlist Timeline 仍是最高優先證據，但不是必要輸入。只有找不到可信時間軸時才以音訊、畫面、歌詞與 ASR 推測曲目，且不論來源為何，留言時間都只是 Boundary Anchor，正式首尾仍須經媒體訊號驗證。登入、人機驗證與存取控制不得被繞過；無法自動取得且影響 Track Selection 時才進入 Exception Review。
