#!/usr/bin/env python3
"""Patches the official Telegram plugin (claude-plugins-official/telegram) in the local plugin cache:
 1. Passes the message you quote or reply to (reply_to_text, reply_to_from, reply_quote) to Claude.
    The official plugin drops it (open issues #929, #1960, #2788, #3109, #6297 in anthropics/claude-plugins-official).
 2. Handles the buttons of permission-hook.py (callback hk:allow|deny:<id>) by writing the verdict to
    $STATE_DIR/verdicts/<id>, after the same allowlist check as the plugin's own buttons.
 3. Logs the plugin's native permission relays to $STATE_DIR/relay.log and, when $STATE_DIR/permission-hook-enabled
    exists (start.sh creates it when the hook is configured), does not send them, to avoid duplicate requests.
 4. (v2) Voice notes and short audios: after the access check, downloads them (with timeouts and one retry) and
    transcribes them with ~/assistant/bin/transcribe.sh *before* notifying Claude, which receives the text as the
    message content plus voice_transcribed_by and voice_path in the tag (and the usual attachment_file_id). If that
    fails or takes more than ~55 s, the notification goes out exactly as without the patch. Timings go to
    $STATE_DIR/voice.log (times and engine only, never the text).
 5. (v2) download_attachment and the photo download get timeouts and one retry (a hung fetch used to leave the
    assistant waiting with no limit).
 6. (v3) /usage is answered by the plugin itself, at once, without passing the message to the assistant: it costs no
    model call and works while the assistant is busy. It reads ~/assistant/state.json (written by statusline.sh),
    autoCompactWindow from ~/.claude/settings.json and ~/.cache/assistant-telegram/turn.json. Only for the allowlist;
    anyone else gets nothing, as before. Logged to $STATE_DIR/usage.log (the time only).
 7. (v4) /model is answered by the plugin too (allowlist only): without an argument it shows the current model and a
    button per model in MODELS of ~/assistant/assistant.env (callback md:<model>); with one (a model of that list or
    its name, "/model sonnet", "/model opus 4.8") or with a button it starts, detached,
    /usr/local/lib/assistant-telegram/model-switch.py <model> (ASSISTANT_MODEL_SWITCH only for the tests), which types
    it into the assistant's terminal once it is free and reports back. Nothing outside MODELS is ever started.
    Logged to $STATE_DIR/model.log.
Idempotent: a file that already carries this version's marker is left alone. A file patched by an older version is
rebuilt from server.ts.orig (the unpatched copy, refreshed whenever a clean plugin file is patched).
The session must restart to load the patched plugin. Exit 0 = patched or already patched; 1 = anchors not found
(the plugin changed: adapt the anchors below)."""
import glob, os, shutil, sys

MARK = "// ASSISTANT-PATCH v4"
FAMILY = "ASSISTANT-PATCH"

