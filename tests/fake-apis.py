#!/usr/bin/env python3
"""Stand-in for the APIs assistant-doctor and assistant-release-watch talk to, for the tests.
  fake-apis.py <port> <root dir> <log file>      prints its port on stdout
- Key checks (Groq /openai/..., Cloudflare /client/v4/..., ElevenLabs /v1/...): 200 if the Authorization or
  xi-api-key header contains "good", 401 otherwise.
- Any other GET: the file <root dir>/<path> (query string dropped) as JSON, or 404.
- POST /wake: appends "<Authorization> <body>" to <root dir>/wake.log (the local wake-up).
Every request's method and path (never its headers) goes to the log file, so a test can tell that nothing was asked."""
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT, LOG = sys.argv[2], sys.argv[3]


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def send(self, code, body=b"{}"):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        with open(LOG, "a") as f:
            f.write(f"GET {path}\n")
        if path.startswith(("/openai/", "/client/v4/", "/v1/")):
            auth = (self.headers.get("Authorization") or "") + (self.headers.get("xi-api-key") or "")
            return self.send(200 if "good" in auth else 401, b'{"success": true}')
        try:
            with open(os.path.join(ROOT, path.lstrip("/")), "rb") as f:
                return self.send(200, f.read())
        except OSError:
            return self.send(404)

    def do_POST(self):
        n = int(self.headers.get("content-length") or 0)
        body = self.rfile.read(n).decode()
        with open(LOG, "a") as f:
            f.write(f"POST {self.path}\n")
        if self.path == "/wake":
            with open(os.path.join(ROOT, "wake.log"), "a") as f:
                f.write((self.headers.get("Authorization") or "") + " " + body + "\n")
        self.send(200)


s = ThreadingHTTPServer(("127.0.0.1", int(sys.argv[1])), H)
s.daemon_threads = True
print(s.server_port, flush=True)
s.serve_forever()
