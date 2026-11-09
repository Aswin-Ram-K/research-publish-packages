# UNIT REQUEST-LEDGER

**Purpose.** Make the request budget a number a machine computes from row files instead of a
hand-carried "≈466 of 4,320".

**Hard bound.** ≤26 tool calls, zero inference requests, no network, no `git`.

**Deliverables (write paths, exactly):**
- `experiments/ptr-engine/tools/request_ledger.py` — counter + cap gate
- `experiments/ptr-engine/longrun/tests/test_request_ledger.py` — red→green, offline fixtures
- `docs/REQUEST-LEDGER.md` — counting rule + reconciliation vs ≈466
- `experiments/ptr-engine/measure/REQUEST-LEDGER.json` — computed report
- `orchestration/units/REQUEST-LEDGER.md`, `orchestration/handoffs/REQUEST-LEDGER.json`,
  `orchestration/journals/REQUEST-LEDGER.jsonl`

**Counting rule (closed vocabulary).** One request per row representing an inference call.
`kind in {turn, tool-followup}` counts. Rows marked `billed: false`, `followup_suppressed`, or
`served_from == "prompt"` do not count. A row whose schema cannot decide (no `kind`, no marker)
counts and is flagged `assumed_billed`.

**Exit codes.** 0 within budget · 4 would exceed · 3 usage error · 5 unreadable/unparseable row file.

**Kill condition.** If the corpus cannot be parsed, report `partial` with the failing file named.
