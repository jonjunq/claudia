#!/usr/bin/env bash
# Scan a skill repo or folder with NVIDIA SkillSpector before installing anything from it (static analysis only:
# --no-llm, no cost). Run it in a disposable VM or container, not on the assistant's machine.
# Usage: vet-skill.sh <git-url|folder> [commit]
#   commit: optional; checks out that exact commit (pin what you reviewed and install that same commit).
# Each folder with a SKILL.md (what actually gets installed) is scanned on its own; the whole repo is scanned too,
# but that score is dominated by false positives from docs, tests and CI: it tells you where to look, not a verdict.
# Reports go to $VET_REPORTS (default ~/skill-reports)/<name>-<date>/. The verdict is yours: read every finding.
set -uo pipefail
src=${1:?usage: vet-skill.sh <git-url|folder> [commit]}
ref=${2:-}
bin=${SKILLSPECTOR_BIN:-skillspector}
command -v "$bin" >/dev/null || { echo "SkillSpector not found: https://github.com/NVIDIA/SkillSpector" >&2; exit 1; }
name=$(basename "${src%.git}")
out=${VET_REPORTS:-$HOME/skill-reports}/$name-$(date +%F-%H%M)
mkdir -p "$out"
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

if [[ -d $src ]]; then
  cp -r "$src" "$work/$name"
elif [[ -n $ref ]]; then
  git clone -q "$src" "$work/$name" && git -C "$work/$name" checkout -q "$ref" || exit 1
else
  git clone -q --depth 1 "$src" "$work/$name" || exit 1
fi
git -C "$work/$name" log -1 --format="commit %H %cd" > "$out/commit.txt" 2>/dev/null

field() { grep -m1 "^| $1 " "$2" | cut -d"|" -f3 | xargs; }

printf "%-55s %-8s %-9s %s\n" SKILL SCORE SEVERITY RECOMMENDATION
while read -r f; do
  d=$(dirname "$f"); rel=${d#"$work/$name"/}
  [[ $d == "$work/$name" ]] && rel=.
  r="$out/skill-${rel//\//_}.md"
  "$bin" scan "$d" --no-llm --format markdown --output "$r" >/dev/null 2>&1
  printf "%-55s %-8s %-9s %s\n" "$rel" "$(field Score "$r")" "$(field Severity "$r")" "$(field Recommendation "$r")"
done < <(find "$work/$name" -name SKILL.md -not -path "*/node_modules/*" | sort)

"$bin" scan "$work/$name" --no-llm --format markdown --output "$out/whole-repo.md" >/dev/null 2>&1
echo
echo "Whole repo (indicative, many false positives): $(field Score "$out/whole-repo.md"), $(grep -c '^### ' "$out/whole-repo.md") findings"
echo "Reviewed: $(cat "$out/commit.txt" 2>/dev/null)"
echo "Reports: $out"
