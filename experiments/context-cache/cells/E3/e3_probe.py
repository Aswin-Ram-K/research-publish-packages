#!/usr/bin/env python3
"""E3 `append-deviation` -- live probe of the warm-append residual (G7).

Measures, on fresh-salt chains, the decomposition

    residual  = (L - m) - (L % 64)
    tail_term = L - 64*floor(L_prev/64) - (L % 64)
    deficit   = 64*floor(L_prev/64) - m          (== tail_term - residual)

where L = prompt_tokens, m = cached_tokens, L_prev = prompt_tokens of the
previous full prompt in the same chain.  A byte-identical repeat of an appended
prompt is the retention test: residual 0 => the state *was* kept after
completion (loss is at the append match), residual > 0 => it was not.

Live path is the shared instrument: experiments/context-cache/client.py
(ChatClient.chat).  No private HTTP client for inference.  Read-only GETs for
server state.  /flush_cache is never called.

Usage:
    python3 e3_probe.py --dry      # offline: build+print the plan, no network
    python3 e3_probe.py            # live: lock, GETs, chains, perturbation
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import importlib.util
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "src"))

import httpx  # noqa: E402

from resextract.context.salt import make_salt  # noqa: E402

CLIENT_PATH = ROOT / "experiments" / "context-cache" / "client.py"
_spec = importlib.util.spec_from_file_location("e3_client", CLIENT_PATH)
client = importlib.util.module_from_spec(_spec)
sys.modules["e3_client"] = client
_spec.loader.exec_module(client)

BASE_URL = client.DEFAULT_BASE_URL.rstrip("/")
BASE = BASE_URL[: -len("/v1")] if BASE_URL.endswith("/v1") else BASE_URL
MODEL = client.DEFAULT_MODEL

LOCK_PATH = ROOT / "experiments" / "context-cache" / ".occamy.lock"
ROWS = HERE / "e3_rows.jsonl"
METRICS = HERE / "e3_metrics.jsonl"
STATE = HERE / "e3_server_state.json"
RUNLOG = HERE / "e3_runlog.json"
RAW_USAGE = HERE / "e3_raw_usage.jsonl"

MAX_REQ = 120
MAX_GET = 60
MAX_SECONDS = 2100.0
LOCK_DEADLINE = 2400.0
GRID = 64

# --------------------------------------------------------------------------- #
# raw-usage archiving: patch the *imported* normalise_cache in the client module
# --------------------------------------------------------------------------- #
RAW: list[dict | None] = []
_orig_normalise = client.normalise_cache


def _recording_normalise(usage):
    RAW.append(dict(usage) if isinstance(usage, dict) else None)
    return _orig_normalise(usage)


client.normalise_cache = _recording_normalise


# --------------------------------------------------------------------------- #
# Deterministic prompt material (strict prefix extension by construction)
# --------------------------------------------------------------------------- #
def sentence(i: int) -> str:
    return (
        f"Note {i}: in run {i * 31 % 9973} the operator recorded ledger {i * 17} "
        f"against batch {i % 29} and the check closed cleanly.\n"
    )


def preamble(salt: str) -> str:
    return (
        "You are a careful analyst. Case salt: " + salt + ". "
        "Read the record below and answer with the single word ok.\n"
    )


def build_prompt(salt: str, n_sent: int) -> str:
    return preamble(salt) + "".join(sentence(i) for i in range(n_sent))


CHAINS = [
    {"name": "c15", "n_sent": 15, "tails": [4, 4, 24, 4, 4, 24, 4, 4]},
    {"name": "c30", "n_sent": 30, "tails": [4, 4, 24, 4, 4, 24, 4, 4]},
    {"name": "c60", "n_sent": 60, "tails": [4, 4, 24, 4, 4, 24, 4, 4]},
    {"name": "c120", "n_sent": 120, "tails": [4, 4, 24, 4, 4, 24, 4, 4]},
]
PERTURB = {"name": "p60", "n_sent": 60, "tails": [4, 24, 4], "interleave": 24,
           "interleave_sent": 8, "interleave_base": 1000}


def plan():
    """Return the ordered request plan (no network)."""
    steps = []
    for ci, ch in enumerate(CHAINS):
        salt = make_salt(910000 + ci)
        n = ch["n_sent"]
        steps.append({"chain": ch["name"], "salt": salt, "kind": "cold", "n_sent": n,
                      "round": 0, "phase": "chain"})
        steps.append({"chain": ch["name"], "salt": salt, "kind": "warm_base", "n_sent": n,
                      "round": 0, "phase": "chain"})
        for r, t in enumerate(ch["tails"], start=1):
            n += t
            steps.append({"chain": ch["name"], "salt": salt, "kind": "append", "n_sent": n,
                          "round": r, "tail_sent": t, "phase": "chain"})
            steps.append({"chain": ch["name"], "salt": salt, "kind": "repeat", "n_sent": n,
                          "round": r, "tail_sent": t, "phase": "chain"})
    ph = PERTURB
    salt = make_salt(920000)
    n = ph["n_sent"]
    steps.append({"chain": ph["name"], "salt": salt, "kind": "cold", "n_sent": n,
                  "round": 0, "phase": "perturb"})
    steps.append({"chain": ph["name"], "salt": salt, "kind": "warm_base", "n_sent": n,
                  "round": 0, "phase": "perturb"})
    n += ph["tails"][0]
    steps.append({"chain": ph["name"], "salt": salt, "kind": "append", "n_sent": n,
                  "round": 1, "tail_sent": ph["tails"][0], "phase": "perturb"})
    steps.append({"chain": ph["name"], "salt": salt, "kind": "repeat", "n_sent": n,
                  "round": 1, "tail_sent": ph["tails"][0], "phase": "perturb"})
    for i in range(ph["interleave"]):
        steps.append({"chain": ph["name"], "salt": make_salt(930000 + i),
                      "kind": "interleave", "n_sent": ph["interleave_sent"],
                      "round": 0, "phase": "perturb",
                      "note": f"distinct fresh-salt prefix #{i}"})
    for j, t in enumerate(ph["tails"][1:], start=2):
        n += t
        steps.append({"chain": ph["name"], "salt": salt, "kind": "append", "n_sent": n,
                      "round": j, "tail_sent": t, "phase": "perturb"})
        steps.append({"chain": ph["name"], "salt": salt, "kind": "repeat", "n_sent": n,
                      "round": j, "tail_sent": t, "phase": "perturb"})
    return steps


# --------------------------------------------------------------------------- #
# Read-only server state
# --------------------------------------------------------------------------- #
def utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def get_json(path: str, bucket: dict):
    with httpx.Client(base_url=BASE, timeout=30.0) as http:
        r = http.get(path)
        body = r.text
    rec = {"url": BASE + path, "http_status": r.status_code, "bytes": len(body.encode()),
           "sha256": hashlib.sha256(body.encode()).hexdigest(), "captured_utc": utc()}
    try:
        rec["body"] = json.loads(body)
    except json.JSONDecodeError:
        rec["body_text"] = body[:20000]
    bucket[path] = rec
    return rec


NUM = re.compile(r"^([a-zA-Z_:][a-zA-Z0-9_:]*)(\{[^}]*\})?\s+([-+0-9.eENaInf]+)$")


def parse_metrics(text: str) -> tuple[dict[str, float], dict[str, float]]:
    exact: dict[str, float] = {}
    base: dict[str, float] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = NUM.match(line)
        if not m:
            continue
        name, _labels, val = m.group(1), m.group(2), m.group(3)
        try:
            v = float(val)
        except ValueError:
            continue
        exact[name] = v
        base[name] = v
    return exact, base


INTEREST = re.compile(
    r"mamba|ckpt|checkpoint|radix|evict|cache|used_token|running|queue|hit|retract|token_usage",
    re.I,
)


def metrics_snapshot(tag: str, idx: int):
    started = time.perf_counter()
    try:
        with httpx.Client(base_url=BASE, timeout=30.0) as http:
            r = http.get("/metrics")
            text = r.text
        status = r.status_code
    except Exception as exc:  # noqa: BLE001 - read-only probe, recorded not raised
        text, status = "", repr(exc)
    elapsed = round((time.perf_counter() - started) * 1000.0, 1)
    exact, base = parse_metrics(text) if text else ({}, {})
    sel = {k: v for k, v in base.items() if INTEREST.search(k)}
    rec = {"id": idx, "tag": tag, "utc": utc(), "http_status": status,
           "bytes": len(text.encode()),
           "sha256": hashlib.sha256(text.encode()).hexdigest(),
           "n_series": len(exact), "selected": sel}
    with METRICS.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({**rec, "raw_text": text}) + "\n")
    return rec


# --------------------------------------------------------------------------- #
# Live loop
# --------------------------------------------------------------------------- #
def run_live() -> int:
    for p in (ROWS, METRICS, RAW_USAGE):
        if p.exists():
            p.unlink()
    t_start = time.time()
    lock_fd = open(LOCK_PATH, "a+")
    waited0 = time.time()
    acquired = False
    while True:
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            acquired = True
            break
        except OSError:
            if time.time() - waited0 > LOCK_DEADLINE:
                break
            time.sleep(0.5)
    lock_wait = round(time.time() - waited0, 3)
    if not acquired:
        RUNLOG.write_text(json.dumps({
            "status": "partial", "blocker": "lock timeout", "lock_wait_s": lock_wait,
            "requests_made": 0, "get_count": 0, "rows": 0}, indent=1), encoding="utf-8")
        print(json.dumps({"blocker": "lock timeout", "lock_wait_s": lock_wait}))
        return 3

    state: dict = {"base": BASE, "model": MODEL, "captured_utc": utc()}
    requests_made = 0
    get_count = 0
    consecutive_failures = 0
    aborted = ""
    seq = 0
    cold_L: dict[str, int] = {}
    prev_L: dict[str, int] = {}
    last_metrics: dict | None = None
    m_idx = 0
    try:
        for path in ("/server_info", "/get_model_info", "/metrics"):
            rec = get_json(path, state)
            get_count += 1
            if path == "/metrics":
                exact, base = parse_metrics(rec.get("body_text", ""))
                state["metrics_names"] = len(exact)
                state["metrics_interesting"] = {
                    k: v for k, v in base.items() if INTEREST.search(k)}
                m_idx += 1
                last_metrics = {"id": m_idx, "tag": "boot", "utc": utc(),
                                "selected": state["metrics_interesting"]}
                with METRICS.open("a", encoding="utf-8") as fh:
                    fh.write(json.dumps({**last_metrics,
                                         "raw_text": rec.get("body_text", "")}) + "\n")

        steps = plan()
        print(f"planned requests: {len(steps)}", flush=True)
        for st in steps:
            if requests_made >= MAX_REQ or time.time() - t_start > MAX_SECONDS:
                aborted = "budget"
                break
            text = build_prompt(st["salt"], st["n_sent"])
            RAW.clear()
            started = time.perf_counter()
            try:
                pt, ct, comp, ttft, wall, status, _out = client.ChatClient().chat(
                    [{"role": "user", "content": text}], max_tokens=8)
                err = ""
            except Exception as exc:  # noqa: BLE001
                pt = ct = comp = status = 0
                ttft = wall = round((time.perf_counter() - started) * 1000.0, 1)
                err = repr(exc)
            requests_made += 1
            seq += 1
            usage = RAW[0] if RAW else None
            with RAW_USAGE.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps({"seq": seq, "kind": st["kind"], "usage": usage}) + "\n")
            if err:
                consecutive_failures += 1
            else:
                consecutive_failures = 0

            L = int(pt)
            m = int(ct)
            chain = st["chain"]
            pL = prev_L.get(st["salt"])
            if st["kind"] == "cold":
                cold_L[chain] = L
            if st["kind"] in ("append", "repeat") and pL is not None:
                expected = GRID * (pL // GRID)
                tail_term = L - expected - (L % GRID)
                deficit = expected - m
            else:
                tail_term = deficit = None
            residual = (L - m) - (L % GRID) if L else None
            row = {
                "seq": seq, "utc": utc(), "phase": st["phase"], "chain": chain,
                "kind": st["kind"], "round": st["round"],
                "n_sent": st["n_sent"], "tail_sent": st.get("tail_sent"),
                "salt": st["salt"], "prompt_tokens": L, "cached_tokens": m,
                "uncached": L - m, "residual": residual,
                "prev_prompt_tokens": pL,
                "tail_term": tail_term, "deficit": deficit,
                "steps_since_cold": (seq - 1) if st["kind"] != "cold" else 0,
                "ttft_ms": round(float(ttft), 1), "wall_ms": round(float(wall), 1),
                "status": status, "raw_usage": usage, "error": err,
                "metrics_id": last_metrics["id"] if last_metrics else None,
                "metrics_selected": last_metrics["selected"] if last_metrics else {},
            }
            with ROWS.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(row) + "\n")
            if L:
                prev_L[st["salt"]] = L
            print(json.dumps({k: row[k] for k in ("seq", "chain", "kind", "round",
                                                  "prompt_tokens", "cached_tokens",
                                                  "residual", "deficit")}), flush=True)

            # snapshot server state around each round pair / after interleaves
            if st["kind"] == "repeat" or st["kind"] in ("warm_base", "cold") and st["phase"] == "perturb":
                m_idx += 1
                last_metrics = metrics_snapshot(f"{chain}:{st['kind']}:r{st['round']}", m_idx)
                get_count += 1
                if st["kind"] == "repeat":
                    pass
            if st["kind"] == "interleave" and (st["round"] == 0) and \
                    (int(st.get("n_sent") or 0) == 8) and seq % 6 == 0:
                m_idx += 1
                last_metrics = metrics_snapshot(f"interleave:{seq}", m_idx)
                get_count += 1
            if consecutive_failures >= 3:
                aborted = "3 consecutive failures"
                break
    finally:
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_UN)
        finally:
            lock_fd.close()

    rows_n = sum(1 for _ in ROWS.open(encoding="utf-8")) if ROWS.exists() else 0
    digest = hashlib.sha256(ROWS.read_bytes()).hexdigest() if ROWS.exists() else ""
    runlog = {
        "status": "partial" if aborted else "done",
        "blocker": aborted, "requests_made": requests_made, "get_count": get_count,
        "rows": rows_n, "rows_sha256": digest, "lock_wait_s": lock_wait,
        "elapsed_s": round(time.time() - t_start, 2),
        "cold_L": cold_L, "base": BASE, "model": MODEL,
        "utc_end": utc(),
    }
    RUNLOG.write_text(json.dumps(runlog, indent=1), encoding="utf-8")
    STATE.write_text(json.dumps(state, indent=1)[:2_000_000], encoding="utf-8")
    print(json.dumps(runlog))
    return 0


def dry() -> int:
    steps = plan()
    print(f"planned requests: {len(steps)}")
    kinds: dict[str, int] = {}
    for s in steps:
        kinds[s["kind"]] = kinds.get(s["kind"], 0) + 1
    print("kinds:", kinds)
    for s in steps[:6] + steps[-6:]:
        txt = build_prompt(s["salt"], s["n_sent"])
        print(s["chain"], s["kind"], s.get("round"), "chars", len(txt),
              "est_tok", len(txt) // 4)
    # prefix-extension invariant
    for ch in CHAINS:
        salt = make_salt(910000 + CHAINS.index(ch))
        prev = None
        n = ch["n_sent"]
        for t in [0] + ch["tails"]:
            n += t if t else 0
            cur = build_prompt(salt, n)
            if prev is not None:
                assert cur.startswith(prev), "append is not a prefix extension"
            prev = cur
    print("prefix-extension invariant OK")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()
    raise SystemExit(dry() if a.dry or os.environ.get("E3_DRY") else run_live())
