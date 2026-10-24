#!/usr/bin/env python3
"""E4 ``boundary-n20`` -- re-measure U10's 64-boundary first-repeat miss at n=20.

Slot allocation is argued in ``orchestration/units/E4.md``: the card's literal
9 cells x 20 trials x 3 sends is 540 live requests against a hard cap of 220, so
the cells are the card's own drop-order survivors (960/1023/1024/1025/1088, with
960 restored because G9 names it, paid for by dropping the redundant control
1008), the two multiple-of-64 cells get three sends per trial (cold, repeat-1,
repeat-2) and the non-multiple controls get two.

Protocol carried from U2 / U10, unchanged:
  * fresh salt per trial -> fixed-width 20-char marker (constant 5-token cost) at
    token 0, so every cold request has a zero-length radix prefix match;
  * cold is *verified* (``cached == 0``), never assumed -- a warm cold row is a
    probe and the trial is redrawn;
  * the exact length is calibrated with one probe per cell (body sized ~25 tokens
    short, one-token ``" the"`` tail closes the gap) and every row records the
    **actual** ``prompt_tokens`` and ``prompt_tokens % 64``;
  * warm = byte-identical resend (sha256 recorded); no ``/flush_cache`` ever;
  * one request in flight, strictly serial.

Bounds: <=220 live requests, <=2400 s of sending, 3 consecutive failures abort.
Lock: ``fcntl.flock(LOCK_EX)`` on ``experiments/context-cache/.occamy.lock``,
2400 s acquisition deadline, acquired *after* all offline preparation (the cell
plan and file names are fixed below) and held until the last live request.

Usage::

    python3 e4_cell.py --dry-run   # no network: fake send, checks the controls
    python3 e4_cell.py             # live: lock, calibrate, run cells
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import importlib.util
import json
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
corpus = _load("e4_u10_corpus", HERE.parent / "U10" / "u10_corpus.py")
client_mod = _load("e4_client", EXP / "client.py")
from resextract.context.salt import make_salt  # noqa: E402

# --------------------------------------------------------------------------- #
# Pre-registered configuration (fixed before the first live request)
# --------------------------------------------------------------------------- #
CELLS: tuple[tuple[int, int, int], ...] = (  # (length, trials, sends per trial)
    (1024, 20, 3),
    (1088, 20, 3),
    (1023, 20, 2),
    (1025, 20, 2),
    (960, 7, 2),
)
MAX_REQUESTS = 220
MAX_SECONDS = 40 * 60
MAX_TOKENS = 2
THINKING = False
CPT = 4.3164  # prompt chars per token, U10 p1 median (4.3164 over 65 rows)
HEADROOM = 25  # tokens the one-token tail must be able to close
MAX_LEN_FIX = 8

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
}
ROWS_PATH = HERE / "e4_rows.jsonl"
RUN_PATH = HERE / "e4_run.json"


class StopBatch(RuntimeError):
    """A hard bound was hit (requests / seconds / consecutive failures)."""


# --------------------------------------------------------------------------- #
# Seeding + sending
# --------------------------------------------------------------------------- #
SEND: Any = None  # set by main(): the 7-tuple send, live or fake


def new_prompt(chars: int, tail: int) -> tuple[int, str, str]:
    """(seed, salt_hex, text) with a never-reused fixed-width marker."""

    seed = int(time.time_ns() % 10**12) + STATE["requests"]  # never reused, even across runs
    salt = make_salt(seed)
    return seed, salt, corpus.prompt_text(corpus.marker_for(salt), chars, 0, tail)


def can_send() -> bool:
    if STATE["requests"] >= MAX_REQUESTS:
        return False
    return time.time() - STATE["started"] < MAX_SECONDS


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
            "unit": "E4", "cell": cell, "trial": trial, "rep": None, "role": role,
            "seed": seed, "salt": salt, "chars": len(text), "tail": tail,
            "sha256": hashlib.sha256(text.encode()).hexdigest(),
            "prompt_tokens": None, "cached_tokens": None, "status": 0,
            "error": f"{type(exc).__name__}: {exc}", "ts": round(t0, 3),
            "gap_ms": None if gap_ms is None else round(gap_ms, 3),
        }
        STATE["rows"].append(row)  # type: ignore[attr-defined]
        _write_row(row)
        if STATE["consec"] >= 3:
            raise StopBatch(f"3 consecutive failures: {type(exc).__name__}: {exc}") from exc
        return row
    STATE["consec"] = 0
    STATE["requests"] += 1
    STATE["last_end"] = time.time()
    L = int(prompt)
    row = {
        "unit": "E4",
        "cell": cell,
        "trial": trial,
        "role": role,
        "seed": seed,
        "salt": salt,
        "chars": len(text),
        "tail": tail,
        "sha256": hashlib.sha256(text.encode()).hexdigest(),
        "prompt_tokens": L,
        "prompt_tokens_mod_64": L % 64,
        "cached_tokens": int(cached),
        "expected_u10": 64 * ((L - 1) // 64) if L > 0 else 0,
        "expected_plain": 64 * (L // 64) if L > 0 else 0,
        "block_tax": L - int(cached),
        "completion_tokens": int(completion),
        "ttft_ms": round(ttft, 3),
        "wall_ms": round(wall, 3),
        "gap_ms": None if gap_ms is None else round(gap_ms, 3),
        "status": status,
        "ts": round(t0, 3),
    }
    STATE["rows"].append(row)  # type: ignore[attr-defined]
    _write_row(row)
    _progress("running", 100.0 * STATE["requests"] / MAX_REQUESTS,
              f"L={cell} trial={trial} {role} cached={row['cached_tokens']}")
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
        with open(os.path.join(d, "e4-boundary.jsonl"), "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"v": 1, "task": "e4-boundary", "state": state,
                                 "pct": round(pct, 1), "msg": msg}) + "\n")
    except OSError:
        pass


# --------------------------------------------------------------------------- #
# Calibration: one probe per cell, then the tail closes the gap exactly
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
        rep1 = send(text, cell=target, trial=len(trials) + 1, role="rep1", seed=seed, salt=salt, tail=tail)
        rep2 = None
        if sends >= 3 and can_send():
            rep2 = send(text, cell=target, trial=len(trials) + 1, role="rep2", seed=seed, salt=salt, tail=tail)
        trials.append({"L": L, "cold": cold, "rep1": rep1, "rep2": rep2})
        r1 = rep1.get("cached_tokens")
        r2 = None if rep2 is None else rep2.get("cached_tokens")
        print(
            f"  [cell {target}] trial {len(trials):2d}/{n_trials} L={L} L%64={L % 64} "
            f"rep1_cached={r1} rep2_cached={r2} ttft={rep1.get('ttft_ms')}",
            flush=True,
        )
    misses = sum(1 for t in trials if (t["rep1"].get("cached_tokens") or 0) == 0)
    print(f"[cell {target}] trials={len(trials)} rep1_full_misses={misses}", flush=True)
    return {"L": target, "trials": len(trials), "sends_per_trial": sends, "chars": chars,
            "tail": tail, "rep1_misses": misses}


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


# --------------------------------------------------------------------------- #
# Run log
# --------------------------------------------------------------------------- #
def write_runlog(extra: dict[str, Any] | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "unit": "E4",
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
    RUN_PATH.write_text(json.dumps(payload, indent=1) + "\n", encoding="utf-8")
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
        if n == 0 or L % 64 != 0:
            cached = 0 if n == 0 else 64 * ((L - 1) // 64)
        else:  # boundary: first repeat misses, later repeats pay one block
            cached = 0 if n == 1 else 64 * ((L - 1) // 64)
        return (L, cached, 2, 12.0, 14.0, 200, "ok")

    return _fake


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    STATE["rows"] = []
    STATE["started"] = time.time()
    ROWS_PATH.write_text("", encoding="utf-8")  # fresh rows for this run
    _progress("running", 0.0, "starting")

    if args.dry_run:
        STATE["max"] = MAX_REQUESTS
        global SEND
        SEND = fake_send_factory()
        for L, n, s in CELLS:
            got = calibrate(L)
            if got is None:
                continue
            run_cell(L, n, s, got[0], got[1])
        log = write_runlog({"mode": "dry-run"})
        print(json.dumps({k: log[k] for k in ("requests", "probes", "row_count", "aborted")}, indent=1))
        return 0

    try:
        fd, wait = acquire_lock(EXP / ".occamy.lock", 2400.0)
    except Exception as exc:  # noqa: BLE001
        STATE["aborted"] = f"lock error: {type(exc).__name__}: {exc}"
        write_runlog()
        return 3
    STATE["lock_wait_s"] = round(wait, 3)
    if fd is None:
        STATE["aborted"] = "lock timeout"
        write_runlog({"status": "partial", "blocker": "lock timeout"})
        print("LOCK TIMEOUT after 2400 s", flush=True)
        return 3
    print(f"lock acquired after {wait:.2f}s", flush=True)

    # live send = the shared client, exactly as U10/U2 wired it
    SEND = client_mod.chat

    def _live(messages: list[dict[str, str]]) -> tuple[int, int, int, float, float, int, str]:
        return client_mod.chat(
            messages, max_tokens=MAX_TOKENS, thinking=THINKING, stream=True, timeout=120.0
        )

    SEND = _live
    rc = 0
    try:
        calibrated: dict[int, tuple[int, int]] = {}
        for L, _n, _s in CELLS:  # calibrate every cell before spending on trials
            got = calibrate(L)
            if got is None:
                STATE["notes"].append(f"L={L}: not calibrated, cell skipped")
                continue
            calibrated[L] = got
        for L, n, s in CELLS:
            if L not in calibrated:
                continue
            if not can_send():
                STATE["notes"].append(f"L={L}: bound reached before cell")
                break
            run_cell(L, n, s, calibrated[L][0], calibrated[L][1])
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
        log = write_runlog({"status": "partial" if rc else "ok"})
        release_lock(fd)
        _progress("done" if rc == 0 else "failed", 100.0,
                  f"requests={log['requests']} rows={log.get('row_count')} aborted={log['aborted']}")
        print(
            json.dumps(
                {"requests": log["requests"], "probes": log["probes"], "rows": log.get("row_count"),
                 "aborted": log["aborted"], "lock_wait_s": log["lock_wait_s"],
                 "elapsed_s": log["elapsed_s"], "rows_sha256": log.get("rows_sha256")},
                indent=1,
            ),
            flush=True,
        )
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
