# Updating: hearing about releases, and applying them safely

The assistant can keep itself up to date: it hears about a new release of this repo, tells you in plain words what
it brings, and with your yes backs up, applies it without overwriting what you changed, checks that everything
still works and tells you how it went. You do not need to follow this repo yourself.

Two rules it never breaks, and why:

- **Only tagged releases, never `main`.** A release is a version someone decided was ready, with notes; `main` is
  work in progress.
- **Never without your yes, and never without reading the changes first.** If this repo were ever compromised (a
  stolen token, a malicious pull request merged by mistake), every installation that updated itself automatically
  would run the bad code within a day, with the reach the assistant has on your machine. A human yes after the
  assistant has read the diff (and told you about anything odd) is the brake. The same goes for any fork you
  install from.

## 1. Knowing what is installed

`install.sh` writes `/usr/local/share/assistant/install.conf` on every run: the version (`git describe`, e.g.
`v1.5.0`, or `v1.4.0-3-gabc1234` for three commits after 1.4.0; from a download without git, the newest release in
`CHANGELOG.md`), the repo it came from, and the settings you installed with (`--name`, `--owner`, `--language`,
`--timezone`), which later runs reuse. It also keeps a copy of every file exactly as it wrote it, in
`/usr/local/share/assistant/installed/`: that is how an upgrade tells apart the files you changed from the ones you
did not. The guides and the changelog are copied to `/usr/local/share/assistant/docs/` so the assistant can read
them.

## 2. Hearing about a release

**With n8n** (recommended if you have it, [n8n.md](n8n.md)): `templates/n8n/workflows/release-watch-to-wakeup.json`.
Once a day at 10:00 it asks GitHub's API for the latest release (`/repos/<owner>/<repo>/releases/latest`, which
skips drafts and pre-releases); if it is newer than the installed version, it wakes the assistant through the
[wake-up](wakeup.md) with one line: the version and the link to its notes. Nothing else: the release title and notes
are not passed on, so nothing written in the repo is typed into the assistant's terminal. It reports each release
once, whatever you decide, and costs no tokens on the days without one (almost all of them).

- No token needed: GitHub allows 60 unauthenticated requests an hour per address, and this makes one a day. If you
  share an address with heavy API users, add a header credential `Authorization: Bearer <fine-grained token with no
  permissions>` to the **Latest release** node.
- Placeholders: `__VERSION__` and `__GITHUB_REPO__` (from `install.conf`), `__WAKEUP_URL__`, `__TIMEZONE__`, and
  the **Assistant wake-up** credential the email template uses too.
- The assistant can set it up itself, like the other templates: through n8n's MCP server, or with
  `n8n-admin import` if it runs as root. Like the email workflow, it wakes the assistant, so leave it out of MCP
  once it is published.
- It never needs editing after an upgrade: it remembers the last release it reported.

**Without n8n**, either of these:

- On GitHub, **Watch → Custom → Releases** on the repo: GitHub emails you each release, and if the assistant
  watches your inbox it sees it too.
- A weekly routine in `notes/routines.md` ("Mondays 10:00: check the latest release with
  `curl -s https://api.github.com/repos/<owner>/<repo>/releases/latest` and compare it with install.conf"). It costs
  one turn a week.

## 3. What the assistant does with the notice

Its `updating` skill has the steps; in short:

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
| Changed, and installed before 1.4.0 (no record of the original) | Left alone; `<file>.new` is the plain new template, to merge by hand |

Your keys and the wake-up token are kept; the n8n kit's copies and the guides are refreshed; units are not enabled
or restarted. Review each `.new`, move it over the original when it is right (`mv CLAUDE.md.new CLAUDE.md`), then
`systemctl daemon-reload` and restart what changed, the session last. If your `CLAUDE.md` is in another language,
its `.new` will be mostly conflicts: port the changes the changelog lists by hand instead.

Without `--upgrade`, `install.sh` stays as it always was: it only adds what is missing.

## Undoing an update

The `.bak-<date>` files, the backup from step 4 and the previous tag: `install.sh` from the old tag with
`--upgrade` brings the untouched files back, and the backup has the rest. The assistant's own memory and notes
have a git history ([memory.md](memory.md)).
