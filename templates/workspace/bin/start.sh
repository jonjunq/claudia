#!/bin/bash
# Keeps the assistant's Claude Code session alive. Runs inside tmux, started by assistant.service.
#  - Normally it resumes the previous conversation (--continue).
#  - If $ASSISTANT_DIR/.new-session exists (the daily restart creates it), it starts a clean conversation.
#  - If --continue fails at once (nothing to continue), it starts a new one; if it fails after a while
#    (Claude Code exited mid-conversation), the next round resumes again.
# shellcheck source=lib.sh
. "$(dirname "$(readlink -f "$0")")/lib.sh"
export PATH="$HOME/.local/bin:$HOME/.bun/bin:$PATH"
cd "$ASSISTANT_DIR" || exit 1
LOG="$ASSISTANT_DIR/restarts.log"
TG_EXTRAS="${TG_EXTRAS:-/usr/local/lib/assistant-telegram}"

FIRST_PROMPT="New conversation after the daily restart. notes/todo.md, notes/yesterday.md and notes/routines.md are already loaded: schedule today's routines. Do not message the owner about this; wait until they write."

while true; do
  load_env
  # Telegram extras (docs/telegram-extras.md): re-apply the plugin patch at every start, because a plugin update
  # replaces it, and tell the plugin whether permission-hook.py handles permission requests.
  if [ -x "$TG_EXTRAS/patch-telegram-plugin.py" ]; then
    python3 -I "$TG_EXTRAS/patch-telegram-plugin.py" >> "$LOG" 2>&1 ||
      tg_send "⚠️ The Telegram plugin changed and the assistant's patch no longer fits: quoted messages, permission buttons, the automatic transcription of voice notes and the instant /usage are off until patch-telegram-plugin.py is adapted."
    if grep -q permission-hook.py "$HOME/.claude/settings.json" 2>/dev/null; then
      touch "$TG_DIR/permission-hook-enabled"
    else
      rm -f "$TG_DIR/permission-hook-enabled"
    fi
  fi
  MODEL="${MODEL:-opus}"
  # Helpers (subagents, .claude/agents/) run on the same model as the session, whatever an agent definition or a
  # built-in agent (Explore, claude-code-guide…) would pick: SUBAGENT_MODEL in assistant.env, or MODEL.
  export CLAUDE_CODE_SUBAGENT_MODEL="${SUBAGENT_MODEL:-$MODEL}" CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1
  CHANNELS=(--channels plugin:telegram@claude-plugins-official)
  if [ -n "${DEV_CHANNELS:-}" ]; then
    # Self-built channels built with a recent MCP SDK may need this to register as a channel (see docs/voice.md).
    export MCP_PROTOCOL_NEGOTIATION=legacy
    read -r -a DEV <<< "$DEV_CHANNELS"
    CHANNELS+=(--dangerously-load-development-channels "${DEV[@]}")
    # Claude Code asks to confirm development channels at every start: accept that one dialog only.
    "$ASSISTANT_DIR/bin/accept-dev-channel.sh" &
  fi

  if [ -f "$ASSISTANT_DIR/.new-session" ]; then
    rm -f "$ASSISTANT_DIR/.new-session"
    echo "[$(date)] start: new conversation" >> "$LOG"
    # The prompt goes BEFORE --channels: --channels takes several values and would swallow it.
    claude "$FIRST_PROMPT" --model "$MODEL" "${CHANNELS[@]}"
  else
    started=$(date +%s)
    if ! claude --model "$MODEL" "${CHANNELS[@]}" --continue && [ $(( $(date +%s) - started )) -lt 30 ]; then
      echo "[$(date)] --continue failed at once: new conversation" >> "$LOG"
      [ -n "${DEV_CHANNELS:-}" ] && "$ASSISTANT_DIR/bin/accept-dev-channel.sh" &
      claude --model "$MODEL" "${CHANNELS[@]}"
    fi
  fi
  echo "[$(date)] claude exited; restarting in 10 s" >> "$LOG"
  sleep 10
done
