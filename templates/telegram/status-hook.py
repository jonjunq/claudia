#!/usr/bin/env python3
"""PreToolUse / PostToolUse / Stop / StopFailure hook (async): records which step the assistant is on and starts
status-daemon.py, which keeps the "⏳ Working…" message on Telegram. It only writes a small file, so it is fast."""
import json, os, subprocess, sys, time
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import tg

hook = json.load(sys.stdin)
if not tg.is_assistant(hook):
    sys.exit(0)
event = hook.get("hook_event_name")
TURN = os.path.join(tg.STATE, "turn.json")
now = time.time()

if event in ("Stop", "StopFailure"):
    t = tg.read_json(TURN)
    if t:
        t["end"] = now
        tg.write_json(TURN, t)
    sys.exit(0)

t = tg.read_json(TURN) or {}
if not t or t.get("end"):
    t = {"start": now}
t["last_event"] = now
if event == "PreToolUse":
    name = hook.get("tool_name", "")
    if name.endswith("telegram__reply"):
        sys.exit(0)  # answering is not a step worth showing
    t["step"] = tg.describe(name, hook.get("tool_input"))
    t["step_since"] = now
tg.write_json(TURN, t)

if os.environ.get("ASSISTANT_TG_NO_DAEMON"):
    sys.exit(0)  # tests
pid = tg.read_json(os.path.join(tg.STATE, "daemon.json"), {}).get("pid")
alive = False
if pid:
    try:
        os.kill(pid, 0)
        alive = True
    except OSError:
        pass
if not alive:
    subprocess.Popen([sys.executable, "-I", os.path.join(os.path.dirname(os.path.realpath(__file__)), "status-daemon.py")],
                     stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
