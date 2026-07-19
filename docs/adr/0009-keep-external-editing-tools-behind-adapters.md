---
status: accepted
---

# Keep external editing tools behind adapters

BaoCut、VideoLingo、auto-editor 與未來其他第三方剪輯能力只透過 External Capability Adapter 接入 Roy AI Editor，不成為第二個 Upstream Foundation，也不接管 Project Manifest、核准狀態、正式時間線或 Production Data Root。這保留使用原生 Mac 工具與快速吸收外部能力的效率，同時避免封閉 binary、私有 project store、provider 行為或版本漂移綁死 Roy 的 Media Projects；外部結果必須轉成 Roy 自有 Work Artifact、Evidence Artifact 或 Edit Plan，並通過獨立 QA。任何候選在安裝為正式依賴前都必須通過有預註冊品質、headless／Apple Silicon、資源、失敗降級、license、版本與 artifact 契約門檻的 Production Capability Spike；單一 demo 或「能跑」不能升格。BaoCut 目前只保留為未來口播／訪談 Workflow 的 optional adapter 候選，不能進入 Concert Live 的核准歌詞至卡拉 OK 正式路徑。
