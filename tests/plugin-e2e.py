#!/usr/bin/env python3
"""End-to-end check of patch-telegram-plugin.py against the REAL Telegram plugin, with a fake Bot API.
Not part of CI (it needs bun and a downloaded copy of the plugin): run it by hand after a plugin update.
  tests/plugin-e2e.py <plugin dir with node_modules, e.g. ~/.claude/plugins/cache/claude-plugins-official/telegram/0.0.7>
It copies the plugin to a temporary directory, applies the patch, points the copy at tests/fake-telegram.py, speaks
MCP to it over stdio like Claude Code does, and checks:
  1. a voice note from the allowlisted user arrives already transcribed (content = transcript, voice_transcribed_by);
  2. a voice note from a stranger is dropped before anything is downloaded;
  3. a download that hangs still delivers the normal notification (without transcript), after the timeouts;
  4. download_attachment with a hung download returns an error instead of hanging forever.
Steps 3 and 4 wait for the real timeouts: about 1.5 minutes in all."""
import json, os, shutil, subprocess, sys, tempfile, threading, time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
if len(sys.argv) != 2 or not os.path.isdir(os.path.join(sys.argv[1], "node_modules")):
    sys.exit(__doc__)
if not shutil.which("bun"):
    sys.exit("bun not found on PATH")

T = tempfile.mkdtemp(prefix="plugin-e2e-")
P = os.path.join(T, "plugin")
shutil.copytree(sys.argv[1], P, symlinks=True, ignore=shutil.ignore_patterns("server.ts.*"))
server = os.path.join(P, "server.ts")
orig = os.path.join(sys.argv[1], "server.ts.orig")
if os.path.exists(orig):  # a patched install: test against its unpatched copy
    shutil.copy(orig, server)
r = subprocess.run([sys.executable, "-I", os.path.join(REPO, "templates/telegram/patch-telegram-plugin.py")],
                   env={**os.environ, "TG_PLUGIN_GLOB": server}, capture_output=True, text=True)
print(r.stdout.strip())
if r.returncode:
    sys.exit("the patch does not fit this plugin")
# Test-only redirection of the Bot API and file downloads to the fake server.
src = open(server).read()
src = src.replace("new Bot(TOKEN)", "new Bot(TOKEN, { client: { apiRoot: process.env.TG_API_ROOT! } })", 1)
src = src.replace("https://api.telegram.org/file/bot", "${process.env.TG_API_ROOT}/file/bot")
open(server, "w").write(src)

state = os.path.join(T, "state"); os.makedirs(state)
json.dump({"dmPolicy": "allowlist", "allowFrom": ["42"], "groups": {}, "pending": {}}, open(os.path.join(state, "access.json"), "w"))
ws = os.path.join(T, "assistant"); os.makedirs(os.path.join(ws, "bin"))
fake_transcribe = os.path.join(ws, "bin", "transcribe.sh")
open(fake_transcribe, "w").write("#!/bin/sh\necho 'hello from the fake transcriber'\necho 'engine=fake 1ms' >&2\n")
os.chmod(fake_transcribe, 0o755)
audio = os.path.join(T, "note.oga"); open(audio, "wb").write(b"OggS fake audio")
sc_path = os.path.join(T, "scenario.json")
api_log = os.path.join(T, "api.log"); open(api_log, "w").close()


def set_scenario(**kw):
    json.dump({"file": audio, **kw}, open(sc_path, "w"))


def voice_update(uid, sender):
    return {"update_id": uid, "message": {
        "message_id": uid, "date": int(time.time()), "chat": {"id": sender, "type": "private"},
        "from": {"id": sender, "is_bot": False, "first_name": "U"},
        "voice": {"file_id": f"F{uid}", "file_unique_id": f"U{uid}", "duration": 3, "mime_type": "audio/ogg"}}}


