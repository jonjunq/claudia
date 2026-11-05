#!/usr/bin/env python3
"""recall: search the assistant's old conversations and its diary.

The idea comes from Hermes Agent's session_search: a SQLite FTS5 index (BM25 ranking), no model calls.
  recall search "words" [--since YYYY-MM-DD] [--until YYYY-MM-DD] [-n 8] [--all]
  recall show <session> <n> [--window 6]       # the messages around a result
  recall index                                 # incremental; search already does it
By default it searches what the owner said, what the assistant answered and the diary;
--all also includes commands, tool results and the helpers' (subagents') own work. If no message has all the words,
it searches again for any of them. Times are shown in local time; --since/--until compare UTC dates.
Paths can be overridden with RECALL_PROJECTS, RECALL_DIARY and RECALL_DB.
"""
import argparse, glob, json, os, re, sqlite3
from datetime import datetime

HOME = os.path.expanduser("~")
ASSISTANT_DIR = os.path.realpath(os.environ.get("ASSISTANT_DIR", os.path.join(HOME, "assistant")))
# Claude Code keeps each working directory's transcripts in ~/.claude/projects/<path with every
# non-alphanumeric character replaced by "-">, e.g. /home/alex/assistant -> -home-alex-assistant.
PROJECTS = os.environ.get("RECALL_PROJECTS",
                          os.path.join(HOME, ".claude/projects", re.sub(r"[^A-Za-z0-9]", "-", ASSISTANT_DIR)))
DIARY = os.environ.get("RECALL_DIARY", os.path.join(ASSISTANT_DIR, "notes/diary"))
DB = os.environ.get("RECALL_DB", os.path.join(HOME, ".cache/assistant-recall.db"))
MAX_TEXT = 4000           # per message; tool results can be huge
CHANNEL = re.compile(r'<channel source="([^"]+)"[^>]*>(.*?)</channel>', re.S)


def connect():
    os.makedirs(os.path.dirname(DB), exist_ok=True)
    os.umask(0o077)  # it stores pieces of emails and conversations: for its user only
    db = sqlite3.connect(DB)
    db.executescript("""
      CREATE TABLE IF NOT EXISTS files(path TEXT PRIMARY KEY, size INTEGER, mtime REAL);
      CREATE TABLE IF NOT EXISTS msg(id INTEGER PRIMARY KEY, session TEXT, n INTEGER, ts TEXT,
                                     who TEXT, text TEXT);
      CREATE INDEX IF NOT EXISTS msg_session ON msg(session, n);
      CREATE VIRTUAL TABLE IF NOT EXISTS fts USING fts5(text, content='msg', content_rowid='id',
                                     tokenize='unicode61 remove_diacritics 2');
    """)
    return db


def transcript_pieces(path):
    """(ts, who, text) from a conversation: owner, system, assistant, tool, result.
    Voice notes count as "owner": they are the output of bin/transcribe.sh."""
    voice = set()
    for line in open(path, encoding="utf-8", errors="replace"):
        try:
            d = json.loads(line)
        except ValueError:
            continue
        kind, m = d.get("type"), d.get("message") or {}
        if kind not in ("user", "assistant"):
            continue
        ts, c = d.get("timestamp", ""), m.get("content")
        blocks = [{"type": "text", "text": c}] if isinstance(c, str) else (c or [])
        for b in blocks:
            bt = b.get("type")
            if bt == "text" and kind == "user":
                t = b.get("text", "")
                channels = CHANNEL.findall(t)
                if channels:
                    for _, body in channels:
                        yield ts, "owner", body.strip()
                elif t.strip():
                    yield ts, "system", t
            elif bt == "text":
                yield ts, "assistant", b.get("text", "")
            elif bt == "tool_use":
                inp = b.get("input") or {}
                name = b.get("name", "")
                if name.endswith("__reply") or name.endswith("__edit_message"):
                    yield ts, "assistant", inp.get("text", "")
                    continue
                command = str(inp.get("command", ""))
                if re.search(r"\brecall\b", command):
                    continue  # its own searches would only add noise
                if "transcribe.sh" in command:
                    voice.add(b.get("id"))
                summary = inp.get("command") or inp.get("query") or inp.get("file_path") or json.dumps(inp, ensure_ascii=False)
                yield ts, "tool", f"[{name}] {summary}"
            elif bt == "tool_result":
                rc = b.get("content")
                if isinstance(rc, list):
                    rc = "\n".join(x.get("text", "") for x in rc if isinstance(x, dict))
                if rc:
                    is_voice = b.get("tool_use_id") in voice
                    yield ts, "owner" if is_voice else "result", ("(voice) " if is_voice else "") + str(rc)


def helper_pieces(path):
    """A helper's (subagent's) conversation: its own text counts as "helper", not as the assistant."""
    for ts, who, text in transcript_pieces(path):
        yield ts, ("helper" if who == "assistant" else who), text


def diary_pieces(path):
    day = os.path.basename(path)[:10]
    yield f"{day}T23:59:00Z", "diary", open(path, encoding="utf-8").read()


