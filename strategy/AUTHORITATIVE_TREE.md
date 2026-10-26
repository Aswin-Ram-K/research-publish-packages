# AUTHORITATIVE_TREE.md — UFIXTREE1 findings

**Question:** which of five on-disk candidate release trees is the one whose *own shipped tools*
reproduce the numbers `papers/encoder-crossover-190/` publishes — and should
`orchestration/units/UBUILD1.build.sh:134` be re-pinned to it?

**Answer (measured, not inferred from timestamps): `scratch/uneutral10/package`** is the only tree that
reproduces every published value with all three shipped tools exiting 0. The current pin
`scratch/urecut1/package` ships the OLD route-A κ and OLD A/B mutual agreement — a build run today
packages data that contradicts the paper.

## 1. Published values (quoted from the paper)

| quantity | published value | source |
|---|---|---|
| route A κ | `0.3248813212427869` | `papers/encoder-crossover-190/CLAIMS.md:110` (`.routeA.kappa`) |
| route A agreement | `0.34210526315789475` | `papers/encoder-crossover-190/CLAIMS.md:110` ("agreement 0.3421") |
| A/B mutual agreement | `0.3684210526315789` | `papers/encoder-crossover-190/CLAIMS.md:111` (`.passes["labelsB.json"].AB_mutual_agreement`) |
| route B κ | `0.9013584840356494` | `papers/encoder-crossover-190/CLAIMS.md:108` (`.passes["labelsB.json"].kappa`) |
| fixture sha256 (input instrument) | `076164ac53c2c1aac130953345c481f88b51f4d6fb93d465c7430308a99b4796` | `papers/encoder-crossover-190/CLAIMS.md:46` |

The tool's own `fixture correctness digest` line is `c7696edc0e71d83faafc2e489925788e0f36c6af94913674f8953718352c9a55`
in **all five** trees — it does not discriminate. It is a different quantity from CLAIMS.md:46's
fixture sha256.

## 2. Per-tree measurement (each tree copied to `scratch/ufixtree1/copies/`, never mutated)

Tools: `python3 verify/recompute-claims.py`, `python3 second-labeller/parse_fixture.py`,
`python3 second-labeller/compare.py`, run with cwd = tree root.
Raw outputs: `scratch/ufixtree1/out/<tree>.<tool>.txt`.

| tree | rc recompute | parse | compare | `ALL CLAIM NUMBERS PRESERVED` | route A κ | agreement | A/B mutual | route B κ | fixture digest | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| `scratch/urecut1/package` (PIN, 01:03) | 0 | 0 | 0 | **True** | `0.32520740993294694` | `0.34210526315789475` | `0.3526315789473684` | `0.9013584840356494` | `c7696edc…` | **STALE — fails 2/4 published values** |
| `scratch/uneutral10/package` (13:56) | 0 | 0 | 0 | **True** | `0.3248813212427869` | `0.34210526315789475` | `0.3684210526315789` | `0.9013584840356494` | `c7696edc…` | **AUTHORITATIVE — matches all 4** |
| `scratch/ufix31/pkg` | **1** | 0 | 0 | **False** | `0.31988636363636364` | `0.3368421052631579` | `0.3473684210526316` | `0.9013584840356494` | `c7696edc…` | FAIL (tool itself exits 1) |
| `scratch/utool1/tree-six` | 0 | 0 | 0 | True | `0.32520740993294694` | `0.34210526315789475` | `0.3526315789473684` | `0.9013584840356494` | `c7696edc…` | STALE (same numbers as the pin) |
| `scratch/udtag1/tree-five` | 0 | **1** | **1** | True | `0.32520740993294694` | `0.34210526315789475` | `0.3526315789473684` | `0.9013584840356494` | `c7696edc…` | BROKEN toolchain |

### Literal proof lines

`scratch/uneutral10/package` — `second-labeller/compare.py` output:
```
  "agreement": 0.34210526315789475,
  "kappa": 0.3248813212427869,
   "kappa": 0.9013584840356494,
   "AB_mutual_agreement": 0.3684210526315789,
```
`scratch/uneutral10/package` — `verify/recompute-claims.py` output:
```
  ALL CLAIM NUMBERS PRESERVED: True
  fixture correctness digest: c7696edc0e71d83faafc2e489925788e0f36c6af94913674f8953718352c9a55
```
(The same run also prints its own stale internal constants:
`route-A kappa: published=0.3252   tree=0.3248813212427869     reproduced=True` and
`A/B mutual agreement: published=0.3526   tree=0.3684210526315789     reproduced=False` — i.e. that
copy's hard-coded "published" cites lag the paper, while its data matches the paper. The literal
`ALL CLAIM NUMBERS PRESERVED: True` line still prints, exit 0.)

`scratch/urecut1/package` (the pin) — `second-labeller/compare.py` output:
```
  "kappa": 0.32520740993294694,
   "AB_mutual_agreement": 0.3526315789473684,
```
`scratch/ufix31/pkg` — `verify/recompute-claims.py` output, exit 1:
```
    0.3252    second-labeller route-A kappa                shipped=0.31988636363636364    MISMATCH
    0.3526    second-labeller A/B mutual agreement         shipped=0.3473684210526316     MISMATCH
  ALL CLAIM NUMBERS PRESERVED: False
```
`scratch/udtag1/tree-five` — `second-labeller/parse_fixture.py`, exit 1:
```
FileNotFoundError: [Errno 2] No such file or directory: '.../second-labeller/reflex-decisions.sandbox.ts'
```
`scratch/udtag1/tree-five` — `second-labeller/compare.py`, exit 1:
```
FileNotFoundError: [Errno 2] No such file or directory: '.../second-labeller/cases.json'
```

