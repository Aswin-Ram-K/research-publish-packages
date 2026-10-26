#!/usr/bin/env python3
"""E1 live driver — paired break cost of FORK vs SUMMARISE_IN_PLACE (GAPS G1).

Re-runs U4's matched-pair design under the **post-U13** library:

* arm ``F`` = ``CompactionPolicy.FORK`` rendered by ``RenderPolicy.POINTER_FORK``
  (fork root carries the ``[fork] ...`` content-addressed marker; the invariant
  preamble labels the chain root);
* arm ``R`` = ``CompactionPolicy.SUMMARISE_IN_PLACE`` rendered by
  ``RenderPolicy.POINTER`` (same bodies, no marker, no label).

U4's defect is that both arms ran ``NAIVE_APPEND`` over a marker-less fork
chain, so they were the same prompt.  Here the two arms are asserted distinct
at/after the event and identical before it, offline, before any request.

Request economy: the pre-fork turns are byte-identical across arms (nothing has
been forked yet), so one request serves both and is recorded as one row per
arm with ``shared_request: true``.  That is what keeps the design inside the
hard 200-request cap: 11 shared + 2 x 27 = 65 per session, 195 total.

Writes only inside ``cells/E1/``.  The lock record is the only write elsewhere
(``experiments/context-cache/.occamy.lock``, as every unit since U4 has done).
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
from typing import Any

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
    CompactionPolicy,
    RenderPolicy,
    StateNode,
    canonical_bytes,
    compact,
    default_est_tokens,
    make_salt,
    needs_compaction,
    render,
)

runner = _load("e1_runner", EXP / "runner.py")
client_mod = _load("e1_client", EXP / "client.py")

# --------------------------------------------------------------------------- #
# Pre-registered configuration
# --------------------------------------------------------------------------- #
SEED = 20261020
DEPTH = 38            # U4 used 44; 38 is the largest symmetric depth inside 200 requests
BUDGET_TOKENS = 8000  # same as U4
KEEP_LAST = 2         # same as U4
MAX_TOKENS = 4        # same as U4
REPS = 1              # first sight of the post-compaction bytes only
SESSIONS = ("u4-s1", "u4-s2", "u4-s3")

ARMS: dict[str, tuple[CompactionPolicy, RenderPolicy]] = {
    "F": (CompactionPolicy.FORK, RenderPolicy.POINTER_FORK),
    "R": (CompactionPolicy.SUMMARISE_IN_PLACE, RenderPolicy.POINTER),
}
ARM_LABEL = {"F": "fork", "R": "summarise_in_place"}

MAX_REQUESTS = 200
MAX_SECONDS = 45 * 60
LOCK_TIMEOUT_S = 1800

CORPUS = EXP / "cells" / "U4" / "u4_sessions.json"
OUT_ROWS = HERE / "e1_rows.jsonl"
OUT_EVENTS = HERE / "e1_events.jsonl"
OUT_RUNLOG = HERE / "e1_runlog.json"
OUT_PLAN = HERE / "e1_plan.json"


def session_salt(session: str) -> str:
    """Per-*session* salt (not per arm): keeps the pre-fork turns identical."""

    key = f"E1:v1:{SEED}:{session}"
    return make_salt(int(hashlib.sha256(key.encode("utf-8")).hexdigest()[:12], 16))


def sha(messages: list[dict[str, str]]) -> str:
    return hashlib.sha256(canonical_bytes(messages)).hexdigest()


def first_diff(a: bytes, b: bytes) -> int | None:
    if a == b:
        return None
    limit = min(len(a), len(b))
    for i in range(limit):
        if a[i] != b[i]:
            return i
    return limit


# --------------------------------------------------------------------------- #
# Offline plan: the exact prompt stream both arms would send, no network
# --------------------------------------------------------------------------- #
def build_plan(sessions: tuple[str, ...] = SESSIONS) -> dict[str, Any]:
    corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
    by_id = {s["case_id"]: s for s in corpus["sessions"]}
    plan: dict[str, Any] = {
        "unit": "E1",
        "seed": SEED,
        "depth": DEPTH,
        "budget_tokens": BUDGET_TOKENS,
        "keep_last": KEEP_LAST,
        "max_tokens": MAX_TOKENS,
        "corpus": str(CORPUS.relative_to(REPO)),
        "corpus_sha256": hashlib.sha256(CORPUS.read_bytes()).hexdigest(),
        "arms": {a: {"compaction": p.value, "renderer": r.value} for a, (p, r) in ARMS.items()},
        "sessions": {},
    }
    total_requests = 0
    for session in sessions:
        case = by_id[session]
        preamble = case["preamble"]
        salt = session_salt(session)
        chains: dict[str, list[StateNode]] = {
            a: [StateNode.create(preamble, "invariant")] for a in ARMS
        }
        turns: list[dict[str, Any]] = []
        events: dict[str, list[dict[str, Any]]] = {"F": [], "R": []}
        for turn_no in range(1, DEPTH + 1):
            text = case["turns"][turn_no - 1]["text"]
            entry: dict[str, Any] = {"turn": turn_no, "arms": {}}
            for arm in ("F", "R"):
                chain = chains[arm]
                chain = chain + [
                    StateNode.create(text, "delta", parent=chain[-1], turn=turn_no)
                ]
                if needs_compaction(chain, budget_tokens=BUDGET_TOKENS, est_tokens=default_est_tokens):
                    chain, event = compact(
                        chain,
                        ARMS[arm][0],
                        keep_last=KEEP_LAST,
                        summarizer=runner._truncating_summarizer,
                        est_tokens=default_est_tokens,
                    )
                    events[arm].append({**event, "turn": turn_no, "arm": arm})
                chains[arm] = chain
                messages = render(
                    ARMS[arm][1], chain, preamble=preamble, volatile={}, salt=salt
                )
                entry["arms"][arm] = {
                    "messages": messages,
                    "prompt_sha256": sha(messages),
                    "bytes": len(canonical_bytes(messages)),
                    "est_tokens": sum(default_est_tokens(n.text) for n in chain),
                    "node_ids": [{"kind": n.kind, "id": n.node_id} for n in chain],
                    "fork_marker_present": any(n.text.startswith("[fork] ") for n in chain),
                    "fork_marker_line": next(
                        (n.text.split("\n", 1)[0] for n in chain if n.text.startswith("[fork] ")),
                        None,
                    ),
                    "preamble_label_present": bool(
                        ARMS[arm][1] is RenderPolicy.POINTER_FORK and chain[0].kind == "fork"
                    ),
                    "is_event": bool(events[arm]) and events[arm][-1]["turn"] == turn_no,
                    "event_index": next(
                        (i + 1 for i, e in enumerate(events[arm]) if e["turn"] == turn_no),
                        None,
                    ),
                    "chain": chain,
                }
            f, r = entry["arms"]["F"], entry["arms"]["R"]
            offset = first_diff(canonical_bytes(f["messages"]), canonical_bytes(r["messages"]))
            entry["shared"] = offset is None
            entry["first_diff_offset"] = offset
            for arm, other in (("F", "R"), ("R", "F")):
                entry["arms"][arm]["diff_offset_vs_other_arm"] = first_diff(
                    canonical_bytes(entry["arms"][arm]["messages"]),
                    canonical_bytes(entry["arms"][other]["messages"]),
                )
            total_requests += 1 if entry["shared"] else 2
            turns.append(entry)
        first_event = min([e["turn"] for e in events["F"]] or [10**9])
        plan["sessions"][session] = {
            "salt": salt,
            "preamble": preamble,
            "turns": turns,
            "events": events,
            "event_turns": {a: [e["turn"] for e in events[a]] for a in ARMS},
            "first_event_turn": first_event,
            "requests": sum(1 for e in turns if e["shared"]) + 2 * sum(
                1 for e in turns if not e["shared"]
            ),
        }
    plan["planned_requests"] = total_requests
    plan["preflight"] = preflight(plan)
    return plan


def preflight(plan: dict[str, Any]) -> dict[str, Any]:
    """The two facts the measurement rests on, checked before any request."""

    problems: list[str] = []
    for session, sp in plan["sessions"].items():
        first_event = sp["first_event_turn"]
        for entry in sp["turns"]:
            t = entry["turn"]
            if t < first_event and not entry["shared"]:
                problems.append(f"{session} turn {t}: arms differ before the first event")
            if t >= first_event and entry["shared"]:
                problems.append(f"{session} turn {t}: arms identical at/after the event")
    paired = 0
    schedules = {}
    for session, sp in plan["sessions"].items():
        f, r = sp["event_turns"]["F"], sp["event_turns"]["R"]
        schedules[session] = {"fork": f, "summarise_in_place": r, "identical": f == r}
        paired += sum(1 for a, b in zip(f, r) if a == b)
    n_event = sum(len(sp["event_turns"]["F"]) for sp in plan["sessions"].values())
    report = {
        "planned_requests": plan["planned_requests"],
        "sessions": len(plan["sessions"]),
        "events_per_arm": n_event,
        "events_paired_on_same_turn": paired,
        "pairs_expected": paired,
        "event_schedules": schedules,
        "event_schedules_identical": all(v["identical"] for v in schedules.values()),
        "problems": problems,
        "within_request_cap": plan["planned_requests"] <= MAX_REQUESTS,
    }
    if problems:
        raise SystemExit("PRE-FLIGHT FAILED -- no request sent:\n  " + "\n  ".join(problems))
    if plan["planned_requests"] > MAX_REQUESTS:
        raise SystemExit(
            f"PRE-FLIGHT FAILED: plan needs {plan['planned_requests']} requests > {MAX_REQUESTS}"
        )
    return report


def strip_marker(chain: list[StateNode]) -> list[StateNode]:
    """The pre-U13 fork chain: root text is the summary alone, no marker."""

    out: list[StateNode] = []
    parent = None
    for node in chain:
        text = node.text
        if text.startswith("[fork] "):
            text = text.split("\n\n", 1)[1] if "\n\n" in text else ""
        new = StateNode.create(text, node.kind, parent=parent)
        out.append(new)
        parent = new
    return out


# --------------------------------------------------------------------------- #
# Instrumentation
# --------------------------------------------------------------------------- #
CURRENT: dict[str, Any] = {}
COUNTS = {"requests": 0, "failures": 0, "consecutive_failures": 0}


class StopBatch(RuntimeError):
    pass


def make_send(chat_client: Any, started: float) -> Any:
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
        COUNTS["requests"] += 1
        try:
            result = call(messages)
        except Exception as exc:  # the client's own retry already happened once
            COUNTS["failures"] += 1
            COUNTS["consecutive_failures"] += 1
            print(f"  !! request failed ({type(exc).__name__}: {exc})", flush=True)
            if COUNTS["consecutive_failures"] >= 3:
                raise StopBatch(f"3 consecutive failures; last {exc!r}") from exc
            raise
        COUNTS["consecutive_failures"] = 0
        return result

    return send


def acquire_lock(path: Path, timeout_s: float) -> tuple[int | None, float]:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_RDWR | os.O_CREAT, 0o644)
    deadline = time.monotonic() + timeout_s
    t0 = time.monotonic()
    waited = False
    while True:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return fd, time.monotonic() - t0
        except BlockingIOError:
            if not waited:
                print(f"[lock] {path} busy; queueing (deadline {timeout_s/60:.0f} min)", flush=True)
                waited = True
            if time.monotonic() >= deadline:
                os.close(fd)
                return None, time.monotonic() - t0
            time.sleep(2.0)


def write_lock_record(path: Path, status: str) -> None:
    record = {
        "unit": "E1",
        "pid": os.getpid(),
        f"{status}_utc": time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime()),
    }
    path.write_text(json.dumps(record) + "\n", encoding="utf-8")


def release_lock(fd: int, path: Path) -> None:
    try:
        write_lock_record(path, "released")
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


# --------------------------------------------------------------------------- #
# Live run
# --------------------------------------------------------------------------- #
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--plan", action="store_true", help="offline plan + preflight only")
    ap.add_argument("--run", action="store_true", help="live run")
    args = ap.parse_args(argv)

    plan = build_plan()
    print(json.dumps(plan["preflight"], indent=2, sort_keys=True), flush=True)
    if args.plan:
        slim = json.loads(json.dumps(plan, default=str))
        for sp in slim["sessions"].values():
            for entry in sp["turns"]:
                for arm in entry["arms"].values():
                    arm.pop("chain", None)
                    arm.pop("messages", None)
        OUT_PLAN.write_text(json.dumps(slim, indent=2, sort_keys=True) + "\n")
        print(f"wrote {OUT_PLAN.relative_to(REPO)}", flush=True)
        return 0
    if not args.run:
        raise SystemExit("pass --plan or --run")

    started_wall = time.time()
    started = time.monotonic()
    chat_client = client_mod.ChatClient()
    send = make_send(chat_client, started)

    runlog: dict[str, Any] = {
        "unit": "E1",
        "mode": "live",
        "preflight": plan["preflight"],
        "planned_requests": plan["planned_requests"],
        "lock_wait_s": None,
        "status": "partial",
        "stop_reason": "",
    }
    lock_fd, lock_wait = acquire_lock(LOCK_PATH, LOCK_TIMEOUT_S)
    runlog["lock_wait_s"] = round(lock_wait, 3)
    if lock_fd is None:
        runlog["status"] = "partial"
        runlog["stop_reason"] = "lock timeout"
        OUT_RUNLOG.write_text(json.dumps(runlog, indent=2, sort_keys=True) + "\n")
        print(json.dumps({"status": "partial", "blocker": "lock timeout"}))
        return 3
    write_lock_record(LOCK_PATH, "acquired")
    print(f"[lock] acquired after {lock_wait:.1f}s", flush=True)

    events: list[dict[str, Any]] = []
    rows_written = 0
    request_index = 0
    status = "done"
    try:
        with OUT_ROWS.open("w", encoding="utf-8") as rows_fh:
            for session in SESSIONS:
                sp = plan["sessions"][session]
                for entry in sp["turns"]:
                    turn = entry["turn"]
                    arms = ("F", "R") if not entry["shared"] else ("F", "R")
                    per_arm: dict[str, Any] = {}
                    if entry["shared"]:
                        messages = entry["arms"]["F"]["messages"]
                        assert sha(messages) == entry["arms"]["R"]["prompt_sha256"]
                        request_index += 1
                        try:
                            result = send(messages)
                            per_arm = {"F": (result, request_index), "R": (result, request_index)}
                            shared = True
                        except StopBatch as exc:
                            status, runlog["stop_reason"] = "partial", str(exc)
                            break
                        except Exception as exc:
                            status, runlog["stop_reason"] = "partial", repr(exc)
                            break
                        delivered = ("F", "R")
                    else:
                        shared = False
                        delivered = []
                        for arm in arms:
                            messages = entry["arms"][arm]["messages"]
                            assert sha(messages) == entry["arms"][arm]["prompt_sha256"]
                            request_index += 1
                            try:
                                per_arm[arm] = (send(messages), request_index)
                                delivered.append(arm)
                            except StopBatch as exc:
                                status, runlog["stop_reason"] = "partial", str(exc)
                                break
                            except Exception as exc:
                                status, runlog["stop_reason"] = "partial", repr(exc)
                                break
                        if status != "done":
                            break
                    for arm in delivered:
                        a = entry["arms"][arm]
                        result_obj, req_idx = per_arm[arm]
                        prompt, cached, completion, ttft, wall, http, _text = runner._unpack(
                            result_obj
                        )
                        row = {
                            "unit": "E1",
                            "request_index": req_idx,
                            "shared_request": shared,
                            "session": session,
                            "turn": turn,
                            "arm": arm,
                            "arm_label": ARM_LABEL[arm],
                            "compaction": ARMS[arm][0].value,
                            "renderer": ARMS[arm][1].value,
                            "salt": sp["salt"],
                            "prompt_tokens": prompt,
                            "cached_tokens": cached,
                            "uncached": max(0, prompt - cached),
                            "prompt_mod64": prompt % 64,
                            "completion_tokens": completion,
                            "ttft_ms": ttft,
                            "wall_ms": wall,
                            "status": http,
                            "is_event": a["is_event"],
                            "event_index": a["event_index"],
                            "node_ids": a["node_ids"],
                            "window_nodes": len(a["node_ids"]),
                            "fork_marker_present": a["fork_marker_present"],
                            "fork_marker_line": a["fork_marker_line"],
                            "preamble_label_present": a["preamble_label_present"],
                            "prompt_sha256": a["prompt_sha256"],
                            "bytes": a["bytes"],
                            "est_tokens": a["est_tokens"],
                            "diff_offset_vs_other_arm": a["diff_offset_vs_other_arm"],
                        }
                        rows_fh.write(json.dumps(row, sort_keys=True) + "\n")
                        rows_fh.flush()
                        rows_written += 1
                    if status != "done":
                        break
                if status != "done":
                    break
                print(
                    f"  {session} done: rows={rows_written} requests={COUNTS['requests']} "
                    f"events={sp['event_turns']}",
                    flush=True,
                )
    finally:
        release_lock(lock_fd, LOCK_PATH)
        for session in SESSIONS:
            sp = plan["sessions"][session]
            for arm in ("F", "R"):
                for event in sp["events"][arm]:
                    events.append(
                        {
                            **{k: v for k, v in event.items() if k != "edited_node_ids"},
                            "session": session,
                            "arm": arm,
                            "edited_count": len(event.get("edited_node_ids") or []),
                        }
                    )
        with OUT_EVENTS.open("w", encoding="utf-8") as fh:
            for event in events:
                fh.write(json.dumps(event, sort_keys=True) + "\n")
        runlog.update(
            {
                "status": status,
                "requests": COUNTS["requests"],
                "failures": COUNTS["failures"],
                "rows": rows_written,
                "elapsed_s": round(time.monotonic() - started, 3),
                "wall_started": time.strftime(
                    "%Y-%m-%dT%H:%M:%S%z", time.localtime(started_wall)
                ),
                "rows_sha256": hashlib.sha256(OUT_ROWS.read_bytes()).hexdigest()
                if OUT_ROWS.exists()
                else None,
            }
        )
        OUT_RUNLOG.write_text(json.dumps(runlog, indent=2, sort_keys=True) + "\n")

    print(
        json.dumps(
            {
                "status": status,
                "requests": COUNTS["requests"],
                "rows": rows_written,
                "elapsed_s": runlog["elapsed_s"],
                "lock_wait_s": runlog["lock_wait_s"],
                "stop_reason": runlog["stop_reason"],
            },
            indent=2,
            sort_keys=True,
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
