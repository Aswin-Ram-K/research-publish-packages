#!/usr/bin/env python3
"""TRACK-INTERVAL driver - three restart-level --mamba-track-interval arms.

Owns experiments/context-cache/.occamy.lock for the whole card.  Per arm N:
  stop production (systemd --user unit) -> launch variant on :8012 with
  --mamba-track-interval N -> health <=900 s -> /get_server_info ->
  TRACK-INTERVAL cell (5 prompt arms x 71 turns = the PROMPT-O1 script) ->
  capacity probe at ~1.5x max_total_num_tokens -> drop the variant ->
  restore production -> verify the six baseline keys (+ interval 256).

Writes only: cells/TRACK-INTERVAL/**, state/config/track-*.json.
"""

from __future__ import annotations

import fcntl
import hashlib
import importlib.util
import json
import math
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
CELLS = REPO / "experiments" / "context-cache" / "cells"
LOCK_PATH = REPO / "experiments" / "context-cache" / ".occamy.lock"
STATE = REPO / "state" / "config"
ARMS = (256, 128, 64)
BASE_V1 = "http://192.168.2.168:8012/v1"
DOC_TARGET_TOKENS = 98304
BUDGET_REQUESTS = 1300
PROBE_CAP = 24
BASELINE = {
    "page_size": 1,
    "mamba_radix_cache_strategy": "extra_buffer",
    "radix_eviction_policy": "lru",
    "mem_fraction_static": 0.45,
    "kv_cache_dtype": "fp8_e4m3",
    "max_mamba_cache_size": 64,
    "mamba_track_interval": 256,
}
INFO_KEYS = list(BASELINE) + ["max_total_num_tokens", "max_running_requests",
                              "version", "served_model_name", "context_length"]


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def log(msg: str) -> None:
    print(f"{now()} {msg}", flush=True)


def load_mod(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


LV = load_mod("lv_track_interval", CELLS / "WIN-SGL" / "launch_variant.py")
SPEC = LV.load_spec()


class Budget:
    n = 0

    @classmethod
    def spend(cls, k: int = 1) -> None:
        cls.n += k
        if cls.n > BUDGET_REQUESTS:
            raise RuntimeError(f"request budget exhausted at {cls.n}")


def http_chat(messages: list[dict], max_tokens: int = 1, timeout: float = 1800.0) -> dict:
    body = json.dumps({"model": "occamy-1.0", "messages": messages,
                       "max_tokens": int(max_tokens), "temperature": 0.0}).encode()
    req = urllib.request.Request(BASE_V1 + "/chat/completions", data=body,
                                 headers={"Content-Type": "application/json"})
    Budget.spend()
    t0 = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode())
            code = int(resp.status)
    except urllib.error.HTTPError as exc:
        return {"http_status": exc.code, "prompt_tokens": None, "cached_tokens": None,
                "body": exc.read().decode()[:400], "wall_s": round(time.monotonic() - t0, 2)}
    usage = payload.get("usage") or {}
    det = usage.get("prompt_tokens_details") or {}
    return {"http_status": code, "prompt_tokens": usage.get("prompt_tokens"),
            "cached_tokens": det.get("cached_tokens"),
            "wall_s": round(time.monotonic() - t0, 2)}


def doc_text(j: int, n_lines: int) -> str:
    parts = []
    for i in range(n_lines):
        h = hashlib.sha256(f"TRACK-INTERVAL|doc{j}|line{i}".encode()).hexdigest()
        parts.append(f"d{j} n{i} {h[:16]} {h[16:32]} {h[32:48]}")
    return "\n".join(parts)


def is_hit(r: dict) -> bool:
    return bool(r.get("http_status") == 200 and r.get("prompt_tokens")
                and r.get("cached_tokens") is not None
                and r["cached_tokens"] >= 0.5 * r["prompt_tokens"])


