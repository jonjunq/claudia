#!/bin/bash
# Installs the assistant's workspace, scripts and services for one user. Run as root.
#   sudo ./install.sh <user> [--name Claudia] [--owner Alex] [--language English] [--timezone Europe/Madrid] [--upgrade]
# It never overwrites your files: re-running it only adds what is missing. --upgrade also brings the files you have
# not changed up to date and writes <file>.new merges for the ones you changed (docs/updating.md). It does not
# start anything; it prints the remaining steps. DESTDIR=/some/dir installs under that prefix (used by the tests).
set -euo pipefail
REPO=$(dirname "$(readlink -f "$0")")
SRC=$REPO/templates
U="${1:-}"
if [ -z "$U" ]; then sed -n '2,6p' "$0"; exit 1; fi
shift
D="${DESTDIR:-}"
# What install.sh installed and with which settings: read by the assistant (its version) and by later runs.
SHARE=/usr/local/share/assistant
CONF=$SHARE/install.conf
BASE=$SHARE/installed   # every file as install.sh last wrote it: the common base for --upgrade merges
conf() {
  [ -r "$D$CONF" ] && [ "$(sed -n 's/^INSTALL_USER=//p' "$D$CONF")" = "$U" ] && sed -n "s/^$1=//p" "$D$CONF" | tail -1
  true
}
NAME=$(conf NAME); OWNER=$(conf OWNER); LANGUAGE=$(conf LANGUAGE); TIMEZONE=$(conf TIMEZONE)
NAME=${NAME:-Claudia}; OWNER=${OWNER:-$U}; LANGUAGE=${LANGUAGE:-English}
TIMEZONE=${TIMEZONE:-$(cat /etc/timezone 2>/dev/null || echo UTC)}
UPGRADE=0
while [ $# -gt 0 ]; do
  case "$1" in
    --name) NAME=$2; shift 2 ;;
    --owner) OWNER=$2; shift 2 ;;
    --language) LANGUAGE=$2; shift 2 ;;
    --timezone) TIMEZONE=$2; shift 2 ;;
    --upgrade) UPGRADE=1; shift ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done
if [ "$UPGRADE" = 1 ] && ! command -v git >/dev/null; then echo "--upgrade needs git (git merge-file)" >&2; exit 1; fi
if [ -z "$D" ]; then
  [ "$(id -u)" -eq 0 ] || { echo "Run as root (it installs systemd units and a cron file)" >&2; exit 1; }
  H=$(getent passwd "$U" | cut -d: -f6) || { echo "No such user: $U" >&2; exit 1; }
else
  H=/home/$U
fi

# Shared secret for the wake-up endpoint: the existing one if there is one (an upgrade must not change it).
TOKEN=$(sed -n 's/^WAKEUP_TOKEN=//p' "$D/etc/assistant-wakeup.env" 2>/dev/null || true)
[ -n "$TOKEN" ] || TOKEN=$(head -c 24 /dev/urandom | od -An -tx1 | tr -d ' \n')
TODAY=$(date +%F)
TMPD=$(mktemp -d)
trap 'rm -rf "$TMPD"' EXIT

