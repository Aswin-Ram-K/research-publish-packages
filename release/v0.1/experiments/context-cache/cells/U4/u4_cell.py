#!/usr/bin/env python3
"""U4 live driver — compaction break-cost measurement.

Design (revised by the orchestrator's correction, applied BEFORE any live
measurement: this file is the first version that ever issued a request).

* **One renderer for every arm.**  ``RenderPolicy.NAIVE_APPEND`` -- an
  append-only transcript.  The newest message is a stable node text and
  ``volatile={}`` on every turn, so a new turn can never rewrite an earlier
  message.  The **only** variable is the compaction policy.
* **Append-only is verified, not assumed**: ``u4_analyze.py`` replays the same
  chains offline and asserts the rendered prefix is a byte-prefix extension of
  the previous turn on every non-compaction turn.  (The earlier
  "volatile on the last message" renderer bug would have failed that check.)
* **reps = 1, deliberately.**  ``break_cost`` is only observable on the FIRST
  sight of the post-compaction bytes: a second repetition would re-send a
  prompt the server has already cached verbatim and report ~0, which measures
  memoisation, not the break.  The freed budget buys a third session instead.
* **Cold isolation** is a per-cell salt at the very front of message 0.  Note
  a real gap in the shared code: ``render(NAIVE_APPEND)`` never applies the
  salt (only POINTER / NAIVE_MUTABLE do), so U4 salts the *Case preamble*
  itself for this renderer.  Without that, the three compaction-policy cells of
  one session would share message 0 bytes and contaminate each other.

Write contract: this script writes only inside ``cells/U4/``.
"""

from __future__ import annotations

import argparse
import fcntl
import functools
import hashlib
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


def _load(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:  # pragma: no cover
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


from resextract.context import (  # noqa: E402
    CacheMeter,
    CompactionPolicy,
    RenderPolicy,
    StateNode,
    canonical_bytes,
    default_est_tokens,
    make_salt,
)

runner = _load("u4_runner", EXP / "runner.py")
client_mod = _load("u4_client", EXP / "client.py")

# --------------------------------------------------------------------------- #
# Configuration (pre-registered)
# --------------------------------------------------------------------------- #
SEED = 20261020
TURNS = 44
BUDGET_TOKENS = 8000
KEEP_LAST = 2
MAX_TOKENS = 4
REPS = 1

RENDER = RenderPolicy.NAIVE_APPEND  # the single renderer for every arm
POLICIES = (
    CompactionPolicy.SUMMARISE_IN_PLACE,
    CompactionPolicy.SLIDING_WINDOW,
    CompactionPolicy.FORK,
)
CORPUS_SESSIONS = ("u4-s1", "u4-s2", "u4-s3")
CONTROL_SESSIONS = ("u4-s1", "u4-s2", "u4-s3")
CONTROL_TURNS = 14

MAX_REQUESTS = 600
MAX_SECONDS = 60 * 60
LOCK_TIMEOUT_S = 40 * 60

OUT_ROWS = HERE / "u4_rows.jsonl"
OUT_EVENTS = HERE / "u4_events.jsonl"
OUT_USAGE = HERE / "u4_usage_raw.jsonl"
OUT_RUNLOG = HERE / "u4_runlog.json"
CORPUS = HERE / "u4_sessions.json"


# --------------------------------------------------------------------------- #
# Corpus -> Cases / Cells
# --------------------------------------------------------------------------- #
def load_corpus() -> dict[str, Any]:
    if not CORPUS.exists():
        raise SystemExit(f"missing corpus {CORPUS}; run u4_corpus.py first")
    return json.loads(CORPUS.read_text(encoding="utf-8"))


def cell_salt(arm: str, compaction: str, session: str) -> str:
    """Distinct salt per (arm, compaction policy, session) -- cold isolation."""

    key = f"U4:v1:{SEED}:{arm}:{compaction}:{session}"
    seed = int(hashlib.sha256(key.encode("utf-8")).hexdigest()[:12], 16)
    return make_salt(seed)


def build_units(corpus: dict[str, Any]) -> list[dict[str, Any]]:
    """Return one dict per cell: {cell, case, compaction}.  Deterministic."""

    by_id = {s["case_id"]: s for s in corpus["sessions"]}
    units: list[dict[str, Any]] = []
    specs: list[tuple[str, str, str, int, int]] = []
    for session in CORPUS_SESSIONS:
        for policy in POLICIES:
            specs.append(("append", policy.value, session, TURNS, BUDGET_TOKENS))
    for session in CONTROL_SESSIONS:
        # No-compaction control: the 64-grid law on a purely growing prompt.
        specs.append(("append", "none", session, CONTROL_TURNS, 10**9))

    for arm, compaction, session, turns, budget in specs:
        salt = cell_salt(arm, compaction, session)
        # The renderer applies the salt to message 0 (``salted(salt, ...)``).
        # ``preflight()`` asserts that it really does before any request goes
        # out: an earlier revision of ``render`` skipped the salt for
        # NAIVE_APPEND, which would have let one cell serve another's prefix.
        preamble = by_id[session]["preamble"]
        case_id = f"U4/{arm}/{compaction}/{session}"
        turns_data = tuple(
            runner.Turn(text=t["text"], volatile={})
            for t in by_id[session]["turns"][:turns]
        )
        case = runner.Case(case_id=case_id, preamble=preamble, turns=turns_data)
        cell = runner.Cell(
            cell=case_id,
            arm=arm,
            policy=RENDER.value,
            case_id=case_id,
            depth=turns,
            reps=REPS,
            salt=salt,
            budget_tokens=budget,
            keep_last=KEEP_LAST,
        )
        units.append(
            {
                "cell": cell,
                "case": case,
                "compaction": compaction,
                "session": session,
                "arm": arm,
                "budget_tokens": budget,
            }
        )
    return units


# --------------------------------------------------------------------------- #
# Pre-flight: the two properties the measurement rests on
# --------------------------------------------------------------------------- #
PREAMBLE_FILES = ("nodes.py", "render.py", "budget.py", "meter.py", "salt.py")


def source_pins() -> dict[str, Any]:
    """sha256 + mtime of every shared module this measurement depends on."""

    pins: dict[str, Any] = {}
    base = SRC / "resextract" / "context"
    for name in PREAMBLE_FILES:
        path = base / name
        blob = path.read_bytes()
        pins[name] = {
            "sha256": hashlib.sha256(blob).hexdigest(),
            "bytes": len(blob),
            "mtime": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(path.stat().st_mtime)),
        }
    return pins


