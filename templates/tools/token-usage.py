#!/usr/bin/env python3
"""Token usage per day and context size per project, read from Claude Code's own transcripts.

Claude Code writes every conversation to ~/.claude/projects/<project>/*.jsonl, including the token usage of each
API call. This script adds those numbers up, so you can see what your assistant (and anything else running Claude
Code on the machine) spends, and above all WHERE the context goes.

    python3 token-usage.py                 # last 7 days, the current user's ~/.claude
    python3 token-usage.py --days 30
    sudo python3 token-usage.py --all-users   # every /home/*/.claude and /root/.claude
    python3 token-usage.py --home /path/to/home --home /other/home

Two tables:
1. Per day: input, output, cache writes, cache reads, total and number of API calls.
2. Per project: average and peak context per call (input + cache) and the context of the first call of a
   conversation (what is loaded before anyone says anything: CLAUDE.md, imported notes, memory index, skill and tool
   listings). A high average with a low start means one conversation that keeps growing all day; a high start means
   too much is loaded up front.

Nothing is sent anywhere; it only reads files. Cache reads dominate the total and are much cheaper than fresh input,
so compare days and projects with each other rather than reading the total as a bill.
"""
import argparse
import datetime as dt
import glob
import json
import os
import sys


def homes(args):
    if args.home:
        return args.home
    if args.all_users:
        return sorted(set(glob.glob("/home/*") + ["/root"]))
    return [os.path.expanduser("~")]


def calls(path):
    """Yield (timestamp, message_id, usage) for each assistant API call in one transcript."""
    with open(path, errors="ignore") as f:
        for line in f:
            if '"usage"' not in line:
                continue
            try:
                d = json.loads(line)
            except ValueError:
                continue
            m = d.get("message") or {}
            u = m.get("usage")
            if d.get("type") != "assistant" or not u or not d.get("timestamp"):
                continue
            yield d["timestamp"], (m.get("id"), d.get("requestId")), u


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--home", action="append", help="home directory to read (repeatable)")
    ap.add_argument("--all-users", action="store_true", help="read every /home/* and /root (needs root)")
    args = ap.parse_args()

    since = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=args.days)
    seen = set()
    days = {}      # day -> [input, output, cache_write, cache_read, calls]
    projects = {}  # project -> {"calls", "context", "peak", "starts": []}

    for home in homes(args):
        for path in glob.glob(os.path.join(home, ".claude/projects/*/**/*.jsonl"), recursive=True):
            try:
                if dt.datetime.fromtimestamp(os.path.getmtime(path), dt.timezone.utc) < since:
                    continue
            except OSError:
                continue
            project = path.split("/projects/", 1)[1].split("/", 1)[0]
            if "/subagents/" in path:
                project += " (subagents)"
            key = f"{os.path.basename(home)}:{project}"
            first = True
            for ts, cid, u in calls(path):
                if cid in seen:
                    continue
                seen.add(cid)
                when = dt.datetime.fromisoformat(ts.replace("Z", "+00:00"))
                if when < since:
                    continue
                i = u.get("input_tokens", 0)
                o = u.get("output_tokens", 0)
                cw = u.get("cache_creation_input_tokens", 0)
                cr = u.get("cache_read_input_tokens", 0)
                row = days.setdefault(when.astimezone().date().isoformat(), [0, 0, 0, 0, 0])
                for n, v in enumerate((i, o, cw, cr, 1)):
                    row[n] += v
                ctx = i + cw + cr
                p = projects.setdefault(key, {"calls": 0, "context": 0, "peak": 0, "starts": []})
                p["calls"] += 1
                p["context"] += ctx
                p["peak"] = max(p["peak"], ctx)
                if first:
                    p["starts"].append(ctx)
                    first = False

    if not days:
        print(f"No Claude Code usage found in the last {args.days} days.")
        return 0

    m = lambda x: f"{x / 1e6:,.1f}M" if x >= 1e6 else f"{x / 1e3:,.0f}k"
    print(f"{'day':10}  {'input':>8} {'output':>8} {'cache write':>12} {'cache read':>12} {'total':>10} {'calls':>7}")
    tot = [0, 0, 0, 0, 0]
    for day in sorted(days):
        r = days[day]
        tot = [a + b for a, b in zip(tot, r)]
        print(f"{day:10}  {m(r[0]):>8} {m(r[1]):>8} {m(r[2]):>12} {m(r[3]):>12} {m(sum(r[:4])):>10} {r[4]:>7}")
    print(f"{'total':10}  {m(tot[0]):>8} {m(tot[1]):>8} {m(tot[2]):>12} {m(tot[3]):>12} {m(sum(tot[:4])):>10} {tot[4]:>7}")

    print()
    print(f"{'project':52} {'calls':>7} {'avg context':>12} {'peak':>8} {'at start':>9}")
    for key, p in sorted(projects.items(), key=lambda kv: -kv[1]["context"]):
        starts = sorted(p["starts"])
        start = starts[len(starts) // 2] if starts else 0
        print(f"{key[:52]:52} {p['calls']:>7} {p['context'] / p['calls'] / 1e3:>11.0f}k "
              f"{p['peak'] / 1e3:>7.0f}k {start / 1e3:>8.0f}k")
    return 0


if __name__ == "__main__":
    sys.exit(main())
