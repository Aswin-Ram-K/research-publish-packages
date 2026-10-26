"""W3-COLLECT main -- G0 gate, 284-row battery, grid probe, on dense 9B / SGLang.

Phases (each runnable alone; the runner refuses duplicate rows):
  --phase gate     2 requests   (G0 gate, raw usage mandatory)
  --phase grid     26 requests  (13 boundary targets x cold/repeat)
  --phase battery  284 requests (4 arms x 71 servable turns at budget 32768)
  --phase probe    24 requests  (4 WIN-SGL discrimination targets x 3 reps)

Total 336 of a 400 cap.  The lock is held for every phase.
"""

from __future__ import annotations

import argparse
import json
import time

import w3collect_cell as C


RETRY_FAILED = False


def gate_usage_ok(row: dict) -> bool:
    raw = row.get("usage_raw")
    if not isinstance(raw, dict):
        return False
    details = raw.get("prompt_tokens_details")
    return isinstance(details, dict) and "cached_tokens" in details


def phase_gate(runner: C.Runner) -> dict:
    messages = [
        {"role": "system", "content": "You are a cache-probe assistant. Answer in one word."},
        {"role": "user", "content": " ".join(retention_ok())},
    ]
    tok = C.count_tokens(messages)
    r1 = runner.send("gate", messages, salt="gate-w3collect", rep=0, note="identical-1",
                     allow_failed_retry=RETRY_FAILED)
    r2 = runner.send("gate", messages, salt="gate-w3collect", rep=1, note="identical-2",
                     allow_failed_retry=RETRY_FAILED)
    gate = {
        "tokenize_count": tok,
        "served_prompt_tokens": r1["prompt_tokens"],
        "offset": (r1["prompt_tokens"] - tok) if tok else 0,
        "rep0_cached": r1["cached_tokens"],
        "rep1_cached": r2["cached_tokens"],
        "usage_rep0": r1["usage_raw"],
        "usage_rep1": r2["usage_raw"],
        "usage_source_rep1": r2["usage_source"],
        # G0: the cached-token count must be PRESENT in the server's own usage
        # object.  An absent key and a cold 0 are indistinguishable downstream,
        # so absence is a STOP, not a zero.
        "cached_tokens_key_present": gate_usage_ok(r2),
        "gate_pass": bool(gate_usage_ok(r2) and r2["cached_tokens"] > 0),
    }
    print(f"GATE pass={gate['gate_pass']} rep1_cached={gate['rep1_cached']} "
          f"key_present={gate['cached_tokens_key_present']} offset={gate['offset']}", flush=True)
    return gate


def retention_ok():
    return ["retention"] * 3100


def phase_grid(runner: C.Runner) -> list:
    out = []
    for idx, target in enumerate(C.GRID_TARGETS):
        salt = C.make_salt(7100 + idx)
        msgs = C.make_grid_messages(target, salt, index=True)
        cold = runner.send("grid", msgs, salt=salt, target_L=target, rep=0, note="cold",
                           allow_failed_retry=RETRY_FAILED)
        rep = runner.send("grid", msgs, salt=salt, target_L=target, rep=1, note="repeat-1",
                          allow_failed_retry=RETRY_FAILED)
        out.append({"target_L": target, "L": cold["prompt_tokens"],
                    "cold_cached": cold["cached_tokens"], "cached": rep["cached_tokens"],
                    "status": rep["status"]})
        print(f"GRID target={target} L={cold['prompt_tokens']} cold={cold['cached_tokens']} "
              f"hot={rep['cached_tokens']}", flush=True)
    return out


