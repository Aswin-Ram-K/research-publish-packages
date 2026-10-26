#!/usr/bin/env python3
"""E4R ``rep3-probe`` -- is the multiple-of-64 64-token lag a one-repeat lag or a
persistent ceiling?

E4 measured repeat-1 (``cached == 0``, 45/45) and repeat-2 (``cached == L-64``,
40/40) but never repeat-3. Two verifiers (VE4, VE24) scoped "deterministic" to
description only and both flagged rep-3 as the missing discriminator. This cell
adds repeat-3 (and, budget permitting, repeat-4) under E4's protocol verbatim:

  * fresh salt per trial -> fixed-width 20-char marker (constant 5-token cost) at
    token 0, so every cold request has a zero-length radix prefix match;
  * cold is *verified* (``cached == 0``), never assumed -- a warm cold row is a
    probe and the trial is redrawn;
  * the exact length is calibrated with one or more probes per cell (body sized
    ~25 tokens short, one-token ``" the"`` tail closes the gap) and every row
    records the **actual** ``prompt_tokens`` and ``prompt_tokens % 64``;
  * warm = byte-identical resend (sha256 recorded); no ``/flush_cache`` ever;
  * one request in flight, strictly serial.

Row roles keep E4's names so rows are directly comparable:
``cold, rep1 (repeat 1), rep2 (repeat 2), rep3 (repeat 3)``.  ``send_index``
(1..4) and ``repeat_index`` (0..3) are recorded too, because the E4R card counts
"rep-2 / rep-3" as sends while E4 counts them as repeats.

Cells: 1024 and 1088 at n=20 with 4 sends (cold + three repeats); 1008 and 1152
sampled at n=5 with 2 sends only if the 180-request cap still has room.  Rep-3
depth is paid for first; the neighbours are last by construction.

Bounds: <=180 live requests, <=20 min of sending (MAX_SECONDS 1100 s), 3
consecutive failures abort -> ``partial`` with rows.
Lock: ``fcntl.flock(LOCK_EX)`` on ``experiments/context-cache/.occamy.lock``,
1800 s acquisition deadline, acquired before the first live request and held to
the last; released on exit.

Usage::

    python3 e4r_cell.py --dry-run   # no network: fake send, checks the controls
    python3 e4r_cell.py             # live: lock, calibrate, run cells, report
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import importlib.util
import json
import math
import os
import sys
import time
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
SRC = REPO / "src"
EXP = REPO / "experiments" / "context-cache"
for _p in (str(SRC), str(EXP), str(HERE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)


def _load(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:  # pragma: no cover
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


#: U10's token-stable corpus (imported by path, never edited -- sha256 recorded).
corpus = _load("e4r_u10_corpus", HERE.parent / "U10" / "u10_corpus.py")
client_mod = _load("e4r_client", EXP / "client.py")
from resextract.context.salt import make_salt  # noqa: E402

# --------------------------------------------------------------------------- #
# Pre-registered configuration (fixed before the first live request)
# --------------------------------------------------------------------------- #
CELLS: tuple[tuple[int, int, int], ...] = (  # (length, trials, sends per trial)
    (1024, 20, 4),
    (1088, 20, 4),
    (1008, 5, 2),
    (1152, 5, 2),
)
MAX_REQUESTS = 180
MAX_SECONDS = 1100  # under the 20 min wall; requests are ~0.25 s each
MAX_TOKENS = 2
THINKING = False
CPT = 4.3164  # prompt chars per token, U10 p1 median (4.3164 over 65 rows)
HEADROOM = 25  # tokens the one-token tail must be able to close
MAX_LEN_FIX = 8
LOCK_PATH = EXP / ".occamy.lock"
LOCK_DEADLINE_S = 1800.0

ROLES = ("cold", "rep1", "rep2", "rep3")

STATE: dict[str, Any] = {
    "requests": 0,
    "failures": 0,
    "consec": 0,
    "probes": 0,
    "notes": [],
    "errors": [],
    "started": time.time(),
    "last_end": 0.0,
    "aborted": "",
    "lock_wait_s": None,
    "rows": [],
}
ROWS_PATH = HERE / "e4r_rows.jsonl"


class StopBatch(RuntimeError):
    """A hard bound was hit (requests / seconds / consecutive failures)."""


SEND: Any = None  # set by main(): the 7-tuple send, live or fake


# --------------------------------------------------------------------------- #
# Seeding + sending
# --------------------------------------------------------------------------- #
def new_prompt(chars: int, tail: int) -> tuple[int, str, str]:
    """(seed, salt_hex, text) with a never-reused fixed-width marker."""

    seed = int(time.time_ns() % 10**12) + STATE["requests"]
    salt = make_salt(seed)
    return seed, salt, corpus.prompt_text(corpus.marker_for(salt), chars, 0, tail)


def can_send() -> bool:
    if STATE["requests"] >= MAX_REQUESTS:
        return False
    return time.time() - STATE["started"] < MAX_SECONDS


def _ceil_u10(L: int) -> int:
    return 64 * ((L - 1) // 64) if L > 0 else 0


def _ceil_plain(L: int) -> int:
    return 64 * (L // 64) if L > 0 else 0


def send(
    text: str,
    *,
    cell: int | None,
    trial: int,
    role: str,
    seed: int,
    salt: str,
    tail: int,
) -> dict[str, Any]:
    if not can_send():
        raise StopBatch(f"bound reached (requests={STATE['requests']})")
    t0 = time.time()
    gap_ms = (t0 - STATE["last_end"]) * 1000.0 if STATE["last_end"] else None
    try:
        prompt, cached, completion, ttft, wall, status, _txt = SEND(
            [{"role": "user", "content": text}]
        )
    except Exception as exc:  # noqa: BLE001 -- any wire failure is a data point
        STATE["failures"] += 1
        STATE["consec"] += 1
        row = {
            "unit": "E4R", "cell": cell, "trial": trial, "role": role,
            "send_index": ROLES.index(role) + 1 if role in ROLES else None,
            "repeat_index": ROLES.index(role) if role in ROLES else None,
            "seed": seed, "salt": salt, "chars": len(text), "tail": tail,
            "sha256": hashlib.sha256(text.encode()).hexdigest(),
            "prompt_tokens": None, "cached_tokens": None, "status": 0,
            "error": f"{type(exc).__name__}: {exc}", "ts": round(t0, 3),
            "gap_ms": None if gap_ms is None else round(gap_ms, 3),
        }
        STATE["rows"].append(row)
        _write_row(row)
        if STATE["consec"] >= 3:
            raise StopBatch(f"3 consecutive failures: {type(exc).__name__}: {exc}") from exc
        return row
    STATE["consec"] = 0
    STATE["requests"] += 1
    STATE["last_end"] = time.time()
    L = int(prompt)
    c = int(cached)
    row = {
        "unit": "E4R",
        "cell": cell,
        "trial": trial,
        "role": role,
        "send_index": ROLES.index(role) + 1 if role in ROLES else None,
        "repeat_index": ROLES.index(role) if role in ROLES else None,
        "seed": seed,
        "salt": salt,
        "chars": len(text),
        "tail": tail,
        "sha256": hashlib.sha256(text.encode()).hexdigest(),
        "prompt_tokens": L,
        "prompt_tokens_mod_64": L % 64,
        "cached_tokens": c,
        "expected_u10": _ceil_u10(L),
        "expected_plain": _ceil_plain(L),
        "block_tax": L - c,
        "cached_eq_L": c == L,
        "cached_eq_L_minus_64": c == L - 64,
        "cached_eq_ceiling_u10": c == _ceil_u10(L),
        "implied_ceiling": 64 * (c // 64),
        "completion_tokens": int(completion),
        "ttft_ms": round(ttft, 3),
        "wall_ms": round(wall, 3),
        "gap_ms": None if gap_ms is None else round(gap_ms, 3),
        "status": status,
        "ts": round(t0, 3),
    }
    STATE["rows"].append(row)
    _write_row(row)
    _progress("running", 100.0 * STATE["requests"] / MAX_REQUESTS,
              f"L={cell} trial={trial} {role} cached={c} L%64={L % 64}")
    return row


def _write_row(row: dict[str, Any]) -> None:
    with ROWS_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, sort_keys=True) + "\n")


def _progress(state: str, pct: float, msg: str) -> None:
    """Append one progress event for the human's view (never read back)."""

    d = os.environ.get("DSH_PROGRESS_DIR")
    if not d:
        return
    try:
        with open(os.path.join(d, "e4r-rep3.jsonl"), "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"v": 1, "task": "e4r-rep3", "state": state,
                                 "pct": round(pct, 1), "msg": msg}) + "\n")
    except OSError:
        pass


