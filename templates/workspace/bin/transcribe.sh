#!/bin/bash
# Transcribes an audio file (e.g. a Telegram voice note) to text on stdout; the engine used goes to stderr
# ("engine=groq 412ms"). Fallback chain, first that works wins:
#   1. Groq, hosted whisper-large-v3-turbo        (GROQ_API_KEY; about 0.3-1 s)
#   2. Cloudflare Workers AI, whisper-large-v3-turbo (CF_AI_TOKEN + CF_AI_ACCOUNT_ID; about 1.5-5 s)
#   3. Parakeet TDT 0.6B v3 locally on the CPU   (venv at $PARAKEET_VENV; about 5 s for a 12 s note)
#   4. faster-whisper locally                    (venv at $WHISPER_VENV; slow on a CPU)
#   5. nothing worked: exit 1, no text.
# Cloud attempts: 5 s to connect, TRANSCRIBE_MAX_TIME seconds in all (default 30). Groq gets one retry on a network
# error or 5xx; a 429 (quota) or another 4xx goes straight to the next engine.
# With a model ("best quality": transcribe.sh <file> large-v3) it goes straight to the local faster-whisper.
# TRANSCRIBE_NAMES (assistant.env): names and words the cloud models should spell right, e.g. "Ada, Proxmox, n8n."
# Tests: TRANSCRIBE_NO_GROQ=1, TRANSCRIBE_NO_CF=1, TRANSCRIBE_NO_LOCAL=1 skip an engine.
# Usage: transcribe.sh <file> [local-whisper-model]   (docs/voice.md)
# shellcheck source=lib.sh
. "$(dirname "$(readlink -f "$0")")/lib.sh"
load_env
f="${1:-}"; [ -f "$f" ] || { echo "No such file: $f" >&2; exit 1; }
KEYS="$HOME/.config/assistant/keys.env"
# shellcheck source=/dev/null
[ -f "$KEYS" ] && . "$KEYS"
MAXT="${TRANSCRIBE_MAX_TIME:-30}"
# Only names, no sentence: an example sentence in the prompt sometimes ends up in the transcript.
NAMES="${TRANSCRIBE_NAMES:-}"
LOCK="${XDG_RUNTIME_DIR:-/tmp}/assistant-transcribe.lock"
T0=$(date +%s%N)
done_with() { echo "engine=$1 $(( ($(date +%s%N) - T0) / 1000000 ))ms" >&2; }

groq() {
  [ -n "${GROQ_API_KEY:-}" ] && [ "${TRANSCRIBE_NO_GROQ:-}" != 1 ] || return 1
  local src="$f" out code rc i
  local prompt=(); [ -n "$NAMES" ] && prompt=(-F "prompt=$NAMES")
  # Groq accepts up to 25 MB and does not recognise Telegram's .oga extension: recompress big files,
  # and always upload with an .ogg name.
  if [ "$(stat -c%s "$f")" -gt 20000000 ]; then
    src=$(mktemp --suffix=.ogg)
    ffmpeg -nostdin -v error -y -i "$f" -ac 1 -c:a libopus -b:a 24k "$src"
  fi
  out=$(mktemp)
  for i in 1 2; do
    code=$(curl -s -o "$out" -w '%{http_code}' --connect-timeout 5 --max-time "$MAXT" \
      https://api.groq.com/openai/v1/audio/transcriptions -H "Authorization: Bearer $GROQ_API_KEY" \
      -F model=whisper-large-v3-turbo -F "file=@$src;filename=audio.ogg" -F response_format=text "${prompt[@]}")
    rc=$?
    if [ $rc -eq 0 ] && [ "$code" = 200 ] && grep -q '[^[:space:]]' "$out"; then
      sed 's/^ *//' "$out"; rm -f "$out"; [ "$src" != "$f" ] && rm -f "$src"; return 0
    fi
    echo "(Groq failed: curl $rc, HTTP $code)" >&2
    case "$code" in 000|5??) [ "$i" = 1 ] && sleep 1 && continue ;; esac
    break
  done
  rm -f "$out"; [ "$src" != "$f" ] && rm -f "$src"; return 1
}

