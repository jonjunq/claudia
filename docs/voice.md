# Voice

All optional. Keys go in `~/.config/assistant/keys.env` (mode 600), settings in `~/assistant/assistant.env`.

## Voice notes in

Telegram voice notes reach the session as attachments. `CLAUDE.md` tells the assistant to download them with the
plugin's `download_attachment` and run `~/assistant/bin/transcribe.sh <file>`, then answer what was said.

`transcribe.sh`:

- With `GROQ_API_KEY`: sends the audio to [Groq](https://console.groq.com)'s hosted `whisper-large-v3-turbo`. It
  takes about a second and detects the language.
  Two quirks handled: Groq rejects Telegram's `.oga` extension (the script uploads it as `.ogg`), and files over 25 MB
  (the script recompresses anything over 20 MB to mono Opus).
- Without a key, or if Groq fails, or with a model argument (`transcribe.sh file.ogg large-v3`): runs
  [faster-whisper](https://github.com/SYSTRAN/faster-whisper) locally from a venv at `$WHISPER_VENV`:
  ```bash
  python3 -m venv ~/whisper && ~/whisper/bin/pip install faster-whisper
  # with an NVIDIA GPU, also: ~/whisper/bin/pip install nvidia-cublas-cu12 nvidia-cudnn-cu12
  ```
  It decodes with ffmpeg because recent PyAV releases broke faster-whisper's own decoder. On a laptop GPU we measured
  about 47 s for 5 minutes of audio with `large-v3-turbo` and about 4.5 minutes with `large-v3`; on CPU, turbo
  ran at roughly 0.6 s per second of audio. We moved to Groq and gave the GPU back.

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
