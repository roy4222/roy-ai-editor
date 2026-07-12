# SETUP — Answer these to make the system *yours*

> **This repo isn't a hand-me-down config — it's a framework + questionnaire.**
> It distills a battle-tested YouTube / short-form automation system into templates.
> You answer the questions below and it generates **your own** voice / brand / strategy
> / community files. The code is generic; **all personalization comes from your answers —
> none of the original author's private data is included.**

*(中文版見 [SETUP.md](SETUP.md))*

## 🧭 Platform requirements (read this first)

The kit has **two first-class paths** with different requirements:

- **Path 1 — Programmatic (recommended default for adopters; Win / Mac / Linux)**: just Python 3.9+ and `ffmpeg`/`ffprobe`.

  **Installing ffmpeg (one-time, all platforms):**
  | Platform | Command |
  |---|---|
  | macOS | `brew install ffmpeg` (needs [Homebrew](https://brew.sh); verify with `ffmpeg -version`) |
  | Windows | `winget install ffmpeg`, or grab a full build from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) and add it to PATH |
  | Linux | `sudo apt install ffmpeg` (Debian/Ubuntu) |

  > Common misconception: "Mac doesn't have ffmpeg" — ffmpeg is cross-platform by design, and the Mac install is actually the easiest (one brew line). "Alternatives" like MoviePy / editly call ffmpeg under the hood anyway. **No CapCut, no Computer Use.** System paths and CJK fonts on Mac/Linux are auto-detected by `src/platform_compat.py`.
- **Path 2 — CapCut-assisted (what the author personally uses; Windows-first)**: additionally needs CapCut Desktop (international edition) + your AI assistant's Computer Use. **Version-sensitive** — read the compatibility matrix in [TROUBLESHOOTING](TROUBLESHOOTING.md) before touching draft JSON.
- **On Mac** → go straight to Path 1 (there is no working equivalent of the CapCut GUI automation on Mac).

## ⚡ Fastest start (you don't have to fill it all in!)

> **Think the questionnaire is long? You don't need to finish it before starting.** Of the 6 sections below, only **3 are ★required** — fill the rest **as you go**.

**Recommended — let the AI interview you (least effort):**
Hand the whole repo to Claude / ChatGPT and paste:
> "Ask me only the **★required 3 sections** from `SETUP.md` first (Brand, Niche, Production) and generate my `profiles/`. Ask the optional sections later."

The AI asks one question at a time and fills the files for you — **you just answer out loud**.

**5-minute minimum (answer just these 3 to start):**
1. Channel name? **Do you show your face?** (decides whether intros/outros schedule an on-camera cue)
2. What do you make, and which platform? (tutorial/vlog…, YT long-form/Shorts/Reels)
3. **Path 1 (programmatic, cross-platform)** or **Path 2 (CapCut, Windows-first)**? Where are your asset / export paths?

→ That's enough to start editing. Voice / Algorithm / Community (4️⃣5️⃣6️⃣) can wait until you want to optimize.

**Manual route (3 steps):**
1. Copy `templates/*.template.md` → `profiles/*.md` (drop the `.template`)
2. Fill the **★required** sections (1️⃣2️⃣4️⃣) first; leave the rest blank
3. `cp config.example.py config.py` → fill in your own paths

---

## 1️⃣ Brand / Channel → generates `profiles/brand.md`　★required
- Channel name + handle? Website / main link?
- **How do you sign off?** (voice-over / title card / on-camera?) — this becomes your outro signature
- ⚠️ **Do you film talking-head / show your face?** (Important — if not, intros/outros must use b-roll + cards, never "selfie cue")
- Brand colors / preferred fonts? Subscribe-CTA placement?

## 2️⃣ Niche / Content type → routes the pipeline　★required
- What do you make? (tutorial / vlog / unboxing / review / gaming …)
- Main platform? (YT long-form / Shorts / Reels / TikTok)
- Language?

## 3️⃣ Your Voice → generates `profiles/voice.md`　⭕optional (add later when tuning scripts)
- **Paste 5–10 scripts/posts you wrote yourself** — the system learns *your* voice, not someone else's
- Your typical opener? Catchphrases? Sign-off?
- **Hard no's?** (anti-patterns — e.g. no profanity, no fake hype, no certain memes)

## 4️⃣ Production → generates `config.py`　★required
- **Which path are you on?** (see "Platform requirements" up top)
  - **Path 1 Programmatic** (recommended default; Win/Mac/Linux) — pure-code pipeline, just Python + ffmpeg, **no CapCut**
  - **Path 2 CapCut-assisted** (Windows-first) — pick this only if you want CapCut's fancy-text / cloud templates
- If Path 2: is **CapCut Desktop (international edition)** installed? ⚠️ **Does your AI assistant have Computer Use enabled?** CapCut has no public API — GUI automation works by the **AI operating the CapCut window via Computer Use** (apply templates / export); without it, it won't run. Draft-JSON editing is **version-sensitive** — run `detect_draft_format()` first and read [TROUBLESHOOTING](TROUBLESHOOTING.md)
- Where are your **fonts** / **BGM** / **b-roll** stored? Project / export paths?
- (Filled into `config.py` — the example contains **no account names**)

## 5️⃣ Algorithm context → fills `profiles/algorithm.md`
- Your current numbers? (subs / avg views / CTR / average view duration)
- Main traffic source? (Browse / Suggested / Search / External …)
- Biggest pain point? (reach / retention / CTR …)
- (The framework gives you **which metrics to watch and how to fix them**; you fill in **your** numbers)

## 6️⃣ Community / external traffic → fills `profiles/community.md`
- Which communities do you have, and how big? (Discord / Line / FB / IG …)
- Which channels can you mobilize at launch?
- (Gives you the mobilization-SOP **structure**; your communities, your numbers)

---

## Why a questionnaire instead of a ready-made config?

The most valuable part of a creator system is its **structure and methodology**, not one
person's private numbers. Copying someone else's voice / strategy / community data won't
help you — it may mislead you. So this repo gives you the **skeleton**; you fill it with
your own flesh. That's what makes it truly **yours**.
