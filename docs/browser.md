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

## Which browser underneath: a full Chromium with a window

agent-browser drives any Chromium. What runs underneath matters more than the tool on top:

- **The headless shell** (`chrome-headless-shell`, what Playwright installs as `chromium_headless_shell`, and the
  easiest to get running in a container) is the old headless mode. Its user agent says `HeadlessChrome`, and it is
  exactly what bot protection looks for: AWS WAF's managed bot rules, in front of many CloudFront sites, have a rule
  for "automated browser" signals out of the box. A second-hand marketplace answered it with CloudFront's
  `403 ERROR / The request could not be satisfied` in 0.1 s; a big provider's sign-in page refused it.
- **A full Chromium in headed mode** (a real window, on a virtual screen, Xvfb) behaves like a normal browser.
  agent-browser starts the Xvfb itself (`--headed`, or `"headed": true` in its config).

Measured on the same container, headless shell → Debian's `chromium` headed:

| | Headless shell | Full Chromium, headed |
|---|---|---|
| User agent | `HeadlessChrome/156` | `Chrome/156.0.0.0` |
| Marketplace behind CloudFront | 403 in 0.1 s | opens in 1.9-3.4 s |
| A big provider's sign-in page | refused | loads in 1.2-2 s (it may still say the browser is not secure; see below) |
| A news site | 0.7 s | 3.5 s |
| Browser start | 0.3 s | 1.7 s |
| Memory with a page open | a few hundred MB | about 1.2 GB RSS (we gave the container 6 GB) |

`navigator.webdriver` is still `true`: agent-browser sets it when it launches the browser, and hiding it would be
anti-detection, which we do not do (see the rule below).

### Install (Debian)

As root:

```bash
apt install chromium xvfb fonts-noto fonts-noto-color-emoji   # Debian's Chromium, with its sandbox
npm install -g agent-browser          # warns about Node < 24 (EBADENGINE): the CLI is a native binary and works anyway
```

As the assistant's user:

```bash
install -d -m 700 ~/.browser/clean ~/.browser/sessions
install -D -m 644 /usr/local/lib/assistant-browser/agent-browser-config.json ~/.agent-browser/config.json
```

