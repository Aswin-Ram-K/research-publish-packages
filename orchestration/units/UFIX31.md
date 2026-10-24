# UFIX31 — correct UNEUTRAL8's record (verifier UVER31, `strategy/VERIFICATION_REPORT_31.md`)

**Status:** DONE (skeleton written first, per unit contract)

## Purpose
Correct six defects UVER31 found in UNEUTRAL8's report **in place**, with dated
`> **Correction 2026-10-16 (UFIX31):** …` blockquote notes next to each corrected sentence.
Original sentences and numbers stay readable. No package tree, no paper file, and no
`orchestration/units/UBUILD1.build.sh` is edited.

## Declared write paths (nothing else)
- `strategy/STIMULUS_NEUTRALISATION.md`
- `orchestration/units/UNEUTRAL8.md`
- `orchestration/handoffs/UNEUTRAL8.json`
- `orchestration/units/UFIX31.md`
- `orchestration/handoffs/UFIX31.json`
- `scratch/ufix31/**`

READ anything else; edit nothing else.

## Hard bound
12 tool calls. Small increments; never `cat` a large file. Every `old_string` asserted to occur
exactly once immediately before its in-place write.

## Method
Read the literal report sentences; re-run `verify/recompute-claims.py` on a copy under
`scratch/ufix31/`; cross-check `bytes_total` by summing the tree; strict-walk the manifest for
unlisted files. Then add the six dated notes to `orchestration/units/UNEUTRAL8.md` and (where the
same claim recurs) `strategy/STIMULUS_NEUTRALISATION.md`, and append a `corrections_2026_10_16`
key to `orchestration/handoffs/UNEUTRAL8.json` without rewriting existing keys.

## Log — the six corrections (literal before → after)
1. **route B κ.** `UNEUTRAL8.md` literally read `0.9013584845356494` → correct **`0.9013584840356494`**
   (wrong at the 10th decimal; route B otherwise unchanged). Note placed after the Proof block.
2. **Census.** "35 of 184 present / 1,608 occurrences" = **pre-state**; the **emitted** package is
   **28 of 184 / 1,362 occurrences** — re-reproduced here: `census.py` prints
   `DISTINCT-CLASS-IDS-PRESENT 28 TOTAL-OCCURRENCES 1362`.
3. **`bytes_total`.** Field = **859428** (sum of the 28 listed files); **871192 = 859428 + 11764**
   (`MANIFEST.json`'s own bytes) = inclusive total of all 29 on-disk files. Cross-checked:
   `du -sb`/sum-of-tree = 871192, `stat -c %s MANIFEST.json` = 11764.
4. **"0 unlisted" self-exempting.** Strict walk: 29 on-disk vs 28 listed → `unlisted_strict =
   ['MANIFEST.json']`, `missing = []`. Convention stated in the note.
5. **Coverage-gap claim REFUTED.** `verify/recompute-claims.py` **does** check `routeA.kappa`
   (`:38` `0.3252: "second-labeller route-A kappa",`; `:115` `sb = {0.3252: met["routeA"]["kappa"],`)
   and `AB_mutual` (`:41` `0.3526: "second-labeller A/B mutual agreement"}`; `:118`
   `0.3526: met["passes"]["labelsB.json"]["AB_mutual_agreement"]}`). **Ran** on a copy
   `scratch/ufix31/pkg`: two `MISMATCH` lines →
   `ALL CLAIM NUMBERS PRESERVED: False`, **EXIT=1**. Operational consequence recorded: applying the
   eight tokens requires re-freezing `metrics.json`'s recorded `routeA` values, because the package's
   own check will otherwise reject the tree — the guard working, not a gap.
6. **"the whole route A movement" overstated for ties.** Dotted four alone reproduce
   κ/agreement/pe/exact_index/AB exactly, but **ties differ (dotted-only 118 vs emitted 121)**;
   hyphenated four alone move **only ties (120 → 123)** (`scratch/uneutral8/result2.json`).

### Also recorded (verified, not defects)
- UVER31's pre-state `scratch/uneutral8/before_pkg` is byte-identical to `scratch/uneutral6/package`
  (`diff -rq` clean); `scratch/urecut1/package` differs.
- Two UVER31 items stay UNVERIFIED: the `manifest_self` derivation algorithm is unnamed (the value
  was confirmed); "two builds byte-identical" was not re-run (proxy: parse + compare reproduced
  byte-identically).

## Result
- `orchestration/units/UNEUTRAL8.md`: 7 dated notes injected (5 anchors).
- `strategy/STIMULUS_NEUTRALISATION.md`: 4 dated notes injected where the same claims recur
  (`:95` PRESERVED, `:279` bytes_total, `:280` checker, `:304` gap claim).
- `orchestration/handoffs/UNEUTRAL8.json`: original keys intact; `corrections_2026_10_16` appended
  (7 entries); re-parsed with `json.load` → valid, 8 top-level keys.
