# Unit PKG-VERIFY (verifier)
Bound: 14 tool calls. Automated session — no questions. Verification only; nothing under
papers/**, experiments/**, state/**, tools/** edited.

## Entry points
- `papers/context-cache/verify_package.py` — package verifier (claim census, 1:1 mapping).
- `papers/context-cache/recompute.py` — recomputes every number in `CLAIMS.md` from raw rows; one
  claim id per call, no `--all`, non-zero on mismatch.
- `papers/context-cache/coverage_guard_selftest.py`, `papers/context-cache/grid_guard_selftest.py`.
- Also present, not this pass's entry point: `recompute_r2.py`, `serving_brief.py`.

## Commands / exit codes
- `.venv/bin/python papers/context-cache/verify_package.py` → EXIT=0.
  `verify_package: PASS — 69 claims in CLAIMS.md, 69 mapped 1:1, 8 script-backed + 61
  recompute.py-backed functions all present, every referenced cell has rows, UNVERIFIED: none`
- `recompute.py <id>` over all 65 ids → 65/65 EXIT=0, 0 mismatch.
- `recompute.py --all` → EXIT=2 (`unknown claim '--all'`): undocumented flag, not a data failure.
- `coverage_guard_selftest.py` EXIT=0 (`SELFTEST PASS`); `grid_guard_selftest.py` EXIT=0
  (`GRID GUARD PASS 34 file(s), 9121 sglang cached_tokens, every one a multiple of 64`).

## Spot-checks (independent of recompute.py)
1. C05 `B/A = 3.3133` (U4b-rows). Rows sha256 verified `c16d1783e425…3246`, 4600 B / 24 lines.
   Independent means A=636.0625, B=864.125, C=570.65 ms → B/A = 1.3586, C/A = 0.8971.
   MANUSCRIPT.md:176 marks the cell's 3.3133 **"(superseded)"**; :169 reports G5's race-free 6.744.
   NOT re-derived from the cited rows, no visible path to 3.3133. Flagged, not asserted wrong.
2. C62 range +134.6…+747.2 / band −927…+5,473 re-derived from recompute.py's row read: matches.
   Independent pass on G1/rows.jsonl (sha256 `9242ad38…7ae66`, 264 rows) could not reproduce C44's
   `mean gross E=1,728.0 / F=1,664.0 / ratio=1.0384615` (saw E=4901.45, F=5003.03): recompute.py
   uses an undisclosed `gross_*` column, so agreement is recompute-internal, not independent.

## Verdict
`partial` — verifier and both guards exit 0, 65/65 recomputes exit 0; spot-check 1 cannot be
re-derived from its cited rows, spot-check 2's independent leg is blocked by an undisclosed column.
