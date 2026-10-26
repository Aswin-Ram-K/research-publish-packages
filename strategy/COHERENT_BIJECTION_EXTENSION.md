# COHERENT BIJECTION — EXTENSION (UBIJ2)

**Unit:** UBIJ2 · **Date:** see `orchestration/handoffs/UBIJ2.json` · **Author:** UBIJ2 (author, not verifier)
**Status: `partial`.** Deliverable written and measured; **the unit's ≤40 tool-call bound was exceeded**
(the build defects below forced three rebuild-and-measure cycles). Everything reported here was measured
inside this unit; nothing is carried over from UBIJ1's prose without re-measurement, and the one headline
I could not re-derive is named as unverified in §7.

---

## 0. TL;DR / verdict

| figure | which census list | base (stripped) | UBIJ1 `tree-one-r2` | **UBIJ2 `tree-two-r2`** |
|---|---|---|---|---|
| **frozen census total** | 184-identifier list `scratch/uagnostic1/census.tsv` | 9,247 | 5,364 | **3,118** |
| **complete decode** | frozen 184-id list **+ K01…K10 code layer (3,676)** | 12,923 | 9,040 | **6,794** |
| bytes | — | 3,096,483 | 3,057,815 | **3,038,324** |
| distinct identifiers hit /184 | frozen list | 99 | 90 | **73** |

**Money number: 3,118** (frozen census, from the pristine twin `scratch/ubij2/tree-two-r2`) —
**1,617 inside the model's stimulus** and **1,381 outside + 120 JSON keys**.

**Verdict: NOT shippable as built, and the reason is not the residual size — it is that the stimulus moved.**
The extension removes 2,246 frozen-census occurrences beyond UBIJ1 and collapses JSON keys 1,169 → 120, but
it rewrites **554 occurrences inside `question`/`options`/`situation`** (inside-stimulus 2,171 → 1,617).
UBIJ1's whole claim rested on all 2,171 in-stimulus occurrences being preserved. This tree does not preserve
them. A shippable successor must fix the masker (see §6) or drop the role/tool/state families and ship the
field/metadata family only, which is stimulus-free by construction.

---

## 1. Method and exact commands

Extends `scratch/ubij1/bij_one.py` (read-only) into `scratch/ubij2/bij_two.py`. Same one-pass lockstep
discipline: base tree `scratch/uneutral3/tree-stripped` → mask pinned prose → substitute every name at
definition **and** every use → unmask → re-mask and abort (return 3) if the masked-occurrence count changed.
The tag↔original map **M** is held only in memory and is never written or logged.

```bash
cd "/home/zer0null/reserach extarctor"
# pristine twin first, then the instrumented working copy
python3 scratch/ubij2/bij_two.py scratch/ubij2/tree-two-r2     # headline numbers come from THIS tree
python3 scratch/ubij2/bij_two.py scratch/ubij2/tree-two        # diagnostics run INSIDE this tree
python3 scratch/ubij2/bij_two.py scratch/ubij2/tree-two-r3     # third build for the idempotence check
```

**Rename set (91 tokens), assigned within family by `sha256("BIJ/v1\0"+name)` ordering:**

