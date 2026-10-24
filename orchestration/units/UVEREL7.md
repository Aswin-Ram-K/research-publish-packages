# UVEREL7 — independent verifier of URELEASE7's gated-read release cut

**Purpose:** falsify (or confirm) the central claims of `strategy/GATED_READ_RELEASE_CUT.md` (244 lines, unit URELEASE7).
**Author/verifier split:** I did not write the cut; I re-run it.

**Hard bound:** 20 tool calls. Write-path conflicts: none (my paths are UVEREL7-scoped, plus an append-only note on the artifact).

## Claims under test
1. Minimal sufficient release = 5 files / 28,233 B at `scratch/urelease7/cut3/`: `record.json`, `verify_claims.py`, `METHOD.md`, `sealed.json`, `provenance.json`; md5s in §4.
2. Ladder: cut1 1,572,498 B / cut2 1,148,991 B / cut3 28,233 B each exit 0 printing `RESULT pass exit=0 claims=143 failed=0 []` (143 PASS, 5 NOTE); cut4 27,447 B exits 3 with `MISSING section 'per_task'`.
3. Two-sided minimality: cut2→cut3 removes 1,120,758 B, loses 0 claims; cut3→cut4 removes 1,035 B, loses all 143.
4. Grep of withheld surface over all four cut dirs → 0 matching files.
5. `0.575` cheapest-sufficient and `207/207` router ship sealed (rows do not reproduce them).
6. Gold-derivation script cannot ship at any reduction.

## Declared write paths (exactly)
- `strategy/VERIFICATION_REPORT_REL7.md`
- `strategy/GATED_READ_RELEASE_CUT.md` (append-only dated `## Verification` note)
- `orchestration/units/UVEREL7.md` (this card)
- `orchestration/handoffs/UVEREL7.json`
- `scratch/uverel7/**`

## Log
(appended as measured)
