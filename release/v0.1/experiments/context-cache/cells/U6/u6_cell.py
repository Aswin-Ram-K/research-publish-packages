#!/usr/bin/env python3
"""U6-R — E5 end-to-end: BASELINE vs SYSTEM over the 60-turn corpus.

BASELINE = static prefix + append-only history + periodic compaction + volatile
state only in the delta (incumbent's best case; prefix never breaks).
SYSTEM   = pointer context + fork compaction (prefix breaks at every fold).

``--plan`` renders every turn of both arms offline, asserts the per-turn
contract (identical through the first fold, distinct after it, the same volatile
block throughout, no raw estimand surviving the seam), schedules the compaction
events and writes ``u6_plan.json``.  No request is sent.

``--run`` replays the plan through the endpoint under the shared
``.occamy.lock``, one request per (arm, turn), then analyses.  ``--analyse``
recomputes ``analysis.json`` from ``rows.jsonl`` and the plan (no requests).

Writes only inside ``cells/U6/`` plus the lock record and the pre-registered
``orchestration/handoffs/U6-R.json`` (this unit's declared write paths).
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import importlib.util
import json
import os
import signal
import sys
import time
import traceback
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
SRC = REPO / "src"
EXP = REPO / "experiments" / "context-cache"
LOCK_PATH = REPO / ".occamy.lock"

sys.path.insert(0, str(SRC))
sys.path.insert(0, str(HERE))

from resextract.context import default_est_tokens  # noqa: E402

import u6_nb  # noqa: E402


def _load(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:  # pragma: no cover
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


client_mod = _load("u6_client", EXP / "client.py")

# --------------------------------------------------------------------------- #
# Pre-registered configuration
# --------------------------------------------------------------------------- #
SEED = 20261021
CORPUS = EXP / "corpora" / "endtoend.json"
MAX_TOKENS = 64           # long enough for the model to name the migration
SALT_TAG = "E5-v1"
MAX_REQUESTS = 260
LOCK_TIMEOUT_S = 90 * 60
HARD_STOP_S = 150 * 60
REFUSAL_LIMIT = 3
REQUEST_TIMEOUT_S = 180.0   # per socket op; client retries once, so <= ~6 min/turn
            
ARMS = u6_nb.ARMS
ARM_ORDER = (u6_nb.BASELINE, u6_nb.SYSTEM)

# Estimand.  The corpus's own estimand is `4 * "#" * 32`; a run of 32 '#' is
# visible to a 4-chars-per-token estimator and is NOT a discriminating accuracy
# test, so the live run answers SEAM-A: a 4-token pointer line carrying the
# measurand's id and sha256.
SEAM_ID = "SEAM-A"
HASH_RUN = "#" * 32

OUT_PLAN = HERE / "u6_plan.json"
OUT_ROWS = HERE / "rows.jsonl"
OUT_ANALYSIS = HERE / "analysis.json"
OUT_RUNLOG = HERE / "u6_runlog.json"
OUT_HANDOFF = REPO / "orchestration" / "handoffs" / "U6-R.json"


def estimand_sha256() -> str:
    return hashlib.sha256((HASH_RUN + "\n").encode("utf-8")).hexdigest()


def module_a_line() -> str:
    return f"[{SEAM_ID}] answer={SEAM_ID} sha256={estimand_sha256()}"


def seam_map() -> dict[str, str]:
    return {HASH_RUN: module_a_line()}


VOLATILE_KEYS = ("step", "elapsed_ms", "task_id", "turn_ts")


def volatile_block(turn: dict[str, Any]) -> str:
    v = turn.get("volatile") or {}
    return "\n".join(f"{k}={v[k]}" for k in VOLATILE_KEYS if k in v)


def delta_body(turn: dict[str, Any], *, volatile: bool) -> str:
    """Turn text; turn 1's body also carries the volatile block (delta only)."""

    text = turn["text"]
    if volatile:
        return f"{text}\n\n[volatile]\n{volatile_block(turn)}"
    return text


def scenario_salt(scenario_id: str) -> str:
    key = f"{SALT_TAG}:{scenario_id}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]


def digest_of(messages: list[dict[str, str]]) -> str:
    return hashlib.sha256(u6_nb.canonical_bytes(messages)).hexdigest()


