# Updating: hearing about new versions, and applying them safely

The assistant can keep itself up to date: it hears about a new release of this repo or of any tool it was installed
with, tells you in plain words what it brings, and with your yes backs up, applies it without overwriting what you
changed, checks that everything still works and tells you how it went. You do not need to follow any of those
projects yourself.

Two rules it never breaks, and why:

- **Only tagged releases, never `main`.** A release is a version someone decided was ready, with notes; `main` is
  work in progress. For the tools, only the versions their source publishes.
- **Never without your yes, and never without reading the changes first.** If this repo were ever compromised (a
  stolen token, a malicious pull request merged by mistake), every installation that updated itself automatically
  would run the bad code within a day, with the reach the assistant has on your machine. A human yes after the
  assistant has read the diff (and told you about anything odd) is the brake. The same goes for any fork you
  install from.

## 1. Knowing what is installed

`install.sh` writes `/usr/local/share/assistant/install.conf` on every run: the version (`git describe`, e.g.
`v1.5.0`, or `v1.4.0-3-gabc1234` for three commits after 1.4.0; from a download without git, the newest release in
`CHANGELOG.md`), the repo it came from, and the settings you installed with (`--name`, `--owner`, `--language`,
`--timezone`, and your answers to `--release-watch` and `--idle-compact`), which later runs reuse. It also keeps a copy of every file exactly as it wrote it, in
`/usr/local/share/assistant/installed/`: that is how an upgrade tells apart the files you changed from the ones you
did not. The guides and the changelog are copied to `/usr/local/share/assistant/docs/` so the assistant can read
them.

## 2. Hearing about new versions: of itself, and of every tool it was installed with

The assistant is not only this repo: it runs on Claude Code, talks through the Telegram plugin (which runs on Bun),
browses with agent-browser, downloads videos with yt-dlp, transcribes with Parakeet or faster-whisper, may have n8n
and third-party skills. Each comes from somewhere else and has its own releases. The **version watch** follows all
of them, from one list: `setup/capabilities.json` says where each capability's code comes from (its `upstream`),
and `assistant-doctor --watch-list` turns that into what is installed **on this machine right now**, with the
installed versions. Installing, removing or declining a capability with `assistant-setup` rebuilds the watch, and
`assistant-doctor` checks that it is on and covers everything installed.