set_scenario()
fake = subprocess.Popen([sys.executable, "-I", os.path.join(HERE, "fake-telegram.py"), "0", api_log, sc_path],
                        stdout=subprocess.PIPE, text=True)
port = fake.stdout.readline().strip()
env = {**os.environ, "TELEGRAM_BOT_TOKEN": "123:FAKE", "TELEGRAM_STATE_DIR": state, "ASSISTANT_DIR": ws,
       "TG_API_ROOT": f"http://127.0.0.1:{port}"}
plugin = subprocess.Popen(["bun", "server.ts"], cwd=P, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                          stderr=open(os.path.join(T, "plugin.err"), "w"), text=True)
inbox, replies = [], {}


def read():
    for line in plugin.stdout:
        try:
            m = json.loads(line)
        except ValueError:
            continue
        if m.get("method") == "notifications/claude/channel":
            inbox.append((time.time(), m["params"]))
        elif "id" in m:
            replies[m["id"]] = (time.time(), m)


threading.Thread(target=read, daemon=True).start()


def send(m):
    plugin.stdin.write(json.dumps(m) + "\n"); plugin.stdin.flush()


def wait(cond, secs):
    end = time.time() + secs
    while time.time() < end:
        if cond():
            return True
        time.sleep(0.1)
    return False


fails = 0
def check(name, ok):
    global fails
    print(("ok   " if ok else "FAIL ") + name)
    fails += not ok


send({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
    "protocolVersion": "2025-06-18", "capabilities": {"experimental": {"claude/channel": {}}},
    "clientInfo": {"name": "plugin-e2e", "version": "0"}}})
check("plugin answers initialize", wait(lambda: 1 in replies, 30))
send({"jsonrpc": "2.0", "method": "notifications/initialized"})

t = time.time(); set_scenario(updates=[voice_update(1, 42)])
check("1. voice note notification arrives", wait(lambda: len(inbox) >= 1, 30))
if inbox:
    meta = inbox[0][1]["meta"]
    check("1. content is the transcript", inbox[0][1]["content"] == "hello from the fake transcriber")
    check("1. tagged with the engine", meta.get("voice_transcribed_by") == "fake")
    check("1. audio saved at voice_path", os.path.exists(meta.get("voice_path", "")))
    check("1. attachment_file_id kept", meta.get("attachment_file_id") == "F1")
    print(f"     arrived {inbox[0][0] - t:.2f} s after the update was offered")

open(api_log, "w").close(); set_scenario(updates=[voice_update(2, 99)])
time.sleep(4)
check("2. stranger's note is not delivered", len(inbox) == 1)
check("2. nothing downloaded for the stranger", "getFile" not in open(api_log).read())

t = time.time(); set_scenario(updates=[voice_update(3, 42)], hang_downloads=True)
check("3. hung download: normal notification still arrives", wait(lambda: len(inbox) >= 2, 70))
if len(inbox) >= 2:
    check("3. without a transcript", "voice_transcribed_by" not in inbox[1][1]["meta"]
          and inbox[1][1]["content"] == "(voice message)")
    print(f"     after {inbox[1][0] - t:.1f} s")

t = time.time()
send({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
      "params": {"name": "download_attachment", "arguments": {"file_id": "F9"}}})
check("4. download_attachment with a hung download returns", wait(lambda: 2 in replies, 90))
if 2 in replies:
    check("4. as an error", replies[2][1].get("result", {}).get("isError") is True or "error" in replies[2][1])
    print(f"     after {replies[2][0] - t:.1f} s")

for line in open(os.path.join(state, "voice.log"), errors="replace") if os.path.exists(os.path.join(state, "voice.log")) else []:
    print("     voice.log: " + line.strip())
plugin.terminate(); fake.terminate()
plugin.wait(5); fake.wait(5)
shutil.rmtree(T, ignore_errors=True)
print(f"{'all passed' if not fails else f'{fails} failed'}")
sys.exit(1 if fails else 0)
