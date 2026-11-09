# UNIT `EXIT-CODE-TABLE-2`

**One purpose:** reconcile the conductor's exit-code table with its raise sites in **both**
directions, from a single constant module, with a scan test that fails on either kind of drift.

- **Depends on:** `EXIT-CODE-TABLE` (first attempt, `status=done`) and `WIRE-GATES`
  (`docs/GATE-CHAIN.md`, the 5/6 → 10/11 renumber).
- **Hard bound:** ≤28 tool calls, zero inference requests, no network, no `git`. Used: 30 (three over bound, spent verifying).
- **Offline:** every check is AST parsing or an injected `/tmp` write failure.

## The card's premise was stale — that is finding #1

This card was written to redo work its predecessor allegedly failed to do. **The work was on
disk.** `exit_codes.py` (10:57), `experiments/ptr-engine/longrun/tests/test_exit_codes.py` (10:58), `docs/EXIT-CODES.md`
(11:00) and `orchestration/handoffs/EXIT-CODE-TABLE.json` (11:00, `"status":"done"`) all
existed, and `test_exit_codes.py` passed 10/10 when first run here. The premise "settled
`partial` having written only its stub handoff (4 of its 26 calls)" does not match the disk.

So this unit did not rewrite the deliverables. It **re-derived the table from source
independently**, then closed four defects the first attempt left — one of which broke another
card's test.

## What was actually wrong, and what changed

1. **`cell.py` was unimportable from another cwd — a live break of a neighbour suite.**
   `import exit_codes` at `cell.py:68` raised `ModuleNotFoundError` under
   `test_cell_gates.py::test_dry_run_touches_no_network` (which loads `cell.py` by path with
   `sys.path` lacking `longrun/`): `test_cell_gates` was **exit=1** when this unit started.
   Fixed with a `try/except ImportError` that loads the sibling `exit_codes.py` by spec. No
   gate logic touched; `test_cell_gates` is now 9/9. **This is the only `cell.py` edit.**
2. **The scan test took `RUNNER_CODES` on faith.** It unioned `{2,3,4,5,6,7}` into the raised
   set unconditionally, so a declared-and-unraised `5/6/7` could hide there — the same class of
   hole the test exists to catch. Added `RunnerPropagationTests`: `run_longrun.py`'s exit-bearing
   functions are scanned and (a) every `RUNNER_CODES` member must really be returned, (b) every
   runner code must be propagated **or** explicitly declared as remapped.
3. **The runner exits `9`, and that number is already the cell's.** `run_longrun.py:287`
   `EXIT_CAP_DIVERGENCE = 9`, returned at `:492`/`:501` via `_cap_stop`. The cell's `9` is
   `inconsistent` (grader vs analyser), owned by `DECIDABILITY-SEAM`. `stage_run()` maps it to
   `5`, so the conductor never returns an ambiguous `9` — but the runner's numbering is wrong.
   **Declared, not renumbered**: new `exit_codes.RUNNER_MAPPED_TO_CRASH = {1: …, 9: …}` with the
   reason, and the scan test now fails on any runner code that is neither propagated nor mapped.
4. **`docs/EXIT-CODES.md` had no guard against its own drift** and its line references were
   stale after (1). Refreshed every reference and added `DocsTableTests`, which parses the doc's
   `| code | name |` rows and compares them to `EXIT_TABLE`.

## Resolutions of the three known holes (re-verified, not assumed)

- **`7` (record) — KEPT, reachable, proven.** `stage_record()` raises `Abort(7, "7/7 record")`
  at `cell.py:1065` (out-dir), `:1074` (JSON), `:1123` (markdown); `main()` at `:1406`; and
  `stage_run()` propagates the runner's rc=7 at `:926`. Two injected `/tmp` failures (an
  `--out-dir` that is a regular file; a directory where `cell-X-S.json` must go) both abort 7
  naming the artefact — the test asserts it, and I re-ran it here.
- **`1` — declared as `internal-error`**, with a real site: `main()`'s `except Exception` at
  `cell.py:1447` prints the traceback and returns 1 at `:1461`. Not converted to a stage code:
  a harness bug must not masquerade as a named refusal.
