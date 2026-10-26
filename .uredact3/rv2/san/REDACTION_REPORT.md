# REDACTION_REPORT — paper #3 release package, mechanism-decluttered and reproduction-verified

**Unit:** UREDACT1 · **Written:** 2026-10-15 (UTC) · **Fixes:** UTS1 `strategy/TRADE_SECRET_AUDIT.md` §4.3 and §5.2
**Subject:** `repro/encoder-crossover-190-SANITISED/` (new directory; the as-audited `repro/encoder-crossover-190/` is untouched)
**Target of record:** `the read-only target repository` at HEAD `907fa39da7ba8ecfbe6e976b7a4cddadea7ac36b` — read-only, never written, no `git` state change.

**What this report answers.** UTS1 found that the reproducibility subset ships mechanism disclosure, and proposed a
cheap fix: redact the fixture's `rationale` and `namespaces` fields, because the schema records that `rationale` is
*"used in review, not fed to the model"*. This unit **tests** that fix rather than assuming it, and reports two things
the audit could not:

1. **The fix is free for every number.** All **nine** values listed in `papers/encoder-crossover-190/CLAIMS.md` are
   accounted for from inside the sanitised tree — **eight recomputed** and one (`0.6684`) a **quoted published
   constant** — and the paired table `39 + 27 + 90 + 34 = 190` recomputes exactly. Nothing moved. (§4)
2. **The fix is not sufficient.** The instrument's **`question` text names internal mechanism 47 times in 47 cases**,
   and two option labels name internal primitives. Those fields are the model input; editing them would move every
   accuracy. The rationales were never the main disclosure surface — the questions are. (§7)

That second finding is the one that should change the author's decision, and it is why this unit also produces a
labelled **no-union variant** rather than silently deciding the `DecisionKind` question UTS1 flagged. (§6)

---

## 1. The leak, as audited

UTS1's finding, verbatim in its own terms: `fixture/reflex-decisions.ts` carries "**335 lines** [that] match
kernel-internals vocabulary", naming `src/broker.ts`, `src/scope.ts`, `src/layer.ts`, `src/loop.ts`, `src/policy.ts`,
`src/state.ts`; `StateClass` 32×, `grantPolicy` 30×, `manifest` 30×, `expanded[]` 6×, `admit()` 4×,
`content-addressed` 3×; and `:292` states enforcement-by-absence outright. `fixture/DECISION_CASE_SCHEMA.ts` ships
the complete 7-member `DecisionKind` union and the six kernel namespaces. `EXCLUDED.md` E1 bounds *implementation
code* and is silent about *mechanism*, which is why it slipped through.

**Re-measured here, and reconciled.** Scanning the fixture with a 14-term set drawn from UTS1's own list
(`StateClass|grantPolicy|expanded|admit(|src/*.ts|manifest|content-addressed|namespaces|DecisionKind`) gives **330
matching lines** in that file. UTS1's 335 counts a slightly wider term set; the two agree to within the difference in
vocabulary, and the finding is confirmed as stated. The strict scan used for the before/after numbers below is the
narrower, higher-precision set in §7, because `manifest` and `layer` also match ordinary English and the model
architecture records (`num_layers`), and mixing those into a leak count makes the count meaningless.

---

## 2. Inventory — before and after, by file and line count

**Term set** (the "strict mechanism" regex; it matches internal type names, internal file paths, internal API calls
and internal codenames, and nothing generic):

```
StateClass|grantPolicy|materialiseGrants|grantKey|admit\(|src/(broker|scope|layer|loop|policy|state)\.ts|content-addressed|DecisionKind|expanded\[\]|Needle
```

**Scope of these counts — corrected by UFIX10 after `strategy/VERIFICATION_REPORT_8.md`.** The per-file table below is
the **instrument-file** scope: it excludes this unit's `verify/` scaffolding and the `variants/` alternative **and**
every unit's own authored prose and tooling (`README.md`, this report, `redact.py`). That is the only scope in which
"210 → 154" holds, and UVER8's finding is that the report published it as though it were the whole. Measured over
**exactly the exclusion this report states** (`verify/` and `variants/` removed, nothing else) the sanitised figure is
**216**; over the **whole shipped tree** it is **330**; instrument-files-only it is **154** against the
as-audited **209**, i.e. **−55**. See §7(d) and [`RESIDUALS.md`](RESIDUALS.md).

Scan, `grep -rIlE "$STRICT" .` + `grep -cE`:

| file | as-audited | sanitised | what the residual lines are |
|---|---:|---:|---|
| `fixture/reflex-decisions.ts` | 80 | **52** | `question` text (50 lines) + 2 option labels — **irreducible**, see §7 |
| `harness/data/fixture-190.json` | 68 | **50** | the same question/option text, exported — **irreducible** |
| `fixture/DECISION_CASE_SCHEMA.ts` | 5 | **3** | the `DecisionKind` type *name* only — the author's trade, §6 |
| `results/eval-{shuffled-label,majority-class,deberta-v3-base,setfit-mpnet,modernbert-base}.json` | 8/7/7/6/6 | **8/7/7/6/6** | option labels used as answer keys — **irreducible** |
| `results/baselines.json` | 6 | **6** | same option labels — **irreducible** |
| `second-labeller/EVIDENCE.md` | 5 | **2** | verbatim option-label quotations (parser-defect note) |
| `second-labeller/disagreements.jsonl` | 3 | **3** | `question` text of a disagreement row — **irreducible** |
| `second-labeller/OWED_CORRECTIONS.md` | 2 | **0** | (10 verbatim rationale quotes removed) |
| `second-labeller/RUN.json` | 2 | **1** | an option-label quotation |
| `second-labeller/parse_fixture.py` | 1 | **1** | docstring quoting the same option label |
| `second-labeller/PREREGISTRATION.md` | 1 | **1** | mentions the `DecisionKind` type declarations |
| `README.md` (authored front matter, **not** an instrument file) | 1 | **4** | the `DecisionKind` *type name* only, in the four places the variant decision requires (see §6); the as-shipped README measured **8** lines — UVER8's C1 — which re-quoted the withheld vocabulary, and those lines now point at §7/`RESIDUALS.md` instead |
| `MANIFEST.json` / `INTEGRITY.md` (as-audited) | 1 / 1 | 1 / 0 | provenance line for the schema; INTEGRITY.md regenerated |
| **TOTAL, instrument files only** | **209** | **154** | **55 strict-mechanism lines removed** |
| *(context)* whole stated exclusion incl. authored front matter | 210 | **216** | **+6** vs as-audited |

