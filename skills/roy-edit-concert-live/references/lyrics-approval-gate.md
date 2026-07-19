# Lyrics approval gate

Treat lyrics, translation, performed repeats, and display line breaks as one versioned approval unit. Stop all lyric-dependent production until Roy approves that exact unit.

## Required search

For every song:

1. Find the official Japanese lyrics or the artist's official description first.
2. Search the exact song title, singer, and `巴哈`.
3. Search `site:home.gamer.com.tw <song title> <singer>`.
4. Retry alternate spellings, Japanese/romanized titles, and the original artist when the concert performer is covering the song.
5. Record every useful result and record that no result was found when the search fails.

Before selecting or drafting line translations, create a Song Interpretation Brief for the complete song. Support it with the official lyrics/context and translation research; identify the narrative voice and addressee, central theme, emotional arc, recurring imagery, cross-line relationships, key terms, and unresolved ambiguity. Compare relevant Roy Translation Notebook cases and explain why their treatment does or does not transfer to this song. Notebook cases are advisory by default; auto-apply only official terminology or an explicit Roy Translation Rule, and still verify current context compatibility. Repeated cases may create a rule-promotion suggestion but never a rule automatically. Do not translate a key image from a dictionary gloss alone when the whole-song concept changes its natural Traditional Chinese expression.

Run discovery as a bounded escalation instead of stopping after one weak search:

1. Use normal web search for every required query and save the query plus ranked result URLs.
2. Read public candidate pages with a static fetch first. Record title, author/translator,
   publication date, source URL, and any explicit reuse or attribution wording.
3. Escalate pages that require client-side rendering to `agent-browser`. Use the isolated
   `roy-concert-discovery` profile under its Browser Read-Only Enforcement Profile rather than Roy's daily browser profile, and preserve the page URL,
   rendered text evidence, and a screenshot when reuse terms or authorship are visual-only.
4. Never bypass CAPTCHA, login, paywall, or access control. If a candidate is uniquely
   valuable and blocked by human verification, ask Roy once to unlock the isolated session,
   then resume the remaining research automatically.
5. Use `agent-browser` as the only V1 browser controller. Do not repeat the same search through
   every candidate tool. Only benchmark Playwright CLI on the same fixtures when public-page
   capture success is below 95% and the recorded failure cause is locator/browser-engine behavior;
   defer `actionbook`, `browser-use`, and Agent-Reach until their distinct capability is required.

Do not silently replace this search with a general web result or present an AI translation as a found translation. If the bounded search finds no acceptable reusable Traditional Chinese translation, preserve the failed queries and produce an independent AI Traditional Chinese draft from the sourced Japanese lyrics. Record its model/provider, generation inputs, date, uncertainty markers, and the fact that it has no external translator or source-translation reuse claim. Put that draft in the same Lyrics Packet; it becomes Workflow Text Authority only when Roy approves that exact packet.

A found page is not automatically reusable. Record the translator, URL, publication title, explicit reuse permission, attribution requirement, modification limits, and unresolved terms. Credit alone is not permission.

## Approval packets and concert review

Build one independently versioned packet per song before alignment or subtitle/video rendering:

- song title, performer, and original artist;
- the versioned Song Interpretation Brief and its supporting sources;
- Roy Translation Notebook cases and Translation Rules consulted, with context, provenance, reuse terms, and transfer/rejection rationale;
- official Japanese lyrics URL;
- all relevant Bahamut result URLs, titles, and translators;
- selected translation source and why, or independent AI draft provenance and why fallback was required;
- reuse and modification terms;
- performed-versus-source differences, repeats, ad-libs, and uncertain words;
- proposed line map with stable line IDs;
- proposed Ruby Map with the exact kanji base span, hiragana reading, provenance, and confidence for every applicable line;
- Source Subtitle Audit classification and source-Japanese line matches; mark Ruby Map entries as non-rendered when verified source Japanese will be preserved;
- warnings and unresolved decisions;
- packet version or content hash.

