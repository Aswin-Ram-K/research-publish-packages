# LEDGER-RECONCILE — why the launcher compares a DELTA, not two numbers

**Status:** in force from `LEDGER-RECONCILE-DELTA` (2026-10-27). Supersedes the
equality cross-check introduced by `LAUNCHER-GEN5-WIRE`.

## The defect this replaces

`measure/REQUEST-LEDGER.json` is **rebuilt from `measure/rows-*.jsonl`**, so its
`requests`/`remaining` move with every billed cell. `measure/LEDGER-GRID-BASELINE-N.json`
is a **photograph frozen at one instant**. Comparing the two for equality therefore
refuses **every** launch once any cell bills after the freeze — not once, forever.

Measured (CANARY-ERA-B-4, exec `435d2b16`, zero requests spent):

> `REFUSED: ledger records disagree on 'remaining': {baseline-2: 3192, request-ledger: 3144}`

The 48-request gap was four complete 12-turn cells billed `20:20–20:43Z`, after
baseline-2 froze at `19:04:18Z`:

| rows file | rows | first ts | last ts |
| --- | --- | --- | --- |
| `rows-cell-pointer-stable-20261026T202040Z.jsonl` | 12 | 20:20:58Z | 20:24:44Z |
| `rows-cell-transcript-grow-20261026T202444Z.jsonl` | 12 | 20:26:41Z | 20:37:32Z |
| `rows-cell-transcript-compact-20261026T203733Z.jsonl` | 12 | 20:37:34Z | 20:37:42Z |
| `rows-cell-pointer-stable-20261026T204258Z.jsonl` | 12 | 20:43:11Z | 20:43:40Z |

Both records were honest. One was stale by construction. Re-cutting the number alone
would have left the trap armed for the next cell, so the **check** changed too.

## The rule

```
live.requests == baseline.requests + attributed_delta
live.remaining == baseline.remaining - attributed_delta
```

`attributed_delta` is counted from the rows files themselves: every row stamped
**after** the baseline's `as_of`, using the ledger's own counting rule
(`request_ledger.py` `rule`: `kind in {turn, tool-followup}` or unmarked
`assumed_billed`; `billed:false`, `followup_suppressed`, `served_from:prompt` do not
count). The launcher prints the three numbers it compared **and the files that
produced the delta**:

```
RUN-A RECONCILE baseline=1176 attributed_delta=0 live=1176 explained=1176 gap=0 as_of=2026-10-26T22:33:00Z files=none
```

A future cell prints, for example, `baseline=1176 attributed_delta=48 live=1224
… files=rows-cell-….jsonl(+12 <sha12>), …` — the next reader does not re-derive it.

### What still refuses, hard

| condition | message | why it must refuse |
| --- | --- | --- |
| `live ≠ baseline + delta` | `REFUSED: N request(s) of ledger gap cannot be attributed to any rows file…unexplained=N` | an unexplained gap means requests were spent that no artefact accounts for — the budget rule, not a formatting complaint |
| `remaining` does not follow the delta | `REFUSED: 'remaining' does not follow the same delta…` | two arithmetic faces of one ledger disagreeing |
| baseline missing / no `remaining` | `REFUSED: ledger baseline <path> is missing or carries no 'remaining'…` | a launcher with no basis must not print a figure |
| baseline has no `as_of`/`requests` | `REFUSED: … carries no usable 'as_of'/'requests'` | a delta that cannot be attributed is not a delta |

The refusal path is proven load-bearing: `tests/test_ledger_reconcile.py` inflates a
live ledger by 7 unattributed requests and requires the refusal to name the 7, then
re-runs the same case against a launcher whose two guard branches are removed and
requires that one to *allow* it (red → green).

## The records