# --------------------------------------------------------------------------- #
# Calibration: one or more probes per cell, then the tail closes the gap exactly
# --------------------------------------------------------------------------- #
def calibrate(target: int) -> tuple[int, int] | None:
    chars = max(200, int(round((target - 5 - HEADROOM) * CPT)))
    tail = 0
    fixes = 0
    while can_send() and fixes < MAX_LEN_FIX:
        seed, salt, text = new_prompt(chars, tail)
        row = send(text, cell=target, trial=0, role="cal", seed=seed, salt=salt, tail=tail)
        STATE["probes"] += 1
        fixes += 1
        L = row.get("prompt_tokens") or 0
        if not L:
            chars = max(200, chars - 8)
            continue
        if (row.get("cached_tokens") or 0) != 0:
            STATE["notes"].append(f"cal L={target}: cold cached={row['cached_tokens']} (redraw)")
            continue
        delta = target - L
        if delta == 0:
            STATE["notes"].append(f"cal L={target}: exact at chars={chars} tail={tail}")
            return chars, tail
        if delta > 0:
            tail += delta
        else:  # self-calibrating: use the ratio this probe actually showed
            chars = max(200, chars + int(round(delta * (len(text) / L))) - 1)
            tail = 0
    STATE["notes"].append(f"cal L={target}: FAILED to reach exact length")
    return None