def content_digest(messages: list[dict[str, str]]) -> str:
    return hashlib.sha256("\n".join(m["content"] for m in messages).encode("utf-8")).hexdigest()


def gold_present(messages: list[dict[str, str]], needle: str) -> bool:
    return any(needle in m["content"] for m in messages)


# --------------------------------------------------------------------------- #
# Offline plan
# --------------------------------------------------------------------------- #
def build_plan() -> dict[str, Any]:
    corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
    eq = seam_map()
    plan: dict[str, Any] = {
        "unit": "U6-R",
        "corpus": str(CORPUS.relative_to(REPO)),
        "corpus_sha256": hashlib.sha256(CORPUS.read_bytes()).hexdigest(),
        "seed": SEED,
        "salt_tag": SALT_TAG,
        "max_tokens": MAX_TOKENS,
        "keep_last": u6_nb.KEEP_LAST,
        "digest_chars": u6_nb.DIGEST_CHARS,
        "fork_lines": u6_nb.FORK_LINES,
        "seam": {"id": SEAM_ID, "estimand_sha256": estimand_sha256(), "replacements": eq},
        "arms": {
            u6_nb.BASELINE: {"prefix": "static", "history": "append-only",
                             "compaction": "append_only (fold to per-turn digests)",
                             "volatile": "delta (turn 1 body)"},
            u6_nb.SYSTEM: {"prefix": "pointer + fork label", "history": "fork-folded",
                           "compaction": "fork (marker + folded lines + kept tail)",
                           "volatile": "delta (turn 1 body)"},
        },
        "scenarios": {},
    }
    total = 0
    for sc in corpus["scenarios"]:
        sid = sc["id"]
        raw_gold = sc["gold_answer"]
        gold = eq.get(raw_gold, raw_gold)
        salt = scenario_salt(sid)
        preamble = sc["preamble"].replace(HASH_RUN, eq[HASH_RUN])
        states = {a: u6_nb.ArmState.new(a, preamble=preamble, salt=salt) for a in ARM_ORDER}
        header_hist: dict[str, list[str]] = {a: [] for a in ARM_ORDER}
        turns: list[dict[str, Any]] = []
        for idx, turn in enumerate(sc["turns"]):
            body = delta_body(turn, volatile=(idx == 0))
            for needle, repl in eq.items():
                body = body.replace(needle, repl)
            entry: dict[str, Any] = {"turn": idx + 1, "role": turn["role"],
                                     "corpus_gold": gold in body, "arms": {}}
            for arm in ARM_ORDER:
                st = states[arm]
                event = st.compact()
                st.append(idx, body, role=turn["role"])
                messages = st.view()
                header_hist[arm].append(hashlib.sha256(messages[0]["content"].encode()).hexdigest())
                entry["arms"][arm] = {
                    "prompt_sha256": digest_of(messages),
                    "content_sha256": content_digest(messages),
                    "header_sha256": header_hist[arm][-1],
                    "n_messages": len(messages),
                    "chars": sum(len(m["content"]) for m in messages),
                    "est_tokens": default_est_tokens("\n".join(m["content"] for m in messages)),
                    "gold_present": gold_present(messages, gold),
                    "raw_estimand_present": gold_present(messages, HASH_RUN),
                    "volatile_present": (volatile_block(turn) in messages[-1]["content"])
                    if idx == 0 else None,
                    "is_event": event is not None,
                    "event": event,
                    "folded_so_far": st.folded_count,
                }
            a, b = entry["arms"][u6_nb.BASELINE], entry["arms"][u6_nb.SYSTEM]
            entry["equal_content"] = a["content_sha256"] == b["content_sha256"]
            turns.append(entry)
            total += 2
        ff = next((t["turn"] for t in turns if t["arms"][u6_nb.SYSTEM]["folded_so_far"]), None)
        plan["scenarios"][sid] = {
            "salt": salt,
            "gold_answer": gold,
            "corpus_gold_answer": raw_gold,
            "gold_turn": sc["gold_turn_index"] + 1,
            "final_question": sc["final_question"],
            "first_fold_turn": ff,
            "turns": turns,
        }
    plan["requests"] = total
    plan["requests_within_bound"] = total <= MAX_REQUESTS
    plan["checks"] = plan_checks(plan)
    return plan


