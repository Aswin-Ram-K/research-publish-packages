# REPLICATE2

Second replicate of all three conditions on TX-01.v1.json (48 turns, 12 checkpoints).

Runs (graded, in order):
1. masking-no-fetch, masking on -> 0/12 (12 NONE abstentions)
2. masking-no-fetch, masking off (WINDOW_TURNS=100 sitecustomize) -> 12/12
3. bounded-context-fetch, masking on, --tools fetch -> 12/12

Comparison: rep2 reproduces rep1 for all three conditions; no checkpoint flipped.

Accounting: 48+48+109=205 rows across three files; each run task_id=TX-01, sha 44a1b435...; cap 3026->3281 (+255 incl failed bounded attempt? rows counts 48+48+109=205 live requests in delivered files). Voided failed bounded attempt replaced by corrected run.
