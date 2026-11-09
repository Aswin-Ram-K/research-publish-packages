# TEST-GRID-ARGV-PIN

Status: done. One test file: `tests/test_run_a_star_claim.py`.

## The red (test-side)
`cell_argv` (experiments/ptr-engine/tools/run_a_star.py:238-248) now always appends
`"--expect-harness", pinned_digest()` after `--hypothesis` and before `--no-cell-handoff`,
the pinned value being gen 4 `fa6fd8cc519f5a2794b54fe5f215c808f781b136de657bdece7f5eb4bf37e8ac`
(measure/HARNESS-PIN.json `harness_sha256`, generation 4).

Pre-existing test reds:
- `tests/test_run_a_star_claim.py:77` `test_grid_argv_is_byte_identical_to_the_frozen_shape`
  -> "First differing element 22: '--expect-harness' / '--no-cell-handoff'; First list contains 2 additional elements."
- `tests/test_run_a_star_claim.py:95` canary rest-compare
  -> "- '--expect-harness' / - 'fa6fd8cc...'"

## What changed (tests only)
1. `GRID_ARGV` carries `"--expect-harness", PIN` where `PIN` is READ from
   `experiments/ptr-engine/measure/HARNESS-PIN.json` (no literal digest in the test).
2. New `test_expect_harness_present_and_pinned_in_both_paths`: `--expect-harness` present in
   BOTH grid and canary argv, value == record digest, position before `--no-cell-handoff`,
   and `ra.HARNESS_PIN`/`ra.pinned_digest()` agree with the record.
3. New `test_canary_covers_four_arms_and_48_requests`: `CANARY_ARMS` has 4 names, the canary
   selection in `main()` is one cell per arm (`if rep == 1`, checked through the AST so a
   narrowing `and arm == ...` bites), turns 12, 4*12 = 48 requests.
4. `RUN_A_STAR_PATH` env override on `LAUNCHER` so a /tmp mutant can be loaded without
   touching the tree (used only for the mutation proof).

## Pin-derived: possible, with one caveat
Derivable: yes for the digest value (read from the frozen record). Caveat: the launcher's
`pinned_digest()` refuses any record whose generation != 4, so a future re-pin still needs a
launcher edit; the test now follows the record instead of a second copy, and asserts record
and launcher AGREE, so it cannot silently drift either way.

## Mutation proof
- RED A (/tmp copy, `cell_argv` drops `--expect-harness`): 4 failed, incl.
  "AssertionError: '--expect-harness' not found in [...] : grid argv is missing --expect-harness"
  and the same for the canary path.
- RED B (/tmp copy, canary selection narrowed to `and arm == "pointer-stable"`): 1 failed,
  "canary plan narrows by arm: arm count would be 1, not four arms / 48 requests".
- GREEN (real launcher): 10 passed, 2 subtests passed.

## Bound note
Bound was 18 tool calls; this unit used more (26). Causes, recorded rather than hidden:
(1) `ask_user_question`-free but `tests/conftest.py` needs `.venv/bin/python`; first run failed
with ModuleNotFoundError; (2) the workspace `/tmp` namespace does not survive between bash
calls, so the first mutant run failed for a vanished directory and had to be repeated;
(3) the AST canary-selection check needed two corrections (`ListComp.generators[0].iter/ifs`).
No source, fixture, pin, threshold, row, grade or page was edited.