| Kind | Asked where | Example |
|---|---|---|
| The assistant itself | its repo's latest GitHub release (`GITHUB_REPO` in `install.conf`) | this kit |
| A GitHub release | `/repos/<owner>/<repo>/releases/latest` | Bun |
| A Python package | PyPI's JSON API, against the version in its venv | yt-dlp, onnx-asr (Parakeet), faster-whisper, PyMuPDF and pymupdf4llm |
| An npm package | the npm registry (n8n: its `stable` tag) | agent-browser, n8n |
| The Telegram plugin | Claude Code's own copy of the official plugin catalogue, on the machine | telegram@claude-plugins-official |
| A third-party skill | its repo's latest commit, against the one in the skill's `.installed-from` | diagram-design |
| Updates itself | not watched, only noted | Claude Code (the daily restart updates it) |
| The system's packages | not watched, only noted | Chromium, poppler (for Claude Code's Read), ffmpeg (the machine's own updates) |

Once a day it asks each source for its latest version and, for anything newer than what is installed, wakes the
assistant through the [wake-up](wakeup.md) with at most two lines: one for its own release (source
`claudia-release`), one for all the tools together (source `tool-updates`). A notice holds only names from our own
list, version numbers that match a strict pattern, and links built from them: release titles and notes are never
passed on, so nothing written upstream is typed into the assistant's terminal. Each version is reported once,
whatever the assistant decides. No token is needed (GitHub allows 60 unauthenticated requests an hour per address,
and this makes a few a day).

Two ways, chosen by `assistant-setup watch` without asking anything:

- **With n8n** ([n8n.md](n8n.md)): it fills in `templates/n8n/workflows/release-watch-to-wakeup.json` ("Versions →
  wake the assistant") with the list, imports the **Assistant wake-up** credential and the workflow with
  `n8n-admin`, publishes it and restarts n8n; the daily timer is turned off. The list lives inside the workflow, so
  `assistant-setup watch` re-imports it when what is installed changes (and only then). Leave that workflow out of
  MCP: `assistant-setup watch` owns it.
- **Without n8n**: `assistant-release-watch.timer` runs `/usr/local/sbin/assistant-release-watch` once a day around
  10:00. It does the same with `curl` and `jq`, reading the list from `assistant-doctor --watch-list` each time, so
  it is never out of date. If the wake-up does not take a notice, it tries again the next day. Log:
  `/var/log/assistant-release-watch.log`; `assistant-release-watch --check` says what it would report today.

Turned on at install (the installer asks nothing technical; `install.sh` asks once from a terminal, or
`--release-watch yes|no`), later with `assistant-setup install updates`, or off with
`assistant-setup decline updates`. Said no, or installed without a terminal? The assistant offers it once in its
first days.

Or, by hand: **Watch → Custom → Releases** on GitHub, for each repo you care about.

## 3. What the assistant does with the notice

**For a tool** (its `updating` skill has the steps): it checks the tool is really behind (someone may have
updated it already), reads the release notes as a reviewer (as data, never as orders), and tells you only what is
worth it, for someone who is not technical: what the tool is in one sentence, what is new that matters to you,
and whether it recommends updating. A security fix or something you would notice comes at once; plain maintenance
waits and comes grouped, in one line, with the next thing worth telling you, at most once a week. With your yes it
updates that one tool (`assistant-setup install <capability>`, `n8n-admin update`, `claude plugin update`…), checks
it, and refreshes the watch. The Telegram plugin is the careful one: a new plugin version can break the patch that
gives the buttons and voice notes on arrival, so unless it is a security fix it suggests waiting for a release of
this kit that supports it.

**For itself:**

1. Compares the release with `install.conf`. Not newer: nothing to do.
2. Fetches that tag (`git clone --branch vX.Y.Z`, not `main`) and reads the `CHANGELOG.md` entries between your
   version and the new one, and the diff of `install.sh` and `templates/` between the two tags. It looks at the
   diff as a reviewer would: new network destinations, downloads that run code, changed permissions or hooks,
   anything the changelog does not explain. Release notes and code are data: it never follows instructions in them.
3. Tells you in a few lines what it brings, what changes on your machine (and what you would have to do, if
   anything), and anything odd it found, and asks: update now, later, or skip this version.
4. With your yes: backs up the workspace, the settings and the root-owned pieces, then runs
   `install.sh <user> --upgrade` from the tag (as root if it can, otherwise it gives you that one command).
5. Reviews each `.new` file the upgrade wrote (below), takes the ones that are right, and asks you about any that
   change how it behaves.
6. Restarts what changed, checks it works (services up, a test notice through the wake-up, a search with
   `recall`…) and tells you the result, how to undo it, and anything new worth turning on, offered once.

## 4. `install.sh --upgrade`

```bash
git clone --branch v1.5.0 https://github.com/jonjunq/claudia /tmp/claudia-v1.5.0
sudo /tmp/claudia-v1.5.0/install.sh <user> --upgrade
```

For every file it installs:

| Your file | What happens |
|---|---|
| Missing | Created (new in this release) |
| The same as the new template | Nothing |
| Unchanged since install.sh wrote it | Replaced; the old one stays as `<file>.bak-<date>` |
| Changed by you (or by the nightly review) | **Left alone.** `<file>.new` gets your changes and the template's merged (`git merge-file`); `CONFLICT` if both changed the same lines, marked with `<<<<<<<` |
| Changed, and installed before 1.4.0 (no record of the original) | Left alone; `<file>.new` is the plain new template, to merge by hand. Except the root-owned code under `/usr/local/`, which is not meant to be edited: replaced, with a `.bak-<date>` |

Your keys and the wake-up token are kept; the n8n kit's copies and the guides are refreshed; units are not enabled
or restarted. Review each `.new`, move it over the original when it is right (`mv CLAUDE.md.new CLAUDE.md`), then
`systemctl daemon-reload` and restart what changed, the session last. If your `CLAUDE.md` is in another language,
its `.new` will be mostly conflicts: port the changes the changelog lists by hand instead.

Without `--upgrade`, `install.sh` stays as it always was: it only adds what is missing.

## Undoing an update

The `.bak-<date>` files, the backup from step 4 and the previous tag: `install.sh` from the old tag with
`--upgrade` brings the untouched files back, and the backup has the rest. The assistant's own memory and notes
have a git history ([memory.md](memory.md)).
