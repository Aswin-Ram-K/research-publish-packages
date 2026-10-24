#!/usr/bin/env python3
"""G3 — context-limit run (GAP-CLOSE): append-note availability at 32k/64k context.

Arms: R summarise-in-place, A append-note, C no compaction, H hybrid
(append until limit then compact with summarise). Two context limits (budgets)
32768 and 65536; turns sized so the growing arms reach ~budget (74 and 148).
Decision rule: A is "unavailable" at a depth if its request cannot be sent at
the target length (prompt_tokens > budget) or returns an error (status != 200
or prompt exceeds max_model_len 131072).

One request in flight, strictly serial; holds .occamy.lock for the whole run.
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
assert (REPO / "src" / "resextract").is_dir()
SRC = REPO / "src"
sys.path.insert(0, str(SRC))

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

CELL_DIR = HERE
ROWS_PATH = CELL_DIR / "rows.jsonl"
EVENTS_PATH = CELL_DIR / "events.jsonl"
ANALYSIS_PATH = CELL_DIR / "analysis.json"
LOCK_PATH = REPO / "experiments" / "context-cache" / ".occamy.lock"
CORPUS_PATH = REPO / "experiments" / "context-cache" / "corpora" / "endtoend.json"
HANDOFF_PATH = REPO / "orchestration" / "handoffs" / "G3.json"

CONFIG_PATH = REPO / "state" / "config" / "live-server-config.json"
CONFIG_SHA256 = hashlib.sha256(CONFIG_PATH.read_bytes()).hexdigest()
STACK = "sglang"
CONFIG_ID = "S0"
MAX_MODEL_LEN = 131072

KEEP_LAST = 2
MAX_TOKENS = 4
REQUEST_CAP = 900
INTERNAL_REQUEST_CAP = 900
LOCK_TIMEOUT_S = 300.0
SUMMARY_CHARS = 750

# depths: (label, budget, turns)
DEPTHS = [
    ("32k", 32768, 74),
    ("64k", 65536, 148),
]

ARMS = (
    {"arm": "R", "policy": "summarise_in_place", "compaction": CompactionPolicy.SUMMARISE_IN_PLACE, "seed": 3201},
    {"arm": "A", "policy": "append_note", "compaction": CompactionPolicy.APPEND_NOTE, "seed": 3202},
    {"arm": "C", "policy": "none", "compaction": None, "seed": 3203},
    {"arm": "H", "policy": "hybrid", "compaction": CompactionPolicy.SUMMARISE_IN_PLACE, "seed": 3204},
)


def summarise(text: str) -> str:
    body = " ".join(text.split())
    if len(body) <= SUMMARY_CHARS:
        return body
    tail_len = SUMMARY_CHARS - 500 - len(" [...] ")
    return f"{body[:500]} [...] {body[-tail_len:]}"


def total_est(chain):
    return sum(default_est_tokens(n.text) for n in chain)


def load_slice(n):
    corpus = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
    scenario = corpus["scenarios"][0]
    turns = (scenario["turns"] * ((n // len(scenario["turns"])) + 1))[:n]
    assert len(turns) == n, (len(turns), n)
    return scenario, turns


def compaction_schedule(preamble, turns, budget):
    chain = [StateNode.create(preamble, "invariant")]
    schedule = []
    for turn_no, turn in enumerate(turns, 1):
        chain = [*chain, StateNode.create(turn["text"], "delta", parent=chain[-1], turn=turn_no)]
        if needs_compaction(chain, budget_tokens=budget, est_tokens=default_est_tokens):
            schedule.append(turn_no)
            chain, _ = compact(chain, CompactionPolicy.SUMMARISE_IN_PLACE, keep_last=KEEP_LAST,
                               summarizer=summarise, est_tokens=default_est_tokens)
    return schedule


def digest_prefix(messages, keep=2):
    return hashlib.sha256(canonical_bytes(messages[:keep])).hexdigest()


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def load_chat_client():
    path = REPO / "experiments" / "context-cache" / "client.py"
    spec = importlib.util.spec_from_file_location("ctx_client_g3", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module.ChatClient


def acquire_lock(path, timeout_s):
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
                raise TimeoutError(f"occamy lock {path} busy")
            time.sleep(0.5)
    handle.seek(0)
    handle.truncate()
    json.dump({"unit": "G3", "pid": os.getpid(), "acquired_utc": utc_now()}, handle)
    handle.flush()
    os.fsync(handle.fileno())
    return handle, time.monotonic() - started


def release_lock(handle):
    try:
        handle.seek(0)
        handle.truncate()
        json.dump({"unit": "G3", "pid": os.getpid(), "released_utc": utc_now()}, handle)
        handle.flush()
        os.fsync(handle.fileno())
        fcntl.flock(handle, fcntl.LOCK_UN)
    finally:
        handle.close()


def load_existing():
    out = {}
    if not ROWS_PATH.exists():
        return out
    for line in ROWS_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        out[(str(row["arm"]), str(row.get("depth")), int(row["turn"]))] = row
    return out


def append_row(row):
    with ROWS_PATH.open("a", encoding="utf-8") as h:
        h.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")
        h.flush()
        os.fsync(h.fileno())


def write_json_atomic(path, payload):
    tmp = CELL_DIR / (path.name + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def run(lock_note):
    started = time.monotonic()
    scenario, _ = load_slice(DEPTHS[0][2])
    preamble = scenario["preamble"]

    existing = load_existing()
    client = load_chat_client()()
    salts = {str(s["arm"]): make_salt(int(s["seed"])) for s in ARMS}

    requests = 0
    live_rows = []
    compaction_events = []
    anomalies = []

    # validate resumed
    for row in existing.values():
        arm = str(row["arm"])
        if arm not in salts:
            raise RuntimeError(f"unknown arm {arm}")
        if row["salt"] != salts[arm]:
            raise RuntimeError(f"salt mismatch {arm}")

    total_rows = sum(len(ARMS) * turns for _, _, turns in DEPTHS)
    done = len(existing)
    print(f"G3 start: rows_existing={done}/{total_rows}", flush=True)

    for depth_label, budget, n_turns in DEPTHS:
        scenario, turns = load_slice(n_turns)
        # use scenario 0 preamble (same)
        preamble = scenario["preamble"]
        schedule = compaction_schedule(preamble, turns, budget)
        print(f"depth={depth_label} budget={budget} turns={n_turns} schedule={schedule}", flush=True)
        for spec in ARMS:
            arm = str(spec["arm"])
            policy = str(spec["policy"])
            base_compaction = spec["compaction"]
            salt = salts[arm]
            chain = [StateNode.create(preamble, "invariant")]
            crossed = False
            for turn_no, turn in enumerate(turns, 1):
                chain = [*chain, StateNode.create(turn["text"], "delta", parent=chain[-1], turn=turn_no)]
                est_before = total_est(chain)
                scheduled = bool(base_compaction is not None and turn_no in schedule)
                # hybrid: before crossing use append_note, after crossing summarise
                if arm == "H" and scheduled:
                    crossed = True
                if arm == "A" and scheduled:
                    compaction_policy = CompactionPolicy.APPEND_NOTE
                elif arm == "H":
                    compaction_policy = CompactionPolicy.APPEND_NOTE if not crossed else CompactionPolicy.SUMMARISE_IN_PLACE
                else:
                    compaction_policy = base_compaction
                event = None
                if scheduled and compaction_policy is not None:
                    chain, event = compact(chain, compaction_policy, keep_last=KEEP_LAST,
                                          summarizer=summarise, est_tokens=default_est_tokens)
                    compaction_events.append({"unit": "G3", "depth": depth_label, "arm": arm,
                                             "turn": turn_no, "policy": str(compaction_policy)})
                messages = render(RenderPolicy.NAIVE_APPEND, chain, preamble=preamble, volatile={}, salt=salt)
                key = (arm, depth_label, turn_no)
                if key in existing:
                    prior = existing[key]
                    if bool(prior.get("scheduled_compaction")) != scheduled:
                        raise RuntimeError(f"arm {arm} depth {depth_label} turn {turn_no}: scheduled mismatch")
                    # replay chain state not tracked; skip request
                    continue
                prompt, cached, completion, ttft, wall, status, text = client.chat(
                    messages, max_tokens=MAX_TOKENS, thinking=False, stream=True, timeout=120.0)
                requests += 1
                # error handling: if prompt exceeds max_model_len, mark unavailable (status already)
                warm_retry = False
                warm1_prompt = None
                warm1_cached = None
                if cached == 0 and prompt > 0 and prompt % 64 == 0 and turn_no > 1 and not scheduled:
                    warm1_prompt, warm1_cached = prompt, cached
                    prompt, cached, completion, ttft, wall, status, text = client.chat(
                        messages, max_tokens=MAX_TOKENS, thinking=False, stream=True, timeout=120.0)
                    requests += 1
                    warm_retry = True
                if requests > INTERNAL_REQUEST_CAP:
                    raise RuntimeError(f"request cap guard: {requests}")
                if turn_no == 1 and cached != 0:
                    raise RuntimeError(f"arm {arm}: cold-start violated cached={cached}")
                uncached = max(0, prompt - cached)
                row = {
                    "unit": "G3",
                    "cell": f"G3/{depth_label}/{arm}",
                    "depth": depth_label,
                    "budget_tokens": budget,
                    "arm": arm,
                    "policy": policy,
                    "turn": turn_no,
                    "turns_total": n_turns,
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
                    "warm_retry": warm_retry,
                    "warm1_prompt_tokens": warm1_prompt,
                    "warm1_cached_tokens": warm1_cached,
                    "request_index": requests,
                    "ts_utc": utc_now(),
                    "stack": STACK,
                    "config_id": CONFIG_ID,
                    "config_sha256": CONFIG_SHA256,
                }
                append_row(row)
                live_rows.append(row)
                done += 1
                print(f"PROGRESS {done}/{total_rows} depth={depth_label} arm={arm} turn={turn_no} "
                      f"prompt={prompt} cached={cached} uncached={uncached} status={status} "
                      f"chain_est={total_est(chain)}", flush=True)

    elapsed = time.monotonic() - started
    # build a minimal analysis payload
    import g3_analyze  # noqa
    rows = g3_analyze.load_rows(ROWS_PATH)
    payload = g3_analyze.analyze(rows)
    rows_sha = hashlib.sha256(ROWS_PATH.read_bytes()).hexdigest()
    stamps = sorted(str(r.get("ts_utc") or "") for r in rows if r.get("ts_utc"))
    payload["digest"] = {
        "rows_sha256": rows_sha,
        "n_rows": len(rows),
        "requests_live": len(rows) + sum(1 for r in rows if r.get("warm_retry")),
        "requests_this_run": requests,
        "requests_cap": REQUEST_CAP,
        "first_row_ts": stamps[0] if stamps else None,
        "last_row_ts": stamps[-1] if stamps else None,
        "elapsed_s": round(elapsed, 1),
        "compaction_schedule": None,
        "salts": salts,
        "config_sha256": CONFIG_SHA256,
        "stack": STACK,
        "config_id": CONFIG_ID,
        "max_model_len": MAX_MODEL_LEN,
        "depths": DEPTHS,
    }
    write_json_atomic(ANALYSIS_PATH, payload)
    EVENTS_PATH.write_text(json.dumps({"unit": "G3", "compaction_events": compaction_events,
                                      "anomalies": anomalies}, indent=2) + "\n", encoding="utf-8")

    status = "done" if len(rows) == total_rows else "partial"
    handoff = {
        "unit": "G3",
        "status": status,
        "artifacts": [
            "experiments/context-cache/cells/G3/rows.jsonl",
            "experiments/context-cache/cells/G3/analysis.json",
            "experiments/context-cache/cells/G3/g3_cell.py",
            "experiments/context-cache/cells/G3/g3_analyze.py",
        ],
        "evidence": {
            "command": ".venv/bin/python experiments/context-cache/cells/G3/g3_cell.py",
            "requests_live": len(rows) + sum(1 for r in rows if r.get("warm_retry")),
            "rows": f"{len(rows)}/{total_rows}",
            "rows_sha256": rows_sha,
        },
        "blocker": "" if status == "done" else f"only {len(rows)}/{total_rows} rows",
        "next_unit_hint": "G5 replication",
        "write_paths": ["experiments/context-cache/cells/G3/**", "orchestration/handoffs/G3.json"],
    }
    tmp = CELL_DIR / "G3.handoff.tmp"
    tmp.write_text(json.dumps(handoff, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, HANDOFF_PATH)
    print(f"handoff: {HANDOFF_PATH} status={status}", flush=True)
    return 0 if status == "done" else 2


def main():
    started = time.monotonic()
    handle = None
    lock_note = ""
    try:
        handle, waited = acquire_lock(LOCK_PATH, LOCK_TIMEOUT_S)
        lock_note = f"acquired after {waited:.1f}s"
    except TimeoutError as exc:
        print(f"BLOCKED: {exc}", flush=True)
        return 3
    try:
        return run(lock_note)
    except Exception as exc:
        print(f"FAILED: {type(exc).__name__}: {exc}", flush=True)
        return 1
    finally:
        if handle is not None:
            release_lock(handle)


if __name__ == "__main__":
    raise SystemExit(main())
