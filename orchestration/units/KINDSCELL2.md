# KINDSCELL2 — AGG and ABS measurement cell

Measured `TX-AGG.v1.json` and `TX-ABS.v1.json`, both arms, one replication each.
Rows: `experiments/ptr-engine/measure/rows-agg2-2026-11-09.jsonl`,
`experiments/ptr-engine/measure/rows-abs2-2026-11-09.jsonl`.
Results: `experiments/ptr-engine/research-seed-concepts/RESULTS-KINDS-2-agg-abs.md`.

Write paths: rows above, results doc, this card, handoff.

Key outcomes:
- AGG: masking 0/48 both levels; fetch 4/48 (d=20:1, d=32:3). Masking abstains 28/48; fetch abstains 18/48, wrong 22, ungradeable 4.
- ABS: masking 3/48 (all d=2); fetch 15/48 (d=2:6, d=6:6, d=20:3, d=32:0). Masking over-refuses: 24/36 answerable refused.
- Activation gates met: masking fetch_rows=0; fetch fetch_rows 82 (AGG) / 50 (ABS), first positive row 10 / 8.
- Requests spent: 484 (242 per fixture), within 800 ceiling.

Checker/scorer: `score_longrun.py --answer-contract`; row-1 gates verified (task_id, fixture_sha256, temperature 0, seed 42, tools_mode).
PY