# GATE_VOCABULARY_ANALYSIS.md — what the build's exclusion gate is really measuring

**Unit:** UGATE1 · **Date:** 2026-10-16 · **Subject:** the positive-vocabulary gate written into
`$DEST/gate.sh` by `orchestration/units/UBUILD1.build.sh`, and the promoted (re-tagged) input tree.

**Verdict in one line:** the gate's `29,936` is **1,464 distinct tokens**, not 29,936 leaks — `19,576`
of those occurrences are the released data's own schema keys (`fama0015`, `famr0036`, …) being measured
against an English word list. A scoped gate that stops doing that still fails on the honest tree with
**6,093 occurrences / 1,253 distinct tokens**, and **404 of those occurrences (37 distinct tokens) are
genuinely the withheld mechanism**. That residual is the author's call, not a defect to be papered over.

---

## 1. Where the gate is and what it does

`orchestration/units/UBUILD1.build.sh` (1,066 lines, sha256 `45fe28e4…7ad3`) writes `$DEST/gate.sh`
from a heredoc and then runs it as its **last** step; the build fails with
`GATE RESULT: FAIL -- 29936 out-of-vocabulary token(s).` on the promoted path and `95,606` on the
frozen path. The gate is a **positive** checker: a token passes only if it is

1. a declared placeholder/tag (`K\d\d`, `TAG_\d\d`, …), **or**
2. a declared public identifier (`vocabulary/public.txt`), **or**
3. a word of `vocabulary/english.txt` · `vocabulary/code.txt` (lowercased, and after splitting
   camelCase and `[^A-Za-z0-9]` runs), **or**
4. a bare hex run of ≥8 chars.

Anything else fails. It reads **every file in the tree**, of every extension. Its `400`-line offender
listing is capped, so a leak late in the alphabetical walk is **counted but never named** — a real
defect in the current gate (see §4).

It replaced a 24-pattern denylist for a good reason: a denylist only sees strings someone already
thought of, and a positive checker fails closed. **That property is worth keeping and this analysis
keeps it.**

## 2. Deliverable 1 — the distinct OOV tokens on the promoted path

Full table (1,464 rows: token, occurrences, class, file classes) is
`scratch/ugate1/oov_tokens.tsv`; the classified variant is
`scratch/ugate1/oov_tokens_classified.tsv`. Reproduce with
`bash orchestration/units/UBUILD1.build.sh` into `scratch/ugate1/emit/` then
`python3 scratch/ugate1/enumerate_oov.py scratch/ugate1/emit/research-publish-packages`.

**29,936 occurrences = 1,464 distinct tokens.** By file class:

| file class | occurrences |
|---|---|
| data `.json` | 18,890 |
| data `.jsonl` | 8,236 |
| prose `.md` | 2,048 |
| Python `.py` | 1,684 |
| TypeScript `.ts` | 533 |
| `.bib` | 471 |
| licence instruments | 22 |
| `.txt` / no-extension | 12 |
| shell | 0 |

Head of the distribution (all 15 top rows are the same story — released schema keys):

```
  fs                                  322   b-thirdparty
  fs.read                             150   c-mechanism-stimulus
  famr0036                            141   a-schema
  fs.write                            140   c-mechanism-stimulus
  famr0046                            139   a-schema
  famr0042                            138   a-schema
  famr0043                            138   a-schema
  famr0047                            137   a-schema
  famr0041                            136   a-schema
  famr0045                            136   a-schema
  famr0037                            135   a-schema
  famr0038                            135   a-schema
  famr0040                            134   a-schema
  famr0000                            132   a-schema
  famr0044                            132   a-schema
```

**Sanity check against the workspace's own census:** `strategy/COHERENT_BIJECTION_EXTENSION_2.md`
finds **3,348** residual occurrences (184 identifiers) in this tree. The gate reports **29,936** —
**8.9× the census**. The gate is not measuring leaks; it is measuring *tokens absent from a hand-written
English word list*.