# --------------------------------------------------------------------------- #
# One cell
# --------------------------------------------------------------------------- #
def run_cell(target: int, n_trials: int, sends: int, chars: int, tail: int) -> dict[str, Any]:
    trials: list[dict[str, Any]] = []
    fixes = 0
    while len(trials) < n_trials and can_send():
        seed, salt, text = new_prompt(chars, tail)
        cold = send(text, cell=target, trial=len(trials) + 1, role="cold", seed=seed, salt=salt, tail=tail)
        if cold.get("prompt_tokens") is None:
            STATE["notes"].append(f"L={target}: cold failed ({cold.get('error')})")
            continue
        L = int(cold["prompt_tokens"])
        if (cold.get("cached_tokens") or 0) != 0:
            STATE["notes"].append(f"L={target}: cold cached={cold['cached_tokens']} (redraw)")
            continue
        if L != target:  # length drifted: correct the knobs, this row is a probe
            delta = target - L
            if tail + delta >= 0:
                tail += delta
            else:
                chars = max(200, chars + int(round(delta * (len(text) / L))) - 1)
                tail = 0
            fixes += 1
            STATE["notes"].append(f"L={target}: length {L} != {target}; tail->{tail} chars->{chars}")
            if fixes >= MAX_LEN_FIX:
                STATE["notes"].append(f"L={target}: giving up on exact length")
                break
            continue
        reps: dict[str, dict[str, Any]] = {}
        for role in ROLES[1:sends]:
            if not can_send():
                break
            reps[role] = send(text, cell=target, trial=len(trials) + 1, role=role,
                              seed=seed, salt=salt, tail=tail)
        trials.append({"L": L, "role_rows": {"cold": cold, **reps}})
        got = " ".join(f"{r}={reps[r].get('cached_tokens')}" for r in reps)
        print(f"  [cell {target}] trial {len(trials):2d}/{n_trials} L={L} L%64={L % 64} {got}", flush=True)
    misses = sum(1 for t in trials if (t["role_rows"]["rep1"].get("cached_tokens") or 0) == 0)
    print(f"[cell {target}] trials={len(trials)} sends={sends} rep1_full_misses={misses}", flush=True)
    return {"L": target, "trials": trials, "n_planned": n_trials, "sends_per_trial": sends,
            "chars": chars, "tail": tail, "rep1_misses": misses}


# --------------------------------------------------------------------------- #
# Analysis (definitions carried from E4: cached_tokens is the server's account)
# --------------------------------------------------------------------------- #
def _binom_cdf(k: int, n: int, p: float) -> float:
    if p <= 0.0:
        return 1.0
    if p >= 1.0:
        return 0.0 if k < n else 1.0
    return min(1.0, sum(math.comb(n, i) * p**i * (1.0 - p) ** (n - i) for i in range(0, max(-1, k) + 1)))


