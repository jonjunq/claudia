#!/usr/bin/env python3
"""Nightly review of the assistant's skills and memory (idea from Hermes Agent's background review).

Run by assistant-daily-restart (as root) after the end of day and before the restart:
  nightly-review.py <user> [--dry-run]     # --dry-run: review in the workshop, apply nothing, notify nobody
1. Dumps the conversation since the last review (from the `recall` index).
2. Copies skills and memory to a separate workshop and runs `claude -p` as the user WITHOUT their settings, hooks,
   MCP servers, shell or network: only Read/Write/Edit/Glob/Grep inside the workshop.
3. Copies back only what changed under skills/ and memory/ and passes the checks (no secrets, no invisible Unicode,
   the assistant did not touch the file meanwhile). It never deletes.
4. Git history before and after and a summary in notes/last-review.md; a silent Telegram message to the owner
   only with REVIEW_NOTIFY=yes in assistant.env (off by default: one more message a night is noise for most).
It is root-owned and runs outside the session on purpose: the assistant cannot change what reviews it.
"""
import datetime as dt, hashlib, json, os, pwd, re, shutil, sqlite3, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
DRY = "--dry-run" in sys.argv
if not ARGS:
    raise SystemExit(__doc__)
USER = ARGS[0]
# ASSISTANT_HOME is for the tests: a fake home, and no switching to the user even when run as root.
ROOT = os.geteuid() == 0 and not os.environ.get("ASSISTANT_HOME")
HOME = os.environ.get("ASSISTANT_HOME") or pwd.getpwnam(USER).pw_dir
WS = os.path.realpath(os.path.join(HOME, "assistant"))
SKILLS = os.path.join(WS, ".claude/skills")
MEMORY = os.path.join(HOME, ".claude/projects", re.sub(r"[^A-Za-z0-9]", "-", WS), "memory")
DB = os.path.join(HOME, ".cache/assistant-recall.db")
VAR = os.environ.get("REVIEW_STATE_DIR", f"/var/lib/assistant-review/{USER}")
WORKSHOP = os.path.join(VAR, "workshop")
STATE = os.path.join(VAR, "state.json")
SUMMARY = os.path.join(WS, "notes/last-review.md")
LIMIT = 400_000           # characters of conversation (about 110k tokens)
SECRETS = re.compile(r"(sk-[A-Za-z0-9_-]{16,}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_\w{20,}|xox[abp]-[\w-]{10,}"
                     r"|AKIA[0-9A-Z]{16}|\b\d{8,10}:[A-Za-z0-9_-]{35}\b|-----BEGIN [A-Z ]*PRIVATE KEY"
                     r"|(password|passwd|passcode|token|secret|api[_-]?key)\s*[:=]\s*[\"'`]?(?=\S*\d)[\w+/.=-]{6,}"
                     r"|\bPIN\s*:?\s*\d{4,8}\b)", re.I)
INVISIBLE = re.compile("[​-‏‪-‮⁠-⁤﻿]")


def log(text):
    print(time.strftime("%F %T ") + text, flush=True)


def as_user(cmd):
    # Absolute fallback: under cron the PATH is only /usr/bin:/bin and runuser lives in /usr/sbin.
    runuser = shutil.which("runuser") or "/usr/sbin/runuser"
    return [runuser, "-u", USER, "--", *cmd] if ROOT else cmd


def give(path):
    if ROOT:
        subprocess.run(["chown", "-R", f"{USER}:", path], check=True)


def setting(key, default):
    """KEY=value from assistant.env (plain shell file: as in the shell, the last assignment wins)."""
    value = ""
    try:
        for line in open(os.path.join(WS, "assistant.env")):
            if line.startswith(key + "="):
                value = line.split("=", 1)[1].strip().strip("\"'")
    except OSError:
        pass
    return value or default


