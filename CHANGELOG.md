# Changelog

## Unreleased

Will be 1.7.0: new code that gets installed.

- **It installs itself.** A `CLAUDE.md` at the root of the repo (and an `AGENTS.md` pointing to it): a Claude Code
  opened in a clone that is asked to install, update or repair the assistant follows `setup/INSTALL.md`, a guide by
  phases: look at the machine (an existing install means upgrade and complete); **one** message to the owner with
  everything that will be set up, the optional pieces with their risk, a few choices with a best guess (where it
  runs, from `docs/isolation.md`, never imposed) and the numbered list of what only they can do, with the links (the
  bot from @BotFather, a free Groq key, the claude.ai connectors, optionally ElevenLabs and Cloudflare); install
  everything else; check with the doctor until it is green; hand it over on Telegram, and offer to delete the
  installation conversation, which holds the pasted keys. Contributors are sent to `CONTRIBUTING.md` instead.
- **`setup/capabilities.json`**: one list of every capability (22), what it gives in plain words, its default
  (`required`, `yes`, `ask` or `later`), what it needs from the owner (with step-by-step instructions), its risk or
  cost, how it is installed and where its code comes from. The guide, the doctor, `assistant-setup` and the version
  watch read it; the tests fail if a capability has no check or no install step.
- **`assistant-doctor`** (`/usr/local/bin`): ✅/⚠️/❌/⏭/○/❔ for each capability with the fix in one line, `--json`,
  `--offline`, `--deep` (opens the browser once), `--only`. No Claude tokens, never prints a key; keys are checked
  with one read-only request each (Telegram `getMe` and `getMyCommands`, Groq's model list, Cloudflare's Workers AI
  model search, the chosen ElevenLabs voice). As root, what runs as the user runs through `runuser`. Declines come
  from `notes/first-days.md` (`- <id>: no`), so neither the installer nor the assistant offers them again.
- **`assistant-setup`** (`/usr/local/bin`): `install <id>…` (system packages, Claude Code, Bun and the Telegram plugin,
  the patch and the bot's menu, the services, **the PDF reader** (PyMuPDF), **yt-dlp** in its own venv,
  **Parakeet** and **faster-whisper** with their models, **the browser** (Debian), the remote window, the wake-up,
  version notices, idle compaction, n8n), `remove`, `decline`, `accept`, `key` and `set` (from stdin, validated,
  mode 600), `telegram-token` (checked with Telegram first), `telegram-owner` (waits for the owner's first message
  to the bot and allowlists only that sender; refuses if two people wrote), `login` / `login-code` (the Claude
  sign-in for another user, through tmux), `trust` (the first-start questions), `merge-settings`, `voices`,
  `window-link`, `watch`.
- **Version notices for everything it uses**, not only for the kit: `assistant-release-watch` and the n8n workflow
  (now "Versions → wake the assistant", one workflow for a list) follow the upstream of every installed
  capability, from `assistant-doctor --watch-list`: GitHub releases (Bun), PyPI (yt-dlp, onnx-asr,
  faster-whisper), npm (agent-browser, n8n's `stable`), the Telegram plugin (against Claude Code's own catalogue)
  and third-party skills (by commit, from a `.installed-from` file). Claude Code (updates itself) and system packages
  are noted, never notified. `assistant-setup watch` builds it without asking anything: with n8n it imports the
  credential and the workflow and publishes it; otherwise the daily timer. It runs at the end of every `install.sh`
  and after every install, remove or decline; the doctor checks it is on and covers exactly what is installed. At
  most two notices a day (`claudia-release`, `tool-updates`), with names from our list, version numbers matching a
  strict pattern and links we build; never upstream text.
- Templates: `CLAUDE.md` runs the doctor when unsure or when asked what it is missing, explains new versions simply
  (what the tool is, what is new for the owner, whether to update), groups plain maintenance instead of nagging,
  and reads PDFs with `pdf-read.py`; `first-days` checks with the doctor before offering and records a no with
  `assistant-setup decline`; `updating` covers the tools (how to update each, and why the Telegram plugin waits for
  a kit release unless it is a security fix).
