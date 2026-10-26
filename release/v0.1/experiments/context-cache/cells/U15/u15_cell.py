#!/usr/bin/env python3
"""U15 — one live four-arm cell: is compaction cost head mutability?

Design (identical across arms except the compaction policy):

* corpus slice ``endtoend.json`` scenario 0 (``E1``), turns 1-40;
* 8k compaction trigger (``needs_compaction`` over ``default_est_tokens``);
* **the same two compaction points in every arm** — turns 18 and 35, derived
  once by simulating the reference arm (``SUMMARISE_IN_PLACE``) so the trigger
  is not arm-dependent;
* renderer ``NAIVE_APPEND`` everywhere, ``max_tokens=4``, no thinking;
* a **fresh salt per arm** (cold isolation — never ``/flush_cache``);
* one request in flight, strictly serial.

Arms: R ``summarise_in_place``, F ``fork``, A ``append_note`` (never shrinks),
C no compaction (control for the ambient per-turn uncached residual).

Durability: every row is appended to ``rows.jsonl`` and ``fsync``-ed before
the next request.  On startup any ``(arm, turn)`` already present is skipped,
and the chain is replayed deterministically, so a crash loses at most the
in-flight request and a rerun resumes for free.

The summariser is an offline deterministic stub (~750 chars ≈ the corpus's own
``summary_hint_est_tokens=188``), identical for every arm — the unit is a cache
measurement, not a summarisation-quality measurement, and an extra model call
would both spend budget and make the compaction points non-deterministic.

Writes only under ``experiments/context-cache/cells/U15/`` and the two
orchestration paths named in ``write_paths``.  No ``src/`` or ``tests/`` edit.
"""

from __future__ import annotations

import fcntl
import hashlib
import importlib.util
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
assert (REPO / "src" / "resextract").is_dir(), f"repo root not found from {HERE}"
SRC = REPO / "src"
sys.path.insert(0, str(SRC))
sys.path.insert(0, str(HERE))

from resextract.context import (  # noqa: E402
    CompactionPolicy,
    RenderPolicy,
    StateNode,
    compact,
    default_est_tokens,
    make_salt,
    needs_compaction,
    render,
)
from resextract.context.render import canonical_bytes  # noqa: E402

import u15_analyze  # noqa: E402

CELL_DIR = HERE
ROWS_PATH = CELL_DIR / "rows.jsonl"
EVENTS_PATH = CELL_DIR / "events.jsonl"
ANALYSIS_PATH = CELL_DIR / "analysis.json"
LOCK_PATH = REPO / "experiments" / "context-cache" / ".occamy.lock"
CORPUS_PATH = REPO / "experiments" / "context-cache" / "corpora" / "endtoend.json"
HANDOFF_PATH = REPO / "orchestration" / "handoffs" / "U15.json"

TURNS = 40
BUDGET_TOKENS = 8192
KEEP_LAST = 2
MAX_TOKENS = 4
REQUEST_CAP = 220
INTERNAL_REQUEST_CAP = 210
LOCK_TIMEOUT_S = 300.0
SUMMARY_CHARS = 750

ARMS: tuple[dict[str, object], ...] = (
    {
        "arm": "R",
        "policy": "summarise_in_place",
        "compaction": CompactionPolicy.SUMMARISE_IN_PLACE,
        "seed": 1501,
    },
    {
        "arm": "F",
        "policy": "fork",
        "compaction": CompactionPolicy.FORK,
        "seed": 1502,
    },
    {
        "arm": "A",
        "policy": "append_note",
        "compaction": CompactionPolicy.APPEND_NOTE,
        "seed": 1503,
    },
    {"arm": "C", "policy": "none", "compaction": None, "seed": 1504},
)

WRITE_PATHS = [
    "experiments/context-cache/cells/U15/**",
    "orchestration/handoffs/U15.json",
    "orchestration/units/U15.md",
]


