#!/usr/bin/env python3
"""PreToolUse / PostToolUse / Stop / StopFailure hook (async): records which step the assistant is on and starts
status-daemon.py, which keeps the "⏳ Working…" message on Telegram. It only writes a small file, so it is fast.

Only real turns count. Claude Code also runs background work in the same session (for example while it prepares
the suggested reply) that fires these hooks but never reaches the transcript. Without the filter that work opened
a phantom turn right after Stop and "⏳ Working" stayed on Telegram until the next real turn ended."""
import json, os, subprocess, sys, time
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import tg

hook = json.load(sys.stdin)
if not tg.is_assistant(hook):
    sys.exit(0)
event = hook.get("hook_event_name")
prompt = hook.get("prompt_id")
TURN = os.path.join(tg.STATE, "turn.json")
now = time.time()


def in_transcript(pid):
    """Is this prompt written in the real conversation? Background runs are not."""
    path = hook.get("transcript_path")
    if not pid or not path:
        return True  # nothing to check against: keep the old behaviour
    needle = f'"promptId":"{pid}"'.encode()
    try:
        with open(path, "rb") as f:
            f.seek(0, 2)
            f.seek(max(0, f.tell() - 2_000_000))
            return needle in f.read()
    except OSError:
        return True


if event in ("Stop", "StopFailure"):
    t = tg.read_json(TURN)
    if t and not t.get("end") and (not prompt or not t.get("prompt") or t["prompt"] == prompt or in_transcript(prompt)):
        t["end"] = now
        tg.write_json(TURN, t)
    sys.exit(0)

t = tg.read_json(TURN) or {}
if not t or t.get("end"):
    if prompt and prompt == t.get("prompt"):
        sys.exit(0)  # late event from a turn that already ended
    if not in_transcript(prompt):
        tg.log(f"ignored {event} {hook.get('tool_name')}: prompt {prompt} is not in the conversation")
        sys.exit(0)
    t = {"start": now, "prompt": prompt}
elif prompt and t.get("prompt") and prompt != t["prompt"] and not in_transcript(prompt):
    sys.exit(0)  # background run while a real turn is open
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
