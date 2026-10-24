#!/usr/bin/env python3
"""U9 live driver — is a prompt-cache HIT actually FASTER?

U2 proved the meter is aligned to the 64-token grid.  It did not prove that a
hit is faster.  This driver measures TTFT (first content chunk, single stream)
for a genuinely cold request and for the identical bytes sent immediately
afterwards, at six prompt lengths, with 7 paired repetitions each.

Design (pre-registered before the first live request)
-----------------------------------------------------
* **One variable: cache state.**  Within a repetition the two prompts are byte
  identical; only the server's radix-cache state differs.
* **Cold is forced by a fresh salt** at the very front of message 0, so the
  radix prefix match is 0 by construction.  Every repetition gets its own salt.
* **Order is interleaved.**  Reps 0/2/4/6 are ``A``: cold measured, then warm.
  Reps 1/3/5 are ``B``: one unmeasured prime (cold) seeds the cache, the warm
  request is measured, then a second, fresh-salted *cold* request is measured.
  ``B`` therefore measures the hit BEFORE the miss, which is what lets us say
  whether measurement order biases the ratio.  Each rep yields exactly one
  paired ``(miss, hit)`` delta.
* **Serialised.**  Exactly one request in flight at all times -- the box runs
  ``max_running_requests=5`` and concurrency corrupts TTFT.
* **Lengths are calibrated, not assumed.**  One calibration request fixes
  chars-per-token; every cell's *actual* prompt length is then read back from
  ``usage.prompt_tokens`` and reported, never the target.
* **Never** ``POST /flush_cache``: it would wipe every tenant's radix tree.
  Cold isolation is per-cell salt, full stop.

Write contract: this script writes only inside ``cells/U9/``.

Usage::

    python3 u9_cell.py --offline     # wiring check, zero network
    python3 u9_cell.py               # live sweep
"""

from __future__ import annotations

import argparse
import functools
import importlib.util
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Callable

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
SRC = REPO / "src"
EXP = REPO / "experiments" / "context-cache"
LOCK_PATH = EXP / ".occamy.lock"

sys.path.insert(0, str(SRC))
sys.path.insert(0, str(HERE))

import fcntl  # noqa: E402

import u9_corpus as corpus  # noqa: E402

from resextract.context import make_salt, salted  # noqa: E402