## 3. Deliverable 2 — every distinct token classified, with counts

| class | distinct | occurrences |
|---|---|---|
| **(a) released data's own schema** — record keys, `kind` values, label names (`fam*`, `ex1*`, `N\d\d-\d\d\d`) | **268** | **19,576** |
| **(b) third-party / incidental** — public library and model names (`GLiNER`, `RoBERTa`, `GLiClass`, `McNemar`), `arXiv`, `LLM`, `ECE`, `MDE`, `kappa`, `acc`, `fs`, `const`, `pre-registered`, `decider-4b`, `imajev-4b`, `clanu01..08`, `workspace` | **1,156** | **9,924** |
| **(c) mechanism vocabulary, split:** | 37 | 420 |
| — (c-stimulus) tokens that occur inside the model's own stimulus | 10 | 332 |
| — (c-outside) mechanism tokens elsewhere in prose/source | 27 | 88 |
| **(d) encoding / tokenisation artifacts** — hex, escapes, odd numeric runs | 3 | 16 |

Class (c) in full — the stimulus ten first:

```
  fs.read (150)  fs.write (140)  policyHash (3)  expiresAtEpoch (6)  reasonerCalls (4)
  MutationProposal (4)  ToolCallIR (3)  ToolCallIR. (2)  role.canRequestEscalation (2)
  canRequestEscalation (2)
  c-outside: tccommon, tcmodel, pchosen, nCandidate, nKind, nSituation, nkind, sharedGramCount,
  maxPairSharedGramCount, orderPermutationFlips, reproducesAt3dp, latencyMs, latencyMs.mean,
  LogisticPairHead, tm.LogisticPairHead, LogisticPairHead.case_logits,
  tm.LogisticPairHead.pair_features, tccommon.render, tccommon.fit_temperature,
  DECIDER_STACK_DECISION.md, LEARNINGS.md, CITATION.cff, tcmodel.py, tccommon.py,
  harness/tccommon.py, evals/fixtures/reflex-decisions.ts, .orderPermutationFlips
```

**A finding that matters more than the count:** the gate is a *positive* checker, so a mechanism token
that is also an ordinary English word is **invisible** to it. Of the 30 identifiers that occur inside
the model's stimulus, **11 are already declared vocabulary and can never be flagged**:

```
editor  reasoner  attached  verifier  detached  topology  MATERIALISE
broker  researcher  critic  escalation
```

Only **19 of the 30** are visible to the gate. The census's "irreducible floor, 2,171 occurrences" is
therefore *not* a floor the gate can see: the gate sees **332** of those occurrences.

## 4. Deliverable 3 — the correct gate, and where it is implemented

**Implemented at `scratch/ugate1/gate_scoped.sh`** (a standalone copy). Nothing was written into
`scratch/ubij3/tree-three-r2/`, into the emitted release tree, or into `UBUILD1.build.sh`.

Design:

* **Prose and source** — the current rule, unchanged: every token must be declared. A mechanism token
  in prose or code still fails. This is the property that makes the current gate good.
* **Data files (`.json`, `.jsonl`)** — validated against the released format's **declared** vocabulary
  (`vocabulary/data.txt`, generated by `scratch/ugate1/make_data_vocab.py`), *in addition to*
  english/code/public: the record keys actually used by the shipped data (740 keys), the single-token
  `kind`/enum values, and the released id grammars. A data file no longer fails for using its own
  schema.
* **Two defects of the current gate fixed:** the `400`-line offender cap is removed (a leak anywhere in
  the walk is now named, file and line), and the checker no longer scans its own `vocabulary/`
  inputs (the current gate reports 117 phantom offenders inside `vocabulary/data.txt`).

`make_data_vocab.py` has two modes and only one is defensible:

| mode | declared | scoped result | verdict |
|---|---|---|---|
| `keys` | record **keys** only (740) + enum values | **6,093** | **used** |
| `full` | keys **+ all single-token values** (1,612) | 5,488 | **rejected** |

