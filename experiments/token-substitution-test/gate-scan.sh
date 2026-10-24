#!/usr/bin/env bash
# UTOK1: byte-for-byte the HARD-FAIL scan from orchestration/units/UBUILD1.build.sh (gate.sh).
ROOT="${1:?usage: gate-scan.sh <tree>}"; SELF="$(basename "$0")"
HARD="$(mktemp)"; REVIEW="$(mktemp)"; trap 'rm -f "$HARD" "$REVIEW"' EXIT
cat >"$HARD" <<'PATTERNS_HARD'
/home/zer0null
duval
a5ef1b28
89003e70
publish-present-compete
consonance
EXCLUDED.md
REDACTION_REPORT
RESIDUALS.md
LICENCE_TODO
TRADE_SECRET
WITHHELD.md
DISCLOSURE_INVENTORY
EXPOSURE_CLOSURE
ARCHIVE_WINDOW
VERIFICATION_REPORT
StateClass
grantPolicy
src/broker
src/scope
src/layer
CommitRecord
admit(
expanded[
PATTERNS_HARD
cat >"$REVIEW" <<'PATTERNS_REVIEW'
src/
dag.ts
store.ts
DecisionKind
memory.admission
capability.family
PATTERNS_REVIEW
scan() { ( cd "$ROOT" && grep -rn -I -i -F -f "$1" . --exclude-dir=.git --exclude="$SELF" ) 2>/dev/null || true; }
hard="$(scan "$HARD")"; rev="$(scan "$REVIEW")"
hn=0; [ -n "$hard" ] && hn="$(printf '%s\n' "$hard" | wc -l)"
rn=0; [ -n "$rev" ]  && rn="$(printf '%s\n' "$rev"  | wc -l)"
echo "EXCLUSION GATE (UBUILD1 hard-fail list) — $ROOT"
echo "HARD-FAIL hit LINES: $hn"
echo "-- HARD-FAIL hits by pattern (n>0) --"
while IFS= read -r p; do [ -n "$p" ] || continue
  c="$(printf '%s\n' "$hard" | grep -c -i -F -- "$p" || true)"
  [ "$c" -gt 0 ] && printf '%5s  %s\n' "$c" "$p"
done <"$HARD"
echo "REVIEW hit LINES (report only): $rn"
echo "HARD-FAIL files:"; printf '%s\n' "$hard" | sed 's/:[0-9]*:.*//' | sort | uniq -c | sort -rn
