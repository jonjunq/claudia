# Comparison: Hermes Agent, a claude.ai Project, and Claude Code + channels

What we actually used, in order, and why we ended up here. Versions and prices are from autumn 2026; check the
current state of each before deciding.

## 1. Hermes Agent + a pay-per-token model

[Hermes Agent](https://github.com/NousResearch/hermes-agent) (Nous Research, open source) was our first assistant,
in its own locked-down container, reached through its Telegram gateway. We started on OpenRouter, hit its usage
limits, and moved to the DeepSeek API directly.

**What it does well**, and the owner liked a lot:

- It is designed as an assistant: a persona file (`SOUL.md`), proactive behaviour, its own scheduler, and it "just
  does things" without many objections.
- Native chat commands such as `/model` and `/new`, optional streaming of replies into Telegram, speech-to-text for
  voice notes.
- `quick_commands`: buttons in Telegram that run a fixed command **without calling the model**. For repetitive
  actions (power a server on/off, status) this costs nothing.
- Any provider: cheap models, local models, or Claude through an API key.
- Very cheap per message with a small model: twelve model calls for one request cost us $0.006.

**What pushed us away:**

- **Model quality.** With DeepSeek's small model it made up causes for problems ("the router", "the Windows
  firewall") and added steps nobody asked for. One "turn on my PC" took 61 s: about 12 s of model calls, 37 s of a
  `sleep` it decided to add, 11 s of a pointless port check. Better instructions helped; the model was the limit.
- **Paying twice.** We already paid for a Claude subscription. A subscription cannot power Hermes: Anthropic does
  not allow third-party apps to route requests through Pro/Max credentials, and Hermes' own "Anthropic OAuth" option,
  when we looked, required Max plus separately purchased extra usage. Since 4 April 2026 Anthropic says it plainly:
  the subscription no longer covers third-party harnesses such as OpenClaw or Hermes, which need paid API usage
  ([TechRadar](https://www.techradar.com/pro/bad-news-claude-users-anthropic-says-youll-need-to-pay-to-use-openclaw-now)).
  Claude Code itself is still covered. A Claude API key works with Hermes, billed per token.

## 2. A claude.ai Project as an assistant

Same subscription, Claude's best models, connectors to Gmail, Calendar and Drive. But it only speaks when spoken
to: nothing runs in between, no reminders, no morning summary, no reaching you first. It did not feel like an
assistant.

## 3. Claude Code + channels (this repo)

Claude Code is an agent that already runs commands, edits files, uses the claude.ai connectors and keeps memory.
[Channels](https://code.claude.com/docs/en/channels) (research preview) add the missing piece: an official
Telegram plugin that pushes your messages into a running session and lets it reply. It is the unmodified Claude Code
binary signed in with your own subscription, which is the use the terms describe.

**Pros**

- **No per-token bill**: it runs on the subscription you already pay for.
- **The best models**: Opus or Sonnet, your choice, set in a file.
- **Official pieces**: Telegram plugin with a sender allowlist and permission relay, Gmail / Calendar / Drive
  connectors, memory, skills, scheduled tasks, auto mode with a safety classifier.
- **It can build its own tools**: it wrote its own Discord voice-call channel and several helper scripts.

**Cons**

- **Shared limits.** Everything it does comes out of the same 5-hour and weekly limits as your own Claude use. If you
  code heavily with Claude, you will feel it; `/usage` and its warnings exist for this.
- **One session, one conversation.** Context fills up, hence the nightly restart, compaction and `/clear`. Long
  work used to make your messages wait; since 1.5.0 heavy work goes to helpers (subagents) in the background and the
  assistant stays free for you ([context.md](context.md)), but it is still one conversation, not one per topic.
- **It is a terminal program run unattended.** Dialogs and prompts that assume someone is at the keyboard can stall
  it; you need the plumbing in this repo (restart loop, dialog acceptor, permission watcher, daily cycle).
- **No built-in chat commands**: the plugin only has pairing commands. We added `/usage` (answered by the patched
  plugin without the model) and `/clear`; changing model means editing a file.
- **Research preview**: the channel flags and protocol may change.
- **Personal use only.** Signing in with your subscription is for you. Not a bot for your team, your family or your
  customers on one subscription: see [Is this allowed?](../README.md#is-this-allowed) and use an API key for that.

## Which one?

| If you… | Use |
|---|---|
| Already pay for Claude (Pro/Max) and want a capable personal assistant | Claude Code + channels |
| Want the cheapest possible running cost and accept a weaker model | Hermes (or similar) + a small pay-per-token model |
| Need several users, a shared bot, or a product | An agent framework with an API key under commercial terms |
| Mostly want fixed buttons (on/off/status) | A plain script bot, or Hermes' `quick_commands`; no model needed |
| Just want to steer a Claude Code session from your phone, no assistant persona | Claude Code's [Remote Control](https://code.claude.com/docs/en/remote-control) |

We kept Hermes for a while alongside, for its free buttons, and moved day-to-day use to the Claude Code assistant.

## What we took from them

Reading the others' code and docs is cheaper than inventing. What this repo borrows, and from whom:

| Idea | From | Here |
|---|---|---|
| Search old conversations with SQLite FTS5, no model calls | Hermes (`session_search`) | `recall` ([memory.md](memory.md)) |
| A background review that improves skills and memory | Hermes | the nightly review |
| Mark skills nobody uses (Hermes' curator goes on to archive them) | Hermes (curator) | the review lists them after 30 days; nothing is deleted |
| Only what the owner said or what was seen to work may become memory | OpenClaw ("Dreaming") | the review's provenance rule |
| Write things down around a compaction | OpenClaw, Hermes | Compact Instructions + the after-compact hook ([context.md](context.md)) |
| Compact or reset after an idle spell | OpenClaw (`reset: idle`) | Claude Code's own idle compaction, and an optional fallback timer |
| Delegate heavy work to isolated children, in parallel | Hermes (`delegate_task`), OpenClaw, Manus | the four helpers, on the same model |
| Answer fixed commands without the model | Hermes (`quick_commands`) | `/usage` from the plugin |
| A stable, lean prefix: carry only what is used | Manus (context engineering) | the settings that trim the fixed context |

What we did not take: a heartbeat that wakes the model on a timer (n8n plus the [wake-up](wakeup.md) costs nothing
while idle), a smaller model for the helpers (quality first; Hermes lets you choose a model per subagent, we force
the same one), public skill registries without vetting ([vetting-skills.md](vetting-skills.md)), and vector search
for `recall` (it rarely misses; see [memory.md](memory.md#recall-search-old-conversations)).

## Where the others are now (November 2026)

Checked in early November 2026; they move fast, so look again before deciding.

- **Hermes Agent** ([v0.22.7](https://github.com/NousResearch/hermes-agent/releases), 3 November): memory as two
  small files frozen at the start of each session, `session_search`, compression in two phases (old tool results
  pruned without a model, then an iterative summary, with `prepare_ahead`), a curator that marks unused skills
  after 30 days and archives them after 90, and `delegate_task` with isolated children that can each run on a
  different model. Any provider, many channels. With Claude, an API key.
- **OpenClaw** (2026.10.3): Markdown memory with hybrid vector + BM25 search, a memory flush before compacting,
  pruning of tool results when the cache expires, sessions per channel with idle resets, a heartbeat. Its security
  record is poor (hundreds of malicious skills on its registry, many exposed instances, a published CVE in 2026), and
  the Claude subscription no longer covers it.
- Commercial assistants (ChatGPT's Scheduled Tasks, Google's Gemini agents, Manus on Telegram) are proactive but
  run in their provider's cloud and do not touch your own machines.

None of this changes the choice above for us: the best model on a flat subscription, with real access to our things
and permissions we control, is still only possible with Claude Code itself.
(For "a company of agents" we also tried other tools; that is a different problem and not covered here.)