`full` mode declares **8 of the 15 mechanism names** as vocabulary. That is exactly the failure the
card warns about: *a mechanism name declared as vocabulary ships the leak as vocabulary.* `full` is
recorded only to show what that shortcut buys (605 occurrences) and why it must not be taken.

### Where this gate is MORE PERMISSIVE than the current one — stated plainly

* **Data files**: strictly more permissive (they may use their declared schema). Justified by a leak I
  can name: without it, `fama0015` — the *name of a released record* — is indistinguishable from a leak,
  and 19,576 schema occurrences drown the 404 real ones. The gate still flags every free-text mechanism
  name **inside** a data value; `full` mode is the version that would not, and it is rejected.
* **Prose/source**: more permissive in exactly one way — the released **id grammars**
  (`^fam[abr]\d{3,6}$`, `^ex1[12][ab]\d{3,6}$`, `^[A-Za-z]\d{2,4}-\d{3}$`, `^[NKFS][A-Z]?\d{2,4}$`) and
  the `N` tag family. Justified: every one of these grammars requires digits, so **no mechanism word can
  match them**. `grantPolicy`, `tccommon`, `pchosen`, `fs.read` — none has that shape.
* Everything else in prose/source is byte-for-byte the current rule.

## 5. Deliverable 4 — red → green, on a copy

Tree under test: `scratch/ugate1/candidate-keys/research-publish-packages` (built by running
`UBUILD1.build.sh` to `DEST=scratch/ugate1/emit/research-publish-packages`, then copying — the real
destination was never used). Probe operated on `scratch/ugate1/redtest/`, a `cp -a` of it.

```
### A. HONEST (unchanged candidate tree)
flagged tokens: 6093
GATE RESULT: FAIL -- 6093 out-of-vocabulary token(s).
listed=6093                     # the complete listing: every offender named, none capped

### B. RED (grantPolicy appended at
###        .../code/harness/README.md:89 -- a prose file, in the COPY only)
flagged tokens: 6095
434:packages/exp12-encoder-crossover/code/harness/README.md:89: grantPolicy  [identifier-shaped, not a declared public identifier]
GATE RESULT: FAIL -- 6095 out-of-vocabulary token(s).

### C. GREEN (probe line removed)
flagged tokens: 6093
GATE RESULT: FAIL -- 6093 out-of-vocabulary token(s).

### D. exact restore check
diff -r candidate-keys/research-publish-packages redtest  ->  IDENTICAL to candidate-keys
```

The red case is: **a known withheld mechanism name injected into a prose file of a copy**. The gate
names the file and the line. Removing it restores the honest result exactly, and the copy is byte-
identical to the candidate afterwards.

**The honest result is 6,093, and it is non-zero.** Per the card, that residual is a finding, reported
and classified here rather than widened away.

### The residual, classified (6,093 occurrences / 1,253 distinct)

| class | occurrences | where |
|---|---|---|
| (b) third-party / incidental | 5,145 | prose 1,830 · Python 1,438 · data 961 · `.bib` 470 · TypeScript 413 · licence 22 · other 11 |
| (a) schema-shaped words **in prose/source** | 528 | Python 213 · prose 148 · `.txt` 109 · TypeScript 58 |
| (c-stimulus) mechanism inside the stimulus | 316 | `.jsonl` 178 · `.json` 75 · TypeScript 62 · `.txt` 1 |
| (c-outside) mechanism in prose/source | 88 | prose 55 · Python 33 |
| (d) artifacts | 16 | prose 15 · `.bib` 1 |

`4,879` occurrences live in **prose/source**; `1,214` in data. The dominant term is **(b)**: a good
package still fails this gate because `arXiv`, `GLiNER`, `RoBERTa`, `McNemar`, `ECE`, `MDE`, `kappa`,
`LLM`, `const`, `fs`, `pre-registered` are not in a 75k-word English list. **That is a lexicon-coverage
fact, not a leak count**, and it is the reason `29,936` could never have been driven to zero by
redaction.

