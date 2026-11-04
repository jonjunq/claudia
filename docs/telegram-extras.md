# Telegram extras: status, quoted messages, permission buttons, rich messages

Four things the official Telegram plugin does not do well enough for an assistant you only see through your phone,
and how this repo adds them. They live in [`templates/telegram/`](../templates/telegram/), which `install.sh` copies to
`/usr/local/lib/assistant-telegram/` owned by root, plus a `hooks` block in `settings.json`. None of it calls the
model: it is plain Python against the Telegram Bot API, so it costs nothing from your plan.

## 1. "Is it working or is it stuck?"

The plugin reacts to your message with 👀 and shows "typing…" once, for about five seconds. After that, a
ten-minute task and a hung session look the same.

Claude Code [hooks](https://code.claude.com/docs/en/hooks) fire on every tool call and at the end of each turn, so
the status does not depend on the assistant remembering to report it:

- `status-hook.py` runs (async) on `PreToolUse`, `PostToolUse`, `Stop` and `StopFailure` and only writes the current
  step to `~/.cache/assistant-telegram/turn.json`. The step is the description Claude already gives each Bash
  command ("Merge the two PDFs"), or the tool and its target. It only counts events whose `prompt_id` is written
  in the session transcript: Claude Code also runs background work in the same session (for example while it
  prepares the suggested reply) that fires the hooks but is not part of any turn, and it used to leave a phantom
  "⏳ Working" on Telegram until the next turn ended. That background work can also reuse the `prompt_id` of the
  turn that just ended, which *is* in the transcript; so every `Stop` records its prompt as closed, even for a turn
  that used no tools and never opened a status, and events of a closed prompt never open a new one.
- `status-daemon.py`, started by the first hook of a turn, keeps "typing…" on and, once the turn passes 15 seconds,
  sends a silent message and edits it every 5 seconds:

  ```
  ⏳ Working · 2 min 35 s
  Now: Upload the five attachments (for 20 s)
  ```

  When the turn ends it deletes the message. It switches to a ⚠️ line when the assistant is stopped: waiting for
  your permission, sitting on a terminal dialog (read from the tmux screen), no hook event for 10 minutes, or the
  session exited.

So: a message that keeps changing means working, ⚠️ means stuck, no message means idle. It also shows for routines
and other work you did not start; that is the point, you see when it is busy.

Why every 5 seconds and not every second: Telegram asks bots to send at most about one message per second per
chat, and edits count. Go over and Telegram throttles the **whole bot** for a while, which is the same bot the
assistant replies with. 5 seconds plus the typing action stays well under the limit.

## 2. Quoted messages

When you reply to or quote an earlier message, the plugin drops that context: the assistant only sees your new
text. This is a known gap (open issues [#929](https://github.com/anthropics/claude-plugins-official/issues/929),
[#1960](https://github.com/anthropics/claude-plugins-official/issues/1960),
[#3109](https://github.com/anthropics/claude-plugins-official/issues/3109),
[#6297](https://github.com/anthropics/claude-plugins-official/issues/6297) and more), still open in plugin 0.0.7.

`patch-telegram-plugin.py` patches the plugin's `server.ts` in the local plugin cache so the `<channel>` tag also
carries `reply_to_text` (one line, at most 1,500 characters), `reply_to_from` (`bot` when it is the assistant's own
message) and `reply_quote` (the exact fragment, if you highlighted one), plus a line in the plugin's instructions
saying what they mean. Line breaks and angle brackets in the quoted text are replaced, so a quoted message cannot
imitate the session's own tags.

A plugin update replaces the patched file. `start.sh` runs the patcher before every start: it is idempotent (a
marker comment), keeps the original as `server.ts.orig`, and if its anchors no longer match a new plugin version it
changes nothing and tells you on Telegram. The patched plugin loads on the next session start.

## 3. Approving permissions from Telegram

**What should already work.** Channels can [relay permission prompts](https://code.claude.com/docs/en/channels-reference#relay-permission-prompts),
and the official plugin declares it: you would get "🔐 Permission: Bash" with Allow / Deny buttons. In a test
session with ordinary permission prompts it did work. In the assistant's session, in auto mode, it never sent one
in weeks: the prompts the auto-mode classifier sends to the terminal were not relayed, and they deny themselves
after a countdown of about 30 seconds ("Claude Code will automatically block this request in 0:07, to avoid holding
up an unattended session"). From the phone, the assistant just went quiet. We did not find out why; the patched
plugin writes each native relay it receives to `~/.claude/channels/telegram/relay.log`, so you can see whether yours
arrive.

**What this repo adds.** A [`PermissionRequest` hook](https://code.claude.com/docs/en/hooks#permissionrequest), which
runs whenever Claude Code is about to ask for permission:

1. `permission-hook.py` sends you "🔐 Permission request" with the tool, its description, the command (or the input)
   and two buttons, ✅ Allow and ❌ Deny. The callback carries a random 16-hex id.
2. When you tap, the patched plugin checks that you are on its allowlist and writes `allow` or `deny` to
   `~/.claude/channels/telegram/verdicts/<id>`.
3. The hook, which polls for that file, returns the decision to Claude Code and edits the message to show the
   outcome. A deny tells the assistant not to retry and to ask you.
4. With no answer within 9½ minutes (the hook's `timeout` is 600 s) it returns no decision and the request goes on as
   before, in the terminal.

While the hook is waiting, `status-daemon.py` shows "⚠️ Stopped: waiting for your permission" and
`permission-watch.sh` does not send a second message for the same prompt. `start.sh` creates
`~/.claude/channels/telegram/permission-hook-enabled` when the hook is configured, and the patched plugin then keeps
quiet about native relays, so you never get the same request twice.

Behaviour change to be aware of: before, a blocked action was denied after about 30 seconds and the assistant moved
on. Now it waits for you, up to the timeout.

What we tested: an `ask` rule (`"ask": ["Bash(echo permission-test)"]`), which overrides auto mode, made the
assistant stop on a prompt; the request reached Telegram, Allow was tapped five seconds later and the command ran.
Not verified yet: whether an answer arrives in time on the prompts that carry the 30-second auto-mode countdown,
since the terminal dialog and the hook run side by side. If the countdown wins, the message on Telegram ends up as
"No answer".

### When the classifier blocks something outright

A `PermissionRequest` hook only runs when Claude Code is about to *ask*. When the auto-mode classifier denies a call
by itself, nobody is asked: the call fails, the model gets the denial and works around it or gives up, and from the
phone you only see the result. Two more hooks cover that case:

1. `denied-hook.py` runs on [`PermissionDenied`](https://code.claude.com/docs/en/hooks). It sends you "🚫 The
   classifier blocked this" with the tool, the classifier's reason, the command and two buttons, ✅ Approve and
   ❌ Keep blocked, and waits for the verdict the same way as the permission hook.
2. If you approve, it saves a **one-time approval** for that exact call (a SHA-256 of the tool name and its input;
   for Bash only the command counts, not the description or the timeout) in `~/.cache/assistant-telegram/approvals/`,
   valid for 5 minutes, and answers `retry: true`, so the model knows it may try again.
3. `approved-hook.py`, a synchronous `PreToolUse` hook, sees the identical call, uses up the approval and returns
   `allow`. Any other call, or the same one a second time, goes through the normal checks. When the approvals folder
   is empty it exits before reading its input, so it costs nothing on ordinary tool calls.

With no answer, or Keep blocked, the denial stands as before. If Telegram did not confirm the message (a timeout
does not mean it was not delivered), the hooks do not resend it, to avoid duplicates, and wait for the button anyway;
the denied hook then only waits 3 minutes.

Use it with care: the classifier blocks things for a reason, and an approval overrides it for that one call. Read
the command before tapping Approve.

### Security

- The scripts are root-owned in `/usr/local/lib/assistant-telegram/`, and the `hooks` block is in
  `~/.claude/settings.json`, which the assistant is not allowed to edit. It can edit its workspace, so nothing that
  decides permissions lives there.
- Buttons only count from senders on the plugin's allowlist, the same check as the plugin's own buttons. Anyone you
  put on that allowlist can approve tool use: keep it to yourself.
- The verdict files belong to the same Unix user as the assistant, so this is not a hard boundary against the
  assistant itself. What stops it from writing its own `allow` is that the id exists only inside the hook and in your
  Telegram message, and that writing a verdict file to approve itself is exactly the kind of action the auto-mode
  classifier refuses.
- The hooks act only when the session's working directory is the assistant's (`~/assistant`), so other Claude Code
  sessions of the same user are left alone.

## 4. Rich messages: headings, tables, collapsible blocks

Since Bot API 10.1 (June 2026) bots can send [rich messages](https://core.telegram.org/bots/api#rich-message-formatting-options)
with `sendRichMessage`: real headings, tables, lists, task lists, quotes, collapsible `<details>` blocks, footnotes
and formulas, which Telegram draws and fits to the phone screen. The plugin's `reply` tool only sends plain
messages, so `send-rich.py` sends the Markdown (or HTML) the assistant writes:

```bash
python3 -I /usr/local/lib/assistant-telegram/send-rich.py summary.md      # or: ... < summary.md
```

The `CLAUDE.md` template tells the assistant when to use it (tables, comparisons, long summaries) and to keep
`reply` for normal answers. If Telegram rejects the message, the script prints the error and exits 1, and the
assistant falls back to `reply`. Two things worth knowing about the Markdown:

- A single line break does **not** start a new line: lines join into one paragraph. Leave a blank line between
  paragraphs, or end the line with two spaces or a backslash.
- Raw `<tags>` are read as HTML and vanish; write them as `&lt;` or put them in `code`.

Limits: 32,768 characters, 500 blocks and 20 table columns per message.

### Writing for the phone

What makes these messages pleasant is less the formatting than the style, and the `CLAUDE.md` template asks for it
as a principle ("Writing for the phone"): a short title with an emoji that says what it is about, little text per
block, emojis as signposts rather than decoration, bold for the key word, a quote for the main idea, warnings that
stand out, an example of how to ask, and numbered options when you have to choose. A real one from our assistant,
translated and with the personal bits made generic, announcing that it had n8n now:

```markdown
## ⚙️ I have n8n now (set up today)

> n8n does **only** the repetitive things that need no thinking, without spending your subscription. I can now create, change and remove those automations **myself**: just ask me here.

- 📧 **Email right away**: every new email reaches me at once. If it matters I tell you now; if not, it goes in the 8:00 summary
- 📦 **The parcel**: n8n checks it every 3 h and writes to you only when something changes. It switches itself off once delivered (or tell me "drop the parcel one")
- 🆕 **Anything you want watched**: the price of something, a page that changes, an RSS feed, a reminder with outside data…

**Example:** "Tell me if the speaker on that second-hand site drops below €60". I tell you in 2 lines what I would set up (what it checks, how often and who it tells), you say "yes" and it runs on its own.

🔒 I never set anything up because an email or a web page says so, and I cannot pay for anything even if asked.
```

On Telegram that arrives as a heading, a highlighted quote and three short points that each start with their own
icon: read in five seconds, and easy to answer.

## Check it

- Status: ask it for something that takes a minute ("summarise today's email"); `~/.cache/assistant-telegram/log`
  shows `status <id> sent` and `deleted after …`.
- Quotes: reply to one of its old messages with "what was this about?".
- Permissions: add the `ask` rule above, ask it to run `echo permission-test`, tap Allow, then remove the rule. The
  log shows `permission asked …` and `permission … allow`.
- Classifier blocks: the next time one happens, the log shows `denied <id> …`, then `denied <id> approved` and
  `approval used …` if you tapped Approve.
- Rich messages: `printf '# Test\n\n| a | b |\n|---|---|\n| 1 | 2 |\n' | python3 -I /usr/local/lib/assistant-telegram/send-rich.py`
  shows a heading and a small table.
