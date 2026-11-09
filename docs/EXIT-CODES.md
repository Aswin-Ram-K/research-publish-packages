# EXIT CODES — `experiments/ptr-engine/longrun/cell.py`

**The table has ONE source of truth:** [`exit_codes.py`](../experiments/ptr-engine/longrun/exit_codes.py)
(`EXIT_TABLE`, plus the derived `EXIT_CODES` / `EXIT_NAMES` views). This document, the
conductor's own docstring, the `--dry-run` printout and the tests all read that table — none
of them types it again. A table duplicated in prose and in code is two tables, and they will
disagree; that is how `7` came to be declared by a table that nothing raised.

Print it from the code, not from this page:

```
python3 experiments/ptr-engine/longrun/exit_codes.py        # full table + action per code
```

Verification — `experiments/ptr-engine/longrun/tests/test_exit_codes.py`, four guards, all offline (16 tests, `python3
experiments/ptr-engine/longrun/tests/test_exit_codes.py`):

0. **external codes are owned, not exempted** — code 13 (`tree-moved`) is declared by the
   table but raised by `tools/tree_freeze.py`, so `EXTERNAL_CODES` names its owner; the
   scan excuses it only for that reason and still fails if `cell.py` raises it, or if its
   owner re-types the literal instead of importing the constant.
1. **set equality, both directions, against `cell.py`** — the codes some raise site can
   produce (`Abort(...)`, `_enforce(..., code)`, `sys.exit`, `SystemExit`, and `main()`'s
   integer returns, parsed from the AST) equal `EXIT_TABLE`'s keys. An extra code (raised,
   undeclared) fails and a missing one (declared, unraisable) fails.
2. **the propagation is not taken on faith** — `run_longrun.py`'s exit-bearing functions
   are scanned too, and the test fails if a `RUNNER_CODES` member is no longer returned by
   the runner, or if the runner returns a code that is neither propagated nor listed in
   `RUNNER_MAPPED_TO_CRASH`.
3. **`7` is reachable** — two injected write failures (an `--out-dir` that is a regular
   file, a directory where `cell-X-S.json` must go) both abort with 7 naming the artefact.
4. **the runner's own `EXIT_*` constants are checked by name** — a code that travels
   through a tuple (`EXIT_CAP_DIVERGENCE`) is invisible to a `return` scan, so the constant
   itself must be propagated or mapped; removing the `9` mapping makes this fail.
5. **this page is a view, not a second table** — its `| code | \`name\` |` rows are parsed
   and compared to `EXIT_TABLE`, so a stale row fails the suite.

## The table

Line numbers were refreshed at unit `EXIT-CODE-TABLE-2` (2026-10-26) after `cell.py`'s
`exit_codes` import was made importable from another cwd; the symbol names are the stable
reference, the numbers are a convenience.

