#!/usr/bin/env python3
"""GROUND-TRUTH-R — live 40-turn arm-R re-measurement on production :8012.

Reuses the U15 arm-R generator verbatim (same corpus slice, same 8k compaction
trigger, same SUMMARISE_IN_PLACE policy, same NAIVE_APPEND renderer,
same max_tokens=4) with a NEW salt so this is a fresh measurement.

Deliberately does NOT touch cells/U15/**: rows go to
experiments/context-cache/cells/GROUND-TRUTH-R/rows.jsonl.
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

ROWS_PATH = HERE / "rows.jsonl"
LOCK_PATH = REPO / "experiments" / "context-cache" / ".occamy.lock"
CORPUS_PATH = REPO / "experiments" / "context-cache" / "corpora" / "endtoend.json"

TURNS = 40
BUDGET_TOKENS = 8192
KEEP_LAST = 2
MAX_TOKENS = 4
SUMMARY_CHARS = 750
SEED = 9501                      # NEW seed -> fresh salt (U15 arm R used 1501)
REQUEST_CAP = 60                 # card bound: 60 live requests
TIMEOUT_S = 120.0


def summarise(text: str) -> str:
    body = " ".join(text.split())
    if len(body) <= SUMMARY_CHARS:
        return body
    tail_len = SUMMARY_CHARS - 500 - len(" [...] ")
    return f"{body[:500]} [...] {body[-tail_len:]}"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_chat_client():
    path = REPO / "experiments" / "context-cache" / "client.py"
    spec = importlib.util.spec_from_file_location("ctx_client_gtr", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module.ChatClient


def acquire_lock(path: Path, timeout_s: float):
    handle = path.open("a+", encoding="utf-8")
    deadline = time.monotonic() + timeout_s
    while True:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            break
        except BlockingIOError:
            if time.monotonic() >= deadline:
                handle.close()
                raise TimeoutError(f"occamy lock busy for {timeout_s:.0f}s")
            time.sleep(0.5)
    handle.seek(0)
    handle.truncate()
    json.dump({"unit": "GROUND-TRUTH-R", "pid": os.getpid(), "acquired_utc": utc_now()}, handle)
    handle.flush()
    os.fsync(handle.fileno())
    return handle


def release_lock(handle) -> None:
    try:
        handle.seek(0)
        handle.truncate()
        json.dump({"unit": "GROUND-TRUTH-R", "pid": os.getpid(), "released_utc": utc_now()}, handle)
        handle.flush()
        os.fsync(handle.fileno())
        fcntl.flock(handle, fcntl.LOCK_UN)
    finally:
        handle.close()


def append_row(row: dict) -> None:
    with ROWS_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def main() -> int:
    handle = acquire_lock(LOCK_PATH, 300.0)
    requests = 0
    try:
        corpus = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
        scenario = corpus["scenarios"][0]
        preamble = scenario["preamble"]
        turns = scenario["turns"][:TURNS]
        assert len(turns) == TURNS

        # Same reference-arm compaction schedule derivation as U15.
        chain = [StateNode.create(preamble, "invariant")]
        schedule: list[int] = []
        for turn_no, turn in enumerate(turns, 1):
            chain = [*chain, StateNode.create(turn["text"], "delta", parent=chain[-1], turn=turn_no)]
            if needs_compaction(chain, budget_tokens=BUDGET_TOKENS, est_tokens=default_est_tokens):
                schedule.append(turn_no)
                chain, _ = compact(
                    chain,
                    CompactionPolicy.SUMMARISE_IN_PLACE,
                    keep_last=KEEP_LAST,
                    summarizer=summarise,
                    est_tokens=default_est_tokens,
                )

        salt = make_salt(SEED)
        client = load_chat_client()()
        print(f"GROUND-TRUTH-R start salt={salt} seed={SEED} schedule={schedule} "
              f"turns={TURNS} budget={BUDGET_TOKENS} max_tokens={MAX_TOKENS}", flush=True)

        chain = [StateNode.create(preamble, "invariant")]
        for turn_no, turn in enumerate(turns, 1):
            chain = [
                *chain,
                StateNode.create(turn["text"], "delta", parent=chain[-1], turn=turn_no),
            ]
            scheduled = turn_no in schedule
            if scheduled:
                chain, _ = compact(
                    chain,
                    CompactionPolicy.SUMMARISE_IN_PLACE,
                    keep_last=KEEP_LAST,
                    summarizer=summarise,
                    est_tokens=default_est_tokens,
                )
            messages = render(
                RenderPolicy.NAIVE_APPEND, chain, preamble=preamble, volatile={}, salt=salt
            )
            prompt, cached, completion, ttft, wall, status, text = client.chat(
                messages, max_tokens=MAX_TOKENS, thinking=False, stream=True, timeout=TIMEOUT_S
            )
            requests += 1
            warm_retry = False
            warm1_prompt = warm1_cached = None
            first_prompt, first_cached, first_status = prompt, cached, status
            if cached == 0 and prompt > 0 and prompt % 64 == 0 and turn_no > 1 and not scheduled:
                warm1_prompt, warm1_cached = prompt, cached
                prompt, cached, completion, ttft, wall, status, text = client.chat(
                    messages, max_tokens=MAX_TOKENS, thinking=False, stream=True, timeout=TIMEOUT_S
                )
                requests += 1
                warm_retry = True
            if requests > REQUEST_CAP:
                raise RuntimeError(f"request cap {REQUEST_CAP} exceeded")

            uncached = max(0, prompt - cached)
            row = {
                "unit": "GROUND-TRUTH-R",
                "cell": "GROUND-TRUTH-R/R",
                "arm": "R",
                "policy": "summarise_in_place",
                "turn": turn_no,
                "turns_total": TURNS,
                "salt": salt,
                "seed": SEED,
                "budget_tokens": BUDGET_TOKENS,
                "max_tokens": MAX_TOKENS,
                "prompt_tokens": prompt,
                "cached_tokens": cached,
                "uncached_tokens": uncached,
                "uncached": uncached,
                "completion_tokens": completion,
                "http_status": status,
                "status": status,
                "scheduled_compaction": scheduled,
                "warm_retry": warm_retry,
                "warm1_prompt_tokens": warm1_prompt,
                "warm1_cached_tokens": warm1_cached,
                "first_attempt_prompt_tokens": first_prompt,
                "first_attempt_cached_tokens": first_cached,
                "first_attempt_http_status": first_status,
                "ttft_ms": round(ttft, 3),
                "wall_ms": round(wall, 3),
                "prefix_sha256": hashlib.sha256(
                    json.dumps(messages[:2], sort_keys=True).encode()
                ).hexdigest(),
                "completion_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                "request_index": requests,
                "ts_utc": utc_now(),
            }
            append_row(row)
            print(f"PROGRESS {turn_no}/{TURNS} prompt={prompt} cached={cached} "
                  f"uncached={uncached} status={status} sched={scheduled}", flush=True)

        print(f"done rows={TURNS} requests={requests} salt={salt}", flush=True)
        return 0
    finally:
        release_lock(handle)


if __name__ == "__main__":
    raise SystemExit(main())
