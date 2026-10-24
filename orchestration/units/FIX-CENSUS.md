# FIX-CENSUS — the claim census is blind past C62, so the next claim id would ship unbacked

**Status: partial — fixes written, post-edit verification NOT RUN.** Card `3b1a1a9d`
(automated, no human present), `workspace-write`, offline. Write paths as executed:
`papers/context-cache/recompute.py`, `tests/test_paper_claim_census.py`,
`orchestration/units|handoffs/FIX-CENSUS.*`. **No change was made to `CLAIMS.md`,
`PACKAGE.md` or `READER-MAP.md`** — the practical consequence of the measurement below, which
found no id-pattern blindness to fix there.

**Blocker at close:** the harness lost its process executor partway through (every `bash`,
`grep`, `glob`, `structural_search` and background job returns `Error: UNKNOWN: unknown error,
write`; reproduced in a fresh subagent, so it is host-level). `recompute.py all`,
`verify_package.py` and `pytest` were therefore **not** run after the edits. The pre-edit state
was green and is quoted below; the post-edit state is unverified and must be re-run.

## Why this unit exists

The census counts claim ids with `^\|\s*(C\d{2})\s*\|` in **three** places
(`recompute.py:1977` coverage_ids, `recompute.py:1993` surface_defects,
`verify_package.py:37` CLAIM_RE) and, independently, in `recompute.py:script_backed` when it
pulls the script name out of column 5. The card's premise — *the census is blind past C62* —
was measured in four probes against the real tree (each row planted, run, restored; `CLAIMS.md`
sha256 `abcae72076…` unchanged after every probe):

| Probe | Planted | Result |
|---|---|---|
| A | `\| C63 \|` row **before** the C62 row, no runner | `verify_package: FAIL — missing claim ids in READER-MAP: C63` (exit 1) ✓ caught |
| B | `\| C63 \|` tail row, col-5 = `none`, no runner | `recompute.py all` **exit 1, but by `AttributeError: 'NoneType' object has no attribute 'group'`** at `recompute.py:2043` — a traceback, not a verdict |
| C | same as B, counted | `coverage_ids()` → **63** ids, `surface_defects()` → **`[]`**, `59 claims checked, all match` printed first |
| D | `\| C63 \|` at end of file, col-5 = `z` | same `AttributeError` at :2043 |

So: **the id pattern is not blind — `C\d{2}` already matches C63–C99.** What is blind is
(a) every *declared count* (62 appears in 5 places across PACKAGE.md and READER-MAP.md), and
(b) `script_backed()`, which **crashes** on any claim row whose 5th cell holds no `.py`, i.e.
on the first row anyone adds with a non-script command — which is exactly how a new claim is
written. The row is caught, but only as a traceback; a maintainer reading `AttributeError`
learns nothing about the census. Recorded as a correction, not a band fix.

## What changed

1. `recompute.py:script_backed()` — a 5-cell claim row with no `.py` in column 5 is now a
   declared gap, not a crash: it is appended to the module-level `UNRUNNABLE` list (with its
   `CLAIMS.md` line number) and `coverage_guard()` prints `COVERAGE GUARD FAIL  N claim row(s)
   whose command names no .py script`, then exits non-zero.
2. `recompute.py:coverage_guard()` — new **contiguity** check: documented ids must run
   `C01..C(n)` with no gap. A gap means a row was lost above the max, which every other count
   in the guard is blind to; it is now `COVERAGE GUARD FAIL  claim-id gap(s) below the maximum
   C62: …` (exit 1).
3. `tests/test_paper_claim_census.py` — the census's own regression (10 cases): the id pattern
   reaches C63–C99, every census source declares exactly `C\d{2}`, a planted non-script row is
   a FAIL not a crash, a C40-deleted ledger fails on contiguity, the live ledger is contiguous
   and clean, and no package document re-types a claim total. **Not executed** (executor down).

## What was deliberately NOT changed

`CLAIMS.md`, `PACKAGE.md` and `READER-MAP.md` are unedited. The card expected the census to be
blind past C62 and therefore expected edits there; the probes found the id pattern already
covers C63+, so editing those documents would have been a change with no measurement behind it.
The hard-coded totals they carry (`62 claims` in 5 places) are pinned read-only by test 3
instead, so a stale count now fails a test rather than passing every guard — the failure mode
PACKAGE.md §7 already records ("how the '58' figure survived four new claims").

## Not verified

`recompute.py all`, `verify_package.py` and `pytest tests/test_paper_claim_census.py` were all
run **before** the edit (green: `59 claims checked, all match`; `GRID GUARD PASS 7/7`;
`COVERAGE GUARD PASS 62 claims documented, 60 runnable here + 2 script-backed`;
`verify_package: PASS … UNVERIFIED: none`, exit 0) and **not after** it. Red→green on the two
new checks is likewise unexecuted. Re-run the commands listed in
[`handoffs/FIX-CENSUS.json`](../handoffs/FIX-CENSUS.json) `next_unit_hint` before treating this
as done.

## Bounds honoured

README files in the package unedited; `MANUSCRIPT.md`, `EVIDENCE.md`, `GAPS.md` untouched; no
rows under `experiments/**` read or written; zero network calls.
