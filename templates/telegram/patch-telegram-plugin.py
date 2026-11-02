#!/usr/bin/env python3
"""Patches the official Telegram plugin (claude-plugins-official/telegram) in the local plugin cache:
 1. Passes the message you quote or reply to (reply_to_text, reply_to_from, reply_quote) to Claude.
    The official plugin drops it (open issues #929, #1960, #2788, #3109, #6297 in anthropics/claude-plugins-official).
 2. Handles the buttons of permission-hook.py (callback hk:allow|deny:<id>) by writing the verdict to
    $STATE_DIR/verdicts/<id>, after the same allowlist check as the plugin's own buttons.
 3. Logs the plugin's native permission relays to $STATE_DIR/relay.log and, when $STATE_DIR/permission-hook-enabled
    exists (start.sh creates it when the hook is configured), does not send them, to avoid duplicate requests.
Idempotent: a file that already carries the marker is left alone; the original is kept as server.ts.orig.
The session must restart to load the patched plugin. Exit 0 = patched or already patched; 1 = anchors not found
(the plugin changed: adapt the anchors below)."""
import glob, os, shutil, sys

MARK = "// ASSISTANT-PATCH v1"
CHANGES = [
    # (anchor, text inserted BEFORE the anchor). Each anchor must appear exactly once.
    ("import { homedir } from 'os'\n",
     "import { appendFileSync as _patchAppend, existsSync as _patchExists } from 'fs' " + MARK + "\n"),
    ("    for (const chat_id of access.allowFrom) {\n      void bot.api.sendMessage(chat_id, text, { reply_markup: keyboard })",
     "    " + MARK + ": log native relays; stay quiet when permission-hook.py handles them\n"
     "    try { _patchAppend(join(STATE_DIR, 'relay.log'), `${new Date().toISOString()} ${request_id} ${tool_name}\\n`) } catch {}\n"
     "    if (_patchExists(join(STATE_DIR, 'permission-hook-enabled'))) return\n"),
    ("  const m = /^perm:(allow|deny|more):([a-km-z]{5})$/.exec(data)\n",
     "  " + MARK + ": buttons of the PermissionRequest hook\n"
     "  const hk = /^hk:(allow|deny):([0-9a-f]{16})$/.exec(data)\n"
     "  if (hk) {\n"
     "    if (!loadAccess().allowFrom.includes(String(ctx.from.id))) {\n"
     "      await ctx.answerCallbackQuery({ text: 'Not authorized.' }).catch(() => {})\n"
     "      return\n"
     "    }\n"
     "    const dir = join(STATE_DIR, 'verdicts')\n"
     "    mkdirSync(dir, { recursive: true, mode: 0o700 })\n"
     "    writeFileSync(join(dir, hk[2]!), hk[1]!, { mode: 0o600 })\n"
     "    await ctx.answerCallbackQuery({ text: hk[1] === 'allow' ? '✅' : '❌' }).catch(() => {})\n"
     "    return\n"
     "  }\n"),
    ("async function handleInbound(\n",
     MARK + ": context of the quoted / replied-to message\n"
     "function replyMeta(ctx: Context): Record<string, string> {\n"
     "  const r = ctx.message?.reply_to_message as any\n"
     "  if (!r) return {}\n"
     "  let t: string = r.text ?? r.caption ?? ''\n"
     "  if (!t) t = r.voice ? '(voice message)' : r.photo ? '(photo)' : r.document ? `(document ${r.document.file_name ?? ''})` : r.audio ? '(audio)' : '(non-text message)'\n"
     "  if (t.length > 1500) t = t.slice(0, 1500) + '…'\n"
     "  // One line, no angle brackets: the text must not be able to imitate the session's own tags.\n"
     "  const clean = (x: string) => x.replace(/\\r?\\n/g, ' ⏎ ').replace(/</g, '‹').replace(/>/g, '›')\n"
     "  const out: Record<string, string> = {\n"
     "    reply_to_message_id: String(r.message_id),\n"
     "    reply_to_text: clean(t),\n"
     "    reply_to_from: r.from?.is_bot ? 'bot' : String(r.from?.username ?? r.from?.id ?? ''),\n"
     "  }\n"
     "  const q = (ctx.message as any)?.quote?.text\n"
     "  if (q) out.reply_quote = clean(String(q).slice(0, 1000))\n"
     "  return out\n"
     "}\n\n"),
    ("        ...(imagePath ? { image_path: imagePath } : {}),\n",
     "        ...replyMeta(ctx),\n"),
    ("      \"Telegram's Bot API exposes no history or search",
     "      'If the tag has reply_to_text, the user is replying to (quoting) that earlier message: reply_to_from says who wrote it (\"bot\" means you) and reply_quote, when present, is the exact fragment they highlighted. Read their message in that context.',\n"
     "      '',\n"),
]


def patch(path):
    src = open(path).read()
    if MARK in src:
        return "already patched"
    for anchor, _ in CHANGES:
        if src.count(anchor) != 1:
            return f"ERROR: anchor not found exactly once: {anchor[:60]!r}"
    for anchor, new in CHANGES:
        src = src.replace(anchor, new + anchor, 1)
    if not os.path.exists(path + ".orig"):
        shutil.copy2(path, path + ".orig")
    with open(path + ".tmp", "w") as f:
        f.write(src)
    os.replace(path + ".tmp", path)
    return "patched"


pattern = os.path.expanduser(os.environ.get("TG_PLUGIN_GLOB", "~/.claude/plugins/cache/claude-plugins-official/telegram/*/server.ts"))
paths = sorted(glob.glob(pattern))
if not paths:
    print("Telegram plugin not found")
    sys.exit(1)
failed = False
for p in paths:
    result = patch(p)
    print(f"{p}: {result}")
    failed |= result.startswith("ERROR")
sys.exit(1 if failed else 0)
