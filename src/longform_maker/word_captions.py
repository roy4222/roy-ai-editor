# -*- coding: utf-8 -*-
"""longform_maker/word_captions.py — word-level caption timing, the mechanical default (M105).

Why this exists: hand-splitting whisper's coarse *segments* into caption lines
drifts 2-3 s by mid-video (a real shipped-and-caught failure). The iron rule:

  Caption line timing = whisper `word_timestamps` (real word-level times),
  auto line-broken. Never guess split points on coarse segments.
  Times come from whisper; text goes through regex fixes — the two never mix.

Usage (import into your build script, zero copy-paste):
  from longform_maker.word_captions import transcribe_words, group_words, to_master_events, build_ass
  words = transcribe_words("beat3.wav")                    # [(s,e,word),...]
  lines = group_words(words, fixes=MY_FIXES)               # [(s,e,text),...] real times + fixed text
  evs   = to_master_events({"b3": lines}, offsets, trims)  # events on the master timeline
  build_ass(evs, "master.ass")

Self-test: `python word_captions.py` (pure line-break logic + a real ffmpeg
subtitle burn). Subprocess capture always uses encoding='utf-8' (cp950-safe, M102).
"""
import os, re, subprocess, sys
for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8")
    except Exception: pass

# 行尾懸掛字（斷在這些字後面 = 片語被腰斬，讀起來卡）→ 斷行點會避開
DANGLERS = set("的了也就才把去和跟在是有我你他很而且然後到個一二兩三")
# 行首懸掛字（下一行用這些字開頭 = 上一行被腰斬）→ 不在這些字前斷
HEAD_DANGLERS = set("了的地得個們嗎呢吧啦")
# 連接詞 token 不掛行尾（「…結論所以」這種）
TAIL_DANGLER_TOKENS = {"所以", "而且", "然後", "但是", "因為", "就是", "甚至", "如果", "但"}
# 常見雙字詞禁拆（斷點兩側字拼起來是這些詞 = 腰斬）。實剪抓到的常見案例整理成 default，
# 專案可自行擴充：`word_captions.NEVER_SPLIT |= {"你的", "詞"}`。
NEVER_SPLIT = {"完整", "下去", "抽卡", "觀念", "作為", "交流", "半成", "成品", "上架", "禮拜",
               "實驗", "訂閱", "引擎", "程度", "結論", "推測", "期待", "教學", "社群", "立繪",
               "美術", "戰鬥", "遊戲", "挑戰", "分享", "留言", "影片", "東西", "部分", "方向",
               "地方", "時候", "小時", "功能", "簡單", "震撼", "誤會", "藍圖", "程式", "工具",
               "角色", "老實", "實說", "打開", "開過", "自己", "大概", "大堆", "什麼"}

# 常見 whisper 誤聽 → 正字。這裡只放【通用】修正（工具名/品牌名/字幕組幻覺）；
# 你自己的口音/題材專屬誤聽請用 fixes= 參數疊加：group_words(words, fixes=[(r"...", "...")])。
# ⚠ 修正套在【字級、斷行前】(apply_fixes_to_words) —— 實剪教訓：逐行修會被斷行拆散
#   （「Cloud」「Code」被斷到兩行，r"Cloud\s*Code" 兩行都 match 不到 → 錯字出貨）。
BASE_FIXES = [
    (r"Cloud\s*Code", "Claude Code"), (r"cloud\s*code", "Claude Code"),
    (r"游戏", "遊戲"),
    (r"Apple\s*Store", "App Store"), (r"AppleStore", "App Store"),
    (r"\bC\s*ode\b", "Code"), (r"G\s*P\s*T", "GPT"), (r"U\s*I", "UI"),
    (r"字幕by\S*", ""), (r"字幕組\S*", ""),   # whisper 訓練資料殘留的字幕組 credit 幻覺
]


