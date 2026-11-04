#!/bin/bash
# Rebuilds the README diagram: the GitHub Pages pages, the skill's checks, and the light/dark SVGs with their
# fonts embedded. Needs Python 3, the diagram-design skill (DIAGRAM_DESIGN, default
# ~/.claude/skills/diagram-design) and network access to fonts.googleapis.com for the font subsets.
set -euo pipefail
cd "$(dirname "$(readlink -f "$0")")"
SKILL=${DIAGRAM_DESIGN:-$HOME/.claude/skills/diagram-design}
S=$SKILL/scripts
[ -f "$S/export_svg.py" ] || { echo "diagram-design not found in $SKILL (set DIAGRAM_DESIGN)" >&2; exit 1; }
# verify-geometry.py lives in the skill's repository, not in the installed skill: point VERIFY_GEOMETRY at it.
VG=${VERIFY_GEOMETRY:-$S/verify-geometry.py}

python3 how-it-works.py .
pages=(how-it-works.html how-it-works.es.html build/how-it-works-light.html build/how-it-works-dark.html
       build/how-it-works-light-es.html build/how-it-works-dark-es.html)
python3 "$S/self_check.py" "${pages[@]}"
if [ -f "$VG" ]; then python3 "$VG" "${pages[@]}"; else echo "skipped verify-geometry.py (not found: $VG)" >&2; fi

for n in light dark light-es dark-es; do
  python3 "$S/export_svg.py" --system-fonts "build/how-it-works-$n.html" "build/how-it-works-$n.svg"
  python3 embed-fonts.py "build/how-it-works-$n.svg" "how-it-works-${n/-es/.es}.svg"
done