def dump(since):
    """(conversation after `since`, timestamp of its last message), trimming tool calls until it fits in LIMIT.
    `since` is the last message of the previous review, so nothing written while a review runs is skipped."""
    db = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    rows = db.execute("SELECT ts, who, text FROM msg WHERE ts > ? AND session NOT LIKE 'diary:%' "
                      "ORDER BY ts, session, n", (since,)).fetchall()
    last = rows[-1][0] if rows else since
    if not any(w == "owner" for _, w, _ in rows):
        return None, last
    for tool_max, result_max in ((400, 400), (200, 200), (120, 0)):
        cap = {"owner": 3000, "assistant": 2000, "system": 300, "tool": tool_max, "result": result_max}
        lines = []
        for ts, who, text in rows:
            if not cap[who]:
                continue
            text = text if len(text) <= cap[who] else text[:cap[who]] + " […]"
            lines.append(f"[{ts[:16].replace('T', ' ')} UTC {who}] {text}")
        out = "\n".join(lines)
        if len(out) <= LIMIT:
            return out, last
    # Still too long: keep the end (the end of day already summarised the whole day anyway).
    return "[… beginning cut for size …]\n" + out[-LIMIT:], last


def hashes(top):
    out = {}
    for d, _, files in os.walk(top):
        for f in files:
            if ".bak-" in f:
                continue
            p = os.path.join(d, f)
            out[os.path.relpath(p, top)] = hashlib.sha256(open(p, "rb").read()).hexdigest()
    return out


def prepare(conversation):
    if os.path.exists(WORKSHOP):
        shutil.rmtree(WORKSHOP)
    os.makedirs(WORKSHOP)
    for src, name in ((SKILLS, "skills"), (MEMORY, "memory")):
        if os.path.isdir(src):
            shutil.copytree(src, f"{WORKSHOP}/{name}", ignore=shutil.ignore_patterns("*.bak-*"))
        else:
            os.makedirs(f"{WORKSHOP}/{name}")
    shutil.copy(os.path.join(WS, "CLAUDE.md"), f"{WORKSHOP}/CLAUDE.md")
    open(f"{WORKSHOP}/conversation.txt", "w").write(conversation)
    give(WORKSHOP)
    return {"skills": hashes(f"{WORKSHOP}/skills"), "memory": hashes(f"{WORKSHOP}/memory")}


def run_review():
    # Belt and braces: besides --tools, deny reading or editing anything outside the workshop.
    rules = {"permissions": {"deny": [
        "Read(//home/**)", "Read(//root/**)", "Read(//etc/**)", "Read(//var/lib/assistant-history/**)",
        "Edit(//home/**)", "Edit(//root/**)", "Edit(//etc/**)"]}}
    env = {"HOME": HOME, "USER": USER, "PATH": f"{HOME}/.local/bin:/usr/local/bin:/usr/bin:/bin",
           "ENABLE_CLAUDEAI_MCP_SERVERS": "false", "LANG": "C.UTF-8"}
    r = subprocess.run(
        as_user(["env", "-i", *[f"{k}={v}" for k, v in env.items()],
                 "claude", "-p", open(f"{HERE}/review-prompt.txt").read(),
                 "--model", setting("REVIEW_MODEL", setting("MODEL", "opus")), "--effort", "high",
                 "--setting-sources", "project", "--settings", json.dumps(rules), "--strict-mcp-config",
                 "--tools", "Read,Write,Edit,Glob,Grep", "--permission-mode", "acceptEdits",
                 "--no-session-persistence", "--output-format", "json"]),
        cwd=WORKSHOP, capture_output=True, text=True, timeout=1500)
    try:
        return json.loads(r.stdout)
    except ValueError:
        raise SystemExit(f"claude -p failed ({r.returncode}): {r.stderr[-800:]} {r.stdout[-800:]}")