def apply_fixes_to_words(words, fixes=None):
    """字級修正（M105 核心防線）：在【斷行前】對整個 beat 的連續文字跑 regex，
    match 到的字區間合併成一個修正後的 word（start=首字 start、end=末字 end）。
    這樣誤聽跨 word（Cloud|Code）或跨未來斷行位置都修得到、拆不散。空替換 = 刪除（幻覺字串）。"""
    allf = list(BASE_FIXES) + list(fixes or [])
    ws = [(s, e, t) for s, e, t in words]
    for pat, rep in allf:
        search_from = 0          # 已處理到的字符位置（防冪等 pattern 如 GPT→GPT 無限迴圈）
        for _guard in range(200):
            joined = "".join(t for _, _, t in ws)
            cidx = [wi for wi, (_, _, t) in enumerate(ws) for _ in t]
            m = re.search(pat, joined[search_from:])
            if not m or not cidx:
                break
            a = search_from + m.start()
            b = max(a, search_from + m.end() - 1)
            if a >= len(cidx):
                break
            w1, w2 = cidx[a], cidx[min(b, len(cidx) - 1)]
            merged_txt = "".join(t for _, _, t in ws[w1:w2 + 1])
            new_txt = re.sub(pat, rep, merged_txt, count=1)
            if new_txt == merged_txt:            # 已是正字（冪等）→ 跳過這個 match 繼續往後找
                search_from = a + max(1, m.end() - m.start())
                continue
            repl = [] if not new_txt.strip() else [(ws[w1][0], ws[w2][1], new_txt)]
            ws = ws[:w1] + repl + ws[w2 + 1:]
            # 下一輪從被替換區之後找起（替換文字長度可能不同 → 用 w1 前綴長 + 新字長）
            search_from = len("".join(t for _, _, t in ws[:w1])) + len(new_txt)
    return ws


def transcribe_words(wav, model_size="small", language="zh", model=None):
    """單檔 → [(start,end,word),...]（faster_whisper word_timestamps）。可傳入共用 model 免重載。"""
    from faster_whisper import WhisperModel
    m = model or WhisperModel(model_size, device="cpu", compute_type="int8")
    segs, _ = m.transcribe(str(wav), language=language, vad_filter=True, word_timestamps=True)
    out = []
    for s in segs:
        for w in (s.words or []):
            out.append((round(w.start, 3), round(w.end, 3), w.word))
    return out


def _cjklen(s):
    return len(re.sub(r"\s", "", s))


def fix_text(t, fixes=None):
    """套誤聽修正 + 清空格/標點（M68 白字乾淨版）。時間不動，只動文字。"""
    t = t.strip()
    for pat, rep in (list(BASE_FIXES) + list(fixes or [])):
        t = re.sub(pat, rep, t)
    t = re.sub(r"\s+", " ", t)
    t = re.sub(r"([一-鿿])\s+([一-鿿])", r"\1\2", t)
    t = re.sub(r"\s*([，。、！？：；,!?])\s*", "", t)
    return t.strip()


