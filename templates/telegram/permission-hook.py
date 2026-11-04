#!/usr/bin/env python3
"""PermissionRequest hook: sends the request to Telegram with Allow / Deny buttons and waits for your answer.
The patched Telegram plugin (patch-telegram-plugin.py) writes the verdict to verdicts/<id> when you tap a button.
With no answer before WAIT, it returns no decision and the request goes on as usual (terminal dialog).
The id is random and only travels in the Telegram message, so a verdict file cannot be prepared in advance."""
import json, os, secrets, sys, time
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import tg

WAIT = int(os.environ.get("ASSISTANT_PERMISSION_WAIT", "570"))  # the hook's timeout in settings.json is 600

hook = json.load(sys.stdin)
if not tg.is_assistant(hook):
    sys.exit(0)

name = hook.get("tool_name", "?")
tool_input = hook.get("tool_input") or {}
what = tg.describe(name, tool_input)
detail = tool_input.get("command") or json.dumps(tool_input, ensure_ascii=False, indent=1)
if len(detail) > 1500:
    detail = detail[:700] + "\n[…]\n" + detail[-700:]

rid = secrets.token_hex(8)
os.makedirs(tg.VERDICTS, mode=0o700, exist_ok=True)
verdict_file = os.path.join(tg.VERDICTS, rid)
CHAT = tg.chat_id()
head = f"🔐 Permission request\n\n{name}: {what}"
text = f"{head}\n\n{detail}\n\nYou have {WAIT // 60} min to answer; after that its terminal decides."
buttons = {"inline_keyboard": [[{"text": "✅ Allow", "callback_data": f"hk:allow:{rid}"},
                                {"text": "❌ Deny", "callback_data": f"hk:deny:{rid}"}]]}
r = tg.api("sendMessage", chat_id=CHAT, text=text[:4000], reply_markup=buttons)
if not r:  # a timeout does not mean it was not delivered: do not resend (duplicates), wait for the button anyway
    tg.log(f"permission {rid}: sendMessage not confirmed, waiting for the button anyway")
msg_id = r["message_id"] if r else None
pending = os.path.join(tg.STATE, "permission-pending.json")
tg.write_json(pending, {"since": time.time(), "what": f"{name}: {what}"})
tg.log(f"permission asked {rid} {name}: {what}")

verdict = None
deadline = time.time() + WAIT
try:
    while time.time() < deadline:
        if os.path.exists(verdict_file):
            verdict = open(verdict_file).read().strip()
            os.remove(verdict_file)
            break
        time.sleep(0.5)
finally:
    try:
        os.remove(pending)
    except OSError:
        pass

if verdict not in ("allow", "deny"):
    msg_id and tg.api("editMessageText", chat_id=CHAT, message_id=msg_id, text=f"{head}\n\n⌛ No answer: its terminal decided.")
    tg.log(f"permission {rid} no answer")
    sys.exit(0)

label = "✅ Allowed" if verdict == "allow" else "❌ Denied"
msg_id and tg.api("editMessageText", chat_id=CHAT, message_id=msg_id, text=f"{head}\n\n{label} from Telegram")
tg.log(f"permission {rid} {verdict}")
decision = {"behavior": verdict}
if verdict == "deny":
    decision["message"] = "The owner denied this from Telegram. Do not retry it; ask them if you need it."
print(json.dumps({"hookSpecificOutput": {"hookEventName": "PermissionRequest", "decision": decision}}))
