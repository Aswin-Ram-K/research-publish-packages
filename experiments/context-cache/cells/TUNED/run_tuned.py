#!/usr/bin/env python3
"""WIN-TUNED — does ``--radix-eviction-policy slru`` beat the production ``lru``
under pressure, on **M4's** protocol?

This cell is deliberately thin: it owns no corpus and no launcher.

* the document pool is M4's ``cells/M4/corpus.jsonl`` (same 300 salted
  documents, same offline sizing), so a pressure run here is byte-comparable
  with the M4 LRU run;
* the container is built by WIN-SGL's ``cells/WIN-SGL/launch_variant.py`` from
  ``state/config/occamy-inspect-pre.json`` with exactly one argv change
  (``--radix-eviction-policy slru``);
* the measurement loop is M4's ``battery.py`` semantics: push distinct
  documents one at a time until cumulative **measured** prompt tokens reach
  ``1.5 x`` this variant's own ``token_capacity``, then replay the oldest 10 /
  middle 10 / newest 10 documents, newest->middle->oldest.

One request in flight, ``temperature 0``, ``max_tokens 4``, holds
``experiments/context-cache/.occamy.lock`` for the whole measurement.

Usage::

    python run_tuned.py --launch          # stop production, start wt-slru, health
    python run_tuned.py --measure         # lock + phase P + phase R + rows.jsonl
    python run_tuned.py --restore         # rm variant, start production, diff
    python run_tuned.py --status          # read-only: containers + health
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import importlib.util
import json
import math
import os
import statistics
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
M4_DIR = REPO / "experiments" / "context-cache" / "cells" / "M4"
WIN_SGL_DIR = REPO / "experiments" / "context-cache" / "cells" / "WIN-SGL"
STATE = REPO / "state" / "config"
LOGS = HERE / "logs"
LOCK_PATH = REPO / "experiments" / "context-cache" / ".occamy.lock"

sys.path.insert(0, str(REPO / "src"))

UNIT = "WIN-TUNED"
VARIANT = "wt-slru"
FLAG = ("--radix-eviction-policy", "slru")
PRODUCTION = "gx10-occamy-nvfp4"
BASE_URL = "http://192.168.2.168:8012"

REQUEST_CAP = 600
TARGET_RATIO = 1.5
BAND_SIZE = 10
MAX_DOCS = 300
MAX_TOKENS = 4
TIMEOUT_S = 120.0
LOCK_TIMEOUT_S = 300.0
CONSECUTIVE_FAILURE_LIMIT = 3

ROWS_PATH = HERE / "rows.jsonl"
RUN_PATH = HERE / "run.json"
SERVER_INFO_PATH = HERE / "variant_server_info.json"


# --------------------------------------------------------------------------- #
# Module loading: reuse, never re-implement
# --------------------------------------------------------------------------- #
def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


corpus_mod = _load("tuned_corpus", M4_DIR / "corpus.py")
launcher = _load("tuned_launcher", WIN_SGL_DIR / "launch_variant.py")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def log(message: str) -> None:
    line = f"{utc_now()} {message}"
    print(line, flush=True)
    LOGS.mkdir(parents=True, exist_ok=True)
    with (LOGS / "run.log").open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def health(url: str = BASE_URL, timeout: float = 10.0) -> int:
    try:
        with urllib.request.urlopen(f"{url}/health", timeout=timeout) as resp:
            return int(resp.status)
    except urllib.error.HTTPError as exc:
        return int(exc.code)
    except Exception:
        return 0


def get_server_info() -> tuple[dict, bytes]:
    with urllib.request.urlopen(f"{BASE_URL}/get_server_info", timeout=30.0) as resp:
        raw = resp.read()
    return json.loads(raw), raw


# --------------------------------------------------------------------------- #
# --launch
# --------------------------------------------------------------------------- #
def capture_pre() -> dict:
    """STEP 0 — production is intact, or it is a P0 and nothing else happens."""

    info, raw = get_server_info()
    (STATE / "tuned-pre.json").write_text(
        json.dumps(info, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    baseline = json.loads((STATE / "occamy-restore-baseline.json").read_text(encoding="utf-8"))
    keys = ("page_size", "mamba_radix_cache_strategy", "radix_eviction_policy",
            "mem_fraction_static", "kv_cache_dtype", "max_mamba_cache_size")
    live_capacity = ((info.get("internal_states") or [{}])[0].get("memory_usage") or {}).get(
        "token_capacity") or info.get("max_total_num_tokens")
    diff = {
        "unit": UNIT,
        "step": "step0_production_intact",
        "sampled_utc": utc_now(),
        "server_info_sha256": sha256_bytes(raw),
        "keys": {k: {"baseline": baseline.get(k), "live": info.get(k),
                     "equal": baseline.get(k) == info.get(k)} for k in keys},
        "token_capacity": {
            "baseline_stored_key": "max_total_num_tokens",
            "baseline": baseline.get("max_total_num_tokens"),
            "live": live_capacity,
            "equal": baseline.get("max_total_num_tokens") == live_capacity,
            "informational": "re-profiled from free memory at every start; not a config key "
                             "(WIN-SGL measured 1,306,681 -> 1,620,892 with no flag changed)",
        },
    }
    diff["config_ok"] = all(v["equal"] for v in diff["keys"].values())
    diff["production_intact"] = diff["config_ok"]
    write_json(HERE / "step0-pre-diff.json", diff)
    log(f"step0 production_intact={diff['production_intact']} "
        f"keys={ {k: v['live'] for k, v in diff['keys'].items()} } "
        f"capacity={live_capacity}")
    return {"info": info, "diff": diff, "capacity": live_capacity}


def launch_variant() -> dict:
    spec = launcher.load_spec(launcher.SPEC_PATH)
    cmd = launcher.build_cmd(spec["Config"]["Cmd"], [FLAG])
    argv = launcher.docker_create_argv(spec, VARIANT, cmd)
    record = {
        "unit": UNIT,
        "step": "launch_variant",
        "container": VARIANT,
        "flag": list(FLAG),
        "image": spec["Image"],
        "cmd_len_production": len(spec["Config"]["Cmd"]),
        "cmd_len_variant": len(cmd),
        "cmd": cmd,
        "create_argv": argv,
        "spec_path": "state/config/occamy-inspect-pre.json",
        "spec_sha256": hashlib.sha256(Path(launcher.SPEC_PATH).read_bytes()).hexdigest(),
        "started_utc": utc_now(),
    }
    write_json(LOGS / "variant-launch.json", record)
    log(f"create argv: {' '.join(argv[:24])} ... ({len(argv)} tokens)")

    # production's live stop surface is its systemd *user* unit; the container
    # carries AutoRemove=true, so a container-level stop would delete it and
    # `docker start` could not restore it (measured by WIN-SGL, recorded in
    # orchestration/handoffs/WIN-SGL.json -> assumptions.stop_surface).
    auto_remove = launcher.ssh_run(
        ["docker", "inspect", "-f", "{{.HostConfig.AutoRemove}}", PRODUCTION]).stdout.strip()
    record["production_auto_remove"] = auto_remove
    record["production_stop_surface"] = (
        "systemctl --user stop gx10-occamy-nvfp4.service" if auto_remove == "true"
        else f"docker stop {PRODUCTION}")
    log(f"production auto_remove={auto_remove} -> stop via {record['production_stop_surface']}")

    if auto_remove == "true":
        launcher.service_stop()
        gone = launcher.container_status(PRODUCTION) == "absent"
    else:
        launcher.stop_container(PRODUCTION)
        gone = launcher.container_status(PRODUCTION) in ("exited", "created")
    record["production_gone"] = gone
    record["port_free_probe_health"] = health()
    log(f"production gone={gone} health={record['port_free_probe_health']} "
        f"service={launcher.service_state()}")

    launcher.remove_container(VARIANT)
    cp = launcher.ssh_run(argv, timeout=180.0)
    record["create_rc"] = cp.returncode
    record["create_stderr"] = cp.stderr.strip()
    if cp.returncode != 0:
        record.update({"ok": False, "reason": "docker create failed"})
        write_json(LOGS / "variant-launch.json", record)
        return record
    cp = launcher.ssh_run(["docker", "start", VARIANT], timeout=180.0)
    record["start_rc"] = cp.returncode
    record["start_stderr"] = cp.stderr.strip()
    polled = launcher.wait_health(VARIANT, deadline_s=900.0, poll_s=5.0)
    record["health"] = polled
    record["service_after_stop"] = launcher.service_state()
    record["production_status_now"] = launcher.container_status(PRODUCTION)
    if not polled.get("ok"):
        record["logs_tail_40"] = launcher.docker_logs_tail(VARIANT, 40)
        record.update({"ok": False, "reason": f"health failed: {polled.get('reason')}"})
        write_json(LOGS / "variant-launch.json", record)
        return record

    info, raw = get_server_info()
    SERVER_INFO_PATH.write_bytes(raw)
    state = (info.get("internal_states") or [{}])[0]
    memory = state.get("memory_usage") or {}
    record["server_info"] = {
        "page_size": info.get("page_size"),
        "radix_eviction_policy": info.get("radix_eviction_policy"),
        "state_radix_eviction_policy": state.get("radix_eviction_policy"),
        "mamba_radix_cache_strategy": info.get("mamba_radix_cache_strategy"),
        "mem_fraction_static": info.get("mem_fraction_static"),
        "kv_cache_dtype": info.get("kv_cache_dtype"),
        "max_mamba_cache_size": info.get("max_mamba_cache_size"),
        "max_total_num_tokens": info.get("max_total_num_tokens"),
        "token_capacity": memory.get("token_capacity"),
        "context_length": state.get("context_length"),
        "disable_chunked_prefix_cache": state.get("disable_chunked_prefix_cache"),
        "server_version": info.get("version"),
        "server_status": info.get("status"),
        "info_sha256": sha256_bytes(raw),
    }
    record["ok"] = True
    log(f"variant up: policy={record['server_info']['radix_eviction_policy']} "
        f"capacity={record['server_info']['token_capacity']} "
        f"page_size={record['server_info']['page_size']} "
        f"mamba={record['server_info']['mamba_radix_cache_strategy']} "
        f"health_s={polled.get('seconds')}")
    write_json(LOGS / "variant-launch.json", record)
    return record


# --------------------------------------------------------------------------- #
# --measure : M4 battery semantics, P + R only
# --------------------------------------------------------------------------- #
def acquire_lock(path: Path, timeout_s: float):
    handle = path.open("a+", encoding="utf-8")
    deadline = time.monotonic() + timeout_s
    while True:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            break
        except BlockingIOError:
            if time.monotonic() >= deadline:
                handle.close()
                raise TimeoutError(f"occamy lock {path} busy")
            time.sleep(0.5)
    handle.seek(0)
    handle.truncate()
    json.dump({"unit": UNIT, "pid": os.getpid(), "acquired_utc": utc_now()}, handle)
    handle.flush()
    os.fsync(handle.fileno())
    return handle


def release_lock(handle) -> None:
    try:
        handle.seek(0)
        handle.truncate()
        json.dump({"unit": UNIT, "pid": os.getpid(), "released_utc": utc_now()}, handle)
        handle.flush()
        os.fsync(handle.fileno())
        fcntl.flock(handle, fcntl.LOCK_UN)
    finally:
        handle.close()


class Sender:
    def __init__(self) -> None:
        client_cls = _load_client()
        self._client = client_cls()
        self.sent = 0
        self.failures = 0
        self.consecutive_failures = 0
        self.first_error = None

    def send(self, messages) -> dict:
        if self.sent >= REQUEST_CAP:
            raise RuntimeError(f"request cap reached: {self.sent}/{REQUEST_CAP}")
        started = time.perf_counter()
        self.sent += 1
        out = {"request_index": self.sent, "status": None, "error": "", "ts_utc": utc_now()}
        try:
            prompt, cached, completion, ttft, wall, status, _text = self._client.chat(
                messages, max_tokens=MAX_TOKENS, thinking=False, stream=True, timeout=TIMEOUT_S)
            out.update(prompt_tokens=int(prompt), cached_tokens=int(cached),
                       completion_tokens=int(completion), ttft_ms=round(float(ttft), 3),
                       latency_ms=round(float(wall), 3),
                       status=int(status) if status is not None else None)
            if status is not None and int(status) != 200:
                raise RuntimeError(f"non-200 status {status}")
            self.consecutive_failures = 0
        except Exception as exc:  # noqa: BLE001 - the failure text is evidence
            self.failures += 1
            self.consecutive_failures += 1
            out["error"] = f"{type(exc).__name__}: {exc}"
            out["latency_ms"] = round((time.perf_counter() - started) * 1000, 3)
            out.setdefault("prompt_tokens", 0)
            out.setdefault("cached_tokens", 0)
            out.setdefault("completion_tokens", 0)
            out.setdefault("ttft_ms", 0.0)
            if self.first_error is None:
                self.first_error = out["error"]
        out["uncached_tokens"] = max(0, out["prompt_tokens"] - out["cached_tokens"])
        return out


def _load_client():
    path = REPO / "experiments" / "context-cache" / "client.py"
    spec = importlib.util.spec_from_file_location("tuned_ctx_client", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module.ChatClient


def append_row(row: dict) -> None:
    """Persist every request as it happens: a crash must not erase the battery."""

    with ROWS_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def band_positions(n: int) -> dict[str, list[int]]:
    middle_start = max(1, n // 2 - (BAND_SIZE // 2 - 1))
    middle = list(range(middle_start, min(n, middle_start + BAND_SIZE) + 1))[:BAND_SIZE]
    return {
        "newest": list(range(max(1, n - BAND_SIZE + 1), n + 1)),
        "middle": middle,
        "oldest": list(range(1, min(n, BAND_SIZE) + 1)),
    }


def measure() -> int:
    handle = acquire_lock(LOCK_PATH, LOCK_TIMEOUT_S)
    started = time.monotonic()
    started_utc = utc_now()
    rows: list[dict] = []
    try:
        ROWS_PATH.write_text("", encoding="utf-8")
        info, raw = get_server_info()
        SERVER_INFO_PATH.write_bytes(raw)
        state = (info.get("internal_states") or [{}])[0]
        memory = state.get("memory_usage") or {}
        capacity = memory.get("token_capacity") or info.get("max_total_num_tokens")
        if not isinstance(capacity, int) or capacity <= 0:
            raise RuntimeError(f"no usable token_capacity: {capacity!r}")
        policy = info.get("radix_eviction_policy") or state.get("radix_eviction_policy")
        log(f"capacity={capacity} policy={policy} page_size={info.get('page_size')} "
            f"version={info.get('version')}")

        docs = corpus_mod.load_corpus(M4_DIR / "corpus.jsonl")
        log(f"corpus: {len(docs)} docs reused from cells/M4/corpus.jsonl")
        sender = Sender()
        target_tokens = int(math.ceil(TARGET_RATIO * capacity))

        # ---- Phase P: distinct documents until 1.5x measured capacity ----
        pushed: list[dict] = []
        cumulative = 0
        aborted = False
        abort_reason = ""
        p_started = time.monotonic()
        for doc in docs[:MAX_DOCS]:
            if cumulative >= target_tokens:
                break
            messages = corpus_mod.messages_for(doc)
            sent = sender.send(messages)
            position = len(pushed) + 1
            cumulative += sent["prompt_tokens"]
            row = {"unit": UNIT, "phase": "P", "doc_id": doc["doc_id"],
                   "doc_position": position, "band": "push",
                   "prompt_tokens": sent["prompt_tokens"],
                   "cached_tokens": sent["cached_tokens"],
                   "uncached_tokens": sent["uncached_tokens"],
                   "completion_tokens": sent["completion_tokens"],
                   "latency_ms": sent["latency_ms"], "ttft_ms": sent["ttft_ms"],
                   "status": sent["status"], "error": sent["error"],
                   "request_index": sent["request_index"], "ts_utc": sent["ts_utc"],
                   "doc_chars": doc["chars"], "doc_body_sha256": doc["body_sha256"],
                   "doc_head_sha256": doc["head_sha256"],
                   "prompt_sha256": sha256_bytes(json.dumps(messages, sort_keys=True).encode()),
                   "messages": len(messages), "token_capacity": capacity,
                   "variant": VARIANT, "radix_eviction_policy": policy,
                   "cum_prompt_tokens": cumulative}
            rows.append(row)
            append_row(row)
            pushed.append({**doc, "position": position,
                           "prompt_tokens": sent["prompt_tokens"], "cum_end": cumulative})
            log(f"P {position:3d} {doc['doc_id']} prompt={sent['prompt_tokens']} "
                f"cached={sent['cached_tokens']} cum={cumulative} "
                f"ratio={cumulative / capacity:.3f} status={sent['status']}")
            if sender.consecutive_failures >= CONSECUTIVE_FAILURE_LIMIT:
                aborted = True
                abort_reason = sender.first_error or "3 consecutive failures"
                log(f"ABORT phase P: {abort_reason}")
                break
        p_wall = round(time.monotonic() - p_started, 3)
        log(f"phase P done docs={len(pushed)} pressure={cumulative} "
            f"ratio={cumulative / capacity:.4f} requests={sender.sent} wall={p_wall}s")

        # ---- Phase R: oldest 10 / middle 10 / newest 10, newest first ----
        by_position = {d["position"]: d for d in pushed}
        plan = band_positions(len(pushed))
        band_order = ["newest", "middle", "oldest"]
        for band in band_order:
            for position in plan[band]:
                doc = by_position[position]
                messages = corpus_mod.messages_for(doc)
                sent = sender.send(messages)
                row = {"unit": UNIT, "phase": "R", "doc_id": doc["doc_id"],
                       "doc_position": position, "band": band,
                       "prompt_tokens": sent["prompt_tokens"],
                       "cached_tokens": sent["cached_tokens"],
                       "uncached_tokens": sent["uncached_tokens"],
                       "completion_tokens": sent["completion_tokens"],
                       "latency_ms": sent["latency_ms"], "ttft_ms": sent["ttft_ms"],
                       "status": sent["status"], "error": sent["error"],
                       "request_index": sent["request_index"], "ts_utc": sent["ts_utc"],
                       "doc_chars": doc["chars"], "doc_body_sha256": doc["body_sha256"],
                       "doc_head_sha256": doc["head_sha256"],
                       "prompt_sha256": sha256_bytes(json.dumps(messages, sort_keys=True).encode()),
                       "messages": len(messages), "token_capacity": capacity,
                       "variant": VARIANT, "radix_eviction_policy": policy,
                       "cum_prompt_tokens": doc["cum_end"],
                       "cum_prompt_tokens_start": doc["cum_end"] - doc["prompt_tokens"],
                       "prompt_tokens_phase_p": doc["prompt_tokens"]}
                rows.append(row)
                append_row(row)
                log(f"R {band:6s} pos={position:3d} {doc['doc_id']} "
                    f"prompt={sent['prompt_tokens']} cached={sent['cached_tokens']} "
                    f"hit={sent['cached_tokens'] / max(1, sent['prompt_tokens']):.3f} "
                    f"status={sent['status']}")
                if sender.consecutive_failures >= CONSECUTIVE_FAILURE_LIMIT:
                    log(f"ABORT phase R: {sender.first_error}")
                    aborted = True
                    abort_reason = sender.first_error or "3 consecutive failures"
                    break
            if aborted:
                break

        run = {
            "unit": UNIT, "variant": VARIANT, "flag": list(FLAG),
            "endpoint": f"{BASE_URL}/get_server_info",
            "server_version": info.get("version"), "server_status": info.get("status"),
            "server_info_sha256": sha256_bytes(raw),
            "radix_eviction_policy": policy, "page_size": info.get("page_size"),
            "mamba_radix_cache_strategy": info.get("mamba_radix_cache_strategy"),
            "mem_fraction_static": info.get("mem_fraction_static"),
            "kv_cache_dtype": info.get("kv_cache_dtype"),
            "max_mamba_cache_size": info.get("max_mamba_cache_size"),
            "mamba_track_interval": info.get("mamba_track_interval"),
            "disable_chunked_prefix_cache": state.get("disable_chunked_prefix_cache"),
            "context_length": state.get("context_length"),
            "token_capacity": capacity,
            "capacity_sampled_utc": utc_now(),
            "capacity_source": "/get_server_info internal_states[0].memory_usage.token_capacity",
            "temperature": 0.0, "max_tokens": MAX_TOKENS, "requests_in_flight": 1,
            "pressure_target_ratio": TARGET_RATIO,
            "target_tokens": target_tokens,
            "total_pressure_tokens": cumulative,
            "pressure_ratio": round(cumulative / capacity, 6),
            "docs_pushed": len(pushed),
            "requests_used": sender.sent, "requests_cap": REQUEST_CAP,
            "requests_by_phase": {"P": len(pushed), "R": len(rows) - len(pushed)},
            "failures": sender.failures, "first_error": sender.first_error,
            "aborted": aborted, "abort_reason": abort_reason,
            "band_replay_order": band_order,
            "band_positions": plan,
            "phase_p_wall_s": p_wall,
            "wall_s": round(time.monotonic() - started, 3),
            "started_utc": started_utc, "finished_utc": utc_now(),
            "corpus_sha256": hashlib.sha256((M4_DIR / "corpus.jsonl").read_bytes()).hexdigest(),
            "corpus_source": "experiments/context-cache/cells/M4/corpus.jsonl",
        }
        for row in rows:
            row.update({k: run[k] for k in ("pressure_ratio", "total_pressure_tokens",
                                            "docs_pushed", "requests_used", "requests_cap")})
        with ROWS_PATH.open("w", encoding="utf-8") as out:
            for row in rows:
                out.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")
            out.flush()
            os.fsync(out.fileno())
        run["rows"] = len(rows)
        run["rows_sha256"] = sha256_bytes(ROWS_PATH.read_bytes())
        run["lock_held_s"] = round(time.monotonic() - started, 3)
        write_json(RUN_PATH, run)
        log(f"rows={len(rows)} sha256={run['rows_sha256']} requests={sender.sent} "
            f"failures={sender.failures}")
        return 0 if not aborted else 2
    except Exception as exc:  # noqa: BLE001
        log(f"MEASURE FAILED: {type(exc).__name__}: {exc}")
        write_json(HERE / "measure-failure.json",
                   {"unit": UNIT, "error": f"{type(exc).__name__}: {exc}",
                    "rows_written": len(rows), "utc": utc_now()})
        return 1
    finally:
        release_lock(handle)


# --------------------------------------------------------------------------- #
# --restore : one command per side, proven by a diff
# --------------------------------------------------------------------------- #
def restore() -> int:
    record = {"unit": UNIT, "step": "restore", "started_utc": utc_now()}
    launcher.remove_container(VARIANT)
    record["variant_status_after_rm"] = launcher.container_status(VARIANT)
    log(f"variant removed: {record['variant_status_after_rm']}")

    pre = json.loads((STATE / "tuned-pre.json").read_text(encoding="utf-8"))
    pre_cap = ((pre.get("internal_states") or [{}])[0].get("memory_usage") or {}).get(
        "token_capacity") or pre.get("max_total_num_tokens")

    attempts = []
    ok = False
    for attempt in (1, 2):
        state = launcher.service_start()
        status = launcher.container_status(PRODUCTION)
        polled = launcher.wait_health(PRODUCTION, deadline_s=900.0, poll_s=5.0)
        attempts.append({"attempt": attempt, "service": state, "status": status,
                         "health": polled})
        log(f"restore attempt {attempt}: service={state} status={status} "
            f"health={polled.get('health') or polled.get('reason')} "
            f"s={polled.get('seconds')}")
        if polled.get("ok"):
            ok = True
            break
    record["attempts"] = attempts
    if not ok:
        record["ok"] = False
        record["reason"] = "production did not come back after 2 attempts"
        record["logs_tail_40"] = launcher.docker_logs_tail(PRODUCTION, 40)
        write_json(LOGS / "restore.json", record)
        log("P0: production did not come back")
        return 1

    info, raw = get_server_info()
    (STATE / "tuned-restored.json").write_text(
        json.dumps(info, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    live_cap = ((info.get("internal_states") or [{}])[0].get("memory_usage") or {}).get(
        "token_capacity") or info.get("max_total_num_tokens")
    keys = ("page_size", "mamba_radix_cache_strategy", "radix_eviction_policy",
            "mem_fraction_static", "kv_cache_dtype", "max_mamba_cache_size",
            "mamba_track_interval", "disable_chunked_prefix_cache", "context_length",
            "max_total_num_tokens")
    diff = {
        "unit": UNIT, "step": "restore_diff", "utc": utc_now(),
        "pre_path": "state/config/tuned-pre.json",
        "restored_path": "state/config/tuned-restored.json",
        "keys": {k: {"pre": pre.get(k), "restored": info.get(k),
                     "equal": pre.get(k) == info.get(k)} for k in keys},
        "token_capacity": {"pre": pre_cap, "restored": live_cap,
                           "delta": (live_cap - pre_cap) if isinstance(live_cap, int)
                           and isinstance(pre_cap, int) else None,
                           "equal": pre_cap == live_cap,
                           "informational": "re-profiled at every start; excluded from the gate"},
        "server_info_sha256": sha256_bytes(raw),
        "variant_absent": launcher.container_status(VARIANT) == "absent",
    }
    gate_keys = ("page_size", "mamba_radix_cache_strategy", "radix_eviction_policy",
                 "mem_fraction_static", "kv_cache_dtype", "max_mamba_cache_size",
                 "mamba_track_interval", "disable_chunked_prefix_cache", "context_length")
    diff["config_ok"] = all(diff["keys"][k]["equal"] for k in gate_keys)
    diff["ok"] = diff["config_ok"] and diff["variant_absent"]

    models = json.loads(urllib.request.urlopen(f"{BASE_URL}/v1/models", timeout=20.0).read())
    model_ids = [m.get("id") for m in models.get("data") or []]
    mm_len = (models.get("data") or [{}])[0].get("max_model_len")
    diff["served"] = {"ids": model_ids, "max_model_len": mm_len,
                      "ok": "occamy-1.0" in model_ids and mm_len == 131072}
    diff["health"] = health()
    diff["health_ok"] = diff["health"] == 200
    diff["qwen9b_health"] = health("http://192.168.2.168:8014")
    diff["service"] = launcher.service_state()
    diff["ok"] = bool(diff["ok"] and diff["served"]["ok"] and diff["health_ok"])
    write_json(STATE / "tuned-restore-diff.json", diff)
    record["ok"] = diff["ok"]
    record["diff"] = diff
    write_json(LOGS / "restore.json", record)
    log(f"restore ok={diff['ok']} config_ok={diff['config_ok']} health={diff['health']} "
        f"models={model_ids} max_model_len={mm_len} qwen9b={diff['qwen9b_health']} "
        f"capacity {pre_cap} -> {live_cap}")
    return 0 if diff["ok"] else 1


def status() -> int:
    out = {
        "production": launcher.container_status(PRODUCTION),
        "variant": launcher.container_status(VARIANT),
        "service": launcher.service_state(),
        "occamy_health": health(),
        "qwen9b_health": health("http://192.168.2.168:8014"),
    }
    print(json.dumps(out, indent=2))
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--launch", action="store_true")
    ap.add_argument("--measure", action="store_true")
    ap.add_argument("--restore", action="store_true")
    ap.add_argument("--status", action="store_true")
    args = ap.parse_args(argv)
    if args.launch:
        pre = capture_pre()
        if not pre["diff"]["production_intact"]:
            log("P0: production already inconsistent at step 0 - not touching it")
            return 9
        record = launch_variant()
        return 0 if record.get("ok") else 1
    if args.measure:
        return measure()
    if args.restore:
        return restore()
    if args.status:
        return status()
    ap.error("one of --launch/--measure/--restore/--status is required")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
