#!/usr/bin/env python3
"""PROMPT-O4 — five prompt arms x 71 turns, qwen3.5-9b on **vLLM** (:8016).

S2 of the 16-cell prompt factorial: the vLLM leg that had no per-arm prompt
measurement at all (only the R-arm battery).  Arms, salt scheme, prompt
builders and budget fitting are copied VERBATIM from
``experiments/context-cache/cells/PROMPT-O2-EXTRA/prompt_o2e_cell.py`` so the
arms stay the same artefacts across engines (SGLang vs vLLM).

Arms:
  R   resend every turn, full body, no structure      (round-1 render("R"))
  A   stable scaffold + pointer index + newest delta  (round-1 render("A"))
  C   A with TAG[t=...] terminating the delta         (round-1 render("C"))
  H   hybrid/compaction, folds every 8 turns          (round-1 render("H"))
  C0  plain chat transcript: system + verbatim history (role-separated, no index)

Config: ``state/config/best-config.json`` -> ``setups.O4`` (read, never
re-derived).  Endpoint ``RESEXTRACT_O4_BASE_URL``
(default http://192.168.2.168:8016/v1).

G0 gate (MANDATORY, stricter than O2E): two identical warm-up calls; the
second MUST report ``usage.prompt_tokens_details.cached_tokens > 0`` AND
``prompt_tokens_details`` present.  vLLM 0.27.1 with
``--enable-prompt-tokens-details`` always returns a dict (0 on a pure miss), so
absence of the key — not a 0 — is the blind signal here; a 0 on the *second
identical* call is a real gate failure.  On failure the cell writes
``GAMMA: unavailable`` with the raw body and returns without running the
battery.

Guards:
  * ARMS_IDENTICAL: each arm's turn-1 prompt is hashed; any two equal ->
    ``status="invalid_arms_identical"``.
  * cold start: each arm gets a fresh salt preamble so turn 1 cannot be
    served from another arm's prefix.
  * non-200 / missing or null cached_tokens -> abort, no row written.

Extra output for this cell: the **resolve block** — the startup lines giving
``block_size`` / ``hash_block_size`` / ``mamba_block_size`` — and the observed
**gcd of cached_tokens** across all rows.  With ``--prefix-match-unit 16`` the
observed grid should be 16-multiples; the gcd is the measurement of that.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import math
import os
import re
import statistics
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
assert (REPO / "src" / "resextract").is_dir(), f"repo root not found from {HERE}"

CELL = "PROMPT-O4B"
ROWS_PATH = HERE / "rows.jsonl"
ANALYSIS_PATH = HERE / "analysis.json"
EVENTS_PATH = HERE / "events.jsonl"
WARMUP_PATH = HERE / "warmup.json"
LAUNCH_PATH = HERE / "launch.json"
G0_PATH = HERE / "g0.json"
SUMMARY_PATH = HERE / "summary.json"
LOCK_PATH = REPO / "experiments" / "context-cache" / ".occamy.lock"
BEST_CONFIG = REPO / "state" / "config" / "best-config.json"
RENDERER_PATH = REPO / "experiments" / "context-cache" / "cells" / "VLLM-CELL" / "vllm_cell.py"
HANDOFF_PATH = REPO / "orchestration" / "handoffs" / f"{CELL}.json"
UNIT_PATH = REPO / "orchestration" / "units" / f"{CELL}.md"

BASE_URL = os.environ.get("RESEXTRACT_O4_BASE_URL", "http://192.168.2.168:8016/v1")
TURNS = 71
BUDGET_TOKENS = 32768
MAX_TOKENS = 8
ALPHA = 0.05
CONTAINER = os.environ.get("RESEXTRACT_O4_CONTAINER", "gx10-p-o4")
REQUESTS_CAP = 500

ROUND1_ARMS = ("R", "A", "C", "H")
ARMS = ("R", "A", "C", "H", "C0")


# --------------------------------------------------------------------------- #
# Imports
# --------------------------------------------------------------------------- #
def load_module(name: str, path: Path):
    import importlib.util

    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def load_client():
    path = REPO / "experiments" / "context-cache" / "client.py"
    return load_module("ctx_client_prompt_o4", path).ChatClient


# --------------------------------------------------------------------------- #
# Config (read, never re-derived)
# --------------------------------------------------------------------------- #
def load_setup() -> dict:
    cfg = json.loads(BEST_CONFIG.read_text(encoding="utf-8"))
    setup = cfg["setups"]["O4"]
    if setup.get("config_id") != "O4":
        raise RuntimeError(f"setups.O4 carries config_id={setup.get('config_id')!r}")
    return {
        "model": setup["model"],
        "engine": setup["engine"],
        "config_id": setup["config_id"],
        "config_sha256": setup["config_sha256"],
        "argv": list(setup["argv"]),
    }


# --------------------------------------------------------------------------- #
# Arms — VERBATIM from PROMPT-O2-EXTRA (salt tag included) so the arm bodies
# are the same bytes across engines.
# --------------------------------------------------------------------------- #
SALT_TAG = "occamy-prompt-o1 salt:%s"


def salt_preamble(arm: str) -> str:
    digest = hashlib.sha256(f"PROMPT-O2|{arm}|2026-10-24".encode("utf-8")).hexdigest()
    return SALT_TAG % digest[:16]


def arm_text(renderer, arm: str, turn: int) -> str:
    if arm in ROUND1_ARMS:
        return renderer.render(arm, turn)[0]["content"]
    if arm == "C0":
        return (renderer.SCAFFOLD + "TRANSCRIPT:\n"
                + renderer.body_upto(turn) + "\n" + renderer.CANARY)
    raise ValueError(f"unknown arm {arm!r}")


def arm_messages(renderer, arm: str, turn: int) -> list[dict]:
    content = salt_preamble(arm) + "\n" + arm_text(renderer, arm, turn)
    first = [{"role": "user", "content": content}]
    if arm == "C0":
        first = [{"role": "system", "content": salt_preamble(arm) + "\n" + renderer.SCAFFOLD}]
        for t in range(1, turn + 1):
            first.append({"role": "assistant" if t % 2 == 0 else "user",
                          "content": renderer.delta_block(t)})
        first.append({"role": "user", "content": renderer.CANARY})
        return first
    return first


def prompt_sha(messages: list[dict]) -> str:
    return hashlib.sha256(json.dumps(messages, sort_keys=True, ensure_ascii=False)
                          .encode("utf-8")).hexdigest()


def prefix_sha(messages: list[dict]) -> str:
    return hashlib.sha256(json.dumps([messages[0], len(messages)], sort_keys=True,
                                     ensure_ascii=False).encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------- #
# Stats (incomplete-beta t distribution, ddof=1) — same as O2E
# --------------------------------------------------------------------------- #
def _betacf(a: float, b: float, x: float) -> float:
    MAXIT, EPS, FPMIN = 200, 3e-14, 1e-300
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c, d = 1.0, 1.0 - qab * x / qap
    if abs(d) < FPMIN:
        d = FPMIN
    d = 1.0 / d
    h = d
    for m in range(1, MAXIT + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        d = FPMIN if abs(d) < FPMIN else d
        c = 1.0 + aa / c
        c = FPMIN if abs(c) < FPMIN else c
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        d = FPMIN if abs(d) < FPMIN else d
        c = 1.0 + aa / c
        c = FPMIN if abs(c) < FPMIN else c
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < EPS:
            break
    return h


def _betai(a: float, b: float, x: float) -> float:
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    bt = math.exp(math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
                  + a * math.log(x) + b * math.log(1.0 - x))
    if x < (a + 1.0) / (a + b + 2.0):
        return bt * _betacf(a, b, x) / a
    return 1.0 - bt * _betacf(b, a, 1.0 - x) / b


def t_cdf(t: float, df: float) -> float:
    tail = 0.5 * _betai(df / 2.0, 0.5, df / (df + t * t))
    return 1.0 - tail if t > 0 else tail


def t_ppf(p: float, df: float) -> float:
    if not 0.5 < p < 1.0:
        raise ValueError("p must be in (0.5, 1)")
    lo, hi = 0.0, 200.0
    for _ in range(200):
        mid = (lo + hi) / 2.0
        if t_cdf(mid, df) < p:
            lo = mid
        else:
            hi = mid
        if hi - lo < 1e-10:
            break
    return (lo + hi) / 2.0


def mean_ci(values: list[float]) -> dict:
    n = len(values)
    mean = statistics.fmean(values)
    if n < 2:
        return {"n": n, "mean": mean, "sd": None, "se": None,
                "ci95": None, "ci95_excludes_zero": None}
    sd = statistics.stdev(values)
    se = sd / n ** 0.5
    half = t_ppf(1.0 - ALPHA / 2.0, n - 1) * se
    lo, hi = mean - half, mean + half
    return {"n": n, "mean": mean, "sd": sd, "se": se,
            "t_crit": t_ppf(1.0 - ALPHA / 2.0, n - 1), "ci95": [lo, hi],
            "ci95_excludes_zero": bool(lo > 0 or hi < 0)}


def paired_delta(a_vals: list[float], b_vals: list[float]) -> dict:
    if len(a_vals) != len(b_vals):
        raise RuntimeError(f"paired delta needs equal n: {len(a_vals)} vs {len(b_vals)}")
    diffs = [a - b for a, b in zip(a_vals, b_vals)]
    out = mean_ci(diffs)
    out["sum_diff"] = sum(diffs)
    out["a_minus_b"] = out["mean"]
    return out


# --------------------------------------------------------------------------- #
# Resolve block (startup lines) — vLLM logs block sizes it actually resolved
# --------------------------------------------------------------------------- #
RESOLVE_PAT = re.compile(
    r"(?P<key>block_size|hash_block_size|mamba_block_size|prefix_match_unit|"
    r"page_size|kv_cache_block_size)\s*[=:]\s*(?P<val>\d+)", re.IGNORECASE)


def resolve_block() -> dict:
    """Pull block-size resolution lines out of the container's startup log."""

    out = {"container": CONTAINER, "source": "docker logs", "raw_lines": [],
           "resolved": {}, "max_model_len": None, "kv_cache_tokens": None}
    try:
        proc = subprocess.run(["docker", "logs", CONTAINER], capture_output=True,
                              text=True, timeout=60)
        log = (proc.stdout or "") + (proc.stderr or "")
    except Exception as exc:  # noqa: BLE001
        out["error"] = f"{type(exc).__name__}: {exc}"
        return out
    if not log.strip():
        out["note"] = ("docker logs is empty for this container (likely started with "
                       "--log-driver none); block sizes therefore come from the "
                       "container Config.Cmd, which is recorded below")
    for line in log.splitlines():
        low = line.lower()
        if any(t in low for t in ("block_size", "block size", "prefix_match_unit",
                                  "mamba_block_size", "hash_block_size",
                                  "non-default args", "available kv cache",
                                  "gpu kv cache size", "using max model len")):
            if len(out["raw_lines"]) < 40:
                out["raw_lines"].append(line.strip()[:600])
            m = re.search(r"Using max model len (\d+)", line)
            if m:
                out["max_model_len"] = int(m.group(1))
            m = re.search(r"GPU KV cache size:\s*([\d,]+)", line)
            if m:
                out["kv_cache_tokens"] = int(m.group(1).replace(",", ""))
        for m in RESOLVE_PAT.finditer(line):
            out["resolved"].setdefault(m.group("key").lower(), int(m.group("val")))
    # non-default args dict carries the authoritative resolved block sizes
    m = re.search(r"non-default args: (\{.*\})", log)
    if m:
        try:
            args = json.loads(m.group(1).replace("'", '"'))
        except Exception:  # noqa: BLE001
            args = {}
        for k in ("block_size", "hash_block_size", "mamba_block_size",
                  "prefix_match_unit", "max_model_len"):
            if k in args:
                out["resolved"][k] = args[k]
        out["non_default_args"] = {k: v for k, v in args.items()
                                   if k in ("block_size", "hash_block_size",
                                            "mamba_block_size", "prefix_match_unit",
                                            "max_model_len", "kv_cache_dtype",
                                            "mamba_cache_mode", "quantization")}
    else:
        # fallback: the container's own resolved Config.Cmd
        try:
            proc = subprocess.run(["docker", "inspect", CONTAINER, "--format",
                                   "{{json .Config.Cmd}}"],
                                  capture_output=True, text=True, timeout=30)
            cmd = json.loads(proc.stdout)
            out["container_cmd"] = cmd
            for i, tok in enumerate(cmd):
                key = str(tok).lstrip("-").replace("-", "_")
                if key in ("block_size", "hash_block_size", "mamba_block_size",
                           "prefix_match_unit", "max_model_len") and i + 1 < len(cmd):
                    try:
                        out["resolved"][key] = int(cmd[i + 1])
                    except ValueError:
                        pass
        except Exception as exc:  # noqa: BLE001
            out["config_error"] = f"{type(exc).__name__}: {exc}"
    return out


