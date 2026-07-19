# Source subtitle audit

Choose the subtitle render mode from evidence before generating ASS or burning pixels. Existing Japanese text may be a soft subtitle stream, burned-in lyrics, a title card, intermittent stage captions, or unrelated chat/MC text; do not treat these as equivalent.

## Two-pass audit

1. Inspect media streams and record every subtitle stream, language tag, codec, and disposition.
2. For each selected track, extract original-resolution, full-width source frames at every available subtitle event or detected text transition. When event timing is unavailable, combine bounded interval sampling with OCR/text-change detection; include opening verse, repeated chorus, final refrain, and outro.
3. Preserve the frame timestamp, image hash, OCR candidate, and source-video hash. Use Computer Use in Preview/QuickTime for a second read-only visual pass through the source frames or source clip.
4. Before lyrics approval, classify provisional presence as `none`, `soft-japanese`, `burned-japanese`, `intermittent/non-lyric`, or `unknown`.
5. After the Lyrics Packet is prepared, compare every source-Japanese event with its stable line ID, performed repeats, timing, and display order. Record missing, extra, mismatched, mistimed, and unsafe-position events.

## Layout selection

Select `source-japanese` only when the audit proves Japanese coverage for 100% of performed lines, matching the approved text, display order, performed repeats, and timing. Preserve the source Japanese, render no duplicate Japanese or generated furigana, and time each Chinese line to its paired source-Japanese event. When the native lower region is unsafe, apply Safe-Area Recovery: keep the output resolution and aspect ratio, uniformly scale and top-align the source, and create a bottom subtitle band. Source pixels and soft tracks remain evidence, not Workflow Text Authority.

Select Normal Bilingual Subtitle Mode directly when no source Japanese lyrics exist. When source Japanese exists but is not complete, first persist one track-wide Source Subtitle Fallback Plan. Disable an incomplete soft subtitle track and render every performed line in Normal Bilingual Subtitle Mode. For incomplete, incorrect, or mistimed burned-in Japanese, use Normal Bilingual Subtitle Mode only after deterministic Caption Region Replacement neutralizes the same caption region for the whole track, leaves no readable old text, preserves important composition, and lets every approved Japanese/ruby/Chinese line be rendered cleanly. Verify those properties for every line.

If a burned caption region moves, intersects important content, or cannot be neutralized consistently, create a version-bound Track-level Exception Review with evidence and only two choices: skip the track, or let Roy approve an exception tied to the exact source/render hashes. Never silently mix render modes, accept 99% coverage, patch only the missing lines, place Chinese above source Japanese, or treat Safe-Area Recovery as a remedy for incomplete text.

## QA evidence

Keep both source-audit crops and final burned-output crops. The final per-line verdict must show that the correct Japanese line is present exactly once, the paired Traditional Chinese is immediately below it, neither line is clipped or outside the safe area, and repeated/final sections were inspected. When Safe-Area Recovery is used, also preserve the scale/offset parameters and full-frame evidence that source Japanese remains legible and important composition is not cropped, covered, or materially harmed. When Caption Region Replacement is used, preserve its fixed region/transform parameters plus source/output evidence that old text is unreadable and important composition remains intact. A single screenshot, OCR result, subtitle-stream tag, or model report cannot pass the audit.
