#!/bin/bash
# Tells you on Telegram when the assistant is stuck on a permission prompt in its terminal.
# Most prompts reach you on Telegram with buttons (permission-hook.py); this is the fallback for any that do not
# (Telegram down, hook not installed). Without it you would only see a silent assistant.
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
  # A request that permission-hook.py already sent you with buttons is not reported twice.
  if echo "$screen" | grep -q "Do you want to proceed?" && [ ! -e "$HOME/.cache/assistant-telegram/permission-pending.json" ]; then
    # The dialog: from the last border line (────) down to "Do you want to proceed?".
    block=$(echo "$screen" | awk '/^ *─{20,}/{b=""; next} {b=b"\n"$0} /Do you want to proceed\?/{print b; exit}' | sed '/^\s*$/d')
    key=$(echo "$block" | md5sum | cut -c1-12)
    if [ "$key" != "$last" ]; then
      last=$key
      # First two lines: kind of tool and its description ("Bash command" / "Merge two PDFs").
      what=$(echo "$block" | grep -v "^ *Tip:" | head -2 | sed "s/^ *//; s/ Tool: (MCP)//" | paste -sd ":" | sed "s/:/: /")
      why=$(echo "$block" | grep -oE "Latest blocked action: \[[^]]*\]|[A-Z][^│]*manual approval required[^│]*" | head -1 | sed "s/Latest blocked action: //; s/ *$//")
      tg_send "⏸️ The assistant is waiting for permission in its terminal: ${what:-a tool}${why:+ ($why)}. If nobody answers it will be denied. To allow it for good, add a rule to ~/.claude/settings.json."
      echo "[$(date)] prompt: $what | $why" >> "$ASSISTANT_DIR/permission-watch.log"
    fi
  elif ! echo "$screen" | grep -q "Do you want to proceed?"; then
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