# --------------------------------------------------------------------------- #
# Deterministic offline pieces
# --------------------------------------------------------------------------- #
def summarise(text: str) -> str:
    """Deterministic offline summary stub: <=``SUMMARY_CHARS`` chars."""

    body = " ".join(text.split())
    if len(body) <= SUMMARY_CHARS:
        return body
    tail_len = SUMMARY_CHARS - 500 - len(" [...] ")
    return f"{body[:500]} [...] {body[-tail_len:]}"


def total_est(chain: list[StateNode]) -> int:
    return sum(default_est_tokens(node.text) for node in chain)


def load_slice() -> tuple[dict, list[dict]]:
    corpus = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
    scenario = corpus["scenarios"][0]
    turns = scenario["turns"][:TURNS]
    if len(turns) != TURNS:
        raise RuntimeError(f"corpus slice has {len(turns)} turns, expected {TURNS}")
    return scenario, turns


def compaction_schedule(preamble: str, turns: list[dict]) -> list[int]:
    """Turn numbers at which the reference arm crosses the 8k trigger."""

    chain = [StateNode.create(preamble, "invariant")]
    schedule: list[int] = []
    for turn_no, turn in enumerate(turns, 1):
        chain = [*chain, StateNode.create(turn["text"], "delta", parent=chain[-1], turn=turn_no)]
        if needs_compaction(chain, budget_tokens=BUDGET_TOKENS, est_tokens=default_est_tokens):
            schedule.append(turn_no)
            chain, _event = compact(
                chain,
                CompactionPolicy.SUMMARISE_IN_PLACE,
                keep_last=KEEP_LAST,
                summarizer=summarise,
                est_tokens=default_est_tokens,
            )
    return schedule


