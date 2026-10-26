#!/usr/bin/env python3
"""U10 continuation: phases 2 and 3 only (phase 1's rows are already on disk).

Phase 1 stopped on a `send()` signature bug after finishing every length cell,
so re-running the whole driver would spend another 65 requests.  This runs just
the delay sweep and the insert test at the worst cell found by phase 1
(L=1088, chars=4621, variant=0, tail=14) and writes u10_rows_p23.jsonl.

Budget: MAX_REQUESTS=55 here + 65 (phase 1) + 39 (pilot) = 159 live requests.
"""
from __future__ import annotations

import functools
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import u10_cell as cell  # noqa: E402

cell.MAX_REQUESTS = 55
cell.PHASE_CAP = {"p1": 0, "p2": 40, "p3": 15}
cell.SEQ["seed"] = cell.SEED_BASE + 500_000  # never reuse a phase-1 marker

L, CHARS, VARIANT, TAIL = 1088, 4621, 0, 14

chat = cell.client_mod.ChatClient()
cell.SEND = functools.partial(
    chat.chat, max_tokens=2, thinking=False, stream=True, timeout=180.0
)

cell.phase2(L, CHARS, VARIANT, TAIL)
cell.phase3(L, CHARS, VARIANT, TAIL)

out = HERE / "u10_rows_p23.jsonl"
with open(out, "w", encoding="utf-8") as fh:
    for row in cell.ROWS:
        fh.write(json.dumps(row) + "\n")
print("rows", len(cell.ROWS), "requests", cell.USED)
json.dump({"requests": cell.USED, "notes": cell.NOTES, "rows": len(cell.ROWS),
           "cell": {"length": L, "chars": CHARS, "variant": VARIANT, "tail": TAIL}},
          open(HERE / "u10_runlog_p23.json", "w"), indent=2)
