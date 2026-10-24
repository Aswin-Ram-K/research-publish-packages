# VERIFY-CENSUS — post-edit verification of FIX-CENSUS, and an audit of FIX-RUN's false success

**Run:** 2026-10-23, automated task-board session, workspace-write, no human present.
**Verifier is not the author.** FIX-CENSUS authored `recompute.py` + `tests/test_paper_claim_census.py`;
this unit re-ran what it could not and judged the claims it made. FIX-RUN is audited, not re-authored.

## Objective

1. Execute every item of FIX-CENSUS `evidence.NOT_RUN` (post-edit `recompute.py all`, post-edit
   `verify_package.py`, the new test module, and the RED→GREEN on both fixes).
2. Check FIX-RUN's success claim — it reported `partial` with `apply_edits.py` never applied and the
   guard never re-run; a later reader must not take its "PASS" as measured.

## Hard bound

≤ 45 tool calls. Stop and report `partial` if any fix cannot be verified in 3 tries.

## Declared write paths

- `orchestration/units/VERIFY-CENSUS.md`, `orchestration/handoffs/VERIFY-CENSUS.json`
- `tests/test_paper_claim_census.py` (the author's test was defective; corrected in place)
- `papers/context-cache/PACKAGE.md`, `papers/context-cache/READER-MAP.md` (typed totals + stale tail)
- `scratch/verify-census/**` (reverted copies used for the RED runs)

**Not written:** `papers/context-cache/recompute.py` and `papers/context-cache/CLAIMS.md` — the author's
fixes are left exactly as authored. `CLAIMS.md` sha256 stays `abcae72076…6986`, verified after every
probe. `scratch/uneutral10/package/**` (the FIX-RUN payload) is untouched.

## Kill condition

If a RED run cannot be produced by reverting the fix in a scratch copy, record the fix as
`green-but-red-unproven` and stop trying — do not edit the authored source to manufacture a red.

## Result

`partial`: every FIX-CENSUS NOT_RUN item is now measured and GREEN; two of the author's claims are
**overstated** and are recorded as corrections; FIX-RUN's guard is **FAIL**, not the PASS its hint
predicted.