def grid_gcd(rows: list[dict]) -> dict:
    """Observed cached_tokens grid across every row with cached > 0."""

    vals = [int(r["cached_tokens"]) for r in rows if r.get("cached_tokens")]
    g = 0
    for v in vals:
        g = math.gcd(g, v)
    mod16 = [v % 16 for v in vals]
    mod64 = [v % 64 for v in vals]
    return {
        "n_positive_cached_rows": len(vals),
        "gcd_cached_tokens": g,
        "gcd_is_16_multiple": bool(g and g % 16 == 0),
        "all_rows_multiple_of_16": bool(vals) and all(v % 16 == 0 for v in vals),
        "all_rows_multiple_of_64": bool(vals) and all(v % 64 == 0 for v in vals),
        "distinct_mod16": sorted(set(mod16))[:10],
        "distinct_mod64": sorted(set(mod64))[:10],
        "min_positive": min(vals) if vals else None,
        "max_positive": max(vals) if vals else None,
        "sample": sorted(set(vals))[:12],
    }


# --------------------------------------------------------------------------- #
# HTTP
# --------------------------------------------------------------------------- #
def call(client, messages, max_tokens=MAX_TOKENS, timeout=180.0) -> dict:
    """One NON-streaming chat call.

    The shared client always sets ``stream_options`` (it is a streaming
    wrapper).  vLLM 0.27.1 rejects that with HTTP 400
    "Stream options can only be defined when `stream=True`", so for this cell
    the body is built here without it: a non-streaming response carries the
    complete ``usage.prompt_tokens_details`` in one object.
    """
    used = client.payload(messages, max_tokens=max_tokens, thinking=False, stream=False)
    used.pop("stream_options", None)
    started = time.perf_counter()
    with client._http(timeout) as http:  # noqa: SLF001 - the class is the contract
        resp = http.post("/chat/completions", json=used)
    wall_ms = (time.perf_counter() - started) * 1000.0
    body = resp.text
    try:
        payload = resp.json()
    except Exception:  # noqa: BLE001
        payload = None
    usage = (payload or {}).get("usage") if isinstance(payload, dict) else None
    details = (usage or {}).get("prompt_tokens_details") if isinstance(usage, dict) else None
    cached = details.get("cached_tokens") if isinstance(details, dict) else None
    prompt = usage.get("prompt_tokens") if isinstance(usage, dict) else None
    return {
        "http_status": int(resp.status_code),
        "usage": usage,
        "prompt_tokens": None if prompt is None else int(prompt),
        "cached_tokens": None if cached is None else int(cached),
        "details_present": isinstance(details, dict),
        "wall_ms": round(wall_ms, 3),
        "body": body,
    }


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def append_row(row: dict) -> None:
    with ROWS_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")
        fh.flush()
        os.fsync(fh.fileno())