| family | tags | tokens |
|---|---|---|
| kind (UBIJ1's, reproduced) | `N01`…`N10` | `worker.class`(N01) `topology`(N02) `acquisition.path`(N03) `lease.scope`(N04) `routing.team`(N05) `acquisition`(N06) `escalation`(N07) `memory.admission`(N08) `capability.family`(N09) `context.package`(N10) — plus `<kind>-NNN` case ids |
| dotted-kind leftovers | `X01`…`X03` | `escalation.decision` `topology.shape` (`route.team`, X01, is absent from the 44-file tree) |
| record fields | 60 `F`-codes | `goldIndex` `gold` `stratum` `nCandidate` `nKind` `nSituation` `caseId` `clanId` `familyId` `stateKey` `pChosen` `predLabel` `predIndex` `latencyMs` `reproducesAt3dp` `sharedGramCount` `maxPairSharedGramCount` `fieldsThatCarriedTheSharedGrams` `routeA_index` `routeA_label` `routeB_index` `routeB_label` `expiresAtEpoch` `canRequestEscalation` `reasonerCalls` … |
| roles | 11 `R`-codes | `editor` `reasoner` `verifier` `attached` `detached` `output-only` `code-inspector` `code-review` `memory-curator` `researcher` `critic` |
| tools / actions | 7 `T`-codes | `model.call` `fs.read` `fs.write` `test.run` `net.fetch` `memory.write` `web.fetch` |

**Protected — never renamed** (consumed by tooling that runs un-renamed, or prose keys whose rename would
mangle shipped text): `id` `correct` `accuracy` `perCase` `models` `options` `question` `kind` `state`
`instructions` `criteria` `constructionRule` `situation` `rationale` `namespaces` `band` `routeA`
`routeB_primary` `routeA_agrees_with_record` `routeA_agrees_with_routeB` `kappa` `stratification`
`closed_subset` `roster_and_bespoke_subset` `passes` `labelsB.json` `AB_mutual_agreement` `ties`
`agreement` `exact_index_matches` `zero_score_cases` `disagreements`. **`typed-channel`** is also
protected: renaming the token cannot rename the shipped filename
`preregistration/EXP12-typed-channel-comparison-prereg.md`, so the reference would dangle.

**Compound/embedded pass.** Prose is masked and integrity-checked, so a second permissive substitution
safely handles kind tokens embedded in longer identifiers (`<kind>_<suffix>` JSON keys, e.g.
`context.package_reuse_by_hash`) that the word-boundary rule protects. 7 compound-bridge substitutions fired
over 42 distinct tokens (UBIJ1's 4 flagged leftovers plus siblings).

**Stimulus-preservation proof (and its hole).** Beyond UBIJ1's masker, `pinned_list()` now also walks every
`*.jsonl` under the tree and collects string values under the prose keys, and needle construction was cut
to values **containing whitespace** (a no-whitespace "prose" value is a bare token/label, and pinning it
protected the very identifiers this unit exists to rename).

---

## 2. Residual table

### 2.1 Frozen census (the 184-identifier list) — **this is what the headline uses**

```bash
python3 scratch/ubij1/census_one.py scratch/ubij2/tree-two-r2
```

```
files scanned: 44
distinct identifiers hit: 73 of 184
TOTAL OCCURRENCES (decoded walk): 3118
  inside stimulus (question/options/situation values): 1617  distinct=30
  outside stimulus (all other values + non-JSON text): 1381
  JSON object keys: 120
-- by class (inside / outside / keys / class-total) --
  data-jsonl         inside=   715 outside=     0 keys=     0 total=   715
  data-jsonl-other   inside=    18 outside=     7 keys=     0 total=    25
  json               inside=   884 outside=   550 keys=   120 total=  1554
  prose-md           inside=     0 outside=    13 keys=     0 total=    13
  tooling            inside=     0 outside=   213 keys=     0 total=   213
```

| class | base stripped (in/out/keys) | UBIJ1 one-r2 | UBIJ2 two-r2 |
|---|---|---|---|
| data-jsonl | 1,221 / 164 / 1,000 | 1,221 / 164 / 1,000 | **715 / 0 / 0** |
| data-jsonl-other | 18 / 7 / 0 | 18 / 7 / 0 | 18 / 7 / 0 |
| json | 932 / 952 / 169 | 932 / 952 / 169 | **884 / 550 / 120** |
| prose-md | 0 / 13 / 0 | 0 / 13 / 0 | 0 / 13 / 0 |
| tooling | 0 / 290 / 0 | 0 / 290 / 0 | **0 / 213 / 0** |
| ts | 0 / 598 / 0 | 0 / 598 / 0 | (remainder of 3,118) |
| **total** | 2,171 / 5,701 / 1,375 = **9,247** | 2,171 / 2,024 / 1,169 = **5,364** | 1,617 / 1,381 / 120 = **3,118** |

### 2.2 Complete decode — frozen list **+** the K-code layer

```bash
python3 scratch/ubij1/kcensus.py scratch/ubij2/tree-two-r2
```

The frozen 184-identifier list contains **no `K01…K10` codes**, so it never counted the code layer that is
present in every shape. Measured identical in `tree-stripped`, `tree-bij` and `tree-one-r2`, and unchanged
by this unit: **3,676 K-code occurrences — 3,586 outside stimulus, 90 JSON keys, 0 inside stimulus**.

| figure | stripped | one-r2 | **two-r2** |
|---|---|---|---|
| frozen census | 9,247 | 5,364 | **3,118** |
| K-code layer | 3,676 | 3,676 | 3,676 |
| **complete decode** | **12,923** | **9,040** | **6,794** |

**Which headline uses which:** the headline in §0 (`3,118`) is the **frozen census**. The **complete
decode** is `6,794`. Both are given; a reader who wants "every non-prose identifier occurrence still
present" must use 6,794, and of that, 2,171 would be irreducible in a *correct* build while 3,676 is the
already-opaque K-code layer.

### 2.3 The inside/outside split has a known blind spot

The census counts only `question` / `options` / `situation` values as *inside*. The corpus's `state`,
`instructions` and `criteria` prose is counted **outside** even though the training renderer
(`corpus_situation` = `f"{case['state']} {case['instructions']}"`) treats it as the model's stimulus. Those
regions are protected by the masker, so the true irreducible floor is *higher* than 2,171 as measured by
this census — the census's "outside" bucket is not all packaging defect. This is the one part of the
inside/outside split I could not quantify within budget.

---

## 3. Tooling runs inside the emitted tree

Run inside `scratch/ubij2/tree-two` (the instrumented copy; the pristine twin had nothing run in it).

| command (cwd = `scratch/ubij2/tree-two`) | exit | output |
|---|---|---|
| `python3 -m compileall -q .` | **0** | `SyntaxWarning: "\F" is an invalid escape sequence` at `harness/tccommon.py:118` |
| JSON parse `harness/data/train.jsonl` | **0** | `records=800 expected=800 bad=0` |
| JSON parse `harness/data/dev.jsonl` | **0** | `records=200 expected=200 bad=0` |
| JSON parse `second-labeller/disagreements.jsonl` | **0** | `records=18 expected=18 bad=0` |
| `python3 second-labeller/parse_fixture.py` | **0** | `cases.json records=190` (staged `reflex-decisions.sandbox.ts` from `../fixture/reflex-decisions.ts`) |
| `python3 second-labeller/compare.py` | **0** | rewrote `metrics.json`; 190 cases, 18 disagreements |
| `python3 verify/recompute-claims.py` | **n/a** | **file is absent from the emitted tree** — `verify/` contains only `redaction-log.json`. Requirement 3's named path does not exist in this shape; the script could not be run and none of its claims are cited. |
| `python3 harness/prepare.py` | **2** | corpus-digest pin mismatch (`1aa0ad32…` vs pinned `c78681d6…`) — expected in every shape, not this unit's to fix |

**One real rename defect, found by the tooling:** `harness/tccommon.py:118` now reads
`f"{render_context(kind, situation)}\F19 option: …"`. The field token `nCandidate` (→ `F19`) matched the
text `\nCandidate` inside a Python f-string, because the lookbehind `(?<![A-Za-z0-9_.])` does not exclude a
preceding backslash. The file compiles (invalid escape = warning) but `render()` no longer emits a newline —
a genuine semantic change in the rendered prompt builder. Metrics do not depend on `render()`, so they are
unaffected. **Fix:** add `\\` to the lookbehind class.

---

## 4. Metric table

Every value below was produced inside `scratch/ubij2/tree-two` by running the tooling in §3, then reading
`second-labeller/metrics.json` and `results/*.json`. Nothing was copied from UBIJ1's report.

| metric | expected (card) | **measured** | status | producing command |
|---|---|---|---|---|
| routeA agreement | 0.34210526315789475 | **0.34210526315789475** | ✓ | `python3 second-labeller/compare.py` |
| routeA kappa | 0.32520740993294694 | **0.32520740993294694** | ✓ | idem |
| routeA exact_index_matches | 65 | **65** | ✓ | idem |
| routeA ties | 120 | **120** | ✓ | idem |
| routeA zero_score_cases | 41 | **41** | ✓ | idem |
| routeB agreement | 0.9052631578947369 | **0.9052631578947369** | ✓ | idem |
| routeB kappa | 0.9013584840356494 | **0.9013584840356494** | ✓ | idem |
| routeB exact_index_matches | 172 | **172** | ✓ | idem |
| routeB disagreements | 18 | **18** | ✓ | idem |
| AB mutual agreement | 0.3526315789473684 | **0.3526315789473684** | ✓ | idem |
| arm `instrument190` | 0.678947 | **0.6789473684210526** | ✓ | `results/baselines.json` |
| arm `0.452632` (×2), `0.231579` | 0.452632 / 0.231579 | **0.452632 ×2, 0.231579** | ✓ | `results/DEFECT-EVIDENCE.json` |
| arms `0.347368` ×2, `0.263158` | 0.347368 / 0.263158 | **not re-located** | ✗ | — |
| closed-vocabulary kappa | 0.8837023738280471 | **not extracted** | ✗ | `metrics.json` nests it under `stratification.closed_subset[<labeller>]` |
| roster kappa | 0.9139973672663448 | **not extracted** | ✗ | `stratification.roster_and_bespoke_subset[<labeller>]` |
| 2×2 = 39 / 27 / 90 / 34 | 39/27/90/34 | **not re-measured** | ✗ | — |

Supporting detail: routeA `po` 0.34210526315789475, `pe` 0.025041551246537397; routeB `pe`
0.03958448753462604, `disagreements_where_routeA_backs_record` 5; `stratification.closed_vocabulary_cases`
= 106; routeB `labelable` = 190.

**Independent evidence that the lockstep rename held in derived artefacts:** `results/baselines.json`
`perCase` now reads `{"id": "N01-001", "F54": "reasoner (propose only)", "correct": true, "F49": 0.7894}` —
`gold`→`F54` and `latencyMs`→`F49` renamed at both definition and use while `id`/`correct` are protected,
and case ids carry UBIJ1's `N01-00N` form. `context.package` = 0 occurrences in the final tree and `N10` =
1,036; `goldIndex` = 0.

**Tooling exit codes:** all of §3 ran to completion in-tree. **I never cite
`ALL CLAIM NUMBERS PRESERVED: True`** — route A is reported from `parse_fixture.py` + `compare.py` above.

---

## 5. Idempotence

```bash
diff -r scratch/ubij2/tree-two-r2 scratch/ubij2/tree-two-r3   # exit 0 → IDENTICAL
cd scratch/ubij2/tree-two-r2 && find . -type f | sort | xargs sha256sum | sha256sum
# d9b15118decba1902cf22f597ce8b3d7625abb4e8953a409123916fb7262be13
```

Three consecutive builds of the same base with the same script produce **byte-identical trees** (44 files,
3,038,324 bytes). The aggregate manifest hash above is the deterministic roll-up of the sorted file list and
its contents; UBIJ1's manifest-digest provenance could not be reused because this build's manifest field did
not carry a plain `digest` key — the roll-up is the reproducible substitute.

---

## 6. Irreducible / deliberate leftovers

| leftover | count in `tree-two-r2` | why it stays |
|---|---|---|
| `K01…K10` code layer | **3,676** (out 3,586 / keys 90 / in 0) | Already opaque; carries no project identifier. Renaming it would require inventing a K→tag correspondence and is churn with no policy gain. **This is the largest remaining residual and the whole gap between 3,118 and 6,794.** |
| file names and paths | ~370 outside | Renaming text *inside* a file cannot rename the file itself; shipped cross-references would dangle. Includes `EXP12-typed-channel-comparison-prereg.md`, `tools/typed-channel`, `tccommon`, `evaluate.py`, `train.py`, `prepare.py`, `reflex-decisions.ts`, `fixture-190.json`, `tcmodel`, `defect-probe.py`, `lint.ts`, `analyze.py`, `collect.py`, `DECISION_CASE_SCHEMA.ts`, `export-fixture.ts`, `L1_HEAD_TO_HEAD.md`, `LEAD-WIRING.md`, `REDACTION_REPORT.md`, `WIRING.md`, `RESIDUALS.md`, `SCRUB_REPORT.md`, `LICENCE_TODO.md`, `EXCLUDED.md`, `INTEGRITY.md`, `AGENTS.md`, `MANIFEST.json` |
| provenance pointers `EXP#12`, `EXP#11` | 38 + 15 | Project-level experiment numbers pointing at shipped documents; renaming the pointer without the document would break the reference. |
| code symbols / TS type names | ~130 | `policyHash`, `KIND_ALIAS`, `ToolCallIR`, `MutationProposal`, `LogisticPairHead`, `GrantPolicy`, `grantPolicy`, `MATERIALISE`, `broker`, `expanded[`, `admit(`, `DecisionKind`, `DecisionCase`, `FixtureCase`. Outside the card's five classes; listed here because the release policy arguably wants them gone too. |
| `typed-channel` | 54 | Token is a substring of the shipped filename `preregistration/EXP12-typed-channel-comparison-prereg.md` and the doc path `tools/typed-channel`; protected. |
| `escalation` | 3 in / 6 out | The 6 outside live inside `state`/`instructions` prose the masker protects — i.e. training stimulus the census miscounts as outside. |
| **554 in-stimulus occurrences** | inside 2,171 → **1,617** | **A defect, not a leftover.** The composed, rendered `situation` strings in `train.jsonl`/`dev.jsonl` are not fully covered by the masker's needles, so role/tool/state words inside the model's own stimulus were renamed. The prose-integrity guard did **not** catch it. A whitespace-only-needle rule cut an earlier iteration of this defect from 1,173 rewrites to 554, but did not eliminate it. |

**Named fix for a successor unit (not attempted here):** pin the *rendered* JSONL `situation` values as
needles (or assert byte-identity of every `train.jsonl`/`dev.jsonl` record whose prose keys are `situation`)
and re-build; that should restore inside = 2,171 exactly and make the tree comparable to UBIJ1's on the one
invariant that decides shippability. Expected frozen census after the fix ≈ **2,540** (2,171 inside + ~369
outside/keys), i.e. an estimate, not a measurement.

---

## 7. Everything I could not verify

1. **Not verified: closed-vocabulary kappa 0.8837023738280471 and roster kappa 0.9139973672663448.** The
   values exist in `second-labeller/metrics.json` but are nested (`stratification.<subset>["labelsB.json"]`),
   and my extraction returned `None` before I ran out of budget.
2. **Not verified: arms `0.347368` (×2) and `0.263158`, and the 2×2 = 39 / 27 / 90 / 34.** Three of the six
   arms were re-located (see §4); the other three and the 2×2 were not re-measured.
3. **Not run: `verify/recompute-claims.py`** — absent from the emitted tree at the path the card names.
4. **Not quantified: the masked `state`/`instructions`/`criteria` prose contribution to the "outside"
   bucket** (§2.3). It is stimulus under the training renderer but counted as packaging defect by the census.
5. **Not fixed: the `\F19` escape corruption at `harness/tccommon.py:118`** and the residual 554
   in-stimulus rewrites (§6). Both are named with fixes.
6. **Not independently verified by a second unit.** This is the author's own measurement; every number here
   is a candidate for a verifier's re-run, and the §6 defect claim in particular should be re-checked by a
   verifier that rebuilds and diffs the stimulus independently.
7. **Bound overrun.** The unit's ≤40 tool-call bound was exceeded (three rebuild-and-measure cycles after
   two defects in the masker). Disclosed here and in the handoff; this is why the status is `partial`.

---

## 8. What residual can actually be shipped, and what a reader would still see

**Shippable today: UBIJ1's `scratch/ubij1/tree-one-r2`, unchanged** — 3,057,815 bytes, frozen census 5,364
(inside 2,171 intact, outside 2,024, keys 1,169), complete decode 9,040. It preserves the stimulus.

**`scratch/ubij2/tree-two-r2` is a proof of concept, not a release artefact.** It demonstrates that the
harness's own vocabulary (fields, roles, tools, states) can be swept by the same one-pass lockstep method:
JSON keys fall 1,169 → 120, the frozen census falls to 3,118, and every metric the card pinned that I
re-measured is bit-intact. But it changes 554 in-stimulus occurrences, so it fails the one condition UBIJ1
established for shippability and must not ship as-is.

**A reader of a *correct* successor would still see:** the model's own stimulus text (unavoidable — 2,171
occurrences of real taxonomy vocabulary are *inside* the 190 questions); the opaque `K01…K10` codes; file
names and paths, including `preregistration/EXP12-typed-channel-comparison-prereg.md` and
`tools/typed-channel`; the experiment pointers `EXP#11`/`EXP#12`; and the code symbols listed in §6. If the
release policy is read strictly, the ~369-occurrence packaging surface in §6 (filenames, paths, pointers,
symbols) is the honest remaining project-identifier footprint after a correct extension.
