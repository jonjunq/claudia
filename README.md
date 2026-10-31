# claudia

**A personal assistant you talk to on Telegram, built from plain [Claude Code](https://code.claude.com/docs) running
24/7 on your Claude subscription.** No agent framework and no API bill: one Claude Code session in an isolated
machine, the official Telegram channel plugin, a `CLAUDE.md` that gives it a personality, notes that survive a
daily restart, and a handful of small scripts that keep it alive unattended.

It reads and drafts your email, manages your calendar and Drive, keeps your to-do list, reminds you of things,
sends a morning summary, transcribes your voice notes and can answer with its own voice.

[Leer en castellano](README.es.md)

```mermaid
flowchart LR
  P[You, on your phone<br/>Telegram] <--> B[Telegram bot<br/>official channel plugin]
  B <--> C[Claude Code session<br/>in tmux, auto mode]
  C --- M[CLAUDE.md + memory<br/>notes/todo, yesterday, routines]
  C --> G[Gmail / Calendar / Drive<br/>claude.ai connectors]
  C --> W[Web, scripts<br/>voice in / out]
  S[systemd: keep alive,<br/>resume with --continue] --> C
  R[cron, daily:<br/>end of day, update, fresh session] --> C
```

> Unofficial project, not affiliated with or endorsed by Anthropic. Read [Is this allowed?](#is-this-allowed) first.

## Why not an agent framework?

We ran [Hermes Agent](https://github.com/NousResearch/hermes-agent) as our assistant first, and liked it: it is
built to be a proactive secretary. But it needs a model behind it paid per token, and the cheap model we used
(DeepSeek's) made up causes and wandered through extra steps. A Claude subscription cannot be plugged into
third-party agents, but it does cover Claude Code. Claude Code with
[channels](https://code.claude.com/docs/en/channels) turned out to be most of an assistant already; this repo is
the rest. The honest comparison, including what Hermes still does better, is in
[docs/comparison.md](docs/comparison.md).

## What you need

- A **Claude subscription** (Pro or Max; Max if you also code with Claude, because the assistant shares your usage
  limits).
- A small **always-on Linux machine you can isolate**: a VM, an LXC container, a mini PC, a cheap cloud VM. 2 cores,
  2-4 GB of RAM and 10 GB of disk are plenty without local voice models. See [docs/isolation.md](docs/isolation.md).
- `tmux`, `jq`, `curl`, `git`, [Bun](https://bun.sh) (the Telegram plugin runs on it) and Claude Code.
- A **Telegram bot** token from [@BotFather](https://t.me/BotFather).
- Optional: Gmail / Google Calendar / Google Drive connected in claude.ai (Settings → Connectors); a
  [Groq](https://console.groq.com) key for voice notes; an [ElevenLabs](https://elevenlabs.io) key for spoken replies.

## Quick start

```bash
# On the assistant's machine, as root
adduser --disabled-password --gecos "" assistant        # or any user name
apt install -y tmux jq curl git ffmpeg
git clone https://github.com/jonjunq/claudia && cd claudia
./install.sh assistant --name Claudia --owner Alex --language English --timezone Europe/London

# As that user: install Claude Code + Bun, log in, connect Telegram
su - assistant
curl -fsSL https://claude.ai/install.sh | bash
curl -fsSL https://bun.sh/install | bash
exec bash -l                             # pick up the new PATH
cd ~/assistant && claude                # log in with your subscription, then inside Claude Code:
#   /plugin install telegram@claude-plugins-official
#   /telegram:configure <bot token>
#   exit, and start once with: claude --channels plugin:telegram@claude-plugins-official
#   message your bot, then:  /telegram:access pair <code>  and  /telegram:access policy allowlist
nano ~/assistant/CLAUDE.md               # make it yours
exit

# As root: run it for good
systemctl enable --now assistant assistant-permission-watch
```

Then write to your bot. Step by step, with every gotcha we hit: [docs/setup.md](docs/setup.md).

## What's in the box

| Piece | What it does |
|---|---|
| `templates/workspace/CLAUDE.md` | Personality and rules: phone-sized answers, proactive, what it may do alone vs. ask first, memory discipline |
| `notes/todo.md`, `yesterday.md`, `routines.md` | The notebook it carries across days, imported into every conversation |
| `bin/start.sh` + `assistant.service` | Runs Claude Code in tmux and brings it back with `--continue` if it exits |
| `assistant-daily-restart` + cron | Every night: asks it to save the day, updates Claude Code, starts a fresh conversation |
| `settings.json` | Auto mode, plus an allowlist: reads and drafts run alone, sending and deleting ask you on Telegram |
| `bin/statusline.sh` | Saves context and plan usage so it can answer `/usage` from Telegram |
| `bin/clear-context.sh` | `/clear` from Telegram: fresh conversation mid-day, after saving what's pending |
| `bin/permission-watch.sh` | Tells you on Telegram when it is stuck on a prompt in its terminal |
| `bin/transcribe.sh`, `bin/speak.sh` | Voice notes in (Groq Whisper, local fallback) and out (ElevenLabs) |
| `templates/tools/vet-skill.sh` | Scans a third-party skill with SkillSpector before you install it |

## Documentation

- [Setup](docs/setup.md): machine, user, Claude Code, Telegram plugin, service, first run.
- [Personality and memory](docs/personality-and-memory.md): writing `CLAUDE.md`, the notes, the memory.
- [Permissions](docs/permissions.md): auto mode, the allowlist, why not `bypassPermissions`.
- [Daily cycle, routines and commands](docs/daily-cycle.md): end of day, morning summary, `/usage`, `/clear`.
- [Voice](docs/voice.md): voice notes, spoken replies and an experimental Discord voice call.
- [Isolation](docs/isolation.md): where to run it and how to fence it.
- [Eyes on your server, no hands](docs/homelab-read-access.md): read-only access to Proxmox, backups and dashboards, safely.
- [Vetting skills](docs/vetting-skills.md): checking third-party skills before installing them (SkillSpector, per skill).
- [Troubleshooting](docs/troubleshooting.md): the real problems we hit.
- [Comparison](docs/comparison.md): Hermes Agent, a claude.ai Project, and this.

## Is this allowed?

We are not lawyers, and the terms can change: read Anthropic's
[Legal and compliance](https://code.claude.com/docs/en/legal-and-compliance) page and the
[Consumer Terms](https://www.anthropic.com/legal/consumer-terms) yourself. What this setup does: **you** sign in to
the **unmodified** Claude Code binary with **your own** subscription, through Anthropic's own login, and the
assistant works for **you alone** (the Telegram allowlist only lets your account in). That page says subscription
OAuth "is designed to support ordinary use of Claude Code", that advertised plan limits "assume ordinary,
individual usage", and that third parties may not route requests through Free/Pro/Max credentials on behalf of
their users. So do not turn this into a bot for other people, a shared family assistant on one subscription, or a
service. If you need that, use an API key under the Commercial Terms.

## Credits

Built with Claude Code on the official [channels](https://code.claude.com/docs/en/channels) and
[claude-plugins-official](https://github.com/anthropics/claude-plugins-official) Telegram plugin. "One question with
your best guess" for vague requests comes from the `interview-me` idea in
[addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) (MIT); the "When you touch code" rules are
adapted from [Ponytail](https://github.com/DietrichGebert/ponytail) (MIT). Sibling project:
[loop-kit](https://github.com/jonjunq/loop-kit), an autonomous build loop for Claude Code.

MIT license, see [LICENSE](LICENSE).
