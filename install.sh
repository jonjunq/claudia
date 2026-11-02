#!/bin/bash
# Installs the assistant's workspace, scripts and services for one user. Run as root.
#   sudo ./install.sh <user> [--name Claudia] [--owner Alex] [--language English] [--timezone Europe/Madrid]
# It never overwrites existing files: re-running it only adds what is missing. It does not start anything;
# it prints the remaining steps. DESTDIR=/some/dir installs under that prefix (used by the tests).
set -euo pipefail
SRC=$(dirname "$(readlink -f "$0")")/templates
U="${1:-}"
if [ -z "$U" ]; then sed -n '2,5p' "$0"; exit 1; fi
shift
NAME=Claudia; OWNER=$U; LANGUAGE=English; TIMEZONE=$(cat /etc/timezone 2>/dev/null || echo UTC)
while [ $# -gt 0 ]; do
  case "$1" in
    --name) NAME=$2; shift 2 ;;
    --owner) OWNER=$2; shift 2 ;;
    --language) LANGUAGE=$2; shift 2 ;;
    --timezone) TIMEZONE=$2; shift 2 ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done
D="${DESTDIR:-}"
if [ -z "$D" ]; then
  [ "$(id -u)" -eq 0 ] || { echo "Run as root (it installs systemd units and a cron file)" >&2; exit 1; }
  H=$(getent passwd "$U" | cut -d: -f6) || { echo "No such user: $U" >&2; exit 1; }
else
  H=/home/$U
fi

# Copies a template unless the target exists, filling in the placeholders.
put() {
  local from=$1 to=$2 mode=$3
  if [ -e "$D$to" ]; then echo "  kept     $to"; return; fi
  mkdir -p "$(dirname "$D$to")"
  sed -e "s|__USER__|$U|g" -e "s|__HOME__|$H|g" -e "s|__NAME__|$NAME|g" -e "s|__OWNER__|$OWNER|g" \
      -e "s|__LANGUAGE__|$LANGUAGE|g" -e "s|__TIMEZONE__|$TIMEZONE|g" "$from" > "$D$to"
  chmod "$mode" "$D$to"
  echo "  created  $to"
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
  printf '# API keys for the optional voice scripts. Only the owner can read this file.\n#GROQ_API_KEY=\n#ELEVENLABS_API_KEY=\n' \
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
  case "$f" in */tg.py) mode=644 ;; *) mode=755 ;; esac
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
[ -z "$D" ] && systemctl daemon-reload

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
EOF
