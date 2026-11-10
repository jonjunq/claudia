#!/usr/bin/env python3
"""model-switch.py against a FAKE Claude Code terminal (tests/fake-claude-tui.py) in tmux sessions of its own:
no model, no Telegram, nothing of a real assistant is touched. Run by tests/run-tests.sh when tmux is there.
  python3 -I tests/model-switch-test.py"""
import json, os, shutil, subprocess, sys, tempfile, time

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(os.path.dirname(HERE), "templates", "telegram", "model-switch.py")
FAKE = os.path.join(HERE, "fake-claude-tui.py")
fails = 0


def check(name, cond, extra=""):
    global fails
    print(("ok   " if cond else "FAIL ") + "model-switch: " + name + (f"  [{extra[-500:]}]" if extra and not cond else ""), flush=True)
    fails += not cond


class Case:
    n = 0

    def __init__(self, model="Opus 5.5", typed="", suggestion="Yes, do the summary", dialog="switch", busy=False):
        Case.n += 1
        self.d = tempfile.mkdtemp(prefix="model-switch-")
        self.term, self.home, self.ws = (os.path.join(self.d, x) for x in ("term", "home", "assistant"))
        self.state = os.path.join(self.home, ".cache", "assistant-telegram")
        for x in (self.term, self.state, self.ws):
            os.makedirs(x)
        for k, v in (("model", model), ("input", typed), ("suggestion", suggestion), ("dialog", dialog)):
            open(os.path.join(self.term, k), "w").write(v)
        if busy:
            open(os.path.join(self.term, "busy"), "w").close()
        self.session = f"model-switch-test-{os.getpid()}-{Case.n}"
        open(os.path.join(self.ws, "assistant.env"), "w").write(
            f"# test\nMODEL=opus\nMODELS=\"opus sonnet haiku claude-opus-4-8\"\nTMUX_SESSION={self.session}\n")
        subprocess.run(["tmux", "new-session", "-d", "-s", self.session, "-x", "120", "-y", "30",
                        sys.executable, "-I", FAKE, self.term], check=True)
        time.sleep(0.8)
        self.env = dict(os.environ, HOME=self.home, ASSISTANT_DIR=self.ws, MODEL_SWITCH_NO_TG="1",
                        MODEL_SWITCH_WAIT="20", MODEL_SWITCH_STEP="0.5")

    def run(self, *args, wait=None):
        env = dict(self.env, **({"MODEL_SWITCH_WAIT": str(wait)} if wait is not None else {}))
        return subprocess.run([sys.executable, "-I", SCRIPT, *args], env=env, capture_output=True, text=True, timeout=90)

    def start(self, *args):
        return subprocess.Popen([sys.executable, "-I", SCRIPT, *args], env=self.env, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, text=True)

    def keys(self):
        try:
            return open(os.path.join(self.term, "keys.log")).read()
        except OSError:
            return ""

    def screen(self):
        return subprocess.run(["tmux", "capture-pane", "-p", "-t", self.session], capture_output=True, text=True).stdout

    def saved(self):
        return [ln for ln in open(os.path.join(self.ws, "assistant.env")).read().split("\n") if ln.startswith("MODEL=")]

    def close(self):
        subprocess.run(["tmux", "kill-session", "-t", self.session], capture_output=True)
        shutil.rmtree(self.d, ignore_errors=True)


# 1. not in MODELS: types nothing
c = Case()
r = c.run("opus; rm -rf ~")
check("a model outside MODELS: error, nothing typed", r.returncode == 2 and c.keys() == "", r.stdout + r.stderr)
r = c.run()
check("no argument: error", r.returncode == 2)
c.close()

# 2. already on that exact model: says so without typing
c = Case(model="Opus 4.8")
r = c.run("claude-opus-4-8")
check("already on it: says so, types nothing", r.returncode == 0 and "already on Opus 4.8" in r.stdout and c.keys() == "", r.stdout + c.keys())
c.close()

# 3. free, with a grey suggestion and the "Switch model?" dialog: switches, confirms and saves
c = Case(model="Opus 4.8")
r = c.run("sonnet")
check("switch with the dialog: success", r.returncode == 0 and "Now on Sonnet 5.5" in r.stdout, r.stdout + r.stderr + c.screen())
check("switch: typed /model with the model", "/model sonnet" in c.keys(), c.keys())
check("switch: the status line shows the new one", "[Sonnet 5.5] ctx" in c.screen())
check("switch: MODEL=sonnet in assistant.env, the rest kept", c.saved() == ["MODEL=sonnet"]
      and "TMUX_SESSION=" in open(os.path.join(c.ws, "assistant.env")).read(), str(c.saved()))
check("switch: logged", "model: saved MODEL=sonnet" in open(os.path.join(c.state, "log")).read())
c.close()