**A second, larger withdrawal that the strict regex does not see.** `harness/LEAD-WIRING.md` (141 lines) carried the
private repository's **complete `npm run suite` script list**, its **CI job matrix**, its repo-policy gate text and
internal decision numbers — UTS1 H8: *"a map of the private tree… Exclude or scrub."* It has no strict-mechanism hit,
so it would pass the regex and still leak. It is replaced by a 42-line sanitised note (§3, R6). **Correction
(UFIX10):** the counts read 142 → 43 in the first release; `wc -l` and `awk 'END{print NR}'` both give **141 → 42**
(both files newline-terminated), per `strategy/VERIFICATION_REPORT_8.md` O5.

**In the instrument files, after the redaction, zero residual lines disclose a kernel rule, an internal file path, or
an internal API call outside instrument field values.** Every one of the 154 is either (i) the instrument's own
`question`/option text, which is the model input, or (ii) a reference to the `DecisionKind` type name — the union
VARIANT A deliberately keeps (§6). §7 classifies all 154. **This is an instrument-scope statement only:** the shipped
tree as a whole also carries the unit's own prose and tooling, which name that vocabulary while describing the
residual — see §7(d) and [`RESIDUALS.md`](RESIDUALS.md).

---

## 3. Exactly what was redacted, and how

Deterministic, re-runnable, logged to `verify/redaction-log.json` by [`redact.py`](redact.py). The script reads only
`../encoder-crossover-190/` and writes only inside this directory; it **refuses** (exit 1, with a reason) rather than
redacting blind if any expected shape is not found.

| # | move | detail |
|---|---|---|
| **R1** | fixture header | The 52-line comment block (which named `admit()`, `src/scope.ts`, `src/state.ts:256`, `DAG`/scope enforcement) is replaced by a neutral header of **exactly 52 lines**, padded with ` *` comment lines. Line count preserved so every record keeps its original physical line number. |
| **R2** | inline comments | The 7 inline comments on the `DecisionKind` union (`// which StateClass runs the next step`, `// … to surface to Needle 3`, …) are stripped; the interface's `/** Namespace(s) the case draws on: task\|evidence\|execution\|capability\|policy\|decision */` becomes `/** Withheld in this sanitised release. */`; the 5 section notes inside `DECISION_CASES` that name mechanism are neutralised. Applied in both the fixture **and** the schema. All of these are same-line replacements: line count unchanged. |
| **R3** | fixture field values | Every `rationale:` value → `""` (190 of them) and every `namespaces: [...]` → `[]` (190). **Keys are kept.** The as-audited file has 190 `rationale:` *keys*, each followed by exactly one value line, and 190 single-line `namespaces:` fields — the script asserts this before touching anything. |
| **R4** | exported fixture | `harness/data/fixture-190.json`: `rationale` → `""`, `namespaces` → `[]`, keys kept, all 190 records. |
| **R5** | exporter | `harness/export-fixture.ts` re-emitted `rationale: c.rationale, namespaces: [...c.namespaces]`; that is now `rationale: "", namespaces: []`, and the digest constant is annotated with `SANITISED_INSTRUMENT_SHA256` instead of being silently rewritten. |
| **R6** | prose that quotes withheld text | `harness/LEAD-WIRING.md` → 42-line sanitised note (private suite/CI map withheld). `second-labeller/EVIDENCE.md`: 2 literal patches (the quoted ERRATA rationale span; the `capability.family-010` rationale quote) + the kernel identifier scrub. `second-labeller/OWED_CORRECTIONS.md`: 10 verbatim rationale quotes → `*[withheld rationale quote]*`. `second-labeller/RUN.json`: 1 kernel identifier → `[redacted]`. |
| **R7** | variant | `variants/no-union/files/` — the same two files with the enumerated union removed, line count preserved. See §6. |

**Why keys and line numbers were preserved rather than fields deleted.** The shipped reader
`second-labeller/parse_fixture.py` *requires* the `rationale` key (it records `missing_fields` when absent), and
`_line` provenance in `cases.json` / `disagreements.jsonl` is a physical line number. Emptying keeps both intact, so
**no reader had to be edited** — which is itself part of the reproduction proof: the readers that produce the
second-labeller numbers are the shipped, unmodified ones.

**One consequence that had to be handled, not hidden.** `second-labeller/disagreements.jsonl` ships with
`recorded_rationale` embedded for all 18 disagreement rows — 18 withheld rationales, in a file the README tells
readers to re-generate. The sanitised tree ships the **regenerated** row set, where `recorded_rationale` is `""`
(§4, test T6). Shipping the stale file would have leaked the very text R3 removes.

---

## 4. PROOF — the acceptance test

Everything below was run as `bash verify/run-verification.sh` (full log: `verify/VERIFICATION.txt`) and
`python3 verify/recompute-claims.py` (full output: `verify/RECOMPUTE-CLAIMS.txt`). The verification script **copies**
the as-audited subset and the sanitised subset into `/tmp/uredact1-verify/` and runs the *same* commands in both; it
never executes anything inside the original directory. Steps 1–4 have no torch, no network and no GPU dependency —
`evaluate.py`/`analyze.py` do (they read `harness/out/manifest-*.json`, which `EXCLUDED.md` E12 excludes and which
are therefore *not* re-runnable in this subset; their outputs ship frozen and are byte-identical, listed in §4.4).

### 4.1 T1 — the instrument digest (EXPECTED TO CHANGE; declared here, not discovered later)