VOICE_HELPERS = (
    MARK + ": downloads with a timeout and one retry, and voice notes transcribed before Claude sees them\n"
    "async function _patchGetFile(file_id: string, ms: number) {\n"
    "  try { return await bot.api.getFile(file_id, AbortSignal.timeout(ms)) }\n"
    "  catch (e) {\n"
    "    if (e instanceof GrammyError) throw e // an API answer (file too big, expired): retrying will not help\n"
    "    await new Promise(r => setTimeout(r, 1000))\n"
    "    return await bot.api.getFile(file_id, AbortSignal.timeout(ms))\n"
    "  }\n"
    "}\n"
    "async function _patchFetch(url: string, ms: number): Promise<Response> {\n"
    "  let last: unknown\n"
    "  for (let i = 0; i < 2; i++) {\n"
    "    try {\n"
    "      const res = await fetch(url, { signal: AbortSignal.timeout(ms) })\n"
    "      if (res.status < 500) return res\n"
    "      last = new Error(`HTTP ${res.status}`)\n"
    "    } catch (e) { last = e }\n"
    "    if (i === 0) await new Promise(r => setTimeout(r, 1000))\n"
    "  }\n"
    "  throw last\n"
    "}\n"
    "const _PATCH_TRANSCRIBE = join(process.env.ASSISTANT_DIR ?? join(homedir(), 'assistant'), 'bin', 'transcribe.sh')\n"
    "type _PatchVoice = { text: string, meta: Record<string, string> }\n"
    "function _patchVoiceLog(s: string) {\n"
    "  try { _patchAppend(join(STATE_DIR, 'voice.log'), `${new Date().toISOString()} ${s}\\n`) } catch {}\n"
    "}\n"
    "async function _patchVoice(file_id: string, unique: string | undefined): Promise<_PatchVoice | undefined> {\n"
    "  const t0 = Date.now()\n"
    "  const end = t0 + 55000 // overall cap: past it, the notification goes out as without the patch\n"
    "  const left = (max: number) => Math.max(1000, Math.min(max, end - Date.now()))\n"
    "  const uid = (unique ?? '').replace(/[^a-zA-Z0-9_-]/g, '') || 'dl'\n"
    "  try {\n"
    "    if (!_patchExists(_PATCH_TRANSCRIBE)) return undefined\n"
    "    const file = await _patchGetFile(file_id, left(10000))\n"
    "    if (!file.file_path) throw new Error('no file_path')\n"
    "    const res = await _patchFetch(`https://api.telegram.org/file/bot${TOKEN}/${file.file_path}`, left(15000))\n"
    "    if (!res.ok) throw new Error(`download HTTP ${res.status}`)\n"
    "    const buf = Buffer.from(await res.arrayBuffer())\n"
    "    const rawExt = file.file_path.includes('.') ? file.file_path.split('.').pop()! : 'bin'\n"
    "    const ext = rawExt.replace(/[^a-zA-Z0-9]/g, '') || 'bin'\n"
    "    const path = join(INBOX_DIR, `${Date.now()}-${uid}.${ext}`)\n"
    "    mkdirSync(INBOX_DIR, { recursive: true })\n"
    "    writeFileSync(path, buf)\n"
    "    const t1 = Date.now()\n"
    "    const secs = Math.floor(left(45000) / 1000)\n"
    "    const r = await new Promise<{ text: string, engine: string }>((ok, ko) => {\n"
    "      _patchExecFile('timeout', ['-k', '3', String(secs), _PATCH_TRANSCRIBE, path],\n"
    "        { env: { ...process.env, TRANSCRIBE_MAX_TIME: '12' }, maxBuffer: 8 << 20 },\n"
    "        (err, stdout, stderr) => {\n"
    "          if (err) return ko(new Error(`transcribe.sh: ${String(err.message).split('\\n')[0]} | ${String(stderr).slice(-300).replace(/\\n/g, ' ')}`))\n"
    "          ok({ text: String(stdout).trim(), engine: /engine=(\\S+)/.exec(String(stderr))?.[1] ?? '?' })\n"
    "        })\n"
    "    })\n"
    "    if (!r.text) throw new Error('empty transcript')\n"
    "    _patchVoiceLog(`ok ${uid} bytes=${buf.length} download=${t1 - t0}ms transcription=${Date.now() - t1}ms total=${Date.now() - t0}ms engine=${r.engine}`)\n"
    "    return { text: r.text, meta: { voice_transcribed_by: r.engine.replace(/[^a-zA-Z0-9_.-]/g, ''), voice_path: path } }\n"
    "  } catch (e) {\n"
    "    _patchVoiceLog(`failed ${uid} total=${Date.now() - t0}ms ${String(e).slice(0, 400).replace(/\\n/g, ' ')}`)\n"
    "    return undefined\n"
    "  }\n"
    "}\n"
    "// The callback handleInbound runs after the access check (none for audio longer than max seconds).\n"
    "function _patchVoiceCb(ctx: Context, file_id: string, unique: string | undefined, seconds: number | undefined, max: number) {\n"
    "  if (seconds != null && seconds > max) return undefined\n"
    "  return async (): Promise<_PatchVoice | undefined> => {\n"
    "    const r = await _patchVoice(file_id, unique)\n"
    "    const cap = ctx.message?.caption\n"
    "    return r && { meta: r.meta, text: cap ? `${cap}\\n\\n${r.text}` : r.text }\n"
    "  }\n"
    "}\n\n"
)

