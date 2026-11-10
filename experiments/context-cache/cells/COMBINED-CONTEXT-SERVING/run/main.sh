#!/usr/bin/env bash
set -u
CELL="$(cd "$(dirname "$0")/.." && pwd)"
cd "$CELL" || exit 1
LOG="$CELL/run/MAIN.log"
: > "$LOG"
stamp() { date -u '+%Y-%m-%dT%H:%M:%SZ'; }
mkdir -p "$CELL/watcher" "$CELL/run"
: > "$CELL/run/main-watcher.out"
: > "$CELL/run/main-driver.log"
EVENTS="$CELL/watcher/main-events.jsonl"
: > "$EVENTS"

watcher_started_utc=""
driver_started_utc=""
driver_exit_utc=""

driver_started_utc="$(stamp)"
python3 run/driver.py --rows rows/ccs.jsonl --watcher-events "$EVENTS" > run/main-driver.log 2>&1 &
dpid=$!
echo "$dpid" > run/driver.pid

watcher_started_utc="$(stamp)"
python3 tools/watcher.py --rows rows/ccs.jsonl --log run/main-driver.log \
  --pid "$dpid" --stall-minutes 10 \
  --deadline-utc "$(date -u -d '+3 hours' '+%Y-%m-%dT%H:%M:%SZ')" \
  --out "$EVENTS" --interval-seconds 120 > run/main-watcher.out 2>&1 &
wpid=$!
echo "$wpid" > run/watcher.pid

# continuous supervision on 120s cadence
watcher_died=0
while kill -0 "$dpid" 2>/dev/null; do
    if ! kill -0 "$wpid" 2>/dev/null; then
        watcher_died=1
        python3 - "$EVENTS" <<'PY'
import json, sys, datetime
p = sys.argv[1]
ev = {"timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
      "rows": 0, "delta": 0, "error_rows": 0, "exit_status": "gone",
      "alerts": ["PROCESS_VANISHED"]}
with open(p, "a") as f:
    f.write(json.dumps(ev) + "\n")
PY
        kill "$dpid" 2>/dev/null
        break
    fi
    sleep "${CCS_SUPERVISION_INTERVAL:-120}"
done

wait "$dpid"
rc=$?
driver_exit_utc="$(stamp)"

# stop watcher
kill "$wpid" 2>/dev/null
wait "$wpid" 2>/dev/null
wexit=$?

watcher_was_alive=1
if [ "$watcher_died" -eq 1 ]; then
    watcher_was_alive=0
fi
# if watcher already gone before kill, mark died
if ! kill -0 "$wpid" 2>/dev/null; then
    if [ "$wexit" -ne 0 ] && [ "$wexit" -ne 143 ]; then
        watcher_died=1
        watcher_was_alive=0
    fi
fi

alerts_json=$(python3 - "$EVENTS" <<'PY'
import json, sys
p = sys.argv[1]
alerts = []
try:
    with open(p) as f:
        for line in f:
            line=line.strip()
            if not line: continue
            try:
                o = json.loads(line)
                for a in o.get("alerts", []):
                    if a not in alerts:
                        alerts.append(a)
            except Exception:
                pass
except FileNotFoundError:
    pass
print(json.dumps(alerts))
PY
)

watcher_alive_throughout=0
if [ "$watcher_died" -eq 0 ]; then
    watcher_alive_throughout=1
fi

python3 - "$CELL/run/MAIN-SUPERVISION.json" "$watcher_started_utc" "$wexit" "$driver_started_utc" "$driver_exit_utc" "$alerts_json" "$watcher_alive_throughout" "$watcher_was_alive" "$watcher_died" <<'PY'
import json, sys
out, ws, we, ds, de, alerts, alive_throughout, was_alive, died = sys.argv[1:]
data = {
    "watcher_started_utc": ws,
    "watcher_exit_code": int(we),
    "driver_started_utc": ds,
    "driver_exit_utc": de,
    "alerts": json.loads(alerts),
    "watcher_alive_throughout": bool(int(alive_throughout)),
    "watcher_was_alive": bool(int(was_alive)),
    "watcher_died_before_driver": bool(int(died)),
}
open(out, "w").write(json.dumps(data, indent=2) + "\n")
PY

echo "$(stamp) driver exit $rc" >> "$LOG"
echo "$(stamp) watcher exit $wexit" >> "$LOG"
echo "$(stamp) done" >> "$LOG"

if [ "$watcher_was_alive" -eq 0 ]; then
    exit 1
fi
exit "$rc"
