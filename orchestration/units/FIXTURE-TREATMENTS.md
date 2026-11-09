# UNIT `FIXTURE-TREATMENTS`

**Purpose.** Make the three treatments (grow eviction, compact digest, lease reopen) reachable at
the frozen 48-turn horizon by changing the **fixture and the row schema** — never the horizon and
never a threshold "until it fits". OFFLINE: zero inference requests.

**Bound.** ≤30 tool calls, 0 requests. **Status:** done (see handoff).

**Write paths (exactly).** `experiments/ptr-engine/longrun/tasks-v6/LR-01.v8.json`,
`experiments/ptr-engine/longrun/run_longrun.py`,
`experiments/ptr-engine/longrun/tests/test_treatments_fire.py`, `docs/TREATMENTS.md`,
`experiments/ptr-engine/measure/FIXTURE-TREATMENTS.json`, `orchestration/units/FIXTURE-TREATMENTS.md`,
`orchestration/handoffs/FIXTURE-TREATMENTS.json`, `orchestration/journals/FIXTURE-TREATMENTS.jsonl`.
`cell.py` is owned by `GATE-OPERAND-VALIDATION` and was NOT touched; the precondition is exported
as `check_treatments()` for it.

**Deliverables.** v8 fixture (wall 3838 + per-arm 10616 + lease [23,40] + derived
`expected_digests`), `digest_at` turn-row marker, launch precondition in `run_longrun.py`, tests
red→green, `docs/TREATMENTS.md`, evidence json.

**Kill condition.** If 48 turns cannot reach a hook even at the declared wall: say which arm and
what it needs, do not raise the wall silently. — Applied: 3838 is 10 tokens below v8's own first
prompt (3848), recorded in the fixture's `wall_tokens_basis` and in `docs/TREATMENTS.md`; the growth
arms use the per-arm field (10616) instead.