# 3b. without the dialog: switches straight away
c = Case(model="Opus 4.8", dialog="none", suggestion="")
r = c.run("opus")
check("switch without the dialog: success", r.returncode == 0 and "Now on Opus 5.5" in r.stdout and c.saved() == ["MODEL=opus"], r.stdout + r.stderr)
c.close()

# 3c. an alias it is already on: no failure notice
c = Case(model="Haiku 5.5", dialog="none")
r = c.run("haiku")
check("an alias it is already on: fine, saved", r.returncode == 0 and c.saved() == ["MODEL=haiku"] and "could not" not in r.stdout, r.stdout + r.stderr)
c.close()

# 4. real text on the input line: not overwritten
c = Case(model="Opus 4.8", typed="hello someone wrote this")
r = c.run("opus")
check("real text on the input line: nothing typed, it says so", r.returncode == 1 and "half-written text" in r.stdout and c.keys() == "", r.stdout + c.keys())
check("real text: nothing saved", c.saved() == ["MODEL=opus"] and "[Opus 4.8] ctx" in c.screen())
c.close()

# 5. busy for a while (screen + open turn): waits, then switches
c = Case(model="Opus 4.8", busy=True)
json.dump({"start": time.time() - 30, "last_event": time.time()}, open(os.path.join(c.state, "turn.json"), "w"))
p = c.start("haiku")
time.sleep(3)
check("busy: nothing typed while it works", c.keys() == "", c.keys())
os.remove(os.path.join(c.term, "busy"))
time.sleep(2)
check("open turn: still nothing typed though the screen no longer shows work", c.keys() == "", c.keys())
t = json.load(open(os.path.join(c.state, "turn.json"))); t["end"] = time.time()
json.dump(t, open(os.path.join(c.state, "turn.json"), "w"))
out, err = p.communicate(timeout=60)
check("busy: switches once free", p.returncode == 0 and "Now on Haiku 5.5" in out and c.saved() == ["MODEL=haiku"], out + err)
c.close()

# 6. busy the whole time: gives up without typing
c = Case(model="Opus 4.8", busy=True)
r = c.run("opus", wait=3)
check("always busy: gives up, says so, types nothing", r.returncode == 1 and "busy" in r.stdout and "(working)" in r.stdout and c.keys() == "", r.stdout)
c.close()

# 6b. a permission waiting: waits too
c = Case(model="Opus 4.8")
json.dump({"since": time.time(), "what": "Bash"}, open(os.path.join(c.state, "permission-pending.json"), "w"))
r = c.run("opus", wait=2)
check("a permission waiting: nothing typed", r.returncode == 1 and "waiting for a permission" in r.stdout and c.keys() == "", r.stdout)
c.close()

# 7. an unknown menu (a usage-credits consent): NOT accepted, Escape and a notice
c = Case(model="Opus 5.5", dialog="odd")
r = c.run("claude-opus-4-8")
check("unknown menu: not accepted, it says so", r.returncode == 1 and "could not switch to Opus 4.8" in r.stdout and "still on Opus 5.5" in r.stdout, r.stdout + r.stderr)
check("unknown menu: Escape sent, no extra Enter", "'\\x1b'" in c.keys() and c.keys().count("'\\r'") == 1, c.keys())
check("unknown menu: nothing saved", c.saved() == ["MODEL=opus"] and "[Opus 5.5] ctx" in c.screen())
c.close()

# 8. lock: a second switch at the same time is refused
c = Case(model="Opus 4.8", busy=True)
p = c.start("opus")
time.sleep(1.5)
r = c.run("sonnet")
check("lock: the second switch is refused", r.returncode == 1 and "Another model switch is under way" in r.stdout, r.stdout)
os.remove(os.path.join(c.term, "busy"))
out, err = p.communicate(timeout=60)
check("lock: the first one ends well", p.returncode == 0 and c.saved() == ["MODEL=opus"], out + err)
c.close()

# 9. --detach: returns at once, and the switch still happens
c = Case(model="Opus 4.8")
t0 = time.time(); r = c.run("--detach", "sonnet")
check("--detach returns at once", r.returncode == 0 and time.time() - t0 < 3 and "switching to Sonnet" in r.stdout, r.stdout + r.stderr)
end = time.time() + 30
while time.time() < end and c.saved() != ["MODEL=sonnet"]:
    time.sleep(0.5)
check("--detach: the switch happens in the background", c.saved() == ["MODEL=sonnet"] and "[Sonnet 5.5] ctx" in c.screen(), str(c.saved()))
r = c.run("--detach", "nope")
check("--detach with a model outside MODELS: error, nothing started", r.returncode == 2)
c.close()

print(f"model-switch: {'all passed' if not fails else f'{fails} failed'}")
sys.exit(1 if fails else 0)