## 6. Deliverable 5 — what the author must authorise

The scoped gate still flags **404 occurrences / 37 distinct tokens** that are genuinely the withheld
mechanism. They split into two very different asks:

1. **316 occurrences / 10 distinct — mechanism inside the released stimulus.**
   `fs.read` (150) · `fs.write` (140) · `expiresAtEpoch` (6) · `reasonerCalls` (4) ·
   `MutationProposal` (4) · `policyHash` (3) · `ToolCallIR` (3) · `ToolCallIR.` (2) ·
   `role.canRequestEscalation` (2) · `canRequestEscalation` (2).
   These sit in `corpus.jsonl`/`corpus.json` — the released model's own stimulus — and 9 further
   stimulus identifiers (`editor`, `reasoner`, `verifier`, …) are already vocabulary and invisible.
   **Shipping the stimulus means shipping its vocabulary.** This is the author's call, and it is the
   same fork already recorded as *the numbers or the vocabulary, never both*: either the released
   numbers keep their instrument names, or the counts are re-emitted anonymised.

2. **88 occurrences / 27 distinct — mechanism left in prose and Python outside the data.**
   `tccommon` (6) · `pchosen` (4) · `tcmodel` (3) · `tm.LogisticPairHead` (3) · `tccommon.render` (3) ·
   `nCandidate` (2) · `sharedGramCount` (2) · `LogisticPairHead` · `nKind` · `nSituation` · `nkind` ·
   `latencyMs` · `orderPermutationFlips` · `reproducesAt3dp` · `tccommon.fit_temperature` · plus
   filenames (`DECIDER_STACK_DECISION.md`, `tcmodel.py`, `tccommon.py`, `LEARNINGS.md`, `CITATION.cff`,
   `evals/fixtures/reflex-decisions.ts`). **These are ordinary redaction work**, not an authorisation
   question: they are mechanism names in human-readable text and can be renamed without touching a
   number.

**Do not** close the remaining 5,145 (b) + 528 (a) occurrences by adding them to
`vocabulary/english.txt`. Adding `arXiv` to an English list is harmless; adding the (c) tokens is not,
and the (c)/(b) boundary is exactly what a future unit would get wrong under pressure to make the
number zero.

## 7. Containment

Everything ran inside `scratch/ugate1/**`. The real destination
`/home/zer0null/research-publish-packages` was never used as `DEST`. Nothing was written under
`scratch/ubij1|ubij2|ubij3|upack1|uver2*|ufix2*|uwire*|unoncensus*|udtag1/**`, `repro/**`,
`orchestration/units/UBUILD1.build.sh` or `tests/test_build_wiring.py`. No git command was run against
`/home/zer0null/Duval`.

## 8. Artifacts

| path | what |
|---|---|
| `scratch/ugate1/oov_tokens.tsv` | deliverable 1 — 1,464 distinct tokens, occurrences, file classes |
| `scratch/ugate1/oov_tokens_classified.tsv` | deliverable 2 — the same rows with a UGATE1 class |
| `scratch/ugate1/gate_scoped.sh` | deliverable 3 — the scoped gate |
| `scratch/ugate1/make_data_vocab.py` | generates `vocabulary/data.txt` (keys mode / full mode) |
| `scratch/ugate1/residual_report.py` | re-runs the scoped rules and aggregates the residual |
| `scratch/ugate1/residual_keys.txt` | the residual table reproduced above |
| `scratch/ugate1/gate-keys.log`, `red.log`, `green.in.log`, `green.out.log` | literal gate output for §5 |

---

## 9. UGATE3 — port verified in the release build, and re-measured (2026-10-16)

**Unit:** UGATE3 · **Subject:** the gate heredoc of `orchestration/units/UBUILD1.build.sh`, run into
`scratch/ugate3/dest/research-publish-packages`.

