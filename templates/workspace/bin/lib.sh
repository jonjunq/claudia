# shellcheck shell=bash
# Shared helpers for the assistant scripts. Sourced, not run.

ASSISTANT_DIR="${ASSISTANT_DIR:-$HOME/assistant}"
TG_DIR="$HOME/.claude/channels/telegram"

load_env() {
  # shellcheck source=/dev/null
  [ -f "$ASSISTANT_DIR/assistant.env" ] && . "$ASSISTANT_DIR/assistant.env"
  TMUX_SESSION="${TMUX_SESSION:-assistant}"
}

# Bot token as saved by /telegram:configure.
tg_token() {
  sed -n 's/^TELEGRAM_BOT_TOKEN=//p' "$TG_DIR/.env" 2>/dev/null | tr -d "\"'"
}

# Chat to send to: TELEGRAM_CHAT_ID, or the first paired sender in the plugin's allowlist.
tg_chat() {
  if [ -n "${TELEGRAM_CHAT_ID:-}" ]; then echo "$TELEGRAM_CHAT_ID"; return; fi
  jq -r '.allowFrom[0] // empty' "$TG_DIR/access.json" 2>/dev/null
}

# curl with what is secret in it (a URL with a token, a key header) on stdin, never on its command line, where any
# user of this machine could read it (ps). curl_secret <url> <header, or ""> [curl options...]; neither holds a quote.
curl_secret() {
  local url=$1 hdr=$2; shift 2
  { printf 'url = "%s"\n' "$url"; [ -z "$hdr" ] || printf 'header = "%s"\n' "$hdr"; } | curl -K - "$@"
}

# Send a text message. sendMessage does not interfere with the plugin's getUpdates polling.
tg_send() {
  local token chat
  token=$(tg_token); chat=$(tg_chat)
  [ -n "$token" ] && [ -n "$chat" ] || { echo "Telegram not configured" >&2; return 1; }
  curl_secret "https://api.telegram.org/bot${token}/sendMessage" "" -s -o /dev/null --max-time 10 \
    --data-urlencode chat_id="$chat" --data-urlencode text="$1"
}

# Type a line into the session. -l sends it literally; Enter must go separately or the line is left unsent.
tmux_say() {
  tmux send-keys -t "$TMUX_SESSION" -l "$1"
  sleep 1
  tmux send-keys -t "$TMUX_SESSION" Enter
}

# True while Claude is working (the spinner line shows "… (12s").
# Heuristic tied to Claude Code's terminal UI: check it after big Claude Code updates.
session_busy() {
  tmux capture-pane -p -t "$TMUX_SESSION" 2>/dev/null | grep -qE '…\s*\([0-9]'
}
