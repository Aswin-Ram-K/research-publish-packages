# COHERENT BIJECTION — EXTENSION 2 (UBIJ3)

**Unit:** UBIJ3 — bounded repair-and-measurement unit.
**Baseline:** `scratch/ubij1/tree-one-r2` (UBIJ1, known-good, invariant-safe).
**Delivered tree:** `scratch/ubij3/tree-three-r2` — 45 files, 3,006,637 bytes.
**Transform:** `NEUTRAL-TAG/v1` substitution, `map_shipped: false` (in-memory only; never written to disk, never logged).
**Verdict: `scratch/ubij3/tree-three-r2` should be the release artifact.** UBIJ1's tree remains a valid fallback but is strictly dominated (see §6).

---

## 1. The invariant, and how it is enforced

The text the model reads — fixture `question` / `options` / `situation` values, and the rendered `situation`
strings inside `harness/data/train.jsonl` and `harness/data/dev.jsonl` — must be **byte-identical**.

Two independent mechanisms enforce it:

1. **Fix 1 — needles derived from the rendered value surface, masking before any JSON re-encoding.**
   The builder reads `harness/data/train.jsonl`, `harness/data/dev.jsonl`,
   `harness/data/fixture-190.json`, `harness/data/corpus.json` and
   `second-labeller/disagreements.jsonl`, collects every string value reachable under the prose keys
   (`question`, `options`, `situation`, `state`, `instructions`, `criteria`, `constructionRule`), and pins
   each one as a needle — **4,305 pinned rendered values**. In non-JSON text every `"…"` / `'…'` / `` `…` ``
   literal is decoded (JSON escapes, `\u`, JS escapes) and its raw span masked when the decoded value is in
   that needle set. For `.json` / `.jsonl` the prose-key subtrees are **never handed to the substituter at
   all**: those files go through a structural transform (parse → rename keys and non-prose string values →
   re-dump in the file's own detected canonical format), which preserves prose values by construction rather
   than by hope. This is the fix for UBIJ2 defect 1: composed **rendered** `situation` strings are now covered
   by needles, so the 554 in-stimulus occurrences UBIJ2 rewrote cannot be reached.

2. **Fail-closed guard — the check UBIJ2 lacked.**
   Before writing any output tree, the builder runs the **identical scanner**
   `scratch/ubij1/census_one.py` as a subprocess on the baseline and on the temp build, and requires the
   inside-stimulus **count** *and* the **distinct-identifier** count to be exactly equal. Any mismatch →
   `shutil.rmtree(tmp)` and exit 3, no tree written. Nothing is emitted on failure.

> **Lowering the headline by lowering in-stimulus is a FAILURE, not an improvement.** That is the rule the
> guard encodes, and it is the rule under which UBIJ2's 3,118 is rejected.

## 2. Fix 2 — the JSON-escape corruption, proven fixed

UBIJ2's substitution lookbehind omitted the backslash, so at `\nCandidate` the substring `nCandidate` (a
census identifier) matched with `\` as the preceding character and was rewritten, leaving
`harness/tccommon.py:118` reading `\F19 option:` instead of `\nCandidate option:` — and emitting an invalid
Python escape (`SyntaxWarning: "\F" is an invalid escape sequence`).

Fix: `lb = r"(?<![A-Za-z0-9_.\\])"` — the backslash is now part of the negative lookbehind, so no identifier
that is the tail of a JSON/JS escape can be matched. Equivalently, the JSON path never substitutes raw text.

Proof (literal, in the emitted tree):

| check | baseline `tree-one-r2` | emitted `tree-three-r2` |
|---|---|---|
| `harness/tccommon.py:118` | `return f"{render_context(kind, situation)}\nCandidate option: {' '.join(str(option).split())}"` | **identical** |
| `harness/prepare.py:148` (`\nKind … \nCandidate option:`) | `"template": tc.TASK_PREFIX + "\\nKind: {kind}\\nSituation: {situation}\\nCandidate option: {option}"` | **identical** |
| `nCandidate` occurrences | 2 (both escapes) | **2, both preserved, 0 inside stimulus** |
| `F19 option` occurrences | 0 | **0** |
| `compileall` | — | **exit 0, no SyntaxWarning** (UBIJ2 emitted `"\F" is an invalid escape sequence`) |
| lines matching `\<letter>` | 64 | 68 |
| of those, invalid `\<UPPER>` | 1 | **1 — the same one** |

The single `\<UPPER>` line in either tree is `harness/data/manifest.json:22`:

```
"template": "Task: pick the one option the situation selects.\\F32: {kind}\\F39: {situation}\\F45 option: {option}"
```

This is **not** an escape corruption: the identical line, with the identical decoded value
(`\F32` / `\F39` / `\F45` as literal backslash-F placeholders), is already present in the **untransformed**
`scratch/uneutral3/tree-stripped` (`sha256 7c54a314…`) and is byte-identical in all four trees
(`tree-one-r2`, `tree-two-r2`, `tree-three-r2`: `58ae7f69…`). `\F<nn>` is the dataset's own field-placeholder
notation and predates every transform in this chain. Nothing in this unit touched it.

**Every line that ever contained a `\n<Identifier>` sequence is unchanged from the baseline.**

## 3. Fix 3 — the missing verifier

**Why it vanished:** the loss is upstream of both UBIJ1 and UBIJ2. `scratch/uneutral3/gen-pinned.log`, step
**"R0 copy"**, records `"files_copied": 41` with
`"own_artefacts_skipped": ["INTEGRITY.md","README.md","REDACTION_REPORT.md","redact.py","variants","verify"]`.
`verify/` was therefore never in `tree-pinned`, hence never in `tree-stripped`, hence absent from
`scratch/ubij1/tree-one-r2` and `scratch/ubij2/tree-two-r2` — each of which ships a `verify/` holding only
`redaction-log.json`. UBIJ1 concealed the gap at diagnostic time: `scratch/uneutral3/run_diags.sh` does
`cp "$LIVE/verify/recompute-claims.py" "$TREE/verify/recompute-claims.py"` with the comment
"the shipped verifier (not in the emitted tree; copied in from the live tree)".

**Fix:** the builder stages `verify/recompute-claims.py` from
`repro/encoder-crossover-190-SANITISED/verify/recompute-claims.py` into the emitted set. Shipped copy in
`scratch/ubij3/tree-three-r2` has sha256
`3e67a39eadc9a4f65d32462ec7093c167d01089089a7a88b131415ef65275dc5` — **identical to the authoritative
SANITISED copy**. It runs standalone, exit 0, printing `ALL CLAIM NUMBERS PRESERVED: True`.

File-set proof: `diff` of baseline vs emitted file lists is exactly
`43a44  > ./verify/recompute-claims.py` — 44 baseline files all present, one file added, **45 files**.

Other `verify/` artefacts SANITISED carries that `tree-stripped` omits (enumerated, deliberately **not**
added, since the card names only `recompute-claims.py`): `RECOMPUTE-CLAIMS.txt`, `RESIDUAL-SCAN.txt`,
`VERIFICATION.txt`, `integrity-table.md`, `run-verification.sh`, `scrub-uscrub1.py`.

## 4. Measurements

### 4.1 Frozen census (the 184-identifier list) — identical scanner on both sides

`python3 scratch/ubij1/census_one.py <tree>` (logs in `scratch/ubij3/census-*.txt`)

| tree | files | TOTAL | inside-stimulus | outside | keys | distinct ids hit |
|---|---|---|---|---|---|---|
| `scratch/uneutral3/tree-stripped` (source) | 44 | 9,247 | 2,171 | 5,701 | 1,375 | — |
| `scratch/ubij1/tree-one-r2` (UBIJ1) | 44 | 5,364 | **2,171** (d=30) | 2,024 | 1,169 | 90 / 184 |
| `scratch/ubij2/tree-two-r2` (UBIJ2) | 44 | 3,118 | **1,617** (d=30) ← broken | 1,381 | 120 | 73 / 184 |
| **`scratch/ubij3/tree-three-r2` (MINE)** | **45** | **3,348** | **2,171** (d=30) | **1,099** | **78** | **74 / 184** |

Mine vs UBIJ1: total **−2,016 (−37.6 %)**; inside **Δ 0**; outside **−925**; keys **−1,091**.

Per-class, mine vs baseline: `data-jsonl` inside 1,221 / outside **0** / keys **0** (baseline: 1,221 / 164 /
1,000) — the *only* movement in the JSONL stimulus carriers is outside/keys. `prose-md` and `ts` identical
(0 / 13 and 0 / 598).

### 4.2 Complete decode (frozen list **plus** the `K01..K10` code layer) — a separate number

`python3 scratch/ubij3/kcensus3.py <tree>` — K layer is **3,676 in every tree** (outside-values 3,586,
keys 90, **inside-stimulus 0**), i.e. the K layer is untouched and never in stimulus.

| tree | frozen | K layer | **complete decode** |
|---|---|---|---|
| `tree-stripped` | 9,247 | 3,676 | 12,923 |
| UBIJ1 `tree-one-r2` | 5,364 | 3,676 | 9,040 |
| UBIJ2 `tree-two-r2` | 3,118 | 3,676 | 6,794 |
| **MINE `tree-three-r2`** | **3,348** | 3,676 | **7,024** |

A headline that adds these two is a different figure from the frozen census; they are reported separately
here and must not be mixed.

### 4.3 Guard result

```
GUARD  baseline inside=2171 distinct=30 total=5364
GUARD  emitted  inside=2171 distinct=30 total=3348
GUARD  inside-stimulus delta = +0
GUARD PASSED: model-readable stimulus preserved exactly (delta 0).
```

Independent corroboration (not the guard — a separate digest):

```
baseline stimulus-digest 26c5ddcb4b68d5c3181db388b7bb0bf829e73c72304d5f0d3d302bb40c9d4653
mine     stimulus-digest 26c5ddcb4b68d5c3181db388b7bb0bf829e73c72304d5f0d3d302bb40c9d4653
STIMULUS IDENTICAL: True
```
(sha256 over the 190 fixture `question`+`options` and the 1,000 rendered `situation` strings.)

### 4.4 Bytes, files, idempotence

| tree | files | bytes |
|---|---|---|
| `tree-stripped` | 44 | 3,096,483 |
| UBIJ1 `tree-one-r2` | 44 | 3,057,815 |
| UBIJ2 `tree-two-r2` | 44 | 3,038,324 |
| **MINE `tree-three-r2`** | **45** | **3,006,637** |

**Idempotence: PASS** — two consecutive builds into `tree-three-r2` and `tree-three-b` are byte-identical
(`diff -r` exit 0); manifest digest `995299b123335bf4c9414f3cb84ab834eec33b7721b1b3b82607783ceb9d466f`.
The headline figure is taken from the **pristine** `tree-three-r2` (no `__pycache__`, no `*.out`/`*.err`;
`find -type f` = 45). All instrumented runs happened in a copy, `scratch/ubij3/tree-three-run`, because
running the tools mutates the tree they run in — the trap UBIJ1 and UBIJ2 both hit.

### 4.5 Tool exit codes, in the emitted tree

| command (run in `scratch/ubij3/tree-three-run`, a byte copy of the pristine tree) | exit | output |
|---|---|---|
| `python3 -m compileall -q .` | **0** | (empty — no warnings) |
| JSONL parse `harness/data/train.jsonl` | — | **800 records, 0 bad**, sha256 `95e0ea1314a01efc…` |
| JSONL parse `harness/data/dev.jsonl` | — | **200 records, 0 bad**, sha256 `a9cd7e4a0698b628…` |
| JSONL parse `second-labeller/disagreements.jsonl` | — | **18 records, 0 bad**, sha256 `cb719d3a3b02a946…` |
| `python3 parse_fixture.py` (in `second-labeller/`) | **0** | `records_found 190`, `cases_parsed 190`, `parse_failures []`, `options_total 721`, `distinct_labels 74` |
| `python3 compare.py` (in `second-labeller/`) | **0** | `cases 190`, routeA agreement `0.34210526315789475`, kappa `0.32520740993294694`, exact `65`, ties `120`, zero `41` |
| `python3 verify/recompute-claims.py` | **0** | see §4.6 — `ALL CLAIM NUMBERS PRESERVED: True` |
| `python3 harness/prepare.py` | **2** | `REFUSED: corpus digest mismatch — expected c78681d6cf35bf23245bd24963c5fbdd6b3ea03e1bf74d1b3ddc5a49ca63fd66, got f1359a72d0826dd6c44cf2672ddaa665cdeb35aad56f0f15f4ba52867bb5ddf3` |

`prepare.py` exits 2 on the **corpus-digest pin only** — a single `REFUSED` line, no traceback, no other
error. It is pre-existing (UBIJ1: `got 47fb4a50…`; UBIJ2: `got 1aa0ad32…`); the "got" value is a self-digest
of the corpus and necessarily changes under any renaming. Confirmed: the reason is that pin and nothing else.
Note the emitted tree ships `verify/recompute-claims.py` itself, so — unlike `run_diags.sh`, which had to
`cp` it in from the live tree — the verifier now runs where it lands.

### 4.6 Every metric re-measured here (nothing inherited from UBIJ2)

All from `verify/recompute-claims.py` (exit 0) and `second-labeller/compare.py` (exit 0) in the emitted tree:

```
arm modernbert-base  n=190 accuracy=0.347368 (recomputed 0.347368)
arm deberta-v3-base  n=190 accuracy=0.347368 (recomputed 0.347368)
arm setfit-mpnet     n=190 accuracy=0.263158 (recomputed 0.263158)
arm majority-class   n=190 accuracy=0.452632 (recomputed 0.452632)
arm shuffled-label   n=190 accuracy=0.231579 (recomputed 0.231579)
arm decider-4b-repro n=190 accuracy=0.678947
  2x2: both=39  headOnly=27  deciderOnly=90  neither=34  sum=190
