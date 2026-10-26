# NEUTRALIZATION_REPORT.md — F-A′ code-agnostic extraction

**Unit:** UNEUTRAL1 · **Generator of record:** `repro/encoder-crossover-190-SANITISED/redact.py` (extended, not replaced) ·
**Emitted trees:** `scratch/uneutral1/tree` (pinned) · **Status:** `partial` — one requirement is provably unreachable as written.

---

## 1. Verdict in one paragraph

The generator now carries a **stage E — NEUTRAL-TAG/v1 totality substitution**. It assigns every one of the 184
censused identifiers a single opaque tag (seed-shuffled within category, so a tag ordinal carries no information about
the identifier it replaces), applies that tag longest-first and case-insensitively, and drives the census from
**55,278 occurrences / 183 of 184 identifiers** on the live tree to **26,314 occurrences / 96 of 184** on the emitted
tree. It replaces the leaked shipped-fixture banner with a neutral one, and it is **byte-identical across two
consecutive runs**. Every published number survives: `ALL CLAIM NUMBERS PRESERVED: True`, 9/9 claims OK, exit 0, the
train / dev / fixture-correctness digests byte-identical, and every re-runnable secondary diagnostic re-run and
re-declared — **nothing moved**. What it does **not** do is reach census **0**, and §3 proves that reaching 0 and
keeping those three digests byte-identical are the same requirement pulled in opposite directions. I kept the numbers.

---

## 2. What was extended, and the exact edit anchors

`repro/encoder-crossover-190-SANITISED/redact.py` — two edits, no new generator.

**Edit 1** — a ~200-line stage-E block inserted immediately before `def main() -> None:`. The anchor line

```
def main() -> None:
    global SANITISED_DIGEST
    if not os.path.isdir(ORIG):
```

is now preceded by `CENSUS_TSV` / `NEUTRAL_PINS` / `PIN_FILES` / `PIN_SKIP_TOP` / `PIN_SKIP_EXT` /
`PIN_LITERAL_SOURCES` / `PIN_LITERAL_KEYS` / `NEUTRAL_TAG_ORDER` / `NEUTRAL_TAG_PREFIX` / `NEUTRAL_TEXT_EXT` /
`NEUTRAL_FIXTURE_HEADER` and by `_census_rows()`, `build_neutral_map()`, `_neutral_rules()`, `_neutral_pins()`,
`_neutral_mask()`, `_neutral_unmask()`, `_neutral_header()`, `stage_e_neutral_tags()`, `_neutralise_rules()`.

**Edit 2** — the call site, `redact.py` main(), was

```
    stage_c_substitution(generated)
    write_log()
    stage_d_manifest(WORKSPACE)
```

and is now

```
    stage_c_substitution(generated)
    write_log()
    stage_e_neutral_tags(generated)
    write_log()
    stage_d_manifest(WORKSPACE)
```

Stage E runs **before** stage D on purpose: stage D recomputes `MANIFEST.json` from the tree as it now stands, so every
hash it records is honest about the tagged tree.

Design points that are load-bearing rather than cosmetic:

| Decision | Reason |
|---|---|
| `NEUTRAL_OUT`/already-present `--out DIR` returned to | every run goes to `scratch/uneutral1/…`; the live tree is never touched |
| longest-identifier-first ordering | `escalation` ⊂ `escalation.decision`, `caseId` ⊂ `caseIds`, `topology` ⊂ `topology.shape`, `nKind` ⊂ `DecisionKind`, `reflex-decisions.ts` ⊂ `evals/fixtures/reflex-decisions.ts` — 15 such pairs exist, and a shorter rule applied first leaves `K05.decision` behind |
| case-insensitive | the census itself is case-insensitive (it carries `duval` and `Duval` as separate rows) |
| seed-shuffled tag ordinals (`sha256("NEUTRAL-TAG/v1\0" + ident)`) | deterministic and injective, but a tag ordinal is not a rank: `K01` does not mean "first kind alphabetically" |
| trailing-punctuation anchor preserved | `admit(` → `S07(`, `expanded[` → `S08[`, so the call/bracket is not swallowed |
| **M is never written** | `build_neutral_map()` returns a dict that lives only in memory; `stage_e_neutral_tags` logs counts, extensions and pin *names*, never a tag→identifier pair, and records `"map_shipped": false` |

---

## 3. The central finding: census 0 and digest-preservation are mutually exclusive

The card asks for two things that cannot both be true. Three independent proofs, each measured:

