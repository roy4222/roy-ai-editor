# -*- coding: utf-8 -*-
"""
M96: 美食/旅遊直式 Shorts pipeline（純 ffmpeg）— silent footage → 多色重點字幕 → 配樂。

9:16 1080x1920 直式短影音。專案只需餵 data（segs + caps），不用每支整檔複製。
適合「無人聲、靠畫面 + 重點字 + BGM」的美食/旅遊 Reels/Shorts。

用法：
    from silent_vlog_maker import normalize_to_portrait, build_one_short
    # 1) 手機直拍/橫拍 .MOV 轉正成 9:16
    for clip in raw_clips: normalize_to_portrait(clip, norm_out)
    # 2) 餵片段 + 多色字幕 + BGM
    build_one_short(
        segs=[(norm1, 1.0, 5.0), (norm2, 0.5, 5.0)],          # (clip, in, dur)
        caps=[(0.2, 5.0, [('重點A','g'), ('重點B','y')], 'main'),
              (5.0, 22.0, [('店名/地點','w'), ('地址','w')], 'addr')],
        bgm='assets/bgm/chill-01.mp3', out='short.mp4', vol=0.42)
"""
import subprocess, os, re

# ── encoding 顯式 utf-8（避免 Windows cp950 對中文路徑/輸出 crash；M96 bug fix）──
def _run(args):
    return subprocess.run([str(a) for a in args], capture_output=True,
                          text=True, encoding="utf-8", errors="replace")

def _probe_dur(f):
    return float(_run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                       '-of', 'csv=p=0', f]).stdout.strip())

# ── M38: 去 emoji（NotoSansTC 無 emoji glyph → libass render 成豆腐框）──
EMOJI_RE = re.compile(
    "[\U0001F000-\U0001FAFF\U00002600-\U000027BF\U0001F1E6-\U0001F1FF"
    "←-⇿⬀-⯿️⃣]")
def strip_emoji(s):
    return EMOJI_RE.sub("", s)

# ── 多色重點字（重點字不同色）= ASS inline color（BGR），必包 {} ──
COLOR_VARIETY = {
    'w': r'{\c&H00FFFFFF&}',   # 白
    'o': r'{\c&H008CFF&}',     # 橙 RGB FF8C00
    'y': r'{\c&H0AD6FF&}',     # 黃 RGB FFD60A
    'r': r'{\c&H303BFF&}',     # 紅 RGB FF3B30
    'g': r'{\c&H58D130&}',     # 綠 RGB 30D158
}
_MAIN_POS = r'{\an5\pos(540,1180)}'   # 中下置中（避上 384 / 下 1440 SHORTS_SAFE_ZONE）
_ADDR_POS = r'{\an5\pos(540,1390)}'   # 底部安全區地址

_HEADER = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: MAIN,Noto Sans TC,82,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,7,3,5,40,40,0,1
Style: ADDR,Noto Sans TC,46,&H00FFFFFF,&H00000000,&HB0000000,-1,0,0,0,100,100,0,0,3,8,0,5,40,40,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

def _ts(t):
    h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return "%d:%02d:%05.2f" % (h, m, s)

def build_multicolor_ass(blocks, out_path):
    """blocks: list of (start, end, segs, kind)。
    segs=[(text,color), ...] color∈w/o/y/r/g（'\\n' 換行）；kind='main'|'addr'。
    自動 strip_emoji（M38 防呆 — 不靠人記得不放 emoji）。"""
    lines = [_HEADER]
    for start, end, segs, kind in blocks:
        pos = _ADDR_POS if kind == 'addr' else _MAIN_POS
        style = 'ADDR' if kind == 'addr' else 'MAIN'
        body = ""
        for text, color in segs:
            body += COLOR_VARIETY.get(color, COLOR_VARIETY['w']) + strip_emoji(text).replace('\n', r'\N')
        lines.append("Dialogue: 0,%s,%s,%s,,0,0,0,,%s%s" % (_ts(start), _ts(end), style, pos, body))
    open(out_path, 'w', encoding='utf-8').write("\n".join(lines))
    return out_path

# ── 手機 .MOV → upright 9:16（autorotate 處理 rotation 旗標，含混 -90/+90）──
def normalize_to_portrait(clip_in, clip_out, crf=19):
    """轉正成 1080x1920/30fps/無音（M29/M81）。
    ffmpeg 預設 autorotate 先套 rotation 旗標 → scale/crop 在「已轉正的幀」上做，
    所以同批混 rot=-90/+90（手機拿反）也全部統一 upright（M96 踩過）。"""
    vf = ('scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,'
          'fps=30,setsar=1,format=yuv420p')
    r = _run(['ffmpeg', '-v', 'error', '-y', '-i', clip_in, '-vf', vf, '-an',
              '-c:v', 'libx264', '-crf', str(crf), '-preset', 'medium', clip_out])
    if r.returncode:
        raise RuntimeError('normalize_to_portrait failed: ' + r.stderr[-500:])
    return clip_out

