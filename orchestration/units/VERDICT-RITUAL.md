# VERDICT-RITUAL — make every card able to earn a PASS

**Card:** 5b8c6ec4-a9e2-4d32-983f-037c46b327e7 · execution d026f43f-25f3-4a4e-a95c-a6e5ab48c4aa
**Bound:** ≤24 tool calls, 0 inference requests. OFFLINE: zero inference.

## Why
The 16:06:55Z sweep closed three executions `FAIL no-verdict no-sha` although all three delivered
(`PROJECTION-MODE`, `STOP-REASON-HOLES`, `OPERATOR-BRIEF-2`). The gate derives its verdict from a
`{command, exitCode, sha}` row and no card wrote one. `failed` stands at 104 and most of it is this.

## What this card changes
- `orchestration/VERDICT-RITUAL.md` — the diagnosis of the three (command, exit code, sha each) and the
  two-step ritual a card runs last.
- `experiments/ptr-engine/tools/verdict_payload.py` — runs one acceptance command, prints the record payload.
- `experiments/ptr-engine/longrun/tests/test_verdict_payload.py` — its acceptance test.
- `orchestration/units/TEMPLATE.md` — created; §CLOSING carries the two steps and the declared-gap rule.

## Acceptance command
`python3 experiments/ptr-engine/longrun/tests/test_verdict_payload.py`

## Evidence
See `orchestration/handoffs/VERDICT-RITUAL.json` and `orchestration/journals/VERDICT-RITUAL.jsonl`.
