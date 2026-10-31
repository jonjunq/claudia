#!/bin/bash
# Checks for the repo: shellcheck, JSON validity, an install into a temporary directory, and a few script
# behaviours with fake tmux/claude. No network, no root, no Claude account needed.
set -u
cd "$(dirname "$(readlink -f "$0")")/.." || exit 1
pass=0; fail=0
ok() { echo "ok   $1"; pass=$((pass + 1)); }
ko() { echo "FAIL $1"; fail=$((fail + 1)); }
check() { local name=$1; shift; if "$@" >/dev/null 2>&1; then ok "$name"; else ko "$name"; fi; }

SCRIPTS=(install.sh tests/run-tests.sh templates/system/assistant-daily-restart templates/workspace/bin/*.sh)
check "shellcheck" shellcheck -S warning -x "${SCRIPTS[@]}"
for s in "${SCRIPTS[@]}"; do check "bash -n $s" bash -n "$s"; done
check "settings.json is valid JSON" jq -e . templates/settings.json

# No EXIT trap for the cleanup: bash runs it in the subshells of pipelines inside functions, too early.
T=$(mktemp -d)
out=$(DESTDIR="$T" ./install.sh alex --name Ada --owner Alex --language Spanish --timezone Europe/Madrid 2>&1)
check "install exits 0" test $? -eq 0
H="$T/home/alex"
for f in assistant/CLAUDE.md assistant/assistant.env assistant/notes/todo.md assistant/notes/yesterday.md \
         assistant/notes/routines.md assistant/bin/start.sh .claude/settings.json .config/assistant/keys.env; do
  check "installed $f" test -e "$H/$f"
done
check "scripts are executable" test -x "$H/assistant/bin/start.sh"
check "keys.env is private" test "$(stat -c %a "$H/.config/assistant/keys.env")" = 600
check "units installed" test -e "$T/etc/systemd/system/assistant.service" -a -e "$T/etc/cron.d/assistant"
check "no placeholders left" bash -c "! grep -rq '__[A-Z]*__' '$H' '$T/etc' '$T/usr'"
check "name and owner filled in" grep -q "You are \*\*Ada\*\*, Alex's" "$H/assistant/CLAUDE.md"
check "language filled in" grep -q "Always in Spanish" "$H/assistant/CLAUDE.md"
check "home filled in service" grep -q "ExecStart=.* /home/alex/assistant/bin/start.sh" "$T/etc/systemd/system/assistant.service"
check "installed settings valid JSON" jq -e . "$H/.claude/settings.json"
echo "edited" >> "$H/assistant/CLAUDE.md"
DESTDIR="$T" ./install.sh alex >/dev/null 2>&1
check "re-install keeps edits" grep -q "^edited$" "$H/assistant/CLAUDE.md"
[ -n "$out" ] || ko "install printed nothing"

# Fake tmux and claude to drive the scripts.
B="$T/bin"; mkdir -p "$B"
cat > "$B/tmux" <<'EOF'
#!/bin/bash
echo "tmux $*" >> "$FAKE_LOG"
[ "$1" = capture-pane ] && cat "$FAKE_SCREEN" 2>/dev/null
exit 0
EOF
cat > "$B/curl" <<'EOF'
#!/bin/bash
echo "curl $*" >> "$FAKE_LOG"
EOF
chmod +x "$B"/*
export FAKE_LOG="$T/fake.log" FAKE_SCREEN="$T/screen" PATH="$B:$PATH" HOME="$H" ASSISTANT_DIR="$H/assistant"
mkdir -p "$H/.claude/channels/telegram"
echo 'TELEGRAM_BOT_TOKEN="123:abc"' > "$H/.claude/channels/telegram/.env"
echo '{"dmPolicy":"allowlist","allowFrom":["42"]}' > "$H/.claude/channels/telegram/access.json"

# shellcheck source=../templates/workspace/bin/lib.sh
. templates/workspace/bin/lib.sh
load_env
check "load_env reads assistant.env" test "$TMUX_SESSION" = assistant
check "tg_token reads the plugin's .env" test "$(tg_token)" = "123:abc"
check "tg_chat falls back to the allowlist" test "$(tg_chat)" = 42
check "TELEGRAM_CHAT_ID wins" test "$(TELEGRAM_CHAT_ID=7 tg_chat)" = 7
: > "$FAKE_LOG"; tmux_say "hello world"
check "tmux_say sends literal text then Enter" bash -c "grep -q 'send-keys -t assistant -l hello world' '$FAKE_LOG' && tail -1 '$FAKE_LOG' | grep -q 'send-keys -t assistant Enter'"
printf '  ✻ Thinking… (12s · esc to interrupt)\n' > "$FAKE_SCREEN"
check "session_busy sees the spinner" session_busy
printf '> \n' > "$FAKE_SCREEN"
if session_busy; then ko "session_busy idle"; else ok "session_busy idle"; fi

# statusline.sh writes state.json
echo '{"model":{"display_name":"Opus"},"context_window":{"used_percentage":12,"context_window_size":200000},"rate_limits":{"five_hour":{"used_percentage":30,"resets_at":1700000000},"seven_day":{"used_percentage":55,"resets_at":1700500000}}}' \
  | "$H/assistant/bin/statusline.sh" > "$T/line"
check "statusline prints a line" grep -q "ctx 12% · 5h 30% · week 55%" "$T/line"
check "statusline writes state.json" test "$(jq -r .week_pct "$H/assistant/state.json")" = 55

# permission-watch.sh notices a prompt once
printf 'Tool use\n  gmail send_message Tool: (MCP)\nLatest blocked action: [External System Writes]\nDo you want to proceed?\n' > "$FAKE_SCREEN"
: > "$FAKE_LOG"
timeout 7 "$H/assistant/bin/permission-watch.sh" >/dev/null 2>&1
check "permission-watch sends one Telegram message" test "$(grep -c 'api.telegram.org/bot123:abc/sendMessage' "$FAKE_LOG")" = 1
check "permission-watch names the tool" grep -q "gmail send_message" "$FAKE_LOG"

# start.sh: fresh conversation when .new-session exists, prompt before --channels; fallback when --continue fails fast
cat > "$B/claude" <<'EOF'
#!/bin/bash
echo "claude $*" >> "$FAKE_LOG"
for a in "$@"; do [ "$a" = --continue ] && exit 1; done
exit 0
EOF
chmod +x "$B/claude"
: > "$FAKE_LOG"; touch "$H/assistant/.new-session"
timeout 3 "$H/assistant/bin/start.sh" >/dev/null 2>&1
check "new session: prompt goes before --channels" bash -c "grep '^claude ' '$FAKE_LOG' | head -1 | grep -q '^claude New conversation.* --model opus --channels plugin:telegram@claude-plugins-official$'"
check "new session: flag file consumed" test ! -e "$H/assistant/.new-session"
: > "$FAKE_LOG"
timeout 3 "$H/assistant/bin/start.sh" >/dev/null 2>&1
check "resume uses --continue" bash -c "grep '^claude ' '$FAKE_LOG' | head -1 | grep -q -- '--continue$'"
check "fast --continue failure falls back to a new conversation" bash -c "grep '^claude ' '$FAKE_LOG' | sed -n 2p | grep -qv -- '--continue'"
check "start.sh logs to restarts.log" grep -q "continue failed at once" "$H/assistant/restarts.log"

rm -rf "$T"
echo; echo "passed $pass, failed $fail"
[ "$fail" -eq 0 ]
