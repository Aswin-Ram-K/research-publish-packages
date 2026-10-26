# OUTSIDE_TOKEN_REDACTION — UOUTSIDE1

**Date:** 2026-10-16 · **Unit:** UOUTSIDE1 · **Source tree:** `scratch/utool1/tree-six` (45 files)
**Emitted tree:** `scratch/uoutside1/tree-seven` · **Rebuild tree (idempotence):** `scratch/uoutside1/tree-seven-b`
**Report of record under reconciliation:** `strategy/GATE_VOCABULARY_ANALYSIS.md` (lines 99–104 hold the
c-outside 27; lines 225–228 hold the counted subset)

Scope: the outside-stimulus residue of the release build's exclusion gate. The 10 mechanism tokens that live
inside the model's `question`/`options` stimulus are **not** touched (open author decision, reported in §6).

---

## 1. Reconciliation of the report's c-outside 27 (against tree-seven)

The report's list (verbatim, `strategy/GATE_VOCABULARY_ANALYSIS.md:99-104`) is:
`tccommon, tcmodel, pchosen, nCandidate, nKind, nSituation, nkind, sharedGramCount,
maxPairSharedGramCount, orderPermutationFlips, reproducesAt3dp, latencyMs, latencyMs.mean,
LogisticPairHead, tm.LogisticPairHead, LogisticPairHead.case_logits,
tm.LogisticPairHead.pair_features, tccommon.render, tccommon.fit_temperature,
DECIDER_STACK_DECISION.md, LEARNINGS.md, CITATION.cff, tcmodel.py, tccommon.py,
harness/tccommon.py, evals/fixtures/reflex-decisions.ts, .orderPermutationFlips`.

| present in this 45-file tree | absent from this tree |
|---|---|
| `tccommon`, `harness/tccommon.py`, `tccommon.render`, `tcmodel`, `tcmodel.py`, `pchosen`, `LogisticPairHead`, `tm.LogisticPairHead`, `LogisticPairHead.case_logits`, `tm.LogisticPairHead.pair_features`, `nCandidate`, `nKind`, `nSituation`, `nkind`, `LEARNINGS.md`, `evals/fixtures/reflex-decisions.ts` | `sharedGramCount`, `maxPairSharedGramCount`, `orderPermutationFlips`, `.orderPermutationFlips`, `reproducesAt3dp`, `latencyMs`, `latencyMs.mean`, `tccommon.fit_temperature`, `DECIDER_STACK_DECISION.md`, `CITATION.cff`, `tccommon.py` |

### 1a. Tokens the report WRONGLY included — not mechanism tokens

- **`nCandidate`, `nKind`, `nSituation`, `nkind`** are tokeniser artefacts of `\n` + English, not identifiers:
  `harness/prepare.py:148` builds `tc.TASK_PREFIX + "\nKind: {kind}\nSituation: {situation}\nCandidate option: {option}"`,
  `harness/tccommon.py:118` returns `f"{render_context(kind, situation)}\nCandidate option: …"`, and
  `harness/prepare.py:177` prints `f"\nkind counts (train/dev/fixture):"`. The source bytes are `\nKind`, `\nSituation`,
  `\nCandidate`, `\nkind`. **Redacting these would rewrite the model's stimulus template** — i.e. it would do
  precisely what the card forbids. Left un-redacted, deliberately.
- **`LEARNINGS`** is one generic English word inside prose: `second-labeller/OWED_CORRECTIONS.md:94` reads
  “…do NOT accuse LEARNINGS of an error it did not make…”. No mechanism. Left.
- `tccommon.py` (as opposed to `harness/tccommon.py`) and the `latencyMs.*`/`sharedGramCount` family do not occur
  in this 45-file tree at all; the report counted them in a larger tree.

### 1b. Tokens the report MISSED (present outside the stimulus, mechanism-bearing, gate-invisible)

The report counted only **gate-visible** tokens. A fresh census (`scratch/ubij1/census_one.py`, cross-checked by
my own `scratch/uoutside1/outside_scan.py`, both on tree-seven) finds **1,094 outside-stimulus occurrences of 70
distinct** withheld-mechanism identifiers — not 88/27 — because:

