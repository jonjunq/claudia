---
name: recall
description: Searching your old conversations with __OWNER__ and your diary. Load it when __OWNER__ asks about something from another day ("what did I tell you about…?", "when did we talk about…?", "that thing last week", a fact, price, link or decision that is not in your memory or in notes/), or when you need a command or result from an earlier session.
---

# Recall: searching old conversations

Every morning you start a new conversation, but all the earlier ones and `notes/diary/` are indexed. Use this instead
of opening the `.jsonl` transcripts by hand with Python or grep: it is instant and returns only the piece that matters.

## Usage
- Search: `recall search "key words"` → up to 8 results: date and time, who (`owner`, `assistant`, `diary`),
  session, message number and the piece with the words marked «like this».
  - Options: `-n 15` (more results), `--since 2026-10-20`, `--until 2026-10-31`, `--all` (also the commands you ran
    and their results: useful to get back a command, a path or the output of something).
- See the context of a result: `recall show <session> <number>` → the messages around it (`--window 10` for more).
  The one marked `>>` is the result.
- The index updates itself at every search.

## Searching well
1. Concrete, rare words, not sentences: names, places, brands, amounts. Each word counts as a prefix (`hotel` finds
   `hotels`) and accents do not matter.
2. Too many results: add another word or narrow with `--since/--until`. None: try synonyms, the word in another
   language, or `--all`.
3. Advanced, FTS5 syntax: `"exact phrase"`, `flight OR plane`, `Rome NOT Paris`.
4. __OWNER__'s voice notes show up as `owner` with `(voice)` in front (it is their transcription).
5. Before answering __OWNER__, open the good result with `show` to confirm the context: a loose piece can be an
   option that was later dropped. Tell them which day it is from.
