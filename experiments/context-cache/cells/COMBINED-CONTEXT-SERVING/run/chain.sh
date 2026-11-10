#!/usr/bin/env bash
# Preregistered chain: a two-call go/no-go probe, then the 144-call main run.
# The probe gates the main run: if either probe call fails to verify, the chain
# stops and records the negative result instead of spending the remaining budget.
set -u
CELL="$(cd "$(dirname "$0")/.." && pwd)"
cd "$CELL" || exit 1
LOG="$CELL/run/CHAIN.log"
: > "$LOG"

stamp() { date -u '+%Y-%m-%dT%H:%M:%SZ'; }

echo "$(stamp) probe start" >> "$LOG"
python3 run/calibrate5.py >> "$LOG" 2>&1
probe_rc=$?
echo "$(stamp) probe exit $probe_rc" >> "$LOG"

verified=$(python3 - <<'PY'
import json, os
rows = []
p = 'rows/cal6.jsonl'
if os.path.exists(p):
    rows = [json.loads(l) for l in open(p) if l.strip()]
print(sum(1 for r in rows if r.get('verified_success') is True))
PY
)
echo "$(stamp) probe verified=$verified" >> "$LOG"

if [ "$verified" -lt 2 ]; then
  echo "$(stamp) STOP: probe did not verify both calls; main run not started" >> "$LOG"
  exit 0
fi

echo "$(stamp) main run start" >> "$LOG"
python3 tools/watcher.py \
  --rows rows/ccs.jsonl \
  --log run/main-driver.log \
  --stall-minutes 10 \
  --deadline-utc "$(date -u -d '+4 hours' '+%Y-%m-%dT%H:%M:%SZ')" \
  --out watcher/ccs-events.jsonl \
  --interval-seconds 180 > run/main-watcher.out 2>&1 &
watcher_pid=$!
echo "$stamp watcher pid $watcher_pid" >> "$LOG"

python3 run/driver.py --rows rows/ccs.jsonl >> "$LOG" 2>&1
main_rc=$?
echo "$(stamp) main exit $main_rc" >> "$LOG"
kill "$watcher_pid" 2>/dev/null
echo "$(stamp) chain done" >> "$LOG"