USAGE_TS = (
    MARK + ": /usage answered at once by the plugin, without the assistant (allowlist only)\n"
    "function _patchUsage(): string {\n"
    "  const read = (p: string): any => { try { return JSON.parse(readFileSync(p, 'utf8')) } catch { return undefined } }\n"
    "  const ws = process.env.ASSISTANT_DIR ?? join(homedir(), 'assistant')\n"
    "  const e = read(join(ws, 'state.json'))\n"
    "  if (!e) return 'No usage data yet (state.json is written after the first reply). Ask the assistant: \"usage\".'\n"
    "  let tz: string | undefined\n"
    "  try {\n"
    "    tz = /^TIMEZONE=(.+)$/m.exec(readFileSync('/usr/local/share/assistant/install.conf', 'utf8'))?.[1]?.trim()\n"
    "    if (tz) new Intl.DateTimeFormat('en-GB', { timeZone: tz })\n"
    "  } catch { tz = undefined }\n"
    "  const o = tz ? { timeZone: tz } : {}\n"
    "  const day = (d: Date) => d.toLocaleDateString('en-CA', o)\n"
    "  const when = (s: unknown) => {\n"
    "    if (typeof s !== 'number' || !s) return '?'\n"
    "    const d = new Date(s * 1000)\n"
    "    const hm = d.toLocaleTimeString('en-GB', { ...o, hour: '2-digit', minute: '2-digit' })\n"
    "    return (day(d) === day(new Date()) ? 'today' : d.toLocaleDateString('en-GB', { ...o, weekday: 'short', day: 'numeric' })) + ' at ' + hm\n"
    "  }\n"
    "  const pct = (x: unknown) => typeof x === 'number' ? `${Math.round(x)} %` : '?'\n"
    "  const st = read(join(homedir(), '.claude', 'settings.json')) ?? {}\n"
    "  let cw: unknown = st.autoCompactWindow\n"
    "  if (typeof cw !== 'number') for (const v of Object.values(st.modelSettings ?? {})) if (typeof (v as any)?.autoCompactWindow === 'number') cw = (v as any).autoCompactWindow\n"
    "  const upd = String(e.updated ?? '?')\n"
    "  const l = [`📊 Usage (as of ${upd.startsWith(day(new Date())) ? upd.slice(11) : upd})`, `• Model: ${e.model ?? '?'}`]\n"
    "  if (typeof e.context_pct === 'number' && typeof e.context_max === 'number') {\n"
    "    const k = Math.round(e.context_pct * e.context_max / 100000)\n"
    "    l.push(typeof cw === 'number' ? `• Context: ≈${k}k of ${Math.round(cw / 1000)}k (compacts by itself there)` : `• Context: ${pct(e.context_pct)} (≈${k}k)`)\n"
    "  }\n"
    "  const warn = (x: unknown, at: number) => typeof x === 'number' && x >= at ? ' ⚠️' : ''\n"
    "  l.push(`• 5-hour limit: ${pct(e.five_hour_pct)}${warn(e.five_hour_pct, 80)} · resets ${when(e.five_hour_resets_at)}`)\n"
    "  l.push(`• Week: ${pct(e.week_pct)}${warn(e.week_pct, 70)} · resets ${when(e.week_resets_at)}`)\n"
    "  const cache = join(homedir(), '.cache', 'assistant-telegram')\n"
    "  const t = read(join(cache, 'turn.json'))\n"
    "  const p = read(join(cache, 'permission-pending.json'))\n"
    "  const now = Date.now() / 1000\n"
    "  if (p && now - (p.since ?? 0) < 900) l.push('• Now: waiting for your permission')\n"
    "  else if (t && t.start && !t.end) l.push(`• Now: working, for ${Math.max(1, Math.round((now - t.start) / 60))} min`)\n"
    "  else l.push('• Now: free')\n"
    "  l.push('', '(automatic answer from the bot: it does not reach the assistant and costs nothing)')\n"
    "  return l.join('\\n')\n"
    "}\n"
    "bot.command('usage', async ctx => {\n"
    "  const g = dmCommandGate(ctx)\n"
    "  if (!g || !g.access.allowFrom.includes(g.senderId)) return\n"
    "  try { _patchAppend(join(STATE_DIR, 'usage.log'), `${new Date().toISOString()} usage\\n`) } catch {}\n"
    "  await ctx.reply(_patchUsage()).catch(() => {})\n"
    "})\n\n"
)

