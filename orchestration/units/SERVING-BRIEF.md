# SERVING-BRIEF — the operator-facing answer: what to run, what does not help, and the real capacity limit

**Card status:** done (1 run, 2026-10-23 19:19–19:31 CDT). **Live requests:** 0. **Lock:** none taken.

## Objective

Turn the measured package in `papers/context-cache/` into the one document an operator of the
GB10 `occamy-1.0` endpoint can act on: which configuration actually costs least per turn, which
plausible-looking levers were measured and did not help, and what the real reusable-capacity
limit is. Every number must re-derive from a cell on disk — the brief is a *view*, not a new
source of truth.

## Deliverable shape

1. `papers/context-cache/SERVING-BRIEF.md` — ~110 lines: "The answer" (bullets), "What to run",
   "What does not help", "The real capacity limit", "What this brief cannot tell you", and a
   generated numbers table (19 rows: item, operator question, value, cell, recompute command).
2. `papers/context-cache/serving_brief.py` — the traceability harness. 19 ledger items S01–S19;
   each claim-backed item calls `recompute.FUNCS[cid]()` and compares against `recompute.EXPECTED[cid]`
   inside `recompute.TOLERANCE`; row-backed items re-read the cell rows; the artefact-backed item
   reads `analysis.json`. Pins sha256 for every row file; injects the two generated tables into
   the brief between markers; `--check` fails on any drift, unknown marker, uncited item, or
   prose number absent from the table.
3. `state/serving-brief.json` — the generated ledger (machine-readable).
4. `tests/test_serving_brief.py` — the guard: `--check` exits 0, ledger shape (19 items), both
   generated tables present.

## Hard bound

One run; ≤25 tool minutes of compute; **0 live requests, 0 locks, 0 target writes**. Stop and
report `partial` if a cited cell is missing or a figure will not re-derive — do not repair the
paper from inside this unit (a fix is a new unit).

## Write paths (declared, non-overlapping with the live MATRIX-FOLD unit)

- `papers/context-cache/SERVING-BRIEF.md` (new)
- `papers/context-cache/serving_brief.py` (new)
- `state/serving-brief.json` (new)
- `tests/test_serving_brief.py` (new)
- `orchestration/units/SERVING-BRIEF.md`, `orchestration/handoffs/SERVING-BRIEF.json` (own card/handoff)

Read-only, not edited: `CLAIMS.md`, `MANUSCRIPT.md`, `recompute.py`, `READER-MAP.md` (MATRIX-FOLD was
live on those), every `experiments/context-cache/cells/**` file, and every target repo.

## Method

1. Read the package's claim ledger and the 13 cells the brief leans on; take values from
   `recompute.EXPECTED`, never from prose.
2. Build one ledger item per operator question, each with the cell and the exact `C##` that
   re-derives it; generate the table from the ledger rather than typing numbers.
3. Lint the brief's prose: every numeral in a non-table line must appear in a ledger row, every
   S-item must be cited; encode both as `--check` failures.
4. Red→green: a drifted `EXPECTED` value, a hand-edited table digit, and a hand-edited prose
   digit must each be refused. Measured: all three refused (evidence in the handoff).

## Kill condition

If any cited cell's rows are absent, `recompute.py` no longer has the `C##`, or a figure fails
tolerance and cannot be explained by rounding — stop, write `partial`, name the item.

## Result

- 19 items, 13 cells; `serving_brief.py --check` → **PASS** ("19 items, 13 cells, all figures
  re-derived; tables, markers and prose numbers match the ledger").
- `pytest tests/test_serving_brief.py` → **3 passed**.
- `verify_package.py` → **PASS** (63/63 claims mapped; unaffected by this unit).
- 0 live requests; 4 files created; no cell or target touched.