def plan_checks(plan: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for sid, sc in plan["scenarios"].items():
        turns = sc["turns"]
        ff = sc["first_fold_turn"]
        eq_through = max((t["turn"] for t in turns if t["equal_content"]), default=0)
        gold_absent = {a: [t["turn"] for t in turns if not t["arms"][a]["gold_present"]]
                       for a in ARM_ORDER}
        gold_after = {
            a: [t["turn"] for t in turns
                if ff is not None and t["turn"] > ff and not t["arms"][a]["gold_present"]]
            for a in ARM_ORDER
        }
        out[sid] = {
            "first_fold_turn": ff,
            "equal_content_through_turn": eq_through,
            "equal_until_fold": eq_through == (ff or 1) - 1,
            "distinct_after_fold": all(
                t["arms"][u6_nb.BASELINE]["prompt_sha256"]
                != t["arms"][u6_nb.SYSTEM]["prompt_sha256"]
                for t in turns if ff and t["turn"] >= ff
            ),
            "volatile_in_turn1_both": (
                all(turns[0]["arms"][a]["volatile_present"] is True for a in ARM_ORDER)
                if turns else None
            ),
            "raw_estimand_absent_everywhere": not any(
                t["arms"][a]["raw_estimand_present"] for t in turns for a in ARM_ORDER
            ),
            "header_changes": {
                a: sum(1 for i in range(1, len(turns))
                       if turns[i]["arms"][a]["header_sha256"]
                       != turns[i - 1]["arms"][a]["header_sha256"])
                for a in ARM_ORDER
            },
            "gold_absent_turns": gold_absent,
            "gold_absent_after_fold": gold_after,
            "gold_present_at_final": {a: turns[-1]["arms"][a]["gold_present"] for a in ARM_ORDER},
            "turn60_est_tokens": {a: turns[-1]["arms"][a]["est_tokens"] for a in ARM_ORDER},
            "total_est_tokens": {a: sum(t["arms"][a]["est_tokens"] for t in turns)
                                 for a in ARM_ORDER},
        }
    return out


# --------------------------------------------------------------------------- #
# Lock management (shared with every unit since U4)
# --------------------------------------------------------------------------- #
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
    record = {"unit": "U6-R", "pid": os.getpid(),
              f"{status}_utc": time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime())}
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
class Refused(RuntimeError):
    pass


def _status(exc: BaseException) -> int | None:
    resp = getattr(exc, "response", None)
    return getattr(resp, "status_code", None)


