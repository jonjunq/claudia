#!/usr/bin/env python3
"""SessionStart hook (matcher "compact"): right after the conversation is compacted, by hand, on its own or while
idle, the old conversation is only a summary. This hands the assistant back what must not get lost even if the
summary misses it: the owner's last messages and its own last answers almost word for word, a permission request
still waiting on Telegram, whether the compaction was the idle one (assistant-idle-compact), and what to check before
going on. CLAUDE.md (with the notes it imports) is reloaded by Claude Code itself after compacting, so it is not
repeated here. Idea: the memory flush OpenClaw and Hermes do before compacting; Claude Code's PreCompact hook cannot
add context, SessionStart can.
Only acts in the assistant's session. No output = nothing added."""
import calendar, json, os, re, sys, time
sys.path.insert(0, os.environ.get("TG_EXTRAS", "/usr/local/lib/assistant-telegram"))
import tg

MAX_OWNER, MAX_OWN, WINDOW = 8, 4, 3 * 3600  # messages kept, and how far back (seconds)

hook = json.load(sys.stdin)
if not tg.is_assistant(hook) or hook.get("source") != "compact":
    sys.exit(0)
try:
    owner = str(tg.chat_id())
except Exception:
    owner = ""
CHANNEL = re.compile(r'<channel source="[^"]*telegram[^"]*"([^>]*)>\n?(.*?)\n?</channel>', re.S)


def short(text, n):
    text = " ".join(str(text).split())
    return text if len(text) <= n else text[:n] + "…"


try:
    with open(hook.get("transcript_path") or "", "rb") as f:
        f.seek(0, 2)
        start = max(0, f.tell() - 4_000_000)
        f.seek(start)
        lines = f.read().decode("utf-8", "ignore").splitlines()[1 if start else 0:]  # a cut first line is dropped
except OSError:
    lines = []
now = time.time()
said, answered = [], []
for line in lines:
    if '"timestamp"' not in line:
        continue
    try:
        d = json.loads(line)
    except ValueError:
        continue
    if d.get("isSidechain") or d.get("isCompactSummary"):
        continue
    try:
        when = calendar.timegm(time.strptime(d["timestamp"][:19], "%Y-%m-%dT%H:%M:%S"))
    except (KeyError, ValueError):
        continue
    if now - when > WINDOW:
        continue
    hm = time.strftime("%H:%M", time.localtime(when))
    content = (d.get("message") or {}).get("content")
    if d.get("type") == "user":
        texts = [content] if isinstance(content, str) else [b.get("text", "") for b in content or []
                                                           if isinstance(b, dict) and b.get("type") == "text"]
        for text in texts:
            for attrs, body in CHANNEL.findall(text):
                if owner and not re.search(rf'\b(user_id|chat_id|user)="{re.escape(owner)}"', attrs):
                    continue
                voice = " (voice note)" if "voice_transcribed_by" in attrs else ""
                said.append(f"- {hm}{voice}: {short(body, 500)}")
    elif d.get("type") == "assistant":
        for b in content or []:
            if isinstance(b, dict) and b.get("type") == "tool_use" and str(b.get("name", "")).endswith("telegram__reply"):
                answered.append(f"- {hm}: {short((b.get('input') or {}).get('text', ''), 300)}")

parts = ["[After compacting] Your earlier conversation is now a summary. So that nothing gets lost:"]
mark = tg.read_json(os.path.join(tg.STATE, "idle-compact.json"))
if mark and now - mark.get("at", 0) < 1800:
    parts.append(f"- This compaction was done by the idle-compaction service because there had been no messages or "
                 f"work for {mark.get('minutes', '?')} min (not a failure). Do not message the owner about it.")
pending = tg.read_json(os.path.join(tg.STATE, "permission-pending.json"))
if pending and now - pending.get("since", 0) < 900:
    parts.append(f"- A permission request is waiting for the owner on Telegram: {pending.get('what', '')}")
parts += [
    "- Check with CronList that today's reminders and routines are still scheduled (notes/todo.md, notes/routines.md);"
    " schedule only what is missing.",
    "- If the summary has tasks half done, yeses from the owner (purchases, subscriptions, emails to send) or"
    " commitments that are not in notes/todo.md, write them down now. Before repeating a payment or a send, check"
    " whether it already happened.",
    "- If you had launched helpers (subagents) that have not finished, their result will reach you by itself: do not"
    " launch them again.",
]
if said:
    parts += ["", "The owner's last messages (word for word, trimmed):"] + said[-MAX_OWNER:]
if answered:
    parts += ["", "Your last answers to them:"] + answered[-MAX_OWN:]
print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": "\n".join(parts)}},
                 ensure_ascii=False))
