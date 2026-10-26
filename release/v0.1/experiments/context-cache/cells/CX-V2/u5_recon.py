#!/usr/bin/env python3
"""CX-V2: offline replay of U5's equal-information + retention claims.

Rebuilds every cell (190 cases x {shallow/shared, deep/baseline,
deep/summarise, deep/fork}) from the unit's own corpus builder and compares

  * prompt sha256 rebuild vs the row U5 actually sent (faithfulness), and
  * POINTER vs NAIVE_APPEND canonical bytes for the same chain.

No network.  Reads cells/U5/u5_pin.json + experiments/second-labeller-190/
cases.json + the live renderer.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CELLS = HERE.parent
REPO = HERE.parents[3]
sys.path.insert(0, str(REPO / "src"))

spec = importlib.util.spec_from_file_location("cx_u5", CELLS / "U5" / "u5_cells.py")
u5 = importlib.util.module_from_spec(spec)
sys.modules["cx_u5"] = u5
spec.loader.exec_module(u5)

cases = u5.load_cases()
pinned = u5.load_pinned()
print(f"cases {len(cases)}; pinned sessions {len(pinned['sessions'])}; "
      f"pinned cases.json sha256 {pinned.get('inputs', {}).get('cases.json', 'n/a')}")

rows = [json.loads(l) for l in (CELLS / "U5" / "u5_raw.jsonl").read_text().splitlines() if l.strip()]
live = {(r["case_id"], r["depth"], r["condition"]): r for r in rows}

same_bytes = 0
diff_cells = []
rebuilt = 0
sha_mismatch = []
ret_bad = []
for i, case in enumerate(cases):
    for depth, cond in (("shallow", "shared"), ("deep", "baseline"),
                        ("deep", "summarise"), ("deep", "fork")):
        a = u5.build_cell(case, i, depth, cond, pinned, policy=u5.RenderPolicy.POINTER)
        b = u5.build_cell(case, i, depth, cond, pinned, policy=u5.RenderPolicy.NAIVE_APPEND)
        rebuilt += 1
        if u5.canonical(a["messages"]) == u5.canonical(b["messages"]):
            same_bytes += 1
        else:
            diff_cells.append((case["id"], depth, cond,
                               len(u5.canonical(a["messages"])),
                               len(u5.canonical(b["messages"]))))
        row = live[(case["id"], depth, cond)]
        sha = u5.sha(u5.concat(b["messages"]))
        if sha != row["prompt_sha256"]:
            sha_mismatch.append((case["id"], depth, cond))
        ret = u5.retention(b, case)
        for key in ("gold", "question", "options"):
            if bool(ret[key]) != bool(row["retained"][key]):
                ret_bad.append((case["id"], depth, cond, key, ret[key], row["retained"][key]))

print(f"rebuilt cells: {rebuilt}")
print(f"POINTER == NAIVE_APPEND byte-identical: {same_bytes}/{rebuilt}")
print(f"  differing cells: {len(diff_cells)} {diff_cells[:3]}")
print(f"rebuilt prompt_sha256 matches the sent row: {rebuilt - len(sha_mismatch)}/{rebuilt}")
print(f"retention flags reproduce: {rebuilt*3 - len(ret_bad)}/{rebuilt*3}")
print(f"  mismatches: {ret_bad[:5]}")
gold = {}
for depth, cond in (("shallow", "shared"), ("deep", "baseline"),
                    ("deep", "summarise"), ("deep", "fork")):
    gold[(depth, cond)] = sum(1 for c in cases
                              if u5.retention(u5.build_cell(c, cases.index(c), depth, cond, pinned), c)["gold"])
print("gold-line retained (rebuilt):", gold)
