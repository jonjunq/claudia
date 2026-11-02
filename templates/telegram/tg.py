"""Shared helpers for the Telegram hooks: the plugin's bot, the owner's chat and a state folder.
Settings come from ~/assistant/assistant.env (TMUX_SESSION, TELEGRAM_CHAT_ID), like the shell scripts."""
import json, os, time, urllib.parse, urllib.request

HOME = os.path.expanduser("~")
ASSISTANT_DIR = os.path.realpath(os.environ.get("ASSISTANT_DIR", os.path.join(HOME, "assistant")))
TG_DIR = os.environ.get("TELEGRAM_STATE_DIR", os.path.join(HOME, ".claude/channels/telegram"))
STATE = os.path.join(HOME, ".cache/assistant-telegram")
VERDICTS = os.path.join(TG_DIR, "verdicts")
API = os.environ.get("TELEGRAM_API", "https://api.telegram.org")
os.makedirs(STATE, mode=0o700, exist_ok=True)


def env():
    """KEY=VALUE pairs from assistant.env (plain shell file, no expansion needed for the keys we read)."""
    out = {}
    try:
        for line in open(os.path.join(ASSISTANT_DIR, "assistant.env")):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                out[k.strip()] = v.strip().strip("\"'")
    except OSError:
        pass
    return out


def token():
    for line in open(os.path.join(TG_DIR, ".env")):
        if line.startswith("TELEGRAM_BOT_TOKEN="):
            return line.split("=", 1)[1].strip().strip("\"'")
    raise SystemExit("no TELEGRAM_BOT_TOKEN")


def chat_id():
    """TELEGRAM_CHAT_ID from assistant.env, or the first sender in the plugin's allowlist (you, after pairing)."""
    return env().get("TELEGRAM_CHAT_ID") or json.load(open(os.path.join(TG_DIR, "access.json")))["allowFrom"][0]


def tmux_session():
    return env().get("TMUX_SESSION") or "assistant"


def api(method, **params):
    """Bot API call. sendMessage/editMessageText do not interfere with the plugin's getUpdates polling."""
    data = {k: (json.dumps(v) if isinstance(v, (dict, list)) else str(v)) for k, v in params.items() if v is not None}
    req = urllib.request.Request(f"{API}/bot{token()}/{method}", data=urllib.parse.urlencode(data).encode())
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.load(r).get("result")
    except Exception as e:
        log(f"api {method}: {e}")
        return None


def log(text):
    with open(os.path.join(STATE, "log"), "a") as f:
        f.write(time.strftime("%Y-%m-%d %H:%M:%S ") + text + "\n")


def is_assistant(hook):
    """Hooks in ~/.claude/settings.json run for every Claude Code session of this user: act only in the assistant's."""
    cwd = os.path.realpath(hook.get("cwd") or "")
    return cwd == ASSISTANT_DIR or cwd.startswith(ASSISTANT_DIR + os.sep)


def read_json(path, default=None):
    try:
        return json.load(open(path))
    except Exception:
        return default


def write_json(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f)
    os.replace(tmp, path)


def describe(name, tool_input):
    """A short phrase for what a tool call does. Bash calls carry the model's own description."""
    tool_input = tool_input or {}
    if tool_input.get("description"):
        return str(tool_input["description"])
    if name.startswith("mcp__"):
        parts = name.split("__")
        return f"{parts[1].replace('claude_ai_', '').replace('_', ' ')} · {parts[-1].replace('_', ' ')}"
    for key in ("file_path", "path", "pattern", "url", "query", "skill"):
        if tool_input.get(key):
            return f"{name} · {tool_input[key]}"
    return name


def duration(s):
    s = int(s)
    if s < 60:
        return f"{s} s"
    return f"{s // 60} min {s % 60:02d} s" if s < 3600 else f"{s // 3600} h {s % 3600 // 60:02d} min"
