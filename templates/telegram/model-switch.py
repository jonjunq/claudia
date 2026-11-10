#!/usr/bin/env python3
"""Switches the assistant's model by typing `/model <model>` into its terminal (tmux), once it is free.
Started by the bot's /model (plugin patch v4) or by the assistant itself, as the LAST step of a turn:
  model-switch.py <model>            one of MODELS in ~/assistant/assistant.env (nothing else ever reaches tmux)
  model-switch.py --detach <model>   the same in the background, detached from the caller (what the assistant runs:
                                     it returns at once, and the switch waits until the assistant's turn is over)
1. Lock: if another switch is under way, it says so and stops.
2. If the status line already shows that exact model, it says so without typing anything.
3. It waits (up to MODEL_SWITCH_WAIT s, 30 min) until the assistant is free: no open turn, no permission waiting,
   no work indicator or menu on screen, and the input line in sight.
4. If the input line holds real text (not the grey suggestion), it touches nothing and says so.
5. It types `/model <model>` + Enter; if "Switch model?" comes up with "Yes" selected, Enter. Any other menu (a
   usage-credits consent, for instance) is NEVER accepted: Escape, and a notice.
6. Success = the status line shows the new model. Then it writes MODEL=<model> in assistant.env (start.sh reads it,
   so it stays after restarts) and tells the owner on Telegram.
Tests: MODEL_SWITCH_NO_TG=1 prints the notices instead of sending them; MODEL_SWITCH_WAIT and MODEL_SWITCH_STEP
change the timings; ASSISTANT_DIR and HOME move the workspace and the state, as for the other hooks (tg.py)."""
import fcntl, os, re, subprocess, sys, time
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import tg

DEFAULT_MODELS = "opus sonnet haiku"
VALID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9.\[\]-]{1,47}$")
WAIT = float(os.environ.get("MODEL_SWITCH_WAIT", 1800))
STEP = float(os.environ.get("MODEL_SWITCH_STEP", 3))
NO_TG = os.environ.get("MODEL_SWITCH_NO_TG") == "1"
TURN = os.path.join(tg.STATE, "turn.json")
PENDING = os.path.join(tg.STATE, "permission-pending.json")
ENV_FILE = os.path.join(tg.ASSISTANT_DIR, "assistant.env")
BUSY = re.compile(r"…\s*\([0-9]")  # "✻ Thinking… (12s · esc to interrupt)", as clear-context.sh looks for
MENUS = ("Do you want to proceed?", "Switch model?", "Model switch", "safeguards flagged")
ESC = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")
GREY = re.compile(r"\x1b\[2m.*?(?:\x1b\[(?:0|22)m|$)")


def models():
    """MODELS from assistant.env (aliases such as opus, or full ids), the ones /model offers. The plugin reads the same."""
    return [m for m in (tg.env().get("MODELS") or DEFAULT_MODELS).split() if VALID.match(m)]


def display(model):
    """What the status line shows for it, or its start: claude-opus-4-8 -> "Opus 4.8", opus -> "Opus"."""
    m = model.split("[")[0]
    if m.startswith("claude-"):
        parts = m[len("claude-"):].split("-")
        nums = [p for p in parts[1:] if p.isdigit() and len(p) <= 2]
        return parts[0].capitalize() + (" " + ".".join(nums) if nums else "")
    return m.capitalize()


def exact(model):
    return model.startswith("claude-")


def notify(text):
    tg.log("model: " + text)
    if NO_TG:
        print("NOTICE:", text, flush=True)
        return
    tg.api("sendMessage", chat_id=tg.chat_id(), text=text)


def pane(color=False):
    cmd = ["tmux", "capture-pane", "-p", "-t", tg.tmux_session()] + (["-e"] if color else [])
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=5).stdout
    except Exception:
        return ""


def keys(*args):
    subprocess.run(["tmux", "send-keys", "-t", tg.tmux_session(), *args], timeout=5, check=True)


def on_status_line(text):
    """The model on statusline.sh's line: "[Opus 5.5] ctx 38% · …"."""
    m = re.findall(r"^\s*\[([^\]\n]+)\] ctx ", text, re.M)
    return m[-1].strip() if m else None


def is_on(name, text, before=None):
    """Already on that model? By the status line or, if there is a new "Set model to …" line, by it."""
    bar = on_status_line(text)
    if bar and bar.startswith(name):
        return True
    if before is not None and text.count("Set model to") > before:
        m = re.findall(r"Set model to (.+?)(?: and |\n|$)", text)
        return bool(m) and m[-1].strip().startswith(name)
    return False


def input_line(colored):
    """What is really on the input line (without the grey suggestion), or None if the box is not in sight. The box
    is a line starting with ❯ in column 0 right below a ─ rule."""
    lines = colored.split("\n")
    for i in range(len(lines) - 1, 0, -1):
        plain = ESC.sub("", lines[i])
        if plain.startswith("❯") and ESC.sub("", lines[i - 1]).lstrip().startswith("─"):
            return ESC.sub("", GREY.sub("", lines[i])).replace("❯", "", 1).replace("\xa0", " ").strip()
    return None