**The port was already present when this unit started.** The heredoc (mtime 2026-10-16 01:12, before
UGATE3) already carried the scoped revision — comment `[UGATE2: SCOPED revision of the UBUILD1 gate]`
at line 661, `FAIL_LIMIT = 10 ** 9` (uncapped) at line 802, the `VOCAB_REL` self-skip at lines 709/808,
the fail-closed empty-vocabulary check in `load()` at lines 728–730, and the JSON-**keys**-only data
vocabulary derivation at lines 587–655. UGATE3 therefore **verified** the four required properties
against the running build rather than re-porting them; `UBUILD1.build.sh` was **not modified** (and
line 134 `PROMOTED_SAN_SRC` is untouched, as the card requires). All four hold:
a 29-file ship-list, `chmod +x`, the invocation, `GATE_RC=$?` and `exit "$GATE_RC"` are unchanged.

**Build result** (`DEST=scratch/ugate3/dest/research-publish-packages`):

```
pruning the staged tree against the ship-list
  staged 29 file(s): 29 kept, 0 dropped
  ship-list enforced: 29 staged file(s) present
  never-ship list enforced: 15 names checked absent
  vocabulary/english.txt: 74959 words
  vocabulary/data.txt: 501 declared data-file key(s) from 32 parsed document(s)
  anchor 907fa39 present in 4 file(s) — kept deliberately
  repo total     : 39 files, 2.6M
flagged tokens: 1410
offender lines listed: 1410
GATE RESULT: FAIL -- 1410 out-of-vocabulary token(s).
```

**Old → new:** the card's pre-patch count was **1689**; the corrected gate measures **1410**
(39 fewer after removing the scan of `vocabulary/` — **0 offenders under `vocabulary/`**, versus the
117 phantom offenders UGATE1 found in the old gate — and after dropping the 400-line cap, every one of
the 1410 is now named). Emitted: **39 files** (excluding `.git`), 29 of them the shipped package.

**The residual 1410, classified** (heuristic classifier — `scratch/ugate3/offenders_classified.tsv`,
every offender with path/line/token):

| class | occurrences | distinct |
|---|---|---|
| (a) released-schema keys / format-shaped identifiers | 80 | 38 |
| (b) third-party / incidental (ordinary words absent from the 75k list) | 1054 | 296 |
| (c) **genuinely mechanism** | **276** | **11** |
| (d) encoding / tokenisation artefacts | 0 | 0 |
| **total** | **1410** | **321** |

All 11 (c) tokens sit in the released data/stimulus — `fixture/fixture-190.json`,
`fixture/reflex-decisions.ts`, `second-labeller/cases.json`, `second-labeller/blinded_cases.json`,
`results/*.json`: `fs.read` 116 · `fs.write` 104 · `fs.write.` 8 · `expiresAtEpoch` 12 ·
`reasonerCalls` 8 · `MutationProposal` 8 · `role.canRequestEscalation` 5 · `ToolCallIR` 5 ·
`ToolCallIR.` 4 · `canRequestEscalation` 4 · `policyHash` 2. That is a subset of UGATE1's 404 and is
the same authorisation fork as §6.1: *shipping the stimulus means shipping its vocabulary*. The count
fell from UGATE1's 6,093 because the tree itself shrank; **the vocabulary was not widened and
`--mode full` was not used.**

**Red → green** (on `scratch/ugate3/redtest`, a copy; honest tree untouched):

```
RED   flagged tokens: 1411
      packages/exp12-encoder-crossover/results/REPORT.md:305: grantPolicy  [identifier-shaped, not a declared public identifier]
GREEN flagged tokens: 1410   (GATE RESULT: FAIL -- 1410 ...)
      diff -r <honest tree>/packages redtest/packages  ->  IDENTICAL after restore
```

**Fail-closed** (on `scratch/ugate3/failclosed`, `vocabulary/english.txt` emptied):

