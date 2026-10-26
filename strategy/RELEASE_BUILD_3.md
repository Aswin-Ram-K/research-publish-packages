# RELEASE_BUILD_3 — a second package through the driver (unit URELEASE3)

**Purpose.** `orchestration/units/UBUILD1.build.sh` was refactored into a driver
(`--package <slug>`, per-package values in `orchestration/packages/<slug>.toml`)
that shipped exactly one manifest. This unit drives a **second** package,
`encoder-crossover-190` (paper #3, `papers/encoder-crossover-190/`), through it
into a scratch destination, verifies the emitted tree, and records what the
driver cannot yet do.

Nothing was weakened, disabled or edited: the driver, the other manifest,
`tests/test_package_build.py` and everything under `papers/**` are untouched.
The exclusion gate failing is the correct, expected outcome.

---

## 1. What was built

- Manifest: `orchestration/packages/encoder-crossover-190.toml` (+ its four
  fragments under `orchestration/packages/encoder-crossover-190/`).
- Emitted tree: `scratch/urelease3/dest/research-publish-packages/` with the
  package at `packages/encoder-crossover-190/` (29 files).
- Literal build stdout: `scratch/urelease3/build.log`.
- Gate JSON (per-class / per-file counts): `scratch/urelease3/gate.json`.

Command (the only build performed; never against a real release destination):

```
cd "/home/zer0null/reserach extarctor"
DEST="$PWD/scratch/urelease3/dest/research-publish-packages" \
  bash orchestration/units/UBUILD1.build.sh --package encoder-crossover-190 \
  2>&1 | tee scratch/urelease3/build.log
```

## 2. The manifest, and where every value came from

| key | value | derivation |
|---|---|---|
| `schema` | `1` | schema in `strategy/PACKAGE_BUILD.md` §1 |
| `slug` | `encoder-crossover-190` | must equal the filename stem; chosen from the paper directory |
| `name` | `encoder-crossover-190` | payload `README.md:1` titles it "Encoder-crossover-190"; deliberately **distinct** from the built-in default's historical `exp12-encoder-crossover` |
| `dest_default` | `/home/zer0null/research-publish-packages` | the shared publish repository (overridden to scratch in every run here) |
| `promoted_san_src` | `scratch/uneutral10/package` | the real 29-file released payload on disk |
| `frozen_san_src` | `repro/encoder-crossover-190-SANITISED` | the pre-promotion sanitised tree on disk |
| `licence_src` / `licence_files` / `licence_sha256` | `strategy/licence-templates/RELEASED-PIECE`, `LICENSE`+`COMMERCIAL.md`+`CONTRIBUTING.md`, `3d364676…e6f900` | measured: the template `LICENSE` is 5851 B, sha256 `3d364676a91dc579954b585e9d3a3c9f0dc03b723715805cc9431f757ce6f900` — the hash **before** the driver appends the scope clause |
| `anchors` | `["907fa39"]` | measured present in 4 payload files; `ad301ae` is present in 0 and is therefore not declared |
| `ship_staged` | the 29 files | `find scratch/uneutral10/package -type f \| sort` → 29/29; fail-closed, so a file omitted here is deleted |
| `never_ship` | 16 names | the frozen tree's process/audit documents (`EXCLUDED.md`, `INTEGRITY.md`, `LICENCE_TODO.md`, `REDACT3_REPORT.md`, `REDACTION_REPORT.md`, `RESIDUALS.md`, `SCRUB_REPORT.md`, `redact.py`), the generated `code/verify/*` outputs, and `paper/DISCLOSURE_CHANGES.md`; checked by **absence** |
| `readme_head`/`readme_tail`/`vocabulary_code`/`vocabulary_public` | `encoder-crossover-190/*` | the four fragments are byte-identical to the default package's: same payload, so the prose and declared vocabulary genuinely describe it |
| `neutralise_rules`/`neutralise_forbidden` | 3 path rules, `["/home/zer0null","duval"]` | repository-wide transform; not per-package |
| `commit_subject` | `Initial commit: encoder-crossover-190 data + verification package` | per-package |

The build's own cross-checks agreed: `staged 29 file(s): 29 kept, 0 dropped`;
`ship-list enforced: 29 staged file(s) present`;
`never-ship list enforced: 16 names checked absent`;
`vocabulary/data.txt: 501 declared data-file key(s) from 32 parsed document(s)`.

## 3. Build result

Driver stdout tail (verbatim):

```
scoped positive vocabulary check
...
flagged tokens: 1133
out-of-vocabulary token lines printed: 1133
GATE RESULT: FAIL -- 1133 out-of-vocabulary token(s).
BUILD COMPLETE — the exclusion gate FAILED (exit 1).
```

**Build exit code: 1** — the gate's rc, by design (driver lines 1016–1029).
No FATAL line, no pruning FATAL, no anchor FATAL.

## 4. Verification of the emitted tree

Run inside
`scratch/urelease3/dest/research-publish-packages/packages/encoder-crossover-190`:

| command | exit | key diagnostics |
|---|---|---|
| `python3 verify/recompute-claims.py` | **0** | `ALL CLAIM NUMBERS PRESERVED: True` |
| `python3 second-labeller/parse_fixture.py` | **0** | regenerates `cases.json`/`blinded_cases.json`…; no errors (it rewrites those files in the built tree) |
| `python3 second-labeller/compare.py` | **0** | route B κ `0.9013584840356494`, agreement `0.9052631578947369`, labelable 190, disagreements 18 |

Values against `papers/encoder-crossover-190/CLAIMS.md`:

| published | CLAIMS.md | emitted tree | verdict |
|---|---|---|---|
| second-labeller agreement | 0.9053 | 0.9052631578947369 | match |
| second-labeller κ (routeB-blind-model) | 0.9014 | 0.9013584840356494 | match |
| disagreements | 18 / 190 | 18 | match |
| route-A agreement | 0.3421 | 0.34210526315789475 | match |
| route-A κ | 0.3249 | 0.3248813212427869 | match |
| A/B mutual agreement | 0.3684 | 0.3684210526315789 | match |
| disagreements where route A backs the record | 4 | 4 | match |
| closed-vocabulary κ (106 cases) | 0.8837 | shipped 0.8837023738280471 | match |
| roster-and-bespoke κ (84 cases) | 0.9140 | shipped 0.9139973672663448 | match |
| arms / majority / chance floor | 0.3474 / 0.3474 / 0.2632 / 0.2316 / 0.4526 / 0.2911 | 0.347368 / 0.347368 / 0.263158 / 0.231579 / 0.452632 / 0.291053 | match |
| decider-4b same-run | 0.6789 | 0.6789473684210526 | match |
| McNemar b/c/p, paired MDE | 27 / 90 / 4.1668e-09 / 0.1595 | 27 / 90 / 4.166818e-09 / 0.159494 | match |

### 4a. FINDING — one *quoted* published delta does not reproduce

`recompute-claims.py` also re-checks the deltas the paper quotes, and reports:

```
route-A kappa: published=0.3252   tree=0.3248813212427869  reproduced=True  cite=papers/encoder-crossover-190/CLAIMS.md:108
A/B mutual agreement: published=0.3526  tree=0.3684210526315789  reproduced=False  cite=…/CLAIMS.md:109
```

So `CLAIMS.md:109`'s quoted A/B mutual agreement **0.3526** is not what the
shipped tree computes (**0.3684**); the tool itself marks it
`reproduced=False`. `CLAIMS.md:108`'s route-A κ 0.3252 vs the tree's 0.3249 is
inside the tool's 5e-4 tolerance and is marked reproduced. **Nothing was
adjusted to hide this** — it is recorded as a paper-side discrepancy against a
value the rest of the tree agrees with (0.3684 at `CLAIMS.md:109`'s companion
figures and in `compare.py`'s `routeB_primary.AB_mutual_agreement`).

Other literal numbers: `fixture correctness digest:
c7696edc0e71d83faafc2e489925788e0f36c6af94913674f8953718352c9a55` (the tool's
own digest over recomputed correctness data, not the fixture file's sha256;
the emitted `fixture/fixture-190.json` hashes to `a15224bada6950ad27f693acd2287dec564134419061baa475f6716d2db3852e`, while the
published fixture sha256 is `076164ac…b4796` — a *different* digest
construction, not a byte mismatch claim). McNemar 2×2: both=39, headOnly=27,
deciderOnly=90, neither=34, sum=190; psi=0.615789, delta=-0.331579.

## 5. The gate residual (the most useful output)

`gate.sh` **fails with 1133 out-of-vocabulary tokens** (its own split:
`prose-source` 774, `data` 359; 302 distinct token strings; 1132 of the 1133
lines matched by this unit's parser). Per-file offenders:

| count | file (under `packages/encoder-crossover-190/`) |
|---|---|
| 183 | `results/REPORT.md` |
| 90 | `second-labeller/compare.py` |
| 87 | `verify/recompute-claims.py` |
| 78 | `second-labeller/EVIDENCE.md` |
| 72 | `fixture/reflex-decisions.ts` |
| 66 | `second-labeller/OWED_CORRECTIONS.md` |
| 65 | `fixture/fixture-190.json` |
| 65 | `second-labeller/cases.json` (and `blinded_cases.json`, 65) |
| 51 | `second-labeller/parse_fixture.py` |
| 44 | `second-labeller/RUN.json` |
| 38 | `preregistration/EXP12-…prereg.md` and `second-labeller/PREREGISTRATION.md` |
| 28 | `MANIFEST.json` |

Classification of the residual (first-match keyword pass; buckets are
**not** a partition — see the unclassified note):

**(a) Third-party / incidental English — 490 occurrences, 192 distinct tokens.**
Ordinary words the frozen `/usr/share/dict` set lacks, or licence machinery.
Top: `redacted`(32), `pre-registered`(28), `licensor`(24),
`pre-registration`(21), `relist`(12), `mtime`(12), `uncompacted`(10),
`unscoped`(10), `typecheck`(8), `substring`(6), `unescape`(6), `arity`(5),
`deterministically`(4), `filesystem`(4), `unsatisfiable`(4),
`evaluator`/`evaluators`(4+4), `re-queryable`(4).
`licensor` is licence wording, not third-party prose — called out because the
keyword pass puts it here.

**(b) Released-schema-shaped — 288 occurrences, 47 distinct tokens.**
JSON keys, TS types and file names the shipped tools themselves emit.
Top: `workspace`(56) and its `workspace/…` path forms, `locator`(38),
`fh`(12), `labelsB.json`(10), `kk`(10), `acc`(9), `src/`(8),
`jload`(5), `perCase`(4), `pmf`(4), `semanticCalls`(4),
`requestedCapabilities`(4), `ActionIR`(4), `CapabilityGrant`(4),
`setfitRefitNote`, `reflex-decisions`, `Reducer`(3). The single-letter and
two-letter forms (`fh`, `kk`, `vv`, `esc`, `instr`, `strat`, `REC`) are enum /
field labels inside the stimulus, not English.

**(c) Mechanism identifiers inside the released stimulus — 354 occurrences,
63 distinct tokens.** Top: `ECE`(44), `kappa`(23), `MCP`(20), `UEXP`(19),
`decider`(17), `UFIX4`(17), `UVER3`(17), `decider-4b`(14), `URECUT1`(10),
`psi`(9), `argmax`(9), `softmax`(8), `MDE`(7), `imajev-4b`(7), `imajev`(7),
`predict_proba`(6), `McNemar`(5), `routeA`(5), `bwrap`(5), `deciders`(5),
`routeB-blind-model`(5), `cuda`(5), plus the model/route paths
`answerdotai/ModernBERT-base`, `microsoft/deberta-v3-base`,
`sentence-transformers/all-mpnet-base-v2`, `docs/research/P04-evidence/*.jsonl`.

**(d) Unclassified — 1 unparsed line + a 252-token long tail.** Beyond the 50
highest-count tokens (641 of 1133 occurrences) the classification is a
catch-all, not a hand audit: 491 occurrences over 252 distinct tokens sit in
bucket (a) by default because the keyword rules did not claim them. This unit
does not assert their class. The full per-line evidence is
`scratch/urelease3/build.log` (1133 `file:line: token [word not in the
declared vocabulary]` lines) and `scratch/urelease3/gate.json`
(`by_class`, `by_file`).

**Why this matters.** The residual is a property of the payload, not of the
second manifest: the same 1133-token count is recorded for the default package
in `strategy/PACKAGE_BUILD.md` §4. The package cannot ship until the residual
is *declared* (added to the manifest's vocabulary fragments, or to a declared
exceptions list) rather than scrubbed from the released evidence — scrubbing
would change the payload the claims are about.

## 6. What the driver could not do for a second package

1. **The two-way tripwire does not block a non-default package — it silently
   skips it.** Every comparison against the built-in literals is inside
   `if [ "$PKG_SLUG" = "$DEFAULT_SLUG" ]`: promoted/frozen trees
   (`UBUILD1.build.sh:312-319`), ship list (`:408-411`), never-ship list
   (`:494-497`), licence sha (`:555-558`). The `encoder-crossover-190` build
   accepted without a single cross-check against the driver's built-in block.
   That is *how* a second package builds at all, and also the limit: a
   non-default manifest has no second opinion on its ship list, anchors or
   licence hash. Ship-list safety still holds (fail-closed pruning), but the
   manifest can declare a *different* 29 files and the driver will not notice.
2. **The emitted root README index is still written whole from one hard-coded
   source.** `UBUILD1.build.sh:514`:
   `cat "$M_README_HEAD" > "$DEST/README.md"` — the entire root README is the
   single per-package fragment. For this package that fragment is
   `orchestration/packages/encoder-crossover-190/readme-head.md:13-17`, a
   "## Packages" table with exactly one row (linking
   `packages/exp12-encoder-crossover/`, the *default* package's name). So the
   emitted root README advertises the wrong package directory, and a second
   build into the same `$DEST` overwrites the first package's index. There is
   no manifest key for a package row and no aggregation across manifests; the
   driver merges per-package *content* but not the index. (The licence
   paragraph is likewise hard-coded "Case B" from
   `strategy/licence-templates/README-PARAGRAPHS.md` at `:519`.)
3. **`DEST` must end in `/research-publish-packages`** (`:292-295`). A build
   cannot be pointed at a neutral empty directory, only at something whose last
   path component matches — so this unit's scratch destination is
   `scratch/urelease3/dest/research-publish-packages`.
4. **`gate.sh` and the vocabulary rules are a here-doc inside the driver**
   (`:725-902`). The exclusion policy — which class a token falls in, and
   `english/code/public/data` vocabularies — cannot be tuned per package
   without editing the driver, which is exactly what this unit must not do.
5. **No package digest is pinned.** Only the licence template hash is asserted;
   the shipped payload can change freely between builds. (Not a defect for this
   unit, but the tripwire that would catch it is the one skipped in (1).)

## 7. Reproduce

```
DEST="$PWD/scratch/urelease3/dest/research-publish-packages" \
  bash orchestration/units/UBUILD1.build.sh --package encoder-crossover-190   # exit 1 (gate)
cd scratch/urelease3/dest/research-publish-packages/packages/encoder-crossover-190
python3 verify/recompute-claims.py            # exit 0, "ALL CLAIM NUMBERS PRESERVED: True"
python3 second-labeller/parse_fixture.py      # exit 0
python3 second-labeller/compare.py            # exit 0

### 4b. Fixture digest — three different numbers, stated precisely

- `scratch/uneutral10/package/fixture/fixture-190.json` (payload) sha256: `a15224bada6950ad27f693acd2287dec564134419061baa475f6716d2db3852e`
- emitted `packages/encoder-crossover-190/fixture/fixture-190.json` sha256: `a15224bada6950ad27f693acd2287dec564134419061baa475f6716d2db3852e`
- `CLAIMS.md` published fixture sha256: `076164ac53c2c1aac130953345c481f88b51f4d6fb93d465c7430308a99b4796`
- tool-printed `fixture correctness digest`: `c7696edc0e71d83faafc2e489925788e0f36c6af94913674f8953718352c9a55`

Payload vs emitted: identical — the driver preserved the fixture bytes, so the gap to the published 076164ac…b4796 is upstream of this build (paper-side, or a different artefact, or a different hash construction), not introduced by the second manifest. The published sha256 therefore does **not** equal the
sha256 of the fixture file this package ships; since `recompute-claims.py`
still returns `ALL CLAIM NUMBERS PRESERVED: True` on that fixture, the likely
explanation is that `CLAIMS.md`'s value hashes a different artefact (a
pre-sanitisation copy or a canonicalised form). Recorded as a discrepancy to
resolve paper-side, not adjusted here.

---

## UFIXPKG3 — fixing pass on the released payload (appended 2026-10-16)

Three defects from `strategy/RESIDUAL_TRIAGE_3.md` fixed in place in
`scratch/uneutral10/package` (backed up first to `scratch/ufixpkg3/before/`, 29 files).

**1. Genericisation — 147 occurrences / 29 distinct author-environment tokens removed.**
All internal unit/handoff names and working-directory path artefacts listed in
RESIDUAL_TRIAGE_3 §A.2 were replaced with neutral `Gnn` tags (`G33`–`G58`, disjoint from the
payload's existing `G01`–`G32`): `UEXP→G33`, `UFIX4→G34`, `UVER3→G35`, `URECUT1→G36`, `UCORR1/2/3→G37/38/39`,
`UVER2→G40`, `UTOOL1→G41`, `UNEUTRAL9/10→G42/43`, `UTS1→G44`; paths
`imajev-rows.jsonl→G45`, `experiments/second-labeller-190→G46`,
`repro/encoder-crossover-190-SANITISED/verify/recompute-claims.py→G47`, `repro/encoder-crossover-190*→G48`,
`packages/exp12-encoder-crossover/README.md→G49`,
`docs/evidence/selfbuild/relay-outbound-2026-10-13.txt→G50`, `evals/fixtures*→G51`,
`docs/research/EXP#12-evidence/→G52/`, `.worktrees/→G53/`, `strategy/D52/D59_3/D60→G56/57/58`,
`scratch/urecut1/build.py→G55`. Mapping is held only in `scratch/ufixpkg3/neutralise.py` and is
not written into the payload. Deliberately NOT rewritten: the package's own shipped path tokens
`results/eval-*.json` and `second-labeller/labelsB.json` — those appear in `MANIFEST.json` `"path"`
fields, which must stay byte-correct for the manifest's fail-closed listing (rewriting them would
falsify the manifest, not de-identify the author).

**2. `verify/recompute-claims.py` can now fail.** The stale expectation `0.3526` for the A/B mutual
agreement was corrected to the tree's own `0.3684210526315789` (`CLAIMS`, and the published value
`0.3684` in what was `PUBLISHED_STALE`, now `PUBLISHED_VALUES`); the reporting loop's `hit` flag is
now folded into `ok` (`ok &= hit`), and the summary line reports
`ALL PUBLISHED NUMBERS REPRODUCED: <bool>` plus an explicit `VERDICT: PASS|FAIL`. The other two
`ok &= hit` sites and every tolerance are untouched (nothing made less strict).

**3. `MANIFEST.json` regenerated** by replicating the documented procedure
(`scratch/urecut1/build.py:94-137`) in `scratch/ufixpkg3/rebuild_manifest.py`, then proved by an
independent check (shell `sha256sum`/`stat` over all 28 entries, fail-closed path-set equality,
`manifest_self` recomputation, banned-token scan). 29 files, `counts.files=29`, 20 entries with
`source_sha256`; old manifest provided the per-file `source` metadata, itself genericised.

**Proof.** Baseline vs edited tree, all three shipped tools:
`recompute-claims.py` 0→0, `parse_fixture.py` 0→0, `compare.py` 0→0. `parse_fixture.py` and
`compare.py` stdout+stderr byte-IDENTICAL. `recompute-claims.py` differs only in reporting lines
(the A/B row now `reproduced=True`, and the honest summary/verdict); every recomputed value, the
McNemar table, the `39+27+90+34=190` counts and the fixture correctness digest `c7696edc…9a55` are
unchanged. Red→green on a copy: green exit 0, change one published expectation → exit 1 with
`reproduced=False` and `VERDICT: FAIL`, restore → exit 0 (`scratch/ufixpkg3/redgreen/`). The pre-fix
tree exits 0 on that same mismatch while printing `reproduced=False` — the defect, demonstrated.
Idempotence: two manifest builds differ only in `generated_utc` (`manifest_self` stable).
Changed files: 10 of 29 — `MANIFEST.json`, `results/baselines.json`, `results/REPORT.md`,
`second-labeller/{compare.py,EVIDENCE.md,OWED_CORRECTIONS.md,parse_fixture.py,PREREGISTRATION.md,RUN.json}`,
`verify/recompute-claims.py`.

## UFIXPKG4 — residual bare-token, digest-label and paper-pairing closure (2026-10-16)
Payload `scratch/uneutral10/package` (29 files), backed up to `scratch/ufixpkg4/before/` before editing.
- **Job 1** residual `second-labeller-190` → **`G46`** (the payload's *existing* canonical tag for this experiment —
  `MANIFEST.json files[].source` already reads `G46/…`; no new tag invented, no collision) in
  `second-labeller/EVIDENCE.md:1`, `PREREGISTRATION.md:1`, `RUN.json:2`. A second same-class bare-form miss found by the
  prefix-independent sweep was closed the same way: `second-labeller/EVIDENCE.md:309` `D60` → `G58` (existing tag for `strategy/D60`).
- **Job 2** shipped-vs-`source_sha256` label confusion: `second-labeller/RUN.json:8-10` held the **as-audited instrument**
  digest `076164ac…b4796` under fixture-shaped keys. Renamed `fixture_sha256_before/after` → `instrument_sha256_before/after`
  and `sandbox_sha256` → `instrument_sandbox_sha256`, with a `_sha256_labels` note naming all three objects from `MANIFEST.json`.
  `results/REPORT.md:5` now names the as-audited source (`P05`, `076164ac…`, 145,031 B), the shipped instrument
  (`fixture/reflex-decisions.ts`, `369159b0…`, 81,284 B) and the shipped fixture (`fixture/fixture-190.json`, `a15224ba…`, 76,897 B).
  *(Dated note, UFIXPKG12 2026-10-16: `369159b0…`/81,284 B are the pre-clean-up bytes as they stood during
  UFIXPKG4. UFIXPKG10 later removed five comments from the shipped instrument, so its current value is
  `89e77a8e…e169`, 81,439 B, read from `scratch/uneutral10/package/MANIFEST.json:75-76`. Live residual outside this
  unit's write paths: `scratch/uneutral10/package/results/REPORT.md:5` and `second-labeller/RUN.json:12` still print the old pair.)*
  Paper-side consumers of the renamed keys updated: `CLAIMS.md:39,46`, `EVIDENCE_NOTES.md:278` and its dated note.
- **Stale constants re-verified as they are now**: `verify/recompute-claims.py:41` and `:122` were **already corrected**
  (no `0.3526` anywhere); only `second-labeller/RUN.json` route-A `0.3526315789473684` remained, and it is a **frozen
  pre-genericisation record** (it reproduces the dated pre-neutralisation output in `EVIDENCE_NOTES.md`), so the value was
  **kept** and annotated (`…_note`), not changed.
- **Job 3 (as of 2026-10-16, UFIXPKG4)** `MANUSCRIPT.md:800-802` paired the shipped path with the then-shipped digest
  `369159b0…` — **superseded 2026-10-16 by UFIXPKG10**, after the shipped instrument's bytes changed: `MANUSCRIPT.md:802`
  and `submission/main.tex:408` now cite `89e77a8e…e169` (81,439 B, `scratch/uneutral10/package/MANIFEST.json:75-76`) — and kept the as-audited
  definition `076164ac…` alongside it; `submission/main.tex` regenerated through `scratch/uprep1/md2tex.py` (run twice, `cmp` clean;
  the only diff is line 408).
- **Proof**: `verify/recompute-claims.py` (VERDICT: PASS, all published numbers reproduced), `second-labeller/parse_fixture.py`,
  `second-labeller/compare.py` all exit 0; `MANIFEST.json` regenerated by `scratch/ufixpkg3/rebuild_manifest.py` (the package's
  documented build.py:94-137 procedure) and checked independently (28 entries, per-file sha256+bytes, totals, banned-token scan).
  `counts.bytes_total` moved 828,303 → 829,574 only because the label text was added; **no published number in the paper moved**
  (the subset byte total is not published anywhere in `papers/encoder-crossover-190/`).
- **Reported, not fixed** (no unambiguous pre-existing tag, so no mapping invented): `SANITISED` ×9 as an ordinary English
  adjective; `imajev` ×19 (model-name fragments e.g. `imajev-4b`); `docs/research/P04-evidence/` ×4 in `results/REPORT.md:40-42`
  and `results/baselines.json:4` (they name a *different* file, `decider-rows.jsonl`).
- **Correction to the sweep report above (same session)**: the prefix-independent sweep was re-run payload-wide and found *three* further
  bare author strategy-doc ids inside narrative text, not one — `second-labeller/RUN.json:128-129` carried `D60` ×2 and `D52`
  once (`verdict`/`limitation` fields). Both have pre-existing tags (`strategy/D60`→`G58`, `strategy/D52`→`G56`) and were replaced;
  the payload now contains **zero** bare `D52`/`D56`/`D57`/`D58`/`D59`/`D60` identifiers.
- **Also reported, deliberately not changed** (path fragments with no unambiguous pre-existing tag, or naming a *different*
  file than the one the earlier unit neutralised): `docs/research/…` occurrences in `results/REPORT.md:40-42,46,121,269`,
  `results/baselines.json:4,2372`, `second-labeller/EVIDENCE.md:258,312`, `second-labeller/OWED_CORRECTIONS.md:22,91,115,120`,
  `second-labeller/RUN.json:109`; `experiments/…` in `preregistration/EXP12-typed-channel-comparison-prereg.md:2`,
  `OWED_CORRECTIONS.md:91,120`, `MANIFEST.json:82`; `repository/` as the ordinary-English phrase "the read-only target
  repository"; `strategy/` at `RUN.json:157`; and `SANITISED` once at `verify/recompute-claims.py:2` (ordinary-English
  adjective inside a description of the sanitised copy). No mapping was invented for these.
- Final `MANIFEST.json` sha256 `b489c3d85d6404856317613ed32b0ab7c8d5f05c228d5b2225cb14e2bf7b1e2b`; all three verification tools
  re-run after the final edit: rc 0/0/0, recompute-claims `VERDICT: PASS`.

## UFIXPKG5 — residual provenance references genericised (append, 2026-10-16)

The released payload's residual class (exact private-tree paths, tail document ids, private relative
links) was genericised in place using only the payload's own vocabulary: existing tags G46/G47/G48/G51/G52
plus coarse kind-descriptors already phrased in-payload. 37 count-asserted substitutions over 8 files.
No new tag minted. `MANIFEST.json` regenerated by `scratch/ufixpkg3/rebuild_manifest.py`
(29 files_on_disk, 28 entries, counts.bytes_total 830738, generator INDEPENDENT CHECK: PASS).
`verify/recompute-claims.py` still prints `VERDICT: PASS` and exits 0; `second-labeller/parse_fixture.py`
and `second-labeller/compare.py` exit 0; fixture-correctness digest c7696edc… unchanged.
`papers/encoder-crossover-190/submission/main.tex` regenerated via `scratch/uprep1/md2tex.py` twice —
byte-identical to each other and to the previous file (paper text unchanged). Leak-class residual scan: 0.
Retained by decision: bare tool/instrument labels (P04/P05/D01–D19/D42/D43/D48) — proposed tags G59/G60.

## UFIXPKG7 — classifier-directed reference fixes (append, 2026-10-16)

Applied the report-only classifier's ruling (`strategy/PARENT_REFERENCE_CLASSIFICATION.md`).

**Fix 1 (the one that ships).** `papers/encoder-crossover-190/MANUSCRIPT.md:301` path
`docs/research/EXP#11-evidence/decider-rows.jsonl` -> the in-workspace generic form
`the target repository's per-case decider rows` (the phrase the classifier names for the released
`submission/main.tex:146`; the `the target repository's …` form and `the target repository's findings
register:47` are already in-workspace, e.g. `strategy/PUBLISH_PACKAGE_MANIFEST.md:428`).
`submission/main.tex` regenerated only via `python3 scratch/uprep1/md2tex.py`, never hand-patched;
run twice, byte-identical; tarball rebuilt with one member.

**Fix 2 (released payload).** `scratch/uneutral10/package/fixture/reflex-decisions.ts:39,40,380,695,1889`
`see D43 §3` -> `see the withheld rationale note, section 3`, the in-payload form already used at
`scratch/uneutral10/package/second-labeller/OWED_CORRECTIONS.md:38` (`the withheld rationale note,
section 5`). Withheld status and the section pointer are both kept; no tag is left dangling.

**Fix 3 (existence check decides).** Literal results — under `/home/zer0null/Duval`: `src` EXISTS,
`kernel` EXISTS; `strategy`, `PAPER_CANDIDATES.md`, `experiments/second-labeller-190`, `second-labeller`
ABSENT. Under this workspace: `strategy` EXISTS, `experiments/second-labeller-190` EXISTS, `src` EXISTS;
`kernel` and bare `PAPER_CANDIDATES.md` ABSENT (the file is `strategy/PAPER_CANDIDATES.md`). Under the
payload: `second-labeller` EXISTS. Rulings: `main.tex:230` (`strategy/`) -> workspace, not a finding;
`:335` (bare `PAPER_CANDIDATES.md`) -> workspace shorthand, not a finding; `:387`
(`experiments/second-labeller-190/…`) -> workspace, not a finding; `:412` (`second-labeller/{…}`) -> the
payload's own shipped dir, not a finding; `:419` (`src/**`, `kernel/**`) -> resolves to the parent's
withheld implementation dirs (`kernel/` exists only there), genericised at its source
`MANUSCRIPT.md:836` to `the target repository's withheld implementation directories`.

**Fix 4 (tag vocabulary).** `scratch/ufixpkg7/tag_re_control.py` extends
`^(?:K|F|S|C|R|D)[0-9][0-9]$|^TAG_[0-9][0-9]$` to `^(?:K|F|S|C|R|D|P)[0-9][0-9]$|^TAG_[0-9][0-9]$`, adding
only the already-minted `P01`–`P05` family (`orchestration/units/UDTAG1.md:22-23`,
`strategy/WHOLE_CLASS_NEUTRALISATION.md:20`, `strategy/DTAG_NEUTRALISATION.md:40`). Red→green control:
`P01`–`P05` unrecognised by OLD, recognised by NEW; near-misses (`P`, `P1`, `P010`, `p01`, `D-067`,
`hello`, …) still rejected. The live gate copy (`orchestration/units/UBUILD1.build.sh:879`) was NOT
modified — it is outside this unit's declared write paths — so the extension is delivered as the proven
patch above for the gate's owner.

**Proof.** `verify/recompute-claims.py` PASS / rc 0 before and after (fixture correctness digest
`c7696edc0e71d83faafc2e489925788e0f36c6af94913674f8953718352c9a55` unchanged); `second-labeller/parse_fixture.py`
and `second-labeller/compare.py` rc 0/0 before and after; tarball re-extracted = exactly one member
`main.tex`, byte-identical to the on-disk file.