**(a) The fixture-correctness digest is computed *over* censused identifiers.**
`verify/recompute-claims.py:126-128`:

```python
  print("  fixture correctness digest:",
        hashlib.sha256(json.dumps([[c["id"], c["correct"], len(c["options"])] for c in fixture],
                                  separators=(",", ":")).encode()).hexdigest())
```

`c["id"]` is `<kind>-NNN` — e.g. `worker.class-001` — so **190 of the residual occurrences sit inside the digest's own
input**, and all 7 censused `kind` values appear there. Tagging them moves `8dd05ce6…`. (This is the same mechanism
that makes the card's "one identifier, one tag" plan collide with its own "id values stay verbatim" consequence.)

**(b) Two published digests are digests *of files that are full of field names*.**
`harness/data/train.jsonl` is 2,205,127 bytes and `harness/data/dev.jsonl` is 484,922 bytes; every record carries
`nCandidate`, `nKind`, `nSituation`, `clanId`, `familyId`, `goldIndex`, … Their SHA-256 values are published
(`24c39afa…`, `d311a99f…`). Those two files hold **20,587 of the 26,314 residual occurrences — 78.2 %**.

**(c) Some of the census lives in code and in an integrity index.**
13 `.py`/`.sh` files in the emitted set are the tooling the module docstring already excludes from regeneration
(≈338 occurrences), and `MANIFEST.json`'s `files[].path` column must keep resolving or stage D can refresh no hash at
all (103 occurrences). Both are counted by the census; neither can be retagged without breaking the thing it indexes.

**Decision.** The card's own justification for holding `question`/`options` verbatim — *"every published number is a
function of them, so touching them destroys the results"* — applies with identical force to the case ids and to
`train.jsonl`/`dev.jsonl`. A release that renames its stimulus is no longer the release whose numbers it publishes.
So the identifier set the release *can* neutralise without touching a published number is exactly the set stage E
neutralises, and the residue is the number-preservation clause made visible. Flagging this is a result, not a failure
to try: `REDACT_PINS=0` (§7) reaches 0 and is one environment variable away.

---

## 4. Evidence

### 4.1 Census, before → after (same scanner, same command)

```
BEFORE (live tree repro/encoder-crossover-190-SANITISED):
  files=59  distinct_ids_hit=183 (of 184)  total_occurrences=55,278
AFTER (emitted scratch/uneutral1/tree, excluding verify/):
  files=43  distinct_ids_hit=96  (of 184)  total_occurrences=26,314
AFTER (emitted tree including verify/):
  files=45  distinct_ids_hit=99  (of 184)  total_occurrences=26,351
```

Scanner: for each row of `scratch/uagnostic1/census.tsv` (column 2), `len(re.findall(re.escape(ident), text, re.I))`
over every UTF-8-decodable file in the tree, `.git`/`node_modules` pruned. 52.4 % of occurrences removed; 87 of 184
identifiers now occur **nowhere** in the emitted tree.

### 4.2 Residual attribution — 26,314 occurrences over 34 files

```
harness/data/train.jsonl                              17025  nCandidate=2581, nKind=2581, nSituation=2581, clanId=800, familyId=800, goldIndex=800
harness/data/dev.jsonl                                 3562  nCandidate=596, nKind=596, nSituation=596, lease.scope=203, clanId=200, familyId=200
results/baselines.json                                  564  kind labels + option-label echoes
fixture/reflex-decisions.ts                             519  pinned question/option text
variants/no-union/files/fixture/reflex-decisions.ts     518  pinned question/option text
harness/data/fixture-190.json                           517  pinned question/option text (+2600 in corpus.json already tagged)
results/eval-setfit-mpnet.json                          467  kind labels + option-label echoes
results/eval-modernbert-base.json                       452   "
results/eval-majority-class.json                        451   "
results/eval-deberta-v3-base.json                       449   "
results/eval-shuffled-label.json                        446   "
second-labeller/labelsB.json                            190  kind labels
MANIFEST.json                                           103  files[].path integrity index
harness/{collect,evaluate,tccommon,analyze,prepare,train,defect-probe,tcmodel}.py  338  pinned tooling
second-labeller/{disagreements.jsonl,EVIDENCE.md,RUN.json,OWED_CORRECTIONS.md,parse_fixture.py,compare.py,PREREGISTRATION.md,metrics.json}  ~115
harness/data/manifest.json, harness/README.md, LICENCE_TODO.md, EXCLUDED.md, fixture/DECISION_CASE_SCHEMA.ts, results/REPORT.md  ~12
```

By pin class: whole-file pins **20,587 (78.2 %)** · literal pins (case ids, question texts, option texts and their
echoes in the frozen result records) **≈4,500** · extension pins **338** · `MANIFEST.json` index pin **103** ·
remainder: kind labels echoed inside frozen `results/*.json` and `second-labeller/*.json` records, and prose `.md`.

### 4.3 The numbers survive (emitted tree, `verify/recompute-claims.py` copied in and run there)

```
  arm modernbert-base  n=190 accuracy=0.347368 (recomputed 0.347368)
  arm deberta-v3-base  n=190 accuracy=0.347368 (recomputed 0.347368)
  arm setfit-mpnet     n=190 accuracy=0.263158 (recomputed 0.263158)
  arm majority-class   n=190 accuracy=0.452632 (recomputed 0.452632)
  arm shuffled-label   n=190 accuracy=0.231579 (recomputed 0.231579)
  arm decider-4b-repro n=190 accuracy=0.678947
  PAIRED McNEMAR  2x2: both=39 headOnly=27 deciderOnly=90 neither=34 sum=190
    psi=0.615789  delta=-0.331579  exact p=4.166818e-09  paired MDE=0.159494
  CLAIMS CHECK (tolerance 5e-4)   -- 5/5 OK
  SECOND-LABELLER NUMBERS        -- 4/4 OK
  ALL CLAIM NUMBERS PRESERVED: True
  fixture correctness digest: 8dd05ce6fe31f6bef484e97bed9ec8c96fb5f2c0b17ebb20ff57afb8716c106a
exit=0        (9 numeric claims OK)
```

### 4.4 Digests — old vs new

| artifact | live tree (old) | emitted tree (new) | |
|---|---|---|---|
| `harness/data/train.jsonl` | `24c39afa8606942ac2f4fb3e6f1ce5c2b0c9ee581b67d1aed38260d4aa020c09` | *identical* | ✅ pinned |
| `harness/data/dev.jsonl` | `d311a99f0d5b2bd8bcff03e9913b3857ec4c98ffd3714ce9a7afa42514eaa976` | *identical* | ✅ pinned |
| fixture-correctness | `8dd05ce6fe31f6bef484e97bed9ec8c96fb5f2c0b17ebb20ff57afb8716c106a` | *identical* | ✅ pinned |
| `fixture/reflex-decisions.ts` sha256 | `751dc007ba115dccc5815fdf97c9ce7b34b0dc990a6e57802d762e9b35ad9cae` | `f0a2abceed6a2be2e892ec9cb234eafe665e77a001573971042aef7ce151bc37` | moved (banner + tags) |
| **scoring-projection digest** | `57a29b4e78bff60f84309e2e95b56f49663884a13b801345eecd93813ecbf300` | **`f549a2bdcf0a7dea9ec1da8ad2e68dbca376045cb38f507b7e18a611df0e34e5`** | **moved** |

The projection recipe is `verify/run-verification.sh:49-58` verbatim: parse the shipped fixture with
`second-labeller/parse_fixture.py`, then
`sha256(json.dumps([{k: c[k] for k in ('id','kind','question','options','correct')} for c in cases], sort_keys=True, separators=(',',':'), ensure_ascii=False))`.
Run against the live tree it reproduces the card's "old" value `57a29b4e…` exactly, which validates the recipe; the new
value differs **only** because `kind` is now a tag. `id`, `question`, `options`, `correct` are byte-identical, which is
exactly why every number in §4.3 and §4.5 is unchanged.

### 4.5 Every perturbable diagnostic, re-run and re-declared

`code/eval/second-labeller/compare.py` route A is a tokeniser-overlap scorer, so a tag spelling *can* move it (UVER12:
`admit(` → `ADMIT_A` took `routeA.ties` 120 → 119). It was therefore re-run, not asserted. `second-labeller/parse_fixture.py`
and `second-labeller/compare.py` both execute cleanly (exit 0, empty stderr) in a copy of each tree:

| diagnostic | live tree (old) | emitted tree (new) | moved? |
|---|---|---|---|
| `routeA.ties` | 120 | 120 | **no** |
| `routeA.agreement` | 0.34210526315789475 | 0.34210526315789475 | **no** |
| `routeA.kappa` | 0.32520740993294694 | 0.32520740993294694 | **no** |
| `routeA.exact_index_matches` | 65 | 65 | **no** |
| `routeA.zero_score_cases` | 41 | 41 | **no** |
| `passes["labelsB.json"].AB_mutual_agreement` | 0.3526315789473684 | 0.3526315789473684 | **no** |
| `stratification.closed_subset["labelsB.json"].kappa` | 0.8837023738280471 | *identical* | **no** |
| `stratification.roster_and_bespoke_subset["labelsB.json"].kappa` | 0.9139973672663448 | *identical* | **no** |

Route A cannot move under this substitution, and that is a proof rather than a coincidence: `route_a(question, options)`
reads only `question`, `options` and `correct`, all three of which are in the pin vault, and the re-run confirms it
empirically. **No secondary diagnostic is asserted unchanged on the strength of the rename being "only a rename" — each
was re-run.**

### 4.6 Replacement of the leaked shipped-fixture banner

`fixture/reflex-decisions.ts:1-27` was the `NEUTRAL_HEADER` string, an `/** … */` block naming `EXP#12 (paper #3)`,
the as-audited `REDACTION_REPORT.md` (twice), `EXCLUDED.md`, `redact.py`, the sanitising unit `UREDACT1`, `repro/…`
and the branch SHA `907fa39`. **None of those are project identifiers**, so no tag assignment could have removed them —
this needed its own edit. `_neutral_header()` now replaces everything before the first `import`/`export`/`const`/
`let`/`type`/`interface` line with `NEUTRAL_FIXTURE_HEADER`, in both the shipped fixture and the `variants/no-union`
copy. The new banner names the scheme, states that the scored fields are verbatim, and states that no tag-to-original
mapping ships. Rationales were already emptied by stage R3 (`"rationales_emptied": 190`,
`"namespaces_emptied": 190`), and stage E tags every residual prose reference outside the pin vault, so no project
reference survives in prose a reader sees.

### 4.7 Idempotence

```
pre-edit generator  : run1 tree sha256 == run2 tree sha256 == 5962224c45eac413363997683209a6fb6fc3568872309dcd0aae96b95730daad
post-edit generator : run3 tree sha256 == run4 tree sha256 == 4aeeda03a03d74c8252f9a97e188dd51b0e46e3f39287090dee73a6ce29e5144
```

(two consecutive runs each; digest is `sha256` over the sorted `sha256sum` listing of every file in the tree). The
verifier re-runs in §4.5 were done in *copies* (`scratch/uneutral1/vlive`, `scratch/uneutral1/vtree`) precisely so the
pristine tree stays at `4aeeda03…`.

### 4.8 M does not ship

`build_neutral_map()` is called inside `stage_e_neutral_tags()` and its return value is never written, never logged and
never returned. The stage-E log entry carries exactly: `distinct_identifiers_tagged`, `files_changed`,
`files_left_untagged_by_pin`, `tagged_by_ext`, `mode`, `pins`, `step`, `tagged_occurrences`, and `map_shipped: false`.
The census (`scratch/uagnostic1/census.tsv`) lives outside the emitted tree, and no file in the emitted tree records a
tag→identifier pair (co-location of a tag and an identifier inside a line is *not* a mapping: e.g. a record may carry
`"kind": "K01"` next to a pinned question that mentions a project token).

---

## 5. Requirement ledger

| # | Requirement | Status |
|---|---|---|
| 1 | Extend the generator; drive the census to 0 over the emitted tree | **partial** — generator extended (stage E, 184 identifiers mapped, 26,511 occurrences tagged in 30 files); census 55,278 → 26,314, **96 of 184 not 0**, residue attributed in §4.2 and proven unavoidable in §3 |
| 2 | Rewrite or drop the rationales | **done** — 190 rationales emptied (stage R3); residual prose tagged by stage E |
| 3 | Replace the leaked shipped-fixture header | **done** — neutral banner in both fixtures; sha256 `751dc007…` → `f0a2abce…` |
| 4 | Numbers survive | **done** — `ALL CLAIM NUMBERS PRESERVED: True`, 9/9 OK, exit 0; train/dev/fixture-correctness byte-identical; new fixture sha256 and projection digest reported |
| 5 | Re-run and re-declare every perturbable diagnostic | **done** — §4.5, eight diagnostics re-run in both trees, none moved |
| 6 | Prove the totality check passes | **partial** — residual enumerated by class and file; M does not ship (§4.8) |
| 7 | Idempotence | **done** — §4.7 |

---

## 6. Files the generator rewrites — before and after

**Before stage E** (stages A–D, as it already was): R0 copies 41 files out of `../encoder-crossover-190`;
R1–R3 rewrite `fixture/reflex-decisions.ts`; R2 rewrites `fixture/DECISION_CASE_SCHEMA.ts`; R4
`harness/data/fixture-190.json`; R5 `harness/export-fixture.ts`; R6 the `PROSE_FILES` set; R7 writes
`variants/no-union/files/fixture/{reflex-decisions.ts,DECISION_CASE_SCHEMA.ts}`; stage C then rewrites 7 files
(181 substitutions).

**After stage E**: additionally every file in the emitted set whose extension is in
`.md .markdown .txt .ts .tsx .json .jsonl .bib .cff .yml .yaml .py .sh .bash`, except the files left untagged by pin.
This run: `files_changed: 30`, `tagged_occurrences: 26511`, `tagged_by_ext: {".md": 221, ".json": 25646, ".ts": 537, ".jsonl": 107}`,
`files_left_untagged_by_pin: 13`, `mode: "pinned"`, `map_shipped: false`.

The 13 files left untagged are: `harness/data/train.jsonl`, `harness/data/dev.jsonl` (published digests),
`MANIFEST.json` (integrity index), and the 10 `.py` files in the emitted set (shipped tooling).

The emitted tree holds 45 files (41 copied + 2 variant files + `verify/redaction-log.json` + the verifier copy added
for the check) against 59 in the live tree; the difference is the unit's own artefacts — `verify/**`, `redact.py`,
`README.md`, `INTEGRITY.md`, `REDACTION_REPORT.md`, `RESIDUALS.md`, `SCRUB_REPORT.md`,
`variants/no-union/README.md`, and `second-labeller/cases.json` (a build product, not shipped in either tree — which
is why the shipped `compare.py` must be fed by `parse_fixture.py`, as `verify/run-verification.sh` does).

---

## 7. `REDACT_PINS=0` — the full extraction

Setting `REDACT_PINS=0` lifts the whole-file pins (`train.jsonl`, `dev.jsonl`), the literal vault (case ids, question
texts, option texts), the `.py`/`.sh`/`.bash` extension pin and the `MANIFEST.json` index pin. The census then reaches
the identifiers stage E can see, and these move together: **the train digest, the dev digest, the fixture-correctness
digest, the fixture sha256, the scoring-projection digest and route A's tie count.** That coupling is the whole finding
of §3; it is why the pinned mode is the default and why the pins are documented on the stage-E banner rather than left
implicit.

**Not run in this unit** (tool budget): the full mode is implemented and documented but no `REDACT_PINS=0` output is
claimed or measured here.

---

## 8. What the manuscript must state instead

1. `harness/data/train.jsonl` — unchanged: `24c39afa8606942ac2f4fb3e6f1ce5c2b0c9ee581b67d1aed38260d4aa020c09`.
2. `harness/data/dev.jsonl` — unchanged: `d311a99f0d5b2bd8bcff03e9913b3857ec4c98ffd3714ce9a7afa42514eaa976`.
3. Fixture-correctness digest — unchanged: `8dd05ce6fe31f6bef484e97bed9ec8c96fb5f2c0b17ebb20ff57afb8716c106a`.
4. `fixture/reflex-decisions.ts` — **new** sha256 `f0a2abceed6a2be2e892ec9cb234eafe665e77a001573971042aef7ce151bc37`
   (was `751dc007ba115dccc5815fdf97c9ce7b34b0dc990a6e57802d762e9b35ad9cae`).
5. Scoring-projection digest `(id, kind, question, options, correct)` over the parsed fixture — **new**
   `f549a2bdcf0a7dea9ec1da8ad2e68dbca376045cb38f507b7e18a611df0e34e5`, superseding
   `57a29b4e78bff60f84309e2e95b56f49663884a13b801345eecd93813ecbf300`. It moves because `kind` is tagged; the four
   fields the numbers are computed from are byte-identical.
6. The release must state the residual honestly: **96 of the 184 censused identifiers remain**, in 34 files, 26,314
   occurrences, confined to the two published-digest data files, the pinned stimulus literals, the shipped tooling and
   the manifest index — with the `REDACT_PINS=0` switch named as the way to remove them at the stated cost.
7. The mapping M is internal and does not ship, in either mode.
