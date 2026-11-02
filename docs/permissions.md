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

If the same block keeps happening for something you always want, add an `allow` rule for it yourself, or describe
it to the classifier ([below](#teaching-the-auto-mode-classifier-about-your-setup)). Do not let the assistant edit
its own `settings.json` or type into its own terminal: we saw the classifier refuse the assistant typing commands into
its own session, and you would not want either to succeed after it read a malicious email. The one exception in this
repo is `bin/clear-context.sh`, a fixed script you allowlist by its exact path, which can only type `/clear` and a
fixed first message.

## Teaching the auto-mode classifier about your setup

`permissions.allow` and `permissions.ask` match tool calls by pattern. Some blocks cannot be fixed that way, because
the action is ordinary on its own and only risky without context: installing an app on a device on your network,
driving a service through its API, signing up for something. For those, Claude Code lets you describe your setup to
the classifier in plain sentences, in the `autoMode` block of `~/.claude/settings.json` (see
[Configure auto mode](https://code.claude.com/docs/en/auto-mode-config)):

- **`autoMode.environment`**: what is yours and trusted. The classifier uses it to tell your own devices and services
  from outside targets, and to read the other rules in your context.
- **`autoMode.allow`**: exceptions to the built-in "soft" block rules, for a kind of action you have decided is fine.
  (There are also `soft_deny` and `hard_deny` to add blocks of your own.)

Each list is an array of prose, read as natural-language rules, not patterns. Start every list you set with the
literal string `"$defaults"`: the built-in entries are spliced in at that position. A list without it **replaces**
the built-in one, so an `allow` list without `"$defaults"` drops the built-in exceptions, and a `soft_deny` or
`hard_deny` list without it drops the protections. Lists you do not set keep their defaults.

The classifier reads `autoMode` only from your user settings (`~/.claude/settings.json`), managed settings and the
`--settings` flag, not from a project's `.claude/settings.json`. The `install.sh` in this repo installs the
assistant's settings to `~/.claude/settings.json`, so that is where the block goes. The template does not set one:
an empty block would only restate the defaults, and JSON has no comments to explain it.

### Writing good sentences

Write them the way you would brief a new assistant who has never seen your house. A good sentence says:

1. **What is yours**, concretely enough to recognise: device or service, name, address.
2. **What is authorised**: the actions, and the tool or route they go through.
3. **When**: always, or only when you ask for it (and from where).
4. **The hard limit**: what stays off-limits even then.

Vague sentences ("trust my network", "do whatever I ask") either change nothing or open far more than you meant.
Keep each one to one device, service or kind of action.

### Examples

Adapt names and addresses; these are generic.

```json
{
  "autoMode": {
    "environment": [
      "$defaults",
      "The owner owns the living-room TV (tv.home.lan, 192.0.2.10) and the projector (192.0.2.11). Installing, launching and uninstalling apps on them through the manufacturer's developer mode and its command-line tools is authorised. Never root them or modify their system software.",
      "The media server at media.home.lan (Radarr, Sonarr, Jellyfin) belongs to the owner. Searching for, adding and downloading films and series with Radarr/Sonarr is authorised when the owner asks and picks the release (or tells the assistant to pick), and removing them is authorised when the owner asks."
    ],
    "allow": [
      "$defaults",
      "The owner authorises the assistant to create accounts on services and accept their terms and conditions on the owner's behalf when the owner asks for it on Telegram (the allowlisted chat), using the owner's details and the e-mail alias owner+<service>@example.com. Never payments, paid subscriptions or bank details."
    ]
  }
}
```

Why these shapes:

- **Devices**: the developer-mode route is what you allow; rooting and system changes are named as off-limits, so
  "install the app" cannot drift into "jailbreak the TV".
- **Own server**: the trigger is your request and your choice of release, so the assistant does not start
  downloading on its own initiative or because a web page suggested it.
- **Accounts**: we hit this one. Asked from Telegram to sign up for a TV maker's developer account (needed for
  developer mode), the assistant was blocked: the classifier would not let it accept terms and give consent on the
  owner's behalf, although the owner's request was right there in the chat. With the `allow` sentence above, the
  same request went through. The `+<service>` alias shows which service each email comes from and lets you filter
  or burn one address without touching the others.

The "never" inside an `allow` sentence narrows the exception; it is not a block of its own. Payments are already
covered by a built-in soft block (Real-World Transactions), which an explicit request from you can still clear. If
you want a line no request can cross, add it to `hard_deny` (with `"$defaults"` first) or, for a tool pattern, to
`permissions.deny`.

Check the result as the assistant's user: `claude auto-mode config` prints the effective lists, and
`claude auto-mode critique` flags sentences that are ambiguous or likely to misfire. Restart the session
(`systemctl restart assistant`) so it starts with the new settings. `/auto-mode-setup` can draft `environment`
entries from a coding project's files and history; for an assistant, writing them by hand is shorter and clearer.

### You edit them, not the assistant

These sentences are standing authorisations, so they are written by whoever administers the machine, never by the
assistant. Edit `~/.claude/settings.json` from root or your own account, and do not allowlist that edit for the
assistant. The classifier already blocks it from widening its own permissions, rightly: the built-in
Self-Modification rule covers its settings files, and also "consent" it would write for itself into `CLAUDE.md` or
memory. Keep authorisations out of `~/assistant/CLAUDE.md` and the memory for the same reason: the template's allow
rules (`Edit(~/assistant/**)` and the memory folder) let the assistant edit those without the classifier looking, so
a sentence there is only as trustworthy as the last email it read.
