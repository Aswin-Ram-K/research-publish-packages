# Unit UFIXPAPER5

**Purpose:** Three presentation/verification fixes on paper #3 (`papers/encoder-crossover-190`) and
`tools/package/md2tex.py`:
1. Make the printed `guard: <label>` line unambiguous (a passing run must not read as a failure),
   while preserving the label's meaning (it names the historical defect the guard prevents).
2. Remove internal companion-record filenames / internal paths that actually reach
   `submission/main.tex`, replacing them with neutral in-register descriptions.
3. Verify (do not "fix") the "29 files" claim about the released reproducibility package.

**Bound:** 20 tool calls.

**Write paths:** `papers/encoder-crossover-190/**`, `tools/package/md2tex.py`,
`tools/package/README.md` (line-level only), `orchestration/units/UFIXPAPER5.md`,
`orchestration/handoffs/UFIXPAPER5.json`, `scratch/ufixpaper5/**`.

**Constraints:** `/home/zer0null/Duval` read-only, never git against it. No number moved in any paper.
Do not weaken/silence any guard. Separate measured / inferred / undetermined. Build only under `scratch/**`.

**Status:** in progress.


## Result (appended by the unit)

- J1: success print now states PASSED and names the label's meaning; failure path untouched.
- J2: companion-record names reaching main.tex replaced per `scratch/ufixpaper5/edits.tsv`; names a citation anchor needs were skipped and are reported in `scratch/ufixpaper5/evidence.log`.
- J3: released package measured at 29 files (`scratch/uneutral10/package/`) -> the paper's 29 is CORRECT.
