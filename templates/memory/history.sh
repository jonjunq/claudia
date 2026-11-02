#!/bin/bash
# Git history, owned by root and out of the assistant's reach, of what the assistant knows:
# CLAUDE.md, notes, skills and memory. Run hourly by assistant-history.timer and around each nightly review.
#   history.sh <user> ["message"]      (no changes, no commit)
# See and undo: git --git-dir=/var/lib/assistant-history/<user> log --stat | show <commit> | checkout <commit> -- <path>
set -euo pipefail
U="${1:?usage: $0 <user> [message]}"
H="${ASSISTANT_HOME:-$(getent passwd "$U" | cut -d: -f6)}"
G="${ASSISTANT_HISTORY_DIR:-/var/lib/assistant-history/$U}"
# Claude Code's memory folder: the workspace path with every non-alphanumeric character turned into "-".
P=$(readlink -m "$H/assistant" | sed 's/[^A-Za-z0-9]/-/g')
g() { git --git-dir="$G" --work-tree="$H" -c safe.directory='*' -c user.name=assistant-history \
        -c user.email=history@localhost "$@"; }
if [ ! -d "$G" ]; then
  mkdir -p "$(dirname "$G")"
  git init -q --bare "$G"
  git --git-dir="$G" config core.bare false
  printf '%s\n' '*.bak-*' '*.json' '*.env' '*.lock' '*.review-tmp' > "$G/info/exclude"
  chmod 700 "$G"
fi
paths=()
for p in assistant/CLAUDE.md assistant/notes assistant/.claude/skills ".claude/projects/$P/memory"; do
  [ -e "$H/$p" ] && paths+=("$p")
done
[ ${#paths[@]} -gt 0 ] || exit 0
g add -A -- "${paths[@]}"
g diff --cached --quiet || g commit -q -m "${2:-hourly}"