The config (installed by `install.sh` with your user's home filled in) points agent-browser at `/usr/bin/chromium`,
headed, with the clean profile and a 1280×720 window. In an unprivileged container Debian's Chromium ran **with its
sandbox** (user namespaces were available); do not add `--no-sandbox` unless it refuses to start without it.

Check it as that user: `agent-browser open https://example.com && agent-browser eval "navigator.userAgent" &&
agent-browser close` should print a user agent without `HeadlessChrome`.

**If Xvfb or Chromium crash in a container without a GPU** (a `double free`, a crash reporter that cannot start):
look for NVIDIA's userspace files left over from a driver install, which point EGL and Vulkan at a GPU that is not
there. On ours they were the EGL vendor file `/usr/share/glvnd/egl_vendor.d/10_nvidia.json`, the
`*nvidia*.json` files in `/usr/share/egl/egl_external_platform.d/`, and the Vulkan ICD
`/usr/share/vulkan/icd.d/nvidia_icd.json` (with `libnvidia-egl-gbm` behind them). Moving them to a backup folder
fixed both Xvfb and the Chrome for Testing that had crashed before; put them back if the GPU returns.

**Two profiles.** The clean profile (the default) is for any site. A second one, `~/.browser/sessions`, is where you
(or the assistant, with its own accounts) are signed in, used only for those sites. Separating them limits what a
malicious page can reach: the clean one has no sessions to steal. agent-browser's `--allowed-domains` cannot be
combined with `--profile`, so the skill carries the list of sites for the sessions profile and the assistant keeps
to it.

**The rule we set**: a standard browser, headed, with a persistent profile, yes. Changing the user agent,
anti-detection flags or "stealth" builds (Camoufox, Patchright, undetected drivers…), cloud browsers sold on
stealth, or captcha-solving services, no: that is evading a site's bot protection, the auto-mode classifier blocks
it anyway, and it breaks most sites' terms. For the steps a standard browser cannot pass, a human does them, which
is what the remote window is for. Big providers state that they may block sign-ins from any browser "controlled
through software automation", so sign in once by hand in the sessions profile, and use official connectors or
APIs for the rest.

Then give the assistant the skill in [`templates/workspace/.claude/skills/browser/SKILL.md`](../templates/workspace/.claude/skills/browser/SKILL.md)
(`install.sh` already puts it in `~/assistant/.claude/skills/`). It tells it to stop writing its own drivers, which
profile to use, how to handle custom dropdowns, logins approved on a phone and captchas, and to ask you before the
final submit. The assistant may add the tricks it learns for a site to that skill; that is intended.

**Simpler, if a site works without it**: the headless shell that Playwright installs (`npx playwright install
chromium`) also runs in a minimal container, with `"args": "--no-sandbox,--disable-dev-shm-usage"`. Fine for sites
without bot protection; expect the blocks above.

## A remote window for captchas and logins

Some steps need you: a captcha, a sign-in that asks "is it you?", a two-factor prompt. If you do them on your phone,
the session stays on your phone and the assistant hits the same wall again. With a remote window you see **the
assistant's own browser** in a web page and do that step there; what you solve or sign in to stays in its profile.

The pieces (templates installed by `install.sh`, not enabled):

- `assistant-window-vnc.service`: [x11vnc](https://github.com/LibVNC/x11vnc) on `localhost:5900`, started with
  `-display WAIT:cmd=…/current-display`: it opens no display until someone connects, then
  [`current-display`](../templates/browser/current-display) finds the virtual screen of the most recently opened
  browser (agent-browser starts one Xvfb per session, so the number changes). When you disconnect it exits and
  systemd starts it waiting again; about 20 MB idle.
- `assistant-window-web.service`: [noVNC](https://novnc.com) served by websockify on `127.0.0.1:6080`, as a
  systemd `DynamicUser` with a read-only system.

```bash
apt install x11vnc novnc websockify
install -d /etc/assistant-window && x11vnc -storepasswd /etc/assistant-window/vncpasswd
chown root:<user> /etc/assistant-window/vncpasswd && chmod 640 /etc/assistant-window/vncpasswd
systemctl enable --now assistant-window-vnc assistant-window-web
```

**Protect it.** Whoever opens that page drives a browser signed in to your accounts. Never publish port 6080 as it
is. Options, from simplest:

- **Only from your own devices**, over a VPN such as Tailscale or WireGuard: keep it on localhost and reach it with
  `tailscale serve`, or bind websockify to the VPN address. Nothing is exposed to the internet.
- **Behind a reverse proxy with a login and a second factor**: any proxy you already run (Caddy, nginx, Traefik)
  with an identity layer in front (Authelia, Authentik, oauth2-proxy, Cloudflare Access…), and a strong second
  factor for this one site (a passkey or a security key, which also resists phishing). Send no-framing headers
  (`X-Frame-Options: DENY`), `Cache-Control: no-store`, and redirect `/` to `vnc.html?autoconnect=1&resize=scale`.
- In both cases a **firewall** rule so that only the proxy (or the VPN) can reach 6080, and websockify bound to
  the narrowest address that works.

The VNC password is a second lock behind the proxy. noVNC takes it from the URL fragment
(`…/vnc.html?autoconnect=1#password=…`), which the browser never sends to the server. Put the full link in
`~/.config/assistant/window-link` (mode 600) so the assistant can send it to you; the link then also sits in your
Telegram chat and in the assistant's transcripts, so treat the proxy's login as the real gate. If that login
already has a strong second factor, you may drop the VNC password (`-nopw` instead of `-rfbauth …`), as we did
once ours used a passkey.

The skill tells the assistant when to send the link and to close other browser sessions first, so the window shows
the right one.

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
