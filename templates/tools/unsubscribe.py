#!/usr/bin/env python3
"""Unsubscribe from mailing lists with the one-click link the emails themselves carry (RFC 8058).

    python3 -I unsubscribe.py [--dry-run] sender@example.com [sender2@example.org ...]
    python3 -I unsubscribe.py [--dry-run] --eml message.eml [...]

For each sender it finds the latest email over IMAP (read-only: nothing is marked as read or moved) and sends the
one-click unsubscribe POST only when all of this holds:
- the email has a List-Unsubscribe header with an https URL and "List-Unsubscribe-Post: List-Unsubscribe=One-Click"
  (what big senders must offer since 2024);
- the owner's own mail provider recorded dkim=pass for a domain aligned with the From address, and that DKIM
  signature covers both List-Unsubscribe headers (RFC 8058 asks for this; it is what stops a forged email from
  steering the POST somewhere else);
- the URL's host is a public address (never the home network or this machine), and no redirect is followed.
It never uses the mailto: variant (that is sending an email on the owner's behalf: ask first) and never follows a
link from the body (it may be phishing). An unsubscribe tells the sender the address is alive: use it for shops and
newsletters the owner recognises, not for spam (report that instead).

Credentials: ~/.config/assistant/mail.env (mode 600) with IMAP_HOST, IMAP_USER and IMAP_PASSWORD; for Gmail,
IMAP_HOST=imap.gmail.com and an app password (needs 2-step verification, revocable at any time). Override the path
with MAIL_ENV. Exit status: 0 if every sender was unsubscribed or skipped with a reason, 1 on an error.
"""
import argparse
import email
import email.policy
import imaplib
import ipaddress
import os
import re
import socket
import sys
import urllib.error
import urllib.parse
import urllib.request

ENV = os.environ.get("MAIL_ENV", os.path.expanduser("~/.config/assistant/mail.env"))
UA = "assistant-unsubscribe/1 (RFC 8058 one-click)"


def domain_of(addr):
    m = re.search(r"@([A-Za-z0-9.-]+)", addr or "")
    return m.group(1).lower().rstrip(".") if m else ""


def aligned(a, b):
    """Relaxed DMARC-style alignment: same domain, or one is a subdomain of the other."""
    return bool(a and b) and (a == b or a.endswith("." + b) or b.endswith("." + a))


def one_click_url(msg):
    """Return (url, None) if the email offers RFC 8058 one-click unsubscription, else (None, reason)."""
    post = str(msg.get("List-Unsubscribe-Post", "")).strip().lower().replace(" ", "")
    if post != "list-unsubscribe=one-click":
        return None, "no one-click unsubscribe (only a link or an email; the owner can use the mail app's button)"
    urls = re.findall(r"<([^>]+)>", str(msg.get("List-Unsubscribe", "")))
    https = [u.strip() for u in urls if u.strip().lower().startswith("https://")]
    if not https:
        return None, "the one-click link is not https"
    return https[0], None


def signed_by_sender(msg):
    """True if the receiving provider saw dkim=pass for a domain aligned with From, whose signature covers both
    List-Unsubscribe headers. Only the first Authentication-Results header counts: it is the one the owner's own
    provider adds on top; anything below it came with the email and could be forged."""
    frm = domain_of(str(msg.get("From", "")))
    results = msg.get_all("Authentication-Results") or []
    if not frm or not results:
        return False
    passed = set()
    for m in re.finditer(r"dkim=pass\b([^;]*)", str(results[0]), re.I):
        d = re.search(r"header\.[id]=@?([A-Za-z0-9.-]+)", m.group(1), re.I)
        if d:
            passed.add(d.group(1).lower().rstrip("."))
    for sig in msg.get_all("DKIM-Signature") or []:
        tags = {k.strip().lower(): v.strip() for k, _, v in
                (t.partition("=") for t in re.sub(r"\s+", "", str(sig)).split(";") if "=" in t)}
        d = tags.get("d", "").lower().rstrip(".")
        signed = {h.lower() for h in tags.get("h", "").split(":")}
        if d in passed and aligned(d, frm) and {"list-unsubscribe", "list-unsubscribe-post"} <= signed:
            return True
    return False