def group_words(words, max_chars=15, hard_gap=0.42, soft_gap=0.28, soft_len=9, fixes=None,
                min_break_gap=0.06, overflow=3):
    """字級時間 →字幕行 [(start,end,text)]。
       ⓪ 先跑 apply_fixes_to_words()（字級修正，斷行拆不散 —— M105 防線）
       ①真實停頓斷行（gap>hard_gap；或已 soft_len 字且 gap>soft_gap）
       ②長度爆了(>max_chars) → 回溯到【合格斷點】：不拆 NEVER_SPLIT 複合詞、
         下一行不用 HEAD_DANGLERS(了/的…) 開頭、連接詞(所以/而且…)不掛行尾、
         gap≥min_break_gap 或前 token 拉長(≥0.45s = whisper 把停頓吃進 token)。
         連續快講沒合格點 → 容忍 overflow 字再放寬、最後不得已才最大 gap 硬斷。
       行時間 = 首字 start / 末字 end（全真實時間，M105 核心）。實剪抓到的失敗模式：
       完|整、花|了、功能|的、做|下去、結論+所以 —— 全部由上面規則擋。"""
    words = apply_fixes_to_words(words, fixes)
    lines, buf = [], []   # buf: [(s,e,w)]

    def flush(upto=None):
        nonlocal buf
        take = buf if upto is None else buf[:upto + 1]
        rest = [] if upto is None else buf[upto + 1:]
        if take:
            txt = fix_text("".join(x[2] for x in take), fixes)
            if txt:
                lines.append((take[0][0], take[-1][1], txt))
        buf = rest

    def _eligible(j):
        a = buf[j][2].strip(); b = buf[j + 1][2].strip()
        if not a or not b:
            return False
        if a[-1] + b[0] in NEVER_SPLIT:      # 複合詞腰斬
            return False
        if re.match(r"[A-Za-z]", b[0]) and re.search(r"[A-Za-z]$", a):
            return False                     # 拉丁字互拆（Un|real、App|Store）
        if b[0] in HEAD_DANGLERS:            # 下一行以 了/的… 開頭
            return False
        if a in TAIL_DANGLER_TOKENS:         # 連接詞掛行尾
            return False
        return _cjklen("".join(x[2] for x in buf[:j + 1])) >= 4

    def best_break(require_gap, strict=True):
        best, best_score = None, -1.0
        for j in range(len(buf) - 1):
            g = buf[j + 1][0] - buf[j][1]
            dur_next = buf[j + 1][1] - buf[j + 1][0]
            # 停頓常被 whisper 吸進【下一個 token 的開頭】→ 下一 token 拉長 = 這裡有停頓。
            # （曾誤用「當前 token 拉長」→ 角(0.54s)|色 被當斷點腰斬，實剪抓到）
            pseudo = g + (0.15 if dur_next >= 0.50 else 0.0)
            if pseudo < require_gap:
                continue
            if strict and not _eligible(j):
                continue
            tail = buf[j][2].strip()[-1:] if buf[j][2].strip() else ""
            score = pseudo - (0.25 if tail in DANGLERS else 0.0)
            if score >= best_score and _cjklen("".join(x[2] for x in buf[:j + 1])) >= 4:
                best, best_score = j, score
        return best

    for i, (s, e, w) in enumerate(words):
        buf.append((s, e, w))
        gap_next = (words[i + 1][0] - e) if i + 1 < len(words) else 99.0
        cur_len = _cjklen("".join(x[2] for x in buf))
        if gap_next > hard_gap or (cur_len >= soft_len and gap_next > soft_gap):
            flush()
        elif cur_len > max_chars:
            b = best_break(min_break_gap, strict=True)
            if b is not None:
                flush(b)
            elif cur_len > max_chars + overflow:
                # 連讀太長：先放寬 gap 但仍守合格性 → 再不行才無限制最大 gap
                b2 = best_break(0.0, strict=True)
                if b2 is None:
                    b2 = best_break(0.0, strict=False)
                flush(b2 if b2 is not None else len(buf) - 2)
    flush()
    return lines


def to_master_events(beat_lines, offsets, trims, hold=0.6, min_show=0.30):
    """beat 內真實時間 → master 時間軸事件。
       beat_lines={bk:[(s,e,text)]}（beat 原始秒）；offsets=narration offsets dict（含 _speed）；
       trims={bk: beat 被 voice chain 剪掉的頭秒數}。
       s_master = beat_start + (s-trim)/SP；end 撐到下一行開始前(hold 上限)不留字幕盒閃爍空檔（M93）。"""
    sp = float(offsets.get("_speed", 1.0))
    evs = []
    for bk, lines in beat_lines.items():
        off, dur, tr = offsets[bk]["start"], offsets[bk]["dur"], trims[bk]
        for j, (rs, re_, txt) in enumerate(lines):
            s = max(off, off + (rs - tr) / sp)
            e = off + (re_ - tr) / sp
            if j + 1 < len(lines):
                nxt = off + (lines[j + 1][0] - tr) / sp
                e = min(nxt - 0.02, e + hold)
            e = min(off + dur + 0.25, e)
            if e - s >= min_show:
                evs.append((round(s, 3), round(e, 3), txt))
    evs.sort()
    return evs


# ─────────────────────────────────── 每句 ≤1 關鍵詞變重（white-first/M68 守則）
# 詞表順序 = 命中優先序（前面的先中）。專案可直接覆寫模組級 EMPHASIS_TERMS
# 或傳 emphasize_line(text, terms=[...])。
EMPHASIS_TERMS = [
    # 工具名
    "Claude", "ChatGPT", "ffmpeg", "GitHub", "Unreal", "CapCut", "AI",
    # 結論動詞/名詞類
    "爆款", "演算法", "開源", "營利", "收益", "觸及", "互動", "瀏覽", "規則", "公式",
]
# 金色 RGB(255,210,63) → ASS BGR=&H3FD2FF&；結尾 reset 回白（white-first：只重點上色）
EMPH_TAG = r"{\fscx112\fscy112\c&H3FD2FF&}"
EMPH_RESET = r"{\fscx100\fscy100\c&HFFFFFF&}"
# 阿拉伯數字+單位（e.g. 12萬 / 56.7% / $12.34 / 1,234,567）＝關鍵詞，優先於詞表
_NUM_KEY_RE = re.compile(r"[0-9][0-9,\.]*(?:%|萬|億|美金)?|\$[0-9][0-9,\.]*")
_HAS_INLINE_TAG = re.compile(r"\{\\")   # 已含 inline ASS tag → 防重入


