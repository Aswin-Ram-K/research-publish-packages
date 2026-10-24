#!/usr/bin/env python3
"""WIN-SGL driver — three SGLang pager configurations, restored after each.

Sequence (strictly serial, one configuration at a time):

    stop production  ->  create+start variant on :8012  ->  bounded health poll
    ->  /get_server_info capture  ->  cell (battery 888 + grid probe 12)
    ->  remove variant  ->  start production  ->  health 200  ->  /get_server_info
    ->  diff against the pre-capture on the five restore keys

The restore lives in a ``try/finally`` for every configuration, so a variant that
dies, a health timeout, a cell that raises, or an operator interrupt all end with
``docker start gx10-occamy-nvfp4`` and a verified snapshot.  A configuration that
leaves production down is a failed unit; the restore verdict is written to
``logs/<config>-restore-verify.json`` in every case.

Request bound: 1800 live requests across all three configurations, allocated
dynamically (``min(900, 1800 - spent)``).  S3 is a launch attempt only; if the
flag is rejected -- which is the documented expectation for a non-DeepSeek hybrid
checkpoint -- the verbatim ``docker logs`` tail is the result and no requests are
spent on it.

Usage::

    python run_unit.py                 # the full unit
    python run_unit.py --only S1       # one configuration (debug/recovery)
    python run_unit.py --analysis-only # no containers touched
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Sequence

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
LOGS = HERE / "logs"
STATE_CONFIG = REPO / "state" / "config"
PYTHON = str(REPO / ".venv" / "bin" / "python")

sys.path.insert(0, str(HERE))
import launch_variant as lv  # noqa: E402

CONFIGS: tuple[dict[str, Any], ...] = (
    {"config_id": "S1", "page_size": 64, "flag": "--page-size=64",
     "label": "page_size 64 (pager aligned to the 64-token state chunk)"},
    {"config_id": "S2", "page_size": 128, "flag": "--page-size=128",
     "label": "page_size 128 (is 64 the granularity or a point on a curve)"},
    {"config_id": "S3", "page_size": None, "flag": "--enable-chunked-prefix-cache",
     "label": "enable-chunked-prefix-cache (documented DeepSeek/MLA-only, one attempt)"},
)
TOTAL_BOUND = 1800
PER_CONFIG = 900
MIN_CELL_REQUESTS = 24


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def run_cell(config: dict[str, Any], page_size: int, cap: int) -> dict[str, Any]:
    summary_path = LOGS / f"{config['config_id']}-cell.json"
    cmd = [
        PYTHON, str(HERE / "win_sgl_cell.py"),
        "--config-id", config["config_id"],
        "--page-size", str(page_size),
        "--cap", str(cap),
        "--server-info", str(STATE_CONFIG / f"{config['config_id']}-server-info.json"),
        "--out", str(summary_path),
    ]
    log(f"cell start {config['config_id']} cap={cap}")
    cp = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
    (LOGS / f"{config['config_id']}-cell.log").write_text(
        (cp.stdout or "") + (("\n[stderr]\n" + cp.stderr) if cp.stderr.strip() else ""), encoding="utf-8")
    summary = json.loads(summary_path.read_text(encoding="utf-8")) if summary_path.exists() else {
        "status": "failed", "requests_live": 0, "returncode": cp.returncode}
    log(f"cell done {config['config_id']}: status={summary.get('status')} "
        f"requests={summary.get('requests_live')} rc={cp.returncode}")
    return summary


def run_one(config: dict[str, Any], pre_info: dict[str, Any], spent: int) -> dict[str, Any]:
    config_id = config["config_id"]
    name = f"{lv.PRODUCTION}-{config_id.lower()}"
    record: dict[str, Any] = {
        "unit": "WIN-SGL", "config_id": config_id, "flag": config["flag"],
        "label": config["label"], "container": name, "page_size_requested": config["page_size"],
        "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    server_info_path = STATE_CONFIG / f"{config_id}-server-info.json"
    variant_launched = False
    try:
        # 1. production must be stopped before the variant can claim :8012
        log(f"stopping production unit ({lv.SERVICE})")
        record["production_status_before"] = lv.service_stop()
        if record["production_status_before"] not in ("exited", "absent"):
            raise RuntimeError(f"production did not stop: {record['production_status_before']}")

        # 2. build + create + start the variant from the inspected spec
        log(f"launching variant {name} with {config['flag']}")
        variant_launched = True
        rc = lv.main(["--config-id", config_id, "--flag=" + config["flag"], "--apply", "--name", name])
        record["create_returncode"] = rc
        if rc != 0:
            record["launch"] = "create_failed"
            record["startup_failure_log"] = f"logs/{config_id}-startup-failure.log"
            (LOGS / f"{config_id}-startup-failure.log").write_text(
                lv.docker_logs_tail(name, 40), encoding="utf-8")
            return record

        # 3. bounded health poll
        health = lv.wait_health(name, deadline_s=900.0, poll_s=5.0)
        record["health"] = health
        if not health.get("ok"):
            log(f"{config_id} did not become healthy: {health.get('reason')}")
            record["launch"] = "startup_failed"
            record["startup_failure_log"] = f"logs/{config_id}-startup-failure.log"
            (LOGS / f"{config_id}-startup-failure.log").write_text(
                lv.docker_logs_tail(name, 40), encoding="utf-8")
            return record

        # 4. this configuration's server-info capture (rows carry its sha256)
        info = lv.capture_server_info(server_info_path)
        reported_page_size = info.get("page_size")
        record["launch"] = "ok"
        record["reported_page_size"] = reported_page_size
        record["page_size_effective"] = (reported_page_size == config["page_size"]
                                         if config["page_size"] is not None else None)
        record["server_info"] = {
            k: info.get(k) for k in ("page_size", "c128_page_size", "mem_fraction_static",
                                     "mamba_radix_cache_strategy", "mamba_track_interval",
                                     "max_mamba_cache_size", "disable_chunked_prefix_cache",
                                     "max_total_num_tokens", "chunked_prefill_size")
        }
        record["server_info_path"] = str(server_info_path.relative_to(REPO))
        log(f"{config_id} healthy in {health['seconds']}s; page_size={reported_page_size}")

        # 5. the cell, with whatever budget remains
        cap = min(PER_CONFIG, TOTAL_BOUND - spent)
        record["cell_cap"] = cap
        if cap < MIN_CELL_REQUESTS:
            record["cell"] = {"status": "skipped", "reason": f"only {cap} requests left of {TOTAL_BOUND}"}
            log(f"{config_id}: cell skipped, cap left {cap}")
            return record
        cell = run_cell(config, int(reported_page_size or config["page_size"] or 1), cap)
        record["cell"] = {k: cell.get(k) for k in
                          ("status", "requests_live", "requests_cap", "battery", "probe", "reason", "notes")}
        return record
    except Exception as exc:  # noqa: BLE001 -- the finally below still restores production
        record["error"] = f"{type(exc).__name__}: {exc}"
        log(f"{config_id} ERROR: {record['error']}")
        return record
    finally:
        # restore discipline: never leave production down, whatever happened
        if variant_launched:
            try:
                lv.remove_container(name)
            except Exception as exc:  # noqa: BLE001
                record.setdefault("cleanup_errors", []).append(f"remove: {exc}")
        log(f"restoring production ({lv.PRODUCTION})")
        try:
            record["production_status_after"] = lv.service_start()
            record["production_unit_after"] = lv.service_state()
            restore_health = lv.wait_health(lv.PRODUCTION, deadline_s=900.0, poll_s=5.0)
            record["restore_health"] = restore_health
            post_info = lv.get_server_info() if restore_health.get("ok") else {}
            if post_info:
                write_json(LOGS / f"{config_id}-restore-server-info.json", post_info)
            diff = lv.restore_diff(pre_info, post_info)
            record["restore"] = {"ok": bool(diff["ok"]) and bool(restore_health.get("ok")),
                                 "config_ok": diff["config_ok"], "keys": diff["keys"],
                                 "token_capacity": diff["token_capacity"], "health": restore_health,
                                 "server_info": str((LOGS / f'{config_id}-restore-server-info.json')
                                                    .relative_to(REPO)) if post_info else None}
            write_json(LOGS / f"{config_id}-restore-verify.json", record["restore"])
            log(f"restore {config_id}: ok={record['restore']['ok']} health={restore_health.get('health')}")
        except Exception as exc:  # noqa: BLE001
            record["restore"] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
            log(f"restore FAILED for {config_id}: {exc}")
        record["finished_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        write_json(LOGS / f"{config_id}-config.json", record)


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="WIN-SGL: three pager configs, restore after each")
    ap.add_argument("--only", help="S1 / S2 / S3")
    ap.add_argument("--analysis-only", action="store_true")
    args = ap.parse_args(argv)

    if args.analysis_only:
        cp = subprocess.run([PYTHON, str(HERE / "win_sgl_analyze.py")], capture_output=True, text=True)
        print(cp.stdout, cp.stderr)
        return cp.returncode

    LOGS.mkdir(parents=True, exist_ok=True)
    pre_info = json.loads((STATE_CONFIG / "S0-server-info.json").read_text(encoding="utf-8"))

    # The live container is owned by a systemd USER unit (Restart=on-failure,
    # --rm); container-level stop cannot hold :8012 free.  Refuse to start the
    # unit work unless that unit is the thing running production.
    state = lv.service_state()
    log(f"production owner: systemd --user unit {lv.SERVICE} is {state}")
    if state != "active":
        log("production unit is not active -- aborting before any variant")
        write_json(LOGS / "run.json", {"aborted": f"unit {lv.SERVICE} is {state}"})
        return 1
    restore_baseline = pre_info
    spend = {"requests": 0, "configs": {}}

    targets = [c for c in CONFIGS if not args.only or c["config_id"] == args.only]
    log(f"unit start: {[c['config_id'] for c in targets]} bound={TOTAL_BOUND}")
    try:
        for config in targets:
            record = run_one(config, restore_baseline, spend["requests"])
            spend["configs"][config["config_id"]] = {
                "requests": (record.get("cell") or {}).get("requests_live") or 0,
                "launch": record.get("launch"),
                "restore_ok": (record.get("restore") or {}).get("ok"),
            }
            spend["requests"] += (record.get("cell") or {}).get("requests_live") or 0
            write_json(LOGS / "spend.json", spend)
            log(f"spent {spend['requests']}/{TOTAL_BOUND} after {config['config_id']}")
    finally:
        # belt and braces: the per-config finally already started production;
        # this catches a crash between configurations.
        try:
            if not lv.health():
                log("production not healthy at end of run -> starting it")
                lv.start_container(lv.PRODUCTION)
                lv.wait_health(lv.PRODUCTION, deadline_s=900.0, poll_s=5.0)
        except Exception as exc:  # noqa: BLE001
            log(f"end-of-run production check failed: {exc}")

    cp = subprocess.run([PYTHON, str(HERE / "win_sgl_analyze.py")], capture_output=True, text=True)
    print(cp.stdout[-4000:], cp.stderr[-2000:])
    write_json(LOGS / "run.json", {"spend": spend, "analysis_rc": cp.returncode,
                                    "finished_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})
    log(f"unit done: requests={spend['requests']}/{TOTAL_BOUND}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