def index(db, quiet=False):
    new = 0
    sources = [(p, transcript_pieces) for p in glob.glob(f"{PROJECTS}/*.jsonl")]
    sources += [(p, helper_pieces) for p in glob.glob(f"{PROJECTS}/*/subagents/agent-*.jsonl")]
    sources += [(p, diary_pieces) for p in glob.glob(f"{DIARY}/*.md")]
    for path, reader in sources:
        st = os.stat(path)
        row = db.execute("SELECT size, mtime FROM files WHERE path=?", (path,)).fetchone()
        if row and row[0] == st.st_size and row[1] == st.st_mtime:
            continue
        session = {diary_pieces: "diary:", helper_pieces: "helper:"}.get(reader, "") + os.path.basename(path).rsplit(".", 1)[0]
        # Re-index the whole file: simpler than tracking offsets, and only a few files are live.
        for rid, text in db.execute("SELECT id, text FROM msg WHERE session=?", (session,)).fetchall():
            db.execute("INSERT INTO fts(fts, rowid, text) VALUES('delete', ?, ?)", (rid, text))
        db.execute("DELETE FROM msg WHERE session=?", (session,))
        for n, (ts, who, text) in enumerate(reader(path)):
            text = text.strip()[:MAX_TEXT]
            if not text:
                continue
            cur = db.execute("INSERT INTO msg(session,n,ts,who,text) VALUES(?,?,?,?,?)", (session, n, ts, who, text))
            db.execute("INSERT INTO fts(rowid, text) VALUES(?, ?)", (cur.lastrowid, text))
            new += 1
        db.execute("INSERT OR REPLACE INTO files VALUES(?,?,?)", (path, st.st_size, st.st_mtime))
    db.commit()
    if not quiet:
        print(f"indexed {new} messages")


def local(ts):
    """ISO UTC from the transcripts -> local time."""
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone().strftime("%Y-%m-%d %H:%M")
    except ValueError:
        return ts[:16]


def fts_query(text, any_word=False):
    """Plain words -> AND of prefixes (OR with any_word); FTS5 syntax typed by the user is kept as it is."""
    if re.search(r'["*()]|\b(AND|OR|NOT|NEAR)\b', text):
        return text
    return (" OR " if any_word else " ").join(f'"{w}"*' for w in re.findall(r"\w+", text))


def search(db, a, any_word=False):
    who = None if a.all else ("owner", "assistant", "diary")
    sql = """SELECT m.session, m.n, m.ts, m.who, snippet(fts, 0, '«', '»', ' … ', 24), bm25(fts) AS r
             FROM fts JOIN msg m ON m.id = fts.rowid WHERE fts MATCH ?"""
    args = [fts_query(a.text, any_word)]
    if who:
        sql += f" AND m.who IN ({','.join('?' * len(who))})"
        args += who
    if a.since:
        sql += " AND m.ts >= ?"; args.append(a.since)
    if a.until:
        sql += " AND m.ts < ?"; args.append(a.until + "T99")
    sql += " ORDER BY r LIMIT ?"; args.append(a.n * 4)
    seen, out = {}, []
    for session, n, ts, who_, piece, _ in db.execute(sql, args):
        # Like Hermes: at most two results per conversation, so one long day does not hide the others.
        if seen.get(session, 0) >= 2:
            continue
        seen[session] = seen.get(session, 0) + 1
        out.append(f"{local(ts)} · {who_} · {session} {n}\n   {' '.join(piece.split())}")
        if len(out) >= a.n:
            break
    if not out and not any_word and len(re.findall(r"\w+", a.text)) > 1 and fts_query(a.text) != a.text:
        # No message has every word (often one of them is one too many): try again with any of them, best first
        # (BM25 ranks higher the messages that have more of the words).
        print("(No message has all the words; these have some of them:)")
        return search(db, a, any_word=True)
    print("\n".join(out) if out else "No results. Try other words, --all, or drop the dates.")


def show(db, a):
    rows = db.execute("SELECT n, ts, who, text FROM msg WHERE session=? AND n BETWEEN ? AND ? ORDER BY n",
                      (a.session, a.n - a.window, a.n + a.window)).fetchall()
    for n, ts, who, text in rows:
        if who == "result" and n != a.n:
            text = text[:300] + ("…" if len(text) > 300 else "")
        mark = ">>" if n == a.n else "  "
        print(f"{mark} [{n}] {local(ts)} {who}: {text}\n")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("search"); s.add_argument("text"); s.add_argument("-n", type=int, default=8)
    s.add_argument("--since"); s.add_argument("--until"); s.add_argument("--all", action="store_true")
    v = sub.add_parser("show"); v.add_argument("session"); v.add_argument("n", type=int)
    v.add_argument("--window", type=int, default=6)
    sub.add_parser("index")
    a = p.parse_args()
    db = connect()
    if a.cmd == "index":
        index(db)
    elif a.cmd == "search":
        index(db, quiet=True)
        search(db, a)
    else:
        show(db, a)


if __name__ == "__main__":
    main()
