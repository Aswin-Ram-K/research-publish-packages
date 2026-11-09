# RECLAIM-ACCEPTANCE

**Purpose:** re-measure three cards charged with the cap-gate red, without re-doing their work.
**Bound:** ≤20 tool calls, 0 requests, offline. **Verdict:** partial (2 of 3 reclaimable; 1 blocked by a second foreign red).
**Write paths:** `experiments/ptr-engine/measure/RECLAIM-ACCEPTANCE.json`, `docs/RECLAIM-ACCEPTANCE.md`,
`orchestration/units/RECLAIM-ACCEPTANCE.md`, `orchestration/handoffs/RECLAIM-ACCEPTANCE.json`,
`orchestration/journals/RECLAIM-ACCEPTANCE.jsonl`.

## Result at HEAD f17663d1

| card | recorded acceptance command | exit today | class | row |
|---|---|---|---|---|
| SEAM-TEST-RED | `python3 -m unittest discover -s experiments/ptr-engine/longrun/tests -p 'test_*.py'` | 1 | blocked-by-foreign-red | none |
| CLAIM-ROW-STAMP | `python3 experiments/ptr-engine/longrun/tests/test_claim_rows.py` | 0 | reclaimable (already PASS) | none needed |
| WIRE-CAP-GATE | `python3 -m unittest discover -s experiments/ptr-engine/longrun/tests -p 'test_cap_gate.py' -v` | 0 | reclaimable | PASS recorded |

Census: **2 reclaimable / 0 still-red-own-work / 0 not-runnable / 1 blocked-by-foreign-red**.

## Finding

Exactly **one** of the three was a false FAIL caused by the stale `experiments/ptr-engine/longrun/tests/test_cap_gate.py:205` assertion
(SEAM-TEST-RED). CLAIM-ROW-STAMP was already verified PASS (its `partial` was a handoff self-report) and
WIRE-CAP-GATE failed `no-verdict` with no command at all. That assertion therefore does not explain
`failed=104`; the next reclaim target is the governance red that now blocks SEAM-TEST-RED
(`test_verdict_ritual` → FIXTURE-GENERATIONS has no verdict row).

## Discipline

No card work product edited; only two new verdict rows' worth of re-measurement added (one row, for
WIRE-CAP-GATE); SEAM-TEST-RED cannot be re-rowed while exit ≠ 0. Details: `docs/RECLAIM-ACCEPTANCE.md`.
