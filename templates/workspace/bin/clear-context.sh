#!/bin/bash
# /clear from Telegram: start a fresh conversation mid-day without restarting the service.
# The assistant runs this as its LAST step, after saving whatever was in progress. In the background it
# waits for the current turn to end, types /clear into the session and sends the first message of the
# new conversation.
# shellcheck source=lib.sh
. "$(dirname "$(readlink -f "$0")")/lib.sh"
load_env

if [ "${1:-}" = "--later" ]; then
  sleep 5
  for _ in $(seq 1 60); do session_busy || break; sleep 5; done   # wait up to 5 min for the turn to end
  sleep 3
  tmux_say "/clear"
  sleep 8
  tmux_say "New conversation because the owner asked for /clear from Telegram (this is not the daily restart). notes/todo.md, notes/yesterday.md and notes/routines.md are loaded, and what was in progress is in notes/todo.md. Do the 'At the start of every conversation' part of notes/routines.md, check with CronList which routines are still scheduled and schedule only the missing ones for today. Then tell the owner on Telegram, in one line, that the context is clean."
  echo "[$(date)] /clear done" >> "$ASSISTANT_DIR/restarts.log"
  exit 0
fi

echo "[$(date)] /clear requested" >> "$ASSISTANT_DIR/restarts.log"
# setsid + nohup: the waiting part must outlive the tool call that started it.
setsid nohup "$0" --later >/dev/null 2>&1 &
echo "Done: when this turn ends the context is cleared and the first message of the new conversation arrives."