def busy():
    """Why it cannot type now, or None if the assistant is free."""
    now = time.time()
    t = tg.read_json(TURN) or {}
    if t.get("start") and not t.get("end") and now - t.get("last_event", t["start"]) < 600:
        return "working"
    p = tg.read_json(PENDING) or {}
    if p and now - p.get("since", 0) < 900:
        return "waiting for a permission"
    text = pane()
    if BUSY.search(text):
        return "working"
    for m in MENUS:
        if m in text:
            return f"a menu is open ({m})"
    if input_line(pane(color=True)) is None:
        return "no input line in sight"
    return None


def save(model):
    """MODEL=<model> in assistant.env, the rest of the file as it was."""
    try:
        lines = open(ENV_FILE).read().split("\n")
    except OSError:
        lines = []
    if f"MODEL={model}" in lines:
        return
    new = [f"MODEL={model}" if re.match(r"^MODEL=", ln) else ln for ln in lines]
    if new == lines:
        new = lines[:-1] + [f"MODEL={model}", ""] if lines and lines[-1] == "" else lines + [f"MODEL={model}"]
    tmp = ENV_FILE + ".tmp"
    with open(tmp, "w") as f:
        f.write("\n".join(new))
    if os.path.exists(ENV_FILE):
        os.chmod(tmp, os.stat(ENV_FILE).st_mode & 0o777)
    os.replace(tmp, ENV_FILE)
    tg.log(f"model: saved MODEL={model} in assistant.env")


def detach():
    """Double fork: the switch outlives the caller's process group (a Bash tool call ends with the turn)."""
    if os.fork():
        return True
    os.setsid()
    if os.fork():
        os._exit(0)
    fd = os.open(os.devnull, os.O_RDWR)
    for n in (0, 1, 2):
        os.dup2(fd, n)
    return False


def main():
    allowed = models()
    args = sys.argv[1:]
    background = args[:1] == ["--detach"]
    if background:
        args = args[1:]
    if len(args) != 1 or args[0] not in allowed:
        print("usage: model-switch.py [--detach] <model>, one of: " + " ".join(allowed), file=sys.stderr)
        return 2
    model = args[0]
    name = display(model)
    if background and detach():
        print(f"switching to {name} once this turn is over; the owner gets the notice")
        return 0

    lock = open(os.path.join(tg.STATE, "model-switch.lock"), "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        notify(f"Another model switch is under way; I am not switching to {name}. Send /model again after its notice.")
        return 1
    tg.log(f"model: asked for {model}")

    if exact(model) and is_on(name, pane()):
        save(model)
        notify(f"It was already on {name}; nothing changed.")
        return 0

    end = time.time() + WAIT
    free_in_a_row = 0
    while True:
        why = busy()
        free_in_a_row = 0 if why else free_in_a_row + 1
        if free_in_a_row >= 2:  # free on two checks in a row (not just as a message comes in)
            break
        if time.time() > end:
            notify(f"I did not switch to {name}: it has been busy for {round(WAIT / 60)} min ({why}). Send /model again when it is done.")
            return 1
        time.sleep(STEP)

    typed = input_line(pane(color=True))
    if typed:
        notify(f"I did not switch to {name}: there is half-written text in its terminal and I will not overwrite it.")
        tg.log(f"model: input line holds text ({len(typed)} chars)")
        return 1
    if exact(model) and is_on(name, pane()):  # it may have switched while waiting
        save(model)
        notify(f"It was already on {name}; nothing changed.")
        return 0

    before = pane().count("Set model to")
    bar_before = on_status_line(pane())

    def switched(text):
        """On it now, by its exact name, a new "Set model to" line or a status line that changed to it."""
        return is_on(name, text, before) and (exact(model) or text.count("Set model to") > before
                                              or on_status_line(text) != bar_before)

    keys("-l", f"/model {model}")
    time.sleep(1)
    keys("Enter")
    confirmed = False
    limit = time.time() + 20
    while time.time() < limit:
        time.sleep(0.5)
        text = pane()
        if switched(text) and "Switch model?" not in text:
            save(model)
            notify(f"✅ Now on {on_status_line(text) or name} (it stays so after restarts too).")
            return 0
        if "Switch model?" in text and not confirmed:
            marked = [ln for ln in text.split("\n") if ln.lstrip().startswith("❯") and not ln.startswith("❯")]
            if marked and re.match(r"\s*❯\s*1\.\s*Yes\b", marked[-1]):
                keys("Enter")
                confirmed = True
                continue
            break
        if not confirmed and "Switch model?" not in text and text.count("Set model to") == before:
            # Another menu (a consent, an error)? An unknown menu is never accepted.
            if any(re.match(r"\s+❯\s*\d+\.", ln) for ln in text.split("\n")) or "Invalid model" in text:
                break
    # It did not happen: close whatever menu is open, and say so.
    keys("Escape")
    time.sleep(1)
    if switched(pane()):  # switched, but something else stayed open
        save(model)
        notify(f"✅ Now on {on_status_line(pane()) or name} (it stays so after restarts too).")
        return 0
    if not exact(model) and bar_before and bar_before.startswith(name) and is_on(name, pane()):
        save(model)  # an alias it was already on: Claude Code had nothing to change
        notify(f"It was already on {bar_before}; nothing changed.")
        return 0
    rest = [ln.strip() for ln in pane().split("\n") if ln.strip()][-8:]
    tg.log("model: failed; pane: " + " | ".join(rest)[:600])
    notify(f"⚠️ I could not switch to {name}; it is still on {on_status_line(pane()) or '?'}. Its terminal showed "
           "something I do not accept on my own (a usage-credits notice, for instance): open the terminal to look.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