| code | name | when it fires (condition) | raise site in `cell.py` | what a reader should do next |
|---|---|---|---|---|
| 0 | `ok` | the cell finished, or `--dry-run`/`--offline` completed | `main()` `return 0` (lines 1300, 1430) | read the record in `--out-dir`; nothing to repair |
| 1 | `internal-error` | a non-`Abort` exception escaped a stage — a **harness defect**, never a measurement | `main()`'s `except Exception` → `return 1`; the full traceback is printed and the run is named (`arm=… fixture=… out_dir=…`) | read the traceback on stderr and the last stage line; do **not** re-run the cell hoping for a different result |
| 2 | `preflight` | fixture unparseable, no checkpoints, truth underivable, answer contract absent, harness file missing/mismatched digest, unreadable gate artefact — **not** a G3 prereg refusal (that is `12`). **Also argparse usage errors** (argparse exits 2 by its own convention) | `preflight()` 211–277, `stage_harness()` 293/303, gate-artefact loaders 501–505 and 622–631, `eval_gate_ledger()` 706/720, offline rows missing 1253 | fix the fixture/harness/artefact or flag named in the message; no request was sent, so nothing was measured |
| 3 | `budget` | the runner's own `--dry-run` (+10 % headroom) exceeds `--budget`, or the dry-run reported no `would_send_total` | `stage_budget()` 316, 325, 347 | raise `--budget` or lower `--turns`/`--reps`/`--arm`; never edit the runner |
| 4 | `ledger-cap` | G1: `spent + would_spend + reserve > cap`, or the ledger's counter could not read its row files (uncountable ⇒ refuse) | `_enforce(eval_gate_ledger(...), …, 4)` 1312; runner rc=4 propagated at `stage_run()` 926 | extend or repair the ledger artefact named in the message; a refusal here is the budget being honest |
| 5 | `runner-crash` | `run_longrun.py` exited with a code that is not one of its own guard refusals (including rc=1 from a bare `raise SystemExit(str)`), or any unmapped runner rc | `stage_run()` 926 with `code = rc if rc in _RUNNER_CODES else 5` | read the runner's stderr in the cell record; rows written before the crash are kept at the path named |
| 6 | `runaway` | the runner's `--runaway-turns` guard fired, or the live turn-wall cap ended the cell | `stage_run()` 926 propagating runner rc=6 | inspect rows up to the last turn; a runaway is a client/harness problem, fix it before spending another request |
| 7 | `unwritable` | **an artefact the cell is required to write could not be written**: the runner's row file (runner rc=7), or stage 7/7's record directory, cell JSON or cell markdown | `stage_record()` 1065 (out-dir), 1074 (JSON), 1123 (markdown); `main()` 1406 (final JSON); `stage_run()` 926 propagating rc=7 | fix the path/permissions/space named in the message and re-run. The measurement may exist but its evidence is **not on disk** |
| 8 | `projection` | G2: projected wall clock (`projected_requests × projected turn wall`) > `--max-wall` | `_enforce(eval_gate_projection(...), …, 8)` 607 and 1319 | raise `--max-wall`, or recalibrate `--projected-from`/`PROJECTION.json` from measured rows; never shrink the projection to fit |
| 9 | `inconsistent` | the grader and the analyser disagree about whether anything was decided at all, and `--allow-inconsistent` was not passed | `stage_consistency()` 1053 | find out why the two populations differ before believing either number; the override records the contradiction, it does not resolve it |
| 10 | `grade` | `grade_v5.py` itself exited non-zero (e.g. `fixture_truth_mismatch`) | `stage_grade()` 943 | re-run `grade_v5.py` on the same rows/fixture: the grading needs re-running, not the cell |
| 11 | `analyse` | `analyze_stats.py` itself exited non-zero (e.g. not a `grade_v5` document) | `stage_analyse()` 966 | re-run the analyser on the same rows and grade document; the grade stands, so no request is needed |
| 12 | `prereg` | G3: the cell's own n cannot support the hypothesis it would claim — absent `--hypothesis` (silence), `--hypothesis none`, an unknown name, H1 with n < 60, or H3 with < 8 checkpoints | `_enforce(eval_gate_prereg(...), "3c/7 G3 prereg gate", 12)` | name the claim with `--hypothesis`, or raise `--turns`/`--reps` until n meets PARM-1's minimum; never lower the minimum to fit the cell |
| 13 | `tree-moved` | `tools/tree_freeze.py` re-hashed a freeze and at least one recorded file is `moved` (sha256 changed) or `deleted` — the tree moved while the audit ran. **Not** a command failure: a result judged against moved bytes is UNSTAMPED, not FAIL | `verify()` returns `exit_codes.EXIT_TREE_MOVED`, declared in `EXTERNAL_CODES`; `cell.py` never raises it | re-run against the settled tree (re-freeze first); never report the movement as the claimant's failure |

| 14 | `capgate-unrecorded` | the cap gate refused: requests reached the wire whose rows were not written, so the ledger understates the spend (`delta < 0`), or a row no request bought (`delta > 0`), or the run could not record its final counts. Reached by **aborted** (runaway) runs too — they reconcile before they exit | `stage_run()` via `RUNNER_MAPPED_TO_CELL[9]` → `Abort(exit_codes.EXIT_CAPGATE_UNRECORDED, "4/7 run", ...)`; the runner itself still exits 9 (`EXIT_CAP_DIVERGENCE`), never renumbered | read the quoted `CAP GATE UNRECORDED` line (`delta`, `used_in_run`, `rows_gained`, `headroom_before/after`); do **not** re-run before reconciling — the ledger would grant headroom that does not exist |

## G3's own code (`12`)

`GATE-CHAIN-FIX` split the prereg refusal out of `2`, so a caller can tell "your fixture is
broken" (`2`) from "your n cannot support your claim" (`12`). The raise site is
`_enforce(eval_gate_prereg(...), "3c/7 G3 prereg gate", 12)`. No other code was renumbered:
`11` stays analyse and nothing else moved. The source-scan equality test balances in both
directions (a declared-but-unraised code and a raised-but-undeclared code each fail).

## How `7`, `1` and `11` were resolved

These were the three holes the scan found. Each was decided explicitly; none is decorative.

- **`7` — declared, never raised. KEPT, and made real.** The record stage's `OSError` used to
  escape uncaught, which surfaced as an undeclared `1`: the one stage whose failure this
  project has already paid for (three cards died at the handoff, one wrote a handoff a minute
  after its card failed) reported itself as a generic crash. `stage_record()` now wraps the
  `--out-dir` creation and both writes, and `Abort(7, "7/7 record", …)` names the artefact it
  could not write; `main()`'s final record write does the same. `7` also remains the code the
  runner's rc=7 propagates as. Proven reachable by
  `experiments/ptr-engine/longrun/tests/test_exit_codes.py::CodeSevenReachableTests` (a directory where the JSON must go, and
  an `--out-dir` that is a regular file: both abort with 7 naming the artefact).
- **`1` — raised, never declared. DECLARED as `internal-error`.** The paths that produced it
  (an unclassified exception) are not converted to a stage code, because pretending a bug is a
  named refusal is worse than naming the bug: `main()` now catches `Exception`, prints the
  **full traceback**, prints a line identifying the run (`arm/fixture/out_dir`), and returns
  `1` deliberately. Declared, reachable, and no longer indistinguishable from a crash.
