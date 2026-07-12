# Concert workflow

1. **Intake:** Record URL, languages, track list, supplied timestamps, singer colors, preferences, and workspace. Create a manifest before expensive work.
2. **Rights:** Check the video description, channel/company derivative-work policy, song restrictions, and translation reuse terms. Save sources, dates, attribution, and uncertainty. Ask Roy when unclear.
3. **Ingest:** Use the CLI when implemented. Save metadata beside the manifest. Keep media outside Git. Never bypass access controls.
4. **Discover tracks:** Prefer creator chapters/description, credible timeline comments, Roy timestamps, then audio/visual inference. Preserve every timestamp source.
5. **Segment:** Combine timeline, waveform, vocals/music/applause/MC, and visual transitions. Preview uncertain endings. Keep the full instrumental decay; silence removal alone cannot choose the end.
6. **Lyrics/translation:** Prefer official sources. Track author, permission, attribution, modification limits, and version. Compare model and permitted reference translations; preserve Roy's corrections as evaluation data.
7. **Align:** Treat trusted lyrics as text truth. Normalize repeats, derive readings, optionally isolate vocals, forced-align, refine by phoneme/mora, and handle rests, breaths, melisma, and long vowels. Put furigana above kanji only.
8. **Multiple singers:** Combine cast, lyric assignment, audio, face/position evidence, and Roy hints. Use stable colors and mark uncertainty.
9. **Render/QA:** Use deterministic CLI execution. Check boundaries, audio, frames, coverage, safe areas, furigana, karaoke drift, rests, long notes, and missing lines. Preview low-confidence findings.
10. **Publish/retain:** Generate media, subtitles, provenance, credits, metadata, and QA. Upload private/unlisted after approval. Public release and source deletion require separate approval.
