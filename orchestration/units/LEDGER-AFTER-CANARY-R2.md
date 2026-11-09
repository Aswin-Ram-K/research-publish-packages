# UNIT `LEDGER-AFTER-CANARY-R2` (re-run of card 208b36cd, execution 6320f71b)

**Purpose.** Verify — independently, from disk — that the brake `experiments/ptr-engine/measure/REQUEST-LEDGER.json` no
longer reads a stale spend, that the post-canary delta is attributed exactly, and that the G1 cap gate's operand is
named with a `file:line`. The card was re-run because the previous execution's handoff claimed artefacts it did not
leave behind (a journal at `orchestration/journals/LEDGER-AFTER-CANARY.jsonl`); everything below was re-derived in this
execution, not inherited.

**Hard bound.** 25 tool calls. Zero inference requests, zero network, no `ask_user_question`.

**Write paths.** `orchestration/journals/LEDGER-AFTER-CANARY.jsonl` ·
`orchestration/units/LEDGER-AFTER-CANARY-R2.md` · `orchestration/handoffs/LEDGER-AFTER-CANARY-R2.json`.
The three data deliverables were **verified in place and left byte-identical** (rewriting them would only move a
timestamp on a number already proven correct): `measure/REQUEST-LEDGER.json` (sha `63e3a156…`),
`measure/LEDGER-AFTER-CANARY.json` (sha `1226fd97…`), `docs/LEDGER-AFTER-CANARY.md` (sha `f13c1b45…`).

**Forbidden, and honoured.** Every row/grade/fixture file, `cell.py`, `run_longrun.py`, `run_a_star.py`,
`analyze_stats.py`, `grade_v5.py`, `measure/HARNESS-PIN.json`, `measure/GRID-PARAMS.json`, published pages other than
`docs/LEDGER-AFTER-CANARY.md`, and `measure/LEDGER-GRID-BASELINE-2.json` (read only).

## Result (re-derived here)

| item | measured |
|---|---|
| rebuild | builder run **twice** → byte-identical, sha256 `eadc56f6…`; `requests_raw` **1176**, `requests` 1176, `requests_deduplicated` **1146** (diagnostic, `deducted:false`, `duplicate_excess` 30), `remaining`/`remaining_raw` **3144**, cap 4320 reserve 0, `files` **19**, `rows` 1176 |
| on-disk vs fresh build | identical for every builder key; the only extra keys are the provenance block `supersedes` / `superseded_by_unit` / `built_by` / `generated_at_utc` |
| `supersedes` | old sha `6da0c1f1…`, spent **1128**, remaining 3192, built `2026-10-26T18:56:31Z` — superseded, not mutated |
| delta | **48**, not the card's 36 — see the fourth file below |
| pre-existing files | 15/15 sha-unchanged against `LEDGER-GRID-BASELINE-2.json` `rows_inventory.per_file`; 0 missing; exactly 4 added; all 19 `per_file` shas equal the bytes on disk |
| `ledger_delta.py` (v2) | `spent_before 1128 → spent_now 1176`, **delta 48**, `remaining_now 3144`, `rows_guard` 4 new, `deficit none`, `verdict OK`, exit 0 |
| gate | **re-counts rows**, does not read `budget.spent` — `cell.py:1255` |

## The delta is 48: three canary arms (36) plus a fourth cell (12)

| file | rows | first row (UTC) | whose |
|---|---|---|---|
| `rows-cell-pointer-stable-20261026T202040Z.jsonl` | 12 | 20:20:58.079 | canary arm pointer-stable |
| `rows-cell-transcript-grow-20261026T202444Z.jsonl` | 12 | 20:26:41.642 | canary arm transcript-grow |
| `rows-cell-transcript-compact-20261026T203733Z.jsonl` | 12 | 20:37:34.021 | canary arm transcript-compact |
| `rows-cell-pointer-stable-20261026T204258Z.jsonl` | 12 | **20:43:11.557** | **not the canary** — manifest created 20:42:58.636Z, `cap_gate.spent_at_start=1164`, `cap_gate.reconcile.spent_after=1176` |

The card's "must equal 36" is therefore **not** reproduced, and is not forced: the card's own escape clause ("if a
fourth file appeared, report it instead of assuming") governs. `CANARY-ERA-B-3.json` records
`spent_rows_before=1128 -> spent_rows_after=1164`, which is exactly the 36 the canary saw; the fourth cell's own
manifest then priced its launch at 1164 and its finish at 1176. 1128 + 36 + 12 = 1176. Nothing else moved.

## What the gate reads — `cell.py:1255`

```
experiments/ptr-engine/longrun/cell.py:1255
        report = ledger.build_report(_ledger_row_paths(doc), facts["cap"],
                                     facts["reserve"], would_spend)
experiments/ptr-engine/longrun/cell.py:1200   def _ledger_row_paths(doc):   # artefact `files` list -> paths
experiments/ptr-engine/longrun/cell.py:1261   b = report["budget"]
experiments/ptr-engine/longrun/cell.py:1267   unspent = b["cap"] - b["reserve"] - b["spent"]
```

Precise answer: G1 **never** priced a cell against `budget.spent` (the literal 1,128), so the gate was not mispriced
by that field. It was mispriced anyway, one level down — `_ledger_row_paths` (`cell.py:1200-1213`) enumerates only the
row files **named in the artefact's `files` list**, and the stale snapshot named 15 while the disk held 19. A cell
launched against the old artefact therefore saw 1,128 rather than 1,164/1,176: under-priced by 48. The rebuilt artefact
closes that hole by carrying all 19 files. Consumers that take `budget.spent` literally (card prose, `run_grid_report.py`)
read 1,128 and overstated headroom by 48.

**Verdict row.** `PASS f17663d1` — `bash -lc '/usr/bin/python3 -m pytest experiments/ptr-engine/tests/test_request_ledger_sound.py experiments/ptr-engine/tests/test_request_ledger_dedup.py experiments/ptr-engine/longrun/tests/test_cell_gates.py -q'` → 35 passed, 7 subtests passed, exit 0.
**Finding for the next unit.** Root cause is the `files` list, not the number: any snapshot read by G1 is stale the
moment a cell appends rows. Either rebuild before every launch (deterministic and cheap — proven here) or make G1 glob
`measure/rows-*.jsonl` instead of trusting the artefact's `files`.
