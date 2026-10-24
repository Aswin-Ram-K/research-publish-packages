#!/usr/bin/env python3
"""R2-SGL-CAP window driver — one variant arm, start to proven restore.

WHAT THIS DRIVER OWNS THAT THE BATTERY DOES NOT
===============================================
1. **The lock.**  `experiments/context-cache/.occamy.lock` is held `flock`-exclusive for the whole live
   phase, because a second window measuring `:8012` at the same time would corrupt both arms' cache
   state without either arm noticing.
2. **The stop-safety rewrite.**  Production is an `--rm` container (`HostConfig.AutoRemove = true`),
   so `docker stop` destroys it.  Before anything is stopped, production is rewritten with
   `AutoRemove=false` **preserving `Config.Cmd` byte-for-byte**; a rewrite that changes the argv is
   refused.  This is the defect `WIN-SGL` hit live and the reason `variant_launcher.assert_stop_safe`
   exists.
3. **The container dance.**  `systemctl --user stop` production (it is the unit's ExecStart, so a
   container-level stop cannot hold `:8012` free) → prove `:8012` down → create + start the variant →
   measure → `docker rm -f` the variant → `systemctl --user start` → prove restore on the six keys.
4. **The G0 gate and the request cap.**  Exactly one of gate/battery/eviction per live session, so a
   crash re-runs only the part that failed, and every live request is metered.

WHY THE ARMS ARE SEPARATE PROCESS RUNS
======================================
A single process doing three arms would hold one 900-request cap across three variant launches and
would lose an already-measured arm if the third failed to start.  One `--arm` per invocation means the
cap is per arm, a failed start costs exactly one arm's worth of nothing, and the restore proof is
re-established three times rather than assumed once.
"""
from __future__ import annotations

import argparse
import fcntl
import importlib.util
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
CELLS = REPO / "experiments" / "context-cache" / "cells"
STATE = REPO / "state" / "config"
LOCK_PATH = REPO / "experiments" / "context-cache" / ".occamy.lock"
CORPUS_PATH = REPO / "experiments" / "context-cache" / "corpora" / "endtoend.json"
BASELINE_PATH = STATE / "occamy-restore-baseline.json"
SPEC_PATH = STATE / "occamy-inspect-pre.json"

sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(STATE))

import battery as B  # noqa: E402

SIX_KEYS = ("page_size", "mamba_radix_cache_strategy", "radix_eviction_policy",
            "mem_fraction_static", "kv_cache_dtype", "max_mamba_cache_size")

