# VERIFICATION_REPORT_23 — independent check of unit UDTAG1

Verifier: **UVER24** — the replacement for UVER23, which died leaving a 12-line placeholder. That
placeholder was read and is superseded by this file (same path, as instructed).

Scope: `scratch/udtag1/tree-five` (emitted) and `scratch/udtag1/base-copy` (the unmodified base the
unit began from), against `strategy/DTAG_NEUTRALISATION.md`, `orchestration/units/UDTAG1.md`,
`orchestration/handoffs/UDTAG1.json`. Nothing below is taken from the author's record; every number
is re-derived from bytes on disk. Hard bound 25 tool calls (17 used).

## Verdict: **pass-with-corrections**

Every material claim reproduced. Two record defects: one recorded number is **contradicted** (the
manifest's `counts.bytes_total`), and one listed artifact **does not exist**.

---

## 1. Rename completeness, injectivity, path names — REPRODUCED

Contents, `grep -rl` (file list, then counts):

| id | base-copy files | tree-five files |
|---|---|---|
| D09 | 4 | 0 |
| D15 | 7 | 0 |
| D25 | 11 | 0 |
| D35 | 9 | 0 |
| D44 | 3 | 0 |

Raw `grep -ro` occurrences in `tree-five`: **D09 = D15 = D25 = D35 = D44 = 0**.

Replacements in `tree-five` (files / raw occurrences) vs their baseline in `base-copy`:

| new | was | base-copy files | tree-five files | tree-five occ |
|---|---|---|---|---|
| P02 | D09 | 0 | 4 | 7 |
| P03 | D15 | 0 | 7 | 35 |
| P05 | D25 | 0 | 11 | 25 |
| P04 | D35 | 0 | 9 | 31 |
| P01 | D44 | 0 | 3 | 6 |

File-count correspondence is exact and **injective** (4→4, 7→7, 11→11, 9→9, 3→3), and none of the
five replacement ids pre-existed in `base-copy` (all `files=0 occ=0`), so no collision, ambiguity, or
partial application was introduced.

Path names: `find scratch/udtag1/tree-five | grep -E 'D09|D15|D25|D35|D44'` → **0 hits**. No file or
directory name carried a neutralised id ("no path renamed" reproduced).

**17 of 45 files rewritten**: `diff -rq base-copy tree-five` → **18** `Files … differ`, **0**
`Only in` lines. The union of files carrying any of the five ids in `base-copy` is exactly **17**
files, and set-difference shows the changed set = those 17 ∪ {`MANIFEST.json`} — i.e. the 17 payload
rewrites plus the regenerated manifest, and nothing else. The **0 `Only in`** lines independently
confirm no path was renamed.

## 2. Census — the invariant that matters — REPRODUCED (delta 0)

`PYTHONHASHSEED=0 python3 scratch/ubij1/census_one.py <tree>` (workspace's own scanner, unmodified):

| tree | files | ids hit | TOTAL | inside-stimulus | distinct | outside | keys |
|---|---|---|---|---|---|---|---|
| tree-five | 45 | 74 of 184 | 3354 | **2171** | **30** | 1105 | 78 |
| base-copy | 45 | 74 of 184 | 3354 | **2171** | **30** | 1105 | 78 |

`diff` of the two full reports (ignoring the `tree:` path line) → **byte-identical**.
**Inside-stimulus delta = 0; distinct-key delta = 0; total delta = 0.** No stimulus moved.

*Caveat recorded honestly*: the five neutralised ids and the five replacement ids are **not** members
of the 184-identifier census vocabulary (each `grep` in `scratch/uagnostic1/census.tsv` → 0), so this
census could not by itself detect a D→P swap; what it proves is that **no census-vocabulary stimulus
moved** — none of the 74 tracked identifiers was disturbed.

## 3. Claims recomputation — REPRODUCED

`cd scratch/udtag1/tree-five && python3 verify/recompute-claims.py` → **exit 0**, output
byte-identical to the same run in `base-copy` (`diff` empty). Capture:
`scratch/uver24/claims_five.txt`. Literal highlights:

```
  arm modernbert-base  n=190 accuracy=0.347368 (recomputed 0.347368)
  arm deberta-v3-base  n=190 accuracy=0.347368 (recomputed 0.347368)
  arm setfit-mpnet     n=190 accuracy=0.263158 (recomputed 0.263158)
  arm majority-class   n=190 accuracy=0.452632 (recomputed 0.452632)
  arm shuffled-label   n=190 accuracy=0.231579 (recomputed 0.231579)
  arm decider-4b-repro n=190 accuracy=0.678947
    2x2: both=39  headOnly=27  deciderOnly=90  neither=34  sum=190
    psi=0.615789  delta=-0.331579  exact p=4.166818e-09  paired MDE=0.159494
    0.3474 … OK   0.4526 … OK   0.2911 … OK   0.6684 … OK   0.6789 … OK
    counts 39+27+90+34 = 39+27+90+34 = 190 (OK)
    0.3252/0.8837/0.914/0.3526 second-labeller … OK
  ALL CLAIM NUMBERS PRESERVED: True
  fixture correctness digest: c7696edc0e71d83faafc2e489925788e0f36c6af94913674f8953718352c9a55
```

The published constants were checked **in `papers/encoder-crossover-190/CLAIMS.md` itself**
(`CLAIMS.md:18` `0.3474 / 0.3474 / 0.2632 / 0.4526 / 0.2316`; `:19` floor `0.2911`; `:20` decider
`0.6684`/`0.6789`; `:33` `b=27, c=90, p=4.17e−09, paired MDE 0.1595`). All agree with the
recomputed values. (`recompute-claims.py:32` hardcodes the `CLAIMS` dict rather than parsing
`CLAIMS.md`, but its constants equal the published ones.) **Reproduced exactly**; the tree-five ≡
base-copy identity is the stronger form — the rename changed no recomputed number.

## 4. Tool exits — REPRODUCED, and the two second-labeller failures are PRE-EXISTING

Run in copies under `scratch/uver24/` (so no verified tree was written to):

| check | tree-five | base-copy |
|---|---|---|
| `python3 -m compileall -q .` | **0** | **0** |
| `harness/data/train.jsonl` | 800 records / 0 malformed | 800 / 0 |
| `harness/data/dev.jsonl` | 200 records / 0 malformed | 200 / 0 |
| `second-labeller/disagreements.jsonl` | 18 records / 0 malformed | 18 / 0 |
| `second-labeller/parse_fixture.py` | **1** | **1** |
| `second-labeller/compare.py` | **1** | **1** |

Failure text is identical in both trees:

```
FileNotFoundError: [Errno 2] No such file or directory: '…/second-labeller/reflex-decisions.sandbox.ts'   # parse_fixture.py
FileNotFoundError: [Errno 2] No such file or directory: '…/second-labeller/cases.json'                    # compare.py
```

Neither `reflex-decisions.sandbox.ts` nor `cases.json` is shipped in either tree
(`find … -name cases.json -o -name reflex-decisions.sandbox.ts` → empty). `second-labeller/metrics.json`
is byte-identical across the two trees, sha256 `6bf39077261f00bed589a4ae8e9fe90324e2435fd28e42a4fc8de7684cba34bf`,
so the route A/B diagnostics are unchanged. **Settled: the two failures are pre-existing, not caused
by the rename.** *(One correction: the unit said both fail "because reflex-decisions.sandbox.ts is not
shipped" — true for `parse_fixture.py`, but `compare.py` dies on its own missing input `cases.json`.
Same verdict, imprecise single cause.)*

## 5. Manifest — checked with MY OWN checker — PASS

`scratch/uver24/check_manifest_uver24.py` (written by me; the author's `check_emitted.py` was **not**
run):

```
manifest bytes=22325 sha256=8527a83be8c7259d230a1eb90452ad818287747dc6646e5b9d21f820cd03c8c1
entries=44 listed_unique=44 duplicates=0
missing=0 size_mismatch=0 hash_mismatch=0
present_files=45 unlisted_present=0 listed_but_absent=0
counts.files=45 entries+1=45 disk=45
counts.bytes_total=3008830 entries_sum=2986505 entries_sum+manifest=3008830 disk_sum=3008830
VERDICT PASS
```

0 missing, 0 hash mismatches, 0 size mismatches, 0 entries naming a nonexistent file, 0 files absent
from the manifest, 0 duplicates. The self-reference convention is **stated explicitly, not implied**,
in the manifest's own `manifest_self` field: *"not listed (self-referential sha256 is impossible);
MANIFEST.json is the only file in the tree absent from `files[]`, and counts.files /
counts.bytes_total count it."*

### Contradiction: `counts.bytes_total`
The record states **3,009,198** (`strategy/DTAG_NEUTRALISATION.md:8`,
`orchestration/handoffs/UDTAG1.json:25`). The manifest on disk and the tree disagree:

```
manifest counts.bytes_total = 3008830
disk_sum                    = 3008830   (45 files incl. MANIFEST.json)
entries_sum + manifest bytes = 2986505 + 22325 = 3008830
```

Difference **368 bytes**. The manifest is internally consistent and correct against the real tree;
**the recorded number 3,009,198 does not reproduce.** (Manifest size 22325 and sha256
`8527a83be8c7259d230a1eb90452ad818287747dc6646e5b9d21f820cd03c8c1` do match the record.)

## 6. Idempotence — REPRODUCED

`diff -rq scratch/udtag1/tree-five scratch/udtag1/tree-five-b | wc -l` → **0**. Two builds are
byte-identical.

## 7. Red→green on my own checker — PASSES (not vacuous)

```
checker on pristine copy            -> VERDICT PASS
append 1 byte to harness/data/train.jsonl
  -> size_mismatch=1 hash_mismatch=1
     SIZE: harness/data/train.jsonl
     HASH: harness/data/train.jsonl
     VERDICT FAIL   (exit 1)
restore the byte                    -> VERDICT PASS
```

## 8. Scope / non-modification — established by digest + mtime, not by snapshot diff

| tree | newest file mtime |
|---|---|
| `scratch/udtag1/tree-five` | 2026-10-15 21:58 (MANIFEST.json) |
| `scratch/udtag1/tree-five-b` | 2026-10-15 21:58 (MANIFEST.json) |
| `scratch/ubij3/tree-three-r2` | 2026-10-15 21:39 (MANIFEST.json) |

All three newest mtimes **precede** `orchestration/handoffs/UDTAG1.json` (2026-10-15 22:01:50), so
nothing was written into any of them after the unit reported; and `tree-five/MANIFEST.json` still
hashes to the value the unit recorded, which pins all 44 payload files. My own writes were confined
to `scratch/uver24/**`, `strategy/VERIFICATION_REPORT_23.md`, and the two UVER24 unit files; the
verification copies (and `compileall`'s `__pycache__`) live only under `scratch/uver24/`.

## Unverified / what stopped me

- **No pre-unit snapshot digest of the three trees exists**, so "unmodified" rests on the recorded
  manifest sha256 still matching disk plus the mtime ordering above — strong, but not a byte
  snapshot diff. I did not have one to compare against.
- The four second-labeller kappa/agreement numbers (0.3252 / 0.8837 / 0.914 / 0.3526) were **not
  re-derived from raw data** — I only confirmed `metrics.json` is byte-identical across the two
  trees and that `recompute-claims.py` matches it. The unit's own tool computes them.
- **Missing artifact:** `scratch/udtag1/udtag1_facts.json` is listed in
  `orchestration/handoffs/UDTAG1.json` `artifacts[]` but does not exist on disk (`find scratch/udtag1
  -maxdepth 1 -name '*.json'` → empty). The task brief also names it as part of the unit's record.

## Verdict

**pass-with-corrections.** Rename is complete, injective, consistent, and renamed no path; the
inside-stimulus census delta is 0 (2171 / 30 both sides); `recompute-claims.py` exits 0 with
byte-identical output and all published numbers preserved; the manifest passes my own independent
checker with every count at 0 (45 files, 3,008,830 bytes, sha256 `8527a83b…`); the two builds are
byte-identical; my checker is red→green non-vacuous. Corrections: the recorded
`counts.bytes_total` (3,009,198) is **wrong** — the artifact says 3,008,830 — and the listed artifact
`scratch/udtag1/udtag1_facts.json` is **absent**.
