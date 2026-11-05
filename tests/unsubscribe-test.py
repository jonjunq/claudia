#!/usr/bin/env python3
"""Offline checks for templates/tools/unsubscribe.py: which emails it unsubscribes from, and what it sends.
No network: DNS answers and the HTTP opener are fakes. Prints one "ok"/"FAIL" line per check, exits 1 on a failure."""
import email
import email.policy
import importlib.util
import io
import os
import socket
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
TOOL = os.path.join(HERE, "..", "templates", "tools", "unsubscribe.py")
spec = importlib.util.spec_from_file_location("unsubscribe", TOOL)
u = importlib.util.module_from_spec(spec)
spec.loader.exec_module(u)

fails = 0


def check(name, cond):
    global fails
    print(("ok   " if cond else "FAIL ") + name)
    fails += 0 if cond else 1


def mail(frm="News <news@shop.example>", lu="<mailto:u@shop.example>, <https://lists.shop.example/u?id=1>",
         lup="List-Unsubscribe=One-Click", ar="mx.provider.example; dkim=pass header.i=@shop.example header.s=s1",
         sig="v=1; a=rsa-sha256; d=shop.example; s=s1;\r\n h=from:to:subject:list-unsubscribe:list-unsubscribe-post; b=xx",
         extra=""):
    h = [f"From: {frm}", "To: owner@example.org", "Subject: Offers"]
    if ar is not None:
        h.insert(0, f"Authentication-Results: {ar}")
    if sig is not None:
        h.append(f"DKIM-Signature: {sig}")
    if lu is not None:
        h.append(f"List-Unsubscribe: {lu}")
    if lup is not None:
        h.append(f"List-Unsubscribe-Post: {lup}")
    raw = "\r\n".join(h) + "\r\n" + extra + "\r\nHello\r\n"
    return email.message_from_bytes(raw.encode(), policy=email.policy.default), raw


def public(host, port, proto=0):
    return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.215.14", port))]


def private(host, port, proto=0):
    return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.0.0.5", port))]


class Resp:
    def __init__(self, status):
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class Opener:
    def __init__(self, status=200):
        self.status, self.reqs = status, []

    def open(self, req, timeout=None):
        self.reqs.append(req)
        return Resp(self.status)


m, _ = mail()
check("picks the https link, not the mailto", u.one_click_url(m)[0] == "https://lists.shop.example/u?id=1")
op = Opener()
good, line = u.handle(m, "news@shop.example", False, op, public)
check("unsubscribes a signed one-click email", good and line.startswith("unsubscribed") and len(op.reqs) == 1)
r = op.reqs[0] if op.reqs else None
check("sends exactly the RFC 8058 POST", r is not None and r.get_method() == "POST"
      and r.data == b"List-Unsubscribe=One-Click"
      and r.get_header("Content-type") == "application/x-www-form-urlencoded")

op = Opener()
good, line = u.handle(m, "x", True, op, public)
check("dry run sends nothing", good and line.startswith("would unsubscribe") and not op.reqs)

for name, kw, want in [
    ("skips without List-Unsubscribe-Post (no one-click)", {"lup": None}, "no one-click"),
    ("skips a mailto-only header", {"lu": "<mailto:u@shop.example>"}, "not https"),
    ("skips an http link", {"lu": "<http://lists.shop.example/u>"}, "not https"),
    ("skips without dkim=pass", {"ar": "mx.provider.example; dkim=fail header.i=@shop.example"}, "not signed"),
    ("skips a signature from another domain", {"ar": "mx.provider.example; dkim=pass header.i=@other.example",
                                                "sig": "v=1; d=other.example; h=from:list-unsubscribe:list-unsubscribe-post"},
     "not signed"),
    ("skips a signature that does not cover the headers", {"sig": "v=1; d=shop.example; h=from:to:subject"}, "not signed"),
    ("skips without Authentication-Results", {"ar": None}, "not signed"),
]:
    msg, _ = mail(**kw)
    op = Opener()
    good, line = u.handle(msg, "x", False, op, public)
    check(name, good and line.startswith("skipped") and want in line and not op.reqs)

# A forged pass lower down does not count: only the top header is the owner's provider.
msg, _ = mail(ar="mx.provider.example; dkim=fail header.i=@shop.example",
              extra="Authentication-Results: forged.example; dkim=pass header.i=@shop.example\r\n")
check("ignores a forged Authentication-Results below the provider's", not u.signed_by_sender(msg))

msg, _ = mail(frm="news@mail.shop.example")
check("accepts a subdomain of the signing domain (relaxed alignment)", u.signed_by_sender(msg))

op = Opener()
good, line = u.handle(m, "x", False, op, private)
check("never posts to a private address", good and "not a public address" in line and not op.reqs)

good, line = u.handle(m, "x", False, Opener(500), public)
check("reports an HTTP error as an error", not good and "HTTP 500" in line)

# The command line, with a saved email and --dry-run (no IMAP, no network: DNS is the only lookup and it may fail
# offline, which is a skip, not an error).
with tempfile.TemporaryDirectory() as d:
    p = os.path.join(d, "m.eml")
    with open(p, "w") as f:
        f.write(mail()[1])
    out = subprocess.run([sys.executable, "-I", TOOL, "--dry-run", "--eml", p], capture_output=True, text=True)
    check("command line with --eml --dry-run exits 0 and says what it would do",
          out.returncode == 0 and ("would unsubscribe" in out.stdout or "not a public address" in out.stdout))
    out = subprocess.run([sys.executable, "-I", TOOL], capture_output=True, text=True)
    check("command line without senders refuses", out.returncode != 0)

# folders(): special-use flags, whatever the mailbox language
class FakeIMAP:
    def list(self):
        return "OK", [b'(\\HasNoChildren) "/" "INBOX"', b'(\\All \\HasNoChildren) "/" "[Gmail]/Todos"',
                      b'(\\HasNoChildren \\Trash) "/" "[Gmail]/Papelera"']


check("finds all-mail and trash by their flags", u.folders(FakeIMAP()) == ['"[Gmail]/Todos"', '"[Gmail]/Papelera"'])
sys.exit(1 if fails else 0)