```
$ sha256sum /tmp/uredact1-verify/{orig,san}/fixture/reflex-decisions.ts
076164ac53c2c1aac130953345c481f88b51f4d6fb93d465c7430308a99b4796  .../orig/fixture/reflex-decisions.ts
751dc007ba115dccc5815fdf97c9ce7b34b0dc990a6e57802d762e9b35ad9cae  .../san/fixture/reflex-decisions.ts
```

The pre-registered digest **cannot** survive a value-level redaction, so the README's command (A) as written is now
unsatisfiable against the sanitised fixture. What replaces it is the invariant that actually matters:

### 4.2 T2 — the scoring projection is byte-identical

```
$ cd <tree>/second-labeller && cp ../fixture/reflex-decisions.ts ./reflex-decisions.sandbox.ts \
    && python3 parse_fixture.py && python3 compare.py
  parse_fixture.py [orig] exit=0    compare.py [orig] exit=0
  parse_fixture.py [san]  exit=0    compare.py [san]  exit=0
  scoring-projection (id,kind,question,options,correct) sha256 [orig] 57a29b4e78bff60f84309e2e95b56f49663884a13b801345eecd93813ecbf300
  scoring-projection (id,kind,question,options,correct) sha256 [san ] 57a29b4e78bff60f84309e2e95b56f49663884a13b801345eecd93813ecbf300
  cases [orig] 190  empty_rationales   0  empty_namespaces   0
  cases [san ] 190  empty_rationales 190  empty_namespaces 190
  _line values preserved [orig] [86, 97, 108] ... [2197, 2208]
  _line values preserved [san ] [86, 97, 108] ... [2197, 2208]
```

### 4.3 T3/T5 — the pipeline re-runs, and the split re-renders identically

```
$ cd <tree>/harness && python3 prepare.py     # verifies both digests, refuses on a fired F4 lint
  prepare.py [orig] exit=0
  prepare.py [san ] exit=0
  PREPARE STDOUT IDENTICAL   (paths normalised; diff -u produced no output)
$ sha256sum {orig,san}/harness/data/train.jsonl {orig,san}/harness/data/dev.jsonl
24c39afa8606942ac2f4fb3e6f1ce5c2b0c9ee581b67d1aed38260d4aa020c09  .../orig/harness/data/train.jsonl
24c39afa8606942ac2f4fb3e6f1ce5c2b0c9ee581b67d1aed38260d4aa020c09  .../san/harness/data/train.jsonl
d311a99f0d5b2bd8bcff03e9913b3857ec4c98ffd3714ce9a7afa42514eaa976  .../orig/harness/data/dev.jsonl
d311a99f0d5b2bd8bcff03e9913b3857ec4c98ffd3714ce9a7afa42514eaa976  .../san/harness/data/dev.jsonl

$ chance floor (mean 1/k over the 190), recomputed from the fixture
  orig  cases 190  chanceFloorMean1OverK 0.29105263157894734  options_total 721
  san   cases 190  chanceFloorMean1OverK 0.29105263157894734  options_total 721
```

The two rendered-split digests are also **the digests `LEAD-WIRING.md` recorded before this unit existed**
(`24c39afa…`, `d311a99f…`), so the redaction did not perturb the training or development render either.

### 4.4 T4 — every headline number, recomputed from inside the sanitised tree

`verify/recompute-claims.py` reads only files that ship in the sanitised subset. It recomputes the per-arm accuracies
from each arm's own 190 `perCase` records, aligns the best head against the decider-4b reproduction **by case id**,
and recomputes the exact McNemar.

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
    0.3474  modernbert-base sealed-190 accuracy      recomputed=0.3473684210526316     OK
    0.4526  majority-class control accuracy          recomputed=0.45263157894736844    OK
    0.2911  chance floor (mean 1/k)                  recomputed=0.29105263157894734    OK
    0.6684  decider-4b published baseline            QUOTED CONSTANT (see below)       OK
    0.6789  decider-4b same-run reproduction         recomputed=0.6789473684210526     OK
    counts 39+27+90+34 = 39+27+90+34 = 190 (OK)

  SECOND-LABELLER NUMBERS (from the shipped sanitised metrics.json)
    0.3252  second-labeller route-A kappa            0.32520740993294694    OK
    0.8837  second-labeller closed-vocabulary kappa  0.8837023738280471     OK
    0.9140  second-labeller roster+bespoke kappa     0.9139973672663448     OK
    0.3526  second-labeller A/B mutual agreement     0.3526315789473684     OK

  ALL CLAIM NUMBERS PRESERVED: True