def capacity_probe(info: dict, n: int) -> dict:
    """Pressure the tree at ~1.5x capacity, then read the resident-document window.

    Documents are unique sha256-hex filler (no shared prefix).  A small
    calibration document measures the generator's tokens-per-line (hex filler
    runs ~1.15 chars/token, not the renderer's 4), so each pressure document is
    sized to DOC_TARGET_TOKENS and stays under the 131072 context.
    """
    cap = int(info["max_total_num_tokens"])
    out: dict = {"capacity_tokens": cap, "target_ratio": 1.5,
                 "doc_target_tokens": DOC_TARGET_TOKENS}
    n_lines = 300
    r1 = http_chat([{"role": "user", "content": doc_text(1, n_lines)}])
    if r1["http_status"] != 200 or not r1.get("prompt_tokens"):
        out.update({"ok": False, "stage": "calibration", "response": r1})
        return out
    p1 = int(r1["prompt_tokens"])
    per_line = p1 / n_lines
    n_lines2 = max(200, int(round(DOC_TARGET_TOKENS / per_line)))
    r2 = http_chat([{"role": "user", "content": doc_text(2, n_lines2)}])
    if r2["http_status"] != 200 or not r2.get("prompt_tokens"):
        out.update({"ok": False, "stage": "calibration2", "response": r2,
                    "calibration": {"lines": n_lines, "tokens": p1, "tokens_per_line": per_line}})
        return out
    doc_tokens = int(r2["prompt_tokens"])
    if doc_tokens > 120000:  # safety: never push a doc into the context ceiling
        out.update({"ok": False, "stage": "doc too large", "doc_tokens": doc_tokens})
        return out
    n_docs = max(2, min(48, math.ceil(1.5 * cap / doc_tokens)))
    out.update({"doc_tokens": doc_tokens, "doc_lines": n_lines2, "n_docs": n_docs,
                "target_tokens": round(1.5 * cap),
                "calibration": {"lines": n_lines, "tokens": p1,
                                "tokens_per_line": round(per_line, 3)}})
    sends = 2
    tokens_sent = p1 + doc_tokens
    for j in range(3, n_docs + 2):
        r = http_chat([{"role": "user", "content": doc_text(j, n_lines2)}])
        sends += 1
        if r["http_status"] != 200 or not r.get("prompt_tokens"):
            out.update({"ok": False, "stage": f"pressure doc {j}", "response": r})
            return out
        tokens_sent += int(r["prompt_tokens"])
    out["pressure_tokens"] = tokens_sent
    out["pressure_requests"] = sends
    probes = []
    first_miss = None
    for j in range(n_docs + 1, 1, -1):
        if len(probes) >= PROBE_CAP:
            break
        r = http_chat([{"role": "user", "content": doc_text(j, n_lines2)}])
        if r["http_status"] != 200 or not r.get("prompt_tokens"):
            out.update({"ok": False, "stage": f"probe doc {j}", "response": r})
            return out
        hit = is_hit(r)
        probes.append({"doc": j, "hit": hit, "prompt_tokens": r["prompt_tokens"],
                       "cached_tokens": r["cached_tokens"],
                       "cached_fraction": round((r["cached_tokens"] or 0) / r["prompt_tokens"], 4)})
        if not hit:
            first_miss = j
            break
    resident_docs = (n_docs + 1 - first_miss) if first_miss else n_docs
    out.update({
        "ok": True,
        "probes": probes,
        "probe_count": len(probes),
        "first_miss_doc": first_miss,
        "resident_docs": resident_docs,
        "resident_window_tokens": resident_docs * doc_tokens,
        "capacity_ratio_realised": round(tokens_sent / cap, 3),
        "note": ("probed newest -> oldest; a miss proves everything older is gone "
                 "(LRU), so the window is the resident tail of the pressure set"),
    })
    return out


