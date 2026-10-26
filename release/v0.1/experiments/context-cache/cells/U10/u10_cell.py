#!/usr/bin/env python3
"""U10 live driver -- characterise the 64-boundary *first-repeat* miss.

Question
--------
U9 saw, at exactly ``prompt_tokens == 1024`` (a multiple of 64), that the
*immediately repeated* identical request reported ``cached = 0`` and paid full
prefill (207 ms), while the second repeat hit 960 (86 ms).  That was 3/3 at
1024 and 0/4 at 1021-1023.  U4b independently lost one of eight fan-out
branches to a ``cached = 0`` on its first warm request.  Are these one
mechanism?

Pre-registered design
---------------------
* **One variable per phase.**  Phase 1 varies only the prompt length; phase 2
  only the gap between a cold request and its repeat (at the worst length from
  phase 1); phase 3 inserts one short unrelated request into that gap.
* **Cold is forced by a never-reused marker.**  ``make_salt(seed)`` still
  generates the salt; six of its hex digits select three fixed-width marker
  words, so the marker costs a constant number of tokens and an *exact* prompt
  length is reachable (``u10_corpus.py`` explains why U9's raw hex salt cannot
  do this: it jitters +/-2 tokens, which is fatal on a 64-token boundary).
* **The length is verified, never assumed.**  Every cold request IS the length
  check for its trial: if the achieved ``prompt_tokens`` is not the cell's
  length (or not the declared exact target for the boundary cells), that
  request is logged as a *probe*, the char count is corrected, and the trial
  is retried.  A cell's length is therefore whatever the server reported, and
  every trial in the cell must report the same value.
* **Miss is measured.**  ``cached == 0`` on the repeat is a *full* miss;
  ``0 < cached < 64*((L-1)//64)`` is recorded as a partial miss.
* **Serial.**  Exactly one request in flight.  No ``flock`` (other units hold
  it, and token counts do not need it) and **never** ``POST /flush_cache``.
* **Hard bounds.**  ``MAX_REQUESTS = 120`` here plus 8 already spent by
  ``u10_smoke.py`` = 158 live requests (< 160), 20 minutes wall.

Phases
------
``p1``  for each target length: cold -> repeat#1 (-> repeat#2 whenever
        repeat#1 missed), five valid trials per cell.
``p2``  at the worst length from p1: cold -> sleep(d) -> repeat,
        d in {0.0, 0.25, 0.5, 1.0, 2.0} s, n=5.
``p3``  at the worst length: cold -> short unrelated request -> repeat, n=5.

Write contract: only ``experiments/context-cache/cells/U10/``.
"""

from __future__ import annotations

import argparse
import functools
import importlib.util
import json
import sys
import time
from pathlib import Path
from typing import Any, Callable

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
SRC = REPO / "src"
EXP = REPO / "experiments" / "context-cache"

sys.path.insert(0, str(SRC))
sys.path.insert(0, str(EXP))
sys.path.insert(0, str(HERE))

import u10_corpus as corpus  # noqa: E402

from resextract.context.salt import make_salt  # noqa: E402


