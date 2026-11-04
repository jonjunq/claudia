# Setup

About an hour the first time. The steps below are how we do it: one normal user on a machine of its own. Adapt
them to your layout; [Run it your way](isolation.md) compares the options (its own container, a user on a machine
you already have, root on a machine that is all its own, a cloud VM).

## 1. The machine

Any always-on Linux box: a VM, an LXC container, a mini PC, a home server or a small cloud VM. Debian or Ubuntu make
the commands below work as written. 2 cores, 2-4 GB of RAM and 10 GB of disk are plenty for the assistant itself;
the full browser ([browser.md](browser.md)) adds about 1.2 GB of RAM while it is open, and the local Parakeet
fallback for voice notes ([voice.md](voice.md)) up to 2.4 GB while it transcribes and about 1 GB of disk (we use
6 GB of RAM with both). Decide how much of your network it should see before you give it your email: [isolation.md](isolation.md).

Set the time zone (`timedatectl set-timezone Europe/London`): reminders, routines and the daily restart all use it.

```bash
apt install -y tmux jq curl git ffmpeg     # ffmpeg only for voice
adduser --disabled-password --gecos "" assistant
```

## 2. The workspace and services

```bash
git clone https://github.com/jonjunq/claudia && cd claudia
./install.sh assistant --name Claudia --owner Alex --language English --timezone Europe/London
```

It creates, without overwriting anything that exists:

| Path | What |
|---|---|
| `~assistant/assistant/` | The workspace: `CLAUDE.md`, `assistant.env`, `notes/`, `bin/` |
| `~assistant/.claude/settings.json` | Permissions, plugin, status line (if a settings file exists it writes `settings.assistant.json` for you to merge) |
| `~assistant/.config/assistant/keys.env` | API keys for the optional voice scripts (mode 600) |
| `/etc/systemd/system/assistant.service` | Runs `bin/start.sh` inside a tmux session called `assistant` |
| `/etc/systemd/system/assistant-permission-watch.service` | The permission-prompt watcher |
| `/usr/local/sbin/assistant-daily-restart` + `/etc/cron.d/assistant` | The nightly end of day (05:45 by default) |
| `/usr/local/share/assistant/` | `install.conf` (version and settings), the guides for the assistant to read, and a copy of what was installed, for upgrades |

Nothing starts yet.

## 3. Claude Code and Bun, as the assistant's user

```bash
su - assistant
curl -fsSL https://claude.ai/install.sh | bash      # Claude Code (native installer, auto-updates)
curl -fsSL https://bun.sh/install | bash            # the channel plugins are Bun scripts
exec bash -l
cd ~/assistant && claude
```

Log in with your Claude account (the subscription, not an API key) and accept the workspace trust prompt for
`~/assistant`. Then pick the model: `MODEL=` in `assistant.env`. We use Opus: the largest model is slower on a phone
and spends more of your limits, and Sonnet falls short on longer errands. `start.sh` passes the model explicitly
because a resumed conversation otherwise keeps the model it was created with.

## 4. Telegram