def _load(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:  # pragma: no cover
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


client_mod = _load("u9_client", EXP / "client.py")

# --------------------------------------------------------------------------- #
# Configuration (pre-registered)
# --------------------------------------------------------------------------- #
SEED = 20261020
LENGTHS = corpus.LENGTHS
REPS = 7
ORDER_PATTERN = ("A", "B", "A", "B", "A", "B", "A")

MAX_TOKENS = 1
THINKING = False

MAX_REQUESTS = 200
MAX_SECONDS = 30 * 60
LOCK_TIMEOUT_S = 40 * 60

#: chars/token guess used for the ONE calibration request; overwritten live.
CPT_GUESS = 3.6
#: ``"[cell-" + 16 + "]\n"`` = 24 characters in front of the body.
SALT_CHARS = 24

NOISE_REPEATS = 10
NOISE_HIT_LENGTHS = (1024, 8192)
NOISE_COLD_LENGTH = 1024

OUT_TRIALS = HERE / "u9_trials.jsonl"
OUT_RAW = HERE / "u9_raw_usage.jsonl"
OUT_RUNLOG = HERE / "u9_runlog.json"

# --------------------------------------------------------------------------- #
# Instrumentation
# --------------------------------------------------------------------------- #
CURRENT: dict[str, Any] = {}
RAW_USAGE: list[dict[str, Any]] = []
COUNTS = {
    "requests": 0,
    "failures": 0,
    "consecutive_failures": 0,
    "null_coercions": 0,
    "explicit_details": 0,
}


class StopBatch(RuntimeError):
    """Raised when a hard bound (requests / seconds) is reached."""


def install_usage_probe() -> None:
    """Count null ``prompt_tokens_details`` coercions and keep raw usage.

    ``client.py`` resolved ``normalise_cache`` into its own module globals at
    import time, so patching the module attribute reaches the wire path without
    touching the shared file.
    """

    original = client_mod.normalise_cache

    def probe(usage: Any) -> tuple[int, int]:
        details = usage.get("prompt_tokens_details") if isinstance(usage, dict) else None
        coerced = not isinstance(details, dict)
        COUNTS["null_coercions" if coerced else "explicit_details"] += 1
        RAW_USAGE.append(
            {
                **dict(CURRENT),
                "usage": usage if isinstance(usage, dict) else None,
                "null_coerced": coerced,
            }
        )
        return original(usage)

    client_mod.normalise_cache = probe


def make_send(chat_client: Any, started: float) -> Callable[[list[dict[str, str]]], Any]:
    call = functools.partial(
        chat_client.chat,
        max_tokens=MAX_TOKENS,
        thinking=THINKING,
        stream=True,
        timeout=180.0,
    )

    def send(messages: list[dict[str, str]]) -> Any:
        if COUNTS["requests"] >= MAX_REQUESTS:
            raise StopBatch(f"request cap {MAX_REQUESTS} reached")
        if time.monotonic() - started > MAX_SECONDS:
            raise StopBatch(f"time cap {MAX_SECONDS}s reached")
        try:
            result = call(messages)
        except Exception as exc:
            # A retry of a COLD request would hit the cache, so a retried miss
            # is detectable and rejected downstream (cold_ok == False).
            COUNTS["failures"] += 1
            print(f"  ! request failed ({type(exc).__name__}: {exc}); retrying once",
                  flush=True)
            try:
                result = call(messages)
            except Exception as exc2:
                COUNTS["consecutive_failures"] += 1
                print(f"  !! retry failed ({type(exc2).__name__}: {exc2})", flush=True)
                if COUNTS["consecutive_failures"] >= 3:
                    raise StopBatch(f"3 consecutive failures; last: {exc2!r}") from exc2
                raise
        COUNTS["requests"] += 1
        COUNTS["consecutive_failures"] = 0
        return result

    return send


# --------------------------------------------------------------------------- #
# Lock
# --------------------------------------------------------------------------- #
def acquire_lock(path: Path, timeout_s: float) -> int | None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_RDWR | os.O_CREAT, 0o644)
    deadline = time.monotonic() + timeout_s
    waited = False
    while True:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return fd
        except BlockingIOError:
            if not waited:
                print(f"[lock] {path} busy; queueing (deadline {timeout_s/60:.0f} min)",
                      flush=True)
                waited = True
            if time.monotonic() >= deadline:
                os.close(fd)
                return None
            time.sleep(2.0)


def release_lock(fd: int) -> None:
    try:
        fcntl.flock(fd, fcntl.LOCK_UN)
    finally:
        os.close(fd)


# --------------------------------------------------------------------------- #
# Prompt construction
# --------------------------------------------------------------------------- #
CPT = {"value": CPT_GUESS}
TRIALS: list[dict[str, Any]] = []
SEQ = {"n": 0}


def seed_for(*parts: int) -> int:
    value = SEED & 0xFFFFFFFF
    for part in parts:
        value = (value * 1000003) ^ (int(part) & 0xFFFFFFFF)
    return value & 0x7FFFFFFF


def chars_for_length(target_tokens: int) -> int:
    return max(200, int(target_tokens * CPT["value"]) - SALT_CHARS)


def messages_for(text: str) -> list[dict[str, str]]:
    return [{"role": "user", "content": text}]


def prompt_for(length_target: int, salt_seed: int) -> tuple[str, list[dict[str, str]]]:
    salt = make_salt(salt_seed)
    text = salted(salt, corpus.body_for(chars_for_length(length_target)))
    return salt, messages_for(text)


