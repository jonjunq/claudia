#!/bin/bash
# Tells you on Telegram when the assistant is stuck on a permission prompt in its terminal.
# Some prompts (e.g. actions the auto-mode classifier sends to the terminal) are not relayed to
# Telegram and are denied by themselves after a while; without this you only see a silent assistant.
# It also tells you when the session changes model on its own: with "switchModelsOnFlag" in settings.json,
# a reply flagged by the model's safeguards moves the session to another model instead of pausing it.
# The model is read from state.json, which the status line writes after each reply.
# Run it as a service (assistant-permission-watch.service).
# shellcheck source=lib.sh
. "$(dirname "$(readlink -f "$0")")/lib.sh"
load_env
last=""
model_prev=""
while true; do
  screen=$(tmux capture-pane -t "$TMUX_SESSION" -p 2>/dev/null)
  if echo "$screen" | grep -q "Do you want to proceed?"; then
    key=$(echo "$screen" | sed -n "/Tool use/,/Do you want/p" | md5sum | cut -c1-12)
    if [ "$key" != "$last" ]; then
      last=$key
      what=$(echo "$screen" | sed -n "/Tool use/{n;p;q}" | sed "s/ Tool: (MCP)//; s/^ *//")
      why=$(echo "$screen" | grep -o "Latest blocked action: \[[^]]*\]" | sed "s/Latest blocked action: //")
      tg_send "⏸️ The assistant is waiting for permission in its terminal: ${what:-a tool} ${why}. If nobody answers it will be denied. To allow it for good, add a rule to ~/.claude/settings.json."
      echo "[$(date)] prompt: $what $why" >> "$ASSISTANT_DIR/permission-watch.log"
    fi
  else
    last=""
  fi
  model=$(jq -r '.model // empty' "$ASSISTANT_DIR/state.json" 2>/dev/null)
  if [ -n "$model" ]; then
    if [ -n "$model_prev" ] && [ "$model" != "$model_prev" ]; then
      tg_send "🔀 The assistant switched from ${model_prev} to ${model}. Usually a safeguard flagged a reply (often a false positive) and it moved on instead of pausing. It keeps working; the next start goes back to MODEL from assistant.env."
      echo "[$(date)] model: $model_prev -> $model" >> "$ASSISTANT_DIR/permission-watch.log"
    fi
    model_prev=$model
  fi
  sleep 5
done
