# Changelog

## 1.3.0 — 2026-11-04

- **Run it your way**: the README and [docs/isolation.md](docs/isolation.md) no longer present an isolated container
  as the only way. They compare the options (its own container or VM, a user on a machine you already have, root on
  a machine that is all its own, a cloud VM) with what each one risks; fencing is described as a choice.
- **Wake-up** (`templates/wakeup/`, installed root-owned to `/usr/local/lib/assistant-wakeup/`, not started by
  default; [docs/wakeup.md](docs/wakeup.md)): `assistant-wakeup` watches log files (`label | regex | path` rules) and
  takes `POST /wake` with a bearer token from allowed addresses, and types a one-line notice into the session only
  when something happened: batched, capped, marked as data, waiting while a permission dialog is open or the session
  is restarting, never through Telegram. It replaces a Claude Code Monitor that expired every 30 minutes and cost
  about 48 empty turns a day to re-arm. Tests with a fake tmux.
- **n8n kit** (`templates/n8n/`, copied to `/usr/local/share/assistant-n8n/`, nothing installed by default;
  [docs/n8n.md](docs/n8n.md)) for alerts and automations that cost no tokens:
  - `install-n8n.sh`: n8n from npm without Docker (Node 24+, `--force` and why), a system user, `n8n.service`,
    a hardened `/etc/n8n.env` (no Execute Command / SSH / Local File Trigger nodes, no community packages, Code nodes
    cannot read the environment, no telemetry, executions pruned), localhost by default, owner account without a
    browser.
  - `n8n-admin`: import, publish and unpublish workflows and credentials from a shell, and `update`: backs up the data
    folder, updates, checks health, version and workflow count, and rolls back on failure; `--tell` reports the
    outcome to the assistant through the wake-up.
  - Workflow templates: new email over IMAP → wake the assistant (Gmail app password; excludes Promotions, Social and
    Forums because Gmail's IMAP ignores `category:primary`; not marked as read; skips old and repeated emails;
    decodes encoded subjects), and watch a page → Telegram only when it changes, which **switches itself off** at its
    final state or after N days without a change. Their Code nodes run in the tests with Node.
  - How the assistant builds workflows itself through n8n's instance-level MCP server (2.13+), enabled without a
    browser, with the rules it follows.
- `settings.json`: `autoMode.hard_deny` with `"$defaults"` plus a hard block on payments and money. "Never payments"
  inside an `allow` sentence narrows that exception but blocks nothing; [docs/permissions.md](docs/permissions.md)
  explains the difference.
- `CLAUDE.md` template: "Writing for the phone", a style principle for Telegram (a short title with an emoji, little
  text per block, emojis as signposts, bold for the key word, a quote for the main idea, warnings that stand out, an
  example of how to ask, numbered options to answer with a number, emoji progress bars of at most 10 squares), and
  rich messages for anything with structure, never edited afterwards. A real example in
  [docs/telegram-extras.md](docs/telegram-extras.md#writing-for-the-phone).
- `CLAUDE.md` template: "Automatic notices" (what the wake-up types and how to treat new-email notices) and "Alerts
  and repetitive checks: n8n first" (n8n for what needs no thinking, the wake-up for what does, no long Monitors,
  rules for building workflows).
- Fix: a phantom "⏳ Working" message could still appear after a turn that used no tools: the suggested reply Claude
  Code prepares afterwards reuses that turn's `prompt_id`, which is in the transcript. `status-hook.py` now records
  every ended prompt on `Stop`, even when the turn never opened a status, and ignores later events for it. Test added
  for that sequence.
