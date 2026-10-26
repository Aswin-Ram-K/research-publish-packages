# UNIT REPRO-IN-RELEASE — prove a third party can re-derive the numbers from the shipped tree

**Date:** 2026-10-24 · **Status:** done · **Bound:** 25 tool calls (used ~20)

## Purpose
`release/v0.1/` is the publication artefact (943 manifest files, 61,035,244 bytes) and had never been
*run*. Its gates prove no secrets and no unresolved citation markers, but the package's central claim is
that every number re-derives from raw rows. This unit runs the package's own tooling from inside the
release tree and reports, without repairing, what breaks.

## Method
From `cd release/v0.1`, with `PYTHONDONTWRITEBYTECODE=1`:
`verify_package.py`, `recompute.py all`, `recompute_r2.py all`, and the three line-pinned guards
(`test_gap_closure_ledger.py`, `test_g5_fanout_attribution.py`, `test_paper_g3_bands.py`).
Where a run failed on a missing file, the same script was re-run in a **hard copy** of the tree at
`/tmp/release-copy` with only `state/` supplied from outside, to separate "missing package data" from
"wrong numbers". A symlink mirror was tried first and rejected: `Path(__file__).resolve()` follows
symlinks, so a symlinked `papers/` resolves back to the release tree and silently reuses it.

## Findings
- `verify_package.py`: **exit 0**, PASS, 69 claims / 69 mapped 1:1 / UNVERIFIED none.
- `recompute.py all`: **exit 1** at claim 65 of 69 — `state/config/rows.jsonl` not shipped (0 MANIFEST entries under `state/`).
- `recompute_r2.py all`: **exit 1**, same missing file (`recompute_r2.py:557`).
- `test_gap_closure_ledger.py`: **exit 1**, `state/gap-ledger.json` missing; with `state/` supplied it still fails 6/8 on `orchestration/**` and `scratch/**` refs a release cannot carry.
- `test_g5_fanout_attribution.py`: **exit 0**, 4 passed.
- `test_paper_g3_bands.py`: **exit 0**, 13 passed.
- With `state/` supplied and shipped bytes untouched: `recompute.py all` exit 0 (`COVERAGE GUARD PASS 69 claims documented, 67 runnable here + 2 script-backed`), `recompute_r2.py all` exit 0 (61/38/48/75/85/70/50 all PASS).

## Verdict
**NO as shipped; YES WITH CAVEATS** once `state/config/rows.jsonl` and `state/gap-ledger.json` ship with it.

## Constraints honoured
No file under `release/v0.1/**` was written; no `papers/**` edit; `/home/zer0null/Duval` untouched;
no model server restarted, no `/flush_cache`, no live call. No `__pycache__` appeared in the release tree.

## Deliverables
`release/REPRO.md`, this card, `orchestration/handoffs/REPRO-IN-RELEASE.json`.
