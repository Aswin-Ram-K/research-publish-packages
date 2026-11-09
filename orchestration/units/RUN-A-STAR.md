# UNIT RUN-A* — tranche 1 adjudicating grid (PAIR-3+CTX-2, v8)

Purpose: run 10 cells / 480 turns / ~660 requests on fixture `tasks-v6/LR-01.v8.json`,
`--hypothesis H2` per cell, all four treatments firing inside 48 turns, under the
hardened gate chain. H1 is adjudicated only on pooled rows at n=144/arm; this unit
produces the rows and reports per-grid.

Hard bound: <=44 tool calls, <=900 requests, 10 cells maximum (tranche 1 only).
Write paths: `experiments/ptr-engine/measure/rows-runA-*` (+ twins),
`measure/RUN-A-STAR.md`, `measure/run-a-star.json`, `orchestration/units/RUN-A*`,
`orchestration/handoffs/RUN-A*.json`, `orchestration/journals/RUN-A*.jsonl`.

Pre-launch ledger: cap 4,320 (artefact), reserve 0, spent 1,101 raw / 1,071 dedup,
remaining 3,219. Frozen flags: turns 48, reps 1, thinking off, max-wall 2880,
turn-wall-cap 180, runaway-turns 2, endpoint http://192.168.2.168:8012/v1, model occamy-1.0.
Per-cell `--budget 67` (the dry-run's 900 was a per-cell ceiling only and is superseded).

Stop rules 1-7 as carried by the card; exit 5/6 = hard stop with diagnosis (defect (a):
cell.py:1568 relabels a runner 9 as 5; defect (b): runaway paths skip `_gate_finish`).
