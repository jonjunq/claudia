#!/usr/bin/env python3
"""Minimal stand-in for the Telegram Bot API, for the tests: answers every method with a message id and logs each
call (method + form or JSON fields) to the file given as the second argument. Prints its port on stdout.
An optional third argument is a JSON scenario for tests that run the real plugin (tests/plugin-e2e.py):
  {"updates": [...]}            returned once by getUpdates (later calls wait a second and return nothing)
  {"file": "/path/to/audio"}    what getFile points to and GET /file/bot<token>/... serves
  {"hang_downloads": true}      file downloads never answer (to test the plugin's timeouts)
The scenario file is re-read on every request, so a test can change it between steps."""
import json, sys, time, urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

LOG = sys.argv[2]
SCENARIO = sys.argv[3] if len(sys.argv) > 3 else None
served = set()  # update_ids already returned


def scenario():
    if not SCENARIO:
        return {}
    try:
        return json.load(open(SCENARIO))
    except (OSError, ValueError):
        return {}


def log(entry):
    with open(LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")


class H(BaseHTTPRequestHandler):
    def reply(self, result):
        out = json.dumps({"ok": True, "result": result}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(out)))
        self.end_headers()
        self.wfile.write(out)

    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("Content-Length", 0))).decode()
        if self.headers.get("Content-Type", "").startswith("application/json"):
            try:
                fields = json.loads(body or "{}")
            except ValueError:
                fields = {}
        else:
            fields = {k: v[0] for k, v in urllib.parse.parse_qs(body).items()}
        method = self.path.rsplit("/", 1)[-1]
        if method != "getUpdates":
            log({"method": method, **fields})
        sc = scenario()
        if method == "getMe":
            return self.reply({"id": 1, "is_bot": True, "first_name": "Test", "username": "test_bot"})
        if method == "getUpdates":
            new = [u for u in sc.get("updates", []) if u["update_id"] not in served]
            if not new:
                time.sleep(1)
                return self.reply([])
            served.update(u["update_id"] for u in new)
            return self.reply(new)
        if method == "getFile":
            return self.reply({"file_id": fields.get("file_id", ""), "file_unique_id": "U1",
                               "file_path": "voice/file_1.oga"})
        if method in ("deleteWebhook", "setMyCommands", "sendChatAction", "setMessageReaction"):
            return self.reply(True)
        self.reply({"message_id": 5})

    def do_GET(self):
        sc = scenario()
        log({"method": "GET", "path": self.path.split("/file/bot", 1)[-1].split("/", 1)[-1]})
        if sc.get("hang_downloads"):
            time.sleep(120)
            return
        data = open(sc["file"], "rb").read() if sc.get("file") else b""
        self.send_response(200)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *a):
        pass


srv = ThreadingHTTPServer(("127.0.0.1", int(sys.argv[1])), H)
srv.daemon_threads = True
print(srv.server_port, flush=True)
srv.serve_forever()
