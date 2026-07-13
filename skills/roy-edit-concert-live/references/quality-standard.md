# Concert clip quality standard

Use HACHI Birthday LIVE 2025 `万華鏡` v3 as the first golden reference. The 2026-07-12 prototype is Roy's approximate 80/100 baseline, not the target ceiling.

## Release gates

- **Rights:** Record source/channel policy, lyric and translation provenance, attribution, reuse limits, and uncertainty.
- **Lyrics approval:** Record the official Japanese source, all Bahamut candidates, selected translator/source, reuse terms, performed repeats, proposed display breaks, packet version, and Roy's explicit approval. Any later text or line-break change invalidates the gate.
- **Boundaries:** Keep the first note/lead-in and full vocal/instrumental ending. Exclude unintended next-song or MC leakage.
- **Text:** Match the performed lyrics, including repeats. Use faithful, natural Traditional Chinese and follow reuse permission.
- **Line breaks:** Default to one approved source line per subtitle event. Never merge three source lines. Merge two only with Roy's explicit approval. Split overlong lines at a sung breath, punctuation, or grammatical boundary and split the translation at the same semantic boundary. Target at most 80% of frame width and fail any clipping or cramped safe-area result.
- **Karaoke:** Align the approved display lines by sung phoneme/mora, not even character timing. Handle rests, breaths, melisma, and long notes. Center furigana above the correct kanji span only.
- **Singers:** Keep colors stable. Show duets/overlaps deliberately and expose uncertain attribution.
- **Visual QA:** Inspect every numbered full-width subtitle-band crop from the actually burned MP4. Compare wording and breaks against the approved line map; separately check ruby readings/centering, Chinese pairing, clipping, and repeated/final sections.
- **Media:** Check audio pops/clipping/mutes, black/frozen frames, encoding, resolution, frame rate, duration, and file integrity.
- **Publish:** Complete title, description, credits, source URL, translation attribution, contact, and hashtags. Default uploads to private/unlisted; public release is separate.
