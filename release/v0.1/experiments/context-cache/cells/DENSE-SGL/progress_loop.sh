#!/usr/bin/env bash
# DENSE-SGL battery progress feeder: reports row count against the 950 cap.
set -u
CELL="<workspace>"
ROWS="$CELL/rows.jsonl"
TASK="${1:?task id}"
CLI="${DSH_PROGRESS_CLI:?}"
CAP=950
while true; do
  if [ -f "$ROWS" ]; then
    n=$(wc -l < "$ROWS" | tr -d ' ')
    pct=$(( n * 100 / CAP ))
    [ "$pct" -gt 99 ] && pct=99
    node "$CLI" emit --task "$TASK" --pct "$pct" --msg "battery rows $n/$CAP" >/dev/null 2>&1 || true
  fi
  sleep 15
done