def write_json(path: Path, payload) -> None:
    tmp = HERE / (path.name + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def acquire_lock(timeout_s: float = 600.0):
    handle = LOCK_PATH.open("a+", encoding="utf-8")
    deadline = time.monotonic() + timeout_s
    while True:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            break
        except BlockingIOError:
            if time.monotonic() >= deadline:
                handle.close()
                raise TimeoutError(f"occamy lock {LOCK_PATH} busy for {timeout_s:.0f}s")
            time.sleep(0.5)
    handle.seek(0)
    handle.truncate()
    json.dump({"unit": CELL, "pid": os.getpid(), "acquired_utc": utc_now(),
               "scope": f"{CELL} five-arm prompt cell on vLLM :8016; held for the whole run"},
              handle)
    handle.flush()
    os.fsync(handle.fileno())
    return handle


def release_lock(handle) -> None:
    try:
        handle.seek(0)
        handle.truncate()
        json.dump({"unit": CELL, "pid": os.getpid(), "released_utc": utc_now()}, handle)
        handle.flush()
        os.fsync(handle.fileno())
        fcntl.flock(handle, fcntl.LOCK_UN)
    finally:
        handle.close()


# --------------------------------------------------------------------------- #
# Analysis
# --------------------------------------------------------------------------- #
def analyse(rows: list[dict], guard: dict) -> dict:
    by_arm: dict[str, list[dict]] = {a: [] for a in ARMS}
    for r in rows:
        by_arm.setdefault(str(r["arm"]), []).append(r)

    per_arm: dict[str, dict] = {}
    series: dict[str, list[float]] = {}
    for arm in ARMS:
        rs = sorted(by_arm.get(arm, []), key=lambda r: int(r["turn"]))
        unc = [float(r["uncached_tokens"]) for r in rs if r.get("uncached_tokens") is not None]
        series[arm] = unc
        if not unc:
            per_arm[arm] = {"n_rows": len(rs), "mean_uncached_per_turn": None, "sd": None,
                            "ci95": None, "ci95_excludes_zero": None,
                            "total_prompt_tokens": 0, "total_cached_tokens": 0,
                            "total_uncached_tokens": 0, "hit_fraction_weighted": None,
                            "hit_fraction_mean_per_turn": None, "series_uncached": []}
            continue
        prompt = sum(int(r["prompt_tokens"]) for r in rs if r.get("prompt_tokens") is not None)
        cached = sum(int(r["cached_tokens"]) for r in rs if r.get("cached_tokens") is not None)
        ci = mean_ci(unc)
        per_arm[arm] = {
            "n_rows": len(rs),
            "turns": [int(r["turn"]) for r in rs],
            "mean_uncached_per_turn": ci["mean"],
            "sd": ci["sd"],
            "ci95": ci["ci95"],
            "ci95_excludes_zero": ci["ci95_excludes_zero"],
            "t_crit": ci.get("t_crit"),
            "total_prompt_tokens": prompt,
            "total_cached_tokens": cached,
            "total_uncached_tokens": int(sum(unc)),
            "hit_fraction_weighted": (cached / prompt) if prompt else None,
            "hit_fraction_mean_per_turn": (
                statistics.fmean([int(r["cached_tokens"]) / int(r["prompt_tokens"])
                                  for r in rs if r.get("cached_tokens") is not None
                                  and int(r["prompt_tokens"]) > 0]) if rs else None),
            "min_uncached": min(unc) if unc else None,
            "max_uncached": max(unc) if unc else None,
            "series_uncached": unc,
        }

    deltas: dict[str, dict] = {}
    for arm in ("A", "C", "H", "C0"):
        if not series.get(arm) or not series.get("R"):
            deltas[f"{arm}-R"] = {"mean_uncached_per_turn_delta": None, "ci95": None,
                                  "sum_diff_tokens": None, "excludes_zero": None,
                                  "n_pairs": 0}
            continue
        d = paired_delta(series.get(arm, []), series.get("R", []))
        deltas[f"{arm}-R"] = {
            "mean_uncached_per_turn_delta": d["mean"],
            "ci95": d["ci95"],
            "sum_diff_tokens": d["sum_diff"],
            "excludes_zero": d["ci95_excludes_zero"],
            "n_pairs": d["n"],
        }

    invalid = bool(guard.get("arms_identical"))
    return {
        "unit": CELL,
        "cell": CELL,
        "status": "invalid_arms_identical" if invalid else (
            "done" if len(rows) == TURNS * len(ARMS) else "partial"),
        "arms_identical_guard": guard,
        "method": {
            "metric": "uncached_tokens = prompt_tokens - prompt_tokens_details.cached_tokens",
            "interval": f"two-sided {1-ALPHA:.0%} t-interval, ddof=1, df=n-1, "
                        "paired over turns for deltas",
            "turns": TURNS,
            "budget_tokens": BUDGET_TOKENS,
            "n_rows": len(rows),
        },
        "per_arm": per_arm,
        "deltas_vs_R": deltas,
    }


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main() -> int:
    HERE.mkdir(parents=True, exist_ok=True)
    setup = load_setup()
    renderer = load_module("vllm_cell_round1", RENDERER_PATH)
    ChatClient = load_client()
    client = ChatClient(base_url=BASE_URL, model=setup["model"], timeout=180.0)

    resolve = resolve_block()
    write_json(LAUNCH_PATH, {"argv": setup["argv"], "config_sha256": setup["config_sha256"],
                             "container": CONTAINER, "image": "2c211a1273b4",
                             "endpoint": BASE_URL, "resolve_block": resolve})
    print(f"resolve block: {json.dumps(resolve.get('resolved'))}", flush=True)

    hashes = {a: hashlib.sha256(
        json.dumps(arm_messages(renderer, a, 1), sort_keys=True).encode()).hexdigest()
        for a in ARMS}
    collisions = []
    for i, a in enumerate(ARMS):
        for b in ARMS[i + 1:]:
            if hashes[a] == hashes[b]:
                collisions.append(f"{a}=={b}")
    guard = {"arm_first_prompt_sha256": hashes, "collisions": collisions,
             "arms_identical": bool(collisions)}
    print(f"ARMS_IDENTICAL guard: collisions={collisions or 'none'}", flush=True)

    handle = acquire_lock()
    try:
        # --- G0 gate: two identical calls, second must show cached_tokens > 0
        warm_msgs = [{"role": "user", "content": (
            "PROMPT-O4 warm-up. Reply with the single word: ready.\n"
            "padding: " + ("cache probe block 0123456789 " * 400))}]
        warm1 = call(client, warm_msgs, max_tokens=8)
        warm2 = call(client, warm_msgs, max_tokens=8)
        warm = {
            "url": BASE_URL + "/chat/completions",
            "model": setup["model"],
            "call1": {k: warm1[k] for k in ("http_status", "prompt_tokens",
                                            "cached_tokens", "details_present", "usage")},
            "call2": {k: warm2[k] for k in ("http_status", "prompt_tokens",
                                            "cached_tokens", "details_present", "usage")},
            "call2_body": warm2["body"][:2000],
        }
        write_json(WARMUP_PATH, warm)
        write_json(G0_PATH, {
            "call1": {"prompt_tokens": warm1["prompt_tokens"],
                      "details": (warm1["usage"] or {}).get("prompt_tokens_details")},
            "call2": {"prompt_tokens": warm2["prompt_tokens"],
                      "details": (warm2["usage"] or {}).get("prompt_tokens_details")},
            "url": BASE_URL + "/chat/completions"})
        print(f"G0: call1 cached={warm1['cached_tokens']} call2 cached={warm2['cached_tokens']} "
              f"details={warm2['details_present']} status={warm2['http_status']}", flush=True)

        gate_ok = (warm2["http_status"] == 200 and warm2["details_present"]
                   and warm2["cached_tokens"] is not None and warm2["cached_tokens"] > 0)
        if not gate_ok:
            payload = {
                "unit": CELL, "cell": CELL, "stack": "vllm",
                "config_id": setup["config_id"],
                "status": "GAMMA: unavailable",
                "reason": "G0 gate failed: second identical warm-up call did not report "
                          "usage.prompt_tokens_details.cached_tokens > 0",
                "g0": {"call1": warm["call1"], "call2": warm["call2"]},
                "raw_body": warm2["body"][:4000],
                "arms_identical_guard": guard, "n_rows": 0,
                "resolve_block": resolve,
            }
            write_json(ANALYSIS_PATH, payload)
            write_handoff(payload, [], "", 2, warm2)
            print("STOP: GAMMA unavailable. raw body: " + warm2["body"][:1500], flush=True)
            return 2

        # --- measurement ---------------------------------------------------- #
        done = set()
        if ROWS_PATH.exists():
            for line in ROWS_PATH.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    try:
                        r = json.loads(line)
                        done.add((r["arm"], int(r["turn"])))
                    except Exception:  # noqa: BLE001
                        continue
        requests = 2
        aborted = None
        for arm in ARMS:
            for turn in range(1, TURNS + 1):
                if (arm, turn) in done:
                    continue
                if requests >= REQUESTS_CAP:
                    aborted = {"reason": "request cap reached", "arm": arm, "turn": turn}
                    break
                messages = arm_messages(renderer, arm, turn)
                fitted, truncated = renderer.fit_budget(messages, BUDGET_TOKENS)
                blob = json.dumps(fitted)
                pad_tokens = renderer.estimate_tokens(blob)
                res = call(client, fitted)
                requests += 1
                if res["http_status"] != 200 or res["cached_tokens"] is None \
                        or res["prompt_tokens"] is None:
                    aborted = {"arm": arm, "turn": turn, "http_status": res["http_status"],
                               "cached_tokens": res["cached_tokens"],
                               "details_present": res["details_present"],
                               "body": res["body"][:3000]}
                    write_json(EVENTS_PATH, {"aborted": aborted, "requests": requests})
                    print(f"ABORT {arm} turn {turn}: http={res['http_status']} "
                          f"cached={res['cached_tokens']} body={res['body'][:600]}", flush=True)
                    break
                row = {
                    "stack": "vllm",
                    "config_id": setup["config_id"],
                    "config_sha256": setup["config_sha256"],
                    "model": setup["model"],
                    "engine": setup["engine"],
                    "engine_version": "0.27.1",
                    "arm": arm,
                    "turn": turn,
                    "prompt_tokens": res["prompt_tokens"],
                    "cached_tokens": res["cached_tokens"],
                    "uncached_tokens": res["prompt_tokens"] - res["cached_tokens"],
                    "http_status": res["http_status"],
                    "prefix_sha256": prefix_sha(fitted),
                    "pad_tokens": pad_tokens,
                    "prompt_sha256": prompt_sha(fitted),
                    "prompt_bytes": len(blob),
                    "messages": len(fitted),
                    "truncated": bool(truncated),
                    "budget_tokens": BUDGET_TOKENS,
                    "wall_ms": res["wall_ms"],
                    "cold_null_details": False,
                    "ts_utc": utc_now(),
                }
                append_row(row)
                if turn % 10 == 0 or turn == 1:
                    print(f"  {arm} t{turn:2d} prompt={row['prompt_tokens']} "
                          f"cached={row['cached_tokens']} unc={row['uncached_tokens']}",
                          flush=True)
            if aborted:
                break

        rows = [json.loads(l) for l in ROWS_PATH.read_text(encoding="utf-8").splitlines()
                if l.strip()] if ROWS_PATH.exists() else []
        payload = analyse(rows, guard)
        payload["stack"] = "vllm"
        payload["config_id"] = setup["config_id"]
        payload["config_sha256"] = setup["config_sha256"]
        payload["warmup_cached_tokens"] = warm2["cached_tokens"]
        payload["g0"] = {"call1_cached": warm1["cached_tokens"],
                         "call2_cached": warm2["cached_tokens"],
                         "call1_prompt_tokens": warm1["prompt_tokens"]}
        payload["resolve_block"] = resolve
        payload["observed_grid"] = grid_gcd(rows)
        payload["requests"] = {"total": requests, "cap": REQUESTS_CAP}
        payload["config"] = {k: setup[k] for k in
                             ("model", "engine", "config_id", "config_sha256")}
        payload["renderer_source"] = {
            "path": str(RENDERER_PATH.relative_to(REPO)),
            "sha256": hashlib.sha256(RENDERER_PATH.read_bytes()).hexdigest(),
            "note": "round-1 renderer imported verbatim; arms + salt copied verbatim "
                    "from cells/PROMPT-O2-EXTRA/prompt_o2e_cell.py",
            "arms_source": "experiments/context-cache/cells/PROMPT-O2-EXTRA/prompt_o2e_cell.py",
            "arms_source_sha256": hashlib.sha256(
                (REPO / "experiments" / "context-cache" / "cells" / "PROMPT-O2-EXTRA"
                 / "prompt_o2e_cell.py").read_bytes()).hexdigest(),
        }
        if aborted:
            payload["aborted"] = aborted
            payload["status"] = "failed_http" if "http_status" in aborted else "partial"
        write_json(ANALYSIS_PATH, payload)
        write_json(SUMMARY_PATH, {
            "hit": {a: (None if v["hit_fraction_weighted"] is None
                        else round(v["hit_fraction_weighted"], 6))
                    for a, v in payload["per_arm"].items()},
            "deltas": {k: (None if v["mean_uncached_per_turn_delta"] is None else
                           round(v["mean_uncached_per_turn_delta"], 1))
                       for k, v in payload["deltas_vs_R"].items()},
            "arms_identical_guard": guard,
            "observed_grid": payload["observed_grid"],
        })
        rows_sha = (hashlib.sha256(ROWS_PATH.read_bytes()).hexdigest()
                    if ROWS_PATH.exists() else "")
        write_handoff(payload, rows, rows_sha, requests, warm2)
        print(json.dumps({"status": payload["status"], "rows": len(rows),
                          "rows_sha256": rows_sha,
                          "gcd": payload["observed_grid"]["gcd_cached_tokens"]}, indent=1),
              flush=True)
        return 0 if payload["status"] == "done" else 3
    finally:
        release_lock(handle)


def write_handoff(payload: dict, rows: list[dict], rows_sha: str, requests: int,
                  warm2: dict) -> None:
    pa = payload.get("per_arm") or {}
    dl = payload.get("deltas_vs_R") or {}
    rb = payload.get("resolve_block") or {}
    grid = payload.get("observed_grid") or {}
    cmd_rows = f"wc -l experiments/context-cache/cells/{CELL}/rows.jsonl"
    cmd_guard = (
        "python3 -c \"import json;rows=[json.loads(l) for l in "
        f"open('experiments/context-cache/cells/{CELL}/rows.jsonl')];"
        "print(sorted({r['arm'] for r in rows}), sum(1 for r in rows if "
        "r['cached_tokens'] is None), sum(1 for r in rows if r['http_status']!=200), "
        "sum(1 for r in rows if (r['cached_tokens'] or 0)>0))\"")
    evidence = {
        cmd_rows: str(len(rows)),
        cmd_guard: (f"{sorted({r['arm'] for r in rows})} "
                    f"{sum(1 for r in rows if r['cached_tokens'] is None)} "
                    f"{sum(1 for r in rows if r['http_status'] != 200)} "
                    f"{sum(1 for r in rows if (r['cached_tokens'] or 0) > 0)}"),
        "g0_warmup_call2_cached_tokens": str(warm2.get("cached_tokens")),
        "resolve_block": json.dumps(rb.get("resolved")),
        "observed_grid_gcd": str(grid.get("gcd_cached_tokens")),
        "per_arm_mean_uncached_per_turn": {
            a: (None if v["mean_uncached_per_turn"] is None
                else round(v["mean_uncached_per_turn"], 4)) for a, v in pa.items()},
        "per_arm_ci95": {a: v.get("ci95") for a, v in pa.items()},
        "deltas_vs_R": {k: [None if v["mean_uncached_per_turn_delta"] is None
                            else round(v["mean_uncached_per_turn_delta"], 4),
                            v["excludes_zero"]] for k, v in dl.items()},
        "arms_identical": payload["arms_identical_guard"]["collisions"] or "none",
        "requests": str(requests),
        "commands": [
            f".venv/bin/python experiments/context-cache/cells/{CELL}/prompt_o4_cell.py",
            cmd_rows, cmd_guard,
        ],
    }
    handoff = {
        "unit": CELL,
        "status": {"done": "done"}.get(payload["status"], "failed"),
        "stack": "vllm",
        "config_id": payload.get("config_id"),
        "artifacts": [
            f"experiments/context-cache/cells/{CELL}/rows.jsonl",
            f"experiments/context-cache/cells/{CELL}/analysis.json",
            f"experiments/context-cache/cells/{CELL}/warmup.json",
            f"experiments/context-cache/cells/{CELL}/launch.json",
            f"experiments/context-cache/cells/{CELL}/summary.json",
        ],
        "evidence": evidence,
        "blocker": payload.get("reason") or (payload.get("aborted") and
                                             json.dumps(payload["aborted"])[:400]) or "",
        "next_unit_hint": "verifier re-runs the two acceptance commands, rebuilds the "
                          "per-arm t-intervals from rows.jsonl and confirms the 16-grid gcd",
        "write_paths": [f"experiments/context-cache/cells/{CELL}/**",
                        f"orchestration/handoffs/{CELL}.json",
                        f"orchestration/units/{CELL}.md"],
        "detail": {"rows_sha256": rows_sha, "requests": requests,
                   "status": payload["status"],
                   "g0_gate": "passed" if warm2.get("cached_tokens") else "failed"},
    }
    HANDOFF_PATH.write_text(json.dumps(handoff, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
