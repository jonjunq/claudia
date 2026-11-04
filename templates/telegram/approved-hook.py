#!/usr/bin/env python3
"""PreToolUse hook (synchronous): if you approved this exact call from Telegram after the classifier blocked it
(see denied-hook.py), it lets it through once. Otherwise it says nothing and the permission system decides."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import tg, approvals

if not os.path.isdir(approvals.DIR) or not os.listdir(approvals.DIR):
    sys.exit(0)  # the common case: nothing approved, so no cost on every tool call
hook = json.load(sys.stdin)
if not tg.is_assistant(hook):
    sys.exit(0)
name = hook.get("tool_name", "?")
if approvals.consume(name, hook.get("tool_input")):
    tg.log(f"approval used {name}: {tg.describe(name, hook.get('tool_input'))}")
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "allow",
        "permissionDecisionReason": "The owner approved this from Telegram after the classifier blocked it (once)"}}))