def phase_probe(runner: C.Runner) -> list:
    out = []
    for idx, target in enumerate(C.PROBE_TARGETS):
        salt = C.make_salt(7400 + idx)
        msgs = C.make_grid_messages(target, salt, index=True)
        rows = [runner.send("grid", msgs, salt=salt, target_L=target, rep=rep,
                            note=f"probe-rep{rep}", allow_failed_retry=RETRY_FAILED)
                    for rep in (0, 1, 2)]
        out.append({"target_L": target, "L": rows[0]["prompt_tokens"],
                    "cached": [r["cached_tokens"] for r in rows]})
        print(f"PROBE target={target} L={rows[0]['prompt_tokens']} "
              f"cached={[r['cached_tokens'] for r in rows]}", flush=True)
    return out


def build_battery_plan(offset: int) -> dict:
    band = C.BAND
    preamble, turns = C.load_turns(band["planned_turns"])
    schedule = C.compaction_schedule(preamble, turns, band["budget"], None)
    salts = {s["arm"]: C.make_salt(int(s["seed"])) for s in C.ARMS}
    per_arm = {}
    per_turn_L = {}
    for spec in C.ARMS:
        arm = str(spec["arm"])
        base = spec["compaction"]
        salt = salts[arm]
        chain = [C.StateNode.create(preamble, "invariant")]
        crossed = False
        msgs_by_turn = []
        lens = []
        for turn_no, turn in enumerate(turns, 1):
            chain = [*chain, C.StateNode.create(turn["text"], "delta", parent=chain[-1],
                                                turn=turn_no)]
            scheduled = bool(base is not None and turn_no in schedule)
            if arm == "H" and scheduled:
                crossed = True
            if arm == "A" and scheduled:
                pol = C.CompactionPolicy.APPEND_NOTE
            elif arm == "H":
                pol = C.CompactionPolicy.APPEND_NOTE if not crossed else C.CompactionPolicy.SUMMARISE_IN_PLACE
            else:
                pol = base
            if scheduled and pol is not None:
                chain, _ = C.compact(chain, pol, keep_last=C.KEEP_LAST, summarizer=C.summarise,
                                     est_tokens=C.default_est_tokens)
            messages = C.render(C.RenderPolicy.NAIVE_APPEND, chain, preamble=preamble,
                                volatile={}, salt=salt)
            msgs_by_turn.append(messages)
            lens.append(C.count_tokens(messages))
        per_arm[arm] = {"lens": lens, "messages": msgs_by_turn, "salt": salt}
        per_turn_L[arm] = lens
    ok_turns = []
    for t in range(band["planned_turns"]):
        vals = [per_turn_L[a][t] for a in per_turn_L]
        ok_turns.append(None if any(v is None for v in vals) else max(vals) + offset)
    n_servable = 0
    for t, L in enumerate(ok_turns, 1):
        if L is not None and L <= band["prompt_limit"]:
            n_servable = t
        else:
            break
    plan = {
        "unit": "W3-COLLECT", "planned_turns": band["planned_turns"],
        "servable_turns": n_servable, "prompt_limit": band["prompt_limit"],
        "context_length": C.CONTEXT_LENGTH, "budget": band["budget"], "offset": offset,
        "per_turn_max_L": ok_turns, "schedule": schedule, "salts": salts,
        "reason": f"turns {n_servable + 1}..{band['planned_turns']} dropped: rendered prompt "
                  f"would exceed prompt_limit {band['prompt_limit']}",
    }
    C.write_json_atomic(C.LOGS / f"battery-plan-{band['budget']}.json", plan)
    print(f"PLAN servable={n_servable}/{band['planned_turns']} "
          f"L@N={ok_turns[n_servable - 1] if n_servable else None} schedule={schedule}",
          flush=True)
    return {"plan": plan, "per_arm": per_arm}


def progress(turn_no: int, spec: dict, n: int) -> None:
    """Live progress for the human panel (best effort, never fatal)."""
    import os
    d = os.environ.get("DSH_PROGRESS_DIR")
    task = os.environ.get("W3_PROGRESS_TASK", "w3collect-battery")
    if not d:
        return
    try:
        done = PROGRESS_SEEN[0] + 1
        PROGRESS_SEEN[0] = done
        pct = int(100 * done / (4 * n))
        with open(f"{d}/{task}.jsonl", "a", encoding="utf-8") as h:
            h.write(json.dumps({"v": 1, "task": task, "state": "running", "pct": pct,
                                "msg": f"arm {spec['arm']} turn {turn_no}/{n}"}) + "\n")
    except Exception:
        pass


