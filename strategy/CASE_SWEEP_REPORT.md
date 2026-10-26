# CASE_SWEEP_REPORT — exhaustive case-insensitive leak sweep of all three release packages

**Unit:** UCASESWEEP1 · **Date:** 2026-10-19 · **Mode:** report-only, nothing repaired, nothing rebuilt.
**Bound:** 25 tool calls; this sweep used 15 and stopped within it.

**Spec of the sweep:** every form at once, case-insensitively, on every surface — the failure mode of the
three earlier sweeps was searching only for what the previous sweep had already found.

---

## 1. Method, and the positive control

Patterns were applied with `grep -rIiE` (recursive, binary-skipping, case-insensitive, extended regex) over
the payload directories, over a **fresh `tar -xzf` extraction** of each `.tar.gz` into
`scratch/ucasessweep1/extract/<paper>/`, over the canonical tree `scratch/uneutral10/package/`, over the
three papers' `MANUSCRIPT.md` / `CLAIMS.md` / `AVAILABILITY.md` / `GAPS.md` / `README.md` /
`submission/main.tex`, and over the workspace's copies of the public repo.

**Control (planted, mixed case).** `scratch/ucasessweep1/control.md` plants every pattern once, in mixed
case: `DuVal`/`dUVaL`/`DUVAL`, `2026-09-28-Trace-M0`, `duval_HOSTED_LAYER_ok`, `DUVAL_hosted_layer_OK`,
`ZeRoNuLl`, `cOnSoNaNcE`, `reSeXtRaCt`, `RESERACH extarctor`, `uCASEsW1`, `scratch/x`, `tools/package/y`,
`state/refresh-verify`, `/home/u`, `orchestration/`, `strategy/`, `dockets/`, `DeepSeek`, `MiMo`,
`LongCat`, `STEP-5-PREVIEW`, `KeyRing`. Re-running the sweep against the control returned **non-zero for
19 of 20 patterns**, and the one zero was a real defect in my own pattern rather than in the grep:
`zer0null` uses a **digit zero**, while the control spelled `ZeRoNuLl` with a **letter o**. Both spellings
were then searched everywhere — `zer0null` (digit 0) and `zeronull` (letter o) — and **both are zero on
every surface**. That is exactly the failure class this unit exists to catch, caught on itself first.

Counts below are `occurrences / matching lines`.

## 2. Surfaces

| Surface | Path | Files |
|---|---|---|
| S1-payload | `papers/encoder-crossover-190/released/` | 34 |
| S1-fresh | `scratch/ucasessweep1/extract/encoder-crossover-190/` (fresh extraction) | archive content |
| S2-payload | `papers/gated-read-batching/released/` | 14 |
| S2-fresh | `scratch/ucasessweep1/extract/gated-read-batching/` (fresh extraction) | archive content |
| S3-payload | `papers/replay-record-not-decision/released/` | 13 |
| S3-fresh | `scratch/ucasessweep1/extract/replay-record-not-decision/` (fresh extraction) | archive content |
| S4-canonical | `scratch/uneutral10/package/` | 29 |
| S5-paper-docs | the three papers' `MANUSCRIPT/CLAIMS/AVAILABILITY/GAPS/README.md` + `submission/main.tex` | 12 files |
| S6-repo | workspace copies of `research-publish-packages` | see §6 |

## 3. Counts

### 3a. Target identity and project-name patterns

| Surface | `duval` | `2026-09-28` | `duval_hosted_layer_ok` | `zer0null`/`zeronull` | `consonance` | `resextract` | `reserach extarctor` | unit ids |
|---|---|---|---|---|---|---|---|---|
| S1-payload | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 8/6 |
| S1-fresh | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 2/2 |
| S2-payload | **2/2** | **5/5** | **2/2** | 0/0 | **437/225** | 0/0 | 0/0 | 1/1 |
| S2-fresh | **2/2** | **5/5** | **2/2** | 0/0 | **437/225** | 0/0 | 0/0 | 0/0 |
| S3-payload | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 |
| S3-fresh | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 |
| S4-canonical | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 |
| S5-paper-docs | **8/4** | **1/1** | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | **36/32** |

### 3b. Path patterns and tooling names (tooling reported separately, per the card)