- Approve from Telegram what the auto-mode classifier blocks: `denied-hook.py` (`PermissionDenied`) sends the
  blocked call with Approve / Keep blocked buttons; an approval is one-time, for that exact call, valid 5 minutes,
  and `approved-hook.py` (synchronous `PreToolUse`) lets it through when the model retries. Without it, a call the
  classifier denies just fails and you only notice later. See [docs/telegram-extras.md](docs/telegram-extras.md#when-the-classifier-blocks-something-outright).
- Fix: when Telegram did not confirm the permission message (a timeout, while the message often did arrive),
  `permission-hook.py` gave up and the button you then tapped did nothing. It now waits for the button anyway.
- Fix: a phantom "⏳ Working" message stayed on Telegram after a turn ended, until the next turn. Claude Code fires
  tool hooks for background work in the same session (for example while it prepares the suggested reply), which
  never reaches the transcript. `status-hook.py` now ties each turn to its `prompt_id` and ignores events whose
  prompt is not in the transcript; `status-daemon.py` takes a lock so two hooks cannot post two status messages.
- Fix: the daily restart and the nightly review failed when run by cron, whose PATH is only `/usr/bin:/bin`
  while `runuser` lives in `/usr/sbin` (it only worked when started by hand). `assistant.cron` and
  `assistant-daily-restart` now set the PATH, and `nightly-review.py` falls back to `/usr/sbin/runuser`. Tests added.
- Rich Telegram messages (Bot API 10.1+): `templates/telegram/send-rich.py` sends Markdown or HTML with
  `sendRichMessage` (headings, tables, lists, collapsible blocks), allowed in `settings.json` and described in the
  `CLAUDE.md` template; falls back to `reply` when Telegram rejects it. See [docs/telegram-extras.md](docs/telegram-extras.md#4-rich-messages-headings-tables-collapsible-blocks).
- README diagram redrawn with [Archify](https://github.com/tt-a1i/archify) instead of Mermaid: light and dark SVG,
  plus an interactive HTML version ([online](https://jonjunq.github.io/claudia/diagrams/how-it-works.html), GitHub Pages from `docs/`) and its source in
  [docs/diagrams/](docs/diagrams/).
- Memory tools (`templates/memory/`, installed root-owned to `/usr/local/lib/assistant-memory/`,
  [docs/memory.md](docs/memory.md)), two ideas taken from Hermes Agent:
  - `recall`: search old conversations and the diary through a SQLite FTS5 index (BM25, no model calls,
    incremental), with a `recall` skill and `Bash(recall *)` allowed. Replaces opening `.jsonl` transcripts by hand.
  - Nightly review: after the end of day, `assistant-daily-restart` runs a separate `claude -p` in a workshop (no
    settings, hooks, MCP, shell or network; deny rules outside it) that patches skills and memory with what the end
    of day missed. Changes are copied back only if they carry no secrets or invisible Unicode and the assistant did
    not touch the file meanwhile; never deletes; summary in `notes/last-review.md` (a silent Telegram message only
    with `REVIEW_NOTIFY=yes`). It picks up from the last message it read, so nothing written during a review is
    skipped. `REVIEW_MODEL` in `assistant.env`, `--dry-run` to try it. Measured cost in the docs.
  - Git history of `CLAUDE.md`, notes, skills and memory, owned by root (`assistant-history.timer`, hourly, and
    around each review), to undo any change.
- `CLAUDE.md` template: use `recall` for earlier days, and what the nightly review is.
- Setup: re-running `install.sh` adds new files without overwriting yours.

## 1.2.0 — 2026-11-02

- Telegram extras (`templates/telegram/`, installed root-owned to `/usr/local/lib/assistant-telegram/`, hooks in
  `settings.json`, [docs/telegram-extras.md](docs/telegram-extras.md)):
  - A "⏳ Working · 2 min 35 s / Now: <step>" message while a turn runs, edited every 5 s and deleted at the end, with
    ⚠️ when it waits for permission, sits on a dialog, makes no progress for 10 min or the session exits. Hooks plus
    a small daemon; no model calls.
  - Quoted and replied-to messages reach the assistant (`reply_to_text`, `reply_to_from`, `reply_quote`), via an
    idempotent patch of the official plugin that `start.sh` re-applies at every start and reports when it no longer fits.
  - Permission requests on Telegram with ✅ Allow / ❌ Deny buttons through a `PermissionRequest` hook that waits up to
    9½ minutes; the plugin's native relay is logged and silenced to avoid duplicates.
- `bin/permission-watch.sh`: reads the current permission dialog layout (the old one left the message empty) and
  does not repeat a request the hook already sent.
- Browser: `.claude/skills/browser` and [docs/browser.md](docs/browser.md) (agent-browser instead of improvised
  Playwright scripts; setup in an unprivileged LXC with Playwright's Chromium; measured on a real form: 0 failed calls
  instead of 13 of 40, about half the usage per step).
- Troubleshooting: chat-scoped bot menus hide the default one.
- `CLAUDE.md` template: "Quality first" section (best effort the first time, check facts before stating them and say
  what was not checked, "on it" when it takes longer, messages stay short).
- `docs/permissions.md`: teaching the auto-mode classifier about your setup with `autoMode.environment` and
  `autoMode.allow` (`"$defaults"` first, how to write the sentences, examples for home devices, an own server and
  creating accounts with an e-mail alias but never payments), and why only the admin edits them.
- `settings.json`: `switchModelsOnFlag: true`, so a reply flagged by the model's safeguards moves the session to
  another model instead of pausing it on a dialog nobody sees.
- `bin/permission-watch.sh`: also tells you on Telegram when the session changes model (read from `state.json`).
- Troubleshooting: safeguard flags, why switching model does not fix a flagged errand, and how to clear it.

## 1.1.0 — 2026-10-31

- `docs/homelab-read-access.md`: giving the assistant read-only visibility of Proxmox VE (`PVEAuditor` token),
  Proxmox Backup Server (`DatastoreAudit`) and dashboards, with a per-service firewall hole, credentials and
  certificate handling, a skill template and a test checklist, plus the threat model behind it.
- `docs/vetting-skills.md` and `templates/tools/vet-skill.sh`: scanning third-party skills with NVIDIA SkillSpector
  before installing them, skill folder by skill folder (whole-repo scores are dominated by false positives), pinned
  to the reviewed commit.

## 1.0.0 — 2026-10-31

First public version, distilled from an assistant in daily use since October 2026.

- `install.sh`: workspace, settings, systemd units and nightly cron for one user, without overwriting existing files.
- Workspace templates: `CLAUDE.md`, notes (`todo`, `yesterday`, `routines`, `diary/`), `assistant.env`.
- Scripts: restart loop with `--continue` and fallback, daily end of day + update + fresh conversation, status line
  for `/usage`, `/clear`, permission-prompt watcher, development-channel dialog acceptor, voice in (Groq / local
  faster-whisper) and out (ElevenLabs).
- Docs: setup, personality and memory, permissions, daily cycle, voice (with an experimental Discord call design),
  isolation, troubleshooting, comparison with Hermes Agent and a claude.ai Project.
