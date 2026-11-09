# UNIT `ARM-TREATMENTS-FIRE`

**Objective.** Make the three treatments the grid is supposed to compare actually fire, and prove
it offline with non-zero row markers, before any request is spent. Zero inference.

**Bound.** ≤28 tool calls, 0 requests. Killed condition: a live cell against :8012/:8014.

**Write paths.** `measure/ARM-TREATMENTS.{json,md}`, `tools/arm_treatments_probe.py`,
`longrun/experiments/ptr-engine/longrun/tests/test_arm_treatments.py`, `orchestration/units/ARM-TREATMENTS-FIRE.md`,
`orchestration/handoffs/ARM-TREATMENTS-FIRE.json`, `orchestration/journals/ARM-TREATMENTS-FIRE.jsonl`.

**Findings.**
1. The card's cited lines (`run_longrun.py:436/:441`) are stale; hooks are at `:1063` (grow
   eviction), `:1080` (compact digest), `:1113` (lease reopen).
2. Compaction has **no turn-row marker** — only a separate `kind=="digest"` row (`:2027`). Field
   gap, not a test gap.
3. Lease reopen is **not a token predicate**: it fires on `t in fixture["lease_reopen_turns"]`,
   and all 12 runtime fixtures omit that key. The 64k wall is irrelevant to arm 3.
4. At the frozen wall every growth arm is `unreachable at 48 turns` (G4 grow T94, G4 compact
   T847, stage1 grow T1654, stage1 compact T571, v3 grow T1046, v4 grow T1010).
5. All three fire offline once `wall_tokens=3838` and `lease_reopen_turns=[23,40]` are declared:
   rows with `evicted=1`, `kind="digest"`, `lease=2` produced by the production writer `make_row`.
6. Price: firing grid at 48 turns = 798 vs A\* 792 (+6 requests, +0.76 %). N=56 would be 930
   (+138) and is needed only for the *second* registered wall.

**Status.** `partial` — measurement and specification complete; the fixture field
`lease_reopen_turns` and a fixture-derived `expected_digests` are the implementation card.