def run_arm(n: int) -> dict:
    arm_dir = HERE / f"t{n}"
    arm_dir.mkdir(parents=True, exist_ok=True)
    name = f"gx10-occamy-nvfp4-t{n}"
    rec: dict = {"arm": n, "interval": n, "container": name, "started_utc": now()}
    log(f"ARM {n}: stop production")
    rec["production_stopped_status"] = LV.service_stop()
    if rec["production_stopped_status"] != "absent":
        rec.update({"ok": False, "abort_all": True,
                    "error": f"production container not absent after service stop: "
                             f"{rec['production_stopped_status']}"})
        return rec
    cmd = LV.build_cmd(SPEC["Config"]["Cmd"], [("--mamba-track-interval", str(n))])
    rec["cmd_overrides"] = {"--mamba-track-interval": str(n)}
    reused = False
    if LV.container_status(name) == "running":
        try:
            cur = LV.get_server_info()
            reused = cur.get("mamba_track_interval") == n
            rec["reused_running_variant"] = reused
        except Exception:  # noqa: BLE001
            reused = False
    if not reused:
        LV.remove_container(name)
        cp = LV.ssh_run(LV.docker_create_argv(SPEC, name, cmd), timeout=180.0)
        if cp.returncode != 0:
            rec.update({"ok": False, "abort_all": False,
                        "error": f"docker create failed: {cp.stderr.strip()[:600]}"})
            return rec
        cp = LV.ssh_run(["docker", "start", name], timeout=180.0)
        rec["docker_start_rc"] = cp.returncode
        if cp.returncode != 0:
            rec.update({"ok": False, "error": f"docker start failed: {cp.stderr.strip()[:600]}",
                        "logs": LV.docker_logs_tail(name, 40)})
            return rec
    rec["health"] = LV.wait_health(name, deadline_s=900.0)
    if not rec["health"].get("ok"):
        rec.update({"ok": False, "logs": LV.docker_logs_tail(name, 60),
                    "error": "variant never became healthy"})
        return rec
    info = LV.capture_server_info(STATE / f"track-{n}.json")
    rec["server_info"] = {k: info.get(k) for k in INFO_KEYS}
    if info.get("mamba_track_interval") != n:
        rec.update({"ok": False, "error": "flag did not take effect",
                    "observed": info.get("mamba_track_interval")})
        return rec
    env = dict(os.environ, TRACK_LOCK_HELD="1", TRACK_CONFIG_ID=f"T{n}",
               TRACK_CONFIG_JSON=str(STATE / f"track-{n}.json"),
               RESEXTRACT_OCCAMY_BASE_URL=BASE_V1)
    log(f"ARM {n}: measuring 5 prompt arms x 71 turns")
    t0 = time.time()
    proc = subprocess.run([sys.executable, str(arm_dir / "cell.py")], env=env,
                          capture_output=True, text=True)
    (arm_dir / "cell.log").write_text((proc.stdout or "") + "\n[stderr]\n" + (proc.stderr or ""))
    rec["cell_rc"] = proc.returncode
    rec["cell_seconds"] = round(time.time() - t0, 1)
    apath = arm_dir / "analysis.json"
    analysis = json.loads(apath.read_text()) if apath.exists() else {}
    rec["cell_status"] = analysis.get("status")
    rec["cell_requests"] = (analysis.get("requests") or {}).get("total")
    rec["per_arm"] = {a: {"mean": v.get("mean_uncached_per_turn"),
                          "ci95": v.get("ci95"), "n": v.get("n_rows")}
                      for a, v in (analysis.get("per_arm") or {}).items()}
    rec["deltas_vs_R"] = {k: {"diff": v.get("mean_uncached_per_turn_delta"),
                              "ci95": v.get("ci95"),
                              "excludes_zero": v.get("excludes_zero")}
                          for k, v in (analysis.get("deltas_vs_R") or {}).items()}
    rec["warmup_cached_tokens"] = analysis.get("warmup_cached_tokens")
    if rec["cell_status"] == "done":
        log(f"ARM {n}: capacity probe")
        rec["capacity"] = capacity_probe(info, n)
    else:
        rec["capacity"] = {"ok": False, "stage": "skipped: cell not done",
                           "cell_status": rec["cell_status"]}
    log(f"ARM {n}: drop variant, restore production")
    LV.remove_container(name)
    rec["variant_removed"] = LV.container_status(name)
    rec["production_unit"] = LV.service_start()
    rec["production_health"] = LV.wait_health(LV.PRODUCTION, deadline_s=900.0)
    if rec["production_health"].get("ok"):
        post = LV.capture_server_info(STATE / f"track-restore-{n}.json")
        rec["restore_keys"] = {k: {"live": post.get(k), "expected": v,
                                   "ok": post.get(k) == v}
                               for k, v in BASELINE.items()}
        rec["restore_ok"] = all(x["ok"] for x in rec["restore_keys"].values())
        rec["restore_max_total_num_tokens"] = post.get("max_total_num_tokens")
    else:
        rec.update({"restore_ok": False, "abort_all": True,
                    "error": "production did not come back healthy after the arm"})
    rec["ok"] = rec.get("cell_status") in ("done", "partial")
    return rec


def main() -> int:
    lock = LOCK_PATH.open("a+", encoding="utf-8")
    fcntl.flock(lock, fcntl.LOCK_EX)
    lock.seek(0)
    lock.truncate()
    json.dump({"unit": "TRACK-INTERVAL", "pid": os.getpid(), "acquired_utc": now(),
               "scope": "three restart-level --mamba-track-interval arms on occamy"}, lock)
    lock.flush()
    os.fsync(lock.fileno())
    log("lock held")
    pre = LV.get_server_info()
    pre_path = STATE / "track-prod-pre.json"
    if not pre_path.exists():
        pre_path.write_text(json.dumps(pre, indent=2, sort_keys=True) + "\n")
    pre_keys = {k: {"live": pre.get(k), "expected": v, "ok": pre.get(k) == v}
                for k, v in BASELINE.items()}
    log(f"production pre-flight: {pre_keys}")
    results = []
    try:
        for n in ARMS:
            try:
                rec = run_arm(n)
            except Exception as exc:  # noqa: BLE001
                log(f"ARM {n} crashed: {type(exc).__name__}: {exc}")
                rec = {"arm": n, "ok": False, "abort_all": True,
                       "error": f"{type(exc).__name__}: {exc}"}
                try:
                    if LV.container_status(LV.PRODUCTION) != "running":
                        LV.service_start()
                        rec["emergency_restore_health"] = LV.wait_health(LV.PRODUCTION, deadline_s=900.0)
                except Exception as exc2:  # noqa: BLE001
                    rec["emergency_restore_error"] = f"{type(exc2).__name__}: {exc2}"
            results.append(rec)
            (HERE / f"arm-{n}.json").write_text(json.dumps(rec, indent=2) + "\n")
            log(f"ARM {n} done: ok={rec.get('ok')} cell={rec.get('cell_status')} "
                f"restore={rec.get('restore_ok')} requests_so_far={Budget.n}")
            if rec.get("abort_all"):
                break
        (HERE / "summary.json").write_text(json.dumps(
            {"arms": results, "requests": Budget.n, "bound": BUDGET_REQUESTS,
             "finished_utc": now()}, indent=2) + "\n")
    finally:
        lock.seek(0)
        lock.truncate()
        json.dump({"unit": "TRACK-INTERVAL", "pid": os.getpid(), "released_utc": now()}, lock)
        lock.flush()
        os.fsync(lock.fileno())
        fcntl.flock(lock, fcntl.LOCK_UN)
        lock.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
