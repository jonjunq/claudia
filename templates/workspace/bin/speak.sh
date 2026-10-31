#!/bin/bash
# Turns text into a natural voice note (ElevenLabs) and sends it to you on Telegram.
# Usage: speak.sh "text"    (or the text on stdin)
# Needs ELEVENLABS_API_KEY in ~/.config/assistant/keys.env and TTS_VOICE_ID in assistant.env.
# The free ElevenLabs tier has a small monthly character quota: keep voice replies for when they are asked for.
set -euo pipefail
# shellcheck source=lib.sh
. "$(dirname "$(readlink -f "$0")")/lib.sh"
load_env
# shellcheck source=/dev/null
. "$HOME/.config/assistant/keys.env"
text="${1:-$(cat)}"
[ -n "$text" ] || { echo "No text" >&2; exit 1; }
[ -n "${TTS_VOICE_ID:-}" ] || { echo "Set TTS_VOICE_ID in assistant.env" >&2; exit 1; }

out_dir="$ASSISTANT_DIR/voice-out"
mkdir -p "$out_dir"
find "$out_dir" -type f -mtime +7 -delete
out="$out_dir/$(date +%Y%m%d-%H%M%S)"
body=$(jq -n --arg t "$text" --arg l "${TTS_LANGUAGE:-en}" '{text: $t, model_id: "eleven_multilingual_v2", language_code: $l}')
code=$(curl -s --max-time 120 -o "$out.mp3" -w '%{http_code}' \
  "https://api.elevenlabs.io/v1/text-to-speech/$TTS_VOICE_ID?output_format=mp3_44100_128" \
  -H "xi-api-key: $ELEVENLABS_API_KEY" -H "Content-Type: application/json" -d "$body")
if [ "$code" != 200 ]; then echo "ElevenLabs failed ($code): $(head -c 300 "$out.mp3")" >&2; rm -f "$out.mp3"; exit 1; fi
# Telegram shows OGG/Opus as a voice note (with waveform) rather than as a music file.
ffmpeg -nostdin -v error -y -i "$out.mp3" -filter:a "atempo=${TTS_SPEED:-1.0}" -c:a libopus -b:a 48k -ar 48000 "$out.ogg"
rm -f "$out.mp3"
curl -sf -F chat_id="$(tg_chat)" -F voice=@"$out.ogg" "https://api.telegram.org/bot$(tg_token)/sendVoice" >/dev/null
echo "Voice note sent ($out.ogg)"
