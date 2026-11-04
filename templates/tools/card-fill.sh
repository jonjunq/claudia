#!/bin/bash
# Saves the details of the assistant's limited virtual card (docs/permissions.md#optional-paying-with-a-limited-card)
# to ~<user>/.config/assistant/card.env, mode 600, without them passing through a chat, the command line or the
# shell history: the number and the security code are read without echo. Run it yourself, as root or as that user,
# never through the assistant.
#   card-fill.sh <user> [last-4-digits-to-check]
set -euo pipefail
U="${1:-}"; LAST4="${2:-}"
[ -n "$U" ] || { sed -n '2,6p' "$0"; exit 1; }
H=$(getent passwd "$U" | cut -d: -f6) || { echo "No such user: $U" >&2; exit 1; }
[ "$(id -u)" -eq 0 ] || [ "$(id -un)" = "$U" ] || { echo "Run it as root or as $U" >&2; exit 1; }
read -rsp "Card number (not shown): " N; echo; N=${N//[ -]/}
read -rp  "Expiry (MM/YY): " E
read -rsp "Security code (not shown): " C; echo
read -rp  "Name on the card: " NAME
[[ $N =~ ^[0-9]{13,19}$ ]] || { echo "The number must have 13 to 19 digits" >&2; exit 1; }
[ -z "$LAST4" ] || [ "${N: -4}" = "$LAST4" ] || { echo "The number does not end in $LAST4" >&2; exit 1; }
[[ $E =~ ^(0[1-9]|1[0-2])/[0-9]{2}$ ]] || { echo "Expiry must be MM/YY" >&2; exit 1; }
[[ $C =~ ^[0-9]{3,4}$ ]] || { echo "The security code has 3 or 4 digits" >&2; exit 1; }
[[ $NAME =~ ^[[:alpha:][:space:].\'-]+$ ]] || { echo "The name may only have letters, spaces, dots, hyphens and apostrophes" >&2; exit 1; }
F="$H/.config/assistant/card.env"
install -d -m 700 "$(dirname "$F")"
( umask 077
  printf '# The assistant'"'"'s virtual card (ends in %s). Read it into variables; never print it.\nCARD_NUMBER=%s\nCARD_EXPIRY=%s\nCARD_CVC=%s\nCARD_NAME="%s"\n' \
    "${N: -4}" "$N" "$E" "$C" "$NAME" > "$F" )
[ "$(id -u)" -eq 0 ] && chown "$U": "$(dirname "$F")" "$F"
chmod 600 "$F"
echo "Saved $F (card ending in ${N: -4}, mode $(stat -c %a "$F"))."
unset N E C NAME
