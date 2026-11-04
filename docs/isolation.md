# Run it your way

This is open source: put the assistant wherever suits you. Nothing in the repo requires a container, a hypervisor
or a second machine. What we describe is **one** way, the one we use, with the reasons behind it, so you can decide
how much of it you want.

The trade-off is always the same. The assistant holds the keys to your email, calendar and files, reads untrusted
text all day (emails, web pages, documents) and runs commands. The more it can reach, the more useful it is, and the
more a bad day (a manipulative email it took seriously, a mistake, a bug) can touch.

| Where | Comfort | What a bad day can touch | Notes |
|---|---|---|---|
| Its own VM or container, network fenced (what we do) | Medium: you give it access service by service | That box and what you opened for it | The rest of this page |
| A normal user on an always-on machine you already have | High | That user's files, and whatever the machine can reach | Fine on a home server; think twice on the laptop you work on |
| **Root on a machine of its own** ("the machine is its home") | Highest: it can install and manage anything itself (n8n, a database, updates) and you never have to step in | The whole machine, and anything reachable from it | Give it a machine with nothing else on it, keep backups outside it |
| A small cloud VM | Medium | That VM | Nothing at home is reachable from it, which is the point; it also means it cannot reach your home devices |

Whatever you pick, the same few habits cover most of the risk: a Telegram allowlist (only you can talk to it),
`ask` rules for sending and deleting, the hard block on payments in `settings.json`, credentials scoped to one job,
and backups. The scripts assume a Linux machine with systemd and a user with a home folder. Running it as root
means `install.sh root` (the workspace goes to `/root/assistant`); we run ours as a normal user, so tell us in an
issue if something there trips.

We use an unprivileged LXC container with 4 cores and 4 GB (more than needed; 2 cores and 2 GB are fine without
local voice models), fenced as below, and the admin (not the assistant) installs system services.

## Fence it (if you isolate it)

- **Network**: allow outbound internet (it needs Anthropic, Telegram, Google and whatever APIs you give it) and DNS,
  and **block your local network** (RFC 1918 ranges, link-local, your VPN's ranges). If you want it to reach one
  local service, open exactly that host and port. On a hypervisor this is a few firewall lines per guest; on a
  plain VM, nftables or your router.
- **DNS gotcha**: some routers hand out DNS servers in ranges your firewall now blocks (e.g. CGNAT addresses), and
  the container loses name resolution. Pin a reachable resolver (with dhclient:
  `supersede domain-name-servers <router-or-public-dns>;` in `/etc/dhcp/dhclient.conf`).
- **No inbound**: nothing needs to reach it. The Telegram plugin polls Telegram; there is no webhook to expose. Turn
  off SSH if you do not use it, or restrict it to your admin machine.
- **One user, no sudo**: in a fenced setup the assistant's user does not need root. The daily restart, the Telegram
  hooks and the memory tools are root-owned and run as root precisely so the assistant cannot alter them. If you run
  it as root, that protection is gone by design: rely on the allowlist, `ask` rules and backups instead.
- **Secrets**: the bot token (`~/.claude/channels/telegram/.env`) and voice keys (`~/.config/assistant/keys.env`) are
  readable by the assistant by necessity. Keep them in files with mode 600, never in `CLAUDE.md` or notes, and never
  paste them into a chat with it. Give it read-only or narrowly scoped credentials for anything else (a token that can
  only power one VM on and off, a read-only monitoring account).
- **Updates**: unattended security updates for the OS; Claude Code updates nightly via the daily restart.
- **Backups**: back up the workspace and `~/.claude` (memory, settings, transcripts). They contain personal data:
  treat the backups accordingly.

## Giving it access to your other systems

Tempting, and useful (turn the game server on, check why something is down, wake your PC). Do it one service at a
time, with its own limited credential, an explicit firewall hole, and an information-only skill that says what it
may do. Keep alerts that must work when things are broken (monitoring, backups) on a separate path that does not
depend on the assistant.