def emphasize_line(text, terms=None, max_hits=1):
    """把該句「第一個命中的關鍵詞」包上金色放大 tag（每句最多 max_hits=1 個）。
    優先序：阿拉伯數字+單位 > 詞表順序。整句已含 inline ASS tag → 原樣返回（防重入）。
    含 \\N 的多行文字也視為一「句」，整句仍只變重 1 個詞。"""
    if not text or max_hits <= 0 or _HAS_INLINE_TAG.search(text):
        return text
    spans = []

    def _free(a, b):
        return all(b <= s or a >= e for s, e in spans)

    for m in _NUM_KEY_RE.finditer(text):          # ① 數字+單位優先
        if len(spans) >= max_hits:
            break
        if _free(m.start(), m.end()):
            spans.append((m.start(), m.end()))
    if len(spans) < max_hits:                     # ② 詞表順序=優先序
        for term in (EMPHASIS_TERMS if terms is None else terms):
            if len(spans) >= max_hits:
                break
            i = text.find(term)
            if i >= 0 and _free(i, i + len(term)):
                spans.append((i, i + len(term)))
    for a, b in sorted(spans, reverse=True):      # 右往左包，index 不位移
        text = text[:a] + EMPH_TAG + text[a:b] + EMPH_RESET + text[b:]
    return text


def chapter_card_tag():
    """章節卡 blur-in 前綴 tag（0.28s 從模糊全透明入場）。
    給呼叫端自行 prepend 到章節卡 Dialogue 文字前，build_ass 不自動加。"""
    return r"{\blur16\alpha&HFF&\t(0,280,\blur0\alpha&H00&)}"


def _ass_fontname() -> str:
    """ASS Style 的 Fontname（libass 用字型「家族名」不是檔案路徑）。
    Windows 維持微軟正黑（行為不變）；Mac 用 PingFang TC（家族名走 CoreText 解析，
    不受 macOS 15 Sequoia PingFang.ttc 檔案搬家影響）；Linux 用 Noto Sans CJK TC。"""
    import sys as _sys
    if _sys.platform == "win32":
        return "Microsoft JhengHei"
    if _sys.platform == "darwin":
        return "PingFang TC"
    return "Noto Sans CJK TC"


ASS_HEAD = ("[Script Info]\nScriptType: v4.00+\nPlayResX: 1920\nPlayResY: 1080\nWrapStyle: 0\n"
            "ScaledBorderAndShadow: yes\n\n[V4+ Styles]\n"
            "Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour, Bold, Italic, "
            "Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
            "Alignment, MarginL, MarginR, MarginV, Encoding\n"
            # M68：教學長片 = 白字 + 黑色半透明底框，不多色
            f"Style: Cap,{_ass_fontname()},82,&H00FFFFFF,&H4D000000,&H00000000,-1,0,0,0,100,100,0.5,0,3,16,0,2,200,200,96,1\n\n"
            "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")


def _ts(t):
    h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def build_ass(events, out_path, fade=(90, 60), emphasize=False):
    """events=[(s,e,text)] → M68 白字黑框 ASS。回傳寫入行數。
    emphasize=True：每個 Dialogue 行文字先過 emphasize_line()（整行含 \\N 也只變重 1 詞；
    在 \\fad 前處理，caller 自帶 tag 的行防重入不動）。預設 False = 行為完全不變。"""
    ev = []
    for s, e, t in events:
        txt = emphasize_line(t) if emphasize else t
        ev.append(f"Dialogue: 0,{_ts(s)},{_ts(e)},Cap,,0,0,0,,{{\\fad({fade[0]},{fade[1]})}}{txt}")
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(ASS_HEAD + "\n".join(ev) + "\n")
    return len(ev)


