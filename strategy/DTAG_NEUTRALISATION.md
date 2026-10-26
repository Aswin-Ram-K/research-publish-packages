# DTAG_NEUTRALISATION - five internal decision-document numbers, removed from the release tree

**Unit:** UDTAG1 (2026-10-16) - **Status: done**
**Base (read-only provenance, never written):** `scratch/ubij3/tree-three-r2` - 45 files, 3,008,378 bytes,
`MANIFEST.json` sha256 `f3e4a22c49261ca937311b1d4edf2e8e52d347faed5d1a4f70d93e41b71fc614`.
**Emitted:** `scratch/udtag1/tree-five` - 45 files; the 44 payload files total **2,986,505 bytes, unchanged** (corrected 2026-10-16 from `3,008,378`: that is the base *tree* total of 45 files including its own 21,873-byte `MANIFEST.json`; the emitted payload is byte-for-byte the base payload, 2,986,505 - found and re-derived from disk by UFIX27, beyond UVER24's two named defects)
(every replacement token is the same byte length as the string it replaced); regenerated `MANIFEST.json`
22325 bytes, sha256 `8527a83be8c7259d230a1eb90452ad818287747dc6646e5b9d21f820cd03c8c1`, `counts.files` 45, `counts.bytes_total` 3,008,830 (corrected 2026-10-16 from `3,009,198`: the manifest and the disk agree on 3,008,830 = 44 payload files 2,986,505 + `MANIFEST.json` 22,325; wrong by 368 bytes, found by UVER24 and re-derived from disk by UFIX27).

## 1. What was changed, and why exactly five

`strategy/NONCENSUS_CLASSIFICATION.md` (UNONCENSUS2) showed the released manuscript is public under
CC BY 4.0 (`papers/encoder-crossover-190/MANUSCRIPT.md:784-785`) and that 16 of the 19 project-specific
strings the 184-identifier census never listed are citations or names the manuscript itself uses. Those
16 stay byte-for-byte: `imajev`, `deberta-v3-base`, `modernbert-base`, `setfit-mpnet`, `H-A`/`H-B` (the two
200-case held-out corpus strata - `harness/prepare.py:74` filters on `c["F06"] in ("revision","H-A")`),
`instrument190`, `decider-4b`, `second-labeller-190`, `typed-channel`, `EXP#11`, `EXP#12`,
`encoder-crossover-190`, `tccommon.py`, `tcmodel.py`.

The five that are genuinely internal are ones that index the **withheld research record** and two of them
also leak internal paths:

| string | occurrences (source tree) | files | leak |
|---|---|---|---|
| `D35` | 31 | 9 | `harness/data/corpus.json:3-4` `"spec": "docs/research/experiments/D35-per-model-option-revision.md section 4"`; `harness/lint.ts:14` names the branch `D35-per-model-option-revision` |
| `D44` | 6 | 3 | `second-labeller/OWED_CORRECTIONS.md:22` carries `docs/research/D44:47` |
| `D09` | 7 | - | `harness/LEAD-WIRING.md:21` |
| `D15` | 35 | - | `EXCLUDED.md` names `tools/D15` plus commit `a5ef1b2` |
| `D25` | 25 | - | `EXCLUDED.md` "Only `D25` is the instrument"; `SCHEMA.ts` `D25 (HEAD 907fa39)` |

The read-only target's `docs/DECISION_LOG.md:155/:260/:612` carries `## D-009`, `## D-015`, `## D-025` as
real numbered decisions, and the released papers cite entirely different ones (`D-067`, `D-038`, `D-047`,
`D-048`) - which is exactly why these numbers had to go.

NEUTRAL-TAG/v1 replacement (prefix `P`, chosen because no `P` family exists among the fixture's question
vocabulary or the tree's own tag families `F/K/N/R/T/X/C/S/M/E`):

| `D09` | `D15` | `D25` | `D35` | `D44` |
|---|---|---|---|---|
| `P02` | `P03` | `P05` | `P04` | `P01` |

Proven in the emitted tree, not inferred: `harness/LEAD-WIRING.md:21` `## 3. \`P02\` is subsumed by the lint`;
`harness/data/corpus.json:4` `"spec": "docs/research/experiments/P04-per-model-option-revision.md section 4"`;
`harness/lint.ts:14` `branch \`P04-per-model-option-revision\``; `second-labeller/OWED_CORRECTIONS.md:22`
`docs/research/P01:47`. Residual occurrences of all five strings anywhere in the emitted tree: **0**.
The internal map is printed as counts only and is never written into the tree, never logged and never
shipped (`map_shipped: false`).

**`LEAD` and `no-union` are left alone.** No unit, in the tree or in the manuscript, could establish what
either denotes (category (d) of the classification). Ambiguous strings are not renamed on a hunch.

## 2. Path renames: NONE, and what that means

No file or directory name anywhere in the tree contains any of the five strings, so the rename touched only
file *contents*. That matters because a filename rename would change manifest `path` values and invalidate
every document that cites the path. Here:

* no manifest entry's `path` changed, so the manifest diff is hashes and provenance text only;
* every docs citation remains valid - the path-like strings that DO exist are prose values inside files
  (`docs/research/experiments/D35-per-model-option-revision.md`, `tools/D15/data/corpus.json`,
  `docs/research/D44:47`, `D38-D15-comparison.md`) and were rewritten as content;
* the shipped outside-facing tools contain **no** D-number at all - `verify/recompute-claims.py`,
  `second-labeller/compare.py`, `second-labeller/parse_fixture.py` were checked by grep - so the
  "rename broke a hardcoded path" conflict rule was never triggered and **no tooling was rewired**.

17 of 45 files were rewritten (identifiers, prose, JSON keys and JSON values alike):

```
base-copy/EXCLUDED.md
base-copy/fixture/DECISION_CASE_SCHEMA.ts
base-copy/harness/data/corpus.json
base-copy/harness/data/lint-report.json
base-copy/harness/data/manifest.json
base-copy/harness/export-fixture.ts
base-copy/harness/LEAD-WIRING.md
base-copy/harness/lint.ts
base-copy/harness/README.md
base-copy/preregistration/EXP12-typed-channel-comparison-prereg.md
base-copy/results/baselines.json
base-copy/results/REPORT.md
base-copy/second-labeller/EVIDENCE.md
base-copy/second-labeller/OWED_CORRECTIONS.md
base-copy/second-labeller/PREREGISTRATION.md
base-copy/second-labeller/RUN.json
base-copy/variants/no-union/files/fixture/DECISION_CASE_SCHEMA.ts
```

## 3. Invariants

### 3.1 No published CLAIM NUMBER moved

`verify/recompute-claims.py` run **inside the emitted tree**, exit 0. Literal output:

```
  arm modernbert-base  n=190 accuracy=0.347368 (recomputed 0.347368)
  arm deberta-v3-base  n=190 accuracy=0.347368 (recomputed 0.347368)
  arm setfit-mpnet     n=190 accuracy=0.263158 (recomputed 0.263158)
  arm majority-class   n=190 accuracy=0.452632 (recomputed 0.452632)
  arm shuffled-label   n=190 accuracy=0.231579 (recomputed 0.231579)
  arm decider-4b-repro n=190 accuracy=0.678947

  PAIRED McNEMAR, best head vs decider-4b reproduction (aligned by case id)
    2x2: both=39  headOnly=27  deciderOnly=90  neither=34  sum=190
    psi=0.615789  delta=-0.331579  exact p=4.166818e-09  paired MDE=0.159494

  CLAIMS CHECK (tolerance 5e-4)
    0.3474    modernbert-base sealed-190 accuracy          recomputed=0.3473684210526316 OK
    0.4526    majority-class control accuracy              recomputed=0.45263157894736844 OK
    0.2911    chance floor (mean 1/k)                      recomputed=0.29105263157894734 OK
    0.6684    decider-4b published baseline                QUOTED CONSTANT (results/REPORT.md 2; not recomputable in this subset) OK
    0.6789    decider-4b same-run reproduction             recomputed=0.6789473684210526 OK
    counts 39+27+90+34 = 39+27+90+34 = 190 (OK)

  SECOND-LABELLER NUMBERS (from the shipped sanitised metrics.json)
    0.3252    second-labeller route-A kappa                shipped=0.32520740993294694    OK
    0.8837    second-labeller closed-vocabulary kappa      shipped=0.8837023738280471     OK
    0.914     second-labeller roster+bespoke kappa         shipped=0.9139973672663448     OK
    0.3526    second-labeller A/B mutual agreement         shipped=0.3526315789473684     OK

  ALL CLAIM NUMBERS PRESERVED: True
  fixture correctness digest: c7696edc0e71d83faafc2e489925788e0f36c6af94913674f8953718352c9a55
```

The same script in the untouched base copy produced output that `diff` reports as identical (exit 0 both
sides): every claim number, the paired McNemar 2x2, the second-labeller kappas and the fixture correctness
digest `c7696edc0e71d83faafc2e489925788e0f36c6af94913674f8953718352c9a55` are unmoved. Digests elsewhere in
the tree are free to change; they are reported, not defended.

### 3.2 Every tool that ships, and its exit code

| tool | base copy | emitted tree |
|---|---|---|
| `python3 -m compileall -q` over the tree | 0 | **0** |
| JSON parse `harness/data/train.jsonl` | 800 lines, 0 bad | **800, 0 bad** |
| JSON parse `harness/data/dev.jsonl` | 200 lines, 0 bad | **200, 0 bad** |
| JSON parse `second-labeller/disagreements.jsonl` | 18 lines, 0 bad | **18, 0 bad** |
| `verify/recompute-claims.py` (inside the tree) | 0 | **0** |
| `second-labeller/parse_fixture.py` | 1 | **1** |
| `second-labeller/compare.py` | 1 | **1** |

`parse_fixture.py` and `compare.py` fail identically **before and after** with a pre-existing packaging
gap, not a rename: both read `second-labeller/reflex-decisions.sandbox.ts`
(`parse_fixture.py:85` `SRC = os.path.join(HERE, "reflex-decisions.sandbox.ts")`), which is **not in the
shipped tree** (it exists in other scratch trees, e.g. `scratch/ubij1/tree-one/second-labeller/`,
`scratch/uneutral4/t/pinned/second-labeller/`), so `parse_fixture.py` raises
`FileNotFoundError: [Errno 2] No such file or directory: .../second-labeller/reflex-decisions.sandbox.ts`
and `compare.py:49` then fails on the `cases.json` it would have produced. Both were run in disposable
copies (`scratch/udtag1/run-base`, `scratch/udtag1/run-b`) so the emitted tree stayed pristine, and both
died before writing anything.

### 3.3 Identifier census - inside-stimulus delta = +0

`scratch/ubij1/census_one.py` against the 184-identifier list `scratch/uagnostic1/census.tsv`, before (base
copy) and after (emitted tree), 45 files each: distinct identifiers hit **74 of 184**, total occurrences
**3354**, **inside-stimulus 2171 occurrences over 30 distinct keys**, outside 1105, keys 78 - identical on
both sides. The builder's own independent guard agrees (inside=2171, distinct=30, total=3354 on both sides,
PASSED). The load-bearing number is the **inside-stimulus delta: +0** (distinct delta also +0). A raw text
diff of the two census reports is dominated by tie ordering inside the `-- by identifier --` section (same
counts, different order); with `PYTHONHASHSEED=0` the two runs are byte-identical apart from the `tree:`
path line.

### 3.4 Manifest regenerated from disk, proved by an independent checker

Procedure: `scratch/upack1/regen_manifest.py` (UPACK1, 2026-10-16). Implementation for this unit:
`scratch/udtag1/regen_manifest.py`, which writes nothing but `MANIFEST.json`; `files[]` lists every regular
file except the manifest itself, `counts.files`/`counts.bytes_total` describe the whole tree including the
manifest, every `sha256`/`bytes` pair is recomputed from disk, the `bytes_total` fixed point is solved, and
`source`/`source_sha256`/`kind` provenance is preserved by path. The manifest was not hand-edited.

Checker `scratch/udtag1/check_emitted.py` (written by this unit, independent code path, reading the tree and
the manifest separately): `listed-but-absent 0`, `present-but-unlisted 0`, `duplicate entries 0`,
**`0 missing, 0 hash mismatches, 0 size mismatches`**, `counts agree with disk: True`, `D-number residue in
manifest: 0`, **VERDICT: PASS** (exit 0).

### 3.5 Idempotence

* Builder run twice, into `tree-five` and `tree-five-b`: `diff -r tree-five tree-five-b` -> **0 lines**; the
  44 payload files compare byte for byte, 0 differing.
* Both regenerated manifests are identical byte for byte with `generated_utc` masked.
* Regeneration run twice in place over the same tree: same 22,325 bytes and same sha256
  `8527a83be8c7259d230a1eb90452ad818287747dc6646e5b9d21f820cd03c8c1` both times. `generated_utc` is a wall-clock stamp and is the only field that moves between runs.

## 4. Second-labeller diagnostics, before and after

route A (tokeniser overlap, the only route renaming could move): agreement 0.34210526315789475, expected 0.025041551246537397, kappa 0.32520740993294694, exact-index matches 65, ties 120, zero-score cases 41, n=190, options 721; rule PREREGISTRATION.md s2 distinct-token overlap + 0.5 substring bonus, argmax, ties->lowest index.
route B (primary, labelsB.json): agreement/po 0.9052631578947369, pe 0.03958448753462604, kappa 0.9013584840356494, exact-index matches 172, n_disagreements 18, A/B mutual agreement 0.3526315789473684, disagreements where route A backs the record 5.
stratification - closed vocabulary (K03/K01/K07/K04, n=106): route A kappa 0.21106870229007632, labelsB kappa 0.8837023738280471; roster+bespoke (K05/N10/K02, n=84): route A kappa 0.4284887087434858, labelsB kappa 0.9139973672663448.
per kind [n, routeA kappa, labelsB kappa]: K01 [30, 0.03508771929824562, 1.0], K02 [30, 0.41534713763702796, 0.9225806451612903], K03 [26, -0.05202312138728322, 0.8048780487804877], K04 [22, 0.06382978723404252, 0.938375350140056], K05 [26, 0.36995153473344106, 0.8717105263157895], K07 [28, -0.04518664047151275, 0.7152542372881355], N10 [28, 0.4196891191709844, 0.9261213720316623].
These are the values BEFORE and AFTER: second-labeller/metrics.json is byte-identical in the base copy and the emitted tree (sha256 6bf39077261f00bed589a4ae8e9fe90324e2435fd28e42a4fc8de7684cba34bf) - neither parse_fixture.py nor compare.py rewrote it in either tree (both exit 1 on a missing input that is absent in BOTH trees: reflex-decisions.sandbox.ts), so no diagnostic value can have moved.

## 5. Open author decision: the manifest's `source` exposure (reported, not acted on)

The regenerated manifest exposes, exactly as the procedure produces it: **44 of 44** `files[]` entries carry
a `source` string, **40** carry `source_sha256`; there are **43 distinct source paths**, of which **19** name
a withheld branch's full `tools/typed-channel/...` path map, **9** name `experiments/`, and **15** are other
(read-only target / `repro/` / unclassified). UNONCENSUS2's count of the same population was 18 typed-channel
/ 11 read-only target / 9 `experiments/` / 4 `repro/`; the difference is classifier boundary in the
"other" bucket, not a change to the manifest. **`source`/`source_sha256` were left exactly as the
regeneration produces them; whether they ship is an author decision and remains open.**

## 6. Containment

Wrote only: `scratch/udtag1/**`, `strategy/DTAG_NEUTRALISATION.md`, `orchestration/units/UDTAG1.md`,
`orchestration/handoffs/UDTAG1.json`. Read-only everywhere else. `scratch/ubij3/tree-three-r2` was never
written (it was copied first; `diff -rq` against the working copy confirms it). No git command was run at
all. `/home/zer0null/Duval` and `/home/zer0null/research-publish-packages` were never written.

## 7. Evidence commands

```
python3 scratch/udtag1/dtag_one.py scratch/udtag1/tree-five         # rename + built-in inside-stimulus guard
cd scratch/udtag1/tree-five && python3 verify/recompute-claims.py  # claim numbers, literal output above
python3 -m compileall -q scratch/udtag1/tree-five
python3 scratch/udtag1/regen_manifest.py tree-five
python3 scratch/udtag1/check_emitted.py
diff -r scratch/udtag1/tree-five scratch/udtag1/tree-five-b
cd scratch/udtag1/run-b/second-labeller && python3 parse_fixture.py ; python3 compare.py
python3 scratch/ubij1/census_one.py <tree> scratch/uagnostic1/census.tsv
```