| Surface | `scratch/` | `tools/package/` | `state/refresh-verify` | `/home/` | `orchestration/` | `strategy/` | `dockets/` | `deepseek` | `mimo` | `longcat` | `step-5-preview` | `keyring` |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| S1-payload | 5/3 | 0/0 | 0/0 | 0/0 | 0/0 | 1/1 | 0/0 | 0/0 | 2/2 | 0/0 | 0/0 | 0/0 |
| S1-fresh | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 2/2 | 0/0 | 0/0 | 0/0 |
| S2-payload | 1/1 | 1/1 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 9271/9268 | 1/1 | 0/0 | 0/0 | 1/1 |
| S2-fresh | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 9271/9268 | 1/1 | 0/0 | 0/0 | 1/1 |
| S3-payload | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 |
| S3-fresh | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 |
| S4-canonical | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 2/2 | 0/0 | 0/0 | 0/0 |
| S5-paper-docs | 7/6 | 2/2 | 4/4 | 0/0 | 0/0 | 7/7 | 0/0 | 19/16 | 12/12 | 0/0 | 6/6 | 0/0 |

`/home/` is zero on every release surface and on the paper docs. The only absolute-host-path hits in the
workspace are in **stale scratch copies of the public repo** (§6), not in the three packages.

## 4. Every hit, with a one-line judgement

### 4.1 Paper #2 package — `papers/gated-read-batching/released/` (the archive that still carries the target name)

File `gated-read-batching-released/data/gated-read-rows.jsonl`, identical in the payload tree and in the
fresh extraction:

| Line | Literal | Judgement |
|---|---|---|
| 9195 | `2026-09-28-trace-m0` | neutralised trace id (the post-rename form) in a `T10` row — internal provenance |
| 9196 | `2026-09-28-trace-m0` | same, `T10`/`gate_min` |
| 9198 | `2026-09-28-trace-m0` | same, `T10`/`stage` |
| 9200 | `2026-09-28-trace-m0` | same, `T10`/`stage_route` |
| **9235** | **`"answer": "DUVAL_HOSTED_LAYER_OK"`** | **the target repo name, uppercase, in the `answer` field of a `T17`/`selfselect` row — exactly the miss the third sweep found and every lowercase grep missed** |
| **9239** | **`"answer": "DUVAL_HOSTED_LAYER_OK"`** | same, `T17`/`stage` |

`gated-read-batching-released/README.md:125` — "trace identifier in `answer`, which named the target
project. It was replaced with the equal-length neutral identifier `2026-09-28-trace-m0`." Judgement: the
package's own README **documents** the rename, and the rename was applied to 4 rows but **not** to the two
`T17` rows — the documentation claims something the data contradicts.

`gated-read-batching-released/data/gated-read-rows.jsonl` — `consonance`, 437 occurrences on 225 lines,
distinct forms: `docs/CONSONANCE_PLAN.md` ×234, `CONSONANCE.md` ×202, `Consonance` ×1. Judgement: the
parent project's name as corpus filenames inside `tag`/`file` fields — **data the paper's numbers depend
on**, and this is a **known, recorded gap**: `papers/gated-read-batching/GAPS.md:204` (G-23) states the
anonymising rename described in `ULEAD1`'s manifest "was **not** performed". So the 224 data rows are the
gap made visible; the sweep confirms it is still open.

`gated-read-batching-released/results/GATED_READ_2026.md:1` (the `Consonance` form) — same corpus naming in
the results narrative.

`gated-read-batching-released/README.md:11` — `scratch/upkginstall7/build_archive.sh`: workspace build path
(also the only `unit_ids` hit on this surface). Judgement: internal build record, should not be in a
deposit README.
`gated-read-batching-released/README.md:15` — `tools/package/check_manifest.py`: workspace tool path.