def cp95(k: int, n: int) -> list[float]:
    """Exact Clopper-Pearson two-sided 95% interval, by bisection on the CDF."""

    if n == 0:
        return [0.0, 1.0]
    if k == 0:
        return [0.0, round(1.0 - 0.025 ** (1.0 / n), 4)]
    if k == n:
        return [round(0.025 ** (1.0 / n), 4), 1.0]
    lo, hi = 0.0, 1.0
    for _ in range(200):
        mid = (lo + hi) / 2.0
        if _binom_cdf(k - 1, n, mid) > 0.025:
            hi = mid
        else:
            lo = mid
    lower = (lo + hi) / 2.0
    lo, hi = 0.0, 1.0
    for _ in range(200):
        mid = (lo + hi) / 2.0
        if _binom_cdf(k, n, mid) < 0.975:
            lo = mid
        else:
            hi = mid
    upper = (lo + hi) / 2.0
    return [round(lower, 4), round(upper, 4)]


def analyse(cells: dict[int, dict[str, Any]], rows: list[dict[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {"unit": "E4R", "cells": [], "pooled": {}, "rows_sha256": None}
    for L in sorted(cells):
        cell = cells[L]
        entry: dict[str, Any] = {
            "L": L, "L_mod_64": L % 64, "multiple_of_64": L % 64 == 0,
            "n_trials": len(cell["trials"]), "n_planned": cell["n_planned"],
            "sends_per_trial": cell["sends_per_trial"], "length_exact": True,
            "cold_cached_nonzero": 0, "per_rep": {},
        }
        lens = set()
        for t in cell["trials"]:
            lens.add(t["L"])
            if (t["role_rows"]["cold"].get("cached_tokens") or 0) != 0:
                entry["cold_cached_nonzero"] += 1
        entry["lengths_seen"] = sorted(lens)
        entry["length_exact"] = lens == {L}
        for role in ROLES[1:cell["sends_per_trial"]]:
            vals = [t["role_rows"][role].get("cached_tokens") for t in cell["trials"]
                    if t["role_rows"].get(role)]
            n = len(vals)
            hist: dict[str, int] = {}
            for v in vals:
                hist[str(v)] = hist.get(str(v), 0) + 1
            entry["per_rep"][role] = {
                "n": n,
                "cached_hist": hist,
                "eq_L": sum(1 for v in vals if v == L),
                f"eq_L_minus_64": sum(1 for v in vals if v == L - 64),
                "eq_zero": sum(1 for v in vals if v == 0),
                "eq_ceiling_u10": sum(1 for v in vals if v == _ceil_u10(L)),
                "eq_ceiling_u10_rate_cp95": cp95(sum(1 for v in vals if v == _ceil_u10(L)), n),
                "block_tax_hist": {},
                "ttft_ms_median": None,
            }
            taxes: dict[str, int] = {}
            for t in cell["trials"]:
                r = t["role_rows"].get(role)
                if r and r.get("prompt_tokens") is not None:
                    k = str(int(r["prompt_tokens"]) - int(r["cached_tokens"]))
                    taxes[k] = taxes.get(k, 0) + 1
            entry["per_rep"][role]["block_tax_hist"] = taxes
            ttfts = sorted(t["role_rows"][role]["ttft_ms"] for t in cell["trials"]
                           if t["role_rows"].get(role) and t["role_rows"][role].get("ttft_ms") is not None)
            if ttfts:
                mid = len(ttfts) // 2
                entry["per_rep"][role]["ttft_ms_median"] = (
                    ttfts[mid] if len(ttfts) % 2 else round((ttfts[mid - 1] + ttfts[mid]) / 2, 3))
        # per-trial persistence: rep3 == rep2's cached value?
        same_23 = [t for t in cell["trials"]
                   if t["role_rows"].get("rep2") and t["role_rows"].get("rep3")]
        entry["rep3_equals_rep2_per_trial"] = sum(
            1 for t in same_23
            if t["role_rows"]["rep3"].get("cached_tokens") == t["role_rows"]["rep2"].get("cached_tokens"))
        entry["rep3_equals_rep2_n"] = len(same_23)
        # classification of the rep-3 rows against the pre-registered predictions
        r3 = entry["per_rep"].get("rep3", {})
        if r3.get("n"):
            n = r3["n"]
            if r3["eq_L_minus_64"] == n and r3["eq_L"] == 0:
                verdict = "one-repeat lag PERSISTS: rep3 == L-64 in %d/%d (persistent ceiling)" % (n, n)
            elif r3["eq_L"] == n:
                verdict = "TRANSIENT: rep3 recovered cached == L in %d/%d" % (n, n)
            elif r3["eq_L_minus_64"] == 0 and r3["eq_L"] == 0:
                verdict = "WORSE: rep3 matched neither L-64 nor L in %d/%d rows" % (
                    n - r3["eq_L_minus_64"] - r3["eq_L"], n)
            else:
                verdict = "MIXED: rep3 L-64 %d/%d, L %d/%d, other %d/%d" % (
                    r3["eq_L_minus_64"], n, r3["eq_L"], n,
                    n - r3["eq_L_minus_64"] - r3["eq_L"], n)
        else:
            verdict = "not measured (budget)"
        entry["rep3_verdict"] = verdict
        out["cells"].append(entry)
    # pooled rep3 across the two n=20 boundary cells
    pool: dict[str, Any] = {}
    for role in ("rep2", "rep3"):
        vals: list[tuple[int, int]] = []
        for L in (1024, 1088):
            c = cells.get(L)
            if not c:
                continue
            for t in c["trials"]:
                r = t["role_rows"].get(role)
                if r and r.get("cached_tokens") is not None:
                    vals.append((L, int(r["cached_tokens"])))
        n = len(vals)
        pool[role] = {
            "n": n,
            "eq_L_minus_64": sum(1 for L, v in vals if v == L - 64),
            "eq_L": sum(1 for L, v in vals if v == L),
            "eq_ceiling_u10": sum(1 for L, v in vals if v == _ceil_u10(L)),
            "eq_ceiling_u10_rate_cp95": cp95(sum(1 for L, v in vals if v == _ceil_u10(L)), n),
            "values": sorted({v for _L, v in vals}),
        }
    out["pooled"] = pool
    out["rows_total"] = len(rows)
    out["rows_by_role"] = {}
    for r in rows:
        k = str(r.get("role"))
        out["rows_by_role"][k] = out["rows_by_role"].get(k, 0) + 1
    if ROWS_PATH.exists():
        out["rows_sha256"] = hashlib.sha256(ROWS_PATH.read_bytes()).hexdigest()
    out["statement_rep3"] = (
        "rep-3 at L=1024: %s; at L=1088: %s; pooled %d/%d rows sit at exactly "
        "64*floor((L-1)/64) == L-64, %d/%d at L." % (
            next((c["rep3_verdict"] for c in out["cells"] if c["L"] == 1024), "n/a"),
            next((c["rep3_verdict"] for c in out["cells"] if c["L"] == 1088), "n/a"),
            pool.get("rep3", {}).get("eq_ceiling_u10", 0), pool.get("rep3", {}).get("n", 0),
            pool.get("rep3", {}).get("eq_L", 0), pool.get("rep3", {}).get("n", 0),
        ))
    return out


# --------------------------------------------------------------------------- #
# Lock
# --------------------------------------------------------------------------- #
def acquire_lock(path: Path, deadline_s: float) -> tuple[int | None, float]:
    fd = os.open(str(path), os.O_CREAT | os.O_RDWR, 0o644)
    t0 = time.time()
    last_note = 0.0
    while True:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return fd, time.time() - t0
        except OSError:
            waited = time.time() - t0
            if waited >= deadline_s:
                os.close(fd)
                return None, waited
            if waited - last_note >= 15.0:
                last_note = waited
                print(f"  waiting for .occamy.lock ({waited:.0f}s / {deadline_s:.0f}s)", flush=True)
            time.sleep(0.5)


def release_lock(fd: int) -> None:
    try:
        fcntl.flock(fd, fcntl.LOCK_UN)
    finally:
        os.close(fd)


def write_runlog(extra: dict[str, Any] | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "unit": "E4R",
        "cells_plan": [{"L": L, "trials": n, "sends": s} for L, n, s in CELLS],
        "requests": STATE["requests"],
        "probes": STATE["probes"],
        "failures": STATE["failures"],
        "aborted": STATE["aborted"],
        "notes": STATE["notes"],
        "errors": STATE["errors"],
        "lock_wait_s": STATE["lock_wait_s"],
        "elapsed_s": round(time.time() - STATE["started"], 1),
        "max_requests": MAX_REQUESTS,
        "max_seconds": MAX_SECONDS,
    }
    if extra:
        payload.update(extra)
    if ROWS_PATH.exists():
        payload["rows_sha256"] = hashlib.sha256(ROWS_PATH.read_bytes()).hexdigest()
        payload["row_count"] = sum(1 for _ in ROWS_PATH.open("rb"))
    (HERE / "e4r_run.json").write_text(json.dumps(payload, indent=1) + "\n", encoding="utf-8")
    return payload


# --------------------------------------------------------------------------- #
# Fake send (offline control-flow check; no network)
# --------------------------------------------------------------------------- #
def fake_send_factory() -> Any:
    seen: dict[str, int] = {}

    def _fake(messages: list[dict[str, str]]) -> tuple[int, int, int, float, float, int, str]:
        text = messages[0]["content"]
        L = 5 + int(round(len(text) / 4.0))  # fake: each " the" is exactly one token
        h = hashlib.sha256(text.encode()).hexdigest()
        n = seen.get(h, 0)
        seen[h] = n + 1
        if n == 0:
            cached = 0
        elif L % 64 != 0:
            cached = 64 * ((L - 1) // 64)
        else:  # boundary: first repeat misses, every later repeat pays one block
            cached = _ceil_u10(L)
        return (L, cached, 2, 12.0, 14.0, 200, "ok")

    return _fake


def main(argv: list[str] | None = None) -> int:
    global ROWS_PATH, SEND
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    STATE["started"] = time.time()
    if args.dry_run:
        ROWS_PATH = HERE / "e4r_rows_dryrun.jsonl"
    ROWS_PATH.write_text("", encoding="utf-8")  # fresh rows for this run
    _progress("running", 0.0, "dry-run" if args.dry_run else "starting")

    if args.dry_run:
        SEND = fake_send_factory()
        cells: dict[int, dict[str, Any]] = {}
        for L, n, s in CELLS:
            got = calibrate(L)
            if got is None:
                continue
            cells[L] = run_cell(L, n, s, got[0], got[1])
        rep = analyse(cells, STATE["rows"])
        (HERE / "e4r_report_dryrun.json").write_text(json.dumps(rep, indent=1) + "\n", encoding="utf-8")
        log = write_runlog({"mode": "dry-run"})
        print(json.dumps({k: log[k] for k in ("requests", "probes", "row_count", "aborted")}, indent=1))
        print(json.dumps({c["L"]: c["rep3_verdict"] for c in rep["cells"]}, indent=1))
        return 0

    try:
        fd, wait = acquire_lock(LOCK_PATH, LOCK_DEADLINE_S)
    except Exception as exc:  # noqa: BLE001
        STATE["aborted"] = f"lock error: {type(exc).__name__}: {exc}"
        write_runlog({"status": "partial"})
        return 3
    STATE["lock_wait_s"] = round(wait, 3)
    if fd is None:
        STATE["aborted"] = "lock timeout"
        write_runlog({"status": "partial", "blocker": "lock timeout"})
        print("LOCK TIMEOUT after 1800 s", flush=True)
        return 3
    print(f"lock acquired after {wait:.2f}s", flush=True)

    def _live(messages: list[dict[str, str]]) -> tuple[int, int, int, float, float, int, str]:
        return client_mod.chat(
            messages, max_tokens=MAX_TOKENS, thinking=THINKING, stream=True, timeout=120.0
        )

    SEND = _live
    rc = 0
    cells: dict[int, dict[str, Any]] = {}
    try:
        for L, n, s in CELLS:  # calibrate a cell, run it, move on (main cells first)
            if not can_send():
                STATE["notes"].append(f"L={L}: bound reached before cell")
                break
            got = calibrate(L)
            if got is None:
                STATE["notes"].append(f"L={L}: not calibrated, cell skipped")
                continue
            cells[L] = run_cell(L, n, s, got[0], got[1])
    except StopBatch as exc:
        STATE["aborted"] = str(exc)
        rc = 2
        print(f"STOP: {exc}", flush=True)
    except Exception as exc:  # noqa: BLE001
        STATE["aborted"] = f"{type(exc).__name__}: {exc}"
        STATE["errors"].append(STATE["aborted"])
        rc = 2
        print(f"STOP: {STATE['aborted']}", flush=True)
    finally:
        rep = analyse(cells, STATE["rows"])
        (HERE / "e4r_report.json").write_text(json.dumps(rep, indent=1) + "\n", encoding="utf-8")
        log = write_runlog({"status": "partial" if rc else "ok"})
        release_lock(fd)
        _progress("done" if rc == 0 else "failed", 100.0,
                  f"requests={log['requests']} rows={log.get('row_count')} aborted={log['aborted']}")
        print(json.dumps(
            {"requests": log["requests"], "probes": log["probes"], "rows": log.get("row_count"),
             "aborted": log["aborted"], "lock_wait_s": log["lock_wait_s"],
             "elapsed_s": log["elapsed_s"], "rows_sha256": log.get("rows_sha256")}, indent=1), flush=True)
        for c in rep["cells"]:
            print(f"L={c['L']} n={c['n_trials']} rep3: {c['rep3_verdict']}", flush=True)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