PROGRESS_SEEN = [0]


def phase_battery(runner: C.Runner, offset: int) -> dict:
    built = build_battery_plan(offset)
    plan = built["plan"]
    n = plan["servable_turns"]
    for spec in C.ARMS:
        arm = str(spec["arm"])
        msgs_by_turn = built["per_arm"][arm]["messages"]
        salt = built["per_arm"][arm]["salt"]
        for turn_no in range(1, n + 1):
            row = runner.send("battery", msgs_by_turn[turn_no - 1], salt=salt, arm=arm,
                              turn=turn_no, policy=str(spec["policy"]), rep=0,
                              depth=C.BAND["depth"], budget=C.BAND["budget"],
                              note=f"turns_total={n}", allow_failed_retry=RETRY_FAILED)
            progress(turn_no, spec, n)
            if row["status"] != 200:
                print(f"BATTERY ERROR arm={arm} turn={turn_no} status={row['status']} "
                      f"{row.get('error', '')[:200]}", flush=True)
                if row["status"] in (400, 404):
                    break
    return {"servable_turns": n, "rows": 4 * n, "schedule_len": len(plan["schedule"])}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", required=True, choices=["gate", "grid", "probe", "battery"])
    ap.add_argument("--offset", type=int, default=None)
    ap.add_argument("--allow-failed-retry", action="store_true",
                    help="re-send a row whose recorded attempt had no usage object")
    args = ap.parse_args()

    runner = C.Runner()
    global RETRY_FAILED
    RETRY_FAILED = args.allow_failed_retry
    started = time.monotonic()
    handle = None
    try:
        handle, waited = C.acquire_lock(C.LOCK_PATH, C.LOCK_TIMEOUT_S, f"W3-COLLECT {args.phase}")
        print(f"lock: acquired after {waited:.1f}s", flush=True)
        summary = {"unit": "W3-COLLECT", "phase": args.phase, "endpoint": C.BASE_URL,
                   "lock_wait_s": round(waited, 1), "started_utc": C.utc_now()}
        if args.phase == "gate":
            gate = phase_gate(runner)
            summary["gate"] = gate
            summary["offset"] = gate["offset"]
            C.write_json_atomic(C.LOGS / "gate.json", summary)
            return 0 if gate["gate_pass"] else 3
        offset = args.offset
        if offset is None:
            gf = C.LOGS / "gate.json"
            offset = json.loads(gf.read_text()).get("offset", 0) if gf.exists() else 0
        summary["offset"] = offset
        started_at = started
        if args.phase == "grid":
            summary["grid"] = phase_grid(runner)
        elif args.phase == "probe":
            summary["probe"] = phase_probe(runner)
        elif args.phase == "battery":
            summary["battery"] = phase_battery(runner, offset)
        summary["requests_this_run"] = runner.requests
        summary["rows_total"] = runner.n_rows()
        summary["elapsed_s"] = round(time.monotonic() - started_at, 1)
        summary["finished_utc"] = C.utc_now()
        C.write_json_atomic(C.LOGS / f"{args.phase}-summary.json", summary)
        print(f"DONE phase={args.phase} requests={runner.requests} rows={runner.n_rows()} "
              f"elapsed={summary['elapsed_s']}s", flush=True)
        return 0
    except Exception as exc:
        print(f"FAILED: {type(exc).__name__}: {exc}", flush=True)
        return 1
    finally:
        if handle is not None:
            C.release_lock(handle, f"W3-COLLECT {args.phase}")


if __name__ == "__main__":
    raise SystemExit(main())