- many mechanism identifiers are **gate-invisible** (their components are English words, so the gate's
  word-vocabulary accepts them): `typed-channel` (54 outside), `tools/typed-channel` (42), `EXP#12` (38),
  `EXP#11` (15), `code-inspector` (14), `MATERIALISE` (12), `broker` (11), `memory.write` (10),
  `memory-curator` (8), `output-only` (24), `code-review` (4), `critic` (4), `researcher` (4), `web.fetch` (4),
  `test.run` (14), `model.call` (128), plus `KIND_ALIAS` (8) and `expanded[` (9).
- the report's own **stimulus ten also occur outside the stimulus**: `fs.write` (54 outside), `fs.read` (48),
  `policyHash` (9), `expiresAtEpoch` (6), `reasonerCalls` (4), `MutationProposal` (4), `ToolCallIR` (4),
  `canRequestEscalation` (4). The report's binary in-stimulus/out-of-stimulus split assigns a token to one bucket,
  so these outside occurrences were never counted in the 88.
- several of the report's "outside" entries are **filename citations**, not tokens (`evaluate.py` 12, `train.py`
  10, `prepare.py` 9, `fixture-190.json` 9, `analyze.py` 8, `INTEGRITY.md` 8, `lint.ts` 6, `collect.py` 5, …).

**This is reported, not acted on**: the card scopes UOUTSIDE1 to the gate-flagged residue. The gate-invisible
mechanism residue is a larger, separate problem for the author.

---

## 2. What was redacted

NEUTRAL-TAG/v1, house style copied from `scratch/udtag1/dtag_one.py`: stable neutral tags, seed
`sha256("NEUTRAL-TAG/v1\0"+ident)`, **map in memory only — never written, logged or shipped**. Tag family
`TAG_NN` (`TAG_01`, `TAG_02`) because `TAG_[0-9][0-9]` is accepted by **both** gate copies
(`orchestration/units/UBUILD1.build.sh:907` `TAG_RE = ^(?:K|F|S|C|R|D|N|P)[0-9][0-9]$ | ^TAG_[0-9][0-9]$`;
`scratch/ugate1/gate_scoped.sh:65` adds `N`). **Corrected by UFIXPKG8:** at the time of this pass the class was
`K|F|S|C|R|D|N`, so the family `P01..P05` used by UDTAG1 was **not** accepted by the build gate's `TAG_RE`;
UFIXPKG8 added `P` to the class at `orchestration/units/UBUILD1.build.sh:907`. The emitted copy
`tools/package/gate.sh:110` still carries the old class and is outside UFIXPKG8's write paths. No `TAG_\d\d`
token existed in the tree before this pass.

**2 identifiers redacted, 13 occurrences, 4 files** (whole-word, `[A-Za-z0-9]` boundaries so adjacent `_`/`.` are
kept): `LogisticPairHead` (6: `harness/defect-probe.py` 3, `harness/evaluate.py` 1, `harness/tcmodel.py` 1,
`harness/train.py` 1) and `pchosen` (7, all `harness/evaluate.py`: lines 339, 342, 357, 358, 359, 360, 361).
No path changed; no filename was renamed.

Deliberately **not** redacted, same family: `meanPChosen` — a capital-P metrics key (`harness/evaluate.py:361`),
once, in the emitted results schema; it is not the report's token and renaming it would move a shipped results
JSON key.

### 2a. Filename tokens STOPPED (rename would require editing shipped tooling)

Per the card's rule, a rename that would require editing shipped tooling is stopped and reported. These three
tokens are left un-redacted for that reason — **not** because they are hard to rename (the house precedent in
`scratch/ubij1/bij_one.py` *does* rename `.py` files together with their uses, so the author may overrule):

| token | what a rename would have to rewire |
|---|---|
| `tccommon` / `harness/tccommon.py` | imported as `import tccommon as tc` by `harness/{evaluate,collect,defect-probe,train,analyze,prepare}.py`; also the substrings `tccommon.render` (cited in `harness/prepare.py:15,147` and `harness/tcmodel.py:22`, `harness/README.md`) and `tccommon.fit_temperature` |
| `tcmodel` / `harness/tcmodel.py` | imported as `import tcmodel as tm` by `harness/{evaluate,defect-probe,train}.py`; cited in `harness/README.md:54`, `EXCLUDED.md`, `LICENCE_TODO.md`, `MANIFEST.json` |
| `evals/fixtures/reflex-decisions.ts` (and the `reflex-decisions` stem) | the shipped fixture, read by `second-labeller/parse_fixture.py` (`SRC = … "fixture", "reflex-decisions.ts"`), cited by `MANIFEST.json` (5), `verify/redaction-log.json` (2), `harness/collect.py` (2), `harness/evaluate.py` (1), `second-labeller/parse_fixture.py` (3); the variant copy `variants/no-union/files/fixture/reflex-decisions.ts` shadows it |

