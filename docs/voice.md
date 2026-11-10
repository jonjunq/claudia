# Voice

All optional. Keys go in `~/.config/assistant/keys.env` (mode 600), settings in `~/assistant/assistant.env`.

## Voice notes in

### Transcribed before the assistant sees them

Out of the box, the Telegram plugin only tells the session "a voice note arrived, file id X". The assistant then
spends one turn deciding to download it and another deciding to transcribe it. We timed 117 real voice notes over
two days (median length 12 s):

| Step | Median | p90 |
|---|---|---|
| The assistant decides to call `download_attachment` | 2.3 s | 4.4 s |
| Download from Telegram | 0.3 s | 0.7 s |
| The assistant decides to run `transcribe.sh` | 2.7 s | 3.7 s |
| Transcription (Groq, including the Bash call) | 0.4 s | 1.5 s |
| The assistant answers (and does what the note asked) | 10.8 s | 33.8 s |
| **From arrival to answer** | **17.5 s** | 48.7 s |

The speech-to-text was 2 % of the time; the two extra turns were about 5 s per note, almost a third. The worst case
took 261 s: the plugin's download has no timeout (120 s) and the script's Groq call allowed 300 s before falling
back to a slow local model.

So [`patch-telegram-plugin.py`](../templates/telegram/patch-telegram-plugin.py) (v2, see
[docs/telegram-extras.md](telegram-extras.md#5-voice-notes-transcribed-on-arrival)) makes the plugin do it:
after its access check (a stranger's note is never downloaded), it fetches voice notes up to 15 minutes and audio
files up to 5 minutes, runs `~/assistant/bin/transcribe.sh`, and sends the transcript as the message itself, with
`voice_transcribed_by="groq"` and `voice_path` in the tag. The download has 10 s for `getFile` and 15 s for the file,
each with one retry; the transcription gets what is left of 55 s in all. If anything fails or runs out of time, the
notification goes out exactly as without the patch and the assistant transcribes it the old way. In the real
setup, a note now reaches the session about 0.7 s after it arrives, transcript included (download 0.1-0.4 s,
Groq 0.2-0.35 s), and the two extra turns are gone. Times (never the text) go to
`~/.claude/channels/telegram/voice.log`.

The patch also gives the plugin's own `download_attachment` and photo download a 30 s timeout with one retry, so a
hung Telegram download returns an error after about a minute instead of leaving the assistant waiting forever.

### `transcribe.sh`: a chain of engines

`transcribe.sh <file>` prints the text on stdout and `engine=<name> <ms>` on stderr. It tries, in order:

| Engine | Needs | Measured | Notes |
|---|---|---|---|
| [Groq](https://console.groq.com) `whisper-large-v3-turbo` | `GROQ_API_KEY` | 0.3 s for 30 s of audio, 0.9 s for 2 min | Free tier: 20 requests a minute, 2,000 a day, 8 h of audio a day. Rejects Telegram's `.oga` name (the script uploads `.ogg`) and files over 25 MB (it recompresses anything over 20 MB) |
| [Cloudflare Workers AI](https://developers.cloudflare.com/workers-ai/models/whisper-large-v3-turbo/) `whisper-large-v3-turbo` | `CF_AI_TOKEN`, `CF_AI_ACCOUNT_ID` | 1.4-4.9 s for 12-30 s, 6-16 s for 2 min | Optional. Free daily allowance of about 200 minutes of audio; same model, so the same quality |
| [Parakeet TDT 0.6B v3](https://huggingface.co/nvidia/parakeet-tdt-0.6b-v3) int8 on the CPU, via [onnx-asr](https://github.com/istupakov/onnx-asr) | a venv at `$PARAKEET_VENV` | 5.4 s for 12 s, 7.8 s for 30 s, 19 s for 2 min, on 4 shared cores | Optional. Stays at home. About 2 % different from Groq's text on our samples, up to 2.4 GB of RAM. 25 European languages, but **not** Basque, Catalan or Galician |
| [faster-whisper](https://github.com/SYSTRAN/faster-whisper) | a venv at `$WHISPER_VENV` | 36 s for 30 s and 78 s for 2 min (turbo, CPU) | Optional; the old fallback. Used directly when asked for a model |

- **Timeouts and retries.** Each cloud call gets 5 s to connect and `TRANSCRIBE_MAX_TIME` seconds in all (30 by
  default; the plugin passes 12). Groq gets one retry on a network error or a 5xx; a 429 (quota) or another 4xx
  goes straight to the next engine. Measured: Groq hanging, then Cloudflare, 17 s in all.
- **Names.** Whisper misspells names it has not heard of. Put them in `TRANSCRIBE_NAMES` in `assistant.env`
  (`"Ada, Proxmox, Jellyfin, n8n."`): the cloud engines get them as a prompt. Only names: an example sentence such as
  "Hi Ada, this is Alex" sometimes ended up inside the transcript. No language is forced, so a note in another
  language still comes out right.
- **Best quality.** `transcribe.sh <file> large-v3` goes straight to faster-whisper with that model (minutes on a
  CPU). The assistant uses it when you ask, or when a local transcript looks wrong.
- Whisper turbo once failed on a clip cut mid-word where Cloudflare and Parakeet got it right: different engines
  fail differently, which is the point of a chain.
- Be careful with test bursts: a quick series of test calls used up Groq's 20-per-minute limit for a minute.

**Install the local engines**: `assistant-setup install voice-local` (Parakeet, installed by default on machines
with 4 GB or more) and `assistant-setup install voice-best` (faster-whisper with the large-v3 model, optional) do
what follows; `assistant-doctor` says whether they are there. By hand, as the assistant's user (each is optional):

```bash
# Parakeet (about 640 MB of model, in the venv folder)
python3 -m venv ~/parakeet && ~/parakeet/bin/pip install "onnx-asr[cpu,hub]"
~/parakeet/bin/python -c 'import onnx_asr, os; d = os.path.expanduser("~/parakeet")
onnx_asr.load_model("nemo-parakeet-tdt-0.6b-v3", d + "/model", quantization="int8"); onnx_asr.load_vad("silero", d + "/model-vad")'

# faster-whisper (for "best quality")
python3 -m venv ~/whisper && ~/whisper/bin/pip install faster-whisper
# with an NVIDIA GPU, also: ~/whisper/bin/pip install nvidia-cublas-cu12 nvidia-cudnn-cu12
```

Both decode with ffmpeg (`apt install ffmpeg`): recent PyAV releases broke faster-whisper's own decoder. Audio over
90 s goes to Parakeet in voice-activity chunks, because in one piece its memory grows with the length. Only one
local model runs at a time (a lock file), since they share the CPU.

Keys: `printf '%s' '<key>' | assistant-setup key GROQ_API_KEY` (also `CF_AI_TOKEN`, `CF_AI_ACCOUNT_ID`,
`ELEVENLABS_API_KEY`) saves one in `keys.env` and checks that the service accepts it; the doctor checks them again
any time with one read-only request each.

**Cloudflare**: in the dashboard, create an API token with only the *Workers AI: Read* permission and put it, with
your account id, in `~/.config/assistant/keys.env`. Do not reuse a broader token you have for other things.

**Privacy.** Groq and Cloudflare say they do not keep the audio by default, but the notes leave your machine. Only
the local engines keep them at home; if that matters to you, leave the cloud keys out and the chain starts at
Parakeet. A transcript reaches the session like a typed message, and only from senders on the plugin's allowlist.

What we left out: a GPU for speech-to-text (with Groq at 0.4 s, a GPU kept awake costs power all day to win a
second), and hosted services whose free tier trains on your audio or shares its quota with text-to-speech.

## Voice replies out

`~/assistant/bin/speak.sh "text"` turns text into speech with [ElevenLabs](https://elevenlabs.io)
(`eleven_multilingual_v2`), converts it to OGG/Opus so Telegram shows it as a voice note, and sends it with the bot's
`sendVoice`. Set `TTS_VOICE_ID` (pick a voice in ElevenLabs' library), `TTS_LANGUAGE` and, if you like it faster,
`TTS_SPEED=1.2`.

The free ElevenLabs tier gives a small monthly character quota, so `CLAUDE.md` says: answer in text unless asked, and
when speaking write for the ear (no markdown, lists or emojis; numbers and times as they are said). If a name comes
out wrong, a phonetic substitution before sending fixes it (for example `sed 's/\bSean\b/Shawn/g'`).

We also ran a local open-source TTS on the GPU first; it worked but took about 35 s for one sentence, which is too
slow for a chat.

## Experimental: a voice call over Discord

Telegram bots cannot take calls, so the assistant's "phone line" is a Discord voice channel. This is a custom
**channel** (an MCP server that pushes events into the session, see
[Channels reference](https://code.claude.com/docs/en/channels-reference)) that the assistant wrote itself; it is not
included here yet because it is long and tied to our setup, but the architecture is simple to reproduce:

- A Discord bot (discord.js + `@discordjs/voice`, with DAVE end-to-end encryption support) joins the voice channel
  when you do and leaves when you leave. It only listens to your Discord user id.
- Your audio is decoded to PCM; a voice-activity detector plus an end-of-turn model decide when you finished a
  sentence; the clip is transcribed with Groq and pushed into the session as a `<channel source="call">` event.
- The assistant answers with the channel's `speak` tool: text to speech with a free neural voice, streamed back into
  the voice channel sentence by sentence. A `hang_up` tool ends the call.

Running it needs two things in `assistant.env`:

```bash
DEV_CHANNELS="server:call"     # the MCP server's name in ~/.claude.json (mcpServers.call)
```

- Self-built channels are not on Anthropic's channel allowlist during the research preview, so they load with
  `--dangerously-load-development-channels`, and Claude Code asks you to confirm that **at every start**.
  `bin/accept-dev-channel.sh` (launched by `start.sh`) waits for that one dialog and accepts it, so the nightly
  restart does not hang. Read what the flag means before using it.
- Channel servers built with a recent MCP SDK may negotiate a protocol revision that Claude Code does not register
  as a channel; `start.sh` exports `MCP_PROTOCOL_NEGOTIATION=legacy` when `DEV_CHANNELS` is set, as the channels
  docs suggested when we built it.
- Whisper invents phrases from silence and noise ("thanks for watching", subtitle credits). Drop those before they
  reach the session.

Treat it as a weekend project, not a feature.
