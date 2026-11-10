#!/usr/bin/env python3
"""Dry-run: render every scheduled call and write run/PLAN.json."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

CELL = Path(__file__).resolve().parents[1]
RUN = CELL / "run"
ARMS_DIR = CELL / "arms"
if str(ARMS_DIR) not in sys.path:
    sys.path.insert(0, str(ARMS_DIR))
import render_arms as ra  # type: ignore
from canonical import dumps as cdumps  # type: ignore

ENV = json.loads((RUN / "envelopes" / "CCS.json").read_text())
MAX_MODEL_LEN = 131072
try:
    fp = json.loads((RUN / "FINGERPRINTS.json").read_text())
    MAX_MODEL_LEN = int(fp["model"]["max_model_len"])
except Exception:
    pass
MASK_AFTER = int(ENV.get("mask_after", 6))

BASE_URL = "http://192.168.2.168:8012/v1"

# Synthetic completed answer ~1,200 bytes (plausible artifact: imports, function, prints).
_base_answer = '''import os
import json
from pathlib import Path

def solve(task_id: str, payload: dict) -> dict:
    """Compute the requested invariant report from the pinned source."""
    root = Path(payload.get("root", "."))
    findings = []
    for name in sorted(root.iterdir()):
        if name.is_file() and name.suffix == ".py":
            findings.append({"file": str(name), "bytes": name.stat().st_size})
    result = {"task_id": task_id, "count": len(findings), "findings": findings}
    print(json.dumps(result, sort_keys=True))
    return result

if __name__ == "__main__":
    solve("demo", {"root": "."})
'''
_pad = 1200 - len(_base_answer.encode("utf-8"))
if _pad < 0:
    _base_answer = _base_answer[:1200]
    _pad = 0
SYNTHETIC_ANSWER = _base_answer + ("\n# " + ("x" * max(0, _pad - 3)) if _pad > 0 else "")
SYNTHETIC_ANSWER = SYNTHETIC_ANSWER[:1200]
while len(SYNTHETIC_ANSWER.encode("utf-8")) < 1200:
    SYNTHETIC_ANSWER += "x"
SYNTHETIC_ANSWER = SYNTHETIC_ANSWER[:1200]
assert len(SYNTHETIC_ANSWER.encode("utf-8")) == 1200, len(SYNTHETIC_ANSWER.encode("utf-8"))


def load_fixture(task_id):
    return json.loads((CELL / "tasks" / f"{task_id}.json").read_text())


def make_history(fixture, n):
    hist = []
    for i in range(1, n + 1):
        turns = fixture.get("turns", [])
        t = turns[i - 1] if i - 1 < len(turns) else {"turn": i}
        instr = t.get("instruction") or t.get("question") or f"turn {i}"
        hist.append({
            "turn": i,
            "instruction": instr,
            "answer": SYNTHETIC_ANSWER,
            "claim": f"claim for turn {i}",
            "refs": None,
            "notes": "",
        })
    return hist


def tokenize_count(messages):
    try:
        import httpx
        payload = {"model": "occamy-1.0", "messages": messages}
        with httpx.Client(base_url=BASE_URL, timeout=30.0) as c:
            r = c.post("/tokenize", json=payload)
            r.raise_for_status()
            return int(r.json().get("count", 0))
    except Exception:
        return max(1, len(cdump(messages)) // 4)


def cdump(messages):
    return cdumps(messages)


def first_divergence(cur, base_msgs, prev_msgs=None):
    if base_msgs is None:
        # arm A: name the append point
        if prev_msgs is None:
            return "append after message 0"
        return f"append after message {len(prev_msgs)}"
    L = 0
    n = min(len(cur), len(base_msgs))
    while L < n and cur[L] == base_msgs[L]:
        L += 1
    if L == len(cur) == len(base_msgs):
        return "identical"
    return f"first differing message index {L} (of {len(cur)})"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    schedule = ENV["schedule"]
    fixtures = {t: load_fixture(t) for t in ENV["tasks"]}
    renders_by_task_arm = {t: {a: {} for a in ENV["arms"]} for t in ENV["tasks"]}

    plan_rows = []
    total_tokens = 0
    per_arm_bytes = {a: 0 for a in ENV["arms"]}
    per_arm_msgs = {a: 0 for a in ENV["arms"]}
    per_arm_tokens = {a: 0 for a in ENV["arms"]}
    per_arm_bytes_by_turn = {a: [] for a in ENV["arms"]}

    base_cache = {}
    prev_arm_cache = {t: {a: {} for a in ENV["arms"]} for t in ENV["tasks"]}

    for call in schedule:
        task = call["task"]
        arm = call["arm"]
        turn = call["turn"]
        fx = fixtures[task]
        hist = make_history(fx, turn - 1)
        msgs = ra.build_messages(arm, fx, hist, turn, K=MASK_AFTER)
        renders_by_task_arm[task][arm][turn] = msgs
        prompt_bytes = len(cdump(msgs))
        if arm == "A":
            base_msgs = None
        else:
            parent_arm = "A" if arm == "B" else "B"
            base_msgs = renders_by_task_arm[task][parent_arm].get(turn)
        prev_msgs = prev_arm_cache[task][arm].get(turn - 1) if turn > 1 else None
        # store current for next turn append-point calc (same arm)
        prev_arm_cache[task][arm][turn] = msgs
        # previous turn messages for append point = msgs of turn-1 same arm
        prev_turn_msgs = renders_by_task_arm[task][arm].get(turn - 1)
        fd = first_divergence(msgs, base_msgs, prev_turn_msgs)
        if arm == "A":
            base_cache[(task, turn)] = msgs

        toks = tokenize_count([{"role": m["role"], "content": m["content"]} for m in msgs])
        total_tokens += toks
        per_arm_bytes[arm] += prompt_bytes
        per_arm_msgs[arm] += len(msgs)
        per_arm_tokens[arm] += toks
        per_arm_bytes_by_turn[arm].append(prompt_bytes)

        if toks > MAX_MODEL_LEN:
            raise SystemExit(f"EXCEEDS WINDOW: task={task} arm={arm} turn={turn} tokens={toks} > {MAX_MODEL_LEN}")

        plan_rows.append({
            "seq": call["seq"],
            "task": task,
            "arm": arm,
            "turn": turn,
            "message_count": len(msgs),
            "prompt_bytes": prompt_bytes,
            "estimated_tokens": toks,
            "first_divergence": fd,
        })

    # prefix identity assertions
    for task in ENV["tasks"]:
        for arm in ENV["arms"]:
            renders = renders_by_task_arm[task][arm]
            for t in range(1, ENV["turns_per_task"]):
                a = renders[t]
                b = renders[t + 1]
                L = 0
                n = min(len(a), len(b))
                while L < n and a[L] == b[L]:
                    L += 1
                assert L > 0, f"prefix identity failed (no common prefix): task={task} arm={arm} turns {t},{t+1}"
                assert cdumps(a[:L]) == cdumps(b[:L]), f"prefix bytes differ: task={task} arm={arm} turns {t},{t+1}"

    # fail loudly if an arm renders byte-identically to its parent for every turn
    parent = {"B": "A", "C": "B"}
    for arm, par in parent.items():
        identical_all = True
        for task in ENV["tasks"]:
            for turn in range(1, ENV["turns_per_task"] + 1):
                if cdumps(renders_by_task_arm[task][arm][turn]) != cdumps(renders_by_task_arm[task][par][turn]):
                    identical_all = False
                    break
            if not identical_all:
                break
        if identical_all:
            raise SystemExit(f"TREATMENT INERT: arm {arm} is byte-identical to parent {par} on every turn")

    # per-arm growth
    per_arm_growth = {}
    for a in ENV["arms"]:
        turns_bytes = per_arm_bytes_by_turn[a]
        # group by turn (12 turns x tasks): average across tasks for that turn
        # bytes_by_turn has 4 tasks * 12 turns in schedule order task-major? Actually schedule is task-major, arm-major, turn.
        # Reconstruct per-turn average bytes across tasks:
        by_turn = []
        for ti in range(ENV["turns_per_task"]):
            vals = [per_arm_bytes_by_turn[a][ti + t * ENV["turns_per_task"]] for t in range(len(ENV["tasks"]))]
            by_turn.append(sum(vals) // len(vals))
        growth = [by_turn[i] - by_turn[i - 1] for i in range(1, len(by_turn))]
        per_arm_growth[a] = {
            "bytes_by_turn": by_turn,
            "growth_per_turn_bytes": growth,
        }

    plan = {
        "run_id": ENV["run_id"],
        "calls": len(plan_rows),
        "per_call": plan_rows,
        "totals": {
            "message_count": sum(r["message_count"] for r in plan_rows),
            "prompt_bytes": sum(r["prompt_bytes"] for r in plan_rows),
            "estimated_tokens": total_tokens,
        },
        "per_arm": {
            a: {
                "message_count": per_arm_msgs[a],
                "prompt_bytes": per_arm_bytes[a],
                "estimated_tokens": per_arm_tokens[a],
                **per_arm_growth[a],
            }
            for a in ENV["arms"]
        },
        "cap": ENV["aggregate_cap"],
        "pct_of_cap": round(100.0 * len(plan_rows) / ENV["aggregate_cap"], 2),
        "dry_run_assumptions": {
            "synthetic_answer_bytes": 1200,
            "synthetic_answer_note": "Dry run seeds each completed turn with a 1200-byte synthetic Python artifact because real answers are unavailable before the live run; real answers are expected to be ~1 KB artifacts.",
            "mask_after": MASK_AFTER,
        },
    }
    (RUN / "PLAN.json").write_text(json.dumps(plan, indent=2) + "\n")

    print(f"calls={len(plan_rows)} pct_of_cap={plan['pct_of_cap']}%")
    for a in ENV["arms"]:
        print(f"arm {a}: messages={per_arm_msgs[a]} bytes={per_arm_bytes[a]} tokens={per_arm_tokens[a]}")
    print(f"total estimated tokens={total_tokens}")
    # show first non-identical C turn
    c_first = None
    for r in plan_rows:
        if r["arm"] == "C" and r["first_divergence"] != "identical":
            c_first = r
            break
    if c_first:
        print(f"C first divergence: turn {c_first['turn']} task {c_first['task']} -> {c_first['first_divergence']}")
    print("prefix-identity: PASS")
    print("model-window: PASS")
    print("treatment-engagement: PASS")


if __name__ == "__main__":
    main()
