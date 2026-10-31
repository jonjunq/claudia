#!/bin/bash
# Accepts the "--dangerously-load-development-channels" confirmation that Claude Code shows at start,
# so an unattended restart does not sit waiting for a key. Only presses Enter on that exact dialog,
# with the "local development" option selected. Gives up after 2 minutes.
# shellcheck source=lib.sh
. "$(dirname "$(readlink -f "$0")")/lib.sh"
load_env
LOG="$ASSISTANT_DIR/accept-dev-channel.log"
for _ in $(seq 1 60); do
  sleep 2
  screen=$(tmux capture-pane -p -t "$TMUX_SESSION" 2>/dev/null) || continue
  if echo "$screen" | grep -qi "local development"; then
    # The selected option carries "❯". If it is not the "local development" one, move down and look again.
    if echo "$screen" | grep -E "❯" | grep -qi "local development"; then
      tmux send-keys -t "$TMUX_SESSION" Enter
      echo "[$(date)] accepted" >> "$LOG"
      exit 0
    fi
    tmux send-keys -t "$TMUX_SESSION" Down
  fi
done
echo "[$(date)] dialog did not show up in 2 min" >> "$LOG"
