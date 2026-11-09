# ROW-PROVENANCE

**Card:** `25c15347-4045-4941-a07b-0171c6b66349` · **Execution:** `866ee0f3-98a3-4543-b2ea-4286963c0452`
**Date:** 2026-10-26 · **Bound:** 28 tool calls · **Cost:** zero inference requests (OFFLINE).

## Purpose (one)
Make every measured row say what produced it, publish the same block on the run manifest,
retrofit the 14 existing rows files **by reading** them, and expose a comparison that
**refuses** when two cells' load-bearing provenance differs.

## Why
`HARNESS-MAP-V2` had to infer a "harness era" axis from file mtimes because rows carried no
harness, fixture, model or thinking field; `LATENCY-REPORT` then marked every
era-load-bearing pair NOT COMPARABLE, and `docs/OPERATOR-BRIEF.md` reports H1 as not
adjudicable partly for that reason. Four revisions of the same fixture
(`LR-01.v2 -> v4 -> v5 -> v6/v7`) changed the task while the rows stayed anonymous.

## Deliverables
| path | what it is |
|---|---|
| `experiments/ptr-engine/longrun/client.py` | field set, `provenance_block`, `fixture_label`, `tools_mode_label`, `same_provenance` (canonical) |
| `experiments/ptr-engine/longrun/run_longrun.py` | `harness_sha256_now`, `provenance_for`; `make_row` stamps every row; `build_manifest` publishes the block |
| `experiments/ptr-engine/tools/row_provenance.py` | read-only retrofit over the 14 rows files + `same_provenance` + cost + proven deltas |
| `docs/ROW-PROVENANCE.md` | field list, source-of-truth ladder, retrofit table, findings |
| `experiments/ptr-engine/measure/ROW-PROVENANCE.json` | machine-readable table |
| `experiments/ptr-engine/longrun/tests/test_row_provenance.py` | 12 tests, (a)-(f) |

## Hard rules honoured
Never edited a rows file, a grade file, `TVS.json`, `LATENCY-REPORT.json`,
`REQUEST-LEDGER.json`, `cell.py`, or anything under `longrun/tasks*/`. `cell.HARNESS_FILES`
is **read**, not changed. No field is filled by a plausible guess: an unknown is the string
`"unknown"` plus `provenance_complete: false`.

## Deliberate deviation, recorded
The card places `make_row` in `client.py`; the row writer is `run_longrun.make_row`
(`run_longrun.py:1484`). The pure helpers live in `client.py` and the stamping in
`run_longrun.py` — both in this unit's write paths.

## Not done (next step, another card's file)
`analyze_stats.py` does **not** call `same_provenance` yet — that file is owned by another
card. Wiring it in is the next step.
