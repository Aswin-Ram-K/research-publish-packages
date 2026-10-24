# UVER13 — independent verification of `strategy/CPRIME_MEASUREMENT.md` (UNEUTRAL4)

**Status:** done. **Bound:** ≤40 tool calls; used 29 (incl. finite writes).
**Target:** `strategy/CPRIME_MEASUREMENT.md` sha256 `13d0712ebecf77a086747115fcda7e21d989642aa8a001e5c17d7e015f338dcb` (recomputed, matched; not edited) + `orchestration/units/UNEUTRAL4.md` + `orchestration/handoffs/UNEUTRAL4.json`.
**Overall verdict:** `pass` — all headline numbers re-derived by my own methods; 2 contradicted wordings/citations, 5 overstated, 1 not reproduced.
**Write paths (only these):** `scratch/uver13/**`, `strategy/VERIFICATION_REPORT_13.md`, `orchestration/units/UVER13.md`, `orchestration/handoffs/UVER13.json`. Isolation honoured: every run on copies under `scratch/uver13/`; `scratch/uneutral3|4/**`, live `repro/encoder-crossover-190-SANITISED/`, `papers/**` read-only.

## What I did

1. Recomputed the report hash; read the report + card.
2. Wrote my own census `scratch/uver13/census_uver13.py` (raw-line + decoded-value walk, inside-stimulus split) and a mixed walk `scratch/uver13/mixed.py`; ran on all three trees.
3. Re-measured bytes, file sets, per-field byte contributions, tooling occurrences.
4. Rebuilt `tree-bij` independently (`scratch/uver13/bij_uver13.py`, DST patched) twice; diffed vs each other and vs on-disk.
5. Settled the stale-build question (`diff -rq tree-bij rt/bij`, mtimes).
6. Ran `run_diags.sh` on fresh copies of all three trees; recomputed every metric + fixture digest; compared live metrics.json.
7. Re-derived the 2,171 / 30 in-stimulus floor and the 23/190 kind-token question count.
8. Re-ran `prepare.py` (exit 2), corpus digests, `KIND_ALIAS`, `compileall`, JSONL parses.
9. Field audit by `grep -n` read-sites on the live tree.
10. Red→green: (a) `prepare.py` corpus guard; (b) trap test that moves stored route-A sibling numbers.

## Headline results

- Census re-derived: raw-line pinned 26,344/99, stripped 9,247/99, **bij 5,384/95** — U4's contradiction of UNEUTRAL3's 8,213/99 is correct. **But `8,213` DOES have an on-disk source** (`scratch/uneutral3/census-tree-bij.txt`, 20:06) → U4:291 contradicted.
- Escape artifact: mixed-walk totals pinned 16,813 / stripped 9,247 / bij 5,384 reproduced exactly; gap 9,531 = 3,177×3 (U4's 9,537 use raw hits, not the gap). Artifact class confirmed (7,743 train + 1,788 dev).
- In-stimulus floor **2,171 / 30 identical in all three trees**, per-identifier list identical to U4's; 23/190 kind-token questions.
- All metrics identical live|pinned|stripped|bij; bij digest `c7696edc0e71d83faafc2e489925788e0f36c6af94913674f8953718352c9a55` (contradicts UNEUTRAL3's `30b75581…`), pinned/stripped `8dd05ce6…`.
- `bij.py` deterministic: two fresh runs byte-identical and byte-identical to on-disk `tree-bij`. `rt/bij` is a 20:06 superseded build (21 files differ).
- `prepare.py` exit 2 in all trees with the exact `REFUSED: corpus digest mismatch — expected c78681d6…, got 58b09a3c…`; KIND_ALIAS 0/9; compileall 0.
- Red→green: corpus restored (c78681d6) → `prepare.py` exit 0 and re-emits the FULL unstripped 2,205,127/484,922-byte JSONL in both pinned and stripped trees → "the strip is one-way" is overstated.
- Trap warning overstated: moving `labelsB.json` numbers makes `recompute-claims.py` print `ALL CLAIM NUMBERS PRESERVED: False` and exit 1.

## Artifacts

`scratch/uver13/{census_uver13.py,mixed.py,bij_uver13.py,bij-runA.out,bij-runB.out,tree-bij-runA,tree-bij-runB,diag-{pinned,stripped,bij}.out,t/**,rg-pinned,rg-stripped,trap}`, `strategy/VERIFICATION_REPORT_13.md`.

## UNVERIFIED

No model was run (torch/transformers untested): every "preserved" statement is metric recomputation from stored labels/results. The pinned generator invocation is not recorded. The superseded `bij.py` revision that produced `30b75581…` is unrecoverable. "23 fixture questions name their own kind" is a textual count, not a behaviour test. The `25 of 190` lowercase-substring figure did not reproduce (I get 23).
