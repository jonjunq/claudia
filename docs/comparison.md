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
  when we looked, required Max plus separately purchased extra usage. A Claude API key works, billed per token.

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
- **One session, one conversation.** While it works on something long, new messages wait. Context fills up, hence
  the nightly restart and `/clear`.
- **It is a terminal program run unattended.** Dialogs and prompts that assume someone is at the keyboard can stall
  it; you need the plumbing in this repo (restart loop, dialog acceptor, permission watcher, daily cycle).
- **No built-in chat commands**: the plugin only has pairing commands. We added `/usage` and `/clear`; changing model
  means editing a file.
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
(For "a company of agents" we also tried other tools; that is a different problem and not covered here.)
