#!/usr/bin/env python3
"""PermissionDenied hook: the auto-mode classifier denied a call. It sends it to Telegram with Approve / Keep blocked
buttons and waits. If you approve, it leaves a one-time approval for that exact call (used up by approved-hook.py
in PreToolUse) and tells the model it may retry. With no answer, or "Keep blocked", the denial stands.
Without this, a blocked call in an unattended session just fails and you only learn about it later."""
import json, os, secrets, sys, time
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import tg, approvals

WAIT = int(os.environ.get("ASSISTANT_PERMISSION_WAIT", "570"))  # the hook's timeout in settings.json is 600

hook = json.load(sys.stdin)
if not tg.is_assistant(hook):
    sys.exit(0)

name = hook.get("tool_name", "?")
tool_input = hook.get("tool_input") or {}
what = tg.describe(name, tool_input)
reason = (hook.get("reason") or "").strip() or "no reason given"
detail = tool_input.get("command") or json.dumps(tool_input, ensure_ascii=False, indent=1)
if len(detail) > 1500:
    detail = detail[:700] + "\n[…]\n" + detail[-700:]
if len(reason) > 400:
    reason = reason[:400] + "…"

rid = secrets.token_hex(8)
os.makedirs(tg.VERDICTS, mode=0o700, exist_ok=True)
verdict_file = os.path.join(tg.VERDICTS, rid)
CHAT = tg.chat_id()
who = f" (to helper {hook['agent_type']})" if hook.get("agent_type") else ""  # a subagent's call
head = f"🚫 The classifier blocked this{who}\n\n{name}: {what}"
text = (f"{head}\n\nClassifier's reason: {reason}\n\n{detail}\n\n"
        f"Approve it? You have {WAIT // 60} min; with no answer it stays blocked.")
buttons = {"inline_keyboard": [[{"text": "✅ Approve", "callback_data": f"hk:allow:{rid}"},
                                {"text": "❌ Keep blocked", "callback_data": f"hk:deny:{rid}"}]]}
r = tg.api("sendMessage", chat_id=CHAT, text=text[:4000], reply_markup=buttons)
if not r:  # a timeout does not mean it was not delivered: wait for the button anyway, without resending
    tg.log(f"denied {rid}: sendMessage not confirmed, waiting for the button anyway")
msg_id = r["message_id"] if r else None
tg.log(f"denied {rid} {name}: {what} · {reason[:120]}")

verdict = None
# Without confirmation from Telegram, do not hold the session for the full WAIT: 3 min in case it did arrive
deadline = time.time() + (WAIT if r else min(WAIT, 180))
while time.time() < deadline:
    if os.path.exists(verdict_file):
        verdict = open(verdict_file).read().strip()
        os.remove(verdict_file)
        break
    time.sleep(0.5)

if verdict == "allow":
    approvals.save(name, tool_input)
    msg_id and tg.api("editMessageText", chat_id=CHAT, message_id=msg_id,
                      text=f"{head}\n\n✅ Approved from Telegram (for that exact call, once)")
    tg.log(f"denied {rid} approved")
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PermissionDenied", "retry": True}}))
    sys.exit(0)

label = "❌ Kept blocked" if verdict == "deny" else "⌛ No answer: it stays blocked"
msg_id and tg.api("editMessageText", chat_id=CHAT, message_id=msg_id, text=f"{head}\n\n{label}")
tg.log(f"denied {rid} {verdict or 'no answer'}")
