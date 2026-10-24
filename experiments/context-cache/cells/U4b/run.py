#!/usr/bin/env python3
"""U4b-R2: per-branch prefix identity vs one shared prefix. Token counts only; no flock."""
from __future__ import annotations

import json
import os
import sys
import traceback

CELL = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(CELL, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "experiments", "context-cache"))
from resextract.context.salt import make_salt, salted  # noqa: E402
import client as occ  # noqa: E402

N, K = 46, 8
SEEDS = {"A": 41001, "B": 41002, "C": 41003}
ROWS = os.path.join(CELL, "rows.jsonl")
HANDOFF = os.path.join(ROOT, "orchestration", "handoffs", "U4b.json")
WRITE = ["experiments/context-cache/cells/U4b/run.py",
         "experiments/context-cache/cells/U4b/rows.jsonl",
         "orchestration/handoffs/U4b.json", "orchestration/units/U4b.md"]


def shared_body():
    return "".join("Sentence about repository work item %d: the maintainer reviewed the "
                   "pending diff, noted the flaky test in the integration suite, and "
                   "scheduled a follow-up review for the next release cycle.\n" % i
                   for i in range(N))


def delta(k):
    return ("Delta payload for branch %d records the query plan, the failing assertion, "
            "the fixture corpus, the log excerpt, the reproduction command, the expected "
            "duration, the review checklist and the rollback note for this shard. It also "
            "notes the operator that owns the shard and the date the snapshot was taken.\n"
            % k)


def tag(k):
    return "[BRANCH-%d]\n" % k


def arm_prompts(arm, P):
    if arm == "A":                       # shared P, tag at the front of the delta
        return [P + tag(k) + delta(k) for k in range(1, K + 1)]
    if arm == "B":                       # tag prepended to P -> nothing shared
        return [tag(k) + P + delta(k) for k in range(1, K + 1)]
    return [P + delta(k) + "\n" + tag(k) for k in range(1, K + 1)]   # C: tag at end


def run_arm(arm):
    salt = make_salt(SEEDS[arm])
    P = salted(salt, shared_body())
    rows = []
    for k, text in enumerate(arm_prompts(arm, P), start=1):
        prompt, cached, _c, ttft, _w, status, _t = occ.chat(
            [{"role": "user", "content": text}], max_tokens=2, thinking=False, stream=True)
        rows.append({"arm": arm, "branch": k, "salt": salt, "chars": len(text),
                     "prompt_tokens": prompt, "cached_tokens": cached,
                     "uncached_tokens": prompt - cached, "cached_gt0": cached > 0,
                     "ttft_ms": round(ttft, 1), "status": status})
    return len(P), rows


def totals(rows):
    ok = [r for r in rows if r["status"] == 200]
    tp = sum(r["prompt_tokens"] for r in ok)
    tu = sum(r["uncached_tokens"] for r in ok)
    return {"requests": len(ok), "total_prompt": tp, "total_uncached": tu,
            "ratio_uncached": round(tu / tp, 4) if tp else None,
            "branches_2_8_cached": sum(1 for r in ok if r["branch"] > 1 and r["cached_gt0"]),
            "branches_2_8_total": 7,
            "cached_by_branch": [r["cached_tokens"] for r in ok]}


def main():
    all_rows, per_arm, plen = [], {}, {}
    for arm in "ABC":
        plen[arm], rows = run_arm(arm)
        all_rows += rows
        per_arm[arm] = totals(rows)
        print(arm, json.dumps(per_arm[arm]), flush=True)
    with open(ROWS, "w", encoding="utf-8") as fh:
        fh.writelines(json.dumps(r) + "\n" for r in all_rows)
    tA, tB, tC = (per_arm[a]["total_uncached"] for a in "ABC")
    B_A, C_A = (round(x / tA, 4) if tA else None for x in (tB, tC))
    verdict = {"fanout_claim_supported": bool(B_A and B_A >= 1.5),
               "placement_discipline_not_pointer": bool(C_A and abs(C_A - 1.0) <= 0.10),
               "arm_A_shared_prefix_did_hit": per_arm["A"]["branches_2_8_cached"] > 0}
    summary = {"per_arm": per_arm, "len_P_chars": plen,
               "expect_cached_64chars": {a: 64 * (plen[a] // 64) for a in "ABC"},
               "expect_cached_64tok": {a: 64 * int(plen[a] / 256) for a in "ABC"},
               "B_over_A": B_A, "C_over_A": C_A}
    with open(HANDOFF, "w", encoding="utf-8") as fh:
        json.dump({"unit": "U4b", "status": "done", "artifacts": WRITE[:2],
                   "evidence": {"per_arm": per_arm, "B_over_A": B_A, "C_over_A": C_A,
                                "len_P_chars": plen, "requests_used": len(all_rows),
                                "verdict": verdict,
                                "commands": [".venv/bin/python "
                                             "experiments/context-cache/cells/U4b/run.py"]},
                   "blocker": "", "next_unit_hint": json.dumps(verdict),
                   "write_paths": WRITE}, fh, indent=2)
    print("SUMMARY " + json.dumps(summary), flush=True)


if __name__ == "__main__":
    try:
        main()
    except BaseException:
        tb = traceback.format_exc()
        print(tb, file=sys.stderr)
        with open(HANDOFF, "w", encoding="utf-8") as fh:
            json.dump({"unit": "U4b", "status": "blocked", "artifacts": [],
                       "evidence": {"traceback": tb[-3000:]},
                       "blocker": tb.strip().splitlines()[-1],
                       "next_unit_hint": "inspect traceback; no lock was used",
                       "write_paths": [WRITE[0], WRITE[2]]}, fh, indent=2)
        sys.exit(1)