- `measure/LEDGER-GRID-BASELINE-3.json` — `requests 1176 / remaining 3144 / cap 4320`,
  `as_of 2026-10-26T22:33:00Z` (the live ledger's `generated_at_utc`), an `attribution`
  table naming the four files with rows + sha256, `supersedes` carrying v2's figures and
  freeze instant, and a `rows_inventory` for `ledger_delta.py`'s rows guard.
  **v2 is not mutated** and remains reachable by path; it is now *acceptable* through
  the delta (`1128 + 48 == 1176`), which is the point.
- `measure/REQUEST-LEDGER.json` — unchanged by this card; rebuilt only by
  `request_ledger.py:build_report` (`requests 1176 / remaining 3144`, 19 files).

`ledger_delta.py --baseline …/LEDGER-GRID-BASELINE-3.json` reports `delta 0`,
`verdict OK` — the re-cut closes. `--baseline …/LEDGER-GRID-BASELINE-2.json` reports
`delta 48` and names the four files as `rows_guard_new`: that is the same 48, measured
against the record that was stale.

## Re-cutting a baseline (procedure)

1. Rebuild the live ledger with its own builder — never hand-edit a number:
   `request_ledger.py --glob 'measure/rows-*.jsonl' --cap 4320 --reserve 0`.
2. Freeze a new `LEDGER-GRID-BASELINE-N.json` with `as_of` = the ledger's
   `generated_at_utc`, `requests`/`remaining`/`cap`, and an `attribution` table for the
   rows billed after the previous baseline's `as_of` (file, rows, sha256, ts range).
3. `supersedes` the previous baseline (figures + freeze instant + sha256). Do **not**
   edit the old file — the delta rule keeps it usable.
4. Add `rows_inventory` (file, rows, sha256) so `ledger_delta.py`'s guard is active.
5. `python3 -m pytest experiments/ptr-engine/tests/test_ledger_reconcile.py -q` — 9 passed.

## Hooks (tests / `/tmp` proof, never a launch)

| env var | meaning |
| --- | --- |
| `RUN_A_STAR_LEDGER_BASELINE` | baseline record (default `measure/LEDGER-GRID-BASELINE-3.json`) |
| `RUN_A_STAR_LEDGER_LIVE` | live ledger (default `measure/REQUEST-LEDGER.json`) |
| `RUN_A_STAR_LEDGER_ROWS` | rows glob the delta is counted from (default `measure/rows-*.jsonl`) |

Read at import time, so a `/tmp` copy is exercised without touching the tree.

## Code map

- `experiments/ptr-engine/tools/run_a_star.py` — `LEDGER_*` (`:203-218`),
  `_epoch`/`_row_counts`/`_sha256`/`attributed_delta` (`:221-296`), `remaining_basis`
  (`:302-392`), printed from the dry-run path (`:916`) and the launch path.
- `experiments/ptr-engine/tests/test_ledger_reconcile.py` — 9 tests, incl. the +7
  refusal and its red→green revert.
- `measure/LEDGER-GRID-BASELINE-3.json`, `measure/LEDGER-GRID-BASELINE-2.json`,
  `measure/REQUEST-LEDGER.json`.

---

# LEDGER-KIND-RULE — one rule for `spent`, written before the fix (2026-10-27)

## The defect

Two occurrences of *the same rule* disagreed. `request_ledger.classify()` counted a row whose
`kind` it did not recognise (returning `(1, 1)` — counted **and flagged**), while
`run_a_star._row_counts()` returned `False` for every kind outside `{turn, tool-followup}` —
it **silently unbilled** them. Both read the same `measure/rows-*.jsonl`.

Measured consequence (RUN-A-STAR-2, gate 2, **0 requests sent**):

```
RECONCILE baseline=1176 attributed_delta=115 live=1176 explained=1291 gap=-115   (stale ledger)
RECONCILE baseline=1176 attributed_delta=115 live=1321 explained=1291 gap=30     (correct ledger)
```

The 30 rows are `kind="turn-initial"`, distributed `2+7+13+6+1+1` across the six rows files
billed after baseline-3 froze. No honest ledger state satisfied `remaining_basis()`.

## The rule (decided from the writer, not from the tally)

| `kind` | one wire request? | evidence |
| --- | --- | --- |
| `turn` | **YES** | `run_longrun.py:2703` `make_row(..., "turn", ...)`; gated at `:2527` `gate.acquire(t, "turn")` |
| `tool-followup` | **YES** | `run_longrun.py:1126` `make_row(..., "tool-followup", ...)`; gated at `:1115` |
| `turn-initial` | **YES** | `run_longrun.py:2726-2729`; the INITIAL send's own row — `run_longrun.py:2672`: "With k >= 1 follow-ups this turn made k+1 requests: the initial send (row_initial, below), follow-ups 1..k-1 … and follow-up k, whose row IS this turn row" |
| `digest` | **YES** | `run_longrun.py:2479` `gate.acquire(t, "digest")` then `:2481` `resp = send_chat(cfg, msg)`; rows at `:2491/:2504/:2512` |
| *(no kind)* | **counted + flagged `assumed_billed`** | legacy schema (232 rows); the schema cannot decide, so guessing "free" would understate spend |
| `tool_call` | **not a kind at all** | no `make_row` call site passes it; `tool_calls` is a row **field** (`run_longrun.py:2692` `row_extra["tool_calls"] = turn_calls`) describing calls the turn row already bills |
| unknown non-empty kind | **REFUSED** | `UnrecognisedKind`; billing invents a request, unbilling deletes one |

`billed: false`, `followup_suppressed`, `served_from: "prompt"` remain the only exclusions.
`tool_call` is named here because it was the one candidate neither reviewer considered: it is
not a kind, so there is nothing to bill.

## The fix: one function, imported

* `request_ledger.row_bills(row)` is the sole implementation;
  `COUNTED_KINDS = ("turn", "tool-followup", "turn-initial", "digest")`.
* `run_a_star._row_counts(row)` **imports and delegates** to it; `COUNTED_KINDS` there is an
  alias. The old restatement also mishandled `billed: "false"` (`is False` vs truthiness).
* Unknown kind → `RowsUnreadable` (exit 5, "nothing counted") on the recount side and
  `SystemExit` refusal on the attribution side.
* The `remaining_basis` label is derived from the baseline path instead of the hard-coded
  `"ledger:baseline-3+attributed-delta"`, and the default baseline is baseline-4.

## Corrected figures

| | baseline-3 | **baseline-4** |
| --- | --- | --- |
| `as_of` | 2026-10-26T22:33:00Z | 2026-10-27T20:53:48Z |
| rows files | 19 | **25** |
| `requests` | 1176 | **1321** |
| `remaining` (cap 4320) | 3144 | **2999** |
| de-duplicated (diagnostic only, never deducted) | 1146 | 1291 |

`REQUEST-LEDGER.json` was **regenerated by its own tool** (`request_ledger.py --write`) at
2026-10-27T20:53:48Z, sha256 `3f879fa424105319cf87b6f571ac88424ccad9d394e052ac65a00c359fe2968a`;
that file is a NEW artefact, not the 1176-era one, and baseline-4 carries exactly its numbers.
baseline-3 is **not mutated**.

Reconciled launch state:

```
RUN-A RECONCILE baseline=1321 attributed_delta=0 live=1321 explained=1321 gap=0 as_of=2026-10-27T20:53:48Z
remaining 2999  ledger:baseline-4+attributed-delta  cap 4320
```

## Grid arithmetic

`remaining − 1056 = 1943` → **fits** (16 cells / ≈1,056 requests). The grid was not re-shaped to
meet a ledger; the ledger was re-derived to describe the work.

## Proof (three ways)

`python3 -m unittest tests.test_ledger_kind_rule -v` — 7 tests, all pass:

* **(a)** every `measure/rows-*.jsonl`: recount == attribution, **total 1321 / 1321**.
* **(b)** `/tmp` copy + one synthetic `turn-initial` row: **both** numbers move by exactly +1
  (ledger `requests` +1, attribution +1, `remaining` −1).
* **(c)** `turn-initial` renamed to `turn-initial-typo`: ledger exits 5 with
  `unrecognised row kind 'turn-initial-typo' … nothing counted`; attribution raises
  `SystemExit`. No silent unbill.

RED→GREEN: restoring the old `_row_counts` body fails (a) on all six files carrying
`turn-initial`; restoring the old `classify` fails (c) on both sides.
