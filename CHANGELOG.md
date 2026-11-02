# Changelog

## Unreleased

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