```
gate_rc=2
FATAL: vocabulary file has no declared terms: .../failclosed/vocabulary/english.txt
# the build's own gate block (UBUILD1.build.sh:958-971) on that copy:
BUILD COMPLETE — the exclusion gate FAILED (exit 2).   propagated_rc=2
```

It never prints PASS on missing/empty inputs. The 1410 is reported as a finding, not driven to zero.

---

## 9. UGATE2 — the correction wired into the build (2026-10-16)

UGATE1's candidate checker `scratch/ugate1/gate_scoped.sh` is now **wired into
`orchestration/units/UBUILD1.build.sh`** (its `GATE_EOF` heredoc). Structure kept:
the heredoc, `chmod +x`, `bash "$DEST/gate.sh"`, `GATE_RC=$?`, `exit "$GATE_RC"`.
`vocabulary/data.txt` is now **derived by the build at build time, in `keys` mode
only** (501 declared JSON keys from 32 parsed documents on the current package).
`make_data_vocab.py --mode full` is **not used anywhere in the build**: it declares
8 of 15 mechanism names and buys a lower number by shipping the leak as vocabulary.

* **Latent defect in UGATE1's shipped artifact, found and fixed before porting:**
  `scratch/ugate1/gate_scoped.sh:121` reads
  `if rel.split(os.sep)[0] == VOCAB_DIR or os.path.dirname(rel) == VOCAB_DIR` —
  `VOCAB_DIR` is an **absolute** path while `rel` is relative, so the guard **never
  fired** and the "does not scan its own `vocabulary/`" fix was not in effect in
  the artifact. Measured: **117** phantom offender lines inside `vocabulary/data.txt`
  on `scratch/ugate1/candidate-keys/research-publish-packages` (6,093 → 5,976 with
  the guard actually working). The ported gate compares against the *relative*
  vocabulary dir name; on the current package that removes **51** phantom lines.
* **Offender cap removed**, listing complete: the current package prints **1,398**
  offender lines for **1,398** flagged tokens (no "(listing the first N)").
* **Fail-closed**, both at the gate and at build time: missing `vocabulary/data.txt`
  → `exit 2` (`FATAL: cannot read vocabulary file: …`); empty file → `exit 2`
  (`FATAL: vocabulary file has no declared terms: …`); the build's derivation of
  `data.txt` over a tree with no data files → `exit 1` (`FATAL: derived an EMPTY
  data vocabulary from …`) and **writes no file**, so the gate cannot run on an
  empty input.
* **RED→GREEN** on a copy: appending the genuine mechanism name `tccommon` to
  `packages/exp12-encoder-crossover/README.md` gives 1,399 and names
  `packages/exp12-encoder-crossover/README.md:32: tccommon  [word not in the declared
  vocabulary]`; removing it restores 1,398; `diff -rq` shows the copy byte-identical.

### Scope correction to §2–§6 (important)

The 29,936 / 6,093 figures above were measured on `scratch/ugate1/candidate-keys/…`
(**65 files**) and `scratch/ugate1/emit/…` (**64 files**). Those trees are **not what
the current build stages**: `UBUILD1.build.sh` stages from `scratch/urecut1/package`
and prunes against `SHIP_STAGED` — **29 staged, 29 kept, 0 dropped**, **39 emitted
files**. The card's "29-file package" is the current state. On that identical tree,
the **old shipped gate measures 1,740** (the card's 1,689 was an earlier revision of
the staged bytes) and the **new scoped gate measures 1,398**. UGATE1's *shape*
survives — third-party lexicon coverage dominates and the mechanism residual
concentrates in the released stimulus — but §2–§6's magnitude is ~4.4× too large
because those 64/65-file trees still carried `code/`, `eval/` and `paper/` content
that the ship-list drops.

### The 1,398 residual, by class (regenerated; exact table below)