Renaming any of these means editing the harness that produced the published numbers and the second-labeller
tooling that a verifier re-runs — i.e. exactly the failure the card names. **Open author decision.**

---

## 3. Invariants

### 3a. No published claim number moves
`python3 verify/recompute-claims.py` inside `scratch/uoutside1/tree-seven` — exit 0, literal output:

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

New digest of the emitted tree is recorded in §4; the fixture correctness digest above is **unchanged**
(`c7696edc…`, same as tree-six), because every `.json`/`.jsonl`/`.ts`/`.md` file is byte-identical to tree-six
and only four `.py` files changed.

### 3b. Re-run battery inside the emitted tree

| command | exit | value |
|---|---|---|
| `python3 -m compileall -q .` | 0 | — |
| `python3 verify/recompute-claims.py` | 0 | see §3a |
| `harness/data/train.jsonl` parse | — | records=800 expected=800 malformed=0 |
| `harness/data/dev.jsonl` parse | — | records=200 expected=200 malformed=0 |
| `second-labeller/disagreements.jsonl` parse | — | records=18 expected=18 malformed=0 |
| `MANIFEST.json`, `harness/data/manifest.json`, `second-labeller/metrics.json`, `second-labeller/labelsB.json`, `results/DEFECT-EVIDENCE.json` | — | all parse OK |
| `python3 second-labeller/parse_fixture.py` | 0 | records_found=190 cases_parsed=190 parse_failures=[] options_total=721, arity {2:33,3:27,4:76,5:54}, distinct_labels=74, single_option_cases=[], duplicate_ids=[], answer_outside_option_set=[], bad_option_arity=[] |
| `python3 second-labeller/compare.py` | 0 | route A: agreement=0.34210526315789475 po=0.34210526315789475 pe=0.025041551246537397 **kappa=0.32520740993294694 exact_index_matches=65 ties=120 zero_score_cases=41**; route B (`labelsB.json`, routeB-blind-model): labelable=190 agreement=0.9052631578947369 po=0.9052631578947369 pe=0.03958448753462604 **kappa=0.9013584840356494 exact_index_matches=172 n_disagreements=18 AB_mutual_agreement=0.3526315789473684 disagreements_where_routeA_backs_record=5**; disagreements_count_routeB=18, kinds {K07:6, K03:4, K05:3, K02:2, N10:2, K04:1}; closed-vocabulary subset n=106 routeA kappa=0.21106870229007632 / routeB **kappa=0.8837023738280471** exact=95; roster+bespoke subset n=84 routeA kappa=0.4284887087434858 exact=37 / routeB **kappa=0.9139973672663448** exact=77; per-kind route B kappa K01=1.0 K02=0.9225806451612903 K03=0.8048780487804877 K04=0.938375350140056 K05=0.8717105263157895 K07=0.7152542372881355 N10=0.9261213720316623 |

**Before/after control.** The same two tools were run in `scratch/uoutside1/probe-before` (a copy of the
**unredacted** tree-six): exit 0 and 0, and both `metrics.json` and `disagreements.jsonl` are **byte-identical**
to the tree-seven run — the redaction moves no second-labeller output.

**Pre-existing discrepancy, reported not fixed.** In `scratch/uoutside1/tree-seven` the shipped
`second-labeller/metrics.json` and `disagreements.jsonl` are **not** the current tools' output: the shipped
metrics carry hand-added `limitation`/`_correction` keys (UFIX4 / UVER3 C2) that `compare.py` does not emit, and
the shipped `disagreements.jsonl` uses feature keys `F14,F31,F33,F55` where the current `compare.py` emits
`F22,F40,F56,F30`. This predates UOUTSIDE1 (probe-before shows the same delta) and is a property of the frozen
shipped artefacts versus the UTOOL1-renamed harness. Flagged for the author.

### 3c. Census: inside-stimulus occurrence and distinct-key counts