def record(
    *,
    role: str,
    length_target: int,
    rep: int,
    order: str,
    salt: str,
    attempt: int,
    result: tuple[int, int, int, float, float, int, str],
    started_at: float,
) -> dict[str, Any]:
    prompt, cached, completion, ttft, wall, status, _text = result
    SEQ["n"] += 1
    #: U2's law, refined at the block boundary: a prompt that ends exactly on
    #: a 64-token checkpoint reuses one block less (measured: L=1024 ->
    #: cached=960, where 64*(L//64) would predict 1024).  Equivalent to
    #: 64*floor(L/64) for every L that is not a multiple of 64.
    expected = 64 * ((prompt - 1) // 64)
    rec = {
        "unit": "U9",
        "seq": SEQ["n"],
        "role": role,
        "length_target": length_target,
        "rep": rep,
        "order": order,
        "salt": salt,
        "attempt": attempt,
        "prompt_tokens": prompt,
        "cached_tokens": cached,
        "completion_tokens": completion,
        "ttft_ms": round(ttft, 3),
        "wall_ms": round(wall, 3),
        "status": status,
        "expected_cached": expected,
        "expected_uncached": prompt - expected,
        "cached_ok": cached == expected,
        "cold_ok": cached == 0,
        "ts": round(started_at, 3),
    }
    TRIALS.append(rec)
    return rec


def request(
    messages: list[dict[str, str]],
    *,
    role: str,
    length_target: int,
    rep: int,
    order: str,
    salt: str,
    attempt: int,
) -> dict[str, Any]:
    t0 = time.time()
    result = SEND(messages)
    return record(
        role=role,
        length_target=length_target,
        rep=rep,
        order=order,
        salt=salt,
        attempt=attempt,
        result=result,
        started_at=t0,
    )


def cold_trial(
    messages: list[dict[str, str]],
    salt: str,
    *,
    length_target: int,
    rep: int,
    order: str,
    slot: int,
) -> tuple[dict[str, Any], list[dict[str, str]], str]:
    """A genuinely cold request; one fresh-salt retry if it was not cold.

    Returns the record **and the exact bytes actually used**, so the following
    hit trial can never send a different prompt than the one just cached.
    """

    rec = request(
        messages, role="miss", length_target=length_target, rep=rep, order=order,
        salt=salt, attempt=1,
    )
    used_messages, used_salt = messages, salt
    if not rec["cold_ok"]:
        print(f"    ! cold contaminated (cached={rec['cached_tokens']}); fresh salt",
              flush=True)
        used_salt, used_messages = prompt_for(
            length_target, seed_for(length_target, rep, slot, 2)
        )
        rec = request(
            used_messages, role="miss", length_target=length_target, rep=rep,
            order=order, salt=used_salt, attempt=2,
        )
    return rec, used_messages, used_salt


def hit_trial(
    messages: list[dict[str, str]],
    *,
    length_target: int,
    rep: int,
    order: str,
    salt: str,
) -> dict[str, Any]:
    rec = request(
        messages, role="hit", length_target=length_target, rep=rep, order=order,
        salt=salt, attempt=1,
    )
    if not rec["cached_ok"]:
        print(f"    ! hit incomplete (cached={rec['cached_tokens']} "
              f"expected={rec['expected_cached']}); resending identical bytes",
              flush=True)
        rec = request(
            messages, role="hit", length_target=length_target, rep=rep,
            order=order, salt=salt, attempt=2,
        )
    return rec


# --------------------------------------------------------------------------- #
# Batch
# --------------------------------------------------------------------------- #
SEND: Callable[[list[dict[str, str]]], Any] = lambda _m: (0, 0, 0, 0.0, 0.0, 200, "")


def calibrate() -> dict[str, Any]:
    """One request fixes chars-per-token; excluded from the statistics."""

    global CPT
    salt, messages = prompt_for(1024, seed_for(1024, 999, 0, 7))
    rec = request(
        messages, role="calibration", length_target=1024, rep=-1, order="-",
        salt=salt, attempt=1,
    )
    chars = len(messages[0]["content"])
    if rec["prompt_tokens"] > 0:
        CPT["value"] = chars / rec["prompt_tokens"]
    print(f"[calib] chars={chars} prompt_tokens={rec['prompt_tokens']} "
          f"cpt={CPT['value']:.4f}", flush=True)
    return rec


def run_length(length_target: int, *, skip_reps: set[int] | None = None) -> None:
    skip_reps = skip_reps or set()
    for rep in range(REPS):
        if rep in skip_reps:
            continue
        order = ORDER_PATTERN[rep % len(ORDER_PATTERN)]
        if order == "A":
            salt, messages = prompt_for(
                length_target, seed_for(length_target, rep, 0, 1)
            )
            miss, messages, salt = cold_trial(
                messages, salt, length_target=length_target, rep=rep, order=order,
                slot=0,
            )
            hit = hit_trial(
                messages, length_target=length_target, rep=rep, order=order, salt=salt
            )
        else:
            salt, messages = prompt_for(
                length_target, seed_for(length_target, rep, 1, 1)
            )
            prime = request(
                messages, role="prime", length_target=length_target, rep=rep,
                order=order, salt=salt, attempt=1,
            )
            if not prime["cold_ok"]:
                print(f"    ! prime not cold (cached={prime['cached_tokens']})",
                      flush=True)
            hit = hit_trial(
                messages, length_target=length_target, rep=rep, order=order, salt=salt
            )
            fresh_salt = seed_for(length_target, rep, 2, 1)
            miss, _m2, _s2 = cold_trial(
                prompt_for(length_target, fresh_salt)[1],
                make_salt(fresh_salt),
                length_target=length_target,
                rep=rep,
                order=order,
                slot=2,
            )
        delta = miss["ttft_ms"] - hit["ttft_ms"]
        flag = "" if (miss["cold_ok"] and hit["cached_ok"]) else " [INVALID]"
        print(
            f"  L~{length_target:5d} rep{rep} {order} "
            f"miss={miss['prompt_tokens']}tok {miss['ttft_ms']:8.2f}ms "
            f"hit={hit['cached_tokens']}/{hit['prompt_tokens']} "
            f"{hit['ttft_ms']:8.2f}ms  d={delta:8.2f}ms{flag}",
            flush=True,
        )


def noise_block_hit(length_target: int, messages: list[dict[str, str]]) -> None:
    for i in range(NOISE_REPEATS):
        rec = request(
            messages, role="noise_hit", length_target=length_target, rep=i,
            order="N", salt="-", attempt=1,
        )
        print(
            f"  noise-hit L~{length_target} {i+1}/{NOISE_REPEATS} "
            f"{rec['ttft_ms']:8.2f}ms cached={rec['cached_tokens']}/"
            f"{rec['prompt_tokens']} ok={rec['cached_ok']}",
            flush=True,
        )


def noise_block_cold(length_target: int) -> None:
    for i in range(NOISE_REPEATS):
        salt, messages = prompt_for(length_target, seed_for(length_target, 8888, i, 3))
        rec = request(
            messages, role="noise_cold", length_target=length_target, rep=i,
            order="N", salt=salt, attempt=1,
        )
        print(
            f"  noise-cold L~{length_target} {i+1}/{NOISE_REPEATS} "
            f"{rec['ttft_ms']:8.2f}ms cold_ok={rec['cold_ok']}",
            flush=True,
        )


def main(argv: list[str] | None = None) -> int:
    global SEND, REPS
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offline", action="store_true", help="no network at all")
    parser.add_argument("--lengths", default="", help="comma list override (debug)")
    parser.add_argument("--reps", type=int, default=0, help="rep override (debug)")
    parser.add_argument("--no-noise", action="store_true", help="skip noise blocks")
    args = parser.parse_args(argv)

    lengths = [int(x) for x in args.lengths.split(",") if x.strip()] or list(LENGTHS)
    REPS = args.reps or REPS

    started_wall = time.time()
    started = time.monotonic()
    runlog: dict[str, Any] = {
        "unit": "U9",
        "seed": SEED,
        "lengths": lengths,
        "reps": REPS,
        "order_pattern": list(ORDER_PATTERN),
        "max_tokens": MAX_TOKENS,
        "thinking": THINKING,
        "max_requests": MAX_REQUESTS,
        "max_seconds": MAX_SECONDS,
        "mode": "offline" if args.offline else "live",
        "lock_wait_s": 0.0,
        "stop_reason": "",
        "cpt": None,
    }

    if args.offline:
        def fake(_messages: list[dict[str, str]]) -> Any:
            COUNTS["requests"] += 1
            return (1000, 960, 1, 10.0, 12.0, 200, "")
        SEND = fake
        install_usage_probe()
    else:
        chat_client = client_mod.ChatClient()
        install_usage_probe()
        SEND = make_send(chat_client, started)

    lock_fd: int | None = None
    status = "done"
    if not args.offline:
        t0 = time.monotonic()
        lock_fd = acquire_lock(LOCK_PATH, LOCK_TIMEOUT_S)
        runlog["lock_wait_s"] = round(time.monotonic() - t0, 3)
        if lock_fd is None:
            runlog["stop_reason"] = "blocked: lock not acquired within 40 min"
            runlog["status"] = "blocked"
            OUT_RUNLOG.write_text(json.dumps(runlog, indent=2, sort_keys=True) + "\n")
            print(json.dumps({"status": "blocked", "reason": runlog["stop_reason"]}))
            return 3
        print(f"[lock] acquired after {runlog['lock_wait_s']:.2f}s", flush=True)

    warm_cache: dict[int, list[dict[str, str]]] = {}
    try:
        if not args.offline:
            calibrate()
            runlog["cpt"] = round(CPT["value"], 6)

        for length_target in lengths:
            print(f"[length] target={length_target} "
                  f"chars={chars_for_length(length_target)} "
                  f"reqs={COUNTS['requests']}", flush=True)
            before = len(TRIALS)
            run_length(length_target)
            if not args.no_noise and length_target in NOISE_HIT_LENGTHS:
                salt, messages = prompt_for(
                    length_target, seed_for(length_target, 5555, 0, 4)
                )
                cold = request(
                    messages, role="prime", length_target=length_target, rep=-2,
                    order="N", salt=salt, attempt=1,
                )
                print(f"  noise seed prompt {cold['prompt_tokens']}tok "
                      f"cached={cold['cached_tokens']}", flush=True)
                noise_block_hit(length_target, messages)
                if length_target == NOISE_COLD_LENGTH:
                    noise_block_cold(length_target)
            print(f"  -> {len(TRIALS) - before} trials, "
                  f"{COUNTS['requests']} requests so far", flush=True)
    except StopBatch as exc:
        status = "partial"
        runlog["stop_reason"] = str(exc)
        print(f"STOP: {exc}", flush=True)
    finally:
        if lock_fd is not None:
            release_lock(lock_fd)
        runlog["requests"] = COUNTS["requests"]
        runlog["failures"] = COUNTS["failures"]
        runlog["null_coercions"] = COUNTS["null_coercions"]
        runlog["explicit_details"] = COUNTS["explicit_details"]
        runlog["elapsed_s"] = round(time.monotonic() - started, 3)
        runlog["wall_started"] = time.strftime(
            "%Y-%m-%dT%H:%M:%S%z", time.localtime(started_wall)
        )
        runlog["status"] = status
        runlog["trials"] = len(TRIALS)
        with OUT_TRIALS.open("w", encoding="utf-8") as fh:
            for rec in TRIALS:
                fh.write(json.dumps(rec, sort_keys=True) + "\n")
        with OUT_RAW.open("w", encoding="utf-8") as fh:
            for rec in RAW_USAGE:
                fh.write(json.dumps(rec, sort_keys=True) + "\n")
        OUT_RUNLOG.write_text(json.dumps(runlog, indent=2, sort_keys=True) + "\n")
        print(json.dumps({k: runlog[k] for k in
                          ("status", "requests", "elapsed_s", "stop_reason")},
                         sort_keys=True))
    return 0 if status == "done" else 2


if __name__ == "__main__":
    raise SystemExit(main())
