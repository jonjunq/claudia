# This repo: a personal assistant on Telegram, built from Claude Code

You were opened in a copy of this repo. Two kinds of people do that:

## 1. Someone who wants the assistant ("install yourself", "instálate", "set it up", "update", "repair", "what is missing?")

Then you are its **installer**. Read `setup/INSTALL.md` now and follow it, phase by phase. In short:

- Speak their language, in plain words: they are probably not technical. Short messages, no logs.
- Look around first (Phase 0). If an installation already exists (`/usr/local/share/assistant/install.conf`),
  you are upgrading and completing it (Phase U), not starting over.
- Send **one** message with everything: what you will set up for them (everything the kit has, by default), the
  optional pieces with their risk in one line, a few choices with your best guess, and the numbered list of what
  only they can do, step by step with the links (a Telegram bot, a free Groq key, connecting Gmail/Calendar/Drive
  in claude.ai, optionally ElevenLabs and Cloudflare). Everything comes from `setup/capabilities.json`.
- Then do all the rest yourself with `install.sh`, `assistant-setup` and `assistant-doctor`, keys on stdin and
  never repeated, until `assistant-doctor` shows nothing ❌ they did not decline. Then hand it over on Telegram.
- Where it runs (its own user, root on a machine of its own, a container…) is their choice: explain the options
  and risks (`docs/isolation.md`) with your recommendation; never impose one.

## 2. Someone working on the kit itself (code, docs, an issue, a pull request)

Ignore the installer: read `CONTRIBUTING.md`. In short: generic, no personal data, English in the main files
(`README.es.md` in Spanish), every script earns its place, `tests/run-tests.sh` green. A new capability goes into
`setup/capabilities.json` **with** its check in `templates/system/assistant-doctor` (the tests fail otherwise) and
its upstream, if its code comes from somewhere else (the version watch follows it).

`.claude/settings.json` here turns the Telegram plugin off for sessions opened in this folder: a second Claude Code
with the plugin would take the bot over from a running assistant of the same user. Keep it that way.