Present every selected track's packet together as one Concert Lyrics Review. Roy may approve the complete review in one response or list only the song IDs and line IDs that need changes. A correction invalidates only the affected packet; unchanged packet hashes remain approved and must not be presented again as unresolved work.

Render each song's review card in this order:

1. a concise Song Interpretation Brief: one-sentence central theme, narrative voice/addressee, emotional opening/turn/ending, three to five key images and their contextual meanings, likely literal-translation traps, and the main external translator comparisons with adoption/rejection rationale;
2. the complete approved-or-user-provided Japanese/Traditional Chinese paired text when reproduction is permitted, with AI-drafted, uncertain, performed-difference, and exceptional-reading lines visibly marked;
3. collapsed provenance, query logs, analyzer agreements, and other technical evidence that already passed automatically, while keeping it available for expansion.

The review approval binds both the displayed Song Interpretation Brief and the exact Lyrics Packet content. If Roy corrects the song-level interpretation, invalidate and rebuild only that song's packet and derived translation; do not preserve line translations that depend on the rejected interpretation or invalidate unchanged tracks.

Apply the Ruby Evidence Policy before presenting the review:

1. Accept an official kana/furigana or artist-provided reading as primary evidence.
2. Otherwise require agreement between two independent Japanese analyzers, no name, jukujikun, ateji, lyric-specific pronunciation, or other ambiguity flag, and no conflict with acoustic evidence from the performed line.
3. Mark the entry `auto-pass` only when all applicable conditions hold. Mark disagreements and missing evidence as `exception`; never resolve them from visual position alone.
4. Show Roy only the exception entries in the review summary. Keep the full Ruby Map available as part of the versioned packet, so approving the batch still approves its exact content hash.

Use this line-map table:

| ID | Japanese source line | Traditional Chinese source line | Proposed on-screen break | Notes |
|---|---|---|---|---|
| L001 | ... | ... | one event | source line 1 |

Show the full paired text when Roy supplied it or the reuse terms permit reproduction. Otherwise show the source URL, author, line count, mismatches, and only a short compliant excerpt; ask Roy to paste the text he wants processed or confirm the linked page.

End the combined review with one explicit gate request:

> 若這是目前唯一待處理的 gate，請直接回覆 `ok` 核准畫面中所有 packet hashes；或列出要修改的歌曲 ID 與行號。
> 在你明確核准前，我不會開始對軸、產生字幕或燒錄影片。

Do not treat silence, a URL alone, an `ok` elsewhere in the conversation, or approval of another review/version as approval. A directly following `ok` counts only when the complete Concert Lyrics Review and proposed line breaks are visible, it is the only pending gate, and no newer review version has replaced it; bind that message to the exact visible packet hashes.

Persist the batch approval message and date plus every included packet version/hash, source URL, and selected translator beside the project manifest.

After approval, append a versioned Translation Notebook case containing the song context, interpretation, candidate phrasings, selected wording, rejected alternatives and reasons, Roy corrections, provenance, reuse terms, and approved packet hash. Store restricted full text only where the existing Production Asset and public-repo boundaries permit it; public Roy Customization may retain only reusable principles and safely licensed or de-identified examples.

## Line-break rules

- Default to one source lyric line per on-screen subtitle event.
- Never join three source lines into one event.
- Join two adjacent source lines only when the sung phrase and source structure require it and Roy approves that exact join.
- Split an overlong source line at a sung breath, punctuation mark, or grammatical boundary. Split the Chinese line at the matching semantic boundary.
- Keep Japanese and Traditional Chinese attached to the same source-line ID; never shift a translation onto the previous or next lyric line.
- Expand every performed repeat in the line map instead of relying on implied repetition.
- Give final refrains and outro lines the same line-by-line review as the opening verse.
- Target no more than 80% of frame width. Split before rendering when either language looks cramped.

## Invalidation

Invalidate only the affected packet and return it to this gate whenever the selected source, translator, lyric wording, translation wording, performed repeats, display line breaks, or Ruby Map changes. Do not patch the rendered video first and ask afterward.