def preflight(units: list[dict[str, Any]], *, verbose: bool = True) -> dict[str, Any]:
    """Abort-before-spend checks on the *live* renderer.

    (1) Cold isolation: every cell's message 0 must be a distinct byte string.
        ``render`` must apply the per-cell salt; if it silently skips it for
        the renderer in use, cells of the same session would share a radix
        prefix and the whole batch would be contaminated.
    (2) Append-only: adding a turn must leave every previously emitted message
        byte-identical (the message list grows by one, nothing is rewritten).
    """

    from resextract.context import render

    problems: list[str] = []
    seen: dict[str, str] = {}
    for unit in units:
        chain = [StateNode.create(unit["case"].preamble, "invariant")]
        msgs = render(
            RENDER,
            chain,
            preamble=unit["case"].preamble,
            volatile={},
            salt=unit["cell"].salt,
        )
        head = hashlib.sha256(canonical_bytes(msgs[0])).hexdigest()
        if head in seen:
            problems.append(
                f"cold-isolation collision: {unit['cell'].cell} shares message 0 "
                f"with {seen[head]}"
            )
        seen[head] = unit["cell"].cell

    probe = units[0]
    chain = [StateNode.create(probe["case"].preamble, "invariant")]
    previous: list[dict[str, str]] | None = None
    for turn in range(1, 5):
        chain = chain + [
            StateNode.create(f"preflight turn {turn} body", "delta", parent=chain[-1], turn=turn)
        ]
        msgs = render(
            RENDER,
            chain,
            preamble=probe["case"].preamble,
            volatile={},
            salt=probe["cell"].salt,
        )
        if previous is not None:
            if len(msgs) != len(previous) + 1:
                problems.append(
                    f"append-only: turn {turn} produced {len(msgs)} messages, "
                    f"expected {len(previous) + 1}"
                )
            for i, old in enumerate(previous):
                if msgs[i] != old:
                    problems.append(
                        f"append-only: turn {turn} rewrote message {i} "
                        f"({len(old['content'])} -> {len(msgs[i]['content'])} chars)"
                    )
        previous = msgs

    report = {
        "cells": len(units),
        "distinct_message0": len(seen),
        "append_only_ok": not any(p.startswith("append-only") for p in problems),
        "cold_isolation_ok": not any(p.startswith("cold-isolation") for p in problems),
        "problems": problems,
    }
    if verbose:
        print(f"[preflight] {json.dumps(report, sort_keys=True)}", flush=True)
    if problems:
        raise SystemExit(
            "PRE-FLIGHT FAILED -- no request was sent:\n  " + "\n  ".join(problems)
        )
    return report


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
    """Wrap ``client.normalise_cache`` to count null coercions + keep raw usage.

    ``client.py`` resolved ``normalise_cache`` into its own module globals at
    import time, so patching the module attribute is picked up by
    ``_stream_once`` / ``_once`` without touching the shared file.
    """

    original = client_mod.normalise_cache

    def probe(usage: Any) -> tuple[int, int]:
        ctx = dict(CURRENT)
        details = usage.get("prompt_tokens_details") if isinstance(usage, dict) else None
        coerced = not isinstance(details, dict)
        if coerced:
            COUNTS["null_coercions"] += 1
        else:
            COUNTS["explicit_details"] += 1
        RAW_USAGE.append(
            {
                **ctx,
                "usage": usage if isinstance(usage, dict) else None,
                "null_coerced": coerced,
                "prompt_tokens_details": details,
            }
        )
        return original(usage)

    client_mod.normalise_cache = probe


