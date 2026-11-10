#!/bin/bash
# Installs n8n without Docker, hardened, as a systemd service, for the assistant's automations (docs/n8n.md).
# Run as root, once. Re-running it keeps your settings and only adds what is missing.
#   install-n8n.sh [--version 2.46.5] [--listen 127.0.0.1] [--host 127.0.0.1] [--timezone Europe/Madrid]
#                  [--owner-email you@example.com]
# Needs Node.js 24 or newer and npm. It does not install Node itself: assistant-setup install email-watch does (from
# NodeSource's apt repository, when the machine's is missing or older), or use your distribution's package.
# DESTDIR=/some/dir writes the files under that prefix (used by the tests).
set -euo pipefail
HERE=$(dirname "$(readlink -f "$0")")
D="${DESTDIR:-}"
VERSION=""; LISTEN=127.0.0.1; HOST=""; OWNER_EMAIL=""
TIMEZONE=$(cat /etc/timezone 2>/dev/null || echo UTC)
while [ $# -gt 0 ]; do
  case "$1" in
    --version) VERSION=$2; shift 2 ;;
    --listen) LISTEN=$2; shift 2 ;;
    --host) HOST=$2; shift 2 ;;
    --timezone) TIMEZONE=$2; shift 2 ;;
    --owner-email) OWNER_EMAIL=$2; shift 2 ;;
    -h|--help) sed -n '2,8p' "$0"; exit 0 ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done
[ -n "$HOST" ] || { [ "$LISTEN" = 0.0.0.0 ] && HOST=$(hostname -I 2>/dev/null | awk '{print $1}'); }
HOST=${HOST:-$LISTEN}
if [ -z "$D" ] && [ "$(id -u)" -ne 0 ]; then echo "Run as root" >&2; exit 1; fi

node_major=$(node -v 2>/dev/null | sed -n 's/^v\([0-9]*\).*/\1/p')
if [ -z "$node_major" ] || [ "$node_major" -lt 24 ]; then
  echo "n8n 2.x needs Node.js 24 or newer (found: $(node -v 2>/dev/null || echo none)). Install it first." >&2
  exit 1
fi
command -v npm >/dev/null || { echo "npm not found" >&2; exit 1; }

