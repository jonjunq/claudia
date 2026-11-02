#!/usr/bin/env python3
"""Send the owner a Telegram rich message (Bot API 10.1+, sendRichMessage): headings, tables, lists, quotes,
collapsible <details> blocks and footnotes, drawn by Telegram and adapted to phone and desktop.

Usage:  python3 -I /usr/local/lib/assistant-telegram/send-rich.py [file.md] [--html] [--silent]
        Markdown from the file, or from stdin. --html if the content is HTML instead of Markdown.
For short answers keep using the plugin's reply tool; this is for tables, comparisons and long summaries.
Uses the plugin's bot and the owner's chat (see tg.py). On failure it prints Telegram's error and exits 1:
then fix the formatting or send the text with reply. Prints the message id on success.
Syntax: https://core.telegram.org/bots/api#rich-markdown-style (note: a single line break joins the lines into one
paragraph; end a line with two spaces or a backslash to keep the break).
"""
import json, os, sys, urllib.error, urllib.parse, urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tg  # noqa: E402

LIMIT = 32768  # Telegram: characters per rich message (and at most 500 blocks)


def main(argv):
    files = [a for a in argv if not a.startswith("--")]
    text = open(files[0], encoding="utf-8").read() if files else sys.stdin.read()
    if not text.strip():
        sys.exit("Empty message")
    if len(text) > LIMIT:
        sys.exit(f"Too long for one rich message ({len(text)} > {LIMIT} characters): split it")
    field = "html" if "--html" in argv else "markdown"
    params = {"chat_id": tg.chat_id(), "rich_message": json.dumps({field: text})}
    if "--silent" in argv:
        params["disable_notification"] = "true"
    req = urllib.request.Request(f"{tg.API}/bot{tg.token()}/sendRichMessage",
                                 data=urllib.parse.urlencode(params).encode())
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            print("sent, message_id", json.load(r)["result"]["message_id"])
    except urllib.error.HTTPError as e:
        print("Telegram error", e.code, e.read().decode(errors="replace")[:400])
        sys.exit(1)
    except Exception as e:
        print("Telegram error", e)
        sys.exit(1)


if __name__ == "__main__":
    main(sys.argv[1:])
