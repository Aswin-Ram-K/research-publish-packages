# VUFIXTREE1 — independent verification of UFIXTREE1 (authoritative release tree)

Status: **DONE — verdict `partial`**. Report: `strategy/VERIFICATION_REPORT_AUTHORITATIVE_TREE.md`.
Bound: 20 tool calls; used 12 (33 subprocess tool invocations). Nothing edited under `papers/`, in any
candidate tree, or in the build script; `/home/zer0null/Duval` never touched (no git invoked at all).

## Claims and dispositions
1. `scratch/uneutral10/package` is the only candidate reproducing the published values → **table
   reproduced cell-by-cell**, but "only tree" **overstated** (see 7).
2. Published values at `papers/encoder-crossover-190/CLAIMS.md:108-111` → **mis-sourced**: paper prints
   `agreement 0.3421` (:110) and `AB 0.3684` (:111), not the full-precision strings claimed; the two κs
   are printed at full precision (:108, :110). **contradicted** as sourcing.
3. Pin line `:134` → **confirmed** verbatim, but line `:39` comment also names the same tree → two edits,
   one functional. **overstated** as "one-line".
4. `SHIP_STAGED` needs no re-derivation → **confirmed**: path sets identical (`diff` of 29 sorted paths),
   29 `SHIP_STAGED` entries match the 29 files. Hit-count annotations **unverified**.
5. `tests/test_build_wiring.py` 11 passed → **confirmed** 11 passed as-is (`PYTHONPATH=src`) and 11 passed
   with a re-pinned copy at `scratch/vufixtree1/UBUILD1.repin.sh` (env `UWIRE3_BUILD_SCRIPT`).
6. Fixture digest identical in all five → **confirmed** (all five recompute logs print
   `c7696edc0e71d83faafc2e489925788e0f36c6af94913674f8953718352c9a55`; computed at runtime, present in
   no file). It is a constant and cannot discriminate; the verdict survives without it.
7. Sixth candidate → **found**: `scratch/uneutral9/package` (distinct in 6 files from uneutral10) also
   reproduces all four values with rc 0/0/0 and PRESERVED True, as do `scratch/uneutral10/before` and
   `scratch/uver32/{after,idem1,idem2,inject}` (byte-identical copies of it). "Only tree" is false
   beyond the enumerated five.

## My table (all cells match UFIXTREE1's)
| tree | rc | PRESERVED | routeA κ | A/B mutual |
|---|---|---|---|---|
| scratch/urecut1/package | 0/0/0 | True | 0.32520740993294694 | 0.3526315789473684 |
| scratch/uneutral10/package | 0/0/0 | True | 0.3248813212427869 | 0.3684210526315789 |
| scratch/ufix31/pkg | 1/0/0 | False | 0.31988636363636364 | 0.3473684210526316 |
| scratch/utool1/tree-six | 0/0/0 | True | 0.32520740993294694 | 0.3526315789473684 |
| scratch/udtag1/tree-five | 0/1/1 | True | 0.32520740993294694 | 0.3526315789473684 |

Unexecutable trees: none (udtag1's parse_fixture/compare exit 1 on missing
`second-labeller/reflex-decisions.sandbox.ts` and `second-labeller/cases.json`).

## Extra finding
`scratch/uneutral10/package/verify/recompute-claims.py` embeds stale "published" constants
(`0.3252`, `0.3526`), cites `CLAIMS.md:108/:109` for values at `:110/:111`, and prints
`A/B mutual agreement … reproduced=False` while the aggregate still prints `ALL CLAIM NUMBERS
PRESERVED: True` (that aggregate tests recompute-vs-shipped, not paper truth).

## Re-pin safety
**Safe to apply.** Edit `:134` (functional) and `:39` (comment). Wiring test green on a re-pinned copy.
