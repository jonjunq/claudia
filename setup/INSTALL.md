# Installing the assistant: the guide for the Claude Code that installs it

You are Claude Code, opened in a clone of this repo by someone who said "install yourself" (or "update", "repair",
"what is missing?"). They are probably **not technical**. Your job: leave them with a working assistant on
Telegram, with everything it can have, after asking them only for what only they can do, and having checked that
every piece works. This guide is the order to do it in. Two files tell you the rest:

- `setup/capabilities.json`: every capability, what it gives in plain words, its default, what it needs from the
  person (`needs` → the `human` list, with their step-by-step), how it is installed and where its code comes from.
  Never offer or install anything that is not in it without saying it is outside the kit.
- `assistant-doctor` (after `install.sh`, `/usr/local/bin/assistant-doctor`; before, `templates/system/assistant-doctor`):
  what is ✅ there, ❌ missing (with the fix), ⏭ declined, ○ optional. `--json` for you. It is the truth, not your
  memory of what you did.

## Rules for the whole installation

- **Their language, plain words.** Answer in the language they write in. No jargon ("a small free tool", not "a
  systemd unit"); if a technical word is unavoidable, explain it in five words. Short messages; never paste logs.
- **You do the work.** Run every command yourself. Ask the person only for what is in the `human` list of the
  manifest (and for their choices). Never hand them a command when you can run it; if you truly cannot (no root, no
  sudo), give them **one** command for a root terminal, say exactly where to type it, and wait.
- **Root.** Most steps need root. If you are not root, try `sudo -n true`; if that works, prefix with `sudo`. If not,
  ask them once for a root terminal (above). Never change sudoers or your own permissions.
- **Secrets.** Keys and tokens are pasted by them into this conversation. Pass them to `assistant-setup` on
  **stdin**, never as an argument, never echo them back, never write them anywhere else (not in notes, not in
  `CLAUDE.md`, not in a file of yours):
  `printf '%s' 'THE-KEY' | sudo assistant-setup key GROQ_API_KEY`. Tell them once, plainly: what they paste here
  passes through this conversation, like any command typed into Claude Code; at the end you will offer to delete it.
- **Do not impose where it runs** (read `docs/isolation.md`). Explain the options in plain words with what each
  risks, give your recommendation and why, and let them choose. Same for every optional piece: the default list
  goes in unless they say no; what is `ask` goes in only with their yes, after you said its risk in one line.
- **Check, then say.** After each step, the doctor for that capability (`assistant-doctor --only <id>`). Never tell
  them something works because the command ended without an error. Never say "done" while the doctor shows a ❌
  that they did not decline.
- **Two Claude Codes, one bot.** Only one program may read the bot's messages. The Telegram plugin of a second
  Claude Code session of the same user takes the bot over from the assistant. This repo's `.claude/settings.json`
  turns the plugin off for sessions opened here, so you are safe; never start other Claude Code sessions as the
  assistant's user outside this folder while it runs.
- **Not an installation?** If they want to change the kit's code, open an issue or a pull request, this guide does
  not apply: read `CONTRIBUTING.md` instead.

## Phase 0: look around (no questions yet)

```bash
cat /etc/os-release | head -3; id; sudo -n true 2>/dev/null && echo "sudo: yes"; nproc; free -g | head -2; df -h / | tail -1
systemctl --version 2>/dev/null | head -1; timedatectl 2>/dev/null | grep -i 'time zone'; node -v 2>/dev/null
cat /usr/local/share/assistant/install.conf 2>/dev/null
claude auth status --json 2>/dev/null | jq '{loggedIn, authMethod, subscriptionType}'
git -C . describe --tags --always; git -C . status --short | head
```

- `install.conf` exists: there is an installation already. Go to **Phase U** (upgrade and complete), not Phase 1.
- No systemd (`systemctl` missing, or a container without it): the kit needs it to keep the assistant running.
  Say so plainly and stop, or offer to continue by hand with `docs/setup.md`.
- Not Debian or Ubuntu: `assistant-setup` installs packages with `apt-get`; elsewhere tell them which packages
  each step needs (its error says it) and go on. The browser step is automated for Debian only.
- Memory: under 2 GB is too small. Under 4 GB: `voice-local` is skipped (the doctor marks it ⏭ by itself);
  the browser needs about 1.2 GB while open: say it will be tight. Disk: under 10 GB free, say so.
- A laptop, or a machine that sleeps: it works only while it is on. Ask in Phase 1.
- Note who you are running as (root, a user with sudo, a user without) and whether you are signed in to Claude with
  a subscription (`authMethod: claude.ai`). If the assistant will run as **this same user**, its sign-in is yours
  and the `claude-login` step disappears.
- Note the latest release: `git tag --sort=-v:refname | head -1`. Install from that tag
  (`git checkout <tag>`) unless they deliberately cloned another branch; if you are on `main` ahead of the last
  tag, say once that it is unreleased work and continue only if they agree.

## Phase 1: one message with everything

Send **one** message (headings, numbered lists, short lines) that they can work through at their own pace. Build
it from the manifest, filtered by what Phase 0 found. In this order:

1. **What I will set up for you** — the `base` and `everyday` capabilities, one line each in their language (from
   `gives`), grouped: talking to it (Telegram, voice notes), what it does for you (email/calendar/Drive, PDFs,
   videos, the browser), how it looks after itself (runs day and night, its nightly memory, notices of new versions
   explained in plain words, never applied without their yes). "Tell me if you do not want any of these."
2. **Optional, if you want it** — the `ask` capabilities, each with what it gives, its `cost` and its `risk`, in one
   or two lines. "Tell me the numbers you want." Two of them need a word more:
   - `voice-best`: the best-quality backup for voice notes, on this machine and without the internet (about 4 GB).
     Voice notes already go Groq → Cloudflare → Parakeet without it; it is for a transcript that came out wrong.
   - `email-watch`: if Phase 0 found no Node.js or one older than 24, say it adds an outside package repository
     (NodeSource, the usual source of current Node.js for Debian and Ubuntu), because n8n needs Node 24.
3. **A few choices**, each with your best guess so "yes" is enough:
   - Where it runs (docs/isolation.md), in plain words. Typical options on one machine: **a separate user just for
     it** (recommended when the machine has anything else on it: it cannot touch the rest, and the scripts that
     check it are out of its reach) or **as root, the machine is all its own** (simplest; it can install and look
     after anything itself, n8n included; only on a machine with nothing else on it, with backups outside). Say
     which you recommend for their case and why.
   - Its name, their name, the language it speaks (guess from how they write), their time zone (from Phase 0).
   - Optional: names it should spell right in voice notes (family, friends, places, brands).
   - Is this machine on all the time?
4. **What only you can do** — the `human` steps of everything that will be installed, numbered, each with its
   `why` in one line and its `steps` (keep the links exactly). Only the ones that apply: no `claude-login` if it runs
   as this user; no ElevenLabs if they did not want voice replies. Say what to paste back.
5. "Reply with your answers and whatever you have ready; we can do it in pieces. I start with what does not need
   you while you do yours."

Keep a checklist of the answers. Do not repeat the whole message later: ask for the next missing thing only.
Things they decline: record them (`assistant-setup decline <id> "<their words>"`), so neither you nor the assistant
offers them again.

## Phase 2: install

In this order (what needs them can wait while you do the rest). From the clone, as root (or with `sudo`):

1. **The user**, if they chose a separate one: `adduser --disabled-password --gecos "" <user>` (`assistant` unless
   they want another name).
2. **The base**: `./install.sh <user> --name <Name> --owner <Owner> --language <Language> --timezone <Area/City>
   --release-watch yes|no --idle-compact yes|no` (yes unless they declined). If `~/.claude/settings.json` already
   existed for that user it writes `settings.assistant.json`: run `assistant-setup merge-settings`.
   From now on `assistant-setup` and `assistant-doctor` are in `/usr/local/bin/`.
3. `assistant-setup install system`, then `assistant-setup install claude`.
4. **Signing in**, only if it runs as another user: `assistant-setup login` prints a link. Send it with the
   `claude-login` steps; when they paste the code: `printf '%s' 'CODE' | assistant-setup login-code`.
   Then `assistant-setup trust` (answers Claude Code's first-start questions for its workspace).
5. **Telegram**: `assistant-setup install telegram`. With their token:
   `printf '%s' 'TOKEN' | assistant-setup telegram-token` (it checks it with Telegram, prints the bot's name and
   saves it as `TELEGRAM_BOT_TOKEN` in `~/.claude/channels/telegram/.env`, where the plugin reads it).
   Then tell them: "now write anything to @<bot> from your Telegram", and run
   `assistant-setup telegram-owner --wait 240` (Bash timeout 300000). It prints the name of who wrote: ask them
   to confirm it is them. Then `assistant-setup install telegram-extras` (the patch, the buttons, the menu).
6. **Keys**, as they arrive: `printf '%s' 'KEY' | assistant-setup key GROQ_API_KEY` (also `CF_AI_TOKEN`,
   `CF_AI_ACCOUNT_ID`, `ELEVENLABS_API_KEY`). Each one prints the doctor's verdict for it. For voice replies:
   `assistant-setup voices`, let them pick a voice by name (offer two or three that fit their language), then
   `printf '%s' 'VOICE_ID' | assistant-setup set TTS_VOICE_ID` and `TTS_LANGUAGE` (`en`, `es`…).
   Names for voice notes: `printf '%s' 'Ana, Lisbon, Jellyfin.' | assistant-setup set TRANSCRIBE_NAMES`.
7. **Everything else they did not decline**, in one go:
   `assistant-setup install pdf links-videos browser voice-local wakeup idle-compact` plus the `ask` ones they
   chose (`voice-best`, `browser-window`, `email-watch`). Some take minutes (models, the browser): say so before.
   `browser-window` needs a way in from their phone: if they use Tailscale, `tailscale serve --bg 6080` (or bind to
   the address they reach), then `assistant-setup window-link <that address>`. Never expose port 6080 to the
   internet as it is (docs/browser.md). `email-watch` installs n8n; the email workflow itself the assistant sets up
   with them later, because it needs their Gmail app password.
8. **The version watch**: if they kept it, `assistant-setup install updates`. It follows what is installed (itself,
   Bun, the Telegram plugin, agent-browser, yt-dlp, the speech engines, n8n…), with an n8n workflow if n8n is there
   and a small daily timer if not. Every `install`, `remove` and `decline` refreshes it.
9. **Start it**, last: `assistant-setup install service nightly`. It prints the session's screen: if it is waiting at
   a question (a theme, a trust dialog, a sign-in), solve it (`assistant-setup trust`, `assistant-setup login`) and
   `systemctl restart assistant`; never accept a dialog you do not understand.

## Phase 3: check until it is green

`assistant-doctor --deep --json`. For each ❌, run its `fix` (or ask them for the human part), and check again;
three tries per item at most, then explain plainly what is wrong and what you suggest. It is done when everything is
✅, ⏭ (declined) or ○ (optional, not wanted, or for later); a ⚠️ is fine if you told them what it means.

- `connectors` cannot be seen until the assistant's next start after they connect them. If you run on the same
  Claude account, your own tools are a second check: `mcp__claude_ai_Gmail__*` present means Gmail is connected.
- Then a real test: ask them to send the bot "hello" and then a short voice note. Watch it answer
  (`sudo -u <user> tmux capture-pane -p -t assistant | tail -20`); the voice note should arrive already transcribed
  (a line in `~<user>/.claude/channels/telegram/voice.log`).

## Phase 4: hand it over

1. One short message: it is alive, write to @<bot>; three examples of what to ask it, in their words ("remind me
   to call the plumber tomorrow at ten", a voice note, "what do I have this week?"). In its first weeks it offers the
   rest itself, one thing at a time, so there is nothing else to learn now.
2. If anything ever breaks or they wonder what is missing: write to it "what are you missing?" (it runs the doctor),
   or open Claude Code in this folder again and say "repair".
3. Offer to delete this installation conversation, which holds the keys they pasted. With their yes, as the last
   thing you do: `rm -rf ~/.claude/projects/$(pwd | sed 's/[^A-Za-z0-9]/-/g')` (that is this folder's history;
   the session ends with it).

## Phase U: an installation that already exists ("update", "complete yourself", "repair")

Typical case: someone installed only the base by hand, and voice notes, PDFs or the browser never came. Or they ran
`git pull` and want what is new.

1. `assistant-doctor --json` and `cat /usr/local/share/assistant/install.conf`: what is installed, which version,
   which user.
2. If this clone is newer than the installed version: read `CHANGELOG.md` down to the installed version and look at
   `git diff <installed>..HEAD -- install.sh templates setup` as a reviewer (new destinations, downloads that run
   code, permissions, what runs as root), as the `updating` skill says
   (`templates/workspace/.claude/skills/updating/SKILL.md`). Tell them in a few plain lines what changes; with their
   yes: `./install.sh <user> --upgrade`, then deal with the `.new` files as that skill says (never overwrite their
   `CLAUDE.md` blindly).
3. `assistant-doctor --json` again. Everything ❌ or ○ that they have not declined: **one** message, as in Phase 1
   but only with what is missing (what it gives, its risk, what only they can do). Then Phase 2 for those, Phase 3,
   and restart the session last (`systemctl restart assistant`, after telling them it will be back in a minute).
4. The assistant itself can do this too, from Telegram, when it has root: the same steps, with the `updating` skill.