The gate does not scan its own `gate.sh` into the count — **0** self-offenders.
`c-outside` (mechanism in prose/source outside data) is **0** on this tree: the
`tccommon`/`tcmodel`/`LogisticPairHead` names lived in `code/` and `paper/`, which
do not ship. What remains is dominated by non-mechanism lexicon coverage, plus the
mechanism *inside the released stimulus*, which is the author's call:
```
listing lines parsed=1398  flagged=1398  listed-field=None  UNCAPPED=False

b-thirdparty           occurrences= 1023  distinct= 260
   top: workspace(56), ECE(44), locator(38), redacted(32), pre-registered(28), licensor(24), pre-registration(21), MCP(20)

c-mechanism-stimulus   occurrences=  268  distinct=  10
   top: fs.read(116), fs.write(104), expiresAtEpoch(12), reasonerCalls(8), MutationProposal(8), role.canRequestEscalation(5), ToolCallIR(5), ToolCallIR.(4)

a-schema               occurrences=   64  distinct=  16
   top: kappa(20), labelsB.json(8), perCase(4), decider-4b-exp11-reproduction(4), laya-typed-decisions(4), labelable(4), routeA(3), falsifier(3)

unclassified           occurrences=   43  distinct=  25
   top: URECUT1(10), docs/research/P04-evidence/decider-rows.jsonl(4), docs/research/P04-evidence/imajev-rows.jsonl(4), UCORR3(3), UVER2/UCORR2(2), scratch/urecut1/build.py(1), repro/encoder-crossover-190(1), DecisionKind(1)
```

## 2026-10-16T06:28:43Z — UFIX30: revision authority + superseded 1,410 / 276 / 11

**Authoritative revision = the current on-disk `orchestration/units/UBUILD1.build.sh`**, sha256
`bbf5a52cb1983a0a0f3b6adf8aeaa1ab87e0dc3eabc97c21563e5e6b0512c372`, 48500 bytes, **968 lines**, mtime
**2026-10-16 01:15:52.564369969 -0500**, `:134 PROMOTED_SAN_SRC` intact. It is stable: re-hashing 15 s apart
gave the identical sha256 and identical size/mtime (no writer active; last write was 01:15:52, ≥10 min before
the probe). It is the only revision with a reproducible count (UGATE2's own build and UVER30's independent
re-run both print 1398) and the only one whose `SHIP_STAGED` (29 names) matches the promoted tree that
`tests/test_build_wiring.py::test_ship_list_is_exactly_the_promoted_tree_as_it_is` asserts.

### Revision trail (filesystem only; no git run)

| artifact | sha256 | lines | mtime | revision it came from |
|---|---|---|---|---|
| `orchestration/units/UBUILD1.build.sh` (live) | `bbf5a52c…` | 968 | 2026-10-16 01:15:52 | current authoritative |
| `scratch/ugate2/UBUILD1.build.sh.pre-ugate2.bak` | `bb4896e5…` | 843 | 01:12:24 | pre-UGATE2 |
| `scratch/uwire3/UBUILD1.build.sh.green` | `bb4896e5…` | 843 | 01:09:55 | same 843-line bytes |
| `scratch/uwire2/UBUILD1.build.sh.orig` | `df471955…` | 1036 | 10-15 21:47:26 | UWIRE2 work product |
| `scratch/uwire1/UBUILD1.build.sh.orig` | `a2a1df17…` | 1019 | 10-15 21:47:20 | older wiring |
| `scratch/uver15/UBUILD1.pre.sh` | `5c837c8d…` | 1019 | 10-15 20:58:51 | older wiring |
| `scratch/ulicence5/UBUILD1.build.sh` | `eecab269…` | 1019 | 10-15 19:49:27 | oldest surviving |
| `scratch/uver21/staled/orchestration/units/UBUILD1.build.sh` | — | — | — | **symlink to the live file**, not a snapshot (do not cite as evidence of an older revision) |