# ──────────────────────────────────────────── self-test
if __name__ == "__main__":
    # 1) line-breaking pure function: length-overflow must back-track past dangler chars
    w = []
    t = 0.0
    for ch, gap in [("你可以", .02), ("看到", .05), ("戰鬥", .02), ("可以", .02), ("打", .30),
                    ("抽卡", .02), ("會", .02), ("跳", .30), ("角色", .02), ("立繪", .02),
                    ("也", .02), ("都", .02), ("進去了", .8), ("後面", .02), ("繼續", .02)]:
        w.append((round(t, 2), round(t + 0.2, 2), ch)); t += 0.2 + gap
    lines = group_words(w, max_chars=10)
    joined = [x[2] for x in lines]
    assert not any(l.endswith(("也", "的", "去", "一")) for l in joined[:-1]), f"dangler not avoided: {joined}"
    assert all(_cjklen(l) <= 13 for l in joined), f"line too long: {joined}"
    # line time must equal real word time (first-word start)
    assert abs(lines[0][0] - w[0][0]) < 1e-6, "line start is not real first-word time"

    # 2) mishear fixes (per-line path)
    assert "Claude Code" in fix_text("全部交給 Cloud Code 幫我寫C ode"), "FIX not applied"

    # 2b) word-level fixes survive line-breaking (shipped-bug regression):
    #     Cloud|Code spans two words AND a would-be break point
    w2 = [(0.0, 0.3, "全部"), (0.3, 0.6, "交給"), (0.6, 0.9, "Cloud"), (0.9, 1.3, " Code"),
          (1.3, 1.6, "幫我"), (1.6, 1.9, "寫"), (1.9, 2.2, "Code"), (2.2, 2.5, "美術圖"),
          (2.5, 2.8, "我就"), (2.8, 3.1, "用"), (3.1, 3.4, "GPT"), (3.4, 3.7, "來生")]
    fixed = apply_fixes_to_words(w2)
    jt = "".join(t for _, _, t in fixed)
    assert "Claude Code" in jt and "Cloud" not in jt, f"word-level fix failed: {jt}"
    g2 = group_words(w2, max_chars=8)   # force breaks -> Claude Code must stay on one line
    assert any("Claude Code" in l[2] for l in g2), f"Claude Code split across lines: {[l[2] for l in g2]}"
    assert not any(("Cloud" in l[2] and "Claude" not in l[2]) for l in g2), f"Cloud residue: {[l[2] for l in g2]}"

    # 2c) whisper hallucinated subtitle-group credit removal
    w3 = [(0.0, 0.3, "App"), (0.3, 0.6, " Store"), (0.6, 0.9, "的"), (0.9, 1.2, "程度"),
          (1.2, 1.5, "字幕by"), (1.5, 1.8, "某某組")]
    g3 = group_words(w3)
    assert all("字幕by" not in l[2] for l in g3), f"hallucinated credit not removed: {[l[2] for l in g3]}"

    # 2d) run-together compound (gap~0, e.g. 抽|卡) must not become a break point
    w4 = []
    tt = 0.0
    for ch, gap in [("你可以", .02), ("看到", .20), ("戰鬥", .02), ("可以打", .20),
                    ("抽", .00), ("卡", .02), ("會跳", .20), ("角色", .02), ("立繪", .02), ("進去了", .5)]:
        w4.append((round(tt, 2), round(tt + 0.2, 2), ch)); tt += 0.2 + gap
    g4 = group_words(w4, max_chars=7)
    for l in g4:
        assert not l[2].endswith("抽"), f"run-together word split: {[x[2] for x in g4]}"

    # 2e) production regressions: never split 完|整, no line starting with 了, no trailing 所以
    w5 = []
    tt = 0.0
    for ch, gap in [("比我", .05), ("一開始", .03), ("想的", .08), ("還要", .02), ("完", .00),
                    ("整", .02), ("的", .02), ("很多", .40), ("我大概", .03), ("只花", .02),
                    ("了", .02), ("一個", .02), ("禮拜", .30)]:
        w5.append((round(tt, 2), round(tt + 0.2, 2), ch)); tt += 0.2 + gap
    g5 = group_words(w5, max_chars=8)
    for li, l in enumerate(g5):
        assert not l[2].endswith("完"), f"完|整 split: {[x[2] for x in g5]}"
        if li > 0:
            assert not l[2].startswith("了"), f"line starts with 了: {[x[2] for x in g5]}"
    w6 = []
    tt = 0.0
    for ch, gap in [("不是", .03), ("已經", .02), ("成功的", .03), ("結論", .06), ("所以", .02),
                    ("大家", .02), ("先不要", .03), ("誤會", .5)]:
        w6.append((round(tt, 2), round(tt + 0.2, 2), ch)); tt += 0.2 + gap
    g6 = group_words(w6, max_chars=8)
    for l in g6[:-1]:
        assert not l[2].endswith("所以"), f"connective at line end: {[x[2] for x in g6]}"

    # 3) master-timeline conversion: SPEED sync (M103)
    off = {"b1": {"start": 10.0, "dur": 5.0}, "_speed": 1.06}
    evs = to_master_events({"b1": [(1.0, 2.0, "第一句"), (2.5, 3.5, "第二句")]}, off, {"b1": 0.5})
    assert abs(evs[0][0] - (10 + 0.5 / 1.06)) < 0.01, "master start /SP wrong"
    assert evs[0][1] <= evs[1][0], "lines overlap"

    # 3b) emphasize_line regression (<=1 keyword per line, number-first, re-entry safe)
    _G, _R = EMPH_TAG, EMPH_RESET
    ea = emphasize_line("我用 Claude 做了一個 AI")
    assert ea == "我用 " + _G + "Claude" + _R + " 做了一個 AI", "emphasize: only Claude wrapped + reset expected"
    assert ea.count(_G) == 1 and ea.count(_R) == 1, "emphasize: exactly 1 wrap"
    eb = emphasize_line("衝到 123萬 瀏覽")
    assert eb == "衝到 " + _G + "123萬" + _R + " 瀏覽", "emphasize: number-first priority failed"
    ec_in = r"已含 {\c&H3FD2FF&}上色{\c&HFFFFFF&} 的行"
    assert emphasize_line(ec_in) == ec_in, "emphasize: pre-tagged line must pass through unchanged"
    ed = emphasize_line("Claude 和 GitHub 都很強")
    assert ed.count(_G) == 1 and (_G + "Claude") in ed and (_G + "GitHub") not in ed, \
        "emphasize: max_hits=1 must wrap first term only"
    en = emphasize_line("用 GitHub 開源\\N演算法推薦")
    assert en.count(_G) == 1, "emphasize: line with \\N must still get only 1 wrap"
    assert emphasize_line("$12.34 收益") == _G + "$12.34" + _R + " 收益", "emphasize: $-amount failed"
    assert emphasize_line("56.7% 互動率").startswith(_G + "56.7%" + _R), "emphasize: percent failed"
    assert chapter_card_tag() == r"{\blur16\alpha&HFF&\t(0,280,\blur0\alpha&H00&)}", "chapter_card_tag mismatch"

    # 4) real ffmpeg subtitle burn (M97)
    import tempfile, shutil
    work = tempfile.mkdtemp(prefix="wordcap_selftest_")
    try:
        ass = os.path.join(work, "t.ass")
        n = build_ass([(0.2, 1.4, "測試字幕一"), (1.5, 2.6, "測試字幕二")], ass)
        assert n == 2
        src = os.path.join(work, "c.mp4")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi",
                        "-i", "color=c=navy:s=640x360:r=30:d=3",
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", src],
                       capture_output=True, encoding="utf-8", errors="replace")
        r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", "c.mp4", "-vf", "ass=t.ass",
                            "-frames:v", "60", "-f", "null", "-"],
                           cwd=work, capture_output=True, encoding="utf-8", errors="replace")
        assert r.returncode == 0, "ASS burn failed:" + (r.stderr or "")[-300:]
        # 4b) build_ass(emphasize=True): exactly 1 gold tag + 1 reset per line; default path tag-free
        ass_e = os.path.join(work, "e.ass")
        n2 = build_ass([(0.2, 1.4, "我用 Claude 做工具"), (1.5, 2.6, "衝到 123萬 瀏覽")],
                       ass_e, emphasize=True)
        assert n2 == 2
        with open(ass_e, encoding="utf-8") as fh:
            body_e = fh.read()
        assert body_e.count(r"\c&H3FD2FF&") == 2 and body_e.count(r"\c&HFFFFFF&") == 2, \
            "build_ass emphasize: expected exactly 1 gold tag + 1 reset per line"
        with open(ass, encoding="utf-8") as fh:
            assert r"\c&H3FD2FF&" not in fh.read(), "build_ass default must stay tag-free"
        print("[word_captions selftest] OK - grouping/danglers/word-fixes/speed-sync/emphasize/ffmpeg-burn all passed")
    finally:
        shutil.rmtree(work, ignore_errors=True)
