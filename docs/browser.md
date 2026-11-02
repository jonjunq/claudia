# Browser

Sooner or later the assistant has to use a website that has no API: a government e-service portal, a form, a
download behind a login. Claude Code can drive a browser, but how it does so makes a large difference in time,
failures and plan usage.

## What goes wrong without a browser tool

With nothing installed, the assistant improvises: it writes a small Playwright script on the spot, guesses CSS
selectors, and after each click dumps the page text and a screenshot to see what happened. On a modern form built
from custom components this breaks down. A selector misses, Playwright waits 30 seconds for the click and fails, the
assistant looks at a screenshot and guesses again. Each step costs a tool call plus a large page dump.

## The options

| Tool | What it is | Fit for this assistant |
|---|---|---|
| [agent-browser](https://github.com/vercel-labs/agent-browser) (Vercel) | CLI; accessibility-tree snapshots with short refs (`@e12`), semantic `find label/role/text`, `batch`, saved login state | **Chosen** |
| [Playwright MCP](https://www.npmjs.com/package/@playwright/mcp) (Microsoft) | MCP server with the same ref idea | Works, but returns a page snapshot after every action (more context) and, being an MCP server, needs a session restart to load |
| [Chrome DevTools MCP](https://www.npmjs.com/package/chrome-devtools-mcp) (Google) | MCP server for DevTools | Built for debugging pages more than for filling them in |

browser-use and Stagehand drive the browser with their own model calls and API key, which this setup does not need.

Why agent-browser:

- **Less context.** The assistant asks for a snapshot only when it needs one (`snapshot -i` lists only the interactive
  elements, `--delta` only what changed), and `screenshot --if-changed` skips identical images. The assistant runs
  all day on a subscription, so context is what you pay for.
- **No restart.** It is a command, not an MCP server: install it and a running session can use it right away. A
  skill dropped into `.claude/skills/` is picked up live as well.
- **Fewer round trips.** `batch` runs several known steps in one call.
- **Refs instead of guessed selectors**, which is what fixes the failing clicks.

## Install

On the assistant's machine (Debian here), as root, then as the assistant's user:

```bash
npm install -g agent-browser          # warns about Node < 24 (EBADENGINE): the CLI is a native binary and works anyway
sudo -u <user> agent-browser install  # downloads Chrome for Testing to ~/.agent-browser/browsers
apt install libnss3 libnspr4          # libraries that Chrome needs and a minimal system may lack
```

In an **unprivileged LXC container** the downloaded Chrome crashed at start (its crash reporter, crashpad, could not
start) even with `--no-sandbox`. The Chromium headless shell that Playwright installs (`python -m playwright install
chromium` or `npx playwright install chromium`) runs fine there, and agent-browser takes any Chromium. Point it there
in `~/.agent-browser/config.json` of the assistant's user:

```json
{
  "executablePath": "/home/<user>/.cache/ms-playwright/chromium_headless_shell-<version>/chrome-headless-shell-linux64/chrome-headless-shell",
  "args": "--no-sandbox,--disable-dev-shm-usage",
  "idleTimeout": "60m"
}
```

Check it as that user: `agent-browser open https://example.com && agent-browser snapshot -i && agent-browser close`
should list a `link "Learn more"`. If you used the Playwright headless shell, delete the Chrome you downloaded
(`~/.agent-browser/browsers`).

Then give the assistant the skill in [`templates/workspace/.claude/skills/browser/SKILL.md`](../templates/workspace/.claude/skills/browser/SKILL.md)
(`install.sh` already puts it in `~/assistant/.claude/skills/`). It tells it to stop writing its own drivers, how to
handle custom dropdowns, logins approved on a phone, and to ask you before the final submit. The assistant may add
the tricks it learns for a site to that skill; that is intended.

## Permissions

Each `agent-browser` command goes through the auto-mode classifier like any Bash call. That costs a little time per
step, and it is also what judges navigation and submissions. You can allow `Bash(agent-browser:*)` in
`settings.json` for speed, but then nothing checks what it does on websites, which is where it reads untrusted text.
We left it to the classifier.

## Measured

The same submission to a government e-registry (login approved on the phone, a four-step form with custom
dropdowns, five attachments, a final review), first with an improvised Playwright driver, then switching to
agent-browser in the middle of the task:

| | Improvised driver | agent-browser |
|---|---|---|
| Elapsed | 17.7 min: login, step 1 and half of step 2 | 14.8 min: login again, all four steps, submitted |
| Step 1 (address with custom dropdowns) | 11.1 min | 4.2 min |
| Browser calls that failed | 13 of 40 | 0 of 58 |
| Text returned per browser call | about 69,000 characters | about 9,100 characters |
| Model tokens per minute | about the same | about the same |

The tokens per minute stayed level because it made more, smaller calls, but it got about three times as much done
with them: roughly half the usage per step. To be fair, the second run already knew which options to pick in the
first two steps; the zero failures and the seven times smaller tool output are the tool's.