# Copies a template, filling in the placeholders. A file that exists is kept, unless --upgrade:
#   unchanged since install.sh wrote it -> replaced by the new template (old copy in <file>.bak-<date>);
#   changed by you -> left alone, and <file>.new gets your changes merged with the template's (git merge-file).
put() {
  local from=$1 to=$2 mode=$3 new base
  new="$TMPD/new"; base="$D$BASE$to"
  sed -e "s|__USER__|$U|g" -e "s|__HOME__|$H|g" -e "s|__NAME__|$NAME|g" -e "s|__OWNER__|$OWNER|g" \
      -e "s|__LANGUAGE__|$LANGUAGE|g" -e "s|__TIMEZONE__|$TIMEZONE|g" -e "s|__TOKEN__|$TOKEN|g" "$from" > "$new"
  if [ ! -e "$D$to" ]; then
    install -D -m "$mode" "$new" "$D$to"; echo "  created  $to"
  elif [ "$UPGRADE" != 1 ]; then
    echo "  kept     $to"; return
  elif cmp -s "$new" "$D$to"; then
    :
  elif { [ -e "$base" ] && cmp -s "$base" "$D$to"; } || { [ ! -e "$base" ] && [[ $to == /usr/local/* ]]; }; then
    # (the root-owned code under /usr/local is not meant to be edited: from installs without a record, replace it)
    cp -p "$D$to" "$D$to.bak-$TODAY"; install -m "$mode" "$new" "$D$to"
    echo "  updated  $to (old copy: $to.bak-$TODAY)"
  elif [ -e "$base" ]; then
    install -m 600 /dev/null "$D$to.new"   # private until it gets the file's own mode
    if git merge-file -p "$D$to" "$base" "$new" > "$D$to.new" 2>/dev/null; then
      if ! cmp -s "$D$to.new" "$D$to"; then
        chmod "$mode" "$D$to.new"
        echo "  merge    $to.new (your changes + the template's, no conflicts: review it, then move it over)"; return
      fi
      rm -f "$D$to.new"   # your file already has everything the new template brings
    else
      chmod "$mode" "$D$to.new"
      echo "  CONFLICT $to.new (your changes + the template's: fix the <<<<<<< parts, then move it over)"; return
    fi
  else
    install -m "$mode" "$new" "$D$to.new"
    echo "  differs  $to.new (the new template; yours differs and there is no record of the original: merge by hand)"
    return
  fi
  install -D -m "$mode" "$new" "$base"
}

echo "Workspace ($H/assistant):"
( cd "$SRC/workspace" && find . -type f ) | sort | while read -r f; do
  f=${f#./}
  case "$f" in bin/*.sh) mode=755 ;; *) mode=644 ;; esac
  put "$SRC/workspace/$f" "$H/assistant/$f" "$mode"
done
put "$SRC/settings.json" "$H/.claude/settings.json" 644
if [ -e "$D$H/.claude/settings.json" ] && ! grep -q assistant/bin/statusline.sh "$D$H/.claude/settings.json"; then
  put "$SRC/settings.json" "$H/.claude/settings.assistant.json" 644
  echo "  ! $H/.claude/settings.json already existed: merge settings.assistant.json into it by hand"
fi
mkdir -p "$D$H/.config/assistant"
[ -e "$D$H/.config/assistant/keys.env" ] || {
  printf '# API keys for the optional voice scripts (docs/voice.md). Only the owner can read this file.\n#GROQ_API_KEY=\n#CF_AI_TOKEN=\n#CF_AI_ACCOUNT_ID=\n#ELEVENLABS_API_KEY=\n' \
    > "$D$H/.config/assistant/keys.env"
  chmod 600 "$D$H/.config/assistant/keys.env"
  echo "  created  $H/.config/assistant/keys.env"
}
[ -z "$D" ] && chown -R "$U": "$H/assistant" "$H/.claude" "$H/.config/assistant"

echo "System:"
put "$SRC/system/assistant.service" /etc/systemd/system/assistant.service 644
put "$SRC/system/assistant-permission-watch.service" /etc/systemd/system/assistant-permission-watch.service 644
put "$SRC/system/assistant-daily-restart" /usr/local/sbin/assistant-daily-restart 755
put "$SRC/system/assistant.cron" /etc/cron.d/assistant 644
# Telegram extras (status message, permission buttons, plugin patch): root-owned, so the assistant cannot edit
# the code that decides its own permissions.
for f in "$SRC"/telegram/*.py; do
  case "$f" in */tg.py|*/approvals.py) mode=644 ;; *) mode=755 ;; esac
  put "$f" "/usr/local/lib/assistant-telegram/$(basename "$f")" "$mode"
done
# Memory tools (recall, nightly review, git history): root-owned too, so the assistant cannot change what reviews it.
for f in "$SRC"/memory/*; do
  case "$f" in *.py|*.sh) mode=755 ;; *) mode=644 ;; esac
  put "$f" "/usr/local/lib/assistant-memory/$(basename "$f")" "$mode"
done
put "$SRC/system/recall" /usr/local/bin/recall 755
put "$SRC/system/assistant-history.service" /etc/systemd/system/assistant-history.service 644
put "$SRC/system/assistant-history.timer" /etc/systemd/system/assistant-history.timer 644
# Browser extras (optional, docs/browser.md): an agent-browser config to copy, and the remote window's units
# (x11vnc + noVNC), installed but not enabled.
put "$SRC/browser/current-display" /usr/local/lib/assistant-browser/current-display 755
put "$SRC/browser/agent-browser-config.json" /usr/local/lib/assistant-browser/agent-browser-config.json 644
put "$SRC/system/assistant-window-vnc.service" /etc/systemd/system/assistant-window-vnc.service 644
put "$SRC/system/assistant-window-web.service" /etc/systemd/system/assistant-window-web.service 644
# Wake-up (optional, docs/wakeup.md): types a notice into the session only when a watched log or n8n has something.
put "$SRC/wakeup/assistant-wakeup.py" /usr/local/lib/assistant-wakeup/assistant-wakeup.py 755
put "$SRC/wakeup/assistant-wakeup.env" /etc/assistant-wakeup.env 600
put "$SRC/wakeup/assistant-wakeup.watch" /etc/assistant-wakeup.watch 644
put "$SRC/system/assistant-wakeup.service" /etc/systemd/system/assistant-wakeup.service 644
# n8n kit (optional, docs/n8n.md): copied as-is, nothing is installed. Root-owned and readable, so the assistant can
# read the workflow templates and the admin (or the assistant, if it runs as root) can run install-n8n.sh.
# Nobody edits these copies (workflows are filled in elsewhere), so --upgrade simply refreshes them.
( cd "$SRC/n8n" && find . -type f ) | sort | while read -r f; do
  f=${f#./}; to="$D/usr/local/share/assistant-n8n/$f"
  if [ -e "$to" ] && { [ "$UPGRADE" != 1 ] || cmp -s "$SRC/n8n/$f" "$to"; }; then continue; fi
  [ -e "$to" ] && echo "  updated  /usr/local/share/assistant-n8n/$f"
  mkdir -p "$(dirname "$to")"
  case "$f" in install-n8n.sh|n8n-admin) install -m 755 "$SRC/n8n/$f" "$to" ;; *) install -m 644 "$SRC/n8n/$f" "$to" ;; esac
done
# n8n-admin, once install-n8n.sh has put it in place, holds nothing of yours: an upgrade keeps it current.
if [ "$UPGRADE" = 1 ] && [ -e "$D/usr/local/sbin/n8n-admin" ] && ! cmp -s "$SRC/n8n/n8n-admin" "$D/usr/local/sbin/n8n-admin"; then
  install -m 755 "$SRC/n8n/n8n-admin" "$D/usr/local/sbin/n8n-admin"; echo "  updated  /usr/local/sbin/n8n-admin"
fi
# All the guides and the changelog, refreshed on every run, so the assistant can read them on its own machine.
# (The two copies under assistant-n8n/docs/ are for CLAUDE.md files from 1.3.0 and 1.4.0 that point there.)
for f in "$REPO"/docs/*.md "$REPO/CHANGELOG.md"; do install -D -m 644 "$f" "$D$SHARE/docs/$(basename "$f")"; done
for f in n8n.md wakeup.md; do install -D -m 644 "$REPO/docs/$f" "$D/usr/local/share/assistant-n8n/docs/$f"; done
echo "  copied   the n8n kit to /usr/local/share/assistant-n8n/ (not installed) and the guides to $SHARE/docs/"

# The version and settings of this install. From a git clone, git describe (the release tag, or the tag plus the
# commits after it); otherwise the newest release in CHANGELOG.md, "+unreleased" if there are changes after it.
VERSION=$(git -c safe.directory="$REPO" -C "$REPO" describe --tags --always --dirty 2>/dev/null || true)
if [ -z "$VERSION" ]; then
  VERSION=v$(sed -n 's/^## \([0-9][0-9.]*\) .*/\1/p' "$REPO/CHANGELOG.md" | head -1)
  [ "$(grep -m1 '^## ' "$REPO/CHANGELOG.md")" = "## Unreleased" ] && VERSION="$VERSION+unreleased"
fi
SOURCE=$(git -c safe.directory="$REPO" -C "$REPO" remote get-url origin 2>/dev/null | sed -E 's#//[^@/]*@#//#' || true)
SOURCE=${SOURCE:-https://github.com/jonjunq/claudia}
GITHUB_REPO=$(echo "$SOURCE" | sed -nE 's#^.*github\.com[:/]([^/]+/[^/]+)$#\1#p' | sed 's/\.git$//')
mkdir -p "$D$SHARE"
cat > "$D$CONF" <<CONFEOF
# Written by install.sh on every run. The assistant reads its version here; later runs reuse these settings.
VERSION=$VERSION
SOURCE=$SOURCE
GITHUB_REPO=${GITHUB_REPO:-jonjunq/claudia}
INSTALL_USER=$U
NAME=$NAME
OWNER=$OWNER
LANGUAGE=$LANGUAGE
TIMEZONE=$TIMEZONE
INSTALLED_AT=$TODAY
CONFEOF
chmod 644 "$D$CONF"
echo "  wrote    $CONF (version $VERSION)"
[ -z "$D" ] && systemctl daemon-reload

if [ "$UPGRADE" = 1 ]; then
  cat <<EOF

Upgraded to $VERSION. Next (docs/updating.md):
  - Review each .new file listed above; move it over the original when it is right, or delete it.
  - Enable any new unit listed as created, then restart what changed: assistant-wakeup, assistant-permission-watch,
    and the session last (it ends the current conversation): systemctl restart assistant
EOF
  exit 0
fi

cat <<EOF

Next steps (details in docs/setup.md):
  1. As $U: claude            -> log in with your Claude subscription, then:
       /plugin install telegram@claude-plugins-official
       /telegram:configure <token from @BotFather>
     exit, run: claude --channels plugin:telegram@claude-plugins-official
     message your bot, then: /telegram:access pair <code>   and   /telegram:access policy allowlist
  2. Read and adapt $H/assistant/CLAUDE.md
  3. As root: systemctl enable --now assistant assistant-permission-watch assistant-history.timer
  4. Attach to watch it: sudo -u $U tmux attach -t assistant   (detach: Ctrl+B D)
Optional:
  - Wake-up instead of Monitors (docs/wakeup.md): systemctl enable --now assistant-wakeup
  - n8n for alerts that need no thinking (docs/n8n.md): /usr/local/share/assistant-n8n/install-n8n.sh --help
  - A full browser with a window, and a remote window for captchas (docs/browser.md)
EOF
