#!/bin/sh
# SafeBump check: read-only. Shows your OpenClaw version's verdict and explains your last update failure.
# Usage: curl -fsSL https://swarm-t3.github.io/safebump/check.sh | sh
# It only runs `openclaw --version` and `openclaw update status --json`. It changes nothing, and nothing leaves your machine.
BASE="https://swarm-t3.github.io/safebump"
command -v openclaw >/dev/null 2>&1 || { echo "openclaw is not on PATH. Run this as the user that owns your Gateway."; exit 1; }
VER=$(openclaw --version 2>/dev/null | grep -Eo '20[0-9]{2}\.[0-9]+\.[0-9]+(-beta\.[0-9]+)?' | head -1)
echo "SafeBump check"
echo "Installed OpenClaw: ${VER:-unknown}"
DATA=$(curl -fsSL "$BASE/data.json" 2>/dev/null)
if [ -n "$VER" ] && [ -n "$DATA" ]; then
  V=$(printf '%s' "$DATA" | tr -d '\n' | grep -Eo "\"version\": \"$VER\"[^}]*\"verdict\": \"[a-z-]+\"" | grep -Eo '"verdict": "[a-z-]+"' | cut -d'"' -f4)
  case "$V" in
    ok) echo "Verdict for $VER: no known blockers." ;;
    caution) echo "Verdict for $VER: caution, open crash/blocker issues exist." ;;
    hold) echo "Verdict for $VER: HOLD, open P0/crash-loop issues are reported against it." ;;
    too-new) echo "Verdict for $VER: too new, wait 48-72h." ;;
    *) echo "Verdict for $VER: not tracked (older release)." ;;
  esac
  echo "Details: $BASE/v/$VER.html"
fi
STATUS=$(openclaw update status --json 2>/dev/null)
CODES=$(curl -fsSL "$BASE/failures.json" 2>/dev/null | tr -d '\n' | grep -Eo '"codes": \{[^}]*\}' | grep -Eo '"[a-z][a-zA-Z:-]*": [0-9]+' | cut -d'"' -f2)
FOUND=""
for c in $CODES; do
  printf '%s' "$STATUS" | grep -q -- "$c" && { FOUND="$c"; break; }
done
if [ -n "$FOUND" ]; then
  SLUG=$(printf '%s' "$FOUND" | tr 'A-Z' 'a-z' | sed 's/[^a-z0-9-]/-/g')
  echo "Your last update recorded reason code: $FOUND"
  echo "What it means and what to do: $BASE/code/$SLUG.html"
elif printf '%s' "$STATUS" | grep -qi '"failed"'; then
  echo "Your last update failed, but the reason code is not one we track yet. See $BASE/failures.html"
else
  echo "No failed update recorded."
fi
echo
echo "Stuck? Update Rescue: fixed price, and you pay only once it works. $BASE/#rescue"
