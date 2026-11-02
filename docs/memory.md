# Recall, nightly review and history

Three small additions to the assistant's memory, all borrowed from
[Hermes Agent](https://github.com/NousResearch/hermes-agent) after reading its code: a search over old
conversations, a nightly review that improves skills and memory, and a git history to undo either. They live in
`templates/memory/`, installed root-owned to `/usr/local/lib/assistant-memory/`, so the assistant can use them but
not change them.

## Recall: search old conversations

Every conversation is a `.jsonl` transcript under `~/.claude/projects/<workspace>/`, and every day leaves a page in
`notes/diary/`. Before this, "what did I tell you about X last month?" meant the assistant opening transcripts with
improvised Python or grep: ours did it 26 times in three weeks, slowly, and sometimes gave up.

`recall` (Hermes' `session_search` idea) keeps a SQLite FTS5 index of both, with BM25 ranking and no model calls:

```bash
recall search "dentist appointment"          # what the owner said, what the assistant answered, the diary
recall search "invoice" --since 2026-10-01 --all    # --all also searches commands and tool results
recall show <session> <n>                     # the messages around a result
```

- It indexes incrementally at every search: only files whose size or mtime changed are re-read. On ours, 7,500
  messages index in under a second and a search takes 30-40 ms.
- Messages from Telegram count as `owner`; voice notes too (with `(voice)` in front), because their text is the
  output of `bin/transcribe.sh`. Its own `recall` calls are left out of the index.
- At most two results per conversation, so one long day does not hide the others.
- The index (`~/.cache/assistant-recall.db`, mode 600) holds pieces of emails and conversations: it is only for its
  user.
- The `recall` skill tells the assistant when to use it and how to search well (rare words, prefixes, confirm the
  context with `show` before answering). `settings.json` allows `Bash(recall *)`.

## The nightly review

The end of day relies on the assistant noticing, at 05:45 and with a full context, everything worth keeping. It
misses things: a correction of style, the trick that finally worked on a website, a skill that turned out outdated.
Hermes runs a "background review" after conversations with a prompt that asks exactly that. Ours runs once a night,
inside `assistant-daily-restart`, right after the end of day and before the restart:

1. `recall index`, then the conversation since the last review is dumped as text: the owner's and the assistant's
   messages in full (up to 3,000 / 2,000 characters each), tool calls and results trimmed, at most 400,000
   characters (about 110k tokens). If nobody wrote that day, there is no review.
2. Skills, memory and `CLAUDE.md` are copied to a workshop, `/var/lib/assistant-review/<user>/workshop`.
3. `claude -p` runs there as the assistant's user with `env -i`, `--setting-sources project` (none of its own
   settings or hooks), `--strict-mcp-config` and no claude.ai connectors, `--tools Read,Write,Edit,Glob,Grep` (no
   shell, no web), and deny rules for anything outside the workshop. The prompt is `review-prompt.txt`: what makes a
   good skill, the order of preference (patch the skill that was used, then another, then a reference file, then a
   new class-level skill), and what **not** to capture: negative claims about tools, one-off stories, transient
   errors, anything not seen to work, and secrets.
4. Only changed files under `skills/` and `memory/` are copied back, atomically, and only if the added lines carry
   no key, token, password or PIN pattern, no invisible Unicode, and the assistant did not touch that file while the
   review ran. It never deletes.
5. A commit in the history before and after and a summary in `notes/last-review.md`, one line per change. With
   `REVIEW_NOTIFY=yes` in `assistant.env` it also sends you that summary as a silent Telegram message; it is off by
   default, because after the first week most people would rather trust it than read one more message a night.

The model is `REVIEW_MODEL` in `assistant.env`, or `MODEL` if unset. Try it by hand without applying anything:

```bash
sudo /usr/local/lib/assistant-memory/nightly-review.py <user> --dry-run
```

Log: `/var/log/assistant-review.log` (one line with turns, seconds and tokens per run). If it fails, the restart
goes on and `restarts.log` says so.

### What it costs

It comes out of the same subscription limits as everything else. Measured on ours, with Opus:

| Day | Conversation | Turns | Time | Cache-read tokens | Output tokens |
|---|---|---|---|---|---|
| An afternoon | 82,000 characters | 16 | 64 s | 340,000 | 5,500 |
| A long, busy afternoon and evening | not measured | 32 | 3 min | ~3.2 million | not measured |

Almost all of it is the conversation being re-read from the prompt cache at every step, which is far cheaper than
fresh input. The long day was about 3 % of the 5-hour limit and 0.5 % of the weekly one on our plan; at 05:45 the
5-hour window has reset by the time you wake up. To spend less, run it every other night or set a smaller model in
`REVIEW_MODEL`.

What it did on its first nights: fixed a TV-control skill that had gone stale, added anti-fake rules it had learnt
for downloads, turned "X does not work" sentences into the positive instruction that does, removed a contradiction
between two notes, and recorded which notification emails the owner wants binned.

## History: undo anything

`history.sh` keeps a git repository at `/var/lib/assistant-history/<user>` (root, mode 700) whose work tree is the
user's home, tracking only `assistant/CLAUDE.md`, `assistant/notes`, `assistant/.claude/skills` and the memory
folder (`*.json`, `*.env`, `*.bak-*` excluded). `assistant-history.timer` commits hourly; the review commits before
and after itself.

### Undoing a change

```bash
g() { git --git-dir=/var/lib/assistant-history/<user> --work-tree=/home/<user> -c safe.directory='*' "$@"; }
g log --stat -5                                      # what changed, and when
g show <commit>                                      # the diff
g checkout <commit>~1 -- assistant/.claude/skills/<skill>/SKILL.md   # the file as it was before that commit
```

It covers the assistant's own edits too: a skill it rewrote badly at 15:00 is in the 14:00 commit.