def make_send(chat_client: Any, started: float) -> Callable[[list[dict[str, str]]], Any]:
    call = functools.partial(
        chat_client.chat,
        max_tokens=MAX_TOKENS,
        thinking=False,
        stream=True,
        timeout=120.0,
    )

    def send(messages: list[dict[str, str]]) -> Any:
        if COUNTS["requests"] >= MAX_REQUESTS:
            raise StopBatch(f"request cap {MAX_REQUESTS} reached")
        if time.monotonic() - started > MAX_SECONDS:
            raise StopBatch(f"time cap {MAX_SECONDS}s reached")
        try:
            result = call(messages)
        except Exception as exc:  # retry once, per the unit contract
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
    """Blocking-with-deadline ``flock``.  Returns the held fd, or None."""

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
# Main
# --------------------------------------------------------------------------- #
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--smoke", action="store_true", help="3-turn wiring probe")
    parser.add_argument("--offline", action="store_true", help="no network at all")
    parser.add_argument("--max-units", type=int, default=0, help="debug: stop early")
    args = parser.parse_args(argv)

    corpus = load_corpus()
    units = build_units(corpus)
    if args.max_units:
        units = units[: args.max_units]
    if args.smoke:
        # 3-turn wiring probe on its OWN salt, so it cannot warm the real
        # cells' prefix (turn 1 of every real cell must miss).
        base = units[0]
        smoke_case = runner.Case(
            case_id="U4/smoke/probe",
            preamble=base["case"].preamble,
            turns=base["case"].turns[:3],
        )
        smoke_cell = runner.Cell(
            cell="U4/smoke/probe",
            arm="append",
            policy=RENDER.value,
            case_id="U4/smoke/probe",
            depth=3,
            reps=1,
            salt=cell_salt("append", "smoke", base["session"] + os.environ.get("U4_SMOKE_TAG", "")),
            budget_tokens=10**9,
            keep_last=KEEP_LAST,
        )
        units = [
            dict(
                base,
                cell=smoke_cell,
                case=smoke_case,
                compaction="none",
                budget_tokens=10**9,
            )
        ]

    started_wall = time.time()
    started = time.monotonic()
    meter = CacheMeter()
    events: list[dict[str, Any]] = []
    pins = source_pins()
    runlog: dict[str, Any] = {
        "unit": "U4",
        "renderer": RENDER.value,
        "volatile": "{} on every turn (baked snapshot never re-rendered)",
        "seed": SEED,
        "budget_tokens": BUDGET_TOKENS,
        "keep_last": KEEP_LAST,
        "reps": REPS,
        "max_tokens": MAX_TOKENS,
        "corpus_sha256": corpus.get("payload_sha256"),
        "cells_planned": [u["cell"].cell for u in units],
        "mode": "offline" if args.offline else ("smoke" if args.smoke else "live"),
        "source_pins_before": pins,
        "lock_wait_s": 0.0,
        "stop_reason": "",
    }

    # Never spend a request before the two invariants are checked on the LIVE
    # renderer (another unit is editing src/resextract/context/ concurrently).
    runlog["preflight"] = preflight(units)


    if args.offline:
        def send(_messages: list[dict[str, str]]) -> Any:
            COUNTS["requests"] += 1
            return (0, 0, 0, 0.0, 0.0, 200, "")
    else:
        chat_client = client_mod.ChatClient()
        install_usage_probe()
        send = make_send(chat_client, started)

    lock_fd: int | None = None
    if not args.offline:
        t0 = time.monotonic()
        lock_fd = acquire_lock(LOCK_PATH, LOCK_TIMEOUT_S)
        runlog["lock_wait_s"] = round(time.monotonic() - t0, 3)
        if lock_fd is None:
            runlog["stop_reason"] = "blocked: lock not acquired within 40 min"
            OUT_RUNLOG.write_text(json.dumps(runlog, indent=2, sort_keys=True) + "\n")
            print(json.dumps({"status": "blocked", "reason": runlog["stop_reason"]}))
            return 3

    results: list[Any] = []
    status = "done"
    try:
        for idx, unit in enumerate(units, 1):
            cell = unit["cell"]
            pct = int((idx - 1) * 100 / max(1, len(units)))
            print(
                f"[{pct}%] [{idx}/{len(units)}] {cell.cell} depth={cell.depth} "
                f"budget={unit['budget_tokens']} reqs={COUNTS['requests']}",
                flush=True,
            )
            CURRENT.update(
                {
                    "cell": cell.cell,
                    "policy": unit["compaction"],
                    "arm": unit["arm"],
                    "session": unit["session"],
                }
            )
            try:
                result = runner.run_cell(
                    cell,
                    unit["case"],
                    send,
                    meter,
                    compaction=unit["compaction"],
                    summarizer=runner._truncating_summarizer,
                    est_tokens=default_est_tokens,
                )
            except StopBatch as exc:
                status = "partial"
                runlog["stop_reason"] = str(exc)
                print(f"  STOP: {exc}", flush=True)
                break
            results.append(result)
            for event in result.events:
                events.append(
                    {
                        **event,
                        "cell": cell.cell,
                        "session": unit["session"],
                        "compaction": unit["compaction"],
                        "arm": unit["arm"],
                        "budget_tokens": unit["budget_tokens"],
                    }
                )
            runlog.setdefault("cells", []).append(
                {
                    "cell": cell.cell,
                    "session": unit["session"],
                    "compaction": unit["compaction"],
                    "rows": len(result.rows),
                    "events": len(result.events),
                    "evicted": result.evicted,
                    "event_turns": [e["turn"] for e in result.events],
                }
            )
            print(
                f"    -> rows={len(result.rows)} events={len(result.events)} "
                f"evicted={result.evicted} turns={[e['turn'] for e in result.events]}",
                flush=True,
            )
    finally:
        if lock_fd is not None:
            release_lock(lock_fd)
        runlog["source_pins_after"] = source_pins()
        runlog["source_changed_during_batch"] = [
            name
            for name, info in runlog["source_pins_after"].items()
            if pins.get(name, {}).get("sha256") != info["sha256"]
        ]
        runlog["requests"] = COUNTS["requests"]
        runlog["failures"] = COUNTS["failures"]
        runlog["null_coercions"] = COUNTS["null_coercions"]
        runlog["explicit_details"] = COUNTS["explicit_details"]
        runlog["elapsed_s"] = round(time.monotonic() - started, 3)
        runlog["wall_started"] = time.strftime(
            "%Y-%m-%dT%H:%M:%S%z", time.localtime(started_wall)
        )
        runlog["status"] = status

        if not args.offline:
            meter.to_jsonl(OUT_ROWS)
            with OUT_EVENTS.open("w", encoding="utf-8") as fh:
                for event in events:
                    fh.write(json.dumps(event, sort_keys=True) + "\n")
            with OUT_USAGE.open("w", encoding="utf-8") as fh:
                for rec in RAW_USAGE:
                    fh.write(json.dumps(rec, sort_keys=True) + "\n")
        else:
            with (HERE / "u4_events_offline.jsonl").open("w", encoding="utf-8") as fh:
                for event in events:
                    fh.write(json.dumps(event, sort_keys=True) + "\n")
        OUT_RUNLOG.write_text(json.dumps(runlog, indent=2, sort_keys=True) + "\n")

    print(
        json.dumps(
            {
                "status": status,
                "requests": COUNTS["requests"],
                "rows": len(meter.rows()),
                "events": len(events),
                "elapsed_s": runlog["elapsed_s"],
                "lock_wait_s": runlog["lock_wait_s"],
                "null_coercions": COUNTS["null_coercions"],
                "stop_reason": runlog["stop_reason"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