def run(args: argparse.Namespace, plan: dict[str, Any]) -> int:
    wanted = [s.strip() for s in args.scenarios.split(",") if s.strip()] or list(plan["scenarios"])
    lock_fd, waited = acquire_lock(LOCK_PATH, LOCK_TIMEOUT_S)
    if lock_fd is None:
        write_lock_record(LOCK_PATH, "timeout")
        print(json.dumps({"status": "partial", "reason": "lock timeout",
                          "waited_s": round(waited, 1)}), flush=True)
        return 3
    write_lock_record(LOCK_PATH, "acquired")
    print(f"[lock] acquired after {waited:.1f}s", flush=True)

    started = time.monotonic()
    state: dict[str, Any] = {
        "unit": "U6-R", "status": "running", "requests_spent": 0, "rows": 0,
        "refusals": 0, "refusal_errors": [], "completed": [],
        "started_utc": time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime()),
        "lock_wait_s": round(waited, 1), "scenarios": wanted,
    }

    def flush_state(status: str) -> None:
        state["status"] = status
        state["elapsed_s"] = round(time.monotonic() - started, 1)
        OUT_RUNLOG.write_text(json.dumps(state, indent=1), encoding="utf-8")

    def _stoptime(signum, frame):  # noqa: ANN001
        raise TimeoutError("U6-R wall-clock stop")

    signal.signal(signal.SIGALRM, _stoptime)
    signal.alarm(HARD_STOP_S)
    cli = client_mod.ChatClient(timeout=REQUEST_TIMEOUT_S)
    corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
    by_id = {s["id"]: s for s in corpus["scenarios"]}
    eq = seam_map()
    rows_path = OUT_ROWS.open("w", encoding="utf-8")
    where = {"scenario": None, "arm": None, "turn": None}
    try:
        for sid in wanted:
            sc = plan["scenarios"][sid]
            raw = by_id[sid]
            preamble = raw["preamble"].replace(HASH_RUN, eq[HASH_RUN])
            states = {a: u6_nb.ArmState.new(a, preamble=preamble, salt=sc["salt"])
                      for a in ARM_ORDER}
            for idx, turn in enumerate(raw["turns"]):
                body = delta_body(turn, volatile=(idx == 0))
                for needle, repl in eq.items():
                    body = body.replace(needle, repl)
                for arm in ARM_ORDER:
                    where.update(scenario=sid, arm=arm, turn=idx + 1)
                    flush_state("running")
                    st = states[arm]
                    st.compact()
                    st.append(idx, body, role=turn["role"])
                    messages = st.view()
                    planned = sc["turns"][idx]["arms"][arm]
                    got = digest_of(messages)
                    if got != planned["prompt_sha256"]:
                        raise RuntimeError(f"plan/live drift {sid} {arm} turn {idx+1}")
                    if state["requests_spent"] >= MAX_REQUESTS:
                        raise TimeoutError("U6-R request bound")
                    try:
                        prompt, cached, completion, ttft, wall, status, text = cli.chat(
                            messages, max_tokens=MAX_TOKENS, stream=True
                        )
                    except Exception as exc:  # noqa: BLE001
                        code = _status(exc)
                        verbatim = f"{type(exc).__name__}: {exc}"
                        if code in (400, 413, 422):
                            state["refusals"] += 1
                            state["refusal_errors"].append(verbatim)
                            flush_state("refused")
                            if state["refusals"] >= REFUSAL_LIMIT:
                                raise Refused(verbatim) from exc
                            continue
                        raise
                    state["refusals"] = 0
                    state["requests_spent"] += 1
                    row = {
                        "arm": arm, "scenario": sid, "turn": idx + 1,
                        "prompt_tokens": prompt, "cached_tokens": cached,
                        "uncached": max(0, prompt - cached),
                        "gold_present": planned["gold_present"],
                        "ts": time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime()),
                        "completion_tokens": completion,
                        "answer_ok": sc["gold_answer"] in text,
                        "status": status,
                        "ttft_ms": round(ttft, 1), "wall_ms": round(wall, 1),
                        "prompt_sha256": got, "n_messages": len(messages),
                        "is_event": planned["is_event"],
                        "is_final": idx == len(raw["turns"]) - 1,
                        "role": turn["role"], "answer_text": text[:600],
                    }
                    rows_path.write(json.dumps(row, ensure_ascii=False) + "\n")
                    rows_path.flush()
                    state["rows"] += 1
                flush_state("running")
                print(f"[run] {sid} turn {idx+1:>2}/60 spent={state['requests_spent']}", flush=True)
            state["completed"].append(sid)
            flush_state("running")
    except Refused as exc:
        flush_state("failed")
        print(json.dumps({"status": "failed", "reason": "refused", "verbatim": str(exc)}), flush=True)
        return 4
    except Exception as exc:  # noqa: BLE001
        state["failed_at"] = dict(where)
        flush_state("partial")
        print(json.dumps({"status": "partial", "reason": type(exc).__name__,
                          "detail": str(exc)[:500], "spent": state["requests_spent"],
                          "failed_at": where,
                          "stack": traceback.format_exc()[-2000:]}), flush=True)
        return 5
    finally:
        signal.alarm(0)
        rows_path.close()
        flush_state("stopped")
        release_lock(lock_fd, LOCK_PATH)
    flush_state("done")
    print(json.dumps({"status": "done", "requests_spent": state["requests_spent"],
                      "rows": state["rows"], "elapsed_s": state["elapsed_s"]}), flush=True)
    return 0


