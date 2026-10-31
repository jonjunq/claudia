#!/bin/bash
# Claude Code status line. Besides printing one line, it saves model, context and plan usage to
# state.json so the assistant can answer /usage from Telegram (it cannot see its own terminal).
# rate_limits only exist on subscription plans, and are refreshed after each reply.
DIR="${ASSISTANT_DIR:-$HOME/assistant}"
input=$(cat)
echo "$input" | jq --arg ts "$(date "+%Y-%m-%d %H:%M")" '{updated: $ts, model: .model.display_name,
  context_pct: .context_window.used_percentage, context_max: .context_window.context_window_size,
  five_hour_pct: .rate_limits.five_hour.used_percentage, five_hour_resets_at: .rate_limits.five_hour.resets_at,
  week_pct: .rate_limits.seven_day.used_percentage, week_resets_at: .rate_limits.seven_day.resets_at}' \
  > "$DIR/state.json.tmp" 2>/dev/null && mv "$DIR/state.json.tmp" "$DIR/state.json"
echo "$input" | jq -r '"[\(.model.display_name)] ctx \(.context_window.used_percentage // 0)% · 5h \(.rate_limits.five_hour.used_percentage // "-")% · week \(.rate_limits.seven_day.used_percentage // "-")%"'
