"""One-time approvals: you allow from Telegram a call that the auto-mode classifier denied (denied-hook.py), and
approved-hook.py lets it through once when the assistant repeats exactly the same call within VALID seconds."""
import hashlib, json, os, time
import tg

DIR = os.path.join(tg.STATE, "approvals")
VALID = 300  # seconds to repeat the call after you tap Approve


def fingerprint(name, tool_input):
    tool_input = dict(tool_input or {})
    tool_input.pop("description", None)
    if name == "Bash":  # only the command counts, not the timeout or the description
        tool_input = {"command": tool_input.get("command", "")}
    return hashlib.sha256(json.dumps([name, tool_input], sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def save(name, tool_input):
    os.makedirs(DIR, mode=0o700, exist_ok=True)
    tg.write_json(os.path.join(DIR, fingerprint(name, tool_input)), {"until": time.time() + VALID, "name": name})


def consume(name, tool_input):
    """True if there was a valid approval for this exact call; it is used up either way."""
    path = os.path.join(DIR, fingerprint(name, tool_input))
    try:
        data = json.load(open(path))
        os.remove(path)
    except Exception:
        return False
    return data.get("until", 0) > time.time()