cloudflare() {
  [ -n "${CF_AI_TOKEN:-}" ] && [ -n "${CF_AI_ACCOUNT_ID:-}" ] && [ "${TRANSCRIBE_NO_CF:-}" != 1 ] || return 1
  local body out code rc txt
  body=$(mktemp); out=$(mktemp)
  # Workers AI takes the audio base64-encoded inside JSON.
  python3 -I -c 'import base64, json, sys
d = {"audio": base64.b64encode(open(sys.argv[1], "rb").read()).decode()}
if sys.argv[2]: d["initial_prompt"] = sys.argv[2]
json.dump(d, open(sys.argv[3], "w"))' "$f" "$NAMES" "$body"
  code=$(curl -s -o "$out" -w '%{http_code}' --connect-timeout 5 --max-time "$MAXT" \
    -H "Authorization: Bearer $CF_AI_TOKEN" -H "Content-Type: application/json" --data-binary @"$body" \
    "https://api.cloudflare.com/client/v4/accounts/$CF_AI_ACCOUNT_ID/ai/run/@cf/openai/whisper-large-v3-turbo")
  rc=$?
  if [ "$code" = 200 ] && txt=$(python3 -I -c 'import json, sys
d = json.load(open(sys.argv[1])); t = ((d.get("result") or {}).get("text") or "").strip()
print(t) if d.get("success") and t else sys.exit(1)' "$out" 2>/dev/null); then
    rm -f "$body" "$out"; echo "$txt"; return 0
  fi
  # No retry here: Groq already used its own, and the local engine is next.
  echo "(Cloudflare failed: curl $rc, HTTP $code)" >&2
  rm -f "$body" "$out"; return 1
}

parakeet() {
  local venv="${PARAKEET_VENV:-$HOME/parakeet}" err txt rc
  [ -x "$venv/bin/python" ] && [ -d "$venv/model" ] && [ "${TRANSCRIBE_NO_LOCAL:-}" != 1 ] || return 1
  err=$(mktemp)
  exec 9>"$LOCK"; flock 9   # one local model at a time: they share the CPU
  txt=$(HF_HUB_OFFLINE=1 "$venv/bin/python" -I - "$f" "$venv" 2>"$err" <<'PY'
import os, subprocess, sys
import numpy as np, onnxruntime as ort, onnx_asr
so = ort.SessionOptions(); so.intra_op_num_threads = min(4, os.cpu_count() or 1); so.log_severity_level = 3
venv = sys.argv[2]
pcm = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-i", sys.argv[1], "-f", "f32le", "-ac", "1", "-ar", "16000", "-"],
                     check=True, capture_output=True).stdout
a = np.frombuffer(pcm, np.float32)
m = onnx_asr.load_model("nemo-parakeet-tdt-0.6b-v3", venv + "/model", quantization="int8", sess_options=so)
if len(a) > 90 * 16000:  # long audio in voice-activity chunks: in one piece, memory grows with the length
    m = m.with_vad(onnx_asr.load_vad("silero", venv + "/model-vad", sess_options=so))
    print(" ".join(s.text.strip() for s in m.recognize(a, sample_rate=16000)).strip())
else:
    print(m.recognize(a, sample_rate=16000).strip())
PY
)
  rc=$?
  exec 9>&-
  if [ $rc -eq 0 ] && [ -n "$txt" ]; then rm -f "$err"; echo "$txt"; return 0; fi
  echo "(local Parakeet failed: $(tail -c 300 "$err"))" >&2; rm -f "$err"; return 1
}

whisper_local() {
  local venv="${WHISPER_VENV:-$HOME/whisper}" model=$1 nv
  [ -x "$venv/bin/python" ] || return 1
  # CUDA libraries installed with pip inside the venv (nvidia-cublas-cu12, nvidia-cudnn-cu12), if any.
  for nv in "$venv"/lib/python3*/site-packages/nvidia; do
    [ -d "$nv" ] && export LD_LIBRARY_PATH="$nv/cublas/lib:$nv/cudnn/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
  done
  exec 9>"$LOCK"; flock 9
  "$venv/bin/python" -I - "$f" "$model" "$venv/models" <<'PY'
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
  local rc=$?
  exec 9>&-
  return $rc
}

if [ -n "${2:-}" ]; then
  # An explicit model: local faster-whisper (e.g. large-v3 for the best quality; it detects the language).
  whisper_local "$2" || { echo "No local Whisper at ${WHISPER_VENV:-$HOME/whisper}, or it failed (see docs/voice.md)" >&2; exit 1; }
  done_with "whisper-$2"; exit 0
fi
if groq; then done_with groq
elif cloudflare; then done_with cloudflare
elif parakeet; then done_with parakeet-local
elif [ "${TRANSCRIBE_NO_LOCAL:-}" != 1 ] && whisper_local "${TRANSCRIBE_LOCAL_MODEL:-large-v3-turbo}"; then
  done_with "whisper-${TRANSCRIBE_LOCAL_MODEL:-large-v3-turbo}"
else
  echo "(Could not transcribe the audio: no engine configured or all of them failed; see docs/voice.md)" >&2; exit 1
fi