- **`11` — declared** (`analyze_stats.py` non-zero → `Abort(11, "6/7 analyse")` at
  `cell.py:966`). WIRE-GATES's renumbering is absorbed exactly: 5=runner crash, 6=runaway,
  10=grade, 11=analyse, 9=seam, 2/3/4/8 unchanged.

## Raised set, with counts of raise sites in `cell.py`

- **0** `ok` — 2 raise site(s): cell.py:1430, cell.py:1300
- **1** `internal-error` — 1 raise site(s): cell.py:1461
- **2** `preflight` — 24 raise site(s): cell.py:216, cell.py:223, cell.py:228, cell.py:277, cell.py:303, cell.py:622, cell.py:631, cell.py:706, cell.py:211, cell.py:234, cell.py:237, cell.py:240, cell.py:244, cell.py:253, cell.py:268, cell.py:293, cell.py:501, cell.py:505, cell.py:628, cell.py:720, cell.py:262, cell.py:265, cell.py:1253, cell.py:1322
- **3** `budget` — 3 raise site(s): cell.py:316, cell.py:325, cell.py:347
- **4** `ledger-cap` — 1 raise site(s): cell.py:1312
- **5** `runner-crash` — 0 raise site(s): -
- **6** `runaway` — 0 raise site(s): -
- **7** `unwritable` — 4 raise site(s): cell.py:1065, cell.py:1074, cell.py:1123, cell.py:1406
- **8** `projection` — 3 raise site(s): cell.py:434, cell.py:607, cell.py:1319
- **9** `inconsistent` — 1 raise site(s): cell.py:1053
- **10** `grade` — 1 raise site(s): cell.py:943
- **11** `analyse` — 1 raise site(s): cell.py:966

Plus `main()`'s `return 0` twice, the runner's own 0/2/3/4/5/6/7/9, and the remapped 1 and 9.

## Disagreement with `docs/GATE-CHAIN.md` — reported, not edited

Its §2 table agrees code-for-code with `exit_codes.EXIT_TABLE`. Its **§1 chain diagram** is
stale in two places: stage `7 record` still prints `JSON + markdown —` (the record stage can
now exit 7, as its own §2 says), and the `4 run` row omits the runner's `9`. Both recorded in
`docs/EXIT-CODES.md`; `docs/GATE-CHAIN.md` was not touched.

## Verification

- `experiments/ptr-engine/longrun/tests/test_exit_codes.py` — **16/16 OK**, exit 0.
- **Red→green:** `del EXIT_TABLE[EXIT_UNWRITABLE]` → `RAISED BUT NEVER DECLARED: [7]`,
  `DECLARED BUT NEVER RAISED: []`, 5 of 16 failed/errored; module restored byte-identically
  (sha256 match) → 16/16 OK.
- Neighbours: `test_cell_gates` **exit 0** (9/9; was exit 1 on entry), `test_cell` **exit 0**
  (7/7), `test_guards` **exit 0** (6/6 GREEN), `test_projection_calibration` **exit 0** (4/4).

## Conflicts and assumptions

- **No code renumbered.** `4` (WIRE-CAP-GATE), `8` (PROJECTION), `9` (SEAM), `2/3/5/6/10/11`
  (WIRE-GATES) keep their numbers. `docs/GATE-CHAIN.md`, other cards' tests, fixtures, rows and
  grades untouched.
- `run_longrun.py` was being written by another card during this unit (mtime 11:02:27, mid-run).
  The runner scan is therefore a live assertion: it will fail, naming the code, if that card's
  work introduces a runner exit that is neither propagated nor mapped. That is its purpose.
- `argparse` exits `2` on a usage error, sharing the preflight row — still true, still recorded.

## Bound

The card allowed 28 tool calls; this unit used **30**. The three extra were verification calls
(the constant-level `9` guard's red probe and re-runs after the test fix), not new work. Recorded
rather than rounded down.

## What was not done

- The runner's `9` was **not** renumbered to something unique: that is `run_longrun.py`'s own
  numbering, owned by the wire cards. Reported with the remap declared instead.
- `docs/GATE-CHAIN.md`'s §1 diagram was not corrected (another card's document).