def _load(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:  # pragma: no cover
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


client_mod = _load("u10_client", EXP / "client.py")

# --------------------------------------------------------------------------- #
# Configuration (pre-registered)
# --------------------------------------------------------------------------- #
SEED = 20261022

#: The boundary, its two immediate neighbours, one other multiple of 64
#: (1088 = 17*64) as the generalisation check, and one non-multiple well below
#: it.  Cells are ordered most-informative-first because the request cap can
#: truncate the sweep.  960/1020/1028/1152/2048/4096 from the card's list are
#: dropped: pilot probes (see u10_report.json "budget") cost 39 of the 160
#: allowed requests, and the remaining 121 cannot pay for them *and* phases 2
#: and 3; 1088 already asks whether a second multiple behaves like 1024.
LENGTHS = (1024, 1023, 1025, 1088, 1008)
#: Cells that must be hit exactly (the boundary and its neighbours).
EXACT = (1023, 1024, 1025, 1088)
#: Body is sized this many tokens short of the target so the one-token tail can
#: always close the remaining gap.
HEADROOM_TOKENS = 12

REPS = 5
DELAYS = (0.0, 0.25, 0.5, 1.0, 2.0)
UNRELATED_CHARS = 200  # ~55 tokens: a genuinely short unrelated request
MAX_TOKENS = 2
THINKING = False

MAX_REQUESTS = 120
MAX_SECONDS = 20 * 60
PHASE_CAP = {"p1": 68, "p2": 45, "p3": 15}
RESERVE_P3 = 15
MAX_PROBES_PER_CELL = 8

CPT = {"v": 4.30}  # prompt chars per token; updated from every reply
#: Seed block: the pilot probes (u10_pilot.json) used SEED*1000 + 1..39, and
#: markers are deterministic, so the live run starts a million seeds later --
#: otherwise a live "cold" prompt can be an extension of a pilot prompt with
#: the *same* marker, which is exactly what fooled the first pilot probe.
SEED_BASE = SEED * 1000 + 1_000_000
SEQ = {"n": 0, "seed": SEED_BASE, "failures": 0, "consec_failures": 0}
USED = {"total": 0, "p1": 0, "p2": 0, "p3": 0}
ROWS: list[dict[str, Any]] = []
NOTES: list[str] = []
STARTED = time.time()
LAST_END = {"t": 0.0}


class StopBatch(RuntimeError):
    """A hard bound was hit (requests / seconds / consecutive failures)."""


# --------------------------------------------------------------------------- #
# Seeding + sending
# --------------------------------------------------------------------------- #
def next_seed() -> int:
    SEQ["seed"] += 1
    return SEQ["seed"]


def new_prompt(body_chars: int, variant: int = 0, tail: int = 0) -> tuple[int, str, str]:
    """(seed, salt_hex, prompt text) carrying a never-reused marker."""

    seed = next_seed()
    salt = make_salt(seed)
    return seed, salt, corpus.prompt_text(
        corpus.marker_for(salt), body_chars, variant, tail
    )


def can_send(phase: str) -> bool:
    if USED["total"] >= MAX_REQUESTS:
        return False
    if USED[phase] >= PHASE_CAP[phase]:
        return False
    return time.time() - STARTED < MAX_SECONDS


SEND: Callable[[list[dict[str, str]]], Any] = lambda _m: (0, 0, 0, 0.0, 0.0, 200, "")


def send(
    text: str,
    *,
    phase: str,
    role: str,
    target: int | None,
    seed: int,
    salt: str,
    rep: int | None = None,
    delay_s: float = 0.0,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not can_send(phase):
        raise StopBatch(f"cap reached in phase {phase} (total={USED['total']})")
    t0 = time.time()
    gap_ms = (t0 - LAST_END["t"]) * 1000.0 if LAST_END["t"] else None
    try:
        prompt, cached, completion, ttft, wall, status, _text = SEND(
            [{"role": "user", "content": text}]
        )
    except Exception as exc:  # noqa: BLE001 - any wire failure is a data point
        SEQ["failures"] += 1
        SEQ["consec_failures"] += 1
        row = {
            "seq": None, "phase": phase, "role": role, "length_target": target,
            "rep": rep, "delay_s": delay_s, "seed": seed, "salt": salt, "chars": len(text),
            "prompt_tokens": None, "cached_tokens": None, "status": 0,
            "error": f"{type(exc).__name__}: {exc}", "ts": round(t0, 3),
        }
        ROWS.append(row)
        if SEQ["consec_failures"] >= 3:
            raise StopBatch(f"3 consecutive failures: {type(exc).__name__}: {exc}") from exc
        return row
    SEQ["consec_failures"] = 0
    SEQ["n"] += 1
    USED["total"] += 1
    USED[phase] += 1
    LAST_END["t"] = time.time()
    expected = 64 * ((prompt - 1) // 64) if prompt > 0 else 0
    row = {
        "unit": "U10",
        "seq": SEQ["n"],
        "phase": phase,
        "role": role,
        "length_target": target,
        "rep": rep,
        "delay_s": delay_s,
        "seed": seed,
        "salt": salt,
        "chars": len(text),
        "prompt_tokens": prompt,
        "cached_tokens": cached,
        "expected_cached": expected,
        "cached_ok": cached == expected,
        "cold_ok": cached == 0,
        "completion_tokens": completion,
        "ttft_ms": round(ttft, 3),
        "wall_ms": round(wall, 3),
        "status": status,
        "gap_ms": None if gap_ms is None else round(gap_ms, 3),
        "ts": round(t0, 3),
    }
    if extra:
        row.update(extra)
    if prompt > 0:
        CPT["v"] = len(text) / prompt
    ROWS.append(row)
    return row


def send_prompt(prompt: tuple[int, str, str], **kw: Any) -> dict[str, Any]:
    seed, salt, text = prompt
    return send(text, seed=seed, salt=salt, **kw)


def predict_chars(target: int) -> int:
    return max(200, int(round(target * CPT["v"])) - corpus.MARKER_CHARS)


# --------------------------------------------------------------------------- #
# Phase 1: length sweep (self-verifying; a wrong length becomes a probe)
# --------------------------------------------------------------------------- #
def acceptable(L: int, target: int) -> bool:
    """Every cell must be hit exactly; the length is the variable under test."""

    return L == target


def run_cell(target: int) -> dict[str, Any]:
    """Five valid cold->repeat trials at one exact length; probes are excluded.

    Length control has two knobs: body chars (coarse, ~3.6 chars/token, a
    staircase because the body is truncated at word boundaries) and a
    one-token-granular tail of repeated ``" the"``.  The body is sized a dozen
    tokens *short* of the target so the tail can always close the gap, which
    makes every target above the body's own count reachable in one or two
    probes.

    The cold request of each trial is also that trial's length check: if the
    achieved ``prompt_tokens`` is not the exact target, the request is logged
    as a *probe*, the knobs are corrected, and the trial is retried.
    """

    chars = max(200, predict_chars(target) - int(round(HEADROOM_TOKENS * CPT["v"])))
    variant = 0
    tail = 0
    cell_L: int | None = None
    trials: list[dict[str, Any]] = []
    probes = 0
    while len(trials) < REPS:
        if not can_send("p1") or probes >= MAX_PROBES_PER_CELL:
            NOTES.append(
                f"cell L={target}: stopped after {len(trials)}/{REPS} trials "
                f"({probes} probes, p1 requests={USED['p1']})"
            )
            break
        prompt = new_prompt(chars, variant, tail)
        cold = send_prompt(prompt, phase="p1", role="cold", target=target,
                           extra={"variant": variant, "tail": tail, "probe": True})
        L = cold.get("prompt_tokens") or 0
        if (cold.get("cached_tokens") or 0) != 0:
            probes += 1
            NOTES.append(f"cell L={target}: cold not cold (cached={cold['cached_tokens']})")
            continue
        if L <= 0:
            probes += 1
            chars += 4
            continue
        if L != target:
            probes += 1
            if cell_L is not None:
                NOTES.append(
                    f"cell L={cell_L}: length drift to {L} at chars={chars} "
                    f"tail={tail}; marker token cost is not constant"
                )
            delta = target - L
            if tail + delta >= 0:
                tail += delta
            else:
                chars = max(200, chars + int(round(delta * CPT["v"])) - 2)
                tail = 0
            if probes >= 3 and tail == 0 and variant < 2 and L != target:
                variant += 1  # re-phase the body staircase if the tail cannot help
            continue
        cell_L = L
        cold["probe"] = False
        rep = len(trials) + 1
        rep1 = send_prompt(prompt, phase="p1", role="rep1", target=target,
                           extra={"rep": rep, "variant": variant, "tail": tail,
                                  "cold_cached": cold.get("cached_tokens")})
        rep2 = None
        if (rep1.get("cached_tokens") or 0) == 0 and can_send("p1"):
            rep2 = send_prompt(prompt, phase="p1", role="rep2", target=target,
                               extra={"rep": rep, "variant": variant, "tail": tail})
        trials.append({"L": L, "cold": cold, "rep1": rep1, "rep2": rep2})
        print(f"  [p1] L={L} rep={rep} cached={rep1.get('cached_tokens')}/"
              f"{rep1.get('expected_cached')} ttft={rep1.get('ttft_ms'):.1f}ms"
              + (f" -> rep2 cached={rep2.get('cached_tokens')}" if rep2 else ""),
              flush=True)
    misses = sum(1 for t in trials if (t["rep1"].get("cached_tokens") or 0) == 0)
    print(f"[p1] cell L={cell_L} (target {target}) chars={chars} variant={variant} "
          f"tail={tail} trials={len(trials)} probes={probes} misses={misses}",
          flush=True)
    return {"target": target, "length": cell_L, "chars": chars, "variant": variant,
            "tail": tail, "trials": len(trials), "probes": probes, "misses": misses}


# --------------------------------------------------------------------------- #
# Phases 2 and 3
# --------------------------------------------------------------------------- #
def plan_delays() -> list[float]:
    """Delay cells that fit the remaining budget (d=0 is p1's immediate repeat)."""

    remaining = MAX_REQUESTS - USED["total"] - RESERVE_P3
    per_cell = 2 * REPS
    k = max(0, remaining // per_cell)
    priority = [d for d in DELAYS if d > 0.0]
    if 0.0 in DELAYS:
        priority.append(0.0)
    planned = sorted(priority[:k])
    shed = [d for d in DELAYS if d not in planned]
    if shed:
        NOTES.append(f"p2 shed delays {shed}: {remaining} requests left < "
                     f"{len(DELAYS) * per_cell} for all cells")
    return planned


def phase2(L: int, chars: int, variant: int = 0, tail: int = 0) -> list[float]:
    done: list[float] = []
    for d in plan_delays():
        if not can_send("p2"):
            break
        ran = 0
        for rep in range(1, REPS + 1):
            if not can_send("p2"):
                break
            prompt = new_prompt(chars, variant, tail)
            cold = send_prompt(prompt, phase="p2", role="cold", target=L, rep=rep,
                               delay_s=d)
            if (cold.get("cached_tokens") or 0) != 0 and can_send("p2"):
                prompt = new_prompt(chars, variant, tail)
                cold = send_prompt(prompt, phase="p2", role="cold", target=L, rep=rep,
                                   delay_s=d, extra={"attempt": 2})
            time.sleep(d)
            send_prompt(prompt, phase="p2", role="rep1", target=L, rep=rep, delay_s=d,
                        extra={"slept_s": d, "cold_cached": cold.get("cached_tokens")})
            ran += 1
        if ran:
            done.append(d)
            print(f"[p2] delay={d}s n={ran} (requests={USED['total']})", flush=True)
    return done


def phase3(L: int, chars: int, variant: int = 0, tail: int = 0) -> int:
    ran = 0
    for rep in range(1, REPS + 1):
        if not can_send("p3"):
            NOTES.append(f"p3 stopped at rep={rep} by the request cap")
            return ran
        prompt = new_prompt(chars, variant, tail)
        cold = send_prompt(prompt, phase="p3", role="cold", target=L, rep=rep)
        if (cold.get("cached_tokens") or 0) != 0 and can_send("p3"):
            prompt = new_prompt(chars, variant, tail)
            cold = send_prompt(prompt, phase="p3", role="cold", target=L, rep=rep,
                               extra={"attempt": 2})
        other = send_prompt(new_prompt(UNRELATED_CHARS), phase="p3", role="unrelated",
                            target=None, rep=rep)
        send_prompt(prompt, phase="p3", role="rep1", target=L, rep=rep,
                    extra={"cold_cached": cold.get("cached_tokens"),
                           "unrelated_tokens": other.get("prompt_tokens")})
        ran += 1
    print(f"[p3] n={ran} (requests={USED['total']})", flush=True)
    return ran


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def offline_check() -> int:
    """No network: marker/prompt invariants only."""

    widths, texts = set(), []
    for _i in range(6):
        _seed, salt, text = new_prompt(3600)
        widths.add(len(text))
        texts.append(text)
    uniq = len(set(texts))
    print(f"offline: marker_chars={corpus.MARKER_CHARS} prompt_chars={sorted(widths)} "
          f"unique_prompts={uniq}/6")
    assert widths == {corpus.MARKER_CHARS + len(corpus.body_for(3600))}
    assert uniq == 6
    print("offline: OK")
    return 0


def write_outputs(stop_reason: str, cells: list[dict[str, Any]]) -> None:
    with open(HERE / "u10_rows.jsonl", "w", encoding="utf-8") as fh:
        for row in ROWS:
            fh.write(json.dumps(row) + "\n")
    runlog = {
        "unit": "U10",
        "seed": SEED,
        "lengths_target": list(LENGTHS),
        "exact_targets": list(EXACT),
        "reps": REPS,
        "delays": list(DELAYS),
        "max_tokens": MAX_TOKENS,
        "requests": USED,
        "max_requests": MAX_REQUESTS,
        "elapsed_s": round(time.time() - STARTED, 3),
        "stop_reason": stop_reason,
        "failures": SEQ["failures"],
        "cells": cells,
        "notes": NOTES,
    }
    with open(HERE / "u10_runlog.json", "w", encoding="utf-8") as fh:
        json.dump(runlog, fh, indent=2)


def run_live() -> int:
    global SEND
    chat = client_mod.ChatClient()
    SEND = functools.partial(
        chat.chat, max_tokens=MAX_TOKENS, thinking=THINKING, stream=True, timeout=180.0
    )
    stop_reason = ""
    cells: list[dict[str, Any]] = []
    try:
        for target in LENGTHS:
            if not can_send("p1"):
                stop_reason = f"p1 request cap ({USED['p1']}) reached"
                NOTES.append(stop_reason)
                break
            cells.append(run_cell(target))
        done = [c for c in cells if c["trials"] > 0]
        if done:
            worst = max(done, key=lambda c: (c["misses"], c["length"] or 0))
            L, chars = worst["length"], worst["chars"]
            variant = worst["variant"]
            tail = worst["tail"]
            print(f"[pick] worst cell L={L} chars={chars} variant={variant} "
                  f"tail={tail} misses={worst['misses']}", flush=True)
            phase2(L, chars, variant, tail)
            phase3(L, chars, variant, tail)
        else:
            stop_reason = "no valid length cell was achieved"
    except StopBatch as exc:
        stop_reason = f"stopped: {exc}"
        NOTES.append(stop_reason)
        print(f"[stop] {exc}", flush=True)
    except Exception as exc:  # noqa: BLE001 - always leave a record
        import traceback

        stop_reason = f"error: {type(exc).__name__}: {exc}"
        NOTES.append(stop_reason)
        traceback.print_exc()
    write_outputs(stop_reason, cells)
    print(f"SUMMARY requests={USED['total']} p1={USED['p1']} p2={USED['p2']} "
          f"p3={USED['p3']} failures={SEQ['failures']} "
          f"elapsed_s={time.time() - STARTED:.1f} stop='{stop_reason}'", flush=True)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true")
    args = ap.parse_args()
    return offline_check() if args.offline else run_live()


if __name__ == "__main__":
    raise SystemExit(main())
