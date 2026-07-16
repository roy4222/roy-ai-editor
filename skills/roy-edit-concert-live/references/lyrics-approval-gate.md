# Lyrics approval gate

Treat lyrics, translation, performed repeats, and display line breaks as one versioned approval unit. Stop all lyric-dependent production until Roy approves that exact unit.

## Required search

For every song:

1. Find the official Japanese lyrics or the artist's official description first.
2. Search the exact song title, singer, and `巴哈`.
3. Search `site:home.gamer.com.tw <song title> <singer>`.
4. Retry alternate spellings, Japanese/romanized titles, and the original artist when the concert performer is covering the song.
5. Record every useful result and record that no result was found when the search fails.

Do not silently replace this search with a general web result or an AI translation. If no acceptable Bahamut translation exists, show the failed queries and ask Roy whether to provide a translation, choose another source, or authorize an independent translation.

A found page is not automatically reusable. Record the translator, URL, publication title, explicit reuse permission, attribution requirement, modification limits, and unresolved terms. Credit alone is not permission.

## Approval packet

Present one packet per song before alignment or subtitle/video rendering:

- song title, performer, and original artist;
- official Japanese lyrics URL;
- all relevant Bahamut result URLs, titles, and translators;
- selected translation source and why;
- reuse and modification terms;
- performed-versus-source differences, repeats, ad-libs, and uncertain words;
- proposed line map with stable line IDs;
- warnings and unresolved decisions;
- packet version or content hash.

Use this line-map table:

| ID | Japanese source line | Traditional Chinese source line | Proposed on-screen break | Notes |
|---|---|---|---|---|
| L001 | ... | ... | one event | source line 1 |

Show the full paired text when Roy supplied it or the reuse terms permit reproduction. Otherwise show the source URL, author, line count, mismatches, and only a short compliant excerpt; ask Roy to paste the text he wants processed or confirm the linked page.

End with an explicit gate request:

> 請回覆「歌詞與翻譯通過：<歌曲名>／版本 <版本>」，或直接列出要修改的行號。
> 在你明確核准前，我不會開始對軸、產生字幕或燒錄影片。

Do not treat silence, a URL alone, a general `OK`, or approval of another song/version as approval. A user message that explicitly says to use the supplied lyrics/translation for the named song counts only after the packet and proposed line breaks are visible.

Persist the approval message, date, packet version/hash, source URLs, and selected translator beside the project manifest.

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

Invalidate approval and return to this gate whenever the selected source, translator, lyric wording, translation wording, performed repeats, or display line breaks change. Do not patch the rendered video first and ask afterward.
