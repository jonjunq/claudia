#!/bin/bash
# Checks for the repo: shellcheck, JSON validity, an install into a temporary directory, and a few script
# behaviours with fake tmux/claude. No network, no root, no Claude account needed.
set -u
cd "$(dirname "$(readlink -f "$0")")/.." || exit 1
pass=0; fail=0
ok() { echo "ok   $1"; pass=$((pass + 1)); }
ko() { echo "FAIL $1"; fail=$((fail + 1)); }
check() { local name=$1; shift; if "$@" >/dev/null 2>&1; then ok "$name"; else ko "$name"; fi; }

SCRIPTS=(install.sh tests/run-tests.sh templates/system/assistant-daily-restart templates/system/recall templates/workspace/bin/*.sh templates/tools/*.sh templates/memory/*.sh)
check "shellcheck" shellcheck -S warning -x "${SCRIPTS[@]}"
for s in "${SCRIPTS[@]}"; do check "bash -n $s" bash -n "$s"; done
check "settings.json is valid JSON" jq -e . templates/settings.json
check "settings.json has the Telegram hooks" jq -e '.hooks.PermissionRequest[0].hooks[0].timeout == 600 and (.hooks.PreToolUse[0].hooks[0].async == true)' templates/settings.json
for p in templates/telegram/*.py templates/memory/*.py tests/*.py; do check "python compiles $p" python3 -m py_compile "$p"; done
find templates tests -name __pycache__ -exec rm -rf {} +

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
check "browser skill installed" test -e "$H/assistant/.claude/skills/browser/SKILL.md"
check "Telegram extras installed" test -x "$T/usr/local/lib/assistant-telegram/permission-hook.py" -a -e "$T/usr/local/lib/assistant-telegram/tg.py"
check "memory tools installed" test -x "$T/usr/local/lib/assistant-memory/nightly-review.py" -a -x "$T/usr/local/bin/recall" -a -e "$T/usr/local/lib/assistant-memory/review-prompt.txt"
check "recall skill installed" test -e "$H/assistant/.claude/skills/recall/SKILL.md"
check "history timer installed" grep -q "history.sh alex hourly" "$T/etc/systemd/system/assistant-history.service"
check "review prompt filled in" grep -q "of Ada, Alex's personal assistant" "$T/usr/local/lib/assistant-memory/review-prompt.txt"
check "recall allowed in settings" jq -e '.permissions.allow | index("Bash(recall *)")' "$H/.claude/settings.json"
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

# permission-watch.sh notices a model switch in state.json, once
: > "$FAKE_SCREEN"; : > "$FAKE_LOG"
echo '{"model":"Opus 5.5"}' > "$H/assistant/state.json"
( sleep 3; echo '{"model":"Opus 4.8"}' > "$H/assistant/state.json" ) &
timeout 12 "$H/assistant/bin/permission-watch.sh" >/dev/null 2>&1
wait
check "permission-watch reports a model switch once" test "$(grep -c 'switched from Opus 5.5 to Opus 4.8' "$FAKE_LOG")" = 1

# permission-watch.sh reads the current dialog layout, and stays quiet when the hook already sent the request
cat > "$FAKE_SCREEN" <<'EOF2'
────────────────────────────────────────────────────────────
 Bash command
 Merge two PDFs into one
╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌
 │ cd /tmp && pdfunite a.pdf b.pdf c.pdf
 │ Compound command contains cd with write operation - manual approval required to prevent path resolution bypass
 Do you want to proceed?
 ❯ 1. Yes
EOF2
: > "$FAKE_LOG"
timeout 7 "$H/assistant/bin/permission-watch.sh" >/dev/null 2>&1
check "permission-watch names tool and description (new layout)" grep -q "Bash command: Merge two PDFs into one" "$FAKE_LOG"
check "permission-watch gives the reason (new layout)" grep -q "manual approval required" "$FAKE_LOG"
mkdir -p "$H/.cache/assistant-telegram"; echo '{}' > "$H/.cache/assistant-telegram/permission-pending.json"
: > "$FAKE_LOG"
timeout 7 "$H/assistant/bin/permission-watch.sh" >/dev/null 2>&1
check "permission-watch skips a request the hook already sent" test "$(grep -c sendMessage "$FAKE_LOG")" = 0
rm -f "$H/.cache/assistant-telegram/permission-pending.json"

# patch-telegram-plugin.py on a stand-in with the plugin's anchors: patches once, then leaves it alone
P="$T/plugin/0.0.7"; mkdir -p "$P"
cat > "$P/server.ts" <<'EOF2'
import { homedir } from 'os'
    instructions: [
      "Telegram's Bot API exposes no history or search — you only see messages as they arrive.",
    ],
    for (const chat_id of access.allowFrom) {
      void bot.api.sendMessage(chat_id, text, { reply_markup: keyboard }).catch(() => {})
    }
bot.on('callback_query:data', async ctx => {
  const data = ctx.callbackQuery.data
  const m = /^perm:(allow|deny|more):([a-km-z]{5})$/.exec(data)
})
async function handleInbound(
      meta: {
        ...(imagePath ? { image_path: imagePath } : {}),
      },
EOF2
export TG_PLUGIN_GLOB="$T/plugin/*/server.ts"
check "patcher patches" bash -c "python3 -I templates/telegram/patch-telegram-plugin.py | grep -q ': patched$'"
check "patch adds reply context" grep -q '\.\.\.replyMeta(ctx),' "$P/server.ts"
check "patch adds the hook buttons" grep -q 'hk:(allow|deny)' "$P/server.ts"
check "patch keeps the original" test -e "$P/server.ts.orig"
check "patcher is idempotent" bash -c "python3 -I templates/telegram/patch-telegram-plugin.py | grep -q 'already patched' && test \$(grep -c replyMeta '$P/server.ts') = 2"
grep -v handleInbound "$P/server.ts.orig" > "$P/server.ts"
if python3 -I templates/telegram/patch-telegram-plugin.py >/dev/null; then ko "patcher fails on a changed plugin"; else ok "patcher fails on a changed plugin"; fi
check "a failed patch changes nothing" bash -c "! grep -q 'ASSISTANT-PATCH' '$P/server.ts'"
unset TG_PLUGIN_GLOB

# status-hook.py records the step and the end of the turn, only for the assistant's session
TURN="$H/.cache/assistant-telegram/turn.json"; rm -f "$TURN"
hook() { echo "$1" | ASSISTANT_TG_NO_DAEMON=1 python3 -I templates/telegram/status-hook.py; }
hook '{"hook_event_name":"PreToolUse","cwd":"/tmp","tool_name":"Bash","tool_input":{"description":"x"}}'
check "status-hook ignores other sessions" test ! -e "$TURN"
hook '{"hook_event_name":"PreToolUse","cwd":"'"$H"'/assistant","tool_name":"Bash","tool_input":{"command":"ls","description":"List files"}}'
check "status-hook records the step" test "$(jq -r .step "$TURN")" = "List files"
hook '{"hook_event_name":"PreToolUse","cwd":"'"$H"'/assistant","tool_name":"mcp__claude_ai_Gmail__search_threads","tool_input":{}}'
check "status-hook describes MCP tools" test "$(jq -r .step "$TURN")" = "Gmail · search threads"
hook '{"hook_event_name":"Stop","cwd":"'"$H"'/assistant"}'
check "status-hook marks the end of the turn" jq -e '.end > 0' "$TURN"
# Background runs (e.g. the suggested reply) fire hooks but are not in the transcript: they must not open a turn
TR="$T/transcript.jsonl"; echo '{"type":"user","promptId":"real-1"}' > "$TR"; rm -f "$TURN"
ev() { hook '{"hook_event_name":"'"$1"'","cwd":"'"$H"'/assistant","prompt_id":"'"$2"'","transcript_path":"'"$TR"'","tool_name":"Bash","tool_input":{"description":"'"$3"'"}}'; }
ev PreToolUse real-1 "Step one"; ev Stop real-1 ""
ev PreToolUse real-1 "Late event"
check "status-hook ignores late events of a finished turn" jq -e '.end > 0 and .step == "Step one"' "$TURN"
ev PreToolUse ghost "No action"
check "status-hook ignores prompts that are not in the transcript" jq -e '.end > 0 and .step == "Step one"' "$TURN"
echo '{"type":"user","promptId":"real-2"}' >> "$TR"; ev PreToolUse real-2 "Step two"
check "status-hook opens a turn for a new real prompt" jq -e '(.end | not) and .step == "Step two" and .prompt == "real-2"' "$TURN"
ev PreToolUse ghost-2 "No action"
check "status-hook ignores background runs during a real turn" test "$(jq -r .step "$TURN")" = "Step two"

# permission-hook.py against a fake Telegram API: Allow from a button -> allow decision; no answer -> no decision
API_LOG="$T/api.log"; : > "$API_LOG"
python3 -I tests/fake-telegram.py 0 "$API_LOG" > "$T/port" &
FAKE_PID=$!
for _ in 1 2 3 4 5 6 7 8 9 10; do [ -s "$T/port" ] && break; sleep 0.3; done
TELEGRAM_API="http://127.0.0.1:$(cat "$T/port")"; export TELEGRAM_API
REQ='{"hook_event_name":"PermissionRequest","cwd":"'"$H"'/assistant","tool_name":"Bash","tool_input":{"command":"rm -rf build","description":"Remove the build folder"}}'
( for _ in $(seq 1 40); do
    id=$(grep -o 'hk:allow:[0-9a-f]\{16\}' "$API_LOG" | head -1 | cut -d: -f3)
    if [ -n "$id" ]; then mkdir -p "$H/.claude/channels/telegram/verdicts"; echo allow > "$H/.claude/channels/telegram/verdicts/$id"; break; fi
    sleep 0.25
  done ) &
out=$(echo "$REQ" | ASSISTANT_PERMISSION_WAIT=15 python3 -I templates/telegram/permission-hook.py)
wait $!
check "permission-hook sends the request with buttons" bash -c "grep '\"method\": \"sendMessage\"' '$API_LOG' | grep -q 'Remove the build folder'"
check "permission-hook returns the button's verdict" bash -c "echo '$out' | jq -e '.hookSpecificOutput.decision.behavior == \"allow\"'"
check "permission-hook edits the message with the outcome" grep -q 'Allowed from Telegram' "$API_LOG"
out=$(echo "$REQ" | ASSISTANT_PERMISSION_WAIT=1 python3 -I templates/telegram/permission-hook.py)
check "permission-hook without an answer leaves the decision to the terminal" test -z "$out"
check "permission-hook clears its pending flag" test ! -e "$H/.cache/assistant-telegram/permission-pending.json"
# Under cron the PATH is only /usr/bin:/bin and runuser lives in /usr/sbin: both entry points must not depend on it
check "assistant.cron sets a PATH with /usr/sbin" grep -q '^PATH=.*/usr/sbin' templates/system/assistant.cron
check "assistant-daily-restart exports a PATH with /usr/sbin" grep -q '^export PATH=.*/usr/sbin' templates/system/assistant-daily-restart
cat > "$T/runuser-check.py" <<'PY'
import importlib.util, sys
sys.argv = ["nightly-review.py", "root"]
spec = importlib.util.spec_from_file_location("nr", "templates/memory/nightly-review.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
m.ROOT = True
print(m.as_user(["true"])[0])
PY
check "nightly-review finds runuser without /usr/sbin in PATH" bash -c "PATH=/usr/bin:/bin python3 -I '$T/runuser-check.py' | grep -q '^/'"

# send-rich.py: Markdown from stdin goes out with sendRichMessage; an empty message is refused
printf '# Week\n\n| a | b |\n|---|---|\n| 1 | 2 |\n' | python3 -I templates/telegram/send-rich.py > "$T/rich.out"
check "send-rich sends a rich message" bash -c "grep '\"method\": \"sendRichMessage\"' '$API_LOG' | grep -q '| a | b |'"
check "send-rich prints the message id" grep -q 'sent, message_id 5' "$T/rich.out"
check "send-rich refuses an empty message" bash -c "! printf '  ' | python3 -I templates/telegram/send-rich.py 2>/dev/null"
kill "$FAKE_PID" 2>/dev/null; unset TELEGRAM_API

# start.sh also re-applies the plugin patch (here it no longer fits: it must say so) and flags the permission hook
export TG_EXTRAS="$T/usr/local/lib/assistant-telegram" TG_PLUGIN_GLOB="$T/plugin/*/server.ts"
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
check "start.sh flags the permission hook to the plugin" test -e "$H/.claude/channels/telegram/permission-hook-enabled"
check "start.sh reports a patch that no longer fits" grep -q "no longer fits" "$FAKE_LOG"
unset TG_EXTRAS TG_PLUGIN_GLOB

# vet-skill.sh with a fake SkillSpector: one report per skill folder, plus the whole repo.
cat > "$B/skillspector" <<'EOF'
#!/bin/bash
out=""; while [ $# -gt 0 ]; do [ "$1" = --output ] && out=$2; shift; done
printf '| Score | 7/100 |\n| Severity | LOW |\n| Recommendation | SAFE |\n### LOW: X1\n' > "$out"
EOF
chmod +x "$B/skillspector"
mkdir -p "$T/repo/skills/one" "$T/repo/skills/two"
touch "$T/repo/skills/one/SKILL.md" "$T/repo/skills/two/SKILL.md"
vet=$(VET_REPORTS="$T/reports" templates/tools/vet-skill.sh "$T/repo" 2>&1)
check "vet-skill lists each skill" grep -qE '^skills/one +7/100 +LOW +SAFE' <<<"$vet"
check "vet-skill lists every skill folder" grep -q '^skills/two ' <<<"$vet"
check "vet-skill writes per-skill reports" test -e "$(find "$T/reports" -name skill-skills_one.md | head -1)"
check "vet-skill scans the whole repo too" grep -q "Whole repo (indicative" <<<"$vet"

# recall: indexes a transcript and the diary, finds what the owner said, skips its own searches
WSP=$(readlink -m "$H/assistant" | sed 's/[^A-Za-z0-9]/-/g')
PRJ="$H/.claude/projects/$WSP"; mkdir -p "$PRJ/memory" "$H/assistant/notes/diary"
NOW=$(date -u +%FT%T.000Z)
cat > "$PRJ/s1.jsonl" <<EOF2
{"type":"user","timestamp":"$NOW","message":{"content":"<channel source=\"telegram\" chat_id=\"42\">Book the dentist for Thursday</channel>"}}
{"type":"assistant","timestamp":"$NOW","message":{"content":[{"type":"tool_use","id":"t1","name":"mcp__plugin_telegram_telegram__reply","input":{"text":"Done, Thursday at 10"}}]}}
{"type":"assistant","timestamp":"$NOW","message":{"content":[{"type":"tool_use","id":"t2","name":"Bash","input":{"command":"recall search dentist"}}]}}
EOF2
echo "Talked about the plumber." > "$H/assistant/notes/diary/2026-10-01.md"
export RECALL_DB="$T/recall.db"
check "recall finds the owner's message" bash -c "python3 -I templates/memory/recall.py search dentist | grep -q 'owner · s1'"
check "recall finds the assistant's reply" bash -c "python3 -I templates/memory/recall.py search thursday | grep -q 'assistant · s1'"
check "recall searches the diary" bash -c "python3 -I templates/memory/recall.py search plumb | grep -q 'diary'"
check "recall leaves its own searches out" bash -c "! python3 -I templates/memory/recall.py search dentist --all | grep -q 'recall search'"
check "recall show gives the context" bash -c "python3 -I templates/memory/recall.py show s1 0 | grep -q '>> \[0\]'"

# nightly review with a fake claude: applies a new skill, rejects a secret, commits history, tells the owner
mkdir -p "$H/.local/bin" "$H/assistant/.claude/skills"
printf -- '- [Owner](owner.md)\n' > "$PRJ/memory/MEMORY.md"
cat > "$H/.local/bin/claude" <<'EOF2'
#!/bin/bash
mkdir -p skills/demo
printf -- '---\nname: demo\ndescription: d\n---\nPress the blue button first.\n' > skills/demo/SKILL.md
printf 'api_key = abc123456789\n' >> memory/MEMORY.md
echo '{"result":"· skills/demo: new","num_turns":3,"usage":{"cache_read_input_tokens":10,"output_tokens":5},"is_error":false}'
EOF2
chmod +x "$H/.local/bin/claude"
API_LOG="$T/api2.log"; : > "$API_LOG"; : > "$T/port"
python3 -I tests/fake-telegram.py 0 "$API_LOG" > "$T/port" &
FAKE_PID=$!
for _ in 1 2 3 4 5 6 7 8 9 10; do [ -s "$T/port" ] && break; sleep 0.3; done
TELEGRAM_API="http://127.0.0.1:$(cat "$T/port")"
export TELEGRAM_API ASSISTANT_HOME="$H" REVIEW_STATE_DIR="$T/review" \
       ASSISTANT_HISTORY_DIR="$T/history" TG_EXTRAS="$PWD/templates/telegram" RECALL_DB="$H/.cache/assistant-recall.db"
echo "REVIEW_NOTIFY=yes" >> "$H/assistant/assistant.env"
review=$(python3 -I templates/memory/nightly-review.py alex 2>&1)
check "review runs" grep -q "applied \['skills/demo/SKILL.md'\]" <<<"$review"
check "review applies the new skill" grep -q "blue button" "$H/assistant/.claude/skills/demo/SKILL.md"
check "review rejects a secret" bash -c "! grep -q api_key '$PRJ/memory/MEMORY.md' && grep -q 'key or password' '$H/assistant/notes/last-review.md'"
check "review commits the history" bash -c "git --git-dir='$T/history' log --oneline | grep -q 'nightly review'"
check "review tells the owner" grep -q 'Nightly review' "$API_LOG"
check "review saves its state" jq -e '.last' "$T/review/state.json"
review=$(python3 -I templates/memory/nightly-review.py alex 2>&1)
check "review with nothing new does nothing" grep -q "nothing to review" <<<"$review"
# A new message arrives: reviewed from where the last one stopped; with REVIEW_NOTIFY off, no message to the owner
echo "{\"type\":\"user\",\"timestamp\":\"$(date -u +%FT%T.999Z)\",\"message\":{\"content\":\"<channel source=\\\"telegram\\\">Also the vet</channel>\"}}" >> "$PRJ/s1.jsonl"
sed -i 's/^REVIEW_NOTIFY=yes$/REVIEW_NOTIFY=no/' "$H/assistant/assistant.env"
rm -rf "$H/assistant/.claude/skills/demo"; : > "$API_LOG"
review=$(python3 -I templates/memory/nightly-review.py alex 2>&1)
check "review picks up the new message" grep -q "applied \['skills/demo/SKILL.md'\]" <<<"$review"
check "review is silent by default" test "$(grep -c sendMessage "$API_LOG")" = 0
kill "$FAKE_PID" 2>/dev/null
unset TELEGRAM_API ASSISTANT_HOME REVIEW_STATE_DIR ASSISTANT_HISTORY_DIR TG_EXTRAS RECALL_DB
find templates tests -name __pycache__ -exec rm -rf {} +

rm -rf "$T"
echo; echo "passed $pass, failed $fail"
[ "$fail" -eq 0 ]