### Tie-break
No tie: `scratch/uneutral10/package` is the unique tree reproducing all four published numbers. Had
`udtag1/tree-five` tied on `recompute-claims.py` (it prints `True`, exit 0), the tie-breaker is that its
other two shipped tools exit 1 — a release tree whose own tools cannot run is not authoritative.

## 3. Required pin change — NOT APPLIED

`orchestration/units/UBUILD1.build.sh:134`, exact new line:

```
PROMOTED_SAN_SRC="$SRC/scratch/uneutral10/package"
```

Current line (unchanged, verified after all work):
```
PROMOTED_SAN_SRC="$SRC/scratch/urecut1/package"
```

**SHIP_STAGED (lines ~178–214) does NOT need re-derivation.** It is a *path* list, and the two trees
carry an identical 29-file path set (`diff` of `find . -type f | sort` → `IDENTICAL FILE SET`); only
contents differ (20 of 29 files). Caveat for the applying unit: the *hard-fail-hit count annotations* in
that comment block were measured on the `urecut1` contents and should be re-measured against
`uneutral10` — the list itself is correct.

**`tests/test_build_wiring.py` stays GREEN.** Run in a copy, real script untouched:
- baseline (current pin): `python3 -m pytest tests/test_build_wiring.py -q` → `11 passed in 0.05s`
- re-pin simulation, `UWIRE3_BUILD_SCRIPT="$PWD/scratch/ufixtree1/UBUILD1.repin.build.sh"` (that copy has
  line 134 set to `uneutral10/package`) → `11 passed in 0.05s`
(`PYTHONPATH=$PWD/src` was needed because `tests/conftest.py:19` imports `resextract`.)

Follow-up doc references that still name `urecut1/package` (not assertions, but stale after the change):
`orchestration/units/UBUILD1.build.sh:39` (comment), `tests/test_build_wiring.py:7,10` (docstring),
`strategy/BUILD_WIRING.md:5,24,38,51,113,139`, `scratch/ufix30/live_minus_datavocab.sh:39,134` (a copy).

## 4. Mirror question — `repro/encoder-crossover-190/` (43 files)

**Still referenced? YES — by shipped/sanitised documents, though not by the manuscript's positive claims.**
- `repro/encoder-crossover-190-SANITISED/redact.py:2` — builds the sanitiser from it; `:48` of
  `REDACT3_REPORT.md` states "stage A re-copies the pristine files from `repro/encoder-crossover-190/`
  on every run" → it is a **live input to the sanitiser**, not dead weight.
- `repro/encoder-crossover-190-SANITISED/INTEGRITY.md:108` — "`repro/encoder-crossover-190/` was never
  written to"; `SCRUB_REPORT.md:394` names it as read-only; `REDACT3_REPORT.md:192` records its
  as-audited digest `57a29b4e78bff60f84309e2e95b56f49663884a13b801345eecd93813ecbf300`.

**Premise corrections (measured):**
- The manuscript does **not** have 0 occurrences of the path. `papers/encoder-crossover-190/CLAIMS.md:82`,
  `MANUSCRIPT.md:424` and `MANUSCRIPT.md:751` each name `results/DEFECT-EVIDENCE.json` — all three saying
  it is **not** part of the released set.
- That statement conflicts with disk: the file is present in the raw mirror (`results/DEFECT-EVIDENCE.json`,
  3,724 B, sha256 `096dec1500693b6e854e3feb7c5fab858b97e7d92cabdb1e23c9455ed940ef35`, verified) **and** in
  the sanitised tree (`repro/encoder-crossover-190-SANITISED/results/DEFECT-EVIDENCE.json` exists).
- `MANIFEST.json` does **not** list the file twice as entries: `repro/encoder-crossover-190/MANIFEST.json`
  carries exactly one `files[]` entry (`"path": "results/DEFECT-EVIDENCE.json"`, 42 files listed); the
  second string match is that entry's `"source"` absolute target path. Count 2 = path + source.

**Recommendation (report only; nothing deleted or edited):** keep the mirror as the read-only as-audited
provenance input the sanitiser reads. Open the manuscript-vs-disk contradiction as a separate unit: either
`CLAIMS.md:82`/`MANUSCRIPT.md:424,751` are wrong that the file is "not part of the released set", or the
sanitised tree should exclude it (and `EXCLUDED.md` E12, which does not name it, needs a row). The
MANIFEST double-string is a non-defect.

## 5. Method / bounds

- 5 trees copied under `scratch/ufixtree1/copies/`; every tool ran in the copy. No candidate tree, build
  script, `papers/**`, or `/home/zer0null/Duval` was written; no git run against the target.
- `/home/zer0null/Duval` never opened.
- Raw outputs retained: `scratch/ufixtree1/out/`; re-pin script copy: `scratch/ufixtree1/UBUILD1.repin.build.sh`.