def extract_gps(clip):
    """抽手機 GPS（com.apple.quicktime.location.ISO6709）→ 例如 '+00.0000+000.0000+000/'。
    回 (lat, lon, alt) 或 None。地址要再 web 反查（無法套件化）。"""
    raw = _run(['ffprobe', '-v', 'error', '-show_entries',
                'format_tags=com.apple.quicktime.location.ISO6709',
                '-of', 'default=nw=1:nk=1', clip]).stdout.strip()
    m = re.match(r'([+-][\d.]+)([+-][\d.]+)([+-][\d.]+)?', raw)
    if not m:
        return None
    return (float(m.group(1)), float(m.group(2)),
            float(m.group(3)) if m.group(3) else None)

_NORMV = ('scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,'
          'setsar=1,fps=30,format=yuv420p')

def build_one_short(segs, caps, bgm, out, vol=0.42, fade=1.2):
    """segs:[(clip,in,dur)]（已 normalize 的直式 clip）；caps:[(s,e,[(text,color)],kind)]；
    bgm: BGM mp3；out: 成品。silent footage + 多色字幕 + BGM 當主音（無人聲）。"""
    total = sum(d for _, _, d in segs)
    base = os.path.splitext(out)[0]
    # 1) visual concat
    cmd = ['ffmpeg', '-v', 'error', '-y']
    for p, ss, d in segs:
        cmd += ['-ss', str(ss), '-t', str(d), '-i', p]
    parts, labs = [], ''
    for i, (_, _, d) in enumerate(segs):
        parts.append(f'[{i}:v]{_NORMV},trim=duration={d},setpts=PTS-STARTPTS[v{i}]'); labs += f'[v{i}]'
    fc = ';'.join(parts) + ';' + labs + f'concat=n={len(segs)}:v=1:a=0[vout]'
    vis = base + '_vis.mp4'
    r = _run(cmd + ['-filter_complex', fc, '-map', '[vout]', '-an', '-c:v', 'libx264',
                    '-crf', '19', '-preset', 'medium', '-pix_fmt', 'yuv420p', '-r', '30', vis])
    if r.returncode:
        raise RuntimeError('build_one_short visual failed: ' + r.stderr[-500:])
    # 2) captions
    ass = base + '.ass'; build_multicolor_ass(caps, ass)
    cap = base + '_cap.mp4'
    r = _run(['ffmpeg', '-v', 'error', '-y', '-i', os.path.basename(vis),
              '-vf', 'ass=' + os.path.basename(ass), '-c:v', 'libx264', '-crf', '19',
              '-preset', 'medium', '-pix_fmt', 'yuv420p', '-r', '30', os.path.basename(cap)])
    # cwd=base dir 讓 ass 用相對路徑（避 Windows 冒號跳脫）
    if r.returncode:
        r = subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', vis, '-vf', 'ass=' + ass,
                            '-c:v', 'libx264', '-crf', '19', '-preset', 'medium',
                            '-pix_fmt', 'yuv420p', '-r', '30', cap],
                           capture_output=True, text=True, encoding='utf-8', errors='replace',
                           cwd=os.path.dirname(out) or '.')
        if r.returncode:
            raise RuntimeError('build_one_short caption failed: ' + r.stderr[-500:])
    # 3) BGM 當主音（無人聲）loop + fade
    fo = max(0.3, total - fade)
    r = _run(['ffmpeg', '-v', 'error', '-y', '-i', cap, '-stream_loop', '-1', '-i', bgm,
              '-filter_complex', f'[1:a]volume={vol},afade=t=out:st={fo:.2f}:d={fade}[a]',
              '-map', '0:v:0', '-map', '[a]', '-t', str(total),
              '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', out])
    if r.returncode:
        raise RuntimeError('build_one_short mux failed: ' + r.stderr[-500:])
    return out


if __name__ == '__main__':
    # self-test：多色 ASS render + emoji strip（不跑 ffmpeg）
    import tempfile
    blocks = [(0.0, 3.0, [('整排樹', 'w'), ('開滿', 'r'), ('小花🌸', 'o')], 'main'),
              (0.0, 3.0, [('📍 海邊步道', 'w')], 'addr')]
    p = os.path.join(tempfile.gettempdir(), '_sv_test.ass')
    build_multicolor_ass(blocks, p)
    txt = open(p, encoding='utf-8').read()
    assert r'{\c&H303BFF&}開滿' in txt, 'inline 紅色標籤(含{})漏了'
    assert '🌸' not in txt and '📍' not in txt, 'emoji 沒被 strip'
    assert strip_emoji('a🌸b📍c') == 'abc'
    print('[shorts_vertical selftest] OK')
