#!/usr/bin/env python3
"""MOE-VLLM — live driver: hold .occamy.lock across launch -> gate/probe/battery -> restore.

Why a driver instead of three shell commands: the lock must span the whole live
phase (the production vLLM container is stopped for the variant's lifetime), and
the production restore must happen even if the battery fails.  The cell script
is invoked with --no-lock because THIS process holds the flock; a second flock
from a child process would deadlock.

Writes logs/live-run.json: timings, launch/restore verdicts, row count, rows
sha256, and the production/occamy healthes before and after.

Usage: .venv/bin/python run_moe_live.py [--skip-launch] [--cell-phase all]
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
LOGS = HERE / "logs"
ROWS = HERE / "rows.jsonl"
LOCK = REPO / "experiments" / "context-cache" / ".occamy.lock"
PY = str(REPO / ".venv" / "bin" / "python")
sys.path.insert(0, str(HERE))

import launch_moe_vllm as lv  # noqa: E402


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def run(cmd: list[str], timeout: int) -> tuple[int, str]:
    print(f"$ {' '.join(cmd)}", flush=True)
    proc = subprocess.run(cmd, cwd=str(REPO), capture_output=True, text=True, timeout=timeout)
    tail = (proc.stdout or "")[-6000:] + (proc.stderr or "")[-2000:]
    print(tail, flush=True)
    return proc.returncode, tail


def state() -> dict:
    return {"prod_health": lv.lv.health(lv.lv.PROD_PORT),
            "prod_models": lv.capture_models(lv.lv.PROD_PORT),
            "occamy": lv.lv.occamy_health()}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-launch", action="store_true")
    ap.add_argument("--cell-phase", default="all")
    ap.add_argument("--fresh", action="store_true", help="archive an existing rows.jsonl first")
    args = ap.parse_args()
    LOGS.mkdir(parents=True, exist_ok=True)

    if args.fresh and ROWS.exists() and ROWS.stat().st_size:
        arch = LOGS / f"rows-prev-{utc_now().replace(':', '')}.jsonl"
        ROWS.replace(arch)
        print(f"archived previous rows -> {arch}", flush=True)

    record: dict = {"unit": "MOE-VLLM", "phase": "live", "started_utc": utc_now(),
                    "commands": [], "steps": []}
    lock_handle = LOCK.open("a+", encoding="utf-8")
    waited = time.monotonic()
    while True:
        try:
            fcntl.flock(lock_handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            break
        except BlockingIOError:
            if time.monotonic() - waited > 900:
                print("LOCK TIMEOUT after 900s", flush=True)
                return 5
            time.sleep(0.5)
    lock_handle.seek(0)
    lock_handle.truncate()
    json.dump({"unit": "MOE-VLLM", "pid": os.getpid(), "note": "full live phase",
               "acquired_utc": utc_now()}, lock_handle)
    lock_handle.flush()
    os.fsync(lock_handle.fileno())
    record["lock_wait_s"] = round(time.monotonic() - waited, 1)
    print(f"lock acquired after {record['lock_wait_s']}s", flush=True)

    launch_rec = None
    restore_rec = None
    try:
        record["pre"] = state()
        print(json.dumps(record["pre"], indent=1)[:800], flush=True)

        if not args.skip_launch:
            t0 = time.monotonic()
            launch_rec = lv.launch("V3", timeout_s=480)
            record["launch"] = {"launched": bool(launch_rec.get("launched")),
                                "health_status": launch_rec.get("health_status"),
                                "health_wait_s": launch_rec.get("health_wait_s"),
                                "spec_sha256": launch_rec.get("spec", {}).get("config_sha256"),
                                "seconds": round(time.monotonic() - t0, 1)}
            record["commands"].append("launch_moe_vllm.py --launch (V3)")
            if not launch_rec.get("launched"):
                record["result"] = "launch-failed"
                print("LAUNCH FAILED", flush=True)
                return 2

        t0 = time.monotonic()
        rc, tail = run([PY, str(HERE / "moe_vllm_cell.py"), "--config", "V3",
                        "--phase", args.cell_phase, "--port", "8020", "--no-lock"],
                       timeout=5400)
        record["cell"] = {"rc": rc, "seconds": round(time.monotonic() - t0, 1), "tail": tail[-3000:]}
        record["commands"].append(f"moe_vllm_cell.py --config V3 --phase {args.cell_phase} "
                                  f"--port 8020 --no-lock")
        if rc != 0:
            record["result"] = "cell-failed"
    finally:
        # Restore production even after a cell failure: the variant owns :8014's
        # predecessor container slot and production must come back.
        try:
            restore_rec = lv.restore("V3")
            record["restore"] = {"config_ok": bool(restore_rec.get("config_ok")),
                                 "health": restore_rec.get("health"),
                                 "models_id": (restore_rec.get("models") or {}).get("id"),
                                 "max_model_len": (restore_rec.get("models") or {}).get("max_model_len"),
                                 "occamy": (restore_rec.get("occamy") or {}).get("status")}
            record["commands"].append("launch_moe_vllm.py --restore (V3)")
        except Exception as exc:  # noqa: BLE001 - restore failure must be recorded, not raised
            record["restore"] = {"error": f"{type(exc).__name__}: {exc}"}
        record["post"] = state()
        lock_handle.seek(0)
        lock_handle.truncate()
        json.dump({"unit": "MOE-VLLM", "pid": os.getpid(), "note": "released",
                   "released_utc": utc_now()}, lock_handle)
        lock_handle.flush()
        os.fsync(lock_handle.fileno())
        fcntl.flock(lock_handle, fcntl.LOCK_UN)
        lock_handle.close()

    rows = [json.loads(line) for line in ROWS.read_text(encoding="utf-8").splitlines() if line.strip()] \
        if ROWS.exists() else []
    record["rows"] = {"n": len(rows),
                      "sha256": sha256_file(ROWS),
                      "status": {str(s): sum(1 for r in rows if r.get("status") == s)
                                 for s in sorted({r.get("status") for r in rows})},
                      "by_phase": {p: sum(1 for r in rows if r.get("phase") == p)
                                   for p in sorted({r.get("phase") for r in rows})}}
    record["finished_utc"] = utc_now()
    record.setdefault("result", "done")
    out = LOGS / "live-run.json"
    tmp = out.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    tmp.replace(out)
    print(json.dumps({"result": record["result"], "rows": record["rows"],
                      "restore": record.get("restore")}, indent=1), flush=True)
    return 0 if record["result"] == "done" else 1


if __name__ == "__main__":
    raise SystemExit(main())
