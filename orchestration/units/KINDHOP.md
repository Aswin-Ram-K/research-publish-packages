# KINDHOP — multi-hop memory task fixture

## Unit
KINDHOP

## Status
done

## Artifacts
- experiments/ptr-engine/longrun/tasks-v7/TX-HOP.v1.json
- experiments/ptr-engine/longrun/tests/test_tx_hop.py
- orchestration/units/KINDHOP.md
- orchestration/handoffs/KINDHOP.json

## Change summary
TX-HOP fixture: 12 chains, each introduces fact A (an entity identifier in doc-key-i) and fact B (a value table keyed by that identifier in doc-val-i) in two different tool outputs at different turns. 48 checkpoints, 12 per distance {2,6,20,32}, 48 unique turns, 48 distinct expected NUM values. Distance measured from the later fact (B). For d=2, A is masked (turn at t-4 or earlier) while B is visible; for d>=6 both A and B are masked. Each checkpoint asks "What is VAL_k of the entity introduced in doc-key-i?", requiring the join of A's identifier with B's table row.

## Invariant (join proof)
- A body (doc-key-i) contains ENTITY_ID = key-i but none of the expected NUM values.
- B body (doc-val-i) contains a table with key-i plus distractor keys (key-i-alt*) and the target values; the target row is only selectable using the identifier from A.
- Neither body alone yields the answer: A has no value; B has multiple keyed rows and no selected identifier.

## Masking hop statement
- d=2: A masked, B visible (12 checkpoints).
- d=6,20,32: A masked, B masked (36 checkpoints).

## Evidence
- checker: experiments/ptr-engine/longrun/tasks-v7/TX-HOP.v1.json: OK; outcomes all four; 48 checkpoints; N=180.
- pytest: 17 passed in 0.07s.