# n8n carries an old agent-browser of its own (@n8n/mcp-browser), and installing n8n repoints the assistant's
# /usr/local/bin/agent-browser to it (vercel-labs/agent-browser#2214): that one cannot open the browser with a window.
# This gives the link back to the copy assistant-setup installed (the same as its browser_link), or removes it.
keep_agent_browser() {  # [prefix]
  local l=${1:-}/usr/local/bin/agent-browser dir=/usr/local/lib/node_modules/agent-browser t
  case "$(readlink "$l" 2>/dev/null)" in */node_modules/n8n/*) ;; *) return 0 ;; esac
  case $(uname -m) in aarch64|arm64) t=$dir/bin/agent-browser-linux-arm64 ;; *) t=$dir/bin/agent-browser-linux-x64 ;; esac
  [ -x "${1:-}$t" ] || t=$dir/bin/agent-browser.js
  if [ -e "${1:-}$t" ]; then ln -sfn "$t" "$l"; else rm -f "$l"; fi
  echo "  gave /usr/local/bin/agent-browser back to the assistant's copy (n8n had taken it over)"
}

# The release n8n marks "stable" on npm, unless a version is given.
[ -n "$VERSION" ] || VERSION=$(npm view n8n@stable version 2>/dev/null)
[ -n "$VERSION" ] || { echo "Could not ask npm for the stable version; pass --version" >&2; exit 1; }
echo "n8n $VERSION, listening on $LISTEN (editor: http://$HOST:5678)"

id n8n >/dev/null 2>&1 || useradd --system --home-dir /var/lib/n8n --create-home --shell /usr/sbin/nologin n8n
mkdir -p "$D/var/lib/n8n/files"
[ -z "$D" ] && chown -R n8n:n8n /var/lib/n8n

# --force: n8n-nodes-base pins prebuilt binaries for the musl build of n8n's Docker image, and npm 11 refuses them
# on glibc with EBADPLATFORM. They are optional at run time. npm 11 also skips install scripts; n8n does not need
# them (sqlite3 and isolated-vm load their prebuilt binaries), and the check below proves it.
# Always under /usr/local, whichever npm this is (Debian's installs there, NodeSource's in /usr): one copy, first in
# PATH, that n8n-admin updates in place.
npm install -g --prefix /usr/local --force "n8n@$VERSION"
keep_agent_browser "$D"
if [ -z "$D" ]; then
  root=$(npm root -g --prefix /usr/local)
  node -e "for (const m of ['sqlite3','isolated-vm']) require(require.resolve(m, {paths: ['$root/n8n']}))" \
    || { echo "n8n installed but its native modules do not load: see docs/n8n.md#troubleshooting" >&2; exit 1; }
fi

if [ -e "$D/etc/n8n.env" ]; then
  echo "  kept     /etc/n8n.env"
else
  key=$(head -c 32 /dev/urandom | od -An -tx1 | tr -d ' \n')
  mkdir -p "$D/etc"
  sed -e "s|__HOST__|$HOST|g" -e "s|__LISTEN__|$LISTEN|g" -e "s|__TIMEZONE__|$TIMEZONE|g" \
      -e "s|__ENCRYPTION_KEY__|$key|g" "$HERE/n8n.env" > "$D/etc/n8n.env"
  chmod 600 "$D/etc/n8n.env"
  echo "  created  /etc/n8n.env (keep a copy of N8N_ENCRYPTION_KEY with your backups)"
fi
mkdir -p "$D/etc/systemd/system" "$D/usr/local/sbin"
install -m 644 "$HERE/n8n.service" "$D/etc/systemd/system/n8n.service"
install -m 755 "$HERE/n8n-admin" "$D/usr/local/sbin/n8n-admin"
systemctl daemon-reload
systemctl enable --now n8n

health="http://$([ "$LISTEN" = 0.0.0.0 ] && echo 127.0.0.1 || echo "$LISTEN"):5678"
for _ in $(seq 1 60); do curl -fs -o /dev/null --max-time 3 "$health/healthz" && break; sleep 2; done
curl -fs -o /dev/null --max-time 3 "$health/healthz" || { echo "n8n did not answer on $health: journalctl -u n8n" >&2; exit 1; }
echo "  n8n is up"

# Owner account without a browser: POST /rest/owner/setup only works while no owner exists.
if [ -n "$OWNER_EMAIL" ]; then
  pass="$(head -c 18 /dev/urandom | od -An -tx1 | tr -d ' \n')Aa1"
  # (the password goes on stdin: on the command line any user of the machine could read it)
  code=$(printf '{"email":"%s","firstName":"Owner","lastName":"Account","password":"%s"}' "$OWNER_EMAIL" "$pass" |
    curl -s -o /dev/null -w '%{http_code}' --max-time 15 -H 'Content-Type: application/json' -d @- "$health/rest/owner/setup")
  if [ "$code" = 200 ]; then
    mkdir -p "$D/root"
    printf 'n8n owner (http://%s:5678)\nuser: %s\npassword: %s\n' "$HOST" "$OWNER_EMAIL" "$pass" > "$D/root/n8n-owner.txt"
    chmod 600 "$D/root/n8n-owner.txt"
    echo "  owner account created: credentials in /root/n8n-owner.txt"
  else
    echo "  owner not created (HTTP $code): it probably exists already; open the editor to log in"
  fi
fi
cat <<EOF

Next (docs/n8n.md):
  - Editor: http://$HOST:5678   (from another machine only if you installed with --listen 0.0.0.0)
  - Workflows without a browser: n8n-admin import <file.json>, n8n-admin publish <id>, n8n-admin restart
  - Let the assistant build workflows itself: Settings > Instance-level MCP (docs/n8n.md#let-the-assistant-build-them)
  - Keep it updated: n8n-admin update   (backup, update, health check, rolls back on failure)
EOF