Which artifact came from which: `scratch/uwire3/dest/research-publish-packages/gate.sh`
`0940edb9…` (124 lines, 0 self-references) ← the 843-line revision; `scratch/ugate3/dest/…/gate.sh`
`7df3ed72…` (184 lines, 13 self-reference occurrences) ← an **unpreserved intermediate revision** live at
~01:13–01:14:04 (no surviving script copy contains `NKFS`, the marker token of that revision);
`scratch/ugate2/dest/…/gate.sh` `cccacbe9…` (176 lines, 0 self-references) and `scratch/uver30/build1.log`
← the current authoritative revision.

### Superseded figures and why they differ

- **Old shipped gate: 1,740** (this file, `:376`; UGATE2 also reports 1,740 on the identical 29-staged /
  39-emitted tree). The **1,689** in UGATE3's handoff ("as reported in the unit card") is an earlier revision
  of the staged bytes — superseded.
- **New scoped gate: 1,398 — authoritative.** `scratch/ugate2/build.log:1455` "GATE RESULT: FAIL -- 1398
  out-of-vocabulary token(s)."; `scratch/uver30/build1.log:1455` reproduces 1398 from the current script.
- **1,410 — SUPERSEDED.** `scratch/ugate3/build1.log:1467` (29 staged files). It is 12 higher because
  UGATE3's emitted `gate.sh` (`7df3ed72…`) carried **13 self-reference occurrences / 12 distinct tokens** the
  current heredoc no longer contains: `UGATE2`(1), `UBUILD1`(1), `UNCAPPED`(3), `DATA_EXT`(2), `fam`(1),
  `abr`(1), `A-Za-z`(1), `NKFS`(1), `uncapped`(3) — plus `enum-label` named by UVER30. The current
  revision's emitted gate (`cccacbe9…`) has **0** such tokens: re-derived from the current heredoc
  (`:661-836`), all of the listed tokens are absent (`fam` counted once as a word but it is incidental prose,
  not a vocabulary identifier). UGATE3's "script was unmodified" claim is **not supported**: its log (01:14:04)
  predates the current mtime (01:15:52).
- **Mechanism-in-stimulus class: 268 occurrences / 10 distinct — authoritative**
  (`scratch/ugate2/residual_by_class.txt`: `c-mechanism-stimulus occurrences=268 distinct=10`; top
  `fs.read`(116), `fs.write`(104), `expiresAtEpoch`(12), `reasonerCalls`(8), `MutationProposal`(8),
  `role.canRequestEscalation`(5), `ToolCallIR`(5), `ToolCallIR.`(4)). **UGATE3's 276 / 11
  ("c-genuinely-mechanism") is SUPERSEDED** — it counts the self-reference tokens as mechanism; the drop of 8
  occurrences / 1 distinct is part of the 1410→1398 correction. Companion classes on the 1,398 run:
  `b-thirdparty` 1023/260, `a-schema` 64/16, `d-encoding` 0, `unclassified` 43/25 in the residual file
  (UGATE2's handoff writes 42/24 — a one-line classification difference, the 43/25 text is the artifact).

### Follow-up edits (not made here)

1. `orchestration/units/UBUILD1.build.sh:134` — current text `PROMOTED_SAN_SRC="$SRC/scratch/urecut1/package"`;
   re-pin **this one line** only.
2. `SHIP_STAGED=( … )` = **lines 178–214** (29 names, lines 179–213; enforced at `:225`, `:242`, `:249`).
3. When the promoted tree changes, `SHIP_STAGED` must be re-derived from the new tree's real files (29 names,
   exact-set), and the gate counts re-measured on the new emitted tree:
   `strategy/BUILD_WIRING.md:143-144` ("re-pinning is **that one line** — the ship list must then be
   re-derived from the new tree's real files"), enforced by
   `tests/test_build_wiring.py::test_ship_list_is_exactly_the_promoted_tree_as_it_is` (`:222-235`).
