#!/usr/bin/env python3
"""A FAKE Claude Code terminal to test model-switch.py inside tmux (no model, no network).
It imitates what the script looks at: the input box (❯ between rules, the suggestion in grey), the status line
"[Name] ctx …", the work indicator "… (12s" and the menus of /model.
Usage: fake-claude-tui.py <dir>  - in <dir>: model (shown name), input (initial text), suggestion, busy (if it
exists, "working"), dialog (switch | none | odd); it writes keys.log."""
import os, select, sys, termios, tty

D = sys.argv[1]
NAMES = {"opus": "Opus 5.5", "sonnet": "Sonnet 5.5", "haiku": "Haiku 5.5", "claude-opus-4-8": "Opus 4.8",
         "claude-sonnet-5-5": "Sonnet 5.5"}


def get(n, default=""):
    try:
        return open(os.path.join(D, n)).read().strip()
    except OSError:
        return default


model = get("model", "Opus 5.5")
typed = get("input")
menu = None       # None | ("switch", id) | ("odd", id)
messages = ["● An earlier test answer."]


def paint():
    out = ["\x1b[2J\x1b[H"]
    out += [m + "\r\n" for m in messages[-4:]]
    if os.path.exists(os.path.join(D, "busy")):
        out.append("✻ Thinking… (12s · esc to interrupt)\r\n")
    out.append("─" * 60 + "\r\n")
    sug = get("suggestion")
    if typed:
        out.append("\x1b[39m❯\xa0" + typed + "\r\n")
    elif sug:
        out.append("\x1b[39m❯\xa0\x1b[2m" + sug + "\x1b[0m\r\n")
    else:
        out.append("\x1b[39m❯\xa0\r\n")
    out.append("─" * 60 + "\r\n")
    if menu and menu[0] == "switch":
        out += ["  Switch model?\r\n", "  Your next response will be slower and use more tokens\r\n",
                f"  \x1b[36m❯ 1. Yes, switch to {NAMES[menu[1]]}\x1b[0m\r\n", "    2. No, go back\r\n"]
    elif menu and menu[0] == "odd":
        out += [f"  {NAMES[menu[1]]} uses usage credits on your plan. Continue?\r\n",
                "  ❯ 1. Yes, use credits\r\n", "    2. No\r\n"]
    else:
        out.append(f"  [{model}] ctx 38% · 5h 7% · week 4%\r\n")
    sys.stdout.write("".join(out))
    sys.stdout.flush()


def apply(mid):
    global model
    model = NAMES[mid]
    messages.append(f"  ⎿  Set model to {model} and saved as your default for new sessions")


old = termios.tcgetattr(0)
tty.setraw(0)
try:
    last = None
    while True:
        state = (os.path.exists(os.path.join(D, "busy")), get("suggestion"))
        if state != last:
            paint()
            last = state
        r, _, _ = select.select([0], [], [], 0.2)
        if not r:
            continue
        data = os.read(0, 256).decode(errors="replace")
        with open(os.path.join(D, "keys.log"), "a") as f:
            f.write(repr(data) + "\n")
        for c in data:
            if c == "\x03":
                raise SystemExit
            if menu:
                if c == "\r":
                    apply(menu[1])  # also for "odd": if anyone accepts it, the test sees it
                    menu = None
                elif c == "\x1b":
                    menu = None
                continue
            if c == "\r":
                if typed.startswith("/model "):
                    mid = typed.split(" ", 1)[1].strip()
                    if mid not in NAMES:
                        messages.append(f"  ⎿  Invalid model: {mid}")
                    else:
                        d = get("dialog", "switch")
                        if d == "none":
                            apply(mid)
                        else:
                            menu = (d, mid)
                typed = ""
            elif c == "\x7f":
                typed = typed[:-1]
            elif c.isprintable():
                typed += c
        paint()
finally:
    termios.tcsetattr(0, termios.TCSADRAIN, old)