- **`11` — raised and declared in prose, but absent from every machine-readable table.**
  Declared properly: `analyze_stats.py` exiting non-zero, action = re-run the analyser.
  (The card's premise that `11` was undeclared was true of the *code*, not of the docstring:
  the prose table listed it, which is exactly the drift this unit removes — prose is not a
  table a program can check.)

## Stage modules: what they exit with, and who consumes it

Enumerated from source, not from documentation (`sys.exit(`, `raise SystemExit(`, `Abort(`):

| module | its own exits | consumed by the conductor as |
|---|---|---|
| `run_longrun.py` | **0** success; **2** usage/fixture; **3** cap-gate usage (no rows); **4** cap refusal; **5** cap-gate rows unreadable / resume-manifest mismatch; **6** runaway / summary abort; **7** the rows could not be written (`report_run`); **9** `EXIT_CAP_DIVERGENCE` — the run's request count and its rows disagree; `raise SystemExit("RESUME REFUSED…")` (a bare string, so the process exits **1**); uncaught traceback → 1 | 2/3/4/5/6/7 propagated unmodified (`RUNNER_CODES`); **1 and 9 are NOT propagated** — `stage_run()` reports 5 (see `RUNNER_MAPPED_TO_CRASH`), because a runner 9 would be read as the cell's unrelated 9 |
| `grade_v5.py` | `sys.exit(str)` → 1, `SystemExit("fixture_truth_mismatch…")` → 1, `sys.exit(main())` → 0/1 | **10** |
| `analyze_stats.py` | `raise SystemExit("--grade … is not a grade_v5 document")` → 1, `sys.exit(main())` | **11** |
| `score_longrun.py`, `grade_v2/v3/v4.py`, `adapt_*.py`, `analyze_longrun.py`, `project_wallclock.py`, `tools/prompt_at_turn.py` | their own CLI codes | **not called by `cell.py`** — they are not conductor codes and are deliberately absent from the table |

## Conflicts with other cards

### The one real collision: `9` means two things

`run_longrun.py` defines `EXIT_CAP_DIVERGENCE = 9` (line 287) and returns it when the run's
own request count and the rows it wrote disagree — a reconciliation **bug**, the runner's
docstring says so. The cell's `9` is `inconsistent` (grader vs analyser population),
introduced by `DECIDABILITY-SEAM`. The two are unrelated refusals wearing one number.

- **What the conductor does:** `stage_run()` maps any runner code outside `RUNNER_CODES` to
  **5**, and `9` is outside it, so a runner cap divergence surfaces as `runner-crash` with
  the divergence named on the runner's stderr (kept verbatim in the cell record). The cell
  itself never emits `9` for a cap divergence, so **a reader of this table is not misled
  about a code the conductor returns**.
- **What is wrong:** `run_longrun.py`'s numbering, not the cell's table. `9` there is a
  second meaning on a number another card owns. **Unit `EXIT-CODE-TABLE-2` did not renumber
  it**: fixing it means changing a code a different card's document pins, which is that
  card's decision. The remap is declared in `exit_codes.RUNNER_MAPPED_TO_CRASH` and the scan
  test fails if the runner returns such a code without a declared mapping — so this cannot
  silently become a third thing.

### Where `docs/GATE-CHAIN.md` and this table disagree (both reported, neither edited)

`docs/GATE-CHAIN.md` is the table of record for the **gates**, and its §2 agrees with this
one code-for-code (0/2/3/4/5/6/7/8/9/10/11, including the 5/6 → 10/11 renumber). Two
disagreements remain, both in GATE-CHAIN's §1 chain diagram, which this unit did **not**
edit:

1. §1's stage `7 record` row says `JSON + markdown —` (no exit code). Since `7` was made
   reachable, the record stage **can** exit 7 — its own §2 row already says so
   ("record refusal … `run_longrun.py` / cell"). The diagram is the stale half of that
   document.
2. §1's `4 run` row lists the runner as exiting `4 / 5 / 6 / 7`. From source it also exits
   **9** (`EXIT_CAP_DIVERGENCE`), which the cell then maps to 5 — see above. The diagram
   omits it, and so does GATE-CHAIN's §2 ownership note that gives `9` only to the cell.


- `WIRE-GATES` owns `2/3/4/5/6/7/8` in the preflight chain; `WIRE-CAP-GATE` owns `4`;
  `DECIDABILITY-SEAM` introduced `9`. **No code was renumbered here.** This unit only added a
  *raise site* for `7` (the record stage) inside the meaning `7` already had ("an artefact the
  cell must write could not be written" — the table's own prose said "stage 7 could not
  write"), and added a declared raise site for `1`.
- One collision is real and now stated rather than hidden: **argparse exits 2** for a usage
  error, the same number as a preflight refusal. Both mean "the invocation was refused before
  anything was measured", so they share the row; if a future card separates them it must take
  a new number and update `EXIT_TABLE` (the scan test will make the old table fail).
