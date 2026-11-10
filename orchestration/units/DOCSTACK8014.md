# DOCSTACK8014 — cross-stack results document

Created `experiments/ptr-engine/research-seed-concepts/RESULTS-STACK-8014.md` with tool-call verification (PASS), serving-config table, five-run table, distance-axis tables, AGG result, HOP attempt-1 vs r2, `:8012` reference totals, and limitations. Corrected STATUS.md line claiming document existence.

Malformed-answer claim verified against `rows-hop-8014-r2.jsonl`: OOV answers are `ANSWER: CALL(fetch(ref="doc-key-1@1"))` (no space between `CALL` and `(`). Claim accurate. Three quoted rows:
- `ANSWER: CALL(fetch(ref="doc-key-1@1"))`
- `ANSWER: CALL(fetch(ref="doc-key-1@1"))`
- `ANSWER: CALL(fetch(ref="doc-key-2@1"))`
