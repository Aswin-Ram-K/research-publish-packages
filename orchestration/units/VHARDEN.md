# VHARDEN — Audit of four hardened fixtures for residual answer-inference channels

## Scope
Read-only audit of `experiments/ptr-engine/longrun/tasks-v7/{TX-SUP,TX-AGG,TX-HOP,TX-ABS}.v1.json`.
No fixtures, tests, runner, or scorer modified. No HTTP requests.

## Checks performed
1. Extrapolability: scanned every revision body, group member list, keyed table, and chain endpoint set for runs of >=3 values with constant first difference; tested expected values against linear functions of ordinal/group index.
2. Question leakage: expected values (and cross-checkpoint expected values) searched in all question text; numeric ordinals/group ids checked against formulas.
3. Structure: 48 checkpoints, 48 unique turns via `run_longrun.checkpoint_expected`/`checkpoint_prompt`, 12 per distance bucket {2,6,20,32}, distinct expected counts, facts only in `tool_outputs[].body`.
4. Kind invariants: SUP stale!=current/present/latest revision; AGG recompute 6 checkpoints; HOP neither body alone; ABS 12 absent/36 answerable, 3 per bucket, absent subject in no body.
5. Guards bite: in-memory mutation reinstating constant-difference series caused the anti-inference assertions to fail (SUP, AGG, HOP).
6. Literal pytest output and default `check_pointer_fixtures.py` output captured.

## Findings
- No run of >=3 values with constant first difference found in any fixture (SUP/AGG/HOP/ABS).
- No expected value equals a linear function of a group index or ordinal.
- No expected value appears in any question text (direct or cross-checkpoint).
- Structure intact for all four (ABS has 37 distinct expected values by design: 36 NUM + NONE).
- Kind invariants hold for all four.

## Residual inference channels
- TX-HOP: target row is always the first data row of the B table (48/48 checkpoints), so an agent could answer from B alone by row position instead of joining on the key from A. Flagged as residual channel; verdict partial.
- TX-ABS: absent subject is the fixed token `VAL_G` in all 12 absent checkpoints; a strategy keyed on that token answers NONE without retrieval. This is the intended absent-fact signal, not a numeric leak, but is a predictable marker.
- TX-AGG: introduction-turn body count varies (1 vs 2) by checkpoint; not sufficient to compute a sum, noted for completeness.
- No numeric leak or cross-group linear relation found.

## Verdicts
- TX-SUP: pass — safe to spend requests on.
- TX-AGG: pass (reachability disabled is inherent to aggregation) — safe to spend requests on.
- TX-HOP: partial — not safe until row ordering is varied; tests/checker pass but residual channel present.
- TX-ABS: pass (disabled checks inherent to absent-fact design) — safe to spend requests on.
