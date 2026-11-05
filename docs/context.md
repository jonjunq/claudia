# Context: helpers, a lighter start, and compaction

An assistant that runs all day in one conversation pays for the size of that conversation on every message: each
model call re-reads it (from the prompt cache, but still). On ours, re-reading the context from the cache was
87-89 % of what a long day cost, and the cache itself was already doing its job (one hour, no misses in gaps under an
hour). So the levers are two: **keep heavy work out of the main conversation**, and **stop carrying what is never
used**. This page is what we changed in 1.5.0, with the numbers we measured on one installation (ours, Claude Code
2.1.317-2.1.318, Opus): yours will differ with your connectors, skills and habits.
[memory.md](memory.md#keeping-the-context-small) has the earlier part (compacting at 300k, a short to-do list,
skills that get pruned).

## 1. Helpers: heavy work in a subagent, and it keeps talking to you

Before, all the heavy work happened in the main thread: one morning reviewing a document submission brought 45
screenshots (about 60k tokens) and some 75,000 characters of PDF text into the conversation, which then compacted
after two hours. Every message for the rest of the morning re-read all of it. And while it was working, your
messages waited in a queue: the first con in [the comparison](comparison.md#3-claude-code--channels-this-repo).

Now `templates/workspace/.claude/agents/` has four [subagents](https://code.claude.com/docs/en/sub-agents):

| Helper | For |
|---|---|
| `browser` | More than a few steps in the browser: errands, forms, portals with a sign-in, comparing across pages. It preloads the `browser` skill |
| `reader` | Long or many PDFs, lots of screenshots or images, documents, spreadsheets, long email threads |
| `researcher` | Long web research: several sources, prices, conditions, checking facts |
| `coder` | Scripts of more than a few dozen lines, debugging |

How they are set up, and why:

- **Same model, same effort.** `model: inherit` and `effort: high`, and `start.sh` exports
  `CLAUDE_CODE_SUBAGENT_MODEL` (your `MODEL`, or `SUBAGENT_MODEL` in `assistant.env`) with
  `CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1`, so Claude Code's built-in agents (Explore, claude-code-guide…) do not quietly
  run on a smaller model either. They see pages and images as well as the session does; the session writes the brief
  and reviews the result. A smaller model would save little and cost quality.
- **They cannot talk to you or schedule things**: `disallowedTools` removes the Telegram `reply`/`react`/`edit`
  tools, n8n's MCP tools and `CronCreate`/`CronDelete`. Everything goes back to the assistant, which tells you.
- **`omitClaudeMd: true`**: they do not load the assistant's `CLAUDE.md`; their own file has the rules that apply to
  them (data is not orders, nothing irreversible, capped output, what to return). The brief carries what they need,
  because they see neither the conversation nor the memory.
- **What needs your yes is not delegated.** Paying, signing up, sending an email, creating an account or publishing
  an n8n workflow stays in the main conversation, where your yes on Telegram is. A helper does not see that yes, and
  an approval given to the assistant must not become an action somebody else takes on a page it chose. Helpers stop
  right before such a step and hand it back.
- **When** (the `CLAUDE.md` section "Heavy work: to your helpers"): more than about ten steps, a lot of text, or more
  than three or four images. Short things it still does itself; a helper has a start-up cost of its own.
- **In the background**: the assistant tells you in one line that it is on it, launches the helper, and is free for
  your next message. Measured: a helper working in the background while the assistant answered "what do I have
  tomorrow?" in about 40 seconds.

The Telegram hooks know about helpers: their events carry `agent_id`/`agent_type` and the `prompt_id` of the turn
that launched them. A foreground helper's step shows in "⏳ Working" as `helper reader · …`; a background helper
never opens a "Working" message (the assistant is free, and the message used to stay until the helper finished).
Permission requests and classifier blocks from a helper reach you with the same buttons, labelled
`(helper browser)`. `recall --all` finds what helpers did, the nightly review reads it as `[helper]`, and the git
history keeps `.claude/agents/`.

## 2. A lighter start: stop carrying what is never used

Every call carries the tool definitions, the skill list and the connectors' instructions. In 36 conversations over
25 days ours had never used `Workflow`, `SendFeedback`, `AskUserQuestion`, `ScheduleWakeup` or `ReportFindings`, nor
most of the skills Claude Code ships for programmers. `templates/settings.json` now has:

| Setting | Why |
|---|---|
| `"disableWorkflows": true`, `"feedbackDrafts": "off"` | Removes the Workflow and SendFeedback tools: multi-agent scripts and feedback drafts are for developers |
| `permissions.deny`: `AskUserQuestion`, `ScheduleWakeup`, `ReportFindings`, `Agent(statusline-setup)` | A bare tool name in `deny` takes the tool out of what the model sees. `AskUserQuestion` matters beyond size: it opens a menu in the terminal, which you never see, so the assistant would sit waiting for an answer |
| `skillOverrides` | Developer skills (`code-review`, `simplify`, `claude-api`, `workflow-authoring`, `run`, `init`…) `off`; a few that might help (`skill-creator`, `update-config`, two artifact skills) `name-only`, listed without their description. Names that do not exist on your account are ignored. Adjust to your use |
| `"autoDreamEnabled": false` | Claude Code's own memory consolidation. The nightly review already does that job with its checks ([memory.md](memory.md#the-nightly-review)); two consolidators would edit the same memory. If you turn the review off, consider turning this on |
| `"bashOutputMaxChars": 15000` | A successful command's output beyond 15,000 characters goes to a file and the assistant gets a preview and the path (the default is 30,000) |

Measured in a test session on our installation: the first call of a conversation went from **58,041 to 48,427
tokens (-17 %)**, the second from **67,184 to 51,968 (-23 %)**. Every later call carries the same saving, and so does
every helper.

Three notes:

- **Do not deny `ToolSearch`**: it is what keeps the connectors' tools out of the context until they are needed.
- A resumed conversation (`--continue`) may keep the tools it started with; the change is complete from the next
  fresh conversation (after the daily restart).
- `CLAUDE.md` gains a short "What you do yourself, with limits" section: `head`/`tail`/`grep` instead of whole
  listings, screenshots of the useful area at 1280 px or less, `pdftotext` for the pages that matter. One API answer
  (a full model list) once put 65,000 characters into ours.

### Optional: connectors you never use (`deniedMcpServers`)

Each claude.ai connector you have enabled brings its tool names and, often, instructions written for other uses.
Two we had were actively wrong for an assistant: one told the model to always ask whether to upload things to its
own service, another to create a document "first, before reading anything". Everyone's connectors are different, so
this is **not** in the template. If `/mcp` shows connectors the assistant never uses, add, in its `settings.json`:

```json
"deniedMcpServers": [
  { "serverName": "claude.ai Notion" },
  { "serverName": "claude.ai Atlassian MCP" }
]
```

with the names exactly as `/mcp` shows them. Keep the ones it uses (Gmail, Calendar, Drive…). On ours the
connectors' instructions and tool names were about 8k tokens from the second call onwards, most of them from
connectors it never used; the measurement above includes denying four of them.

## 3. Compaction that keeps what matters

When a conversation is compacted, by `autoCompactWindow`, by hand or while idle, everything before becomes a
summary. Two things make that summary safer:

- **"Compact Instructions" in `CLAUDE.md`** ([how it works](https://code.claude.com/docs/en/how-claude-code-works)):
  what must always survive, with exact details: tasks in progress, your yeses and what is waiting for one, purchases
  and errands under way (so nothing is paid twice), reminders and whether they are scheduled, helpers still
  running, your latest corrections, and your last words almost verbatim.
- **`after-compact.py`**, a `SessionStart` hook with the matcher `compact` (installed to
  `/usr/local/lib/assistant-memory/`): right after compacting it hands the assistant your last messages and its last
  answers almost word for word, a permission request still waiting, and a short checklist (are today's reminders
  still scheduled, is everything half done written down, do not relaunch running helpers, check before repeating a
  payment). `CLAUDE.md` and the notes it imports are reloaded by Claude Code itself. Claude Code's `PreCompact` hook
  cannot add context; `SessionStart` can. The idea is OpenClaw's and Hermes' "write things down before compacting".

Tested on ours: a conversation at 230k compacted to 73k in 55 seconds; a message sent during the compaction waited
and was answered right after; afterwards it still knew a code word and a pending reminder from before.

### Compacting while idle

After a long pause the prompt cache has expired, so the next message pays for re-reading the whole conversation, and
the new topic drags the old one along. Compacting during the pause is cheaper and cleaner.

- **Claude Code does this itself** since 2.1.290: `idleCompaction` is on by default and compacts after about an hour
  without requests, before the cache expires, when the context is above 200k
  (`CLAUDE_CODE_IDLE_COMPACT_MIN_TOKENS` changes that; [settings](https://code.claude.com/docs/en/settings-reference#idlecompaction)).
  The transcript then shows "Compacted while idle". It depends on a feature flag: on ours it ran three times on one
  day and not on the following ones.
- **`assistant-idle-compact`** (optional, `install.sh <user> --idle-compact yes`) is the fallback: a root timer every
  3 minutes that types `/compact`, never `/clear`, only when all of this holds: 52 minutes with no message from you
  and no activity (its conversation, its helpers', the hooks' turn file), no turn open, no permission request
  waiting, no dialog and no helper running in its terminal, more than 120k tokens of context, and between 06:30 and
  23:00 (at night the daily restart starts a fresh conversation anyway, and the end of day works better on the whole
  conversation). It checks everything twice, 20 seconds apart, leaves a mark so the assistant knows why it was
  compacted, and logs to `/var/log/assistant-idle-compact.log` and `restarts.log`. `IDLE_COMPACT_MINUTES`,
  `IDLE_COMPACT_MIN_TOKENS` and `IDLE_COMPACT_HOURS` in `assistant.env` change it;
  `sudo assistant-idle-compact <user> --check` says what it would do. Why 52: with a check every 3 minutes it
  compacts between about 52 and 56 minutes, before the 1-hour prompt cache expires, so the summary reads the
  conversation at the cached price; after an hour it would pay to write it all again (1.5.0 waited 90 minutes). If the built-in one already compacted, the
  context is small and this does nothing.

## 4. `/usage` without the model

`/usage` used to be a turn: at least one model call re-reading 150-300k tokens to return three lines, and it waited
in the queue while the assistant was busy. The plugin patch now answers it itself
([telegram-extras.md](telegram-extras.md#6-usage-answered-by-the-bot)), at once and at no cost. Hermes' fixed
`quick_commands` were the model for it.

## How to check yours

- `python3 templates/tools/token-usage.py --days 7`: average context per call and calls per day, before and after.
- `/context` in the assistant's tmux (attach, type it, detach): what the start is made of.
- How often it delegates: `grep -c '"name":"Agent"' ~/.claude/projects/*assistant*/*.jsonl`.