def digest_prefix(messages: list[dict], keep: int = 2) -> str:
    return hashlib.sha256(canonical_bytes(messages[:keep])).hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_chat_client():
    """Import ``client.py`` by path -- ``context-cache`` is not an identifier."""

    path = REPO / "experiments" / "context-cache" / "client.py"
    spec = importlib.util.spec_from_file_location("ctx_client_u15", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load chat client from {path}")
    module = importlib.util.module_from_spec(spec)
    # dataclasses resolves cls.__module__ through sys.modules; exec_module on an
    # unregistered module fails on 3.14.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module.ChatClient


# --------------------------------------------------------------------------- #
# Lock
# --------------------------------------------------------------------------- #
def acquire_lock(path: Path, timeout_s: float) -> tuple[object, float]:
    """flock ``path`` with a deadline; never hang past ``timeout_s``."""

    handle = path.open("a+", encoding="utf-8")
    started = time.monotonic()
    deadline = started + timeout_s
    while True:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            break
        except BlockingIOError:
            if time.monotonic() >= deadline:
                handle.close()
                raise TimeoutError(f"occamy lock {path} busy for {timeout_s:.0f}s")
            time.sleep(0.5)
    handle.seek(0)
    handle.truncate()
    json.dump(
        {
            "unit": "U15",
            "pid": os.getpid(),
            "acquired_utc": utc_now(),
            "waited_s": round(time.monotonic() - started, 1),
            "scope": "U15 four-arm cell; hold for the whole run",
        },
        handle,
    )
    handle.flush()
    os.fsync(handle.fileno())
    return handle, time.monotonic() - started


def release_lock(handle: object) -> None:
    try:
        handle.seek(0)
        handle.truncate()
        json.dump({"unit": "U15", "pid": os.getpid(), "released_utc": utc_now()}, handle)
        handle.flush()
        os.fsync(handle.fileno())
        fcntl.flock(handle, fcntl.LOCK_UN)
    finally:
        handle.close()


# --------------------------------------------------------------------------- #
# Rows
# --------------------------------------------------------------------------- #
def load_existing() -> dict[tuple[str, int], dict]:
    out: dict[tuple[str, int], dict] = {}
    if not ROWS_PATH.exists():
        return out
    for line in ROWS_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue  # truncated trailing line from a crash
        out[(str(row["arm"]), int(row["turn"]))] = row
    return out


def append_row(row: dict) -> None:
    with ROWS_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def write_json_atomic(path: Path, payload: dict) -> None:
    tmp = CELL_DIR / (path.name + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)


# --------------------------------------------------------------------------- #
# Main run
# --------------------------------------------------------------------------- #
def run(lock_note: str = "") -> int:
    started = time.monotonic()
    scenario, turns = load_slice()
    preamble = scenario["preamble"]
    schedule = compaction_schedule(preamble, turns)
    salts = {str(spec["arm"]): make_salt(int(spec["seed"])) for spec in ARMS}

    existing = load_existing()
    total_rows = len(ARMS) * TURNS
    requests = 0
    live_rows: list[dict] = []
    compaction_events: list[dict] = []
    anomalies: list[dict] = []

    # Validate resumed rows against this run's deterministic design.
    for row in existing.values():
        arm = str(row["arm"])
        if arm not in salts:
            raise RuntimeError(f"rows.jsonl holds unknown arm {arm!r}")
        if row["salt"] != salts[arm]:
            raise RuntimeError(f"arm {arm}: resumed row salt {row['salt']!r} != {salts[arm]!r}")

    client = load_chat_client()()
    done = len(existing)
    print(
        f"U15 start: schedule={schedule} rows_existing={done}/{total_rows} "
        f"salts={salts} corpus={CORPUS_PATH.relative_to(REPO)}",
        flush=True,
    )

    for spec in ARMS:
        arm = str(spec["arm"])
        policy = str(spec["policy"])
        compaction = spec["compaction"]
        salt = salts[arm]
        chain = [StateNode.create(preamble, "invariant")]
        for turn_no, turn in enumerate(turns, 1):
            chain = [
                *chain,
                StateNode.create(turn["text"], "delta", parent=chain[-1], turn=turn_no),
            ]
            est_before = total_est(chain)
            scheduled = bool(compaction is not None and turn_no in schedule)
            event = None
            if scheduled:
                chain, event = compact(
                    chain,
                    compaction,  # type: ignore[arg-type]
                    keep_last=KEEP_LAST,
                    summarizer=summarise,
                    est_tokens=default_est_tokens,
                )
                compaction_events.append(
                    {**event, "unit": "U15", "arm": arm, "turn": turn_no, "salt": salt}
                )
            messages = render(
                RenderPolicy.NAIVE_APPEND,
                chain,
                preamble=preamble,
                volatile={},
                salt=salt,
            )
            key = (arm, turn_no)
            if key in existing:
                prior = existing[key]
                if bool(prior.get("scheduled_compaction")) != scheduled:
                    raise RuntimeError(
                        f"arm {arm} turn {turn_no}: resumed scheduled_compaction="
                        f"{prior.get('scheduled_compaction')} != computed {scheduled}"
                    )
                continue

            prompt, cached, completion, ttft, wall, status, text = client.chat(
                messages,
                max_tokens=MAX_TOKENS,
                thinking=False,
                stream=True,
                timeout=120.0,
            )
            requests += 1
            warm_retry = False
            warm1_prompt = None
            warm1_cached = None
            # U10 rule: an exact multiple of 64 misses on the first identical
            # repeat, so warm twice -- but only on a normal appended turn.  At
            # a scheduled compaction turn the prompt is a genuinely new prefix,
            # where cached==0 is the break being measured, not a grid artefact.
            if cached == 0 and prompt > 0 and prompt % 64 == 0 and turn_no > 1 and not scheduled:
                warm1_prompt, warm1_cached = prompt, cached
                prompt, cached, completion, ttft, wall, status, text = client.chat(
                    messages,
                    max_tokens=MAX_TOKENS,
                    thinking=False,
                    stream=True,
                    timeout=120.0,
                )
                requests += 1
                warm_retry = True
                anomalies.append(
                    {
                        "kind": "warm_twice",
                        "arm": arm,
                        "turn": turn_no,
                        "warm1_prompt_tokens": warm1_prompt,
                        "warm1_cached_tokens": warm1_cached,
                        "warm2_prompt_tokens": prompt,
                        "warm2_cached_tokens": cached,
                    }
                )
            if requests > INTERNAL_REQUEST_CAP:
                raise RuntimeError(
                    f"request cap guard tripped: {requests} > {INTERNAL_REQUEST_CAP} "
                    f"(hard cap {REQUEST_CAP})"
                )
            if turn_no == 1 and cached != 0:
                raise RuntimeError(
                    f"arm {arm}: cold-start contract violated -- turn 1 cached={cached}, "
                    "the per-arm salt is not fresh"
                )
            if turn_no > 1 and cached == 0 and not scheduled:
                anomalies.append(
                    {
                        "kind": "unexpected_zero_cache",
                        "arm": arm,
                        "turn": turn_no,
                        "prompt_tokens": prompt,
                    }
                )

            uncached = max(0, prompt - cached)
            row = {
                "unit": "U15",
                "cell": f"U15/{arm}",
                "arm": arm,
                "policy": policy,
                "turn": turn_no,
                "turns_total": TURNS,
                "salt": salt,
                "prompt_tokens": prompt,
                "cached_tokens": cached,
                "uncached": uncached,
                "completion_tokens": completion,
                "ttft_ms": round(ttft, 3),
                "wall_ms": round(wall, 3),
                "status": status,
                "scheduled_compaction": scheduled,
                "est_chain_tokens_before": est_before,
                "est_chain_tokens_after": total_est(chain),
                "nodes": len(chain),
                "messages": len(messages),
                "chars": sum(len(str(m["content"])) for m in messages),
                "prefix_sha256": digest_prefix(messages, keep=2),
                "head_sha256": hashlib.sha256(
                    str(messages[0]["content"]).encode("utf-8")
                ).hexdigest(),
                "warm_retry": warm_retry,
                "warm1_prompt_tokens": warm1_prompt,
                "warm1_cached_tokens": warm1_cached,
                "completion_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                "request_index": requests,
                "ts_utc": utc_now(),
            }
            append_row(row)
            live_rows.append(row)
            done += 1
            pct = 100.0 * done / total_rows
            print(
                f"PROGRESS {done}/{total_rows} ({pct:.1f}%) arm={arm} turn={turn_no} "
                f"prompt={prompt} cached={cached} uncached={uncached} "
                f"status={status} chain_est={total_est(chain)}",
                flush=True,
            )

    elapsed = time.monotonic() - started
    rows = u15_analyze.load_rows(ROWS_PATH)
    payload = u15_analyze.analyze(rows)
    rows_sha = hashlib.sha256(ROWS_PATH.read_bytes()).hexdigest()
    warm_retries = sum(1 for r in rows if r.get("warm_retry"))
    # One row == one request, except a grid-boundary warm retry (two sends).
    requests_total = len(rows) + warm_retries
    stamps = sorted(str(r.get("ts_utc") or "") for r in rows if r.get("ts_utc"))
    payload["digest"] = {
        "rows_sha256": rows_sha,
        "n_rows": len(rows),
        "n_rows_by_arm": {arm: len([r for r in rows if r["arm"] == arm]) for arm, _ in u15_analyze.ARMS},
        "requests_live": requests_total,
        "requests_this_run": requests,
        "requests_cap": REQUEST_CAP,
        "first_row_ts": stamps[0] if stamps else None,
        "last_row_ts": stamps[-1] if stamps else None,
        "elapsed_s": round(elapsed, 1),
        "compaction_schedule": schedule,
        "summariser": (
            f"deterministic offline stub: whitespace-collapsed folded text "
            f"truncated to {SUMMARY_CHARS} chars (~188 est tokens, matching the "
            f"corpus summary_hint)"
        ),
        "renderer": RenderPolicy.NAIVE_APPEND.value,
        "budget_tokens": BUDGET_TOKENS,
        "keep_last": KEEP_LAST,
        "corpus": str(CORPUS_PATH.relative_to(REPO)),
        "corpus_scenario": scenario["id"],
        "corpus_sha256": hashlib.sha256(CORPUS_PATH.read_bytes()).hexdigest(),
        "salts": salts,
    }
    write_json_atomic(ANALYSIS_PATH, payload)

    events = {
        "unit": "U15",
        "compaction_events": compaction_events,
        "warm_twice": [a for a in anomalies if a["kind"] == "warm_twice"],
        "unexpected_zero_cache": [a for a in anomalies if a["kind"] == "unexpected_zero_cache"],
    }
    EVENTS_PATH.write_text(json.dumps(events, indent=2) + "\n", encoding="utf-8")

    status = "done" if len(rows) == total_rows else "partial"
    return write_handoff(
        status=status,
        payload=payload,
        requests=requests_total,
        requests_this_run=requests,
        elapsed=elapsed,
        blocker="" if status == "done" else f"only {len(rows)}/{total_rows} rows present",
        lock_note=lock_note,
    )


def per_arm_line(payload: dict, arm: str) -> str:
    s = payload["arms"][arm]
    if s.get("missing"):
        return f"{arm}: MISSING"
    return (
        f"{arm}: prompt={s['total_prompt_tokens']} cached={s['total_cached_tokens']} "
        f"uncached={s['total_uncached_tokens']} hit={s['hit_rate_weighted']:.4f} "
        f"breaks={s['prefix_break_events']} "
        f"net_break_cost={s['break_cost_net_total_vs_C']}"
    )


def break_line(payload: dict, arm: str) -> str:
    s = payload["arms"][arm]
    if s.get("missing"):
        return f"{arm}: MISSING"
    return f"{arm}: {s['prefix_break_events']} at {s['prefix_break_turns']}"


def write_handoff(
    *,
    status: str,
    payload: dict | None,
    requests: int,
    requests_this_run: int,
    elapsed: float,
    blocker: str,
    lock_note: str,
) -> int:
    evidence: dict[str, object] = {
        "command": ".venv/bin/python experiments/context-cache/cells/U15/u15_cell.py",
        "requests_live": (
            f"{requests} cell requests (this run: {requests_this_run}; "
            f"hard cap {REQUEST_CAP})"
        ),
        "elapsed_s": round(elapsed, 1),
    }
    answer: dict[str, object] = {}
    if payload is not None:
        digest = payload["digest"]
        evidence.update(
            {
                "rows": f"{digest['n_rows']}/160 rows "
                f"{digest['n_rows_by_arm']} in experiments/context-cache/cells/U15/rows.jsonl",
                "rows_sha256": digest["rows_sha256"],
                "first_row_ts": digest.get("first_row_ts"),
                "last_row_ts": digest.get("last_row_ts"),
                "compaction_schedule": digest["compaction_schedule"],
                "per_arm": "; ".join(per_arm_line(payload, arm) for arm, _ in u15_analyze.ARMS),
                "prefix_breaks": "; ".join(
                    break_line(payload, arm) for arm, _ in u15_analyze.ARMS
                ),
                "window_cost_A": json.dumps(payload["window_cost_of_never_compacting"]),
                "decomposition": json.dumps(payload.get("decomposition")),
            }
        )
        c = payload["claim"]
        answer = {
            "question": c["question"],
            "answer": c["answer"],
            "ratio_R_over_A": c["ratio_R_over_A"],
            "statement": c["statement"],
            "window_cost_of_never_compacting": payload["window_cost_of_never_compacting"],
            "decomposition": payload.get("decomposition"),
        }
        evidence["claim"] = json.dumps(c)

    handoff = {
        "unit": "U15",
        "status": status,
        "artifacts": [
            "experiments/context-cache/cells/U15/rows.jsonl",
            "experiments/context-cache/cells/U15/events.jsonl",
            "experiments/context-cache/cells/U15/analysis.json",
            "experiments/context-cache/cells/U15/u15_cell.py",
            "experiments/context-cache/cells/U15/u15_analyze.py",
            "orchestration/units/U15.md",
        ],
        "evidence": evidence,
        "blocker": blocker,
        "next_unit_hint": (
            "Verifier: re-run `.venv/bin/python "
            "experiments/context-cache/cells/U15/u15_analyze.py` offline (no live "
            "calls) and compare analysis.json's rows_sha256; check Arm A has zero "
            "prefix-break events while R and F break exactly at the scheduled "
            "compaction turns, and that C's ambient residual is subtracted in the "
            "net break cost. Then rule on whether the edit-vs-fork refutation "
            "stands."
        ),
        "write_paths": WRITE_PATHS,
        "answer": answer,
        "lock": lock_note,
    }
    tmp = CELL_DIR / "U15.handoff.tmp"
    tmp.write_text(json.dumps(handoff, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, HANDOFF_PATH)
    print(f"handoff: {HANDOFF_PATH.relative_to(REPO)} status={status}", flush=True)
    if payload is not None:
        print(per_arm_line(payload, "R"))
        print(per_arm_line(payload, "F"))
        print(per_arm_line(payload, "A"))
        print(per_arm_line(payload, "C"))
        print(payload["claim"]["statement"])
    return 0 if status == "done" else 2


def main() -> int:
    started = time.monotonic()
    lock_note = ""
    handle = None
    try:
        handle, waited = acquire_lock(LOCK_PATH, LOCK_TIMEOUT_S)
        lock_note = f"acquired after {waited:.1f}s; pid {os.getpid()}; held for the whole run"
    except TimeoutError as exc:
        lock_note = f"NOT acquired: {exc}"
        print(f"BLOCKED: {exc}", flush=True)
        write_handoff(
            status="failed",
            payload=None,
            requests=0,
            requests_this_run=0,
            elapsed=time.monotonic() - started,
            blocker=lock_note,
            lock_note=lock_note,
        )
        return 3

    try:
        code = run(lock_note)
        return code
    except Exception as exc:  # noqa: BLE001 - a failed unit still reports
        print(f"FAILED: {type(exc).__name__}: {exc}", flush=True)
        rows = u15_analyze.load_rows(ROWS_PATH) if ROWS_PATH.exists() else []
        payload = u15_analyze.analyze(rows) if rows else None
        if payload is not None:
            payload["digest"] = {
                "rows_sha256": hashlib.sha256(ROWS_PATH.read_bytes()).hexdigest(),
                "n_rows": len(rows),
                "n_rows_by_arm": {
                    arm: len([r for r in rows if r["arm"] == arm]) for arm, _ in u15_analyze.ARMS
                },
                "requests_live": len(rows),
                "requests_this_run": None,
                "requests_cap": REQUEST_CAP,
                "elapsed_s": round(time.monotonic() - started, 1),
                "compaction_schedule": None,
                "summariser": "deterministic offline stub",
                "renderer": RenderPolicy.NAIVE_APPEND.value,
                "budget_tokens": BUDGET_TOKENS,
                "keep_last": KEEP_LAST,
                "corpus": str(CORPUS_PATH.relative_to(REPO)),
                "corpus_scenario": "E1",
                "corpus_sha256": hashlib.sha256(CORPUS_PATH.read_bytes()).hexdigest(),
                "salts": {},
            }
            write_json_atomic(ANALYSIS_PATH, payload)
        write_handoff(
            status="partial" if rows else "failed",
            payload=payload,
            requests=len(rows),
            requests_this_run=0,
            elapsed=time.monotonic() - started,
            blocker=f"{type(exc).__name__}: {exc}",
            lock_note=lock_note,
        )
        return 1
    finally:
        if handle is not None:
            release_lock(handle)


if __name__ == "__main__":
    raise SystemExit(main())
