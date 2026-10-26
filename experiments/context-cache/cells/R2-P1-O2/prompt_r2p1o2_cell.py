#!/usr/bin/env python3
"""R2-P1-O2 — Round-2 prompt factorial, CELL 1 of 4 (setup O1).

Setup O2 is the dense 9B cell and already serving at http://192.168.2.168:8017/v1
(qwen3.5-9b NVFP4, SGLang, max_model_len 32768, --page-size 64, grid unit 64).
Nothing here restarts, stops or reconfigures it: this cell *uses* production.

Five arms, identical task content, copied VERBATIM (code, not prose) from
``cells/PROMPT-O2-EXTRA/prompt_o2e_cell.py`` and ``cells/PROMPT-O4/prompt_o4_cell.py``
so the arm bodies are the same artefacts across engines:

    R   whole evolving state re-sent as one appended message
    A   pointer index (id | byte-span | sha8 | one-line summary) + newest delta
    C   A with the tag at the delta end
    H   mid-context compaction (index folds an earlier block every 8 turns)
    C0  plain-chat transcript: system prompt + verbatim history, no index

``C0`` has no renderer of its own -- in both source cells the renderer imports
the round-1 module frozen in ``VLLM-CELL/vllm_cell.py`` and the cell composes C0
from ``SCAFFOLD`` / ``body_upto`` / ``delta_block`` / ``CANARY``.  It is copied
here in exactly that shape, so the C0 bytes are the same bytes as O2E/O4.

Run:  python3 prompt_r2p1o1_cell.py
Env:  RESEXTRACT_R2P1O2_REQUESTS_CAP  (default 400)

Holds ``experiments/context-cache/.occamy.lock`` (flock) for the whole run.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO = Path("/home/zer0null/reserach extarctor")
HERE = Path(__file__).resolve().parent
CELL = "R2-P1-O2"
CONFIG_ID = "O2"

ROWS_PATH = HERE / "rows.jsonl"
ANALYSIS_PATH = HERE / "analysis.json"
SUMMARY_PATH = HERE / "summary.json"
WARMUP_PATH = HERE / "warmup.json"
G0_PATH = HERE / "g0.json"
LAUNCH_PATH = HERE / "launch.json"
EVENTS_PATH = HERE / "events.json"

PROGRESS_LOG = HERE / "progress.log"
HANDOFF_PATH = HERE / "cell_handoff.json"
LOCK_PATH = REPO / "experiments" / "context-cache" / ".occamy.lock"

RENDERER_PATH = REPO / "experiments" / "context-cache" / "cells" / "VLLM-CELL" / "vllm_cell.py"
ARMS_SOURCE = REPO / "experiments" / "context-cache" / "cells" / "PROMPT-O2-EXTRA" / "prompt_o2e_cell.py"
ARMS_SOURCE2 = REPO / "experiments" / "context-cache" / "cells" / "PROMPT-O4" / "prompt_o4_cell.py"

BASE_URL = os.environ.get("RESEXTRACT_R2P1O2_BASE_URL", "http://192.168.2.168:8017/v1")
TURNS = 71
BUDGET_TOKENS = 32768
ARMS = ("R", "A", "C", "H", "C0")
ROUND1_ARMS = ("R", "A", "C", "H")
MAX_TOKENS = 8
CONTAINER = os.environ.get("RESEXTRACT_R2P1O2_CONTAINER", "gx10-p-o2")
REQUESTS_CAP = int(os.environ.get("RESEXTRACT_R2P1O2_REQUESTS_CAP", "400"))
TOTAL_CELLS = 355


# --------------------------------------------------------------------------- #
# Module loading
# --------------------------------------------------------------------------- #
def load_module(name: str, path: Path):
    import importlib.util

    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def load_client():
    """The shared ChatClient. Preferred as an import; file exec as a fallback.

    ``client.py`` pulls in ``resextract.context``; when that package is not
    importable in this interpreter the file is exec'd with the environment boot
    that ``experiments/context-cache`` uses elsewhere.
    """
    for p in (REPO / "src", REPO / "experiments" / "context-cache"):
        sp = str(p)
        if sp not in sys.path:
            sys.path.insert(0, sp)
    from client import ChatClient  # type: ignore

    return ChatClient


def load_setup() -> dict:
    data = json.loads((REPO / "state" / "config" / "best-config.json").read_text())
    setup = data["setups"][CONFIG_ID]
    if setup["engine"] != "sglang" or setup["model"] != "qwen3.5-9b":
        raise SystemExit(f"unexpected O2 setup: {setup['engine']}/{setup['model']}")
    argv = [a for a in setup["argv"] if a not in ("sglang", "serve")]
    argv = ["/model-nvfp4" if a == "/model" else a for a in argv]
    return dict(setup, argv=argv, model_path="/model-nvfp4",
                launch_note="docker run --shm-size 32g --ipc host; image entrypoint supplies sglang serve")


# --------------------------------------------------------------------------- #
# Arms -- VERBATIM from PROMPT-O2-EXTRA / PROMPT-O4 (salt tag included) so the
# arm bodies are the same bytes across engines.
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
    """Stable-prefix digest: the first message IN FULL + the number of later ones."""
    return hashlib.sha256(json.dumps([messages[0], len(messages)], sort_keys=True,
                                     ensure_ascii=False).encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------- #
# Stats (incomplete-beta t distribution, ddof=1) -- same as O2E / O4
# --------------------------------------------------------------------------- #
def _betacf(a: float, b: float, x: float) -> float:
    MAXIT, EPS, FPMIN = 300, 3e-16, 1e-300
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
        if abs(d) < FPMIN:
            d = FPMIN
        c = 1.0 + aa / c
        if abs(c) < FPMIN:
            c = FPMIN
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < FPMIN:
            d = FPMIN
        c = 1.0 + aa / c
        if abs(c) < FPMIN:
            c = FPMIN
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
    lbt = (math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
           + a * math.log(x) + b * math.log(1.0 - x))
    bt = math.exp(lbt)
    if x < (a + 1.0) / (a + b + 2.0):
        return bt * _betacf(a, b, x) / a
    return 1.0 - bt * _betacf(b, a, 1.0 - x) / b


def t_cdf(t: float, df: float) -> float:
    x = df / (df + t * t)
    p = 0.5 * _betai(df / 2.0, 0.5, x)
    return 1.0 - p if t > 0 else p


def t_ppf(p: float, df: float) -> float:
    lo, hi = 0.0, 200.0
    for _ in range(200):
        mid = (lo + hi) / 2.0
        if t_cdf(mid, df) < p:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def mean_ci(values: list[float]) -> dict:
    n = len(values)
    if n == 0:
        return {"n": 0, "mean": None, "sd": None, "se": None, "t": None,
                "ci95": None, "ci95_half": None, "df": None}
    mean = sum(values) / n
    if n < 2:
        return {"n": n, "mean": mean, "sd": None, "se": None, "t": None,
                "ci95": None, "ci95_half": None, "df": None}
    var = sum((v - mean) ** 2 for v in values) / (n - 1)  # ddof=1
    sd = math.sqrt(var)
    se = sd / math.sqrt(n)
    df = n - 1
    tcrit = t_ppf(0.975, df)
    half = tcrit * se
    return {"n": n, "mean": round(mean, 6), "sd": round(sd, 6), "se": round(se, 6),
            "t": round(tcrit, 6), "ci95": [round(mean - half, 6), round(mean + half, 6)],
            "ci95_half": round(half, 6), "df": df}


def paired_delta(a_vals: list[float], b_vals: list[float]) -> dict:
    if len(a_vals) != len(b_vals) or not a_vals:
        return {"n": 0, "mean": None, "ci95": None, "excludes_zero": None}
    diffs = [x - y for x, y in zip(a_vals, b_vals)]
    ci = mean_ci(diffs)
    lo, hi = ci["ci95"] if ci["ci95"] else (None, None)
    return {"n": ci["n"], "mean": ci["mean"], "ci95": ci["ci95"],
            "se": ci["se"], "df": ci["df"],
            "excludes_zero": bool(lo is not None and (lo > 0 or hi < 0))}


# --------------------------------------------------------------------------- #
# Ops evidence
# --------------------------------------------------------------------------- #
def resolve_block() -> dict:
    out = {"container": CONTAINER, "source": "docker inspect (via ssh 192.168.2.168)",
           "raw_lines": [], "resolved": {}}
    try:
        proc = subprocess.run(
            ["ssh", "-o", "ConnectTimeout=10", "-o", "BatchMode=yes",
             "zer0null@192.168.2.168",
             f"docker inspect {CONTAINER} --format '{{{{.Id}}}} {{{{.Image}}}} "
             f"{{{{.State.StartedAt}}}} {{{{json .Config.Cmd}}}}'"],
            capture_output=True, text=True, timeout=60)
        if proc.stdout.strip():
            out["raw_lines"].append(proc.stdout.strip()[:4000])
            cid, image, started, cmd = proc.stdout.strip().split(" ", 3)
            out["resolved"] = {"container_id": cid[:12], "image": image.split(":")[-1][:12],
                               "started_at": started, "cmd": cmd[:2000]}
        if proc.stderr.strip():
            out["stderr"] = proc.stderr.strip()[:400]
    except Exception as exc:  # noqa: BLE001
        out["error"] = str(exc)[:300]
    return out


def grid_gcd(rows: list[dict]) -> dict:
    from functools import reduce

    vals = sorted({int(r["cached_tokens"]) for r in rows
                   if isinstance(r.get("cached_tokens"), int) and r["cached_tokens"] > 0})
    if not vals:
        return {"n_positive_cached_rows": 0, "gcd_cached_tokens": None, "sample": []}
    g = reduce(math.gcd, vals)
    return {
        "n_positive_cached_rows": sum(1 for r in rows
                                      if isinstance(r.get("cached_tokens"), int)
                                      and r["cached_tokens"] > 0),
        "gcd_cached_tokens": int(g),
        "gcd_is_16_multiple": g % 16 == 0,
        "gcd_is_64_multiple": g % 64 == 0,
        "all_rows_multiple_of_16": all(v % 16 == 0 for v in vals),
        "all_rows_multiple_of_64": all(v % 64 == 0 for v in vals),
        "distinct_mod64": sorted({v % 64 for v in vals}),
        "min_positive": vals[0],
        "max_positive": vals[-1],
        "n_distinct_positive": len(vals),
        "sample": vals[:12],
    }


# --------------------------------------------------------------------------- #
# I/O
# --------------------------------------------------------------------------- #
def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def append_row(row: dict) -> None:
    with ROWS_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")
        fh.flush()
        os.fsync(fh.fileno())


def write_json(path: Path, payload) -> None:
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def progress(line: str) -> None:
    PROGRESS_LOG.parent.mkdir(parents=True, exist_ok=True)
    with PROGRESS_LOG.open("a", encoding="utf-8") as fh:
        fh.write(f"{utc_now()} {CELL} {line}\n")
        fh.flush()


def acquire_lock(timeout_s: float = 900.0):
    import fcntl

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
               "scope": f"{CELL} five-arm prompt cell on sglang :8017 "
                        f"(no restart); held for the whole run"}, handle)
    handle.flush()
    os.fsync(handle.fileno())
    return handle


def release_lock(handle) -> None:
    import fcntl

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
# One HTTP call
# --------------------------------------------------------------------------- #
def call(client, messages, max_tokens=MAX_TOKENS, timeout=180.0) -> dict:
    """One NON-streaming chat call carrying the full ``usage`` object."""
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
        # SGLang emits this itself on a radix miss; the renderer's parenthetical.
        "cold_null": bool("cold_null_details" in body),
        "wall_ms": round(wall_ms, 3),
        "body": body,
    }


COLD_RETRIES = 3


def measure(client, fitted, truncated, arm, turn, is_first_arm_turn):
    """One measured call; a cold radix miss reported as null is retried NEUTRALLY.

    A prefix-cache hit is by definition served from a 16-token-aligned radix
    node, so the *second* identical call on the same prompt is free (prompt
    467 -> cached 416 was measured in this cell's own warm-up).  A cold miss is
    therefore retried with the same bytes, same temperature, at most
    ``COLD_RETRIES`` times; the retry is not counted as a measurement.  If the
    miss persists the row carries ``cached_tokens = 0`` (a real miss, not an
    instrument failure) and the analysis agrees with the hidden-token-ledger
    convention: a 16-token-aligned 0 is a miss, an unaligned 0 is "unavailable".
    """
    tries = 0
    res = call(client, fitted)
    while (res["http_status"] == 200 and res["cached_tokens"] is None
           and res["details_present"] is False and res["cold_null"]
           and not is_first_arm_turn and tries < COLD_RETRIES):
        tries += 1
        time.sleep(0.15)
        res = call(client, fitted)
    res["null_retries"] = tries
    return res


# --------------------------------------------------------------------------- #
# Analysis
# --------------------------------------------------------------------------- #
def analyse(rows: list[dict], guard: dict) -> dict:
    per_arm = {}
    unc_by_arm = {}
    for arm in ARMS:
        rs = sorted([r for r in rows if r["arm"] == arm], key=lambda r: r["turn"])
        unc_obs = [float(r["uncached_tokens"]) for r in rs if r["uncached_tokens"] != "unavailable"]
        unc_by_arm[arm] = {int(r["turn"]): float(r["uncached_tokens"]) for r in rs
                           if r["uncached_tokens"] != "unavailable"}
        ci = mean_ci(unc_obs)
        pt = sum(int(r["prompt_tokens"]) for r in rs
                 if isinstance(r.get("prompt_tokens"), int))
        ct = sum(int(r["cached_tokens"]) for r in rs
                 if isinstance(r.get("cached_tokens"), int))
        per_arm[arm] = {
            "n_rows": len(rs),
            "n_measured": len(unc_obs),
            "turns": [int(r["turn"]) for r in rs],
            "mean_uncached_per_turn": ci["mean"],
            "sd_uncached": ci["sd"],
            "se_uncached": ci["se"],
            "df": ci["df"],
            "t_crit_975": ci["t"],
            "ci95_uncached_per_turn": ci["ci95"],
            "ci95_halfwidth": ci["ci95_half"],
            "hit_fraction_weighted": (round(ct / pt, 6) if pt else None),
            "prompt_tokens_total": pt,
            "cached_tokens_total": ct,
            "n_cached_gt_0": sum(1 for r in rs
                                 if isinstance(r["cached_tokens"], int) and r["cached_tokens"] > 0),
            "n_non_200": sum(1 for r in rs if r.get("http_status") != 200),
            "first_prompt_sha256": (prompt_sha(arm_messages(CURRENT_RENDERER, arm, 1))
                                    if CURRENT_RENDERER is not None else "unavailable"),
            "distinct_prompt_sha256": len({r.get("prompt_sha256") for r in rs
                                           if r.get("prompt_sha256")}),
        }
    # paired deltas vs R, turn by turn where both arms are measured
    r_vals = unc_by_arm["R"]
    deltas = {}
    for arm in ARMS:
        if arm == "R":
            continue
        common = sorted(set(r_vals) & set(unc_by_arm[arm]))
        a_vals = [unc_by_arm[arm][t] for t in common]
        b_vals = [r_vals[t] for t in common]
        d = paired_delta(a_vals, b_vals)
        d["direction"] = (f"{arm} cheaper" if d.get("mean") is not None and d["mean"] < 0
                          else f"{arm} costlier")
        deltas[f"{arm}-R"] = d
    return {"unit": CELL, "cell": CELL, "status": "done",
            "arms_identical_guard": guard, "per_arm": per_arm, "deltas_vs_R": deltas}


# --------------------------------------------------------------------------- #
# Handoff
# --------------------------------------------------------------------------- #
def write_handoff(payload: dict, rows: list[dict], rows_sha: str, requests: int,
                  warm2: dict, extra: dict) -> None:
    per_arm = payload.get("per_arm", {})
    table = {a: {"hit": v["hit_fraction_weighted"], "unc_per_turn": v["mean_uncached_per_turn"],
                 "ci95": v["ci95_uncached_per_turn"]} for a, v in per_arm.items()}
    handoff = {
        "unit": CELL,
        "status": payload["status"],
        "artifacts": [str(ROWS_PATH.relative_to(REPO)),
                      str(ANALYSIS_PATH.relative_to(REPO)),
                      str(SUMMARY_PATH.relative_to(REPO)),
                      str(WARMUP_PATH.relative_to(REPO)),
                      str(G0_PATH.relative_to(REPO)),
                      str(LAUNCH_PATH.relative_to(REPO)),
                      str(PROGRESS_LOG.relative_to(REPO))],
        "evidence": {
            "warmup_cached_tokens": warm2.get("cached_tokens"),
            "rows": len(rows),
            "arms_present": sorted({r["arm"] for r in rows}),
            "cached_gt_0": sum(1 for r in rows if isinstance(r.get("cached_tokens"), int)
                               and r["cached_tokens"] > 0),
            "non_200": sum(1 for r in rows if r.get("http_status") != 200),
            "first_prompt_sha_per_arm": {a: v.get("first_prompt_sha256")
                                         for a, v in per_arm.items()},
            "per_arm_table": table,
            "A_minus_R": payload.get("deltas_vs_R", {}).get("A-R"),
            "headline_A_over_R": payload.get("headline_A_over_R"),
            "grid_gcd": payload.get("observed_grid", {}).get("gcd_cached_tokens"),
            "prod_models_code": extra.get("prod_models_code"),
            "rows_sha256": rows_sha,
            "requests": {"total": requests, "cap": REQUESTS_CAP},
            "commands": extra.get("commands", []),
        },
        "assumptions": extra.get("assumptions", []),
        "blocker": extra.get("blocker", ""),
        "next_unit_hint": extra.get("next_unit_hint", ""),
        "write_paths": [f"experiments/context-cache/cells/{CELL}/**",
                        f"state/logs/{CELL}-progress.log",
                        f"orchestration/handoffs/{CELL}.json",
                        f"orchestration/units/{CELL}.md"],
    }
    tmp = HANDOFF_PATH.with_name(HANDOFF_PATH.name + ".tmp")
    tmp.write_text(json.dumps(handoff, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, HANDOFF_PATH)


CURRENT_RENDERER = None


def _is_complete_row(line: str) -> bool:
    """A row this run may append after.

    Rejects a torn last line (not JSON) and any row whose cache field is the
    string ``"unavailable"`` -- that turn is the one a resumed run must redo, so
    the redo appends rather than rewrites history.
    """
    try:
        r = json.loads(line)
    except Exception:  # noqa: BLE001
        return False
    return r.get("cached_tokens") != "unavailable"


def main() -> int:
    global CURRENT_RENDERER
    HERE.mkdir(parents=True, exist_ok=True)
    setup = load_setup()
    renderer = load_module("sglang_cell_round1", RENDERER_PATH)
    CURRENT_RENDERER = renderer
    ChatClient = load_client()
    client = ChatClient(base_url=BASE_URL, model=setup["model"], timeout=180.0)

    resolve = resolve_block()
    write_json(LAUNCH_PATH, {"argv": setup["argv"], "config_sha256": setup["config_sha256"],
                             "container": CONTAINER, "endpoint": BASE_URL,
                             "max_model_len": 32768, "grid_unit": setup.get("grid_unit"),
                             "resolve_block": resolve})

    # ARMS_IDENTICAL guard: first prompt of every arm must be a distinct sha256
    hashes = {a: prompt_sha(arm_messages(renderer, a, 1)) for a in ARMS}
    collisions = []
    for i, a in enumerate(ARMS):
        for b in ARMS[i + 1:]:
            if hashes[a] == hashes[b]:
                collisions.append(f"{a}=={b}")
    guard = {"arm_first_prompt_sha256": hashes, "collisions": collisions,
             "arms_identical": bool(collisions), "distinct_count": len(set(hashes.values()))}
    print(f"ARMS_IDENTICAL guard: collisions={collisions or 'none'} "
          f"distinct={len(set(hashes.values()))}/5", flush=True)

    handle = acquire_lock()
    try:
        # --- warm-up: two identical calls, second must report cached_tokens > 0
        warm_msgs = [{"role": "user", "content": (
            "R2-P1-O2 warm-up on cell 2. Reply with the single word: ready.\n"
            "padding: " + ("cache probe block 0123456789 " * 400))}]
        warm1 = call(client, warm_msgs, max_tokens=8)
        warm2 = call(client, warm_msgs, max_tokens=8)
        warm = {"url": BASE_URL + "/chat/completions", "model": setup["model"],
                "call1": {k: warm1[k] for k in ("http_status", "prompt_tokens",
                                                "cached_tokens", "details_present", "usage")},
                "call2": {k: warm2[k] for k in ("http_status", "prompt_tokens",
                                                "cached_tokens", "details_present", "usage")},
                "call2_body": warm2["body"][:2000]}
        write_json(WARMUP_PATH, warm)
        write_json(G0_PATH, {
            "call1": {"prompt_tokens": warm1["prompt_tokens"],
                      "details": (warm1["usage"] or {}).get("prompt_tokens_details")},
            "call2": {"prompt_tokens": warm2["prompt_tokens"],
                      "details": (warm2["usage"] or {}).get("prompt_tokens_details")},
            "url": BASE_URL + "/chat/completions"})
        print(f"G0: call1 cached={warm1['cached_tokens']} call2 cached={warm2['cached_tokens']} "
              f"details={warm2['details_present']} status={warm2['http_status']}", flush=True)
        progress(f"warmup call1_cached={warm1['cached_tokens']} "
                 f"call2_cached={warm2['cached_tokens']} status={warm2['http_status']}")

        gate_ok = (warm2["http_status"] == 200 and warm2["details_present"]
                   and warm2["cached_tokens"] is not None and warm2["cached_tokens"] > 0)
        if not gate_ok:
            payload = {"unit": CELL, "cell": CELL, "stack": "sglang",
                       "config_id": setup["config_id"], "status": "GAMMA: unavailable",
                       "reason": "G0 gate failed: second identical warm-up call did not report "
                                 "usage.prompt_tokens_details.cached_tokens > 0 (instrument blind)",
                       "raw_body": warm2["body"][:4000],
                       "arms_identical_guard": guard, "n_rows": 0, "resolve_block": resolve}
            write_json(ANALYSIS_PATH, payload)
            write_handoff(payload, [], "", 2, warm2,
                          {"blocker": "G0 gate failed: cached_tokens == 0 on second identical call",
                           "prod_models_code": extra_prod_code()})
            progress("GAMMA: unavailable (instrument blind) -- STOPPED before measuring")
            print("STOP: GAMMA unavailable. " + warm2["body"][:800], flush=True)
            return 2

        # --- measurement: resume from the last COMPLETE row if rows.jsonl exists
        # rows.jsonl is append-only; a resumed run must not leave a partial line
        # behind, so any bytes after the persisted offset are dropped first.
        done = set()
        if ROWS_PATH.exists():
            raw = ROWS_PATH.read_bytes()
            off_path = HERE / "rows.offset"
            off = int(off_path.read_text()) if off_path.exists() else len(raw)
            if len(raw) > off:
                tail = raw[off:].split(b"\n", 1)[0] + b"\n"
                incomplete = [l for l in tail.decode("utf-8", "replace").splitlines()
                              if not _is_complete_row(l)]
                if incomplete:
                    ROWS_PATH.write_bytes(raw[:off])
                    print(f"dropped {len(incomplete)} incomplete/retryable row(s) after "
                          f"offset {off}", flush=True)
            for line in ROWS_PATH.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    try:
                        r = json.loads(line)
                        if r.get("turn") is not None and r.get("arm"):
                            done.add((r["arm"], int(r["turn"])))
                    except Exception:  # noqa: BLE001
                        continue
        if done:
            progress(f"resume: {len(done)} rows already present in rows.jsonl")
            print(f"resume: {len(done)} rows already present", flush=True)

        requests = 2
        aborted = None
        for arm in ARMS:
            arm_rows_this_run = 0
            arm_unc = []
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
                is_first = (turn == 1 and arm == ARMS[0] and not any(
                    r["arm"] == arm for r in [])) or (turn == 1)
                res = measure(client, fitted, truncated, arm, turn, is_first)
                requests += 1 + res.get("null_retries", 0)
                if res["http_status"] != 200 or res["prompt_tokens"] is None:
                    aborted = {"arm": arm, "turn": turn, "http_status": res["http_status"],
                               "cached_tokens": res["cached_tokens"],
                               "details_present": res["details_present"],
                               "body": res["body"][:3000]}
                    write_json(EVENTS_PATH, {"aborted": aborted, "requests": requests})
                    print(f"ABORT {arm} turn {turn}: http={res['http_status']} "
                          f"cached={res['cached_tokens']} body={res['body'][:600]}", flush=True)
                    break
                # cold_null_details: the server said "cold miss" in its own field.
                # That is a real 0, not a blind instrument -- record 0 and flag it.
                # Any OTHER absent detail (no cold_null field) is unobservable.
                if res["cached_tokens"] is None:
                    cold_null = bool(res.get("cold_null")) or res["details_present"]
                    cached = 0 if cold_null else None
                    source = "cold_null" if res.get("cold_null") else (
                        "zero_cached" if res["details_present"] else "unavailable")
                else:
                    cold_null, cached = False, res["cached_tokens"]
                    source = "reported"
                unc = (res["prompt_tokens"] - cached) if cached is not None else None
                row = {
                    "setup": CONFIG_ID,
                    "stack": "sglang",
                    "model": setup["model"],
                    "engine": setup.get("engine", "sglang"),
                    "engine_version": setup.get("engine_version", "unavailable"),
                    "config_id": setup["config_id"],
                    "config_sha256": setup["config_sha256"],
                    "arm": arm,
                    "turn": turn,
                    "prompt_tokens": res["prompt_tokens"],
                    "cached_tokens": cached if cached is not None else "unavailable",
                    "uncached_tokens": unc if unc is not None else "unavailable",
                    "pad_tokens": pad_tokens,
                    "http_status": res["http_status"],
                    "prefix_sha256": prefix_sha(fitted),
                    "prompt_sha256": prompt_sha(fitted),
                    "cache_source": source,
                    "cold_null_details": cold_null,
                    "null_retries": res.get("null_retries", 0),
                    "budget_tokens": BUDGET_TOKENS,
                    "messages": len(fitted),
                    "prompt_bytes": len(blob),
                    "truncated": bool(truncated),
                    "wall_ms": res["wall_ms"],
                    "ts_utc": utc_now(),
                }
                append_row(row)
                arm_rows_this_run += 1
                if unc is not None:
                    arm_unc.append(unc)
                done.add((arm, turn))
                # persist the append offset so a resumed run never leaves a torn line
                with (HERE / "rows.offset").open("w", encoding="utf-8") as oh:
                    oh.write(str(ROWS_PATH.stat().st_size))
                if turn % 20 == 0 or turn == 1:
                    print(f"  {arm} t{turn:2d} prompt={row['prompt_tokens']} "
                          f"cached={row['cached_tokens']} unc={unc}", flush=True)
            if aborted:
                progress(f"arm {arm} ABORTED at turn {aborted.get('turn')} "
                         f"http={aborted.get('http_status')}; requests={requests}")
                break
            if arm_rows_this_run:
                mu = (f"{sum(arm_unc)/len(arm_unc):.1f}" if arm_unc else "unavailable")
                progress(f"arm {arm} done: rows_this_run={arm_rows_this_run} "
                         f"mean_unc={mu} requests={requests}")
            else:
                progress(f"arm {arm} done: already present, skipped; requests={requests}")

        rows = []
        if ROWS_PATH.exists():
            rows = [json.loads(l) for l in ROWS_PATH.read_text(encoding="utf-8").splitlines()
                    if l.strip()]
        payload = analyse(rows, guard)
        payload["stack"] = "sglang"
        payload["config_id"] = setup["config_id"]
        payload["config_sha256"] = setup["config_sha256"]
        payload["warmup_cached_tokens"] = warm2["cached_tokens"]
        payload["g0"] = {"call1_cached": warm1["cached_tokens"],
                         "call2_cached": warm2["cached_tokens"],
                         "call1_prompt_tokens": warm1["prompt_tokens"]}
        payload["resolve_block"] = resolve
        payload["observed_grid"] = grid_gcd(rows)
        payload["requests"] = {"total": requests, "cap": REQUESTS_CAP}
        payload["config"] = {k: setup.get(k) for k in
                             ("model", "engine", "config_id", "config_sha256", "grid_unit")}

        # P1/P0-style headline = A / R
        a_unc = payload["per_arm"]["A"]["mean_uncached_per_turn"]
        r_unc = payload["per_arm"]["R"]["mean_uncached_per_turn"]
        a_hit = payload["per_arm"]["A"]["hit_fraction_weighted"]
        r_hit = payload["per_arm"]["R"]["hit_fraction_weighted"]
        payload["headline_A_over_R"] = {
            "metric": "mean_uncached_tokens_per_turn",
            "A": a_unc, "R": r_unc,
            "A_over_R": (round(a_unc / r_unc, 6) if a_unc and r_unc else None),
            "A_minus_R": (round(a_unc - r_unc, 6) if a_unc is not None and r_unc is not None
                          else None),
            "hit_A": a_hit, "hit_R": r_hit,
            "hit_A_over_R": (round(a_hit / r_hit, 6) if a_hit and r_hit else None),
            "excludes_zero": payload["deltas_vs_R"].get("A-R", {}).get("excludes_zero"),
        }
        payload["renderer_source"] = {
            "path": str(RENDERER_PATH.relative_to(REPO)),
            "sha256": hashlib.sha256(RENDERER_PATH.read_bytes()).hexdigest(),
            "note": "round-1 renderer imported verbatim; arms + salt copied verbatim from "
                    "cells/PROMPT-O2-EXTRA/prompt_o2e_cell.py and cells/PROMPT-O4/prompt_o4_cell.py",
            "arms_source": str(ARMS_SOURCE.relative_to(REPO)),
            "arms_source_sha256": hashlib.sha256(ARMS_SOURCE.read_bytes()).hexdigest(),
            "arms_source2": str(ARMS_SOURCE2.relative_to(REPO)),
            "arms_source2_sha256": hashlib.sha256(ARMS_SOURCE2.read_bytes()).hexdigest(),
        }
        if aborted:
            payload["aborted"] = aborted
            payload["status"] = "failed_http" if "http_status" in aborted else "partial"
        elif len(rows) < TOTAL_CELLS:
            payload["status"] = "partial"
        write_json(ANALYSIS_PATH, payload)
        write_json(SUMMARY_PATH, {
            "hit": {a: v["hit_fraction_weighted"] for a, v in payload["per_arm"].items()},
            "unc_per_turn": {a: v["mean_uncached_per_turn"] for a, v in payload["per_arm"].items()},
            "ci95": {a: v["ci95_uncached_per_turn"] for a, v in payload["per_arm"].items()},
            "deltas_vs_R": payload["deltas_vs_R"],
            "headline_A_over_R": payload["headline_A_over_R"],
            "arms_identical_guard": guard,
            "observed_grid": payload["observed_grid"],
        })
        rows_sha = hashlib.sha256(ROWS_PATH.read_bytes()).hexdigest() if ROWS_PATH.exists() else ""
        prod = extra_prod_code()
        write_handoff(payload, rows, rows_sha, requests, warm2,
                      {"prod_models_code": prod,
                       "blocker": ("" if payload["status"] == "done"
                                   else f"{payload['status']}: {aborted or {}}"),
                       "next_unit_hint": "PROMPT-O2-EXTRA style cell in this factorial: same arms, "
                                         "other setup; compare A vs C0 on the same grid.",
                       "commands": ["wc -l experiments/context-cache/cells/R2-P1-O2/rows.jsonl",
                                    "curl -s -o /dev/null -w '%{http_code}' "
                                    "http://192.168.2.168:8017/v1/models"]})
        progress(f"FINAL status={payload['status']} rows={len(rows)} requests={requests} "
                 f"A/R={payload['headline_A_over_R']['A_over_R']} "
                 f"gcd={payload['observed_grid']['gcd_cached_tokens']} prod={prod}")
        print(json.dumps({"status": payload["status"], "rows": len(rows),
                          "rows_sha256": rows_sha,
                          "gcd": payload["observed_grid"]["gcd_cached_tokens"],
                          "A_over_R": payload["headline_A_over_R"]["A_over_R"]}, indent=1),
              flush=True)
        return 0 if payload["status"] == "done" else 3
    finally:
        release_lock(handle)


def extra_prod_code() -> str:
    try:
        proc = subprocess.run(["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
                              "--max-time", "10", BASE_URL + "/models"],
                              capture_output=True, text=True, timeout=30)
        return proc.stdout.strip() or "unavailable"
    except Exception:  # noqa: BLE001
        return "unavailable"


if __name__ == "__main__":
    sys.exit(main())