MODEL_TS = (
    MARK + ": /model: the plugin starts model-switch.py, which types it into the assistant's terminal once it is free\n"
    "const _PATCH_WS = process.env.ASSISTANT_DIR ?? join(homedir(), 'assistant')\n"
    "function _patchEnvValue(key: string): string {\n"
    "  try { return (new RegExp(`^${key}=(.*)$`, 'm').exec(readFileSync(join(_PATCH_WS, 'assistant.env'), 'utf8'))?.[1] ?? '').trim().replace(/^[\"']|[\"']$/g, '') }\n"
    "  catch { return '' }\n"
    "}\n"
    "function _patchModels(): string[] {\n"
    "  const l = _patchEnvValue('MODELS').split(/\\s+/).filter(m => /^[A-Za-z0-9][A-Za-z0-9.\\[\\]-]{1,47}$/.test(m))\n"
    "  return l.length ? l : ['opus', 'sonnet', 'haiku']\n"
    "}\n"
    "// What the status line shows for it, or its start: claude-opus-4-8 -> Opus 4.8, opus -> Opus (as model-switch.py)\n"
    "function _patchModelName(m: string): string {\n"
    "  const b = m.split('[')[0]!\n"
    "  const cap = (x: string) => x.charAt(0).toUpperCase() + x.slice(1)\n"
    "  if (!b.startsWith('claude-')) return cap(b)\n"
    "  const p = b.slice(7).split('-')\n"
    "  const n = p.slice(1).filter(x => /^\\d{1,2}$/.test(x))\n"
    "  return cap(p[0] ?? '') + (n.length ? ' ' + n.join('.') : '')\n"
    "}\n"
    "function _patchModelPick(arg: string): string | undefined {\n"
    "  const a = arg.trim().toLowerCase().replace(/\\s+/g, ' ')\n"
    "  return _patchModels().find(m => m.toLowerCase() === a || _patchModelName(m).toLowerCase() === a)\n"
    "}\n"
    "function _patchModelNow(): string {\n"
    "  try { const e = JSON.parse(readFileSync(join(_PATCH_WS, 'state.json'), 'utf8')); if (e?.model) return String(e.model) } catch {}\n"
    "  const m = _patchEnvValue('MODEL')\n"
    "  return m ? _patchModelName(m) : '?'\n"
    "}\n"
    "function _patchModelKeyboard(now: string): InlineKeyboard {\n"
    "  const kb = new InlineKeyboard()\n"
    "  const l = _patchModels()\n"
    "  const exact = l.some(m => _patchModelName(m) === now)\n"
    "  l.forEach((m, i) => {\n"
    "    const n = _patchModelName(m)\n"
    "    kb.text(((exact ? n === now : now.startsWith(n)) ? '✅ ' : '') + n, `md:${m}`)\n"
    "    if (i % 2 === 1) kb.row()\n"
    "  })\n"
    "  return kb\n"
    "}\n"
    "function _patchModelSwitch(m: string): boolean {\n"
    "  if (!_patchModels().includes(m)) return false\n"
    "  try { _patchAppend(join(STATE_DIR, 'model.log'), `${new Date().toISOString()} ${m}\\n`) } catch {}\n"
    "  try {\n"
    "    const script = process.env.ASSISTANT_MODEL_SWITCH || '/usr/local/lib/assistant-telegram/model-switch.py'\n"
    "    const h = _patchSpawn('python3', ['-I', script, m], { detached: true, stdio: 'ignore' })\n"
    "    h.on('error', () => {})\n"
    "    h.unref()\n"
    "    return true\n"
    "  } catch { return false }\n"
    "}\n"
    "const _patchModelSwitching = (m: string) => `🔄 Switching to ${_patchModelName(m)} once the assistant finishes what it is doing; I will tell you.`\n"
    "bot.command('model', async ctx => {\n"
    "  const g = dmCommandGate(ctx)\n"
    "  if (!g || !g.access.allowFrom.includes(g.senderId)) return\n"
    "  const arg = String(ctx.match ?? '').trim()\n"
    "  const now = _patchModelNow()\n"
    "  if (!arg) {\n"
    "    await ctx.reply(`🧠 It is on ${now}. Pick a model (I switch it in its terminal once it is free):`, { reply_markup: _patchModelKeyboard(now) }).catch(() => {})\n"
    "    return\n"
    "  }\n"
    "  const m = _patchModelPick(arg)\n"
    "  if (!m) {\n"
    "    await ctx.reply(`I do not know \"${arg.slice(0, 40)}\". Models: ${_patchModels().map(_patchModelName).join(', ')} (/model ${_patchModels().join(', /model ')}).`, { reply_markup: _patchModelKeyboard(now) }).catch(() => {})\n"
    "    return\n"
    "  }\n"
    "  await ctx.reply(_patchModelSwitch(m) ? _patchModelSwitching(m) : 'I could not start the model switch.').catch(() => {})\n"
    "})\n\n"
)

