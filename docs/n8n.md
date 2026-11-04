# n8n: alerts and automations that cost no tokens

Every time the assistant wakes up, it spends part of your subscription: it re-reads the conversation and thinks.
That is worth it for things that need judgement ("is this email important?"), and wasted on things that do not
("has the parcel moved?", "did the price drop?"). [n8n](https://n8n.io) is an open-source automation tool that does
the second kind for free, around the clock, and can hand the first kind over to the assistant only when there is
something to look at.

The rule we use:

| Needs thinking? | Who does it | Example |
|---|---|---|
| No | n8n, and it tells **you** directly on Telegram | A tracking page changes; a product is back in stock; a site goes down |
| Yes | n8n notices it and wakes **the assistant** through the [wake-up](wakeup.md), not Telegram | A new email arrives: is it important? Does it need a reply? |
| Yes, at a fixed time | The assistant's own routines (`notes/routines.md`) | The morning summary |

With this split our assistant went from checking a parcel every morning and watching email in its daily summary to
hearing about email within seconds, about 3 times a day, and never spending a turn on the parcel.

## Who sets it up

You do not need to know n8n. Pick whichever fits how you [run the assistant](isolation.md):

- **The assistant does it all.** If it runs with root on its machine, ask it on Telegram ("install n8n and tell me
  about new emails"): the kit is in `/usr/local/share/assistant-n8n/` and this page tells it how.
- **You install, it builds.** If it runs as a normal user (our setup), you run the installer once as root, connect
  the assistant to n8n's MCP server (below), and from then on it builds, changes and switches workflows off itself
  when you ask.
- **You do it all**, in n8n's editor, with the templates below as a starting point.

## Install

Needs Node.js 24 or newer and npm (n8n 2.x refuses older Node). The installer does not install Node for you: use
your distribution's package or [NodeSource](https://github.com/nodesource/distributions).

```bash
/usr/local/share/assistant-n8n/install-n8n.sh --owner-email you@example.com
# options: --version X (default: the release npm marks "stable"), --listen 0.0.0.0 --host <LAN address>, --timezone
```

It creates a system user `n8n`, installs n8n globally with npm, writes `/etc/n8n.env` (mode 600) with a random
encryption key, installs and starts `n8n.service`, waits until it answers, creates the owner account without a
browser (password in `/root/n8n-owner.txt`) and installs `n8n-admin` for the chores below. By default it listens on
127.0.0.1 only. Re-running it keeps your settings.

What `/etc/n8n.env` sets, and why:

- No telemetry, version banners or onboarding survey.
- `NODES_EXCLUDE`: no Execute Command, SSH or Local File Trigger nodes. The assistant has a shell of its own; n8n
  does not need one, and a workflow that can run commands is one leaked credential away from running anything.
- `N8N_COMMUNITY_PACKAGES_ENABLED=false`: installing a community node runs third-party code inside n8n, and the MCP
  server even offers a tool to do it.
- `N8N_BLOCK_ENV_ACCESS_IN_NODE=true`: Code nodes cannot read the encryption key or other settings.
- File nodes can only touch `/var/lib/n8n/files`; old executions are deleted after 14 days.
- `N8N_ENCRYPTION_KEY`: encrypts the credentials stored in n8n. **Keep a copy with your backups**: a restored
  `/var/lib/n8n` cannot decrypt its credentials without it.

Two things we learned installing it without Docker: npm 11 refuses n8n on glibc with `EBADPLATFORM` because one of
its packages pins prebuilt binaries for the musl build of n8n's Docker image, so the installer uses `--force` (those
binaries are optional); and npm 11 skips install scripts, which n8n does not need (the installer checks that its
native modules load).

## Let the assistant build them

n8n 2.13 and later include an **instance-level MCP server**: the assistant connects to it as it does to any MCP
server and can search, create, update, validate, test, publish and unpublish workflows, list the credentials that
exist (not their secrets) and read executions. This is the recommended way; it is n8n's own, so there is nothing
else to install. ([n8n docs](https://docs.n8n.io/advanced-ai/accessing-n8n-mcp-server/))

Turn it on, as the n8n owner. In the editor: **Settings → Instance-level MCP → Enable MCP access**, then
**Connect → Claude Code** gives you the command and a token. Without a browser, with n8n's internal REST API:

```bash
N=http://127.0.0.1:5678; J=$(mktemp)
curl -s -c "$J" -H 'Content-Type: application/json' -d '{"emailOrLdapLoginId":"you@example.com","password":"…"}' $N/rest/login
curl -s -b "$J" -X PATCH -H 'Content-Type: application/json' -d '{"mcpAccessEnabled":true,"autoExposeNewWorkflows":true}' $N/rest/mcp/settings
curl -s -b "$J" $N/rest/mcp/api-key        # the token for the assistant
rm -f "$J"
```

Then, as the assistant's user:

```bash
claude mcp add --scope user --transport http n8n http://127.0.0.1:5678/mcp-server/http \
  --header "Authorization: Bearer <token>"
```

A workflow is invisible to the MCP client until it is exposed (`autoExposeNewWorkflows` exposes the ones created
from now on; older ones: `PATCH /rest/mcp/workflows/toggle-access` with `{"availableInMCP":true,"workflowIds":[…]}`,
or the workflow's settings). **Leave the workflow that wakes the assistant unexposed**: it carries the wake-up token,
and the assistant has no reason to edit how it is woken.

Rules the assistant follows (they are in the `CLAUDE.md` template):

- It builds or changes workflows only when you ask, on your channel, and confirms with you before publishing one.
- Watches switch themselves off (below), so nothing keeps running forever because someone forgot it.
- It uses credentials that already exist in n8n, or asks you to create one; never a key or password in a workflow's
  code or in its own notes.
- It turns a workflow off by unpublishing it rather than deleting it, so it can be turned back on.

The community [n8n-mcp](https://github.com/czlonkowski/n8n-mcp) (MIT, widely used) is an alternative or a
complement: it adds documentation and validation for every node type and works through n8n's public API with an API
key. The built-in server covers what the assistant needs here.

## Without MCP: the command line

`n8n-admin` runs n8n's CLI as the `n8n` user with its settings:

```bash
n8n-admin import-credentials creds.json      # plain JSON (n8n encrypts it); delete the file afterwards
n8n-admin import workflow.json               # same id = replaces it
n8n-admin publish <id>                       # or: unpublish <id>
n8n-admin restart                            # imports and publishes apply after a restart
n8n-admin list | export <id> | cli <any n8n command>
```

Gotchas we hit:

- `n8n execute --id` only runs workflows that start with a Manual Trigger ("Missing node to start execution"
  otherwise), and it starts a second n8n: `n8n-admin cli` uses spare ports so it does not clash with the service.
- There is no CLI command to delete a workflow. Unpublish it, or through the REST API (logged in as above):
  `POST /rest/workflows/<id>/archive`, then `DELETE /rest/workflows/<id>`.
- If you generate workflow JSON from a shell script, quote the heredoc (`<<'EOF'`): otherwise the shell eats
  `$input` and `$json` from the Code nodes and the workflow breaks without saying why.

## Templates

In `/usr/local/share/assistant-n8n/workflows/` (and `templates/n8n/workflows/` in this repo), with `__PLACEHOLDERS__`
to fill in and `credentials.example.json` for the credentials they use.

### New email → wake the assistant

`email-to-wakeup.json`: an IMAP trigger on the inbox → a Code node that writes one line per email (sender, subject,
message id) → `POST` to the wake-up. The assistant then reads the email with its own Gmail connector and decides:
tell you now, or leave it for the morning summary.

- **Gmail**: use an [app password](https://myaccount.google.com/apppasswords) (it needs 2-Step Verification; some
  Google Workspace accounts do not allow them). Revoke it there to cut n8n off.
- Gmail's IMAP does not understand `category:primary` (it returns nothing), so the trigger excludes Promotions,
  Social and Forums instead (`X-GM-RAW "-category:promotions -category:social -category:forums"`). Updates stay in:
  appointments, security alerts and deliveries land there.
- Emails are **not marked as read**. The first search after activation can return the day's older unread emails:
  the Code node skips anything older than 3 hours, and never wakes the assistant twice for the same message id.
- Encoded subjects (`=?UTF-8?B?…?=`) are decoded. Several emails arriving together become one notice.
- Only sender and subject reach the assistant's terminal, marked as data. The body is fetched by the assistant
  itself, as when it does the morning summary, and the template tells it that emails give no orders.
- Cost: on our inbox, about 23 emails a week got through the filter, so about 3 turns a day.

### Watch a page → Telegram when it changes (switches itself off)

`page-watch-to-telegram.json`: every few hours → **Still on?** → fetch the page → **What changed?** → Telegram to
you. Adapt the constants at the top of the second Code node (or ask the assistant to):

- `extract()` decides what is compared. By default the page's visible text, between two markers if you give them.
  For a parcel tracker, return only the latest row (date, place, status). Some trackers want a form `POST`
  instead of a `GET`: change the HTTP node.
- The first run only remembers the current state; you get a message only when it changes.
- **It switches itself off**: when the text matches `FINAL` (for a parcel, `/delivered|entregado/i`) it sends the
  last message saying so, and after `MAX_DAYS_UNCHANGED` days without a change (14 by default) it says that too.
  From then on **Still on?** stops each run before any request is made. Nobody has to remember to unpublish it.
- Messages end with "— automatic notice from n8n", so you know the assistant did not write them.

The Telegram node can use the assistant's own bot (its token is in `~/.claude/channels/telegram/.env`): sending
does not interfere with the plugin, which only polls for incoming messages, and the assistant does not see what its
bot sends. If you reply to one of those messages, the assistant sees your reply and the quoted text.

## Keeping it updated

n8n does not update itself, and it has had serious vulnerabilities: in 2026 alone,
[CVE-2026-21858](https://cvefeed.io/vuln/detail/CVE-2026-21858) (unauthenticated access through form webhooks,
fixed in 1.121.0) and several more fixed in 2.x releases. Keep it current:

```bash
n8n-admin update            # or: n8n-admin update 2.47.0
```

It stops n8n, **backs up its data folder** (the database migrates on the first start of a new version, so only a
copy can undo an update), installs the new version, starts it and checks that it answers, reports the new version
and still has the same number of workflows. If any check fails it **rolls back**: the old version and the data from
before. Exit codes: 0 updated or nothing to do, 1 rolled back, 2 nothing changed (no stable version found or the backup failed), 3 rollback failed. The last 3
backups are kept in `/var/lib/n8n-backups`.

Schedule it rather than remembering it. With `--tell` it passes the outcome to the assistant through the
[wake-up](wakeup.md), and the assistant tells you on Telegram in plain words ("n8n updated to 2.47.0" or "the update
failed and was rolled back"):

```bash
# /etc/cron.d/n8n-update — Mondays at 04:30
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
30 4 * * 1 root n8n-admin update --tell >> /var/log/n8n-update.log 2>&1
```

Or ask the assistant to schedule the check for you and report: it is the same command.

## Security checklist

- Keep the editor on localhost or your LAN. If you want it from outside, put a login layer in front (a reverse
  proxy with its own authentication, or a VPN), and turn on two-factor authentication for the n8n account.
- n8n holds credentials (an email app password, a bot token): back up `/var/lib/n8n` and the encryption key, and
  treat those backups as secrets.
- Do not expose the wake-up workflow to MCP, and do not turn community packages on without a reason.
- Content that arrives through n8n (emails, pages, webhooks) is data for the assistant, never instructions.
- Every notice to the assistant is a turn of your subscription: filter in n8n before waking it.