| | before (tree-six / tree-seven pre-edit) | after (tree-seven) | delta |
|---|---|---|---|
| inside-stimulus occurrences (`question`/`options`/`situation` values) | **2171** | **2171** | **0** |
| inside-stimulus distinct identifiers | **30** | **30** | **0** |
| outside-stimulus occurrences | 1107 | 1094 | −13 |
| outside-stimulus distinct identifiers | 71 | 70 | −1 |

The delta is 0; the build refuses to emit if it is not. Residual word-bounded occurrences of the two redacted
identifiers in the whole emitted tree: **0**. Stronger than the census: every `.json`/`.jsonl` file in tree-seven
parses to an object **exactly equal** to its tree-six counterpart (asserted per file during the build), so the
stimulus bytes are provably unmoved.

---

## 4. Manifest regenerated from disk, and proved

Regenerated with `scratch/uoutside1/regen_manifest.py` (a copy of `scratch/udtag1/regen_manifest.py` retargeted
at `scratch/uoutside1/<tree>`; procedure unchanged): `sha256 changed vs previous manifest: 4 of 44`,
`dropped: []`, `added: []`, `counts.files=45`, `counts.bytes_total=3009245`.

Proved by an **independently written** checker (`scratch/uoutside1/check_seven.py`, its own walk + streaming
hash, not the regen code), exit 0:

```
  files[] entries                            44
  files on disk (incl MANIFEST.json)         45
  missing (listed but on-disk absent)        0
  hash mismatch                              0
  size mismatch                              0
  unlisted (on disk but not listed)          0
  listed-but-absent                          0
  files[] count == disk-1                    True
  counts.files == 45                         45
  counts.files matches disk                  True
  counts.bytes_total == 3009245              3009245
  counts.bytes_total matches disk            True
  MANIFEST.json lines=443 bytes=22709 sha256=fecd31574bad62cef328d7d95b851ac338aad552c420d1b08a1126cb48cd97ef
CHECKER: PASS
```

## 5. Idempotence

Built twice (`build_seven.py tree-seven`, `build_seven.py tree-seven-b`), manifest regenerated in each.
Build digest (sha256 of the sorted `sha256  relpath` list, pre-manifest-regen) **identical**:
`63d015b152c931e98f6855a6bd262617147047453058031200b0697f77152ef6`.
File sets identical (45 each); the only byte-differing file is `MANIFEST.json`, and inside it the only differing
key is `generated_utc` (`2026-10-16T03:19:13Z` vs `2026-10-16T03:19:47Z`, written by
`regen_manifest.py:110`). All 44 non-manifest files are byte-identical — **idempotent up to the manifest
timestamp**.

## 6. Open author decisions (reported, not acted on)

1. **The 10 in-stimulus tokens** — `fs.read`, `fs.write`, `policyHash`, `expiresAtEpoch`, `reasonerCalls`,
   `MutationProposal`, `ToolCallIR`, `ToolCallIR.`, `role.canRequestEscalation`, `canRequestEscalation`
   (316 occurrences inside the model's `question`/`options`). Untouched. Note from §1b that eight of these also
   have outside-stimulus occurrences (237 in total), which the report's binary split did not count.
2. **Manifest `source`/`source_sha256` exposure** — all 44 `files[]` entries carry a `source` path and 40 a
   `source_sha256` of a file (under `repro/encoder-crossover-190-SANITISED`) that does not ship. Regeneration
   preserves this exposure unchanged, neither adding nor removing it.
3. **The stopped filename tokens** (§2a) — `tccommon`/`harness/tccommon.py`, `tcmodel`/`harness/tcmodel.py`,
   `evals/fixtures/reflex-decisions.ts`. A rename is mechanically easy (house precedent) but rewires the shipped
   harness and the second-labeller tooling; author to decide.
4. **Gate-invisible mechanism residue** (§1b): 1,094 outside occurrences of 70 identifiers that the exclusion gate
   cannot see because their components are English words.

## 7. Write paths

`scratch/uoutside1/**` (tree-seven, tree-seven-b, probe-before, run-after, `build_seven.py`,
`regen_manifest.py`, `check_seven.py`, `outside_scan.py`), this report,
`orchestration/units/UOUTSIDE1.md`, `orchestration/handoffs/UOUTSIDE1.json`. Nothing else was written;
no tree other than `scratch/uoutside1/**` was touched.