# (mode, anchor, text): "before" inserts the text in front of the anchor; "replace" replaces the anchor with the text.
# Each anchor must appear exactly once in the plugin's server.ts.
CHANGES = [
    ("before", "import { homedir } from 'os'\n",
     "import { appendFileSync as _patchAppend, existsSync as _patchExists } from 'fs' " + MARK + "\n"
     "import { execFile as _patchExecFile, spawn as _patchSpawn } from 'child_process' " + MARK + "\n"),
    ("before", "    for (const chat_id of access.allowFrom) {\n      void bot.api.sendMessage(chat_id, text, { reply_markup: keyboard })",
     "    " + MARK + ": log native relays; stay quiet when permission-hook.py handles them\n"
     "    try { _patchAppend(join(STATE_DIR, 'relay.log'), `${new Date().toISOString()} ${request_id} ${tool_name}\\n`) } catch {}\n"
     "    if (_patchExists(join(STATE_DIR, 'permission-hook-enabled'))) return\n"),
    ("before", "  const m = /^perm:(allow|deny|more):([a-km-z]{5})$/.exec(data)\n",
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
     "  }\n"
     "  " + MARK + ": buttons of /model\n"
     "  const md = /^md:([A-Za-z0-9.\\[\\]-]{2,48})$/.exec(data)\n"
     "  if (md) {\n"
     "    if (!loadAccess().allowFrom.includes(String(ctx.from.id))) {\n"
     "      await ctx.answerCallbackQuery({ text: 'Not authorized.' }).catch(() => {})\n"
     "      return\n"
     "    }\n"
     "    const m = md[1]!\n"
     "    if (!_patchModelSwitch(m)) {\n"
     "      await ctx.answerCallbackQuery({ text: 'Unknown model' }).catch(() => {})\n"
     "      return\n"
     "    }\n"
     "    await ctx.answerCallbackQuery({ text: _patchModelName(m) }).catch(() => {})\n"
     "    await ctx.editMessageText(_patchModelSwitching(m)).catch(() => {})\n"
     "    return\n"
     "  }\n"),
    ("before", "async function handleInbound(\n",
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
     "}\n\n"
     + VOICE_HELPERS),
    ("before", "        ...(imagePath ? { image_path: imagePath } : {}),\n",
     "        ...replyMeta(ctx),\n"
     "        ...(_voice ? _voice.meta : {}),\n"),
    ("before", "      \"Telegram's Bot API exposes no history or search",
     "      'If the tag has reply_to_text, the user is replying to (quoting) that earlier message: reply_to_from says who wrote it (\"bot\" means you) and reply_quote, when present, is the exact fragment they highlighted. Read their message in that context.',\n"
     "      '',\n"
     "      'If the tag has voice_transcribed_by, the message was a voice note or audio and its content is already the transcript (made by that engine): treat it as what the user said, and do not call download_attachment or transcribe it again. The audio file is already saved at voice_path in case a higher-quality transcription is ever needed.',\n"
     "      '',\n"),
    # v2: voice notes and audios transcribed before the notification
    ("replace", "  attachment?: AttachmentMeta,\n): Promise<void> {\n",
     "  attachment?: AttachmentMeta,\n"
     "  voice?: () => Promise<_PatchVoice | undefined>, " + MARK + "\n"
     "): Promise<void> {\n"),
    ("replace", "  const imagePath = downloadImage ? await downloadImage() : undefined\n",
     "  const imagePath = downloadImage ? await downloadImage() : undefined\n"
     "  const _voice = voice ? await voice().catch(() => undefined) : undefined " + MARK + "\n"),
    ("replace", "      content: text,\n",
     "      content: _voice ? _voice.text : text, " + MARK + "\n"),
    ("replace", "    mime: voice.mime_type,\n  })\n",
     "    mime: voice.mime_type,\n"
     "  }, _patchVoiceCb(ctx, voice.file_id, voice.file_unique_id, voice.duration, 900)) " + MARK + "\n"),
    ("replace", "    mime: audio.mime_type,\n    name,\n  })\n",
     "    mime: audio.mime_type,\n    name,\n"
     "  }, _patchVoiceCb(ctx, audio.file_id, audio.file_unique_id, audio.duration, 300)) " + MARK + "\n"),
    # v2: downloads with a timeout
    ("replace", "        const file = await bot.api.getFile(file_id)\n",
     "        const file = await _patchGetFile(file_id, 30000) " + MARK + "\n"),
    ("replace", "        const res = await fetch(url)\n        if (!res.ok)",
     "        const res = await _patchFetch(url, 30000) " + MARK + "\n        if (!res.ok)"),
    ("replace", "      const res = await fetch(url)\n      const buf",
     "      const res = await _patchFetch(url, 30000) " + MARK + "\n      const buf"),
    # v3: /usage without the model (before the text handler, so the command never reaches the assistant); v4: /model
    ("before", "bot.on('message:text', async ctx => {\n", USAGE_TS + MODEL_TS),
]


def write(path, text, like):
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        f.write(text)
    shutil.copystat(like, tmp)
    os.replace(tmp, path)


def patch(path):
    src = open(path).read()
    if MARK in src:
        return "already patched"
    orig = path + ".orig"
    if FAMILY in src:
        # Patched by an older version: start again from the unpatched copy.
        if not os.path.exists(orig):
            return "ERROR: patched by an older version and there is no server.ts.orig to rebuild from"
        src = open(orig).read()
        if FAMILY in src:
            return "ERROR: server.ts.orig is patched too"
        clean = None
    else:
        clean = src  # a clean file (new install or plugin update): it becomes the new .orig
    for _, anchor, _ in CHANGES:
        if src.count(anchor) != 1:
            return f"ERROR: anchor not found exactly once: {anchor[:60]!r}"
    for mode, anchor, new in CHANGES:
        if src.count(anchor) != 1:
            return f"ERROR: anchor no longer unique while patching: {anchor[:60]!r}"
        src = src.replace(anchor, new + anchor if mode == "before" else new, 1)
    if clean is not None:
        write(orig, clean, path)
    write(path, src, path)
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