Tooling names (reported separately for the author to judge): `deepseek` 9271 occurrences / 9268 lines —
`deepseek-v4-flash` ×9143 and `deepseek-v4.1-flash` ×126 in the data rows, plus
`results/GATED_READ_2026.md` (5), `results/gated-read-summary.json` (2),
`results/GATED_READ_PROVENANCE.md:7` containing **`DEEPSEEK_API_KEY`** ("`web_search` is unavailable in this
session (`DEEPSEEK_API_KEY` missing)") — a *variable name*, not a value, but secret-shaped;
`results/GATED_READ_2026.md:331` `non-DeepSeek`; `results/GATED_READ_2026.md:5` `mimo-v2.6-flash`;
`data/gated-read-rows.jsonl:9028` `keyring` (a search term inside a router row).

### 4.2 Paper #1 package — `papers/encoder-crossover-190/released/` (**already public on Zenodo**)

| File:line | Literal | Judgement |
|---|---|---|
| `SUPERSEDED-UNPACKED-TREE.md:3` | `(UDEPOSIT2)` | internal orchestration unit id |
| `SUPERSEDED-UNPACKED-TREE.md:24` | `scratch/udeposit2/superseded-unpacked-tree/` | workspace path |
| `SUPERSEDED-UNPACKED-TREE.md:25` | `scratch/udeposit2/superseded-unpacked-tree.sha256` | workspace path |
| `SUPERSEDED-UNPACKED-TREE.md:35` | `scratch/uneutral10/package/`, `scratch/uzenodo2/run2/CITATION.cff` | workspace paths naming the canonical tree |
| `SUPERSEDED-UNPACKED-TREE.md:38` | `strategy/DEPOSIT_ARCHIVE.md` | workspace spec path |
| **`encoder-crossover-190-released/CITATION.cff:30`** | **`# DOI installed 2026-10-18 (UDOIBACK1) …`** | **internal unit id — inside the published archive** |
| **`encoder-crossover-190-released/CITATION.cff:31`** | **`# CONCEPT DOI installed 2026-10-18 (UCONCEPT1) …`** | **internal unit id — inside the published archive** |
| `encoder-crossover-190-released/second-labeller/EVIDENCE.md:152` | `mimo-v2.6-flash` | model name, legitimately part of a robustness check |
| `encoder-crossover-190-released/second-labeller/RUN.json:157` | `mimo-v2.6-flash` | same |

`SUPERSEDED-UNPACKED-TREE.md` sits **beside** the `.tar.gz`, not inside it; `CITATION.cff` is **inside** the
archive — the fresh extraction reproduces exactly the 2 unit-id hits at `CITATION.cff:30,31` and no others.
So the public archive leaks unit ids only through two comment lines; the payload directory adds a
`scratch/`+`strategy/`+unit-id trail in the superseded-tree note.

No `duval`, no `2026-09-28`, no `duval_hosted_layer_ok`, no `zer0null`/`zeronull`, no `consonance`, no
`/home/`, no `orchestration/`, no `dockets/` on this surface.

### 4.3 Paper #3 package — `papers/replay-record-not-decision/released/`

**Zero hits, every pattern, payload and fresh extraction.** The two data files
(`data/decision-variants.jsonl`, `data/l1-head-to-head.jsonl`) carry none of the target-name, trace-id,
path or tooling patterns, and `verify/recompute-claims.py` and `README.md` carry none either.

### 4.4 Canonical tree — `scratch/uneutral10/package/`

**Zero** target-name, trace-id, path, `zer0null`, or `consonance` hits. Two `mimo` hits only:
`second-labeller/EVIDENCE.md:152`, `second-labeller/RUN.json:157` (model name).
**See the disagreement in §7: this tree is not paper #3's.**

### 4.5 The papers themselves (manuscripts, claims, LaTeX) — yes, there are hits

| File:line | Literal | Judgement |
|---|---|---|
| `papers/replay-record-not-decision/CLAIMS.md:12` | `state/refresh-verify/duval/scnB/state/kg-refresh/duval/repo/.worktrees/engine-a/docs/research/decision-variants.jsonl` | target name **twice** in a workspace path in the data-provenance table |
| `papers/replay-record-not-decision/CLAIMS.md:13` | same path form, `…/l1-head-to-head.jsonl` | same |
| `papers/replay-record-not-decision/CLAIMS.md:14` | same path form, `…/experiments/EXP#7-replay-divergence.md` | same |
| `papers/replay-record-not-decision/CLAIMS.md:15` | `state/refresh-verify/duval/scnB/…/evals/fixtures/reflex-decisions.ts` | same |
| `papers/gated-read-batching/CLAIMS.md:13` | `2026-09-28-trace-m0` | the neutralised trace id named in the claim's evidence row |
| `papers/replay-record-not-decision/MANUSCRIPT.md:141` | `scratch/urever2/verify_divergence.py` | workspace path in the manuscript body |
| `papers/replay-record-not-decision/MANUSCRIPT.md:225,245` | `strategy/PAPER2_REVERIFICATION.md:149/:152` | workspace path in the manuscript body |
| `papers/replay-record-not-decision/CLAIMS.md:21,22,194,196` | `scratch/urever2/…`, `scratch/udraft2/…`, `scratch/ufixtex1`, `tools/package/md2tex.py` | workspace paths |
| `papers/replay-record-not-decision/AVAILABILITY.md:29` | `scratch/urever2/…`, `scratch/uda…` | workspace paths |
| `papers/replay-record-not-decision/GAPS.md:153,155` | `scratch/ufixtex1`, `tools/package/md2tex.py` | workspace paths |
| `papers/encoder-crossover-190/CLAIMS.md:4` | `strategy/PAPER_CANDIDATES.md` §A3 | workspace spec path |
| `papers/encoder-crossover-190/AVAILABILITY.md:57` | `strategy/licence-templates/RELEASED-PIECE/` | workspace path |
| `papers/encoder-crossover-190/GAPS.md:3` | `strategy/PAPER_CANDIDATES.md` | workspace path |
| `papers/gated-read-batching/GAPS.md:108,204` | `strategy/GATED_READ_REVERIFY.md`, `ULEAD1`'s manifest | workspace path + unit id |
| `papers/replay-record-not-decision/AVAILABILITY.md:3`, `GAPS.md:3` | `(UPKG2C)` | internal unit id |
| `papers/*/MANUSCRIPT.md`, `CLAIMS.md`, `GAPS.md`, `AVAILABILITY.md` | `UPAPER1a`, `UFIXFMT3`, `UBIB2`, `UFIXBIB4`, `UFIXGR7`, `ULEAD1`, `UDOIBACK1`, `UCONCEPT1`, `UDEPOSIT2`, `UPKG2C`, `urever2`, `udraft2`, `ufixtex1`, `udeposit2`, `upkginstall7` | internal unit ids / scratch dir names — 36 occurrences over 32 lines |
| `papers/*/submission/main.tex:4` (all three) | `\usepackage[utf8]{inputenc}` | **false positive of the id regex** — `utf8` matches `\bU[A-Z]{2,}[0-9]` case-insensitively; not a unit id |

Tooling in the paper text: `deepseek` 19 occurrences / 16 lines, `mimo` 12/12, `step-5-preview` 6/6 —
across `MANUSCRIPT.md`, `CLAIMS.md`, `GAPS.md` and `submission/main.tex` of all three papers. These look
like deliberate methodology statements (the papers name the model and the runtime), but the card asked that
they be reported separately rather than silently bundled, so: **the model and runtime names are printed in
the papers' own LaTeX**, not only in the data.

`duval` in `submission/main.tex`: **zero**, in all three papers. `duval` in `MANUSCRIPT.md`: **zero**.
The target name reaches the paper layer only through `papers/replay-record-not-decision/CLAIMS.md:12–15`.

### 4.6 Public-repo working copies in this workspace

The workspace holds ~45 copies of `research-publish-packages`. The four with a configured remote —
`scratch/urepo1/repo`, `scratch/urepoman1/clone`, `scratch/ureadme2/clone`,
`scratch/urepoman1/verify_clone` — contain **0 files with `duval` and 0 with
`duval_hosted_layer_ok`**. Older scratch copies carry pre-cleanup state and are **not** release surfaces:
`scratch/uver11/A/research-publish-packages/gate.sh:37` is a bare `duval` line;
`scratch/uver11/C/…/gate.sh:37` same; `scratch/uver11/D`, `scratch/ufix14/red2`, `scratch/ufix14/redcheck`
hold `fixture/DECISION_CASE_SCHEMA.ts:2` and `harness/data/manifest.json:5,10,15` with
`/home/zer0null/Duval/.worktrees/…` absolute paths — historical leaks that are gone from the current
release payloads. Flagged because they show the class of thing that used to ship, not because they ship now.

## 5. The three answers

**1. Is paper #3's published deposit affected?**
On the surfaces named in the card, **no target-name hit exists** in paper #3's package
(`papers/replay-record-not-decision/released/`, payload and fresh extraction) or in the canonical tree it
points at (`scratch/uneutral10/package/`): `duval`, `2026-09-28`, `duval_hosted_layer_ok`,
`zer0null`/`zeronull`, `consonance` are all zero. **But the premise needs correcting before anyone acts on
"paper #3 is already public":** (a) the only DOI'd deposit in this workspace is
`doi: "10.5281/zenodo.23463944"`, declared in
`papers/encoder-crossover-190/released/encoder-crossover-190-released/CITATION.cff:25` — paper #1's
archive — while **paper #3's own** `CITATION.cff:33` says "No DOI exists for this deposit yet";
(b) the file the third sweep found, `data/gated-read-rows.jsonl`, is in **paper #2's** package, not paper
#3's. So: the published deposit that *is* affected is paper #1's, and only in the unit-id/path class
(`CITATION.cff:30–31` inside the archive; `SUPERSEDED-UNPACKED-TREE.md` beside it). If the author believed
the `DUVAL_HOSTED_LAYER_OK` rows were in the published deposit, they are not — they are in paper #2's
unpublished archive, which is good news and should be stated plainly.

**2. Do the other two archives have the same class of miss?**
**Paper #2 does, and it is the severe one.** `"answer": "DUVAL_HOSTED_LAYER_OK"` survives at
`data/gated-read-rows.jsonl:9235` and `:9239` (uppercase, in a field no lowercase grep reached), the trace
id at `:9195,:9196,:9198,:9200`, 224 rows of `CONSONANCE*` corpus names (a documented-but-open G-23), and
build paths in its README. **Paper #1 does not have the name class** but does have the path/unit-id class
(`CITATION.cff:30–31` inside the published archive; `SUPERSEDED-UNPACKED-TREE.md:3,24,25,35,38`). Paper #3
is clean on all of it.

**3. Are there hits in the papers themselves?**
**Yes, in the paper *support* files, not in the LaTeX.** `submission/main.tex` of all three papers is free
of `duval`; the only `main.tex` hits are the `utf8` regex artefact and the model/runtime names. But
`papers/replay-record-not-decision/CLAIMS.md:12–15` prints
`state/refresh-verify/duval/scnB/state/kg-refresh/duval/repo/…` four times (8 occurrences of the target
name), and all three papers' `MANUSCRIPT.md`/`CLAIMS.md`/`GAPS.md`/`AVAILABILITY.md` carry internal unit
ids (36 occurrences) and `scratch/`, `strategy/`, `tools/package/` workspace paths. If `CLAIMS.md`/`GAPS.md`
are ever sent to a venue or posted alongside the paper, they leak the target and the workspace layout.

## 6. Programme of measurement

Every count above is reproducible:
`bash scratch/ucasessweep1/sweep.sh` (control + counts matrix), `bash scratch/ucasessweep1/hits.sh`
(per-hit lines), `bash scratch/ucasessweep1/hits2.sh` (exact literals on the flagged rows, tooling hits,
surface trees, clone state). Raw outputs: `scratch/ucasessweep1/out/counts.tsv`,
`scratch/ucasessweep1/out/perfile.tsv`, `scratch/ucasessweep1/out/control.txt`.
No `git` command was run against `/home/zer0null/Duval` or any registered target; no target was read
through git at all. Nothing was repaired, rebuilt, or re-uploaded.

## 7. Disagreements with the unit card (reported, not smoothed over)

1. **`scratch/uneutral10/package/` is not paper #3's canonical tree.** Its own contents are the
   encoder-crossover package (`fixture/fixture-190.json`, `second-labeller/`, `results/eval-setfit-mpnet.json`,
   `results/REPORT.md`, `verify/recompute-claims.py`), and `papers/encoder-crossover-190/released/SUPERSEDED-UNPACKED-TREE.md:35`
   names `scratch/uneutral10/package/` as one of *its* inputs, with "29 files" matching that tree's 29
   files. It is the canonical tree behind **paper #1's** deposit.
2. **The third sweep's `DUVAL_HOSTED_LAYER_OK` miss is in paper #2's package**
   (`papers/gated-read-batching/released/…/data/gated-read-rows.jsonl`), not paper #3's.
3. **"Paper #3's published deposit" is not supported by the trees.** Paper #3's `CITATION.cff:33–34` and
   `README_DEPOSIT.md` say no DOI has been minted for it; the only DOI present is paper #1's
   `10.5281/zenodo.23463944`. If a paper #3 deposit does exist on Zenodo, it is not represented by any
   tree in this workspace, and that fact should be resolved by the author before any correction decision.
4. Minor: `AVAILABILITY.md` and `README.md` do not exist for every paper (gated-read-batching has neither
   `AVAILABILITY.md` nor `README.md`; encoder-crossover and replay have no `README.md`), so "the three
   papers' `AVAILABILITY.md`" is two of three.

## 8. Not verified / limits

- The Zenodo record itself was not fetched or inspected; publication status is inferred from the packages'
  own `CITATION.cff` / `README_DEPOSIT.md` text.
- "Every hit" is exact for the 20 patterns on the named surfaces; it is not a proof of absence for
  semantically equivalent leaks (e.g. an answer field naming the target in a form that shares no characters
  with `duval`, or a path under a target name that is not `Duval`). The control shows the *patterns* fire;
  it cannot show that the pattern list is complete, and three prior sweeps are evidence that it may not be.
- Coverage of surface 6 is a sample: four remote-bearing clones plus every scratch copy of
  `research-publish-packages` reachable at depth 3; deeper or differently named copies were not enumerated.
- Sizes/digests of the archives were not re-measured; this unit did not touch package contents.
