#!/usr/bin/env python3
"""G1 — isolated fork break-cost (EDIT vs FORK).

Design:
* corpus slice endtoend.json scenario 0, turns 1-44;
* 8k compaction trigger; compaction points 18 and 35 in every arm;
* renderer NAIVE_APPEND everywhere, max_tokens=4;
* 3 sessions (salt replicates) x 2 arms = 6 independent chains;
* one request in flight, strictly serial.
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

import g1_analyze  # noqa: E402

CELL_DIR = HERE
ROWS_PATH = CELL_DIR / "rows.jsonl"
EVENTS_PATH = CELL_DIR / "events.jsonl"
ANALYSIS_PATH = CELL_DIR / "analysis.json"
LOCK_PATH = REPO / "experiments" / "context-cache" / ".occamy.lock"
CORPUS_PATH = REPO / "experiments" / "context-cache" / "corpora" / "endtoend.json"
HANDOFF_PATH = REPO / "orchestration" / "handoffs" / "G1.json"
CONFIG_PATH = REPO / "state" / "config" / "live-server-config.json"

TURNS = 44
BUDGET_TOKENS = 8192
KEEP_LAST = 2
MAX_TOKENS = 4
REQUEST_CAP = 320
INTERNAL_REQUEST_CAP = 310
LOCK_TIMEOUT_S = 5400.0
SUMMARY_CHARS = 750
STACK = "sglang"
CONFIG_ID = "S0"

SESSIONS = ("g1-s1", "g1-s2", "g1-s3")
ARMS: tuple[dict[str, object], ...] = (
    {
        "arm": "E",
        "policy": "summarise_in_place",
        "compaction": CompactionPolicy.SUMMARISE_IN_PLACE,
        "seed_base": 1501,
    },
    {
        "arm": "F",
        "policy": "fork",
        "compaction": CompactionPolicy.FORK,
        "seed_base": 1502,
    },
)


def summarise(text: str) -> str:
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
    path = REPO / "experiments" / "context-cache" / "client.py"
    spec = importlib.util.spec_from_file_location("ctx_client_g1", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load chat client from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module.ChatClient


def acquire_lock(path: Path, timeout_s: float) -> tuple[object, float]:
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
            "unit": "G1",
            "pid": os.getpid(),
            "acquired_utc": utc_now(),
            "waited_s": round(time.monotonic() - started, 1),
            "scope": "G1 isolated fork break-cost; hold for the whole run",
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
        json.dump({"unit": "G1", "pid": os.getpid(), "released_utc": utc_now()}, handle)
        handle.flush()
        os.fsync(handle.fileno())
        fcntl.flock(handle, fcntl.LOCK_UN)
    finally:
        handle.close()


def load_existing() -> dict[tuple[str, str, int], dict]:
    out: dict[tuple[str, str, int], dict] = {}
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
        out[(str(row["arm"]), str(row.get("session")), int(row["turn"]))] = row
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


def config_sha256() -> str:
    return hashlib.sha256(CONFIG_PATH.read_bytes()).hexdigest()


def chat_with_refusal_guard(client, messages, *, max_tokens, thinking, stream, timeout, refusal_state):
    # Returns client result; raises RuntimeError on 3 consecutive refusals.
    while True:
        try:
            result = client.chat(
                messages,
                max_tokens=max_tokens,
                thinking=thinking,
                stream=stream,
                timeout=timeout,
            )
            refusal_state["streak"] = 0
            return result
        except Exception as exc:  # noqa: BLE001
            text = str(exc).lower()
            if "refus" in text or "connect" in text or "connection" in text:
                refusal_state["streak"] += 1
                refusal_state["last_error"] = str(exc)
                if refusal_state["streak"] >= 3:
                    raise RuntimeError(
                        f"endpoint refused 3 consecutive attempts: {exc}"
                    ) from exc
                time.sleep(5.0)
                continue
            refusal_state["streak"] = 0
            raise


def run(lock_note: str = "") -> int:
    started = time.monotonic()
    scenario, turns = load_slice()
    preamble = scenario["preamble"]
    schedule = compaction_schedule(preamble, turns)
    salts: dict[tuple[str, str], str] = {}
    for spec in ARMS:
        arm = str(spec["arm"])
        for i, session in enumerate(SESSIONS):
            salts[(arm, session)] = make_salt(int(spec["seed_base"]) + i * 1000)

    existing = load_existing()
    total_rows = len(ARMS) * len(SESSIONS) * TURNS
    requests = 0
    live_rows: list[dict] = []
    compaction_events: list[dict] = []
    anomalies: list[dict] = []
    refusal_state = {"streak": 0, "last_error": ""}

    for (arm, session), salt in salts.items():
        for row in existing.values():
            if row.get("arm") == arm and row.get("session") == session and row.get("salt") != salt:
                raise RuntimeError(f"arm {arm} session {session}: resumed row salt {row['salt']!r} != {salt!r}")

    client = load_chat_client()()
    done = len(existing)
    cfg_sha = config_sha256()
    print(
        f"G1 start: schedule={schedule} rows_existing={done}/{total_rows} "
        f"salts={salts} corpus={CORPUS_PATH.relative_to(REPO)} config_sha256={cfg_sha}",
        flush=True,
    )

    for session in SESSIONS:
        for spec in ARMS:
            arm = str(spec["arm"])
            policy = str(spec["policy"])
            compaction = spec["compaction"]
            salt = salts[(arm, session)]
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
                        {**event, "unit": "G1", "arm": arm, "session": session, "turn": turn_no, "salt": salt}
                    )
                messages = render(
                    RenderPolicy.NAIVE_APPEND,
                    chain,
                    preamble=preamble,
                    volatile={},
                    salt=salt,
                )
                key = (arm, session, turn_no)
                if key in existing:
                    prior = existing[key]
                    if bool(prior.get("scheduled_compaction")) != scheduled:
                        raise RuntimeError(
                            f"arm {arm} session {session} turn {turn_no}: resumed scheduled_compaction="
                            f"{prior.get('scheduled_compaction')} != computed {scheduled}"
                        )
                    continue

                prompt, cached, completion, ttft, wall, status, text = chat_with_refusal_guard(
                    client,
                    messages,
                    max_tokens=MAX_TOKENS,
                    thinking=False,
                    stream=True,
                    timeout=120.0,
                    refusal_state=refusal_state,
                )
                requests += 1
                warm_retry = False
                warm1_prompt = None
                warm1_cached = None
                if cached == 0 and prompt > 0 and prompt % 64 == 0 and turn_no > 1 and not scheduled:
                    warm1_prompt, warm1_cached = prompt, cached
                    prompt, cached, completion, ttft, wall, status, text = chat_with_refusal_guard(
                        client,
                        messages,
                        max_tokens=MAX_TOKENS,
                        thinking=False,
                        stream=True,
                        timeout=120.0,
                        refusal_state=refusal_state,
                    )
                    requests += 1
                    warm_retry = True
                    anomalies.append(
                        {
                            "kind": "warm_twice",
                            "arm": arm,
                            "session": session,
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
                        f"arm {arm} session {session}: cold-start contract violated -- turn 1 cached={cached}"
                    )
                if turn_no > 1 and cached == 0 and not scheduled:
                    anomalies.append(
                        {
                            "kind": "unexpected_zero_cache",
                            "arm": arm,
                            "session": session,
                            "turn": turn_no,
                            "prompt_tokens": prompt,
                        }
                    )

                uncached = max(0, prompt - cached)
                ts_utc = utc_now()
                row = {
                    "unit": "G1",
                    "cell": f"G1/{arm}",
                    "arm": arm,
                    "session": session,
                    "policy": policy,
                    "turn": turn_no,
                    "turns_total": TURNS,
                    "salt": salt,
                    "stack": STACK,
                    "config_id": CONFIG_ID,
                    "config_sha256": cfg_sha,
                    "prompt_tokens": prompt,
                    "cached_tokens": cached,
                    "uncached": uncached,
                    "completion_tokens": completion,
                    "ttft_ms": round(ttft, 3),
                    "wall_ms": round(wall, 3),
                    "status": status,
                    "scheduled_compaction": scheduled,
                    "is_break_turn": bool(scheduled),
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
                    "ts_utc": ts_utc,
                    "ts": ts_utc,
                }
                append_row(row)
                live_rows.append(row)
                done += 1
                pct = 100.0 * done / total_rows
                print(
                    f"PROGRESS {done}/{total_rows} ({pct:.1f}%) session={session} arm={arm} turn={turn_no} "
                    f"prompt={prompt} cached={cached} uncached={uncached} "
                    f"status={status} chain_est={total_est(chain)}",
                    flush=True,
                )

    elapsed = time.monotonic() - started
    rows = g1_analyze.load_rows(ROWS_PATH)
    payload = g1_analyze.analyze(rows)
    rows_sha = hashlib.sha256(ROWS_PATH.read_bytes()).hexdigest()
    warm_retries = sum(1 for r in rows if r.get("warm_retry"))
    requests_total = len(rows) + warm_retries
    stamps = sorted(str(r.get("ts_utc") or "") for r in rows if r.get("ts_utc"))
    payload["digest"] = {
        "rows_sha256": rows_sha,
        "n_rows": len(rows),
        "n_rows_by_arm": {arm: len([r for r in rows if r["arm"] == arm]) for arm, _ in [("E", None), ("F", None)]},
        "n_rows_by_session": {s: len([r for r in rows if str(r.get("session")) == s]) for s in SESSIONS},
        "requests_live": requests_total,
        "requests_this_run": requests,
        "requests_cap": REQUEST_CAP,
        "first_row_ts": stamps[0] if stamps else None,
        "last_row_ts": stamps[-1] if stamps else None,
        "elapsed_s": round(elapsed, 1),
        "compaction_schedule": schedule,
        "summariser": (
            f"deterministic offline stub: whitespace-collapsed folded text "
            f"truncated to {SUMMARY_CHARS} chars (~188 est tokens)"
        ),
        "renderer": RenderPolicy.NAIVE_APPEND.value,
        "budget_tokens": BUDGET_TOKENS,
        "keep_last": KEEP_LAST,
        "corpus": str(CORPUS_PATH.relative_to(REPO)),
        "corpus_scenario": scenario["id"],
        "corpus_sha256": hashlib.sha256(CORPUS_PATH.read_bytes()).hexdigest(),
        "salts": {f"{a}:{s}": salts[(a, s)] for a, s in salts},
        "config_sha256": cfg_sha,
        "config_id": CONFIG_ID,
        "stack": STACK,
    }
    # fix n_rows_by_arm keys to be strings
    payload["digest"]["n_rows_by_arm"] = {
        arm: len([r for r in rows if r["arm"] == arm]) for arm in ("E", "F")
    }
    write_json_atomic(ANALYSIS_PATH, payload)

    events = {
        "unit": "G1",
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
        f"breaks={s['prefix_break_events']}"
    )


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
        "command": ".venv/bin/python experiments/context-cache/cells/G1/g1_cell.py",
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
                "rows": f"{digest['n_rows']}/264 rows "
                f"{digest['n_rows_by_arm']} in experiments/context-cache/cells/G1/rows.jsonl",
                "rows_sha256": digest["rows_sha256"],
                "first_row_ts": digest.get("first_row_ts"),
                "last_row_ts": digest.get("last_row_ts"),
                "compaction_schedule": digest["compaction_schedule"],
                "per_arm": "; ".join(per_arm_line(payload, arm) for arm in ("E", "F")),
                "prefix_breaks": "; ".join(
                    f"{arm}: {payload['arms'][arm]['prefix_break_events']} at {payload['arms'][arm]['prefix_break_turns']}"
                    for arm in ("E", "F")
                ),
                "per_break_uncached_cost": payload.get("per_break_uncached_cost"),
                "kill_condition": payload.get("kill_condition"),
                "u15_1_700x_survives_decomposition": payload.get("u15_1_700x_survives_decomposition"),
            }
        )
        c = payload["claim"]
        answer = {
            "question": c["question"],
            "answer": c["answer"],
            "ratio_E_over_F_per_break_mean": c["ratio_E_over_F_per_break_mean"],
            "statement": c["statement"],
            "u15_1_700x_survives_decomposition": c["u15_1_700x_survives_decomposition"],
        }
        evidence["claim"] = json.dumps(c)

    handoff = {
        "unit": "G1",
        "status": status,
        "artifacts": [
            "experiments/context-cache/cells/G1/rows.jsonl",
            "experiments/context-cache/cells/G1/events.jsonl",
            "experiments/context-cache/cells/G1/analysis.json",
            "experiments/context-cache/cells/G1/g1_cell.py",
            "experiments/context-cache/cells/G1/g1_analyze.py",
            "orchestration/units/G1.md",
        ],
        "evidence": evidence,
        "blocker": blocker,
        "next_unit_hint": (
            "Verifier: re-run `.venv/bin/python "
            "experiments/context-cache/cells/G1/g1_analyze.py` offline and compare "
            "analysis.json rows_sha256; check E/F break at turns 18 and 35 in all 3 "
            "sessions; check per-break uncached costs and kill condition."
        ),
        "write_paths": [
            "experiments/context-cache/cells/G1/**",
            "orchestration/handoffs/G1.json",
            "orchestration/units/G1.md",
        ],
        "answer": answer,
        "lock": lock_note,
    }
    tmp = CELL_DIR / "G1.handoff.tmp"
    tmp.write_text(json.dumps(handoff, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, HANDOFF_PATH)
    print(f"handoff: {HANDOFF_PATH.relative_to(REPO)} status={status}", flush=True)
    if payload is not None:
        print(per_arm_line(payload, "E"))
        print(per_arm_line(payload, "F"))
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
    except Exception as exc:  # noqa: BLE001
        print(f"FAILED: {type(exc).__name__}: {exc}", flush=True)
        rows = g1_analyze.load_rows(ROWS_PATH) if ROWS_PATH.exists() else []
        payload = g1_analyze.analyze(rows) if rows else None
        if payload is not None:
            payload["digest"] = {
                "rows_sha256": hashlib.sha256(ROWS_PATH.read_bytes()).hexdigest(),
                "n_rows": len(rows),
                "n_rows_by_arm": {arm: len([r for r in rows if r["arm"] == arm]) for arm in ("E", "F")},
                "n_rows_by_session": {s: len([r for r in rows if str(r.get("session")) == s]) for s in SESSIONS},
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
                "config_sha256": config_sha256(),
                "config_id": CONFIG_ID,
                "stack": STACK,
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