ALL CLAIM NUMBERS PRESERVED: True
fixture correctness digest: c7696edc0e71d83faafc2e489925788e0f36c6af94913674f8953718352c9a55
```

From `second-labeller/metrics.json` (byte-identical to baseline, sha256 `6bf39077261f00be…`):

| metric | value |
|---|---|
| `routeA.ties` / `agreement` / `kappa` / `exact_index_matches` / `zero_score_cases` | 120 / 0.34210526315789475 / 0.32520740993294694 / 65 / 41 |
| `routeB_primary.agreement` / `kappa` / `exact_index_matches` / `n_disagreements` | 0.9052631578947369 / 0.9013584840356494 / 172 / 18 |
| `passes["labelsB.json"].AB_mutual_agreement` | 0.3526315789473684 |
| `stratification.closed_subset["labelsB.json"].kappa` | **0.8837023738280471** (n=106) |
| `stratification.roster_and_bespoke_subset["labelsB.json"].kappa` | **0.9139973672663448** (n=84) |
| `cases` / `options_total` / `disagreements_count_routeB` | 190 / 721 / 18 |

The 2×2 is 39/27/90/34 (sum 190) as expected. UBIJ2 had left the closed-vocabulary kappa, the roster kappa,
the two `0.347368` arms, the `0.263158` arm and the 2×2 un-extracted; all are measured here, and all match
UBIJ1's values.

### 4.7 Kept digests, baseline vs mine

| digest | baseline | mine | moved |
|---|---|---|---|
| fixture `harness/data/fixture-190.json` | `022be4a3c4ba3757…` | `022be4a3c4ba3757…` | **no** |
| `harness/data/train.jsonl` | `e81baca922b0b44e…` | `95e0ea1314a01efc…` | yes |
| `harness/data/dev.jsonl` | `4162971988fb8c35…` | `a9cd7e4a0698b628…` | yes |
| fixture correctness (recompute) | `c7696edc0e71d83f…` | `c7696edc0e71d83f…` | **no** |
| scoring projection (`cases.json`) | `620e4a07f8add8c5…` | `620e4a07f8add8c5…` | **no** |
| `second-labeller/metrics.json` | `6bf39077261f00be…` | `6bf39077261f00be…` | **no** |
| `MANIFEST.json` | `0553ea51672cb7f8…` | `0553ea51672cb7f8…` | **no** |
| `results/baselines.json` | `8d4c584cfa42441e…` | `90689d5789ad7868…` | yes |
| stimulus-only (prose values) | `26c5ddcb4b68d5c3…` | `26c5ddcb4b68d5c3…` | **no** |

The two JSONL digests move because record-level **non-prose** material was renamed (the `goldIndex` key and
other field keys, plus renamed values); the prose inside them is proven identical twice over (§4.3). The
fixture digest does not move because the fixture's `kind` values were *already* the neutral `K01..K10` code
layer before this chain started. `results/baselines.json` moves for the same non-prose reason.

Because the fixture's kinds were already `K01..K07/N10` in the source, the K layer is common to all trees —
which is exactly why the K figure (3,676) is constant and why it is reported apart from the frozen figure.

## 5. Packaging surface — enumerated, not decided

UBIJ2's "~369 occurrences" **does not reproduce**. It is unverified prose in
`strategy/COHERENT_BIJECTION_EXTENSION.md:236` ("Expected frozen census after the fix ≈ 2,540 (2,171 inside
+ ~369 outside/keys)") and `:276`; that document's own §6 rows sum to ≈607.

Measured over `tree-one-r2` and `tree-two-r2` (identical per-item counts in both):

- **309** raw per-item occurrences — `filename` 179 + `path` 100 + `pointer` 30
- **240** de-overlapped distinct match spans
- **187** of them in non-JSON text only (filename 111 + path 68 + pointer 8); 122 in JSON data values
- **keys 0, stimulus prose 0** — every one is outside the neutralised stimulus, which is why substitution
  never touched them
- 33 of 63 census ids occur; 30 occur in neither tree; max reachable over any tree = 316
- **plus 44 on-disk file names and 11 directory names**, which are occurrence-independent and were never
  counted in the 369 at all

Disagreements with the prior definition: `pointer` is **not** uniformly un-substitutable (all 9 present
pointer ids are plain strings and are reachable by substitution); and `filename` conflates **shipped** names
(`tccommon.py`) with **stale original-repo fragments** (`tools/typed-channel`,
`evals/fixtures/reflex-decisions.ts`) that do not resolve anywhere in this tree.

The genuinely un-renameable core — text substitution cannot rename a file:

| shipped name | vocabulary | refs | blast radius |
|---|---|---|---|
| `preregistration/EXP12-typed-channel-comparison-prereg.md` | `EXP12` + `typed-channel` | 1 | `MANIFEST.json:265` — best value per unit of work |
| `harness/tccommon.py` | `tc` = typed channel | 13 | 9 files (imports dominate) |
| `harness/tcmodel.py` | `tc` | 9 | 8 files (imports dominate) |
| `variants/no-union/` (+ its 2 fixture copies) | `no-union` ablation label | 9 | 2 files |
| `harness/LEAD-WIRING.md` | `LEAD` | 4 | 3 files |

Directories carrying vocabulary: `variants/`, `variants/no-union/`, `variants/no-union/files/`,
`variants/no-union/files/fixture/` (4 of 11).

Non-census labels (substitutable, not renameable): `imajev` **42 occurrences in 10 files** — the largest
single non-census leak, in `imajev-rows.jsonl`, `harness/{analyze,collect,evaluate,tccommon}.py`,
`results/REPORT.md`, `second-labeller/*` and the preregistration file; `second-labeller-190` 36;
`no-union` 9; `encoder-crossover-190` 4. `D15/D25/D09` are already-substituted neutral tags (out of scope).

Also found, in no census class: `MANIFEST.json` carries `"source": "…docs/research/EXP#12-evidence/…"` plus
`source_sha256` digests of **unreleased private-repo files** (e.g. `results/REPORT.md` →
`cc0b8c5ac16af61a4c1ecd5a1252bfd316a353ded81efb7355aec54bdf3bbc8d`). `MANIFEST.json` is also
self-inconsistent: it declares `counts.files: 42`, lists 2 files that do not exist on disk (`INTEGRITY.md`,
`README.md`) and omits 4 that do (42 − 2 + 4 = 44).

**Recommendation (author decides; nothing was renamed in this unit):** start with the preregistration file
(1 reference), then one mechanical pass for `tccommon.py` / `tcmodel.py`, then `variants/no-union/` (2 files)
and `LEAD-WIRING.md` (3 references). Decide deliberately whether `imajev` is project vocabulary or an
external public dataset name, whether `LEAD` is project vocabulary or a generic pipeline stage, and whether
`MANIFEST.json` should publish digests of unreleased files. Missing-file pointers (`INTEGRITY.md`,
`REDACTION_REPORT.md`, `SCRUB_REPORT.md`, `RESIDUALS.md`, `WIRING.md`, `L1_HEAD_TO_HEAD.md`) need no rename.
Generic names (`analyze.py`, `collect.py`, `evaluate.py`, `prepare.py`, `train.py`, `defect-probe.py`,
`lint.ts`, `export-fixture.ts`, `parse_fixture.py`, `DECISION_CASE_SCHEMA.ts`, `reflex-decisions(.ts)`,
`fixture-190.json`, `MANIFEST.json`, `verify/redaction-log.json`) are out of scope.

## 6. Why the in-stimulus 2,171 is irreducible

The 30 distinct identifiers with any in-stimulus presence are, in both trees:

```
editor, reasoner, model.call, attached, verifier, fs.read, fs.write, test.run, net.fetch,
detached, topology, output-only, code-inspector, memory.write, memory-curator, policyHash,
MATERIALISE, expanded[, broker, admit(, researcher, critic, web.fetch, code-review, escalation,
expiresAtEpoch, ToolCallIR, reasonerCalls, canRequestEscalation, MutationProposal
```

These are agent roles, tool name-caps and option-label fragments that occur **inside the rendered
`question` / `options` / `situation` prose the model reads** (e.g. `reasoner (propose only)`,
`editor (attached, writes)`). Renaming them would change the stimulus and invalidate every published number.
They are correctly left alone. UBIJ1 reached the same conclusion.

## 7. Verdict

**Ship `scratch/ubij3/tree-three-r2`.**

It is invariant-safe **and** better:

| | UBIJ1 `tree-one-r2` | UBIJ2 `tree-two-r2` | **UBIJ3 `tree-three-r2`** |
|---|---|---|---|
| frozen census total | 5,364 | 3,118 | **3,348** |
| inside-stimulus | 2,171 | 1,617 ← broken | **2,171 ← equal to baseline** |
| outside / keys | 2,024 / 1,169 | 1,381 / 120 | **1,099 / 78** |
| guard | n/a | absent (did not notice) | **PASSED, delta +0** |
| stimulus digest | `26c5ddcb…` | differs | **`26c5ddcb…` identical** |
| files / bytes | 44 / 3,057,815 | 44 / 3,038,324 | **45 / 3,006,637** |
| `verify/recompute-claims.py` | absent (copied in at diag time) | **absent** | **shipped, exit 0, claims preserved** |
| `compileall` | 0 | 0 with `invalid escape sequence` | **0, clean** |

- UBIJ2's 3,118 must **not** ship: its headline was bought by rewriting 554 in-stimulus occurrences, i.e.
  the run that produced the published numbers is no longer the run this package reproduces. A smaller
  residual bought with a broken invariant is worse than a larger one that holds.
- UBIJ1's 5,364 is valid and invariant-safe, but dominated: same in-stimulus floor, **+2,016** residual, and
  no shipped verifier.
- The corrected tree lowers the residual **without touching the stimulus**, which the stimulus-only digest
  and the guard both demonstrate, and it fixes UBIJ2's escape corruption and the missing verifier.

**Honest scope note.** The improvement comes from renaming more classes than UBIJ1's kind-only transform —
field keys (e.g. `goldIndex`, worth 1,000 key occurrences), `role` values and `tool-cap` values — in addition
to kinds. That is a wider blast radius, but every rename is invariant-safe by construction (structural JSON
transform for `.json`/`.jsonl`, rendered-prose needles elsewhere) and is verified by the fail-closed guard.
If the author prefers the narrowest possible blast radius over the lowest residual, `scratch/ubij1/tree-one-r2`
remains valid and invariant-safe; it is the fallback, not the recommendation.

**Residual caveats (not blockers).** (i) The 2,171 in-stimulus is irreducible under the invariant. (ii) The
packaging surface — 309 occurrences + 44 file names + 11 directory names — is not reachable by text
substitution; author decision, §5. (iii) `harness/prepare.py` exits 2 on a corpus-digest pin whose "got"
value must change under any renaming — pre-existing across all units. (iv) The emitted tree now has 45 files
while `MANIFEST.json` still declares 42 and does not list `verify/recompute-claims.py`; the manifest was not
edited (it is shipped data, and rewriting it is outside the sanctioned transform).

**Map handling.** The `NEUTRAL-TAG/v1` map (91 identifiers over the `kind`, `kind-dotted`, `field`, `role`
and `tool-cap` families) was built and held **in memory only**, `map_shipped: false`. It was never written to
disk and never printed; no mapping pairs are reproduced in this document. Three identifiers were explicitly
protected from renaming: `constructionRule` (read by `harness/prepare.py`), `criteria` (load-bearing JSON key
whose value subtree is prose), and `typed-channel` (a census `filename` — renaming text cannot rename the
shipped path).

*Reproduce:* `python3 scratch/ubij3/bij_three.py scratch/ubij3/tree-three-r2` (log
`scratch/ubij3/build-r2.log`). **Note 2026-10-16:** `bash scratch/ubij3/measure.sh` was removed by UPACK1 — it crashed on `KeyError: 'routeB'` (the metrics key is `routeB_primary`) and read `second-labeller/cases.json`, which is not shipped; its step-7 projection-digest claim is therefore **not reproducible by any shipped script**, and no command is invented for it. What it did reproduce runs instead as `python3 scratch/upack1/packaging_surface.py` (packaging counts, over `scratch/ubij3/tree-three-r2`) and `python3 scratch/ubij1/census_one.py scratch/ubij3/tree-three-r2` (identifier census over the 184-identifier list `scratch/uagnostic1/census.tsv`). See `scratch/upack1/MEASURE_SH_REMOVAL.md`.