#: The three arms this card declares.  `flags` are the ONLY permitted deltas on production argv.
ARMS: dict[str, dict[str, Any]] = {
    "S1": {
        "label": "slot sweep: 64 -> 320 slots, production strategy (extra_buffer, S=5 per request)",
        "flags": (("--max-mamba-cache-size", "320"),),
        "slot_cost_S": 5,
        "expect": "320 slots / S=5 = 64 requests; --max-running-requests 5 caps admission at 5",
    },
    "S2": {
        "label": "cheaper slots: no_buffer (S=3) at 320 slots",
        "flags": (("--mamba-radix-cache-strategy", "no_buffer"), ("--max-mamba-cache-size", "320")),
        "slot_cost_S": 3,
        "expect": "320 slots / S=3 = 106 requests; production's extra_buffer costs 5 slots/request",
    },
    "S3": {
        "label": "policy: --radix-eviction-policy lfu (documented for few-prompts-reused-heavily)",
        "flags": (("--radix-eviction-policy", "lfu"),),
        "slot_cost_S": 5,
        "expect": "slots unchanged (64); only the eviction choice moves",
    },
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


class Lock:
    """`flock`-exclusive over the shared occamy lock for the whole live phase."""

    def __init__(self, path: Path = LOCK_PATH):
        self.path = path
        self.fh = None

    def __enter__(self):
        self.fh = self.path.open("a+", encoding="utf-8")
        started = time.monotonic()
        while True:
            try:
                fcntl.flock(self.fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() - started > 300:
                    raise RuntimeError(f"could not acquire {self.path} within 300 s")
                time.sleep(2.0)
        self.fh.seek(0)
        self.fh.truncate()
        self.fh.write(json.dumps({"unit": "R2-SGL-CAP", "acquired_utc": utc_now()}))
        self.fh.flush()
        return self

    def __exit__(self, *exc):
        try:
            self.fh.seek(0)
            self.fh.truncate()
            self.fh.write(json.dumps({"unit": "R2-SGL-CAP", "released_utc": utc_now()}))
            self.fh.flush()
            fcntl.flock(self.fh, fcntl.LOCK_UN)
        finally:
            self.fh.close()
        return False


# --------------------------------------------------------------------------- #
# Live sender — one request in flight, metered
# --------------------------------------------------------------------------- #
class Sender:
    """Wraps the shared ChatClient so every live request is counted and normalised.

    `counted` is the meter: the request cap is enforced *here*, so no code path can spend an
    unmetered request.  A response without `prompt_tokens_details.cached_tokens` yields
    `cached_tokens=None` — an unobservable value, never a zero.
    """

    def __init__(self, base_url: str, cap: int, log: Callable[[str], None] = print):
        mod = load_module(REPO / "experiments" / "context-cache" / "client.py", "r2sgl_client")
        self.client = mod.ChatClient(base_url=base_url)
        self.cap = cap
        self.counted = 0
        self.log = log
        self.failures: list[str] = []

    def __call__(self, messages, *, salt: str, rep: int = 0, phase: str = "battery",
                 max_tokens: int = 4) -> dict[str, Any]:
        if self.counted >= self.cap:
            raise RuntimeError(f"request cap reached ({self.cap}); refusing to spend another request")
        self.counted += 1
        t0 = time.perf_counter()
        try:
            prompt, cached, completion, ttft, wall, status, _text = self.client.chat(
                messages, max_tokens=max_tokens, thinking=False, stream=True, timeout=180.0)
        except Exception as exc:  # noqa: BLE001 - a failed request is data, not a crash
            self.failures.append(f"{phase}/{salt}: {exc!r}")
            raise
        return {"prompt_tokens": int(prompt), "cached_tokens": cached,
                "completion_tokens": int(completion), "ttft_ms": float(ttft),
                "wall_ms": float(wall), "status": int(status),
                "salt": salt, "rep": rep, "phase": phase}


def make_salt_fn(arm: str, run_id: str) -> Callable[[str], str]:
    """Per-arm, per-run salt: cross-window contamination would otherwise read as a cache hit."""
    def salt_fn(tag: str) -> str:
        return f"r2sglcap-{arm}-{run_id}-{tag}"
    return salt_fn


# --------------------------------------------------------------------------- #
# Boot-log slot accounting — resolved from the log, never from the card
# --------------------------------------------------------------------------- #
SLOT_PATTERNS = ("state slots", "max_mamba_cache_size", "mamba_radix_cache_strategy",
                 "mamba cache", "linear-attn state", "Hybrid (mamba")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="R2-SGL-CAP variant window")
    ap.add_argument("--arm", required=True, choices=sorted(ARMS))
    ap.add_argument("--phase", required=True,
                    choices=["preflight", "gate", "battery", "eviction", "restore", "all"])
    ap.add_argument("--request-cap", type=int, default=900)
    ap.add_argument("--apply", action="store_true", help="touch the host; without it everything is a dry run")
    ap.add_argument("--run-id", default=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
    args = ap.parse_args(argv)

    HERE.mkdir(parents=True, exist_ok=True)
    state_path = HERE / f"state-{args.arm}.json"
    state: dict[str, Any] = json.loads(state_path.read_text()) if state_path.exists() else {}
    state.setdefault("unit", "R2-SGL-CAP")
    state.setdefault("arm", args.arm)
    state.setdefault("run_id", args.run_id)
    state.setdefault("phases_done", [])
    log_path = HERE / f"window-{args.arm}.log"
    logfh = log_path.open("a", encoding="utf-8")

    def log(msg: str) -> None:
        line = f"{datetime.now(timezone.utc).isoformat()} {msg}"
        print(line, flush=True)
        logfh.write(line + "\n")
        logfh.flush()

    launcher = load_module(STATE / "variant_launcher.py", "r2sgl_launcher")
    spec = launcher.load_spec(SPEC_PATH)
    cfg = launcher.VariantConfig(config_id=f"R2SGL{args.arm}",
                                 label=ARMS[args.arm]["label"],
                                 flags=tuple(ARMS[args.arm]["flags"]))
    plan = launcher.build_variant(spec, cfg)
    plan.assert_single_delta()      # refuse BEFORE any host action if the delta is not exactly declared

    exec_ = launcher.SshExecutor()
    log(f"[{args.arm}] argv delta vs production:\n{plan.render()}")
    state["plan"] = {"flags": [list(f) for f in cfg.flags], "rendered_diff": plan.render(),
                     "create_argv": plan.create_argv, "spec_digest": plan.spec_digest,
                     "delta": plan.delta()}

    if not args.apply:
        state["dry_run"] = True
        state_path.write_text(json.dumps(state, indent=1))
        log(f"[{args.arm}] DRY RUN: {len(plan.create_argv)} argv tokens, no host contact")
        return 0

    result = {"arm": args.arm, "phase": args.phase}
    with Lock():
        session = launcher.LaunchSession(exec_, spec, cfg, rows_dir=HERE, log=log)

        if args.phase in ("preflight", "all"):
            free = exec_.run(["free", "-m"])
            docker_ps = exec_.run(["docker", "ps", "--format", "{{.Names}}|{{.Status}}"])
            log(f"free -m:\n{free.out}")
            log(f"docker ps:\n{docker_ps.out}")
            avail = None
            for line in free.out.splitlines():
                if line.startswith("Mem:"):
                    avail = int(line.split()[6])
            state["preflight"] = {"available_mb": avail, "docker_ps": docker_ps.out}
            if avail is not None and avail < 60000:
                log(f"PREFLIGHT REFUSED: available {avail} MB < 60000 MB required to relaunch production")
                state_path.write_text(json.dumps(state, indent=1))
                return 4

        if args.phase in ("gate", "battery", "eviction", "all"):
            # --- stop-safety -------------------------------------------------
            auto = session.autoremove()
            state["autoremove_pre"] = auto
            log(f"production AutoRemove={auto!r}")
            if launcher.is_stop_safe(auto) is False:
                raise launcher.LauncherError(
                    "production is --rm; the stop-safety rewrite must run before any window "
                    "(this driver refuses to stop a container it cannot restart)")
            session.assert_stop_safe()

            # --- production down, variant up ---------------------------------
            log("stopping production via systemd")
            status = session.stop_production()
            log(f"production status after stop: {status}")
            if status != "absent":
                raise launcher.LauncherError(f"production still {status} after stop; refusing to create")
            log("creating and starting variant")
            session.create_and_start()
            try:
                info = wait_health(exec_, 900.0, log)
                state["variant_server_info"] = info
                (STATE / f"r2-sgl-{args.arm.lower()}.json").write_text(json.dumps(info, indent=2, sort_keys=True))
                state["slot_accounting"] = slot_report_remote(
                    exec_, info, container=cfg.container_name(), log=log)
                sender = Sender("http://192.168.2.168:8012", args.request_cap, log)
                salt_fn = make_salt_fn(args.arm, args.run_id)

                if args.phase in ("gate", "all"):
                    gate = load_module(STATE / "window_gate.py", "r2sgl_gate")
                    gcfg = gate.window_gate_config(grid_unit=1, max_requests=8)
                    verdict = gate.run_gate(gcfg, sender)
                    log(f"G0 gate: {gate.summarise(verdict)}")
                    state["gate"] = verdict
                    gate.assert_gate(verdict)

                if args.phase in ("battery", "all"):
                    corpus = json.loads(CORPUS_PATH.read_text())
                    scenario = corpus["scenarios"][0]
                    turns = (scenario["turns"] * ((71 // len(scenario["turns"])) + 1))[:71]
                    rows = B.run_battery(sender, preamble=scenario["preamble"], turns=turns,
                                         config_id=args.arm,
                                         config_sha256=config_sha(state, args.arm),
                                         salt_fn=salt_fn, log=log)
                    write_rows(HERE / f"battery-{args.arm}.jsonl", rows)
                    state["battery_rows"] = len(rows)
                    state["battery_analysis"] = B.analyse_battery(
                        rows, capacity_tokens=capacity_of(info))
                    log(f"battery: {state['battery_analysis']['pooled']}")

                if args.phase in ("eviction", "all"):
                    ev = B.run_eviction(sender, token_capacity=capacity_of(info),
                                        config_id=args.arm,
                                        config_sha256=config_sha(state, args.arm),
                                        salt_fn=salt_fn, request_cap=args.request_cap - sender.counted,
                                        log=log)
                    ratio = ev["bracket"].get("resident_tokens")
                    if ratio and ev["token_capacity"]:
                        ev["bracket"]["ratio_of_capacity"] = [
                            round(ratio[0] / ev["token_capacity"], 4),
                            round(ratio[1] / ev["token_capacity"], 4)]
                    write_rows(HERE / f"eviction-{args.arm}.jsonl", ev.pop("rows"))
                    state["eviction"] = ev
                    log(f"eviction bracket: {json.dumps(ev['bracket'])}")
                state["requests_used"] = sender.counted
            finally:
                # --- variant down, production back, ALWAYS -------------------
                log("removing variant")
                session.remove_variant()
                log("starting production")
                session.start_production()
                proof = prove(session, exec_, state, log)
                state["restore"] = proof
                state["phases_done"].append(args.phase)
                state_path.write_text(json.dumps(state, indent=1))
                log(f"restore proven={proof['proven']}")

    state_path.write_text(json.dumps({k: v for k, v in state.items() if k != "prod_server_info"},
                                     indent=1))
    log(f"[{args.arm}] phase {args.phase} complete; requests={state.get('requests_used')}")
    return 0


def config_sha(state: Mapping[str, Any], arm: str) -> str:
    """Digest of *what was launched*: production argv + the arm's declared flags.

    Hashing the state file would move on every rewrite (timestamps, request counts) and hashing the
    raw inspect payload would move whenever docker re-serialises an unrelated field.  This digest is
    a statement about exactly the configuration the rows were measured on.
    """
    payload = {"arm": arm, "flags": [list(f) for f in ARMS[arm]["flags"]],
               "spec_digest": state.get("plan", {}).get("spec_digest"),
               "create_argv": state.get("plan", {}).get("create_argv")}
    return B.sha256_bytes(json.dumps(payload, sort_keys=True).encode())


def capacity_of(info: Mapping[str, Any]) -> int | None:
    st = (info.get("internal_states") or [{}])[0]
    mu = st.get("memory_usage") or {}
    cap = mu.get("token_capacity")
    return int(cap) if isinstance(cap, int) else None


def wait_health(exec_, timeout_s: float, log) -> dict[str, Any]:
    """Poll /health until 200, then capture /get_server_info. The variant must report ready."""
    started = time.monotonic()
    attempt = 0
    while time.monotonic() - started < timeout_s:
        attempt += 1
        r = exec_.run(["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
                       "-m", "5", "http://192.168.2.168:8012/health"])
        if r.out.strip() == "200":
            info = exec_.run(["curl", "-sf", "-m", "20", "http://192.168.2.168:8012/get_server_info"])
            log(f"health 200 after {attempt} attempts ({time.monotonic() - started:.0f}s)")
            return json.loads(info.out)
        time.sleep(10.0)
    raise RuntimeError(f"variant did not become healthy within {timeout_s:.0f}s")


def slot_report_remote(exec_: Any, info: Mapping[str, Any], container: str,
                       log: Callable[[str], None] = print) -> dict[str, Any]:
    """Pull the variant's own boot log and resolve the slot accounting from it.

    The card is explicit that two research lanes disagreed about whether 64 slots bind and that the
    boot log decides.  So the log is fetched, the slot-bearing lines are quoted verbatim, and the
    arithmetic (`slots / S` vs `--max-running-requests`) is stated as the resolved answer.
    """
    r = exec_.run(["docker", "logs", container], timeout=90.0)
    text = (r.out or "") + "\n" + (r.err or "")   # sglang logs to stderr inside the container
    lines = []
    for raw in text.splitlines():
        low = raw.lower()
        if any(p.lower() in low for p in SLOT_PATTERNS):
            lines.append(raw.strip())
    state = (info.get("internal_states") or [{}])[0]
    get = lambda k: info.get(k, state.get(k))  # noqa: E731
    slots = get("max_mamba_cache_size")
    strategy = get("mamba_radix_cache_strategy")
    running = get("max_running_requests")
    s_cost = {"extra_buffer": 5, "lazy": 4, "no_buffer": 3}.get(str(strategy))
    admitted = (slots // s_cost) if isinstance(slots, int) and s_cost else None
    binding = "unknown"
    if isinstance(admitted, int) and isinstance(running, int):
        binding = "running_requests" if running <= admitted else "mamba_slots"
    report = {
        "container": container,
        "log_lines": lines[-40:],
        "log_line_count": len(lines),
        "max_mamba_cache_size": slots,
        "mamba_radix_cache_strategy": strategy,
        "max_running_requests": running,
        "slots_per_request_S": s_cost,
        "admitted_concurrency_by_slots": admitted,
        "binding_constraint": binding,
        "warning_lines": [ln for ln in lines
                          if "warning" in ln.lower() or "too small" in ln.lower()],
        "stderr_capture_rc": r.rc,
    }
    log(f"slots={slots} S={s_cost} -> admitted={admitted}; running={running}; binding={binding}")
    return report


def prove(session, exec_, state, log, *, wait_s: float = 900.0) -> dict[str, Any]:
    """Restore proof: six baseline keys, `:8012` 200, `occamy-1.0`, max_model_len 131072.

    Production reloads ~24 GB of weights on every start (measured startup_time.load_weight 123.7 s in
    the baseline), so a cold `:8012` right after `systemctl start` is expected, not a failed restore.
    The proof therefore WAITS for health rather than sampling once.
    """
    baseline = json.loads(BASELINE_PATH.read_text())
    started = time.monotonic()
    health_code = ""
    while time.monotonic() - started < wait_s:
        h = exec_.run(["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "-m", "5",
                       "http://192.168.2.168:8012/health"])
        health_code = h.out.strip()
        if health_code == "200":
            break
        time.sleep(10.0)
    log(f"restore: health {health_code} after {time.monotonic() - started:.0f}s")
    info_r = exec_.run(["curl", "-sf", "-m", "30", "http://192.168.2.168:8012/get_server_info"])
    models_r = exec_.run(["curl", "-sf", "-m", "30", "http://192.168.2.168:8012/v1/models"])
    post = json.loads(info_r.out) if info_r.ok and info_r.out.strip() else {}
    st = (post.get("internal_states") or [{}])[0]
    keys = {k: {"baseline": baseline.get(k),
                "restored": post.get(k, st.get(k)),
                "equal": baseline.get(k) == post.get(k, st.get(k))} for k in SIX_KEYS}
    model_id, max_len = None, None
    try:
        data = json.loads(models_r.out)["data"][0]
        model_id, max_len = data.get("id"), data.get("max_model_len")
    except Exception:  # noqa: BLE001
        pass
    checks = {
        "health_200": health_code == "200",
        "six_keys_equal": all(v["equal"] for v in keys.values()),
        "model_occamy": model_id == "occamy-1.0",
        "max_model_len_131072": max_len == 131072,
        "container_running": session.container_status() == "running",
    }
    return {"proven": all(checks.values()), "checks": checks, "keys": keys,
            "model_id": model_id, "max_model_len": max_len,
            "token_capacity": state.get("prod_server_info", {}).get("max_total_num_tokens"),
            "utc": utc_now()}


def write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("a", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, sort_keys=True) + "\n")


if __name__ == "__main__":
    raise SystemExit(main())