- **A second Claude Code no longer steals the bot from sessions opened in the repo**: the plugin replaces any poller
  it finds, so a session of the same user would take the assistant's messages. `.claude/settings.json` in the repo
  turns the plugin off there; troubleshooting says what to do otherwise.
- **No token or key on a command line any more.** The bot token (in Telegram's URLs) and the Groq, Cloudflare,
  ElevenLabs and wake-up keys (in headers) went to `curl` as arguments, which any user of the machine can read with
  `ps` while the request lasts. `assistant-setup`, `assistant-release-watch`, `lib.sh` (`tg_send`), `transcribe.sh`
  and `speak.sh` now give them to curl on stdin (`curl_secret`, a config read with `-K -`), and `install-n8n.sh`
  sends the n8n owner's password on stdin too. The tests fail if a token or key shows up in curl's arguments.
- `install.sh` installs `assistant-doctor`, `assistant-setup`, `capabilities.json` and the guide; its closing steps
  point to them.
- Tests: `tests/installer-tests.sh` (the manifest and the doctor agree; the doctor on a fake machine, keys accepted
  and rejected, `--offline` asks nobody, no secret in its output, declines and optional ones; `assistant-setup` keys,
  settings, the bot token and owner, trust, merge-settings, the n8n watch; the watched list matches what is installed
  and follows a tool installed or removed; the tool notices against fake GitHub, PyPI and npm: one notice, numbers and
  links only, each version once, the wake-up down), `tests/fake-apis.py`, and the n8n Code nodes for the list.

- **PDFs with PyMuPDF**, the reader our own assistant uses, instead of poppler's `pdftotext`: `assistant-setup install
  pdf` puts PyMuPDF and pymupdf4llm in a venv (`~/pdf`, about 300 MB; AGPL, no obligation for personal use), and
  `templates/tools/pdf-read.py` (root-owned, allowed in `settings.json`) gives the pages asked for as Markdown
  (`--pages 1-3,7`; tables and columns kept), says which pages have no text (scans) and saves them as PNGs with
  `--images DIR` for the assistant to look at (`--every-page` for all). A PDF is untrusted: a child process with a
  clean environment, a time limit, a CPU limit and a cap on what it writes, at most 200 pages at a time and 200 MB
  per file, nothing in the PDF opened, run or followed. `poppler-utils` stays, because Claude Code's own Read tool
  draws PDF pages with `pdftoppm`. The doctor reads a PDF made on the spot (as Markdown with `--deep`); the version
  watch follows both packages on PyPI; `CLAUDE.md`, the `reader` helper and the guides point to the tool.
- **`email-watch` installs Node.js 24 itself** when the machine's is missing or older (Debian 13 has 20): from
  NodeSource's apt repository, with its key checked against its fingerprint and used only for it (`signed-by`, in
  `/etc/apt/keyrings`), and a pin so that only `nodejs` comes from it; no setup script run from the internet. The
  installer says in one line that it adds an outside repository and why. n8n now goes under `/usr/local` whichever
  npm installs it (`install-n8n.sh`, `n8n-admin update`). The version watch notes Node.js as a system package, with
  its version and NodeSource's repository if it was added; the doctor says which Node n8n runs on.
- **Faster first answer**: `CLAUDE.md` now says that if answering needs any tool (beyond reading a note or looking at
  the calendar), the first action is a one-line reply saying what it will do, with no tool before it; small talk and
  what it can answer at once get a direct answer. Measured on ours: the first answer took a median of 16 s for
  questions and 28 s for errands, and now takes one model call, about 5-7 s. The Telegram "Working" status shows
  after 5 s instead of 15 (a short turn still deletes it when it ends).
- `CLAUDE.md` template: when to continue a helper with `SendMessage` and when to launch a new one (same request vs a new
  one, and a fresh helper once one carries ~150k of context), after a real helper grew to 262k from 7 chained requests.
- Reminders: the README ("What you can ask it") and `docs/daily-cycle.md` say how the kit keeps them
  (`notes/todo.md` and CronCreate) and two alternatives you can ask for: Google Tasks (with an OAuth client of your
  own) or an n8n table that sends them on Telegram without the assistant, at no token cost.
- **The browser no longer breaks when n8n is installed or updated.** n8n carries an old agent-browser (0.26, in
  `@n8n/mcp-browser`) and `npm install -g n8n` repointed `/usr/local/bin/agent-browser` to it
  (vercel-labs/agent-browser#2214, open). That copy predates the automatic Xvfb of 0.31.2, so the headed browser
  failed with "Missing X server or $DISPLAY" while the doctor still showed the installed version. `install-n8n.sh`
  and `n8n-admin update` (and its rollback) give the link back after each install; `assistant-setup install browser`
  always points it at its own copy, even when npm has nothing to update; `assistant-doctor` fails with the fix when
  the command is another copy (no `--deep` needed), and `--deep` says when Chromium found no display. Not an
  agent-browser 0.42.0 regression: 0.41.2 and 0.42.0 both open the browser with a window on Debian 13.
- **`browser-fast`, a cheaper browser helper** (`.claude/agents/browser-fast.md`, Sonnet with medium effort): only
  reading and comparing on public pages (prices, listings, product pages), with the browser skill; forms, sign-ins,
  the owner's data and payments stay with `browser`. `CLAUDE.md` says when to use each and not to pass `model`
  when launching a helper. For it to run on Sonnet, `start.sh` no longer sets `CLAUDE_CODE_SUBAGENT_MODEL_FORCE`:
  that flag ignores the model an agent definition asks for (anything but `inherit`), so it put `browser-fast` on
  the session's model too. The other helpers say `model: inherit` and now also follow a `/model` switch;
  `SUBAGENT_MODEL` sets the model for helpers that name none, and the new `SUBAGENT_MODEL_FORCE=yes` in
  `assistant.env` brings back the old behaviour (every helper on one model, `browser-fast` included).

## 1.6.0 — 2026-11-05

- **Everything you can ask it**: the README's "What you can ask it" (English and Spanish) now lists what our
  assistant does every day or whenever it comes up (the TV and the projector, films, series and torrents, the
  computer and game servers, money read only, paperwork and appointments, trips, videos and reels, a course and a
  work portal, a clean inbox, diagrams) apart from what is possible but untried (smart home, buying with the card,
  selling second-hand, posting on social media, a phone number, WhatsApp, a team summary), each with its risk in
  one line and a link to its guide.
- **docs/recipes/**: thirteen recipes and a full catalog (`docs/recipes/README.md`: what each thing needs, its main
  risk, its guide). Each recipe says what it needs, gives a message to ask your assistant to set it up, the
  `autoMode` sentence where one is needed (generic examples), the risks and what we learned. For what breaks a
  service's terms or touches money, ideas and risks only, no code: unofficial social media APIs (only ever an
  account of the assistant's own, with the rules we follow so it lasts) and banks, brokers and exchanges (read-only
  at the provider: exports, read-only keys, open-banking consent; never an online-banking password).
- **`templates/tools/unsubscribe.py`**: one-click unsubscribe (RFC 8058) from a sender's latest email over IMAP,
  read-only. It only sends the POST when the email offers one-click over https, the owner's provider saw a DKIM pass
  for a domain aligned with From whose signature covers both List-Unsubscribe headers (only the topmost
  Authentication-Results counts), and the host is a public address; no redirects, never `mailto:`, never a link
  from the body. `--dry-run`, `--eml` for a saved message. Folders by their special-use flags, so it works whatever
  the mailbox language.
- `install.sh` copies `docs/recipes/` next to the other guides, and the tools to `/usr/local/share/assistant/tools/`
  (root-owned, so an allow rule for one of them cannot be widened by editing it).
- **first-days**: the catalog offers the new things (`photo-dates`, `inbox-zero`, `links-videos`, `filing`,
  `money-read`, `social`, `second-hand`, `study-work`, `diagrams`) and the existing items point to their recipe; the
  first-weeks phase ends when the everyday and automation items have an answer (or after four weeks, as before).
- Fixed: the README said a Home Assistant token could be limited to some devices; Home Assistant tokens cannot. The
  recipe uses Home Assistant's MCP Server integration, which only reaches the entities exposed to Assist.
- Tests: the recipes and the tools are installed; `tests/unsubscribe-test.py` (offline: which emails it acts on,
  forged Authentication-Results, alignment, private addresses, HTTP errors, the exact POST, the command line).

## 1.5.1 — 2026-11-05

- **Idle compaction while the cache is still warm**: `assistant-idle-compact` now waits 52 minutes instead of 90, and
  its timer checks every 3 minutes instead of 10, so it compacts between about 52 and 56 minutes, before the 1-hour
  prompt cache expires. The compaction then reads the conversation at the cached price instead of writing it all
  again; the safety checks are unchanged. `IDLE_COMPACT_MINUTES` in `assistant.env` still changes it. To get it:
  `sudo ./install.sh <user> --upgrade`.

## 1.5.0 — 2026-11-05

- **Helpers for heavy work** ([docs/context.md](docs/context.md)): four subagents in
  `templates/workspace/.claude/agents/` (`browser`, `reader`, `researcher`, `coder`), on the same model as the session
  (`model: inherit`, and `start.sh` exports `CLAUDE_CODE_SUBAGENT_MODEL` + `CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1`, so
  built-in agents do not drop to a smaller model; `SUBAGENT_MODEL` in `assistant.env` to choose another), without the
  Telegram reply tools, n8n or `CronCreate`, and without the assistant's `CLAUDE.md` (their own rules instead). A new
  `CLAUDE.md` section says when to delegate (more than ~10 steps, a lot of text, more than 3-4 images), how to write a
  complete brief, to stay free for the owner while a helper works in the background, and that whatever needs the
  owner's yes (payments, sign-ups, emails, accounts, publishing workflows) is never delegated, and why.
- The Telegram hooks understand helpers: their events never open a "⏳ Working" turn (a background helper used to
  keep it on until it finished), a foreground helper's step shows as `helper <name> · …`, and permission requests and
  classifier blocks from a helper say `(helper <name>)`.
- **A lighter start** (`templates/settings.json`): `disableWorkflows`, `feedbackDrafts: "off"`, `deny` for
  `AskUserQuestion` (a terminal menu the owner never sees), `ScheduleWakeup`, `ReportFindings` and
  `Agent(statusline-setup)`, `skillOverrides` for developer skills, `autoDreamEnabled: false` (the nightly review
  already consolidates memory) and `bashOutputMaxChars: 15000`. Measured on one installation: the first call of a
  conversation 58,041 → 48,427 tokens (-17 %), the second 67,184 → 51,968 (-23 %). `deniedMcpServers` for unused
  claude.ai connectors is documented as an optional example, since everyone's connectors differ.
- **Compaction that keeps what matters**: a "Compact Instructions" section in `CLAUDE.md`, and
  `templates/memory/after-compact.py`, a `SessionStart` hook (matcher `compact`) that hands back the owner's last
  messages and the assistant's last answers, a pending permission, and a short checklist after every compaction.
- **Idle compaction, optional** (`install.sh <user> --idle-compact yes`): `assistant-idle-compact` + its timer type
  `/compact` (never `/clear`) after 90 minutes without messages or activity, only with more than 120k of context,
  no turn, permission, dialog or helper open, between 06:30 and 23:00, checked twice. It is the fallback for Claude
  Code's own `idleCompaction`, which is on by default but did not run every day for us.
- **`/usage` without the model**: plugin patch v3 answers it in the plugin itself, at once and at no cost, even while
  the assistant is busy, only for the allowlist (`$STATE_DIR/usage.log` keeps the time only). Checked against the
  real plugin 0.0.7 in `tests/plugin-e2e.py`.
- **Capped output**: a `CLAUDE.md` section for the assistant's own work (`head`/`tail`/`grep`, screenshots of the
  useful area at ≤1280 px, the PDF pages that matter).
- **Nightly review**: a provenance rule (only what the owner said or what was seen to work becomes memory or a
  skill; never content whose only source is an email, a page, a document or a notice), every conversation line
  labelled with who wrote it (`helper` included), added lines that read like planted instructions rejected, and the
  skills and references nobody used in 30 days listed in `notes/last-review.md` (never deleted).
- **`recall`**: when no message has all the words it searches again for any of them (and says so); helpers' work is
  indexed as `helper` (with `--all`). The git history keeps `.claude/agents/` too.
- **Release notices from the install**: at the end of its first run `install.sh` asks whether to turn them on
  (`--release-watch yes|no` from a script). Without n8n, `assistant-release-watch` + its daily timer ask GitHub for
  the latest release and wake the assistant through the wake-up with one line, numbers only, once per release; with
  n8n already installed, the existing workflow template is used instead. The choice goes to `install.conf`
  (`RELEASE_WATCH`, `RELEASE_WATCH_HOW`); if it was not accepted, the `first-days` skill offers it once, early.
  Nothing is ever updated without the owner's yes.
- **docs/comparison.md**: since 4 April 2026 the Claude subscription does not cover third-party harnesses such as
  OpenClaw or Hermes; where Hermes (v0.22.7) and OpenClaw are now; what we took from them and what we did not.
- **A video** at the top of the README (English and Spanish).
- Tests: helpers installed and filled in, the hooks with foreground and background helpers, the helper label on
  permission requests, `/usage` in the patch, the settings, `after-compact.py`, the idle compaction (compacts, and
  waits for permissions, dialogs, helpers, hours, small contexts and recent activity), the release watch against a
  fake GitHub and wake-up (newer, once, pre-releases, nothing of the release text, wake-up down), the review's
  injection check and unused skills, `recall`'s retry and helpers, and the install flags.
- Upgrading from 1.4.0: `install.sh <user> --upgrade` from the `v1.5.0` tag. Your `CLAUDE.md` and `settings.json`
  get a merged `.new` if you changed them (review the new sections and settings before taking it); the helpers, the
  hooks, the patch and the new scripts are added or replaced. Restart the session last.

## 1.4.0 — 2026-11-05

- **First weeks, proactive** (`templates/workspace/.claude/skills/first-days/`): a new owner should not need the
  docs to find out what the assistant can do. While `notes/first-days.md` says `phase: active`, the assistant offers
  the things in the skill's catalog (connectors, the morning summary, voice notes, email watched by n8n instead of
  by its own turns, release notices, page watches, the browser and errands, TV and media, a home server, payments
  with a limited card, accounts of its own, and, as possibilities, Home Assistant, a WhatsApp Business agent and
  team check-ins): it checks first what is already set up, offers one thing a day at most at a natural moment, in
  plain words with what it costs and risks, never asks again after a no, and asks once more after a "later". The
  phase ends by itself after four weeks or when everything has an answer. A new `CLAUDE.md` section points to it.
- **Release notices with n8n** ([docs/updating.md](docs/updating.md)):
  `templates/n8n/workflows/release-watch-to-wakeup.json` asks GitHub once a day for the latest release (no token
  needed; drafts and pre-releases skipped) and, if it is newer than the installed version, wakes the assistant with
  one line: the version and a link built from the tag, so no release text reaches its terminal. Each release is
  reported once. Without n8n: GitHub's Watch → Releases email, or a weekly routine.
- **The `updating` skill**: only tagged releases, never `main`; the changelog and the diff of `install.sh` and
  `templates/` read first, as a reviewer (new destinations, code downloads, hooks, permissions, root); a short
  plain-words summary with options; nothing without the owner's yes; backup, `install.sh --upgrade`, the `.new`
  files reviewed, restarts with the session last, checks, and a report with how to undo it. Why: if the repo were
  compromised, every installation that updates itself would run the bad code.
- **`install.sh --upgrade`**: a file you never changed is replaced (old copy as `<file>.bak-<date>`); a file you
  changed is left alone and gets `<file>.new` with both sets of changes merged by `git merge-file` (`CONFLICT` with
  `<<<<<<<` markers when both touched the same lines). The wake-up token and your install settings are kept, the n8n
  kit copies, `n8n-admin` and the guides are refreshed. Installs from before 1.4.0 have no record of the originals:
  the first upgrade replaces the root-owned code under `/usr/local/` (with a `.bak`) and writes the plain template
  as `.new` for the other files that differ. Without `--upgrade` it still only adds what is missing.
- `install.sh` writes `/usr/local/share/assistant/install.conf` on every run (version from `git describe`, or from
  `CHANGELOG.md` without git; the source repo; `--name`, `--owner`, `--language`, `--timezone`, which later runs
  now reuse), keeps the base copies in `/usr/local/share/assistant/installed/`, and copies every guide and the
  changelog to `/usr/local/share/assistant/docs/` (the template `CLAUDE.md` points there now; the old
  `assistant-n8n/docs/` copies stay for older `CLAUDE.md` files).
- README and README.es: **what you can ask it**, everyday examples in plain words, with what we use daily separated
  from what is possible if you set it up.
- Tests: the upgrade cases (untouched, merged, conflict, no base, token kept, nothing to merge the second time, the
  version without git) and the release watch's Code node (numbers compared as numbers, pre-releases, once per
  release, no release text passed on); the workflow was also run against GitHub's real API in n8n.

- **Devices away from home** ([docs/remote-devices.md](docs/remote-devices.md), optional): the assistant on Tailscale
  in userspace mode with its own tag, a policy whose grants only let it open specific ports on a tagged device (which
  can open nothing), tests in the policy, `tailscale nc` as SSH `ProxyCommand`, a one-off pre-authorised tagged key;
  and why it matters: with the default policy and a subnet router, any new node sees your LAN.
- **Optional: paying with a limited card** ([docs/permissions.md](docs/permissions.md#optional-paying-with-a-limited-card)),
  off by default (the template still blocks every payment): a virtual or prepaid card with a separate balance,
  `templates/tools/card-fill.sh` to store it (mode 600, outside the workspace, number and code read without echo),
  the form filled from variables so the number never reaches the transcripts that `recall` indexes, your yes to
  each purchase (site, product, total; subscriptions with price and period, a list and a reminder before renewals),
  and the three `autoMode` sentences: `environment`, an `allow` for that card only with your yes, and a `hard_deny`
  rewritten to forbid everything else. The browser skill has the steps.
- **A full browser with a window** ([docs/browser.md](docs/browser.md#which-browser-underneath-a-full-chromium-with-a-window)):
  Debian's Chromium in headed mode on Xvfb (agent-browser starts it) instead of the headless shell, whose
  `HeadlessChrome` user agent got a CloudFront site's 403 in 0.1 s and was refused by a big provider's sign-in; with
  the full browser the same site opens in 2-3 s. `templates/browser/agent-browser-config.json`, two profiles
  (clean, and one for signed-in sites), the measurements, and the fix for Xvfb/Chromium crashing in a container
  without a GPU (leftover NVIDIA EGL/Vulkan files). The rule: a standard browser yes; user-agent changes, stealth
  and captcha solvers no.
- **Remote window** (optional, not enabled): `assistant-window-vnc.service` (x11vnc on localhost that attaches to
  the newest browser only when you connect, via `templates/browser/current-display`) and
  `assistant-window-web.service` (noVNC/websockify on localhost), so you solve a captcha or a sign-in in the
  assistant's own session from your phone. The doc compares ways to protect it (a VPN, or a proxy with a login and
  a passkey, plus a firewall) without requiring any.
- The browser skill: the two profiles, when to send the remote window, captchas, and the no-stealth rule.
- **Voice notes transcribed before the assistant sees them** ([docs/voice.md](docs/voice.md),
  [docs/telegram-extras.md](docs/telegram-extras.md#5-voice-notes-transcribed-on-arrival)). Timing 117 real notes
  showed the speech-to-text took 0.4 s of the 17.5 s from arrival to answer, while the assistant's two extra turns
  (download, then transcribe) took about 5 s. `patch-telegram-plugin.py` v2 makes the plugin download and transcribe
  voice notes (up to 15 min) and audio files (up to 5 min) after its access check and deliver the transcript as the
  message, tagged `voice_transcribed_by` and `voice_path`; on any failure, or past 55 s, the notification goes out as
  before. Measured on the real setup: about 0.7 s from arrival to a transcribed notification.
- The plugin's downloads get timeouts: `getFile` and the file fetch (10 s / 15 s for voice, 30 s for
  `download_attachment` and photos), one retry each. A hung download had once held a note for two minutes; now
  `download_attachment` returns an error after about a minute.
- **`transcribe.sh`: a chain of engines** with timeouts: Groq (5 s to connect, `TRANSCRIBE_MAX_TIME`, one retry on a
  network error or 5xx, none on a 429) → Cloudflare Workers AI `whisper-large-v3-turbo` (optional) → Parakeet TDT
  0.6B v3 on the CPU (optional, about 5 s for a 12 s note) → faster-whisper (optional) → a clear error.
  `TRANSCRIBE_NAMES` in `assistant.env` gives the cloud engines the names they misspell. The engine goes to stderr.
  It used to wait up to 300 s on a hung Groq call.
- Upgrading (`install.sh` never overwrites, [docs/setup.md](docs/setup.md#updating)): copy
  `templates/telegram/patch-telegram-plugin.py` to `/usr/local/lib/assistant-telegram/` and `bin/transcribe.sh` to
  your workspace; the patcher rebuilds a v1-patched plugin from `server.ts.orig` at the next start. Copy the new
  voice-notes rule from the `CLAUDE.md` template into yours, and add `TRANSCRIBE_NAMES` and `PARAKEET_VENV` to your
  `assistant.env` if you want them.
- Tests: the patch on a stand-in with the new anchors (and the upgrade from v1), `transcribe.sh` with a fake curl, and
  [`tests/plugin-e2e.py`](tests/plugin-e2e.py), which runs the real plugin against `tests/fake-telegram.py` (now able
  to serve updates and files, or hang); not in CI because it needs bun.

- **Smaller context** ([docs/memory.md](docs/memory.md#keeping-the-context-small)), from measuring a week of use:
  - `"autoCompactWindow": 300000` in `templates/settings.json`: an all-day conversation averaged ~300k tokens of
    context per message (peaks near 880k); it now compacts at 300k.
  - The end of day keeps `notes/todo.md` (imported into every conversation) to about 8 KB of open items; done items
    and details go to the diary.
  - The nightly review prunes: no more "be active", a rule that replaces another deletes it, a `SKILL.md` over ~15 KB
    is split into `references/` files, and a new skill needs the same class of task in several conversations. It
    still never deletes whole files.
- **`templates/tools/token-usage.py`**: tokens per day and average / peak / starting context per project, read from
  Claude Code's transcripts (repeated usage lines counted once). Tests included.
- README diagram redrawn with [diagram-design](https://github.com/cathrynlavery/diagram-design) (MIT) instead of
  Archify, generated by `docs/diagrams/how-it-works.py`: it now shows the wake-up and n8n (with its MCP server), no
  longer suggests an isolated machine is required, and its light/dark SVGs embed their fonts as subsets so they look
  the same inside GitHub's `<img>`. See [docs/diagrams/README.md](docs/diagrams/README.md).

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