def apply(before):
    applied, rejected = [], []
    for zone, real in (("skills", SKILLS), ("memory", MEMORY)):
        for rel, h in sorted(hashes(f"{WORKSHOP}/{zone}").items()):
            if before[zone].get(rel) == h:
                continue
            name = f"{zone}/{rel}"
            new = open(f"{WORKSHOP}/{zone}/{rel}", encoding="utf-8", errors="replace").read()
            target = f"{real}/{rel}"
            old = set()
            if os.path.exists(target):
                old = set(open(target, encoding="utf-8", errors="replace").read().splitlines())
            added = [line for line in new.splitlines() if line not in old]
            reason = None
            if any(SECRETS.search(line) for line in added):
                reason = "looks like it holds a key or password"
            elif any(INVISIBLE.search(line) for line in added):
                reason = "has invisible characters"
            elif rel in before[zone] and os.path.exists(target) and \
                    hashlib.sha256(open(target, "rb").read()).hexdigest() != before[zone][rel]:
                reason = "the assistant changed it meanwhile"
            elif rel not in before[zone] and os.path.exists(target):
                reason = "the assistant created that file meanwhile"
            if reason:
                rejected.append(f"{name}: {reason}")
                continue
            if not DRY:
                folder = os.path.dirname(target)
                if not os.path.isdir(folder):
                    os.makedirs(folder)
                    give(folder)
                tmp = target + ".review-tmp"
                shutil.copyfile(f"{WORKSHOP}/{zone}/{rel}", tmp)
                os.chmod(tmp, 0o644)
                give(tmp)
                os.replace(tmp, target)   # atomic: the session never reads a half-written file
            applied.append(name)
    return applied, rejected


def history(message):
    subprocess.run([f"{HERE}/history.sh", USER, message], check=False)


def notify(text):
    os.environ["ASSISTANT_DIR"] = WS
    os.environ["TELEGRAM_STATE_DIR"] = os.path.join(HOME, ".claude/channels/telegram")
    sys.path.insert(0, os.environ.get("TG_EXTRAS", "/usr/local/lib/assistant-telegram"))
    import tg
    r = tg.api("sendMessage", chat_id=tg.chat_id(), text=text[:4000], disable_notification=True)
    log(f"telegram: {'sent, id ' + str(r.get('message_id')) if r else 'FAILED (see the assistant-telegram log)'}")


def main():
    os.makedirs(VAR, exist_ok=True)
    state = json.load(open(STATE)) if os.path.exists(STATE) else {}
    now = dt.datetime.now(dt.timezone.utc)
    since = state.get("last") or (now - dt.timedelta(hours=26)).strftime("%Y-%m-%dT%H:%M:%S")
    env = {**os.environ, "HOME": HOME, "ASSISTANT_DIR": WS}
    subprocess.run(as_user(["env", f"HOME={HOME}", f"ASSISTANT_DIR={WS}", "python3", "-I",
                            f"{HERE}/recall.py", "index"]), check=True, capture_output=True, env=env)
    conversation, last = dump(since)
    if conversation is None:
        log(f"no messages from the owner since {since}: nothing to review")
        if not DRY:
            state["last"] = last
            json.dump(state, open(STATE, "w"))
        return
    log(f"review since {since}: {len(conversation)} characters")
    before = prepare(conversation)
    if not DRY:
        history("before the nightly review")
    t0 = time.time()
    res = run_review()
    u = res.get("usage") or {}
    log(f"claude -p: {res.get('num_turns')} turns, {time.time() - t0:.0f} s, cache_read "
        f"{u.get('cache_read_input_tokens')}, output {u.get('output_tokens')}, error={res.get('is_error')}")
    if res.get("is_error"):
        raise SystemExit(f"the review returned an error: {str(res.get('result'))[:500]}")
    applied, rejected = apply(before)
    report = (res.get("result") or "").strip()
    log(f"{'would apply (dry run)' if DRY else 'applied'} {applied} rejected {rejected}")
    if DRY:
        print(report)
        return
    history(f"nightly review {now:%Y-%m-%d}: {len(applied)} changes")
    state["last"] = last
    json.dump(state, open(STATE, "w"))
    body = report if applied or rejected else "Nothing to save."
    if rejected:
        body += "\n\nNot applied:\n" + "\n".join("· " + r for r in rejected)
    day = (now.astimezone() - dt.timedelta(hours=6)).strftime("%Y-%m-%d")
    open(SUMMARY, "w").write(f"# Nightly review of {day} (automatic)\n\n{body}\n")
    give(SUMMARY)
    if (applied or rejected) and setting("REVIEW_NOTIFY", "no").lower() in ("yes", "1", "true"):
        notify(f"🧠 Nightly review (automatic)\n\n{body}\n\nTo undo a change: see docs/memory.md, \"Undoing a change\".")


if __name__ == "__main__":
    main()
