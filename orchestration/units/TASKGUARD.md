# TASKGUARD

Guarded TX-01 run: fixture/task mismatch refused; no-selector refused; 10 live requests (5 turns x 2 arms), all rows task_id TX-01.

- Guard: `--task` resolves fixture and refuses on task_id mismatch; no selector refuses.
- Live: masking-no-fetch and bounded-context-fetch, turns 1-5, 0 fetches issued, 0 truncated.
- Rows: `experiments/ptr-engine/measure/rows-tx01-real-20261109.jsonl` (10 rows, cap 2668->2678).
- Turn 5: C `ANSWER: NONE`, D `ANSWER: NONE` (fact not available on either arm).
