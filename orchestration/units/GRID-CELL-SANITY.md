# UNIT GRID-CELL-SANITY — are the grid's cells analysable?

**Tag prompt:** `[automated]` no human, no questions · `[verdict]` verdict row before the handoff.
**Bound:** 26 tool calls, journal first, handoff within 6 calls of the end.
**Cost:** 0 inference requests, 0 network calls. **Read-only** over rows, grades, manifests, gates,
`cell.py`, `run_longrun.py`, `PARM-1*` and the fixture.

## Objective
Test — do not assume — whether each `rows-cell-*.jsonl` on disk satisfies the seven
analysability rules (row model, provenance/v8 sha, claim stamp, cache attribution, stop-reason
census, treatment markers per arm, wall guardrails), and record a conservative `usable_for` per
cell. No outcome statistic is computed: that is `V-TRANCHE-1`'s job.

## Write paths
`experiments/ptr-engine/measure/GRID-CELL-SANITY.json` · `docs/GRID-CELL-SANITY.md` ·
`tests/test_grid_cell_sanity.py` · `orchestration/units/GRID-CELL-SANITY.md` ·
`orchestration/handoffs/GRID-CELL-SANITY.json` · `orchestration/journals/GRID-CELL-SANITY.jsonl`

## Method
`tests/test_grid_cell_sanity.py` is both the analyser and its test suite: it parses rows offline,
parses `client.STOP_REASONS` out of `experiments/ptr-engine/longrun/client.py` by regex (never
imports it — importing pulls in `requests`), hashes every file it reads before and after, and
writes the JSON with `--emit`. Treatment predicates are the runner's own, quoted from
`experiments/ptr-engine/longrun/run_longrun.py:1125-1126` (pointer prefix) and the
`evicted`/`digest_at`/`lease` row fields.

## Results (RUN-A* cell, snapshot)
* **Row model pass** — 27 turns, one initial row each, 27 distinct `request_sha256`, no reuse.
* **Provenance pass** — nine fields on every row, `fixture_sha256` = v8 `0804b515…`, no STOP flag.
* **Claim stamp pass** — `claim=H2`, `comparison_eligible=true`, `.claim.json` twin agrees.
* **Cache attribution pass** — `cached_tokens` on 27/27 rows via `prompt_tokens_details` (sglang).
* **Stop reasons pass with one flag** — `stop` 26 / `length` 1 (turn 3, 4096 completion tokens,
  `truncated=true`), excluded in the row (`failed_turn=true`, `timing_usable=false`), 0 `unknown`.
* **Treatments not_applicable** — `pointer-stable` writes no `prefix_sha256` to the row, so its
  treatment cannot be proven from rows; the other three arms' predicates are row-decidable.
* **Wall guardrails pass** — max 114,838.846 ms, 0 over 180,000 ms, exclusion recorded in the row.

`usable_for: []` for both cells: the RUN-A* cell is 27/48 turns (**in progress** — wait for turn 48
and re-emit) and the pre-RUN-A* six-row fragment is schema-incapable and must never be analysed.

## Tests
`python3 -m unittest tests.test_grid_cell_sanity` — 7 tests green, including the two required red
cases (duplicate `request_sha256`, zero treatment marker) plus v7-sha-in-v8-era, unexcluded
`length`, `claim=none`, and the partial-last-line skip.
