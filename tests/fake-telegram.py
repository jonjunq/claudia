#!/usr/bin/env python3
"""Minimal stand-in for the Telegram Bot API, for the tests: answers every method with a message id and logs each
call (method + form fields as JSON) to the file given as the second argument. Prints its port on stdout."""
import json, sys, urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer

LOG = sys.argv[2]


class H(BaseHTTPRequestHandler):
    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("Content-Length", 0))).decode()
        fields = {k: v[0] for k, v in urllib.parse.parse_qs(body).items()}
        with open(LOG, "a") as f:
            f.write(json.dumps({"method": self.path.rsplit("/", 1)[-1], **fields}) + "\n")
        out = json.dumps({"ok": True, "result": {"message_id": 5}}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(out)

    def log_message(self, *a):
        pass


srv = HTTPServer(("127.0.0.1", int(sys.argv[1])), H)
print(srv.server_port, flush=True)
srv.serve_forever()
