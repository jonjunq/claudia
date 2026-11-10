# claudia

**A personal assistant you talk to on Telegram, built from plain [Claude Code](https://code.claude.com/docs) running
24/7 on your Claude subscription.** No agent framework and no API bill: one Claude Code session on a machine of
yours, the official Telegram channel plugin, a `CLAUDE.md` that gives it a personality, notes that survive a daily
restart, and a handful of small scripts that keep it alive unattended.

It reads and drafts your email, manages your calendar and Drive, keeps your to-do list, reminds you of things,
sends a morning summary, transcribes your voice notes and can answer with its own voice. With the optional
[n8n](docs/n8n.md) kit it hears about new email within seconds and sets up alerts for you that cost no tokens.
And, as far as you want to take it: your TV, your media server, your computer, your money (read only), your
paperwork, appointments and trips. [What you can ask it](#what-you-can-ask-it), with the risk of each thing.

**Installing it is one sentence.** On an always-on Linux machine with Claude Code signed in to your subscription:
`git clone https://github.com/jonjunq/claudia && cd claudia && claude`, then say *"install yourself"*. That Claude
Code becomes its installer: it sends you **one** message with everything it will set up and the few things only you
can do, step by step (a Telegram bot from @BotFather, a free Groq key for voice notes, connecting Gmail, Calendar
and Drive in claude.ai; optionally ElevenLabs for a voice of its own), installs the rest itself, checks that every
piece works and says hello on Telegram. Already have one? *"Update yourself"* brings it up to date and offers what
it is missing. [How](#install-it).

[Leer en castellano](README.es.md)

<p align="center">
  <a href="https://jonjunq.github.io/claudia/video/claudia.mp4">
    <img src="docs/video/claudia.webp" width="320" alt="105-second video of a day with the assistant on a phone: it texts you first about rain on your padel evening and moves it; a voice note becomes a plumber booked in your calendar; it turns off the lights and puts on the film you mentioned; it watches your inbox, books a renewal and claims back a power bill charged twice; it orders batteries only after you say yes; it plans a trip to Rome with flights and a hotel and books them with your OK; it answers a shop's customers and gathers thirty people's status into one summary. You decide, she handles it.">
  </a>
</p>

<sub>▶ 1 min 45 s, no sound here · [full-quality video with sound](https://jonjunq.github.io/claudia/video/claudia.mp4). Everything in it is made up; some scenes are optional or untried uses ([what you can ask it](#what-you-can-ask-it)). Made with [HyperFrames](https://github.com/heygen-com/hyperframes).</sub>

<p align="center">
  <a href="https://jonjunq.github.io/claudia/diagrams/how-it-works.html">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="docs/diagrams/how-it-works-dark.svg">
    <img src="docs/diagrams/how-it-works-light.svg" width="100%" alt="How the assistant fits together: you chat on your phone with a Telegram bot, and the official channel plugin connects it to a Claude Code session in tmux, in auto mode, on your Claude subscription, on an always-on machine of yours (a container, a VM, a plain user or root: your call). Voice notes are turned into text on arrival (Groq, then Cloudflare, then a local engine). The session reads and writes CLAUDE.md, its notes and memory, uses a full browser with a remote window, the devices you allow (TV, media server) and optionally a limited card, and uses the claude.ai Gmail, Calendar and Drive connectors. Hooks send its status and permission buttons to Telegram, and a nightly cycle saves the day, reviews memory, updates Claude Code and restarts it. Optional, and costing no tokens until something happens: n8n alerts you directly when nothing needs thinking, and otherwise (new email, a new release) hands a one-line notice to the wake-up, which types it into the session; the session builds n8n workflows over MCP.">
  </picture>
  </a>
</p>

<sub>Larger version, light or dark following your system: [open it in your browser](https://jonjunq.github.io/claudia/diagrams/how-it-works.html). Drawn with [diagram-design](https://github.com/cathrynlavery/diagram-design) (MIT).</sub>

> Unofficial project, not affiliated with or endorsed by Anthropic. Read [Is this allowed?](#is-this-allowed) first.

## What you can ask it

You write to it (or send a voice note) as you would to a person. Below, what you can say, the risk of each thing in
one line, and its guide. **The full list, with what each one needs: [docs/recipes/](docs/recipes/README.md).**

**What ours does, every day or whenever it comes up**

- 🎙️ Walking down the street: *"Remind me to call the plumber tomorrow at ten."* A voice note is understood in
  about a second, and the reminder is there tomorrow.
  ⚠️ The audio goes to the transcription service you choose (or stays on your machine, slower). · [Voice](docs/voice.md)
- ☀️ Without asking: every morning, your day in one message (appointments, what is due, the emails that matter),
  ending with a proposal to leave the inbox at zero that you approve with one "yes".
  ⚠️ It reads all your email; whatever an email says is data, never an order. · [Daily cycle](docs/daily-cycle.md)
- 📧 *"Tell me if anything important comes in."* With [n8n](docs/n8n.md) it watches your inbox day and night and
  only speaks up when an email needs you, spending nothing while nothing arrives.
  ⚠️ n8n keeps a password that can read your email (on your machine). · [n8n](docs/n8n.md)
- 🧹 *"Unsubscribe me from all that advertising."* *"File my payslips in Drive as they arrive."*
  ⚠️ Unsubscribing tells the sender your address is alive: for shops you know, not for spam. · [Recipe](docs/recipes/email-cleanup.md)
- 📺 *"Put YouTube on the TV."* *"Install the media app on the projector."* Through the TV's own developer mode.
  ⚠️ Never ask it to root a device: it trips the model's safeguards and stalls the session. · [Recipe](docs/recipes/tv-and-projector.md)
- 🎬 *"I want to watch Dune tonight."* It asks your home media server, shows you the versions it found, downloads the
  one you pick and tells you when it is ready. It also takes the torrents you send it.
  ⚠️ Copyright law where you live, and fakes on public trackers. · [Recipe](docs/recipes/films-and-series.md)
- 💻 *"Turn on the computer in the study."* *"Turn it off, I forgot."* *"Start the Minecraft server for tonight."*
  ⚠️ An SSH key to your computer is a lot of reach: keep it narrow. · [Recipe](docs/recipes/your-computer.md)
- 📈 *"How is my portfolio doing this year?"* *"Anything odd in my account?"* It reads your bank, your funds and your
  crypto **read only**, draws the charts, and checks the bank quietly every morning, speaking up only if something
  looks wrong.
  ⚠️ Read-only must be set at the provider, not in a prompt; your financial data passes through the model. · [Recipe](docs/recipes/money-read-only.md)
- 🧾 *"Fill in this government form with my details."* *"Claim what my old employer owes me."* It works through
  complicated websites itself, keeps the reference and watches for the answer; if a captcha or a sign-in shows up,
  it sends you a link and you solve it from your phone.
  ⚠️ Submitting is a legal act in your name: it shows you the summary first, every time. · [Recipe](docs/recipes/errands-and-appointments.md)
- 🚗 *"Book the car inspection, any weekday after work."* It looks at several companies at once, checks the travel
  time at that hour and books the slot you choose.
  ⚠️ It books only what you pick; your details live in a private file. · [Recipe](docs/recipes/errands-and-appointments.md#appointments)
- ✈️ *"Rome the last weekend of the month, flights and a hotel, the whole price."* Totals with everything, the links,
  and once you book, every flight in your calendar and a reminder when check-in opens.
  ⚠️ Prices move by the hour; you pay, or the limited card does with your yes. · [Recipe](docs/recipes/trips.md)
- 📱 *"Watch this reel and tell me if it's true."* Links, reels and long videos: it transcribes them, looks at a few
  frames and checks the claims. On an Instagram account of its own, you share reels with it straight from the app.
  ⚠️ That Instagram route uses an unofficial API: it breaks Instagram's terms and can cost the account, so only ever
  its own account, never yours. · [Videos](docs/recipes/links-and-videos.md) · [Social media](docs/recipes/social-media.md)
- 🎓 *"What do I have to hand in this week?"* *"How many holiday days do I have left?"* Your course and your work
  portal, read only.
  ⚠️ Your school's and your employer's rules come first. · [Recipe](docs/recipes/study-and-work.md)
- 🖥️ *"Did last night's backup work?"* It keeps an eye on your home server without being able to change anything.
  ⚠️ The tokens must really be read-only. · [Guide](docs/homelab-read-access.md)
- 🗺️ *"Explain it to me in a diagram."* A picture or a one-page explainer instead of a wall of text.
  ⚠️ It is a third-party skill: check it before installing. · [Vetting skills](docs/vetting-skills.md)
- 🔎 *"What did I tell you about the boiler last month?"* It searches your old conversations.
  ⚠️ Everything you tell it stays on its machine: that is why the machine must be yours. · [Memory](docs/memory.md)

**What it can do if you set it up** (possible with what is here; not tried by us)

- 💡 *"Turn off the living-room lights."* With [Home Assistant](https://www.home-assistant.io)'s MCP Server
  integration, which only lets it touch the devices you expose.
  ⚠️ Expose nothing that is dangerous to switch by mistake (locks, alarms, ovens). · [Recipe](docs/recipes/smart-home.md)
- 🛒 *"Order the batteries."* *"Subscribe me to that, and remind me before it renews."* It pays with a
  [virtual card with its own small balance](docs/permissions.md#optional-paying-with-a-limited-card), only after your
  yes to that total. The pieces are here; we have not made a real purchase with it yet.
  ⚠️ The card's limit is the boundary that holds even if it is fooled: keep it small. · [Recipe](docs/permissions.md#optional-paying-with-a-limited-card)
- 🏷️ *"Sell my old camera, here are the photos."* An account of its own on a second-hand marketplace: it writes the
  listing, proposes the price and answers buyers; the deal goes through you.
  ⚠️ Scams aimed at sellers; never paid outside the platform. · [Recipe](docs/recipes/shopping-and-second-hand.md)
- 📣 Its own social media: it drafts the posts, publishes each one after your yes, and answers comments, through the
  network's official API.
  ⚠️ Public and permanent: your yes for every post. · [Recipe](docs/recipes/social-media.md)
- 📞 A phone number you can call it on, through a voice-agent service. (Ours takes calls on a Discord voice channel.)
  ⚠️ Pay-per-minute APIs, outside your subscription. · [Voice](docs/voice.md#experimental-a-voice-call-over-discord)
- 💬 A WhatsApp number of its own, or, for a shop, an agent that answers your customers (opening hours, stock,
  orders, appointments) and passes you what it does not know. Through the official WhatsApp Business Platform, and
  as a separate, limited agent without your email, card or home, because anyone can write to it.
  ⚠️ Automating a normal WhatsApp breaks its rules and can get the number banned.
- 👷 *"What are my people doing?"* Instead of calling thirty people, it messages each one, asks again if an answer
  is vague, and gives you one summary: who is on what, what is late, what is stuck.
  ⚠️ Your team must know they are talking to an assistant; work matters only, working hours only. · [Recipe](docs/recipes/study-and-work.md#your-team-possible-not-tried-by-us)

However you set it up, three rules hold: what it reads (emails, web pages, reels, strangers' messages) is data,
never orders; it asks before anything that leaves a mark (sending, publishing, paying, submitting, deleting); and the
limits that must hold even if it is fooled live outside the conversation (read-only keys, a card's balance,
`hard_deny`, a firewall rule).

You do not need to remember any of this: in its first weeks it offers these things itself, one at a time, when they
fit ([how](templates/workspace/.claude/skills/first-days/SKILL.md)). Or ask it *"what can you do?"*.

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
- An **always-on Linux machine**: a VM, an LXC container, a mini PC, a home server, a cheap cloud VM. 2 cores,
  2-4 GB of RAM and 10 GB of disk are plenty without local voice models. How isolated it is, is up to you:
  [Run it your way](#run-it-your-way).
- `tmux`, `jq`, `curl`, `git`, [Bun](https://bun.sh) (the Telegram plugin runs on it) and Claude Code.
- A **Telegram bot** token from [@BotFather](https://t.me/BotFather).
- Optional: Gmail / Google Calendar / Google Drive connected in claude.ai (Settings → Connectors); a
  [Groq](https://console.groq.com) key for voice notes; an [ElevenLabs](https://elevenlabs.io) key for spoken replies.

## Run it your way

This is open source, and there is no single right way to deploy it. We run ours as a normal user in its own
container, with the network fenced off and the admin installing system services, because it reads untrusted email
all day. You might prefer it as a user on the home server you already have, on a cloud VM, or as **root on a machine
that is entirely its own**, so it can install and look after everything itself (n8n included) and you never have to
step in. All of these work with the same files. The trade-off (more reach = more useful = more at stake if it is
fooled or makes a mistake) and what each option protects are in [docs/isolation.md](docs/isolation.md). Take what
fits, change the rest.

## Install it

The easy way, on the machine that will run it (a VM, a container, a mini PC… [your call](#run-it-your-way)), with
[Claude Code](https://code.claude.com/docs) installed and signed in with your Claude subscription:

```bash
git clone https://github.com/jonjunq/claudia && cd claudia && claude
```

Say **"install yourself"**, in your language. The repo's [CLAUDE.md](CLAUDE.md) points that Claude Code at
[setup/INSTALL.md](setup/INSTALL.md), and it:

1. looks at the machine (memory, disk, root or not, an installation already there?);
2. sends you one message: what it will set up by default (Telegram, voice notes, PDFs, videos, a real browser, its
   nightly memory, notices of new versions explained in plain words…), the optional pieces with their risk in one
   line, a few choices with its best guess (where it runs, its name, your language), and the numbered list of what
   only you can do, with the links;
3. installs everything else itself, with your keys passed straight into private files, never repeated;
4. checks each piece with `assistant-doctor` until it is all ✅ (or ⏭, what you said no to);
5. starts it, and it says hello on Telegram. In its first weeks it offers the rest, one thing at a time.

Everything it can install, with what each needs from you, is one list: [setup/capabilities.json](setup/capabilities.json).
`assistant-doctor` stays on the machine: run it, or ask your assistant *"what are you missing?"*, whenever you
wonder. Installed by hand before? Open Claude Code in an up-to-date clone and say *"update yourself"*.

### Quick start, by hand

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
systemctl enable --now assistant assistant-permission-watch assistant-history.timer
```

Then write to your bot. Step by step, with every gotcha we hit: [docs/setup.md](docs/setup.md).

## What's new

The latest changes (full list in [CHANGELOG.md](CHANGELOG.md)).

**1.7.0** (not released yet)

- **It installs itself** ([above](#install-it)): clone, open Claude Code, say *"install yourself"*. One message
  with what it will set up and what only you can do, step by step; it installs and checks the rest, and hands it
  over on Telegram. Before, `install.sh` set up the base and left voice notes, the PDF reader, the browser and the
  keys for you to find out about.
- **`assistant-doctor`**: every capability ✅, ❌ with the command that fixes it, ⏭ declined or ○ optional, free and
  without showing a single key. Your assistant runs it when it is unsure, and when you ask what it is missing.
- **`assistant-setup`**: one command per capability (`install pdf`, `install browser`, `key GROQ_API_KEY`,
  `telegram-owner`…), so neither the installer nor your assistant improvises. The PDF reader, yt-dlp and the local
  speech engines can now be installed by script, not only read about.
- **Notices of new versions of everything it uses**, not only of itself: Bun, the Telegram plugin, agent-browser,
  yt-dlp, the speech engines, n8n and third-party skills, with n8n or a small daily timer, set up by itself. It
  explains them simply (what the tool is, what is new for you, whether to update), groups the plain maintenance
  instead of nagging, and never updates without your yes. Only numbers and links reach it, never upstream text.

**1.6.0** (2026-11-05)

- **Everything you can ask it** ([above](#what-you-can-ask-it) and [docs/recipes/](docs/recipes/README.md)): what
  ours does every day, from the TV and the media server to read-only money, paperwork, trips and its own Instagram,
  and what is possible but untried, each with its risk in one line and a recipe: what it needs, how to ask your
  assistant to set it up, the `autoMode` sentence, the risks and what we learned. Ideas and risks only, no code, for
  what breaks a service's terms or touches money (unofficial social media APIs, banks and brokers).
- **One-click unsubscribe** ([recipe](docs/recipes/email-cleanup.md)): `templates/tools/unsubscribe.py` uses only the
  RFC 8058 link a sender signed with its own domain, over https, never to your home network, never by email.
- **Its first weeks offer more**: the `first-days` catalog now covers all of the above, each item pointing at its
  recipe on the assistant's own machine.

**1.5.0** (2026-11-05)

- **It keeps talking to you while it works** ([docs/context.md](docs/context.md)): heavy work (long browser
  errands, piles of PDFs and screenshots, long research, code) goes to four helpers that run in the background on
  the same model, so your next message does not wait and the main conversation does not fill up. What needs your yes
  is never delegated.
- **A lighter start**: tools, skills and connector instructions it never uses are left out. Measured on ours: the
  first call of a conversation -17 %, the second -23 %, and the same on every call after.
- **Safer compaction**: what must survive a summary is spelled out, and right after compacting it gets your last
  messages back word for word. Optional: compacting after a long idle spell.
- **`/usage` answered by the bot itself**, at once and at no cost, even while it is busy.
- **A more careful nightly review**: only what you said or what was seen to work becomes memory; nothing from an
  email or a web page alone. Skills nobody used in a month are listed for you.
- **Release notices from the install**: one question at the end of `install.sh`, a small daily check without n8n;
  it never updates without your yes.
- **The comparison** with Hermes and OpenClaw, updated for November 2026, and what we took from them.

**1.4.0** (2026-11-05)

- **Its first weeks, proactive** ([the skill](templates/workspace/.claude/skills/first-days/SKILL.md)): it offers
  what it can do or set up for you (email watched by n8n, voice notes, updates, the browser…), one thing at a time
  when it fits, in plain words with what it costs, and never asks again about something you turned down. It stops by
  itself after four weeks.
- **It keeps itself up to date, with your yes** ([docs/updating.md](docs/updating.md)): an n8n workflow tells it
  about new releases; it explains what they bring, reads the changes first and, once you agree, updates with
  `install.sh --upgrade`, which never overwrites what you changed (it writes a merged `.new` instead). Only tagged
  releases, never automatically.
- **Examples of what to ask it**, [above](#what-you-can-ask-it).
- **Voice notes arrive already transcribed** ([docs/voice.md](docs/voice.md)): the Telegram
  plugin patch downloads and transcribes them before the assistant sees them, which saves two turns (about 5 s) per
  note; downloads have timeouts; `transcribe.sh` falls back from Groq to Cloudflare Workers AI to Parakeet on the
  CPU, with your list of names so they come out right.
- **A real browser** ([docs/browser.md](docs/browser.md)): a full Chromium with a window on a
  virtual screen instead of the headless shell that bot protection rejects, two profiles, and an optional remote
  window so you solve captchas and sign-ins in the assistant's own session from your phone. No stealth tricks.
- **Optional: paying with a limited card** ([docs/permissions.md](docs/permissions.md#optional-paying-with-a-limited-card)):
  a virtual card with its own small balance, your yes to every purchase, the card never in the chat, and the
  `autoMode` rules that allow only that.
- **Devices away from home** over Tailscale ([docs/remote-devices.md](docs/remote-devices.md)):
  the assistant reaches one device on two ports, and the device reaches nothing.
- **Smaller context** ([docs/memory.md](docs/memory.md#keeping-the-context-small)): the
  conversation compacts at 300k tokens instead of near 1M, the to-do list loaded into every conversation stays short,
  the nightly review prunes skills instead of only adding, and `templates/tools/token-usage.py` shows where your
  tokens and context go.

**1.3.0** (2026-11-04)

- **Alerts that cost no tokens, with n8n** ([docs/n8n.md](docs/n8n.md)): an installer that hardens n8n, workflow
  templates (new email → wake the assistant; watch a page → tell you, and switch itself off when done), updates with
  backup and automatic rollback, and the assistant building workflows itself through n8n's MCP server.
- **Wake-up instead of Monitors** ([docs/wakeup.md](docs/wakeup.md)): a small daemon that types one-line notices
  into the session only when a watched log or n8n has something. It replaced a Monitor that cost ~48 empty turns a
  day.
- **Payments are hard-blocked** in `settings.json` (`autoMode.hard_deny`), because "never payments" inside an allow
  rule blocks nothing.
- **Writes for the phone**: Telegram rich messages with a title, emoji signposts, a quote for the main idea and
  numbered options to answer with a number ([an example](docs/telegram-extras.md#writing-for-the-phone)).
- **Approve from Telegram what the classifier blocks**, one time, for that exact call.
- **Run it your way**: the docs no longer assume an isolated container; they compare the options.
- Fixes: a phantom "⏳ Working" after turns without tools, and the nightly jobs under cron.

## What's in the box

The pieces, grouped by what they are for. Everything except the core is optional.

**Core**

| Piece | What it does |
|---|---|
| `templates/workspace/CLAUDE.md` | Personality and rules: phone-sized answers, quality first, proactive, what it may do alone vs. ask first, memory discipline |
| `notes/todo.md`, `yesterday.md`, `routines.md` | The notebook it carries across days, imported into every conversation |
| `bin/start.sh` + `assistant.service` | Runs Claude Code in tmux and brings it back with `--continue` if it exits |
| `assistant-daily-restart` + cron | Every night: asks it to save the day, updates Claude Code, starts a fresh conversation |
| `settings.json` | Auto mode, plus an allowlist: reads and drafts run alone, sending and deleting ask you on Telegram |
| `bin/statusline.sh` | Saves context and plan usage, which the bot uses to answer `/usage` on Telegram |
| `autoMode.hard_deny` in `settings.json` | Payments and money are blocked outright, whatever anyone asks |
| `bin/clear-context.sh` | `/clear` from Telegram: fresh conversation mid-day, after saving what's pending |
| `bin/permission-watch.sh` | Tells you on Telegram when it is stuck on a prompt in its terminal, or switches model after a safeguard flag |
| `setup/` (`INSTALL.md`, `capabilities.json`) + the root `CLAUDE.md` | The installer: a Claude Code opened in the repo follows the guide; one list of every capability, its default, what it needs from you and where its code comes from |
| `assistant-doctor`, `assistant-setup` | What is installed and working, with the fix for what is not; one command per capability to install it, record a no, save a key |

**Telegram and memory**

| Piece | What it does |
|---|---|
| `templates/telegram/` + hooks in `settings.json` | "⏳ Working" message while it works, quoted messages reach it, permission requests with Allow / Deny buttons, one-time approval of what the classifier blocked, rich messages (headings, tables) with `send-rich.py`, voice notes transcribed before they reach it |
| `templates/memory/` + `recall` skill | Searches old conversations (`recall`), reviews skills and memory every night, keeps a git history to undo |
| `.claude/agents/` (`browser`, `reader`, `researcher`, `coder`) | Helpers for heavy work, in the background and on the same model, so it keeps answering you and the conversation stays small |
| `after-compact.py` + Compact Instructions | After a compaction, your last messages and what is pending come back word for word; optional `assistant-idle-compact` for long idle spells |
| `first-days` skill + `notes/first-days.md` | Its first weeks: offers what it can do, one thing at a time, and remembers your answers |
| `updating` skill + `install.sh --upgrade` | Updates to a new release with your yes, merging the templates with your changes instead of overwriting them |
| `assistant-release-watch` + timer | Without n8n: once a day, tells it about new versions of itself and of its tools (numbers and links only), so it can tell you |

**Reacting to the world without spending tokens**

| Piece | What it does |
|---|---|
| `templates/wakeup/` (`assistant-wakeup`) | Types a one-line notice into the session only when a watched log or n8n has something for it; batches bursts, waits out permission dialogs, never goes through Telegram |
| `templates/n8n/` (`install-n8n.sh`, `n8n-admin`, workflows) | Installs n8n hardened, imports and publishes workflows from the shell, updates it with backup and rollback; templates for new email → assistant, new release → assistant, and page watch → you |

**Extras**

| Piece | What it does |
|---|---|
| `bin/transcribe.sh`, `bin/speak.sh` | Voice notes in (transcribed by the plugin on arrival: Groq, then Cloudflare, then Parakeet locally) and out (ElevenLabs) |
| `.claude/skills/browser` + `templates/browser/` | Uses websites through agent-browser and a full Chromium with a window instead of improvised scripts; optional remote window (noVNC) for captchas and sign-ins |
| `templates/tools/card-fill.sh` | Stores a limited virtual card for optional payments, without it passing through the chat |
| `templates/tools/vet-skill.sh` | Scans a third-party skill with SkillSpector before you install it |
| `templates/tools/pdf-read.py` | Reads a PDF as Markdown with PyMuPDF (tables and columns kept), and saves the scanned pages as images to look at |
| `templates/tools/unsubscribe.py` | One-click unsubscribe from newsletters, only with the link the sender signed (RFC 8058) |
| `docs/recipes/` | How to set up everything in [What you can ask it](#what-you-can-ask-it), with the risks; installed for the assistant to read |

## Documentation

- [Setup](docs/setup.md): the easy way (it installs itself), and by hand: machine, user, Claude Code, Telegram
  plugin, service, first run. The installer's own guide: [setup/INSTALL.md](setup/INSTALL.md).
- [Recipes: everything you can ask it](docs/recipes/README.md): the TV, films and series, your computer, the smart
  home, money read only, social media, accounts of its own, videos, a clean inbox, paperwork and appointments,
  trips, second-hand, your course and work. What each needs, how to ask for it, and the risks.
- [Personality and memory](docs/personality-and-memory.md): writing `CLAUDE.md`, the notes, the memory.
- [Permissions](docs/permissions.md): auto mode, the allowlist, why not `bypassPermissions`, and teaching the
  classifier which devices and services are yours.
- [Daily cycle, routines and commands](docs/daily-cycle.md): end of day, morning summary, `/usage`, `/clear`.
- [Context: helpers, a lighter start, compaction](docs/context.md): heavy work in subagents, what the fixed context
  carries, compaction that keeps what matters, with measurements.
- [Recall, nightly review and history](docs/memory.md): searching old conversations, improving skills and memory
  every night, and undoing it, with what it costs.
- [Telegram extras](docs/telegram-extras.md): a live "working" status, quoted messages, approving permissions with
  buttons, rich messages with tables, and voice notes transcribed on arrival.
- [Browser](docs/browser.md): agent-browser and a full Chromium for websites without an API, two profiles, a remote
  window for captchas and sign-ins, with measurements.
- [Voice](docs/voice.md): voice notes transcribed on arrival (a chain of engines, with measurements), spoken replies
  and an experimental Discord voice call.
- [Devices away from home](docs/remote-devices.md): reaching one remote device over Tailscale, and nothing else.
- [Run it your way](docs/isolation.md): where to run it (its own container, a user, root on its own machine, a cloud
  VM), what each option risks, and how to fence it if you want to.
- [Wake-up](docs/wakeup.md): reacting to logs and n8n with one-line notices instead of Monitors.
- [n8n](docs/n8n.md): alerts and automations that cost no tokens, built by the assistant itself, kept up to date.
- [Eyes on your server, no hands](docs/homelab-read-access.md): read-only access to Proxmox, backups and dashboards, safely.
- [Vetting skills](docs/vetting-skills.md): checking third-party skills before installing them (SkillSpector, per skill).
- [Updating](docs/updating.md): hearing about new versions of it and of every tool it uses, applying them with your
  yes without losing your changes, and why never automatically.
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
