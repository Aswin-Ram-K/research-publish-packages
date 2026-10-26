# PLANT-REACHABILITY

**Purpose.** Prove or refute, offline, that the 64-fact never entered the `pointer-stable` arm's
prompt (grader phrase "no 64 and it was never in context"), per arm and per checkpoint turn.

**Bound.** Max 22 tool calls; if the runner could not be driven to a prompt at T12 within 8 calls,
report `PMOT-UNREACHABLE` and still deliver the re-grade. Used 18. No fallback needed.

**Write paths.** `experiments/ptr-engine/longrun/tools/prompt_at_turn.py`,
`experiments/ptr-engine/measure/REACHABILITY-MATRIX.md`,
`experiments/ptr-engine/measure/rows-longrun-v3-2026-10-26.grade-v3-final.json`,
`/tmp/**`, this card, its handoff.

**Kill condition.** Any HTTP attempt is a card failure. Enforced structurally: five network entry
points patched to raise AssertionError before the runner is driven; observed
`network_attempts=[]`, `requests_sent=0`.

**Deliverables.** Six-cell reachability matrix (fact / expected value / observed answer / reachable),
the settled 96-row re-grade, and one sourced verdict paragraph. Result: T12/T24 unreachable in BOTH
arms (fixture defect, not pointer design); T46 reachable in both and failed in both (behaviour).
