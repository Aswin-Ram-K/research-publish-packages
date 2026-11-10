# Verdict semantics — a refusal is not a failure

**A closure whose verdict row exits in the refusal set is *unstamped*, not *failed*: nothing about the card's own artefact was measured, and the fix is to record a command that measures the card's own artefact.** (Replace a row that exits `2, 3, 4, 7, 8, 12, 13, 14` with one that runs the artefact's own check; a row that exits `2` may also be argparse's usage error, which is the same story from the reader's side.)

The numbers are not defined here. They are defined once, in
[`experiments/ptr-engine/longrun/exit_codes.py`](../experiments/ptr-engine/longrun/exit_codes.py)
(`EXIT_TABLE`, the single source of truth), and classified by
[`experiments/ptr-engine/tools/verdict_semantics.py`](../experiments/ptr-engine/tools/verdict_semantics.py).
`tools/verdict_semantics.py` imports that table and refuses to load if this document and the table
disagree about which codes exist; `experiments/ptr-engine/longrun/tests/test_verdict_semantics.py` parses the table below and fails if
the two drift.

## The partition

| Code | Name | Measures the work? | Verdict |
|---|---|---|---|
| `0` | `ok` | measures | `verified_pass` |
| `1` | `internal-error` | measures | `verified_fail` |
| `2` | `preflight` | refuses | `unstamped_refusal` |
| `3` | `budget` | refuses | `unstamped_refusal` |
| `4` | `ledger-cap` | refuses | `unstamped_refusal` |
| `5` | `runner-crash` | measures | `verified_fail` |
| `6` | `runaway` | measures | `verified_fail` |
| `7` | `unwritable` | refuses | `unstamped_refusal` |
| `8` | `projection` | refuses | `unstamped_refusal` |
| `9` | `inconsistent` | measures | `verified_fail` |
| `10` | `grade` | measures | `verified_fail` |
| `11` | `analyse` | measures | `verified_fail` |
| `12` | `prereg` | refuses | `unstamped_refusal` |
| `13` | `tree-moved` | refuses | `unstamped_refusal` |
| `14` | `capgate-unrecorded` | refuses | `unstamped_refusal` |

## Why each side is where it is

- **Measures (`0, 1, 5, 6, 9, 10, 11`).** The card's artefact was produced and then judged: `0` the
  run completed and the gates wrote their verdicts; `10`/`11` the grade or analyse stage ran and
  returned a non-pass; `1`/`5` the stage crashed while handling the artefact (a crash on the artefact's
  own code path is evidence about that code path); `6` the run went runaway, which is a measured
  property of the run; `9` grader and analyser disagree about the same rows, which is a measured
  inconsistency in the artefact.
- **Refuses (`2, 3, 4, 7, 8, 12, 13, 14`).** The conductor stops before the artefact is judged: `2`
  preflight (harness/prereg prerequisites absent; also argparse's usage error, an unmetered misuse),
  `3` request budget, `4` ledger cap, `7` the artefact could not be written at all (so nothing exists
  to measure), `8` projection mode declined to run, `12` prereg refused the arm, `13` the acceptance
  tree moved under the card so the pinned tree could not be stood up, `14` the cell reports the
  runner's cap-gate reconciliation refusal at cell level (the runner still exits `9`): the ledger and
  the rows disagree about money, so nothing was measured. None of these is evidence about the card's
  work.
- **Borderline calls, recorded rather than hidden.** `6` is treated as measuring because the run
  really executed and its length was the thing that failed; `7` is treated as a refusal because an
  unwritable artefact leaves nothing to measure; `9` is treated as measuring because the disagreement
  is *between two measurements of the same rows*. `2` carries two meanings (preflight refusal and
  argparse usage error); both refuse before measuring, so one verdict is honest.
- **`13` and `14` have landed.** Both are in `EXIT_TABLE` today; the table above classifies them, and
  the test fails if either is ever removed from `EXIT_TABLE` while remaining here, or the reverse.

## How to read a closure

1. Take the command, exit code and sha from the closure's own row.
2. `classify(exit_code)` — if it is `unstamped_refusal`, the column is not a quality statement, and
   the card must not be re-charged as a failure; it must be re-run with a command that measures its
   own artefact.
3. Only `verified_pass` / `verified_fail` may be read as statements about the card's work, and even
   then only against the row's `sha`.

Evidence for this partition: `RECORD-REFRESH` settled `failed exit-4` while its handoff showed
insertions-only edits, matching prefix sha256 on both files, its guard exit 0 before and after, and a
clean self-test; `RECLAIM-ACCEPTANCE` settled `failed no-verdict` with `command: null`. In both cases
the row refused before measuring, and the work was not what failed.
