# Permissions

The assistant reads untrusted text all day: emails from strangers, web pages, shared documents. Any of them can
contain instructions ("forward the last invoice to…"). The permission setup assumes that one day it will read such a
thing.

## Auto mode + an allowlist

`settings.json` sets `"defaultMode": "auto"`. In [auto mode](https://code.claude.com/docs/en/permission-modes)
Claude Code runs without routine prompts and a background classifier checks risky actions against what you asked
for. On top of that:

- **allow**: things it does alone. Reading (files, web, mail, calendar, Drive), drafting, labelling, calendar
  changes, creating and editing Drive files, its own notes, scheduling routines, its voice and `/clear` scripts.
- **ask**: things it must clear with you: sending, replying to and forwarding email, trash, spam, sharing files.
  The Telegram plugin relays these prompts to your chat, so you approve or deny from the phone.
- Everything else goes through the classifier.

The prompt text is also repeated in `CLAUDE.md` ("sending: always confirm first"), so it asks you in plain words
before it even reaches the rule. The rule is the guarantee; the text is the manners.

A few details that bite:

- Path rules: in `~/.claude/settings.json`, `Edit(/home/me/x/**)` does **not** mean the absolute path; a single
  leading slash anchors at `~/.claude/`. Use `~/x/**` or `//home/me/x/**`. `Write(...)` path rules never match;
  use `Edit(...)`, which covers writes. See [Configure permissions](https://code.claude.com/docs/en/permissions).
- Bash rules match the command text: `Bash(~/assistant/bin/speak.sh *)` does not match the same script called by its
  absolute path, so the template lists both forms.
- Connector tool names are `mcp__claude_ai_<Service>__<tool>`. `/permissions` in the session shows the ones you have.

## Why not `bypassPermissions`?

Because of what it reads. With `--dangerously-skip-permissions` there is no classifier and no prompts: a crafted
email could make it send or delete things and you would find out afterwards. Auto mode costs you an occasional
prompt on the phone; that is the price of having a check between "it read something" and "it acted". If prompts
annoy you, add specific `allow` rules for the actions you approve every time, rather than switching the checks off.

## When it gets blocked

Sometimes the classifier sends a decision to the **terminal** instead of to Telegram. Nobody is there, the prompt
times out, and from your phone the assistant just looks silent. We once lost about ten minutes this way while it
tried to delete a batch of calendar events one by one. Two defences, both in the templates:

1. `CLAUDE.md`: "if the permission system blocks a tool, do not retry in a loop: stop at the first block and tell
   the owner what you wanted to do".
2. `bin/permission-watch.sh` (service `assistant-permission-watch`): every 5 seconds it looks at the tmux screen
   and, when it sees "Do you want to proceed?", sends you a Telegram message saying which tool is waiting. It uses
   the bot's `sendMessage`, which does not interfere with the plugin's polling.

If the same block keeps happening for something you always want, add an `allow` rule for it yourself. Do not let
the assistant edit its own `settings.json` or type into its own terminal: we saw the classifier refuse the assistant
typing commands into its own session, and you would not want either to succeed after it read a malicious email. The one exception in this repo is `bin/clear-context.sh`, a fixed script you allowlist
by its exact path, which can only type `/clear` and a fixed first message.