```

**Honest limits of this table, stated rather than blurred.**

* `0.6684` is the **published decider-4b baseline** recorded in `tccommon.BASELINES` and `results/REPORT.md` §2. It is
  a quoted constant, not a recomputation — the same-run reproduction (`0.6789`) is what this tree can recompute.
  The script labels it as a quoted constant.
* `evaluate.py` and `analyze.py` are **not runnable inside this subset** (their `harness/out/manifest-eval.json` and
  `manifest-train.json` are excluded by `EXCLUDED.md` E12). Their outputs — `results/*.json` — are shipped frozen and
  are **byte-identical** between the two trees; `INTEGRITY.md` §1 hashes them. `analyze.py`'s McNemar is recomputed
  here from the shipped per-case records by `recompute-claims.py`, which is a re-implementation, not a re-run.
* The recomputed exact p (`4.166818e-09`) and paired MDE (`0.159494`) match `results/REPORT.md` (`4.167e-09`,
  `0.1595`). The 2×2 matches the audit's `39 + 27 + 90 + 34 = 190`.

### 4.5 T6 — the stale-rationale leak is removed, and nothing else changed

```
  rows 18 18
  keys that differ: ['recorded_rationale']
  every other key identical: True
  sanitised recorded_rationale values all empty: True

  orig-regenerated metrics.json == san-regenerated metrics.json : True
  san-regenerated == shipped (the 4 hand-added UFIX4 keys stripped) : True
```

**No headline number moved. `numbers_that_moved = 0`.** Had any moved, this report would say so in the first line.

---

## 5. The reproducibility cost — stated plainly

**Free of charge.** Every number, the split, the render, the instrument's case identity, the option sets, the
recorded answers, and the physical line numbers of all 190 cases. A reviewer can still re-run the second-labeller
check and re-derive every headline figure. The redaction is, on this evidence, **free for reproduction**.

**What a reviewer loses, and it is real.**

1. **The reasoning behind each label is gone.** The 190 rationales were the per-case justification — the reason each
   answer is the answer. A reviewer can now check *that* a label was recorded and *that* the second labeller agreed
   on 172/190, but not *why* the author chose it. The instrument's own self-containment claim can no longer be
   audited case by case.
2. **Four open flags lose their evidence.** `second-labeller/OWED_CORRECTIONS.md` flagged
   `capability.family-010`, `worker.class-023`, `capability.family-004` (and one register-quote item) on the strength
   of the rationales' own text. With the quotes withheld, those flags **can no longer be independently checked from
   this subset** — only taken on trust. The ledger says so at the top of the sanitised file, rather than reading as
   if the flags were still self-evident. Note the direction: `worker.class-023`'s defect is *visible in the question*,
   which survives, so that one is still checkable.
3. **`EVIDENCE.md` §7's judgement that "for those four cases a reviewer holding only the file still needs the
   rationale" becomes permanent** rather than fixable by shipping one more file.
4. **The pre-registered digest check cannot be run as written.** `sha256sum fixture/reflex-decisions.ts` no longer
   equals `076164ac…`; steps 1–2 (`export-fixture.ts`, `lint.ts`) assert that digest and would refuse. In the subset
   those steps already need a repo-shaped checkout and a TypeScript runner that the subset does not ship
   (`README.md` §5), and their outputs ship frozen — but a reviewer who did wire them up would hit a hard refusal,
   not a match. What replaces it: the scoring-projection digest
   `57a29b4e78bff60f84309e2e95b56f49663884a13b801345eecd93813ecbf300`, identical before and after.
5. **The paper's claims still stand.** The contribution is the measurement ("a fine-tuned encoder does not beat a
   fine-tuned 4B on this fixture; the crossover is a property of the baseline"), and every number behind it is
   reproduced. The rationales were never the contribution. **No claim in `CLAIMS.md` rests on a rationale.**

**Materiality verdict.** The cost is **material to reviewability, immaterial to the claims**. Stating it the other
way round would be the dishonest framing: a reader would reasonably expect a released instrument to justify its own
labels, and this one no longer does.

---

## 6. The union trade — both ways, labelled, with the author's decision left intact

UTS1: *"The `DecisionKind` union is a harder call: it is load-bearing for the paper's claim that the fixture is
**typed single-label**, so removing it weakens the contribution. That trade is the author's."* This unit does not
decide it. Both variants ship.

### VARIANT A — union **KEPT** (this is the default `repro/encoder-crossover-190-SANITISED/`)

`fixture/DECISION_CASE_SCHEMA.ts` and `fixture/reflex-decisions.ts` keep
`export type DecisionKind = "worker.class" | … | "acquisition";` with **comments stripped**. The seven kind names
remain declared, and they remain in the data: every one of the 190 records carries a `kind` field, and
`second-labeller/metrics.json` stratifies its kappa by kind. What is removed is the mechanism narration attached to
them (`StateClass`, `Needle 3`, the namespace list).

- **Preserves:** the paper's "typed single-label" claim; the closed-set typing; the fixture as shipped.
- **Costs:** 3 residual strict-scan lines that are the *type name* `DecisionKind` (a provenance comment, the
  declaration, the field type). No mechanism is disclosed by the name alone.

### VARIANT B — union **REMOVED** — `variants/no-union/files/{fixture/reflex-decisions.ts, fixture/DECISION_CASE_SCHEMA.ts}`

Both files replace the enumerated union with `export type DecisionKind = string;`, keeping the type name so the file
still type-checks and **keeping the line count** so `_line` provenance survives. Apply with the two `cp` commands in
`variants/no-union/README.md`.

- **Removes:** the enumerated union *declaration* — 7 member lines and the type's closed-set guarantee.
- **Does not remove:** the seven kind names. They are the `kind` **values** in all 190 records, in
  `harness/data/fixture-190.json`, and in `results/*.json` and `metrics.json`. Removing the declaration while leaving
  the data is why the measured leak reduction is **effectively nil**: the variant's own strict line count is 57 (the
  fixture) and 9 (the schema) — *higher* than variant A's 52/3, because the explanatory banner comment names the type
  it removed. The kind taxonomy is disclosed by the release either way.
- **Costs:** the "typed single-label" claim loses its declared closed set; a reviewer can no longer see that the
  label space is bounded by construction. That is a contribution-level loss for a mechanism-level gain of ~0.

### Assessment, with the reasoning exposed

**Variant A is the better trade on the measured evidence**, because the leak that matters is not the *declaration* —
it is the taxonomy's presence in the data, which neither variant can remove without changing every `kind` value and
therefore every per-kind number. Variant B pays a real price (the typing claim) for a real gain of zero. But this is
an assessment, not a decision: **if the author's view is that a declared closed label set is itself the mechanism**
(because it enumerates the kernel's decision surface), then variant B is the right call and the union *comments*
being stripped in variant A is not enough. The two variants are labelled and either can be shipped.

---

## 7. Residual-term scan — what still matches, and why it cannot be removed

Full log: `verify/RESIDUAL-SCAN.txt`. Scan of the sanitised **instrument** files: **154 strict-mechanism lines**
(§2 table, instrument scope), all classified. The shipped tree as a whole is larger — **330** lines, the bulk of
the difference being the unit's own prose and tooling (this report 35, `redact.py` 18, `README.md`
4) — and every one of those files is listed with a fixed/irreducible judgement in
[`RESIDUALS.md`](RESIDUALS.md). §7(d) states the scope.

**(a) The instrument's own `question` text — 47 of 190 cases, ~50 lines. IRREDUCIBLE.**
The `question` is the rendered model input (`tccommon.render`: `Situation: <question>`). Editing it changes what every
arm saw, and therefore every accuracy in `CLAIMS.md`. Per-term, inside questions: `StateClass` 30×, `grantPolicy` 19×,
private `src/*.ts` paths 10×, `content-addressed` 1×, `Needle` 1×. **`src/*.ts`, restated precisely (UFIX10 after
UVER8 O3):** the residue is **10 occurrences on 7 lines in `fixture/reflex-decisions.ts`** (one line, `:233`, carries
two), mirrored as **10** in `harness/data/fixture-190.json` and **2** in one `disagreements.jsonl` row — **22
occurrences across the instrument files**, every one inside `question` text. The earlier "9 path mentions" counted
distinct mentions in the fixture and missed the two on `:233`.

**(b) Two option labels — 2 lines, mirrored into every result record. IRREDUCIBLE.**
`"none -- admit() mints the state"` and `"the expanded[] ref list"`. These are entries in real option sets (and
answer keys in `results/eval-*.json`, `results/baselines.json`), so they are part of the tensors the arms were scored
on. They are also *quoted* in `second-labeller/{parse_fixture.py,EVIDENCE.md,RUN.json}` to document parser defect
D-P1 — quoting them there is what makes the defect explanation checkable.

**(c) `DecisionKind` type-name references — 5 lines.** `fixture/DECISION_CASE_SCHEMA.ts` ×3 (`:3`, `:8`, `:19`),
`MANIFEST.json` `:82`, `second-labeller/PREREGISTRATION.md` `:29`. The author's trade, §6. **Correction (UFIX10):**
the first release said 4; UVER8's O6 counted 5, and a direct grep confirms 5 in the instrument/front-matter files
(the sanitised `README.md` adds its own 4 `DecisionKind` mentions, which are front matter and not instrument
lines).

**(d) The unit's own prose and tooling — not instrument lines, and NOT absent.** After R1–R6 the sanitised
**instrument** files contain no residual occurrence of `src/*.ts`, `StateClass`, `grantPolicy`, `materialiseGrants`,
`grantKey`, `content-addressed` or `expanded[]` outside (a) and (b). The shipped tree *as a whole* does: this report
**35** strict lines, `redact.py` **18**, `README.md` **4**, `MANIFEST.json` **1**,
`INTEGRITY.md` **0**, plus the as-audited `verify/` logs and the `variants/` alternative. Each is a *description of*
the residual (this report's classification, the redaction script's own assertions, the README's pointer) rather than a
new disclosure of mechanism, and [`RESIDUALS.md`](RESIDUALS.md) lists every one of them file-by-file with that
judgement so a reader does not have to take it on trust.

**Correction recorded (UFIX10, from `strategy/VERIFICATION_REPORT_8.md` §7(d)/C2):** the sentence that stood here
claimed the sanitised tree contained *no* residual occurrence of that vocabulary "outside (a) and (b)". That was
false for the shipped tree — `REDACTION_REPORT.md`, `redact.py` and `README.md` carry it in prose — and it has been
replaced by this paragraph. The scanner remains the check: it runs at `verify/run-verification.sh` step 7, so a later
edit that reintroduces a term shows up in the scan totals.

**This is the finding that bounds the unit's own fix, and it should be read as the headline:**
**redacting the rationales removed the review notes, not the disclosure.** The questions disclose more (56
occurrences in 47 cases) than the rationales did (31 occurrences in 25 cases). A release that ships the sanitised
fixture still tells a reader that the system has a `StateClass` concept, a `grantPolicy` rule, and files named
`src/scope.ts` and `src/layer.ts` — because it asks models about them. Fixing that is **not a redaction**: it is
re-authoring the instrument and re-running every arm, i.e. a new experiment. The author should choose between that
and accepting question-level disclosure; the third option — shipping the rationales — is what this unit removes.

---

## 8. Leak surface beyond file contents — the fresh-export rule

UTS1 §5.3 / H6: *"EXP#12's harness was recovered from the closed branch `<redacted>` via `git cat-file blob`, so a
released repo's history is a leak surface: the release must be a fresh export, never a push of an existing tree."*
**Verified, and worse than merely plausible** (read-only `git` in the target; no state change). The commit id is
**redacted from this release** — see §8.1 for why and for what replaces it:

```
$ git -C the read-only target repository cat-file -t <redacted-commit-id>
commit
$ git -C the read-only target repository merge-base --is-ancestor <redacted-commit-id> HEAD ; echo $?
1                                  # NOT an ancestor: the branch is closed and unmerged
$ git -C the read-only target repository rev-parse <redacted-commit-id>:tools/typed-channel/{analyze,tccommon,train}.py
18966eff5fbd088fa850d0f01d6d32dae6b2d507
68c39632efbd81dae37a5332a6c0b716f574cc68
15858fcd4eb31840758987e1490ebeab56a8981c
$ git hash-object harness/{analyze,tccommon,train}.py      # in the subset
18966eff5fbd088fa850d0f01d6d32dae6b2d507
68c39632efbd81dae37a5332a6c0b716f574cc68
15858fcd4eb31840758987e1490ebeab56a8981c
```

A closed, unmerged branch is fully present in the object store, and **the released harness bytes are exactly those
blobs**. Nothing about releasing the *files* removes the *history* they came from. **The tree as it now stands
contains no `.git` directory, no packfile, no `.idx`, no bundle, no `packed-refs` and no `ORIG_HEAD` — 0 hits across
the tree** (UVER8's E/§6 re-check; `find` for all of those → nothing). **Correction (UFIX10):** the first release said
"no `.git` directory and no history", which understated what the tree still carried — `MANIFEST.json` shipped the
private branch's commit id **19×** as `git:<sha>:tools/typed-channel/…` provenance (18 harness entries + a
`branch_commit` field), and `INTEGRITY.md`, `README.md` and this report named it in prose. No history *object* was
present, but a history *reference* was. It has been removed from all four files (§8.1); `RESIDUALS.md` records it as
**fixed**. This unit's own INSTRUCTION TO THE RELEASE PROCESS follows. It is written into `README.md` §6 as an operational rule:

> **Release by fresh export, never by pushing an existing tree.** `git archive`/`cp -r` from the sanitised directory
> into a brand-new repository with a new first commit — no `git clone`, no `git push`, no `.git` carried over, no
> `--depth` clone of the private repo, no subtree/submodule. The release repository's first commit is its only
> commit, and its history contains nothing about the recovered branch or anything reachable from it. Corollary: **the
> sanitised tree must never be committed inside the private repository and then exported** — committing it there
> puts the sanitised files into the private object store and, more importantly, tempts the next person to export the
> private repo's history instead.

---

## 9. Deliverables and provenance

| path | what it is |
|---|---|
| `repro/encoder-crossover-190-SANITISED/` | the sanitised subset — **VARIANT A, union kept** |
| `…/REDACTION_REPORT.md` | this report |
| `…/README.md` | updated for the sanitised subset, incl. the fresh-export rule and what is withheld |
| `…/INTEGRITY.md` | sha256 of every sanitised file; the projection digest; proof the original and target are unmodified |
| `…/RESIDUALS.md` | **every** known residual mechanism reference in the shipped tree, file/line/count, each judged fixed or irreducible (added by UFIX10) |
| `…/variants/no-union/` | **VARIANT B**, labelled, with apply instructions (§6) |
| `…/redact.py` | the deterministic, self-checking redaction builder |
| `…/verify/run-verification.sh`, `verify/recompute-claims.py`, `verify/VERIFICATION.txt`, `verify/RECOMPUTE-CLAIMS.txt`, `verify/RESIDUAL-SCAN.txt`, `verify/redaction-log.json` | the acceptance test and its verbatim output |

- **Target read-only discipline:** HEAD before = after = `907fa39da7ba8ecfbe6e976b7a4cddadea7ac36b`;
  `git status --porcelain` reports the same four pre-existing untracked paths before and after
  (`.ci-trunk.txt`, `.relay/`, `docs/evidence/selfbuild/relay-outbound-2026-10-13.txt`, `docs/migration/`),
  attributed to the unrelated concurrent session, not this unit. All target access was read-only, including
  `git cat-file`.
- **The as-audited subset is unmodified:** re-verifying its own `MANIFEST.json` gives **42/42 entries unchanged, 0
  mismatched, 0 missing** (`INTEGRITY.md` §3).
- **No secret-shaped file was encountered or excluded.** Nothing in this unit's inputs was credential-shaped; the
  subset's own scan (`EXCLUDED.md` §4) records zero hits and this unit re-encountered none.
- **Nothing outside the declared write paths was touched:**
  `repro/encoder-crossover-190-SANITISED/**`, `orchestration/units/UREDACT1.md`,
  `orchestration/handoffs/UREDACT1.json`. In particular `strategy/`, `papers/`, `jobs/`, `journal/`,
  `experiments/` and the as-audited `repro/encoder-crossover-190/` were **not written**.
- **Amendment (UFIX10, 2026-10-15), containment:** writes limited to
  `repro/encoder-crossover-190-SANITISED/**` (this report, `README.md`, `MANIFEST.json`, `INTEGRITY.md`,
  `RESIDUALS.md`, `verify/integrity-table.md`), `orchestration/units/UFIX10.md`,
  `orchestration/handoffs/UFIX10.json`. `the read-only target repository` was not read from or written to by UFIX10 at all
  (the commit id was already recorded in this tree and in `strategy/VERIFICATION_REPORT_8.md`, which UFIX10 read).
  The as-audited `repro/encoder-crossover-190/` was not written. The re-run after these edits is recorded in §11.

## 10. AMENDMENT — UVER5's correction, the field-by-field leak surface, and the two honest options

**Added 2026-10-15 after `strategy/VERIFICATION_REPORT_5.md` (unit UVER5) corrected the carded premise, and
`strategy/VERIFICATION_REPORT_6.md` (UVER6) filed two flags against this directory mid-flight. Read §7 with this
section: §7 is the measurement, this is the decision framing.**

### 10.1 The correction, stated without hedging

**The carded "cheap fix" — redact `rationale` and `namespaces` — is INSUFFICIENT. It does not close the
disclosure.** UVER5 C1/O1 measures the fixture's `question` text as carrying **more** kernel vocabulary than the
rationales (**71 vs 38 prose lines** by its vocabulary; `:288`, `:571–575`, `:620–627`). This unit measured the
same thing independently before the correction arrived — **56 strict-mechanism occurrences across 47 cases in
`question`, versus 31 across 25 cases in `rationale`** (§7) — and both readings agree in direction and magnitude.
The difference is vocabulary, not finding.

What this unit's redaction therefore is, precisely: it removes **review metadata and documentation** that
disclosed internal file paths, internal type names, the namespace list, the enforcement rule, and the private
repository's CI/script map. It does **not** remove the disclosure carried by the fields the model reads. The
as-audited subset was an *unexamined* leak; the sanitised subset is a **documented, measured, bounded** one. That
is a better state and it is not a clean fixture, and any sentence in this tree that reads as "mechanism
disclosure removed" is wrong — §7 governs.

### 10.2 The leak surface, field by field (measured on the as-audited fixture)

| field | role | mechanism-bearing? | removable? | measured |
|---|---|---|---|---|
| `id` | key / alignment | no | must stay | 190 |
| `kind` | **model input** (`Kind:` line) + the label taxonomy = **M11** | yes — the 7 names | only the *declaration*; the names are the data | 7-member union + 190 values |
| `question` | **MODEL INPUT** (`Situation:` — `tccommon.render`) | **yes, and most** | **NO — editing it changes every accuracy** | **47/190 cases, 56 occurrences, ~50 lines** |
| `options` | **MODEL INPUT** (`Candidate option:`) | yes, 2 labels: `none -- admit() mints the state`, `the expanded[] ref list` | **NO — they are answer keys in the shipped result records** | 2 labels, mirrored into ~34 result lines |
| `correct` | label / scoring | no | must stay | 190 |
| `rationale` | **review metadata** — schema, verbatim: *"used in review, not fed to the model"*; `tccommon.py:19`: *"`rationale` and `namespaces` are never read"* | yes | **YES → removed** | 25 cases, 31 occurrences, 190 value lines emptied |
| `namespaces` | **review metadata** (never read) | yes — the six kernel namespaces = M11 | **YES → removed** | 190 values emptied |
| file header / inline union + interface comments / section notes | documentation | yes | **YES → removed** | 52-line header rewritten at equal length; 7+1+5 comments stripped |
| `LEAD-WIRING.md`, `EVIDENCE.md`, `OWED_CORRECTIONS.md`, `RUN.json` prose | documentation | yes | **YES → removed/scrubbed** | 142→43 lines; 10 rationale quotes; 3 literal patches |
| `disagreements.jsonl` `recorded_rationale` | stale copy of a withheld field | yes | **YES → regenerated empty** | 18 rows |

**The plain statement the card asked for: the decision surface's own vocabulary is disclosed, and it is disclosed
inside the fields that may not be removed without changing the experiment.** UVER5's conclusion — that the fixture
is closer to `withhold` than to a cheap redaction — is consistent with this table. So is this unit's position that
it is now a bounded, measured disclosure instead of an unexamined one.

### 10.3 The two honest options (the author's decision; this unit does not choose)

**(a) Rewrite the questions to carry the decision semantics without naming kernel internals.**

* **Is it achievable? Partially — and never with the numbers held fixed.**
* *What is preservable:* most of the 47 cases decide between semantically-describable options, so the rule can be
  stated neutrally — "a class whose declared policy grants no tools" instead of `grantPolicy 'none'`; "the
  narrower of the two permitted sets" instead of naming the module that enforces it. The questions would remain
  self-contained; the answer would remain derivable.
* *What is not preservable:* (i) the two **option labels** that name internal primitives are entries in the option
  sets *and answer keys in the frozen result records* — rewriting them rewrites the strings every arm was scored
  on; (ii) the cases whose **subject** is the mechanism (the 2026-10-01 errata cases about scope narrowing and
  grant construction, and the `context.package` cases about `expanded[]` paging); (iii) tokenisation: any question
  edit changes the rendered `Situation:` string and therefore the arms' outputs by an amount nobody can bound in
  advance.
* *Cost in fidelity:* the numbers in `papers/encoder-crossover-190/CLAIMS.md` would be **superseded, not
  preserved**; all five arms, the decider-4b baselines and the second-labeller pass would have to be re-run; and
  the instrument's in-place errata provenance becomes unverifiable, because the corrected text is gone.
* *Verdict:* this is **a new experiment, not a redaction** — and this unit's acceptance test forbids doing it
  silently, because it would move the headline numbers.

**(b) Ship the fixture as-is and accept that the decision surface is disclosed.**

* The evidence that makes this defensible, **attributed and not independently verified here:** UVER6 reports that
  **12 of the 13 mechanisms (M1–M10, M12, M13) are already public** in `the author's public companion repository`,
  whose `findings/PAPER-DERIVATION.md` is byte-identical (sha256
  `d98c4359d37b987db07707e0b96358de0cd280c979896c6a15858d96bcd14802`) to the derivation paper in the read-only
  corpus. This unit **did not verify that external claim**: within this workspace that sha256 string appears only
  in UVER6's own report and handoff (`strategy/VERIFICATION_REPORT_6.md`, `orchestration/handoffs/UVER6.json`). If
  it holds, disclosure of those mechanisms has already happened, secrecy is not a live question for them, and the
  remaining question is licence/provenance rather than confidentiality.
* Under (b) the sanitised tree still does real work — it removes the rationale, namespace, comment and wiring
  material, which adds nothing to the paper and cannot move a number — but the release must **carry the disclosure
  statement** (§7) instead of a clean bill of health.

**What is never acceptable, and this unit does not do:** shipping a leak while claiming it was fixed. The abstract,
§5 and §7 of this report say the fix is incomplete; §10.1 says it again.

### 10.4 UVER6's two flags on this directory — answered

1. **"The sanitised tree still names 9 `src/` paths → the M12 scrub is unmet." Measured and now closed as far as
   it can be.** Re-measured on the shipped artefacts, the `src/`-path residue is exactly: **10 path occurrences on 7
   lines inside `question`/option text in `fixture/reflex-decisions.ts`** (`workspace/src/loop.ts`, `workspace/src/broker.ts`,
   `workspace/src/broker-test.ts`, `src/policy.ts`, `src/a.ts`, `src/b.ts`, `src/x.ts`, `src/y.ts`; `:233` carries
   two) plus their mirror — **10** in `harness/data/fixture-190.json` and **2** in `disagreements.jsonl`, **22
   occurrences instrument-wide** — plus **one withholding statement**
   (`EXCLUDED.md:16`'s `src/**` boundary), plus this report's own citations. The generic `a/b/x/y` names disclose
   nothing; `policy.ts`, `loop.ts` and `broker.ts` are real kernel module basenames and **are irreducible** —
   they sit in the model input. **One prose leak the flag caught has been removed by this unit:**
   `harness/README.md` named the private `tools/` vs `src/` split (2 mentions → 0). The private *path map* asserted
   in the fixture's header and rationales (`src/scope.ts`, `src/layer.ts`, `src/state.ts:256`, `src/dag.ts`,
   `src/store.ts`, `admit()`, `grantPolicy`) is gone; what remains is M12 residue inside fields §10.2 marks
   non-removable. **M12 is therefore partially unmet and provably irreducible without re-authoring the questions.**
2. **"`LICENCE_TODO.md` says the code licence is NOT YET DECIDED, but it has since been decided."** Corrected:
   `LICENCE_TODO.md` now records **extracted pieces under PolyForm Noncommercial 1.0.0**, the main the source repository
   repository **proprietary**, papers **CC BY 4.0**, with the authoritative text in
   `strategy/licence-templates/` (this file records the decision and does not restate the text), and it retains the
   two constraints that survive the decision — a published licence is permanent for that version, and publishing
   source under any terms discloses it. `README.md` §9 is aligned to the same statement.

### 10.5 What remains open

The author's choice between (a) and (b); whether the residual in §10.2 is acceptable disclosure (a legal question —
UTS1 §8's standing recommendation, and UVER5 §"The single question that most deserves the time", are unchanged);
and UVER5's V2 — the public-footprint/prior-disclosure audit that UTS1 flagged as its largest untested assumption
and which this unit did not perform either. VERIFYING UVER6's public-repo claim independently is the cheapest way
to convert (b) from *attributed* to *established*.

---

**Not legal advice.** This report is an engineering redaction and its verification. Whether the residual in §7 is
acceptable disclosure is exactly the `needs-author-decision` row UTS1 §5.2 raises, and UTS1 §8's standing
recommendation applies unchanged: put the triage in front of a lawyer before the release ships.

---

## 11. AMENDMENT — UFIX10's corrections after `strategy/VERIFICATION_REPORT_8.md`

**Added 2026-10-15 by unit UFIX10**, acting on UVER8's `pass-with-corrections` verdict. UVER8 re-ran the acceptance
test on a fresh copy and confirmed the load-bearing result — **reproduction holds, `0` numbers moved, red→green
passed, the released harness blobs match the withheld branch, and the public-file hash was computed independently by
UVER8** — while finding residual leaks and overstated counts. Every item below was re-measured here before editing.

| # | UVER8 finding | state in the first release | **what this amendment changes** |
|---|---|---|---|
| A | `MANIFEST.json` shipped the private branch commit id (regex-blind) | 19 citations (`git:<sha>:tools/typed-channel/…` ×18 + `branch_commit`) | **removed from `MANIFEST.json`**; `harness_revision.branch` now reads "unmerged private branch — branch name and commit id withheld"; every harness entry keeps `source_sha256`; **§8.1** states the trade-off. UVER8 measured 20, the direct count here is 19 |
| B | `README.md` was not clean | 8 strict lines (UVER8 C1: 5 `DecisionKind` + 3 re-quoting the withheld vocabulary) | re-measured **8**; the 3 re-quoting lines now point at §7/`RESIDUALS.md` → **4** lines remain, all `DecisionKind`, judged **irreducible** because VARIANT A ships that union on purpose |
| C | leak counts stated without scope | "210 → 154 (−56)" mixing two scopes | restated with scopes: **instrument-only 209 → 154 (−55)**; over the report's stated exclusion **210 → 211**; whole tree **330**. `src/*.ts` corrected to **10 in the fixture / 22 instrument-wide**; `LEAD-WIRING.md` **141 → 42**; "ten values" → **nine** |
| D | §7(d) "nothing else" was false for the shipped tree | claimed no residual outside (a)(b) | §7(d) rewritten to name what *is* residual and where (this report 35, `redact.py` 18, `README.md` 4, `MANIFEST.json` 1) |
| E | "no history" overstated | no `.git`/packfile (true, 0 hits) but a commit-id reference survived | restated: no VCS objects **and** the reference is gone; §8/§8.1 |

### 8.1 The commit-id trade-off, stated plainly

**What removing it costs.** A verifier inside the private repository could previously take the commit id and check
the provenance claim directly — `git cat-file -t`, `merge-base --is-ancestor`, `rev-parse <id>:tools/typed-channel/…`
— and confirm that the released harness bytes are exactly that branch's blobs. Without the id they cannot; they must
fall back on content identity (below) and on the audit trail outside the release.

**What keeping it costs.** The branch is private and force-rewritten. Its id is *history structure* — it tells a
reader that a specific, unreachable private commit exists, when it was made and which private directory tree
(`tools/typed-channel/`) the release was carved from — and it is **useless to anyone outside the repository**: they
cannot resolve it, so it is provenance that cannot be checked by the readers it is published to. It is the exact
shape the fresh-export rule exists to keep out ("no `.git`, no history").

**Chosen: remove the id.** The rule is "no history", and an unresolvable history reference buys a verifier nothing
while leaking private-history structure. **What replaces it** (not a silent drop):

1. **Per-file content identity** — every recovered harness file carries `source_sha256` in `MANIFEST.json`, and
   `INTEGRITY.md` §1 carries the sha256 and byte count of every shipped file. A reader can tell a modified copy from
   this one without any repository access; that is the check that actually protects the release.
2. **The byte-identity claim, preserved and attributed** — the three spot-checked harness files hashed to
   `18966eff5…`, `68c39632…`, `15858fcd…` at recovery time, and those are the blob digests recorded in §8's transcript
   (now with the commit id redacted). The claim stands; only the unresolvable pointer to it is gone.
3. **The private path `tools/typed-channel/` is retained, deliberately.** It cannot be removed by editing this
   manifest alone: the released harness bytes themselves reference that directory **68 times** across
   `harness/{analyze,collect,train,evaluate,lint,export-fixture,defect-probe,prepare}.py`, `harness/README.md` and
   `results/REPORT.md`. Removing it would mean rewriting released harness files — breaking their byte-identity with
   the source blobs, which is the very property the fresh-export check verifies. It is recorded as an
   **irreducible** residual in `RESIDUALS.md` rather than hidden.
4. **The audit trail keeps the id** — `strategy/VERIFICATION_REPORT_8.md` and the workspace journal name it. The
   release does not.

**Re-verification after these edits (UFIX10, same day):** `bash verify/run-verification.sh` → exit 0, and
`python3 verify/recompute-claims.py` → exit 0, `ALL CLAIM NUMBERS PRESERVED: True`; **`numbers_that_moved = 0`**.
The edit touched prose, counts and provenance only — no instrument byte, no result record, no reader.