1. In Telegram, talk to [@BotFather](https://t.me/BotFather), send `/newbot`, pick a name and a username ending in
   `bot`, copy the token. Never paste that token into a chat (including with the assistant); if you do, regenerate it.
2. In Claude Code:
   ```
   /plugin install telegram@claude-plugins-official      (choose user scope)
   /telegram:configure <token>
   ```
   The token is saved in `~/.claude/channels/telegram/.env`.
3. Exit and start once by hand with the channel:
   ```bash
   claude --channels plugin:telegram@claude-plugins-official
   ```
4. Send any message to your bot. It answers with a pairing code. In Claude Code:
   ```
   /telegram:access pair <code>
   /telegram:access policy allowlist
   ```
   From now on only your Telegram account reaches the session; everyone else is silently dropped. The allowlist lives
   in `~/.claude/channels/telegram/access.json`. Anyone on it can also approve permission prompts, so keep it to you.
5. Say hello from Telegram and check that it answers. Exit Claude Code.

The plugin's own commands (`/start`, `/help`, `/status`) are for pairing; `/status` is taken by the plugin, which is
why the assistant's usage command is `/usage`. To show your commands in the bot's menu:

```bash
TOKEN=...; CHAT=...   # your bot token and your numeric chat id (the id in access.json)
curl -s "https://api.telegram.org/bot$TOKEN/setMyCommands" -H 'Content-Type: application/json' -d '{
  "commands": [{"command":"usage","description":"Context and plan usage"},
               {"command":"clear","description":"Start a fresh conversation"}],
  "scope": {"type":"chat","chat_id":'"$CHAT"'}}'
```

## 5. Email, calendar and Drive (optional)

Connect Gmail, Google Calendar and Google Drive in claude.ai (Settings → Connectors) with the same Claude account.
Claude Code picks the connectors up as `mcp__claude_ai_Gmail__*` and so on. `settings.json` already lets the
assistant read, search, draft, label and manage the calendar alone, and makes it ask you (on Telegram) before
sending, forwarding, trashing, marking spam or sharing. Adjust it in [permissions.md](permissions.md).

## 6. Make it yours

Edit `~/assistant/CLAUDE.md` ([personality-and-memory.md](personality-and-memory.md)). Write it in the language you
want it to speak. Put your morning summary and other recurring tasks in `notes/routines.md`.

## 7. Run it for good

```bash
exit                                                    # back to root
systemctl enable --now assistant assistant-permission-watch assistant-history.timer
sudo -u assistant tmux attach -t assistant              # watch it; detach with Ctrl+B D, never Ctrl+C
```

What happens from now on:

- `assistant.service` starts tmux, and `bin/start.sh` runs Claude Code in it with the Telegram channel.
- If Claude Code exits, `start.sh` relaunches it in 10 s with `--continue`, so the conversation goes on. If
  `--continue` fails within 30 s (there is nothing to continue), it starts a new conversation instead; if it fails
  after a while, the next round resumes again rather than throwing the conversation away.
- Every night the daily restart asks it to save the day, reviews its skills and memory, updates Claude Code and
  starts a clean conversation ([daily-cycle.md](daily-cycle.md), [memory.md](memory.md)).
- Every hour `assistant-history.timer` commits its notes, skills and memory to a root-owned git history.

One gotcha baked into `start.sh`: when you pass a first prompt to `claude`, put it **before** `--channels`.
`--channels` takes several values and swallows a prompt placed after it.

## 8. Optional: wake-up and n8n

- **Wake-up** ([wakeup.md](wakeup.md)): if the assistant should react to things other than your messages (a log
  that gets a new line, an email, a job that fails), `systemctl enable --now assistant-wakeup` lets them reach it as
  one-line notices, without Monitors that cost a turn every 30 minutes.
- **n8n** ([n8n.md](n8n.md)): for alerts that need no thinking (a tracking page, a price, a site that goes down) and
  for watching your inbox in real time. `/usr/local/share/assistant-n8n/install-n8n.sh` installs it; after that the
  assistant can build the workflows itself.

## Updating

The assistant can do this for you, with your yes: it hears about new releases (with n8n, or a GitHub
notification), explains what they bring, and applies them without overwriting your changes. How, and why it never
updates on its own: [updating.md](updating.md).

By hand, from the release's tag (not `main`):

```bash
git fetch --tags && git checkout v1.5.0        # in your clone; read CHANGELOG.md first
sudo ./install.sh <user> --upgrade
```

Files you never changed are updated (the old copy stays as `<file>.bak-<date>`); files you changed are left alone
and get a `<file>.new` with your changes and the template's merged, for you (or the assistant) to review and move
over. Then `systemctl daemon-reload` and restart what changed. Installs from before 1.4.0 have no record of the
original files, so the first upgrade writes the plain new template as `.new` for every file of yours that
differs (except the root-owned code under `/usr/local/`, which it replaces, keeping a `.bak-<date>`). Claude Code itself updates every night; n8n, if you use it, does not: `n8n-admin update`
([n8n.md](n8n.md#keeping-it-updated)).