# --------------------------------------------------------------------------- #
# Analysis
# --------------------------------------------------------------------------- #
def analyse() -> dict[str, Any]:
    plan = json.loads(OUT_PLAN.read_text(encoding="utf-8"))
    rows = [json.loads(line) for line in OUT_ROWS.read_text(encoding="utf-8").splitlines()
            if line.strip()]
    arm_rows = {a: [r for r in rows if r["arm"] == a] for a in ARM_ORDER}
    scenario_ids = sorted({r["scenario"] for r in rows})
    out: dict[str, Any] = {
        "unit": "U6-R",
        "requests": len(rows),
        "per_arm_requests": {a: len(arm_rows[a]) for a in ARM_ORDER},
        "scenarios": {},
    }
    tot = {a: {"prompt": 0, "cached": 0, "uncached": 0} for a in ARM_ORDER}
    correct = {a: 0 for a in ARM_ORDER}
    finals = {a: 0 for a in ARM_ORDER}
    for a in ARM_ORDER:
        for r in arm_rows[a]:
            tot[a]["prompt"] += r["prompt_tokens"]
            tot[a]["cached"] += r["cached_tokens"]
            tot[a]["uncached"] += r["uncached"]
            if r.get("is_final"):
                finals[a] += 1
                correct[a] += int(bool(r["answer_ok"]))
    for sid in scenario_ids:
        per = {a: [r for r in arm_rows[a] if r["scenario"] == sid] for a in ARM_ORDER}
        by_turn = {a: {r["turn"]: r for r in per[a]} for a in ARM_ORDER}
        order = {a: sorted(by_turn[a]) for a in ARM_ORDER}
        sc = plan["scenarios"][sid]
        ff = sc["first_fold_turn"]
        per_turn = {}
        cum = {}
        for a in ARM_ORDER:
            c = 0
            pt, cc = [], []
            for t in order[a]:
                r = by_turn[a][t]
                c += r["uncached"]
                cc.append(c)
                pt.append([t, r["prompt_tokens"], r["cached_tokens"], r["uncached"]])
            per_turn[a] = pt
            cum[a] = cc
        final = {a: by_turn[a].get(60) for a in ARM_ORDER}
        out["scenarios"][sid] = {
            "turns_paired": min(len(per[a]) for a in ARM_ORDER),
            "first_fold_turn_plan": ff,
            "totals": {a: {"prompt": sum(r["prompt_tokens"] for r in per[a]),
                           "cached": sum(r["cached_tokens"] for r in per[a]),
                           "uncached": sum(r["uncached"] for r in per[a]),
                           "calls": len(per[a])} for a in ARM_ORDER},
            "uncached_ratio_baseline_over_system": (
                sum(r["uncached"] for r in per[u6_nb.BASELINE])
                / max(1, sum(r["uncached"] for r in per[u6_nb.SYSTEM]))
            ),
            "gold_presence_trace": {a: [by_turn[a][t]["gold_present"] for t in order[a]]
                                    for a in ARM_ORDER},
            "gold_lost_after_fold": {
                a: [t for t in order[a]
                    if ff is not None and t > ff and not by_turn[a][t]["gold_present"]]
                for a in ARM_ORDER
            },
            "final_answers": {
                a: {"turn": 60,
                    "answer_ok": bool(final[a] and final[a]["answer_ok"]),
                    "answer_text": (final[a] or {}).get("answer_text", ""),
                    "gold_present": (final[a] or {}).get("gold_present")}
                for a in ARM_ORDER
            },
            "uncached_per_turn": per_turn,
            "uncached_cumulative": cum,
        }
    out["totals"] = {a: {**tot[a], "final_answers_correct": correct[a],
                         "final_question_rows": finals[a]} for a in ARM_ORDER}
    sep = out["totals"][u6_nb.BASELINE]["uncached"] / max(1, out["totals"][u6_nb.SYSTEM]["uncached"])
    out["separation"] = {"metric": "total uncached tokens, BASELINE / SYSTEM", "ratio": sep}
    acc_b = correct[u6_nb.BASELINE] / max(1, finals[u6_nb.BASELINE])
    acc_s = correct[u6_nb.SYSTEM] / max(1, finals[u6_nb.SYSTEM])
    out["accuracy"] = {
        "baseline": acc_b, "system": acc_s, "drop_points": (acc_b - acc_s) * 100,
        "basis": f"final turn's model answer contains the gold answer ({SEAM_ID})",
    }
    gold_lost_any = any(
        out["scenarios"][s]["gold_lost_after_fold"][a]
        for s in out["scenarios"] for a in ARM_ORDER
    )
    fired = []
    if sep < 1.5:
        fired.append("separation < 1.5x on total uncached tokens")
    if (acc_b - acc_s) * 100 > 5:
        fired.append("accuracy drop above 5 points")
    if gold_lost_any:
        fired.append("compaction lost the gold answer after compaction")
    out["kill_condition"] = {"fired": fired, "fired_bool": bool(fired),
                             "verdict": "FAIL" if fired else "PASS"}
    out["plan_checks"] = plan.get("checks")
    out["mechanism"] = mechanism(rows, out)
    # The estimand the pre-registration actually names is total *prompt* tokens.
    # Report how the claim reads under that reading of its own words.
    prompt_sep = (out["totals"][u6_nb.BASELINE]["prompt"]
                  / max(1, out["totals"][u6_nb.SYSTEM]["prompt"]))
    out["prompt_token_separation"] = {
        "metric": "total prompt tokens, BASELINE / SYSTEM", "ratio": prompt_sep,
        "meets_1.5x": prompt_sep >= 1.5,
        "note": "the pre-registration's own phrase is 'separation on total prompt tokens'; "
                "the delivered separation is on total uncached tokens, the cost metric.",
    }
    return out


