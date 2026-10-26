#!/usr/bin/env python3
"""Capacity-only pass for the three TRACK-INTERVAL arms.

The first driver pass measured the five prompt arms but its capacity probe
overran the 131072 context (hex filler is ~1.15 chars/token, so the 4-chars/token
estimate built a 343k-token document and the server answered 400).  This pass
re-launches each interval, runs the corrected probe, and restores production.
"""

from __future__ import annotations

import fcntl
import importlib.util
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load_mod(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


RT = load_mod("rt_capacity", HERE / "run_track.py")
RT.Budget.n = int(os.environ.get("TRACK_REQUESTS_SO_FAR", "1080"))


def run(n: int) -> dict:
    name = f"gx10-occamy-nvfp4-t{n}"
    rec: dict = {"arm": n, "interval": n, "stage": "capacity-only", "started_utc": RT.now()}
    RT.log(f"CAP {n}: stop production")
    rec["production_stopped_status"] = RT.LV.service_stop()
    if rec["production_stopped_status"] != "absent":
        rec.update({"ok": False, "abort_all": True,
                    "error": f"production not absent: {rec['production_stopped_status']}"})
        return rec
    reused = False
    if RT.LV.container_status(name) == "running":
        try:
            reused = RT.LV.get_server_info().get("mamba_track_interval") == n
        except Exception:  # noqa: BLE001
            reused = False
        rec["reused_running_variant"] = reused
    if not reused:
        RT.LV.remove_container(name)
        cmd = RT.LV.build_cmd(RT.SPEC["Config"]["Cmd"], [("--mamba-track-interval", str(n))])
        cp = RT.LV.ssh_run(RT.LV.docker_create_argv(RT.SPEC, name, cmd), timeout=180.0)
        if cp.returncode != 0:
            rec.update({"ok": False, "error": f"docker create failed: {cp.stderr.strip()[:500]}"})
            return rec
        cp = RT.LV.ssh_run(["docker", "start", name], timeout=180.0)
        if cp.returncode != 0:
            rec.update({"ok": False, "error": f"docker start failed: {cp.stderr.strip()[:500]}",
                        "logs": RT.LV.docker_logs_tail(name, 40)})
            return rec
    rec["health"] = RT.LV.wait_health(name, deadline_s=900.0)
    if not rec["health"].get("ok"):
        rec.update({"ok": False, "error": "variant never became healthy",
                    "logs": RT.LV.docker_logs_tail(name, 60)})
        return rec
    info = RT.LV.capture_server_info(RT.STATE / f"track-{n}.json")
    rec["server_info"] = {k: info.get(k) for k in RT.INFO_KEYS}
    if info.get("mamba_track_interval") != n:
        rec.update({"ok": False, "error": "flag did not take effect",
                    "observed": info.get("mamba_track_interval")})
        return rec
    RT.log(f"CAP {n}: probe at ~1.5x capacity={info.get('max_total_num_tokens')}")
    rec["capacity"] = RT.capacity_probe(info, n)
    RT.log(f"CAP {n}: resident_docs={rec['capacity'].get('resident_docs')} "
           f"probe_ok={rec['capacity'].get('ok')}")
    RT.LV.remove_container(name)
    rec["variant_removed"] = RT.LV.container_status(name)
    rec["production_unit"] = RT.LV.service_start()
    rec["production_health"] = RT.LV.wait_health(RT.LV.PRODUCTION, deadline_s=900.0)
    if rec["production_health"].get("ok"):
        post = RT.LV.capture_server_info(RT.STATE / f"track-restore-{n}.json")
        rec["restore_keys"] = {k: {"live": post.get(k), "expected": v, "ok": post.get(k) == v}
                               for k, v in RT.BASELINE.items()}
        rec["restore_ok"] = all(x["ok"] for x in rec["restore_keys"].values())
        rec["restore_max_total_num_tokens"] = post.get("max_total_num_tokens")
    else:
        rec.update({"restore_ok": False, "abort_all": True,
                    "error": "production did not come back healthy"})
    return rec


def main() -> int:
    lock = RT.LOCK_PATH.open("a+", encoding="utf-8")
    fcntl.flock(lock, fcntl.LOCK_EX)
    lock.seek(0)
    lock.truncate()
    json.dump({"unit": "TRACK-INTERVAL", "pid": os.getpid(), "acquired_utc": RT.now(),
               "scope": "capacity-only pass"}, lock)
    lock.flush()
    os.fsync(lock.fileno())
    results = []
    try:
        for n in (256, 128, 64):
            done_path = HERE / f"arm-{n}-capacity.json"
            if done_path.exists():
                try:
                    prior = json.loads(done_path.read_text())
                except Exception:  # noqa: BLE001
                    prior = {}
                if prior.get("capacity", {}).get("ok") and prior.get("restore_ok"):
                    RT.log(f"CAP {n}: already done, skipping")
                    results.append(prior)
                    continue
            rec = run(n)
            results.append(rec)
            (HERE / f"arm-{n}-capacity.json").write_text(json.dumps(rec, indent=2) + "\n")
            arm = HERE / f"arm-{n}.json"
            if arm.exists():
                data = json.loads(arm.read_text())
                data["capacity"] = rec.get("capacity")
                data["capacity_pass"] = {"health": rec.get("health"),
                                         "restore_ok": rec.get("restore_ok"),
                                         "server_info": rec.get("server_info")}
                arm.write_text(json.dumps(data, indent=2) + "\n")
            RT.log(f"CAP {n} done: ok={rec.get('capacity', {}).get('ok')} "
                   f"restore={rec.get('restore_ok')} requests={RT.Budget.n}")
            if rec.get("abort_all"):
                break
        (HERE / "capacity-summary.json").write_text(json.dumps(
            {"arms": results, "requests": RT.Budget.n, "finished_utc": RT.now()}, indent=2) + "\n")
    finally:
        lock.seek(0)
        lock.truncate()
        json.dump({"unit": "TRACK-INTERVAL", "pid": os.getpid(), "released_utc": RT.now()}, lock)
        lock.flush()
        os.fsync(lock.fileno())
        fcntl.flock(lock, fcntl.LOCK_UN)
        lock.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
