# Isolation

The assistant holds the keys to your email, calendar and files, reads untrusted text, and runs commands. Give it a
machine of its own and assume that machine could one day be talked into doing something stupid.

## Where

Anything always-on that you can fence: a VM or LXC container on a home server, a mini PC, a small cloud VM. Not your
laptop, not the server that holds your backups. We use an unprivileged LXC container with 4 cores and 4 GB (more
than needed; 2 cores and 2 GB are fine without local voice models).

## Fence it

- **Network**: allow outbound internet (it needs Anthropic, Telegram, Google and whatever APIs you give it) and DNS,
  and **block your local network** (RFC 1918 ranges, link-local, your VPN's ranges). If you want it to reach one
  local service, open exactly that host and port. On a hypervisor this is a few firewall lines per guest; on a
  plain VM, nftables or your router.
- **DNS gotcha**: some routers hand out DNS servers in ranges your firewall now blocks (e.g. CGNAT addresses), and
  the container loses name resolution. Pin a reachable resolver (with dhclient:
  `supersede domain-name-servers <router-or-public-dns>;` in `/etc/dhcp/dhclient.conf`).
- **No inbound**: nothing needs to reach it. The Telegram plugin polls Telegram; there is no webhook to expose. Turn
  off SSH if you do not use it, or restrict it to your admin machine.
- **One user, no sudo**: the assistant's user does not need root. The daily restart runs as root from cron precisely so
  the assistant cannot alter it.
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
