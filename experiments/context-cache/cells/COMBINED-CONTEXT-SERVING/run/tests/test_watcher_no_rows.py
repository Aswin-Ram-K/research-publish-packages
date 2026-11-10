import json
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

CELL = Path(__file__).resolve().parents[2]
WATCHER = CELL / "tools" / "watcher.py"


def test_watcher_missing_rows_no_exception(tmp_path):
    rows = tmp_path / "does_not_exist.jsonl"  # deliberately absent
    out = tmp_path / "events.jsonl"
    log = tmp_path / "run.log"
    log.write_text("")
    deadline = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat().replace("+00:00", "Z")
    proc = subprocess.Popen(
        [sys.executable, str(WATCHER),
         "--rows", str(rows), "--log", str(log),
         "--stall-minutes", "10", "--deadline-utc", deadline,
         "--out", str(out), "--interval-seconds", "0.5"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    time.sleep(1.6)
    proc.terminate()
    proc.wait(timeout=5)
    stderr = proc.stderr.read().decode()
    assert stderr == "", stderr
    events = [json.loads(ln) for ln in out.read_text().splitlines() if ln.strip()]
    assert len(events) >= 1
    assert any("NO_ROWS_YET" in e.get("alerts", []) for e in events)