def public_host(url, resolve=socket.getaddrinfo):
    host = urllib.parse.urlsplit(url).hostname
    if not host:
        return False
    try:
        addrs = {a[4][0] for a in resolve(host, 443, proto=socket.IPPROTO_TCP)}
    except OSError:
        return False
    return bool(addrs) and all(ipaddress.ip_address(a.split("%")[0]).is_global for a in addrs)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def post(url, opener=None):
    req = urllib.request.Request(url, data=b"List-Unsubscribe=One-Click", method="POST", headers={
        "Content-Type": "application/x-www-form-urlencoded", "User-Agent": UA})
    opener = opener or urllib.request.build_opener(NoRedirect)
    try:
        with opener.open(req, timeout=20) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code


def handle(msg, who, dry_run, opener=None, resolve=socket.getaddrinfo):
    """One email: returns (ok, line). ok is False only for errors, not for skips."""
    url, why = one_click_url(msg)
    if not url:
        return True, f"skipped {who}: {why}"
    if not signed_by_sender(msg):
        return True, f"skipped {who}: the unsubscribe headers are not signed by the sender's domain (could be forged)"
    host = urllib.parse.urlsplit(url).hostname
    if not public_host(url, resolve):
        return True, f"skipped {who}: {host} is not a public address"
    if dry_run:
        return True, f"would unsubscribe {who} via {host}"
    try:
        status = post(url, opener)
    except OSError as e:
        return False, f"error {who}: {host} did not answer ({e})"
    if 200 <= status < 300:
        return True, f"unsubscribed {who} (HTTP {status}, {host})"
    return False, f"error {who}: {host} answered HTTP {status}"


def credentials():
    d = {}
    with open(ENV) as f:
        for line in f:
            k, sep, v = line.strip().partition("=")
            if sep and not k.startswith("#"):
                d[k.strip()] = v.strip().strip("'\"")
    return d["IMAP_HOST"], d["IMAP_USER"], d["IMAP_PASSWORD"]


def folders(im):
    """The all-mail and trash folders by their special-use flags (RFC 6154), which do not depend on the language
    of the mailbox; INBOX if the server has none."""
    found = {}
    _, lines = im.list()
    for raw in lines or []:
        line = raw.decode(errors="replace") if isinstance(raw, bytes) else str(raw)
        m = re.match(r'\((?P<flags>[^)]*)\)\s+(?:"[^"]*"|NIL)\s+(?P<name>.+)$', line)
        if not m:
            continue
        for flag in ("\\All", "\\Trash"):
            if flag.lower() in m.group("flags").lower().split():
                found[flag] = m.group("name").strip()
    return [found[f] for f in ("\\All", "\\Trash") if f in found] or ["INBOX"]


def latest_from(im, boxes, sender):
    for box in boxes:
        name = box if box.startswith('"') else '"' + box.replace('"', '\\"') + '"'
        if im.select(name, readonly=True)[0] != "OK":
            continue
        _, ids = im.search(None, "FROM", '"' + sender.replace('"', "") + '"')
        ids = ids[0].split() if ids and ids[0] else []
        if ids:
            _, data = im.fetch(ids[-1], "(BODY.PEEK[HEADER])")
            raw = next((p[1] for p in data if isinstance(p, tuple)), None)
            if raw:
                return email.message_from_bytes(raw, policy=email.policy.default)
    return None


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("senders", nargs="*", help="sender addresses (the latest email of each is used)")
    ap.add_argument("--eml", action="append", default=[], help="use this saved email instead of IMAP")
    ap.add_argument("--dry-run", action="store_true", help="say what would happen, send nothing")
    a = ap.parse_args(argv)
    if not a.senders and not a.eml:
        ap.error("give at least one sender or --eml file")
    ok = True
    for path in a.eml:
        with open(path, "rb") as f:
            msg = email.message_from_bytes(f.read(), policy=email.policy.default)
        good, line = handle(msg, str(msg.get("From", path)), a.dry_run)
        ok &= good
        print(line)
    if a.senders:
        host, user, password = credentials()
        im = imaplib.IMAP4_SSL(host, timeout=30)
        try:
            im.login(user, password)
            boxes = folders(im)
            for s in a.senders:
                msg = latest_from(im, boxes, s)
                good, line = handle(msg, s, a.dry_run) if msg else (True, f"skipped {s}: no email from them found")
                ok &= good
                print(line)
        finally:
            try:
                im.logout()
            except (OSError, imaplib.IMAP4.error):
                pass
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