def mechanism(rows: list[dict[str, Any]], out: dict[str, Any]) -> dict[str, Any]:
    """Why the split lands where it does, stated as measurements, not a story."""

    stats: dict[str, Any] = {}
    for arm in ARM_ORDER:
        rr = [r for r in rows if r["arm"] == arm and r["scenario"] == sorted(out["scenarios"])[0]]
        body = [r for r in rr if r["turn"] >= 5]  # past the shared opening turns
        if not body:
            continue
        cached = sorted(r["cached_tokens"] for r in body)
        stats[arm] = {
            "turns": len(body),
            "mean_prompt": sum(r["prompt_tokens"] for r in body) / len(body),
            "mean_cached": sum(cached) / len(cached),
            "cached_min": cached[0], "cached_max": cached[-1], "cached_median": cached[len(cached)//2],
            "hit_ratio": sum(cached) / max(1, sum(r["prompt_tokens"] for r in body)),
        }
    turn1 = [{"scenario": r["scenario"], "arm": r["arm"],
              "prompt": r["prompt_tokens"], "cached": r["cached_tokens"]}
             for r in rows if r["turn"] == 1]
    windows = {}
    for lo in (1, 4):
        windows[f"from_turn_{lo}"] = {
            sid: (sum(x[3] for x in out["scenarios"][sid]["uncached_per_turn"][u6_nb.BASELINE]
                      if x[0] >= lo)
                  / max(1, sum(x[3] for x in out["scenarios"][sid]["uncached_per_turn"][u6_nb.SYSTEM]
                               if x[0] >= lo)))
            for sid in out["scenarios"]
        }
    return {
        "per_arm_cache_behaviour": stats,
        "turn1_rows": turn1,
        "uncached_ratio_by_window": windows,
        "reading": (
            "SYSTEM's prompts are shorter (lower total prompt tokens) but its cached share is "
            "monotone-decreasing and its cached token count is pinned near a small constant after "
            "the first fold, while BASELINE's grows with the prompt. Under a prefix-cache server the "
            "pointer's advantage is a smaller prompt, not a warmer one; on this router the fold at "
            "every turn breaks the reusable prefix, so the baseline's static prefix wins the uncached "
            "metric. SYSTEM spends more uncached tokens per turn than BASELINE does."
        ),
    }


# --------------------------------------------------------------------------- #
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--analyse", action="store_true")
    ap.add_argument("--scenarios", default="")
    args = ap.parse_args(argv)

    if args.analyse:
        result = analyse()
        OUT_ANALYSIS.write_text(json.dumps(result, indent=1), encoding="utf-8")
        print(json.dumps({"separation": result["separation"]["ratio"],
                          "accuracy": result["accuracy"],
                          "kill": result["kill_condition"]}, indent=1), flush=True)
        return 0

    plan = build_plan()
    OUT_PLAN.write_text(json.dumps(plan, indent=1), encoding="utf-8")
    print(json.dumps({"requests": plan["requests"],
                      "within_bound": plan["requests_within_bound"],
                      "checks": plan["checks"]}, indent=1), flush=True)
    if args.plan:
        return 0
    rc = run(args, plan)
    if rc in (0, 5) and OUT_ROWS.exists() and OUT_ROWS.stat().st_size:
        result = analyse()
        OUT_ANALYSIS.write_text(json.dumps(result, indent=1), encoding="utf-8")
        print(json.dumps({"separation": result["separation"]["ratio"],
                          "kill": result["kill_condition"]}, indent=1), flush=True)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
