#!/bin/bash
# Transcribes an audio file (e.g. a Telegram voice note) to text on stdout.
# Default: Groq's hosted Whisper (whisper-large-v3-turbo, about a second, detects the language).
# If Groq fails or is not configured, or a model is given, it falls back to a local faster-whisper
# (GPU if there is one, otherwise CPU) when a venv exists at $WHISPER_VENV.
# Usage: transcribe.sh <file> [local-model]
# shellcheck source=lib.sh
. "$(dirname "$(readlink -f "$0")")/lib.sh"
load_env
f="${1:-}"; [ -f "$f" ] || { echo "No such file: $f" >&2; exit 1; }
KEYS="$HOME/.config/assistant/keys.env"
# shellcheck source=/dev/null
[ -f "$KEYS" ] && . "$KEYS"

if [ -z "${2:-}" ] && [ -n "${GROQ_API_KEY:-}" ]; then
  # Groq accepts up to 25 MB and does not recognise Telegram's .oga extension: recompress big files,
  # and always upload with an .ogg name.
  src="$f"
  if [ "$(stat -c%s "$f")" -gt 20000000 ]; then
    src=$(mktemp --suffix=.ogg)
    ffmpeg -nostdin -v error -y -i "$f" -ac 1 -c:a libopus -b:a 24k "$src"
  fi
  txt=$(curl -sf --max-time 300 https://api.groq.com/openai/v1/audio/transcriptions \
        -H "Authorization: Bearer $GROQ_API_KEY" -F model=whisper-large-v3-turbo \
        -F "file=@$src;filename=audio.ogg" -F response_format=text)
  ok=$?
  [ "$src" != "$f" ] && rm -f "$src"
  if [ $ok -eq 0 ] && [ -n "$txt" ]; then echo "$txt" | sed 's/^ *//'; exit 0; fi
  echo "(Groq failed; transcribing locally)" >&2
fi

VENV="${WHISPER_VENV:-$HOME/whisper}"
[ -x "$VENV/bin/python" ] || { echo "No Groq key and no local Whisper at $VENV (see docs/voice.md)" >&2; exit 1; }
model="${2:-${TRANSCRIBE_LOCAL_MODEL:-large-v3-turbo}}"
# CUDA libraries installed with pip inside the venv (nvidia-cublas-cu12, nvidia-cudnn-cu12), if any.
for nv in "$VENV"/lib/python3*/site-packages/nvidia; do
  [ -d "$nv" ] && export LD_LIBRARY_PATH="$nv/cublas/lib:$nv/cudnn/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
done
"$VENV/bin/python" - "$f" "$model" "$VENV/models" <<'PY'
import sys, subprocess, numpy as np, ctranslate2
from faster_whisper import WhisperModel
f, m, root = sys.argv[1:4]
gpu = ctranslate2.get_cuda_device_count() > 0
model = WhisperModel(m, device="cuda" if gpu else "cpu", compute_type="float16" if gpu else "int8",
                     download_root=root)
# Decode with ffmpeg (16 kHz mono float32): recent PyAV releases do not work with faster-whisper's decoder.
pcm = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-i", f, "-f", "f32le", "-ac", "1", "-ar", "16000", "-"],
                     check=True, capture_output=True).stdout
segments, _ = model.transcribe(np.frombuffer(pcm, np.float32), language=None, vad_filter=True, beam_size=5)
print(" ".join(s.text.strip() for s in segments))
PY
