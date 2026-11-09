# UNIT `GRID-PARAMS-16CELL`

**Purpose (one):** wire the power-conformant 16-cell grid shape into the records the launcher reads, additively, so
`RUN-A-STAR-2` cannot launch a shape its own card does not describe.

**Why it existed:** `V-LEDGER-BASELINE` recorded, under `unverified`, that the 16-cell price 1,056 was not a grid
artefact on disk: `GRID-SHAPE.json` said 10 cells / 724 requests and `GRID-PARAMS.json` priced the 10-cell package at
1,016; 1,056 existed only as a shape price in `price-replication.json:461`. `RUN-A-STAR-2` is now 16 cells because
`POWER-UNDER-TURN-N` measured `n_eff(144) = 31.36` on the binding arm (`rows-longrun-c`, r=0.6423) against a floor of
60; six runs per pair arm is the smallest conformant shape (`n_eff(288) = 62.73`). Both prices fit the 3,192
headroom, so the brake cannot catch the mismatch — only the wiring can.

**Hard bound:** ≤20 tool calls; OFFLINE — `--dry-run` and `/tmp` copies only; zero requests, zero sockets.

**Write paths:** `experiments/ptr-engine/measure/GRID-PARAMS.json`,
`experiments/ptr-engine/measure/GRID-SHAPE.json`, `docs/GRID-PARAMS.md`,
`experiments/ptr-engine/measure/GRID-PARAMS-16CELL.json`, `orchestration/units/GRID-PARAMS-16CELL.md`,
`orchestration/handoffs/GRID-PARAMS-16CELL.json`, `orchestration/journals/GRID-PARAMS-16CELL.jsonl`.

**Not editable:** `cell.py`, `run_longrun.py`, `analyze_stats.py`, `grade_v5.py`, `measure/HARNESS-PIN.json`
(including its digest field), any fixture, any threshold, `PARM-1*`, any published page, `RUN-A-STAR-2`'s card.
No re-pin; `spend_status` never becomes an approval.

## Result

| | before (rev 2) | after (rev 3) |
|---|---|---|
| arms | 3 / 3 / 2 / 2 | 6 / 6 / 2 / 2 |
| cells | 10 | 16 |
| turns | 480 | 768 (16 × 48) |
| price | 1,016 (964 + 48 canary + 4 warm-ups) | 1,056 = 768 × 1.374532 |
| remaining after | 2,176 | 2,136 |
| `spend_status` | NOT approved spend | NOT approved spend |

The 10-cell figures are preserved verbatim in `GRID-PARAMS.json :: supersedes.ten_cell_figures_preserved_verbatim`,
with the previous `price` object, `per_cell_budget` and the earlier `supersedes` block kept intact beside it.
`GRID-SHAPE.json` gained `sixteen_cell_supersede` and had its `cells[0..9]` left byte-identical.

**Measured residual (the finding this card actually produced):** `tools/run_a_star.py` reads neither
`GRID-PARAMS.json` nor `GRID-SHAPE.json`. Its grid is the module constant `CELLS` (`run_a_star.py:99-103`), a literal
10-tuple, and it prints no price. So promotion moves the record and not the launcher: the dry run says `cells=10`
both before and after. Wiring 16 cells into a launch is a change inside `run_a_star.py` — a follow-up card.
Two further open items: `run_a_star.py:51` still pins generation 4 while `HARNESS-PIN.json` is generation 5 (so the
repo launcher refuses before any cell, and the dry-run evidence required a `/tmp` copy with only that constant
advanced), and `run_a_star.py:571` bills `3219 - delta` while the gate bills `4,320 - 1,128 = 3,192`.
