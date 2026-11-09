# VKINDS — audit of TX-AGG / TX-SUP / TX-ABS / TX-HOP fixtures

## Unit
VKINDS

## Status
done

## Artifacts
- orchestration/units/VKINDS.md
- orchestration/handoffs/VKINDS.json

## Scope
Read-only audit of `experiments/ptr-engine/longrun/tasks-v7/{TX-AGG,TX-SUP,TX-ABS,TX-HOP}.v1.json`. No fixtures, tests, runner or scorer modified. No HTTP requests.

## Asked-not-graded (runner functions)
`run_longrun.checkpoint_expected` + `run_longrun.checkpoint_prompt` over every turn:
- TX-AGG: paired_count=48, mismatches=0
- TX-SUP: paired_count=48, mismatches=0
- TX-ABS: paired_count=48, mismatches=0
- TX-HOP: paired_count=48, mismatches=0

## Structure
All four: 48 unique checkpoint turns; buckets {2:12, 6:12, 20:12, 32:12}; 0 distance mismatches; distances measured from turn indices.

## Leak
- TX-AGG: expected appears in 0 single bodies (multi-fact by construction); 0 leaks to system prompt / questions / items / other bodies.
- TX-SUP: each expected appears in exactly 1 body; 0 leaks to system prompt / questions / items / other bodies.
- TX-ABS: answerable values: exactly 1 body each, 0 leaks. Absent: `VAL_G` appears in 0 bodies, 0 item bodies, 0 system prompt; appears only in the 12 questions (by design, no numeric candidate).
- TX-HOP: each expected appears in exactly 1 body (B); 0 leaks to system prompt / questions / items / other bodies.

## Full checker (default, nothing disabled)
- TX-AGG: FAIL — 48 `... fact value ... not found in introduction turn ... tool output` (reachability; inherent to aggregation).
- TX-SUP: OK.
- TX-ABS: FAIL — `duplicate expected` (×11), `kind/type mismatch` (×12), reachability (×36); inherent to absent design.
- TX-HOP: OK.

## Kind semantics
- TX-AGG: 6/6 recomputed aggregates match `expected` and use >=2 facts (e.g. g05.d2 220786 = 55000+55131+55262+55393; g00.d32 10262 = 5000+5262).
- TX-SUP: 6/6 stale value present, differs from expected, expected is latest revision (rev2).
- TX-ABS: 12 absent / 36 answerable; 3 absent per bucket; answerable values all distinct; absence proof above.
- TX-HOP: 6/6 neither body alone yields answer (A has key, no value; B has value + distractors, needs A's key); masking: d=2 => A masked, B visible (12 cps); d>=6 => both masked (36 cps). No case with A visible/B masked.

## Realism
All four are placeholder-grade: templated questions (`What is VAL_A of doc-fact-01?`, `What is VAL_1 of the entity introduced in doc-key-1?`), synthetic value series (3000/4000, 10101…, 5000…), generic group labels. They exercise mechanism (masking, aggregation, supersession, absence) but cannot support claims about realistic content or domain transfer. TX-ABS system_prompt still says `TX-03` (copy-paste leftover).

## pytest (literal)
- test_tx_agg.py: `14 passed in 0.05s`
- test_tx_sup.py: `19 passed in 0.06s`
- test_tx_abs.py: `9 passed in 0.04s`
- test_tx_hop.py: `17 passed in 0.07s`

## Per-fixture verdict
| Fixture | Asked-not-graded | Structure | Leak | Default checker | Kind semantics | Realism | pytest | Verdict |
|---|---|---|---|---|---|---|---|---|
| TX-AGG | pass (48/0) | pass | pass (0 single-body) | fail (reachability, inherent) | pass | placeholder | pass (14) | partial |
| TX-SUP | pass (48/0) | pass | pass | pass | pass | placeholder | pass (19) | pass |
| TX-ABS | pass (48/0) | pass | pass (absence proof) | fail (dup/gradability/reachability, inherent) | pass (12/36, 3/bucket) | placeholder | pass (9) | partial |
| TX-HOP | pass (48/0) | pass | pass | pass | pass | placeholder | pass (17) | pass |

## Spec deviations (with numbers)
1. TX-AGG: default checker FAILS unless `reachability` disabled (48 reachability errors). Inherent to task kind: aggregate is by construction absent from any single body, so reachability's "value must be in introduction turn body" cannot hold. Not a defect; documented in test_tx_agg (disabled={"reachability"}).
2. TX-ABS: actual split is 12 absent / 36 answerable (3 absent per bucket), not the "24/24" figure in the suspicious claim. The "3 absent per bucket of 12" clause matches the fixture (3×4=12); the "24/24" clause is internally inconsistent with it and with the fixture. Treat as an unresolved spec ambiguity, not a code defect.
3. TX-ABS: default checker FAILS unless `duplicate_expected, gradability, reachability` disabled (11 duplicate + 12 kind/type + 36 reachability errors). Inherent to absent design (NONE repeated; no source value; answer kind NONE vs expected type TEXT).
4. TX-ABS: system_prompt mislabels task as `TX-03` (cosmetic).
5. TX-HOP: masking is one-directional only — d=2 has A masked/B visible (12 cps); d>=6 has both masked (36 cps). There is no A-visible/B-masked case, so "vice versa" does not occur.
6. All four: placeholder-grade content, so none can support a claim about realistic-task performance.

## Safe to run now
- TX-SUP and TX-HOP: default checker green, tests green, run as-is.
- TX-AGG: safe only with `disabled={"reachability"}`; reachability N/A by construction. Do not run default checker expecting green.
- TX-ABS: safe only with `disabled={"duplicate_expected","gradability","reachability"}`. Resolve the 24/24 vs 12/36 spec ambiguity before treating it as a 24-absent benchmark.

## Blocker
none.

## next_unit_hint
Reconcile the TX-ABS absent-count spec (24/24 vs 12/36) with the original brief before spending requests; otherwise the four fixtures are audit-clean for mechanism testing.
