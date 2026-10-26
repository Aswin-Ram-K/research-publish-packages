#!/usr/bin/env python3
"""Restart-resilient capacity probe for TRACK-INTERVAL.

One invocation advances one arm through launch -> health -> pressure ->
probes -> restore, bounded by --max-seconds, saving progress after every
batch so a killed harness turn resumes instead of re-paying.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load_mod(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


RT = load_mod("rt_capstep", HERE / "run_track.py")
PHASES = ("launch", "health", "pressure", "probes", "restore", "done")


def spath(n: int) -> Path:
    return HERE / f"cap-{n}.json"


def load_state(n: int) -> dict:
    p = spath(n)
    if p.exists():
        try:
            return json.loads(p.read_text())
        except Exception:  # noqa: BLE001  (a kill can truncate a save)
            pass
    return {"arm": n, "phase": "launch", "requests": int(__import__("os").environ.get("TRACK_REQUESTS_SO_FAR", "1077")),
            "sent": [], "tokens_sent": 0, "probed": [], "log": []}


def save(st: dict) -> None:
    st["requests"] = RT.Budget.n
    tmp = spath(st["arm"]).with_suffix(".json.tmp")
    tmp.write_text(json.dumps(st, indent=2) + "\n")
    tmp.replace(spath(st["arm"]))


def note(st: dict, msg: str) -> None:
    st.setdefault("log", []).append(f"{RT.now()} {msg}")
    RT.log(f"CAP {st['arm']}: {msg}")


def s_launch(st: dict, deadline: float) -> str:
    n = st["arm"]
    name = f"gx10-occamy-nvfp4-t{n}"
    reused = False
    if RT.LV.container_status(name) == "running":
        try:
            reused = RT.LV.get_server_info().get("mamba_track_interval") == n
        except Exception:  # noqa: BLE001
            reused = False
    st["reused_running_variant"] = reused
    if reused:
        note(st, "variant already running")
        return "health"
    note(st, "stop production")
    st["production_stopped_status"] = RT.LV.service_stop()
    if st["production_stopped_status"] != "absent":
        st["error"] = f"production not absent: {st['production_stopped_status']}"
        return "restore"
    RT.LV.remove_container(name)
    cmd = RT.LV.build_cmd(RT.SPEC["Config"]["Cmd"], [("--mamba-track-interval", str(n))])
    cp = RT.LV.ssh_run(RT.LV.docker_create_argv(RT.SPEC, name, cmd), timeout=180.0)
    if cp.returncode != 0:
        st["error"] = f"docker create failed: {cp.stderr.strip()[:400]}"
        return "restore"
    cp = RT.LV.ssh_run(["docker", "start", name], timeout=180.0)
    if cp.returncode != 0:
        st["error"] = f"docker start failed: {cp.stderr.strip()[:400]}"
        st["logs"] = RT.LV.docker_logs_tail(name, 40)
        return "restore"
    return "health"


def s_health(st: dict, deadline: float) -> str:
    name = f"gx10-occamy-nvfp4-t{st['arm']}"
    while time.monotonic() < deadline:
        if RT.LV.container_status(name) in ("exited", "dead", "absent"):
            st["error"] = "variant container died"
            st["logs"] = RT.LV.docker_logs_tail(name, 60)
            return "restore"
        if RT.LV.health() == 200:
            info = RT.LV.capture_server_info(RT.STATE / f"track-{st['arm']}.json")
            st["server_info"] = {k: info.get(k) for k in RT.INFO_KEYS}
            if info.get("mamba_track_interval") != st["arm"]:
                st["error"] = f"flag did not take: {info.get('mamba_track_interval')}"
                return "restore"
            st["capacity_tokens"] = int(info["max_total_num_tokens"])
            note(st, f"healthy, capacity={st['capacity_tokens']}")
            return "pressure"
        time.sleep(5)
    return "health"


def s_pressure(st: dict, deadline: float) -> str:
    if not st.get("calibrated"):
        n_lines = 300
        r1 = RT.http_chat([{"role": "user", "content": RT.doc_text(1, n_lines)}])
        if r1["http_status"] != 200 or not r1.get("prompt_tokens"):
            st["error"] = f"calibration failed: {r1}"
            return "restore"
        p1 = int(r1["prompt_tokens"])
        per_line = p1 / n_lines
        n_lines2 = max(200, int(round(RT.DOC_TARGET_TOKENS / per_line)))
        r2 = RT.http_chat([{"role": "user", "content": RT.doc_text(2, n_lines2)}])
        if r2["http_status"] != 200 or not r2.get("prompt_tokens"):
            st["error"] = f"calibration2 failed: {r2}"
            return "restore"
        doc_tokens = int(r2["prompt_tokens"])
        import math
        n_docs = max(2, min(48, math.ceil(1.5 * st["capacity_tokens"] / doc_tokens)))
        st.update({"calibrated": True, "calibration": {"lines": n_lines, "tokens": p1,
                                                       "tokens_per_line": round(per_line, 3)},
                   "doc_tokens": doc_tokens, "doc_lines": n_lines2, "n_docs": n_docs,
                   "sent": [1, 2], "tokens_sent": p1 + doc_tokens,
                   "requests": RT.Budget.n})
        note(st, f"calibrated doc={doc_tokens} n_docs={n_docs} target={round(1.5 * st['capacity_tokens'])}")
        save(st)
    n_docs = st["n_docs"]
    pending = [j for j in range(2, n_docs + 2) if j not in st["sent"]]
    while pending and time.monotonic() < deadline - 45:
        batch, pending = pending[:4], pending[4:]
        with ThreadPoolExecutor(max_workers=4) as ex:
            results = list(ex.map(
                lambda j: (j, RT.http_chat([{"role": "user", "content": RT.doc_text(j, st["doc_lines"])}])),
                batch))
        for j, r in results:
            if r["http_status"] != 200 or not r.get("prompt_tokens"):
                st["error"] = f"pressure doc {j} failed: {r}"
                return "restore"
            st["sent"].append(j)
            st["tokens_sent"] += int(r["prompt_tokens"])
        save(st)
        note(st, f"pressure {len(st['sent'])}/{n_docs} docs, {st['tokens_sent']} tokens")
    st["pressure_tokens"] = st["tokens_sent"]
    st["capacity_ratio_realised"] = round(st["tokens_sent"] / st["capacity_tokens"], 3)
    return "probes" if not pending else "pressure"


def s_probes(st: dict, deadline: float) -> str:
    n_docs = st["n_docs"]
    nxt = st.get("next_probe", n_docs + 1)
    while nxt >= 2:
        if time.monotonic() > deadline:
            st["next_probe"] = nxt
            return "probes"
        r = RT.http_chat([{"role": "user", "content": RT.doc_text(nxt, st["doc_lines"])}])
        if r["http_status"] != 200 or not r.get("prompt_tokens"):
            st["error"] = f"probe doc {nxt} failed: {r}"
            return "restore"
        hit = RT.is_hit(r)
        st.setdefault("probes", []).append(
            {"doc": nxt, "hit": hit, "prompt_tokens": r["prompt_tokens"],
             "cached_tokens": r["cached_tokens"],
             "cached_fraction": round((r["cached_tokens"] or 0) / r["prompt_tokens"], 4)})
        st["next_probe"] = nxt - 1
        if not hit:
            st["first_miss_doc"] = nxt
            break
        nxt -= 1
        save(st)
    st["resident_docs"] = (n_docs + 1 - st["first_miss_doc"]) if st.get("first_miss_doc") else n_docs
    st["resident_window_tokens"] = st["resident_docs"] * st["doc_tokens"]
    save(st)
    return "restore"


def s_restore(st: dict, deadline: float) -> str:
    name = f"gx10-occamy-nvfp4-t{st['arm']}"
    if RT.LV.container_status(name) in ("running", "created", "exited"):
        RT.LV.remove_container(name)
    st["variant_removed"] = RT.LV.container_status(name)
    if RT.LV.container_status(RT.LV.PRODUCTION) != "running":
        st["production_unit"] = RT.LV.service_start()
    while time.monotonic() < deadline:
        if RT.LV.health() == 200:
            post = RT.LV.capture_server_info(RT.STATE / f"track-restore-{st['arm']}.json")
            st["restore_keys"] = {k: {"live": post.get(k), "expected": v, "ok": post.get(k) == v}
                                  for k, v in RT.BASELINE.items()}
            st["restore_ok"] = all(x["ok"] for x in st["restore_keys"].values())
            st["restore_max_total_num_tokens"] = post.get("max_total_num_tokens")
            note(st, f"production restored ok={st['restore_ok']}")
            return "done"
        time.sleep(5)
    return "restore"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", type=int, required=True)
    ap.add_argument("--max-seconds", type=float, default=300.0)
    args = ap.parse_args()
    st = load_state(args.arm)
    RT.Budget.n = int(st.get("requests", 1077))
    import fcntl
    lock = RT.LOCK_PATH.open("a+", encoding="utf-8")
    fcntl.flock(lock, fcntl.LOCK_EX)
    deadline = time.monotonic() + args.max_seconds
    try:
        while st["phase"] != "done" and time.monotonic() < deadline:
            phase = st["phase"]
            nxt = {"launch": s_launch, "health": s_health, "pressure": s_pressure,
                   "probes": s_probes, "restore": s_restore}[phase](st, deadline)
            st["phase"] = nxt
            save(st)
        if st["phase"] == "done":
            payload = dict(st)
            (HERE / f"arm-{args.arm}-capacity.json").write_text(json.dumps(payload, indent=2) + "\n")
            arm = HERE / f"arm-{args.arm}.json"
            if arm.exists():
                data = json.loads(arm.read_text())
                data["capacity"] = {k: st.get(k) for k in
                                    ("capacity_tokens", "doc_tokens", "n_docs", "sent",
                                     "pressure_tokens", "capacity_ratio_realised",
                                     "probes", "first_miss_doc", "resident_docs",
                                     "resident_window_tokens")}
                data["capacity"]["ok"] = True
                arm.write_text(json.dumps(data, indent=2) + "\n")
        print(json.dumps({"arm": args.arm, "phase": st["phase"], "requests": RT.Budget.n,
                          "error": st.get("error")}, indent=1))
    finally:
        lock.seek(0)
        lock.truncate()
        json.dump({"unit": "TRACK-INTERVAL", "pid": __import__("os").getpid(),
                   "released_utc": RT.now(), "scope": f"cap-step arm {args.arm}"}, lock)
        lock.flush()
        fcntl.flock(lock, fcntl.LOCK_UN)
        lock.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
