# Troubleshooting

Problems we actually hit, roughly in order of how often.

**It does not answer on Telegram**
Attach to the session: `sudo -u <user> tmux attach -t assistant` (detach with Ctrl+B D). Usual causes: a permission
prompt or a dialog is waiting (see below), Claude Code logged out (run `claude` and `/login` inside the session),
you hit your plan's usage limit, or the service is down (`systemctl status assistant`, `~/assistant/restarts.log`).

**It stopped answering right after you opened Claude Code yourself, as the same user**
Only one program can read a bot's messages, and the Telegram plugin of a new Claude Code session replaces the one
it finds polling: your new session now gets the assistant's messages. Close it and `systemctl restart assistant`.
Run your own sessions as another user, or inside this repo's folder (its `.claude/settings.json` turns the plugin
off there).

**Something it should have is missing (voice notes, PDFs, the browser…)**
`assistant-doctor` lists every capability with ✅, ❌ and the command that fixes it; or ask the assistant "what are
you missing?". Typical after a by-hand install: no Groq key, no PDF reader, the plugin patch not applied yet.

**A dialog sits on the screen and blocks everything**
Unattended sessions stall on any interactive dialog. Ones we met: the development-channel confirmation at each start
(handled by `bin/accept-dev-channel.sh`) and "Teach auto mode about your environment?", which appeared out of the
blue; answer it once with "Don't show again". After big Claude Code updates, attach and look.

**Permission prompts that never reach Telegram**
Some classifier decisions are shown only in the terminal and are denied after a timeout; from the phone it just
looks like silence. The plugin's own permission relay did not cover them in our setup. The `PermissionRequest` hook
sends them to you with buttons ([telegram-extras.md](telegram-extras.md)), and `assistant-permission-watch` covers
whatever slips through. If it is something you always want to allow, add an `allow` rule ([permissions.md](permissions.md)).
If no request arrives at all, check `~/.cache/assistant-telegram/log`, and that `start.sh` ran the patcher
(`restarts.log`) since the last plugin update.

**You cannot tell whether it is working or hung**
That is what the "⏳ Working" message is for ([telegram-extras.md](telegram-extras.md)). If it never shows, look at
`~/.cache/assistant-telegram/log` and check that the `hooks` block is in `~/.claude/settings.json`.

**It does not know which message you replied to**
The official plugin drops quoted messages; the patch adds them. After a plugin update, the patch is re-applied at
the next start; if the plugin changed too much, `start.sh` tells you on Telegram.

**A command is missing from the bot's menu**
Telegram shows the most specific menu: one set for your chat (`scope` `chat`) hides the default one. The plugin sets
`/start`, `/help`, `/status` for all private chats; put every command you want in the chat-scoped call of
[setup.md](setup.md), in a single list. We once added `/clear` to the default scope only and it never appeared.

**The browser takes forever on a form**
Without a browser tool the assistant improvises Playwright scripts with guessed selectors, and custom dropdowns
make clicks time out. Install agent-browser and the browser skill ([browser.md](browser.md)).

**The browser stopped opening after n8n was installed or updated ("Missing X server or $DISPLAY")**
n8n carries an old agent-browser of its own (0.26, inside `@n8n/mcp-browser`), and installing n8n repoints
`/usr/local/bin/agent-browser` to it ([vercel-labs/agent-browser#2214](https://github.com/vercel-labs/agent-browser/issues/2214)).
That copy predates the automatic Xvfb (0.31.2), so Chromium with a window finds no display. `assistant-doctor` says
so; `assistant-setup install browser` puts the link back, and `install-n8n.sh` and `n8n-admin update` now do it
themselves after each install.

**It went silent after "This model's safeguards flagged this message"**
The safeguards behind Claude's newest models are intentionally broad and sometimes flag normal work (we hit it with
an errand about installing an app on a smart TV, flagged as `[cyber]`). By default the session then pauses on a
"Model switch" dialog in the terminal, and from the phone it looks dead. `"switchModelsOnFlag": true` (in the
template `settings.json`) moves it to another model and carries on; `assistant-permission-watch` tells you when the
model changes, and the next start goes back to `MODEL`. Switching model does not help if the errand itself keeps
being flagged: the trigger is the **words in the context**, not the model, so it repeats every turn while the topic
is in the conversation, even in a note telling it to stay away from it. Start a fresh conversation (`/clear` or
`.new-session`) and reword whatever it rereads at start (`notes/todo.md`, `yesterday.md`) in neutral terms.

**Optional: a backup model for flagged turns**
If you would rather not fall back to another Claude model, start the session with
`CLAUDE_CODE_DISABLE_REFUSAL_FALLBACK=1` (in `start.sh`): a flagged turn simply ends and the session stays on its
model, without the dialog. What it could not answer can then go to a backup model of your own: a local LLM
(llama.cpp, Ollama…) or another provider's API (DeepSeek, OpenRouter…), behind its own Telegram bot. The flag is in
the session transcript (`stop_reason: "refusal"` on the assistant message, or a `model_refusal_*` system entry), so
a small watcher can offer a button and copy the last messages across as they are. Two lessons: do not ask the
assistant to summarise the conversation for the handover (the same safeguards would flag the summary), and keep the
backup's answers, and any instructions about the safeguards, out of the assistant's context and its `CLAUDE.md`:
text about getting around them is itself enough to trip them. Not covered further here; if you go this way, you
will know how to wire it up.

**It retried a blocked action over and over**
Add (it is in the template): "if the permission system blocks a tool, stop at the first block and tell the owner".

**Typing into the session from a script does nothing**
`tmux send-keys -t assistant "text" Enter` can leave the text typed but unsent. Send the text with `-l` (literal) and
the Enter as a separate `send-keys` a second later, as `bin/lib.sh` does. And check the prompt is idle first: grey
text in the input box is only a suggestion, not a queued message.

**The first prompt was ignored at start**
The prompt must come before `--channels`, which takes several values and swallows it.

**After a crash it started a brand-new conversation**
If `--continue` fails right away there is nothing to continue and a new conversation is the right call; if it fails
after a while (Claude Code exited mid-conversation), starting fresh would lose the day. `start.sh` tells the two apart
by how long the attempt lasted (30 s).

**`/status` from Telegram does not reach the assistant**
The plugin uses `/status` for pairing. Use `/usage`.

**`/usage` shows old numbers**
`state.json` is written by the status line after each reply. Rate limits only exist on subscription plans.

**Scheduled reminders vanished**
Session-scoped scheduled tasks die with the session. Anything that must happen later belongs in `notes/todo.md` or
`notes/routines.md` too, and is rescheduled each morning ([daily-cycle.md](daily-cycle.md)).

**The end of day logged "summary NOT updated"**
The assistant was busy or the session was not idle at the time. The restart happens anyway after 12 minutes; the
summary from the previous day stays. Check the time is one when you never use it.

**Voice notes come out in the wrong language or garbled**
Leave language detection on (the scripts do). Locally, use `large-v3` for hard audio.

**It answered in the terminal instead of Telegram**
The channel message must be answered with the `reply` tool. Keep that line near the top of `CLAUDE.md`.
