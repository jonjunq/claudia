#!/usr/bin/env python3
"""Keeps one status message on Telegram while the assistant works, and deletes it when the turn ends:
  ⏳ Working · 2 min 35 s / Now: <step> (for 20 s)
  ⚠️ … when it is stuck: waiting for permission, on a dialog, no progress for a while, or the session exited.
Pure script, no model calls. Telegram asks bots for at most about one message per second per chat, and edits
count; the typing action every 4 s plus an edit every 5 s stays well under that, leaving room for the replies."""
import os, subprocess, sys, time
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import tg

TURN = os.path.join(tg.STATE, "turn.json")
PENDING = os.path.join(tg.STATE, "permission-pending.json")
DELAY = 15         # s before showing the message: short turns do not need one
EVERY = 5          # s between edits
NO_PROGRESS = 600  # s without any hook event -> warning
MAX_LIFE = 4 * 3600

tg.write_json(os.path.join(tg.STATE, "daemon.json"), {"pid": os.getpid()})
CHAT = tg.chat_id()
SESSION = tg.tmux_session()
msg_id = None
prev = None
last_edit = 0
last_typing = 0
born = time.time()


def screen():
    try:
        return subprocess.run(["tmux", "capture-pane", "-p", "-t", SESSION], capture_output=True, text=True, timeout=5).stdout
    except Exception:
        return ""


def claude_running():
    return subprocess.run(["pgrep", "-u", str(os.getuid()), "-x", "claude"], capture_output=True).returncode == 0


def delete():
    if msg_id:
        tg.api("deleteMessage", chat_id=CHAT, message_id=msg_id)
        tg.log(f"status {msg_id} deleted after {tg.duration(time.time() - born)}")


while True:
    time.sleep(1)
    now = time.time()
    t = tg.read_json(TURN)
    if not t or t.get("end") or now - born > MAX_LIFE:
        delete()
        break
    if not claude_running():
        if msg_id:
            tg.api("editMessageText", chat_id=CHAT, message_id=msg_id,
                   text="⚠️ The assistant's session exited mid-task. The service starts it again; if it does not answer in a few minutes, check the server.")
        os.remove(TURN)
        break

    working = now - t["start"]
    if now - last_typing >= 4:
        tg.api("sendChatAction", chat_id=CHAT, action="typing")
        last_typing = now
    if working < DELAY:
        continue

    scr = screen()
    step = t.get("step", "thinking")
    p = tg.read_json(PENDING)
    if p and now - p.get("since", 0) < 900:
        text = f"⚠️ Stopped: waiting for your permission (sent to you with buttons)\n{p.get('what', '')}"
    elif "Do you want to proceed?" in scr:
        text = "⚠️ Stopped: waiting for permission in its terminal"
    elif "Model switch" in scr or "safeguards flagged" in scr:
        text = "⚠️ Stuck on a dialog in its terminal (model switch)."
    elif now - t.get("last_event", t["start"]) > NO_PROGRESS:
        text = f"⚠️ No progress for {tg.duration(now - t['last_event'])}: thinking hard, or stuck.\nLast step: {step}"
    else:
        text = f"⏳ Working · {tg.duration(working)}\nNow: {step} (for {tg.duration(now - t.get('step_since', t['start']))})"
    text = text[:900]

    if msg_id is None:
        r = tg.api("sendMessage", chat_id=CHAT, text=text, disable_notification="true")
        if r:
            msg_id = r["message_id"]
            prev, last_edit = text, now
            tg.log(f"status {msg_id} sent")
    elif text != prev and (now - last_edit >= EVERY or text.startswith("⚠️") != prev.startswith("⚠️")):
        tg.api("editMessageText", chat_id=CHAT, message_id=msg_id, text=text)
        prev, last_edit = text, now

try:
    os.remove(os.path.join(tg.STATE, "daemon.json"))
except OSError:
    pass
