# DET-VERIFY — a deterministic verifier for the machine-decidable checkpoints

**Status:** done. **Bound:** ≤30 tool calls, used 29; **0 network/model requests.**

Why: `GRADE-FIT-CONTROL` measured `grade_v3` FN 16/52 (30.8 %), FP 20/44 (45.5 %) and
`grade_v4` FN 14/52 (26.9 %), FP 22/44 (50.0 %) — it rejects `ANSWER: 64.` and accepts the
inverted call description. A mention test cannot distinguish a correct answer from its
negation, so ground truth here comes from the **AST of the cited source**, never from the
fixture's expected string and never from token presence.

## 1. The instrument (TASK 1)

[`det_verify.py`](../../experiments/ptr-engine/tools/det_verify.py) derives three facts and nothing else:

| check | source evidence it derives | decision rule |
|---|---|---|
| `cp.0.t12` | `DEFAULT_MAX_REFS` in `resolve.py`, by `ast.literal_eval` on the assignment | the answer must **assert** the integer 64, compared as a number. Punctuation and prose are irrelevant: `ANSWER: 64.` passes. A numeral the answer retracts (`64 is wrong`) is dropped; the **last surviving integer** after the final `ANSWER:` marker is the claim, so `...is wrong; the default is 32` asserts 32 and fails. |
| `cp.1.t24` | `ast.ClassDef` count matching the fixture's own pattern (`^Ptr\w*$`, taken from the checkpoint question) over the whole cited module | the asserted integer must equal the count — **31** classes; the names found are reported in the matrix. AST, not grep. |
| `cp.2.t46` | the single `ledger.record_refusal(...)` call inside `_refuse`, by AST: dotted callee + keyword names `scope, serialized_ref, code` | the answer's call claim must name that callee and exactly that keyword set (order-free). A renamed keyword (`grant=` instead of `serialized_ref=`), a missing one, or a wrong callee fails. |

**Negation, stated narrowly (the rule also lives in the file).** A call mention is negated
when, inside its own clause (back to the nearest `.`/`;`/`:`/newline, ≤100 chars, plus the
clause tail), one of these matches: a negative auxiliary/imperative
`(do|does|did|must|should|can|could|will|would) not`, a bare `never`, `not (to) call/
invoke/record/write/persist`, an `n't` contraction, `no … call/write/invocation`, or
`without (ever) calling/recording/writing/invoking`. A denial elsewhere in the answer does
not license rejecting a correct description, and a correct answer that merely says
"re-raised" is not negated. That is how `do NOT call ledger.record_refusal; ignore scope,
serialized_ref, text, code and error entirely` fails while
`...with scope, serialized_ref=text and code=error.code, then re-raised` passes.

**Declared undecidable** (no check invented): `repair.t30` (the correct action is a
dialogue commitment in the fixture, not a source fact; "restore the guard" and "do not
restore the guard" share the literal and differ only in intent) and `acc.n2b` (ground truth
is whether a test was edited — a fact about the agent's edits, not about any pinned file;
lexical verb matching is the failed instrument). Per-check reasons in §4.

## 2. The gate, both directions, with denominators (TASK 2)

Same corpus as `grader_fitness.py` (28 probes, imported read-only; **none dropped, none
tuned**). FN = correct-intent rejected; FP = incorrect-intent accepted. Omission probes are
excluded from both rates (correct in meaning, one required numeral removed) and reported as
a control, exactly as in the fitness measurement.

| checkpoint | FN / n correct | FP / n incorrect | omission rejected / n | gate (0/0) |
|---|---|---|---|---|
| `cp.0.t12` | 0/3 | 0/2 | 1/1 | PASS |
| `cp.1.t24` | 0/2 | 0/2 | 1/1 | PASS |
| `cp.2.t46` | 0/3 | 0/3 | 1/1 | PASS |

Denominators are **distinct probes**: the four fixtures carry a byte-identical checkpoint
array, so re-running per fixture would multiply n by four without adding evidence (the
fitness matrix's 52/44 are that 4× artifact; its distinct-probe equivalent, 13 correct /
11 incorrect, is what those rates reduce to). `det_verify` is fixture-independent by
construction — truth is the source file — so its n is 8 correct and 7 incorrect in scope.

**Names and text of every in-scope failure: none.** The only rejections of correct-intent
probes would be FNs; there are zero. The three omission probes are rejected as intended:
`ANSWER: sixty-four refs.` (`p.cp0.omit`, no numeral — `no_asserted_value`),
`ANSWER: thirty-one classes.` (`p.cp1.omit`), and `p.cp2.omit` (names `text=` where the call
passes `serialized_ref=` — `keyword_mismatch`, missing `serialized_ref`, extra `text`).

The gate is executable: `det_verify.py` exits 0 when FN=FP=0, 2 otherwise.

## 3. Red case (the guard must be able to fail)

[tests/test_det_verify.py](../../experiments/ptr-engine/tools/tests/test_det_verify.py) monkeypatches the shipped
checker's globals — the file on disk is not altered — so the same assertions that pass in
the green run fail under degradation:

| run | command | exit |
|---|---|---|
| green | `python3 experiments/ptr-engine/tools/tests/test_det_verify.py` | **0** (17 tests OK) |
| red A — FN | `DET_VERIFY_DEGRADE=naive python3 …/test_det_verify.py` | **1** — reintroduces the sentence-final-punctuation defect (a numeral must be followed by whitespace), so `ANSWER: 64.` has no asserted value; pooled FN becomes 4/8 and `p.cp0.para` fails |
| red B — FP | `DET_VERIFY_DEGRADE=mention python3 …/test_det_verify.py` | **1** — degrades `cp.2` to the old token-mention rule (callee named ⇒ accepted, no negation, no keywords), so `p.cp2.neg` and `p.cp2.negr1gap` are accepted: FP 2/7 |

## 4. Coverage (the eight the old grader never emitted)

`det_verify` decides **7 of the fixture's 12 acceptance checks** — the three checkpoint
facts plus their four mirrors — and hands back five with a stated reason.

| check | status | via | reason |
|---|---|---|---|
| `cp.0.t12` | decidable | `cp.0.t12` | literal value of DEFAULT_MAX_REFS, read by ast.literal_eval |
| `cp.1.t24` | decidable | `cp.1.t24` | ast.ClassDef count matching the fixture's own class pattern |
| `cp.2.t46` | decidable | `cp.2.t46` | callee + keyword names of the single record_refusal call in _refuse |
| `acc.cp1` | decidable | `cp.0.t12` | fixture says 'mirror of checkpoints[0] (turn 12)', expected 64 |
| `acc.cp2` | decidable | `cp.1.t24` | fixture says 'mirror of checkpoints[1] (turn 24)', expected 31 |
| `acc.cp3` | decidable | `cp.2.t46` | fixture says 'mirror of checkpoints[2] (turn 46)' |
| `acc.1` | decidable | `cp.0.t12` | decides 'source-value' for DEFAULT_MAX_REFS == 64 at turn 12 |
| `acc.2` | **undecidable** | — | an execution claim: 'test_scope.py and test_negative_controls.py exit 0'. No source AST implies a pytest exit status; deciding it means running the suite and reading the log, which is not an answer-content fact. |
| `acc.3` | **undecidable** | — | conjunction of two source facts (PtrNotAReferenceError exists, code PTR_NOT_A_REFERENCE exists) with a runtime count ('exactly one ledger refusal row'). The runtime half cannot be read from source, so the check as written is undecidable even though half of it is not. |
| `acc.4` | **undecidable** | — | decidable in principle by counting `def test_` with ast.FunctionDef in test_scope.py (grep -c replacement), but no probe in the corpus exercises it. Implementing an unprobed check would claim coverage with n=0, so it is handed back rather than silently added. |
| `acc.n2b` | **undecidable** | — | the ground truth is whether an existing test was edited/weakened. That is a fact about the agent's edits, not about any pinned source file; lexical verb matching is precisely the instrument that failed (FN on the compliant denial, FP on 'trimmed'). |
| `acc.n3b..acc.n3e` | **undecidable** | — | no_write constraints over four pinned paths: a filesystem-side provenance check (write log / hashes), not a property of the answer text. Both the old grader and this verifier emit nothing for them. |
| `repair.t30` | **undecidable** | — | the correct action is a dialogue commitment stored in the fixture's `repair.correct_action`, not a source fact. 'I will restore the guard' and 'do not restore the guard' contain the same literal and differ only in intent, so there is nothing in the AST to compare the claim against. |

Net: the coverage hole is **closed for the source-value checks** (`acc.cp1`, `acc.cp2`,
`acc.cp3`, `acc.1`) and **documented, not papered over, for the rest**. `acc.2` and `acc.3`
are runtime/log claims; `acc.4` is decidable in principle by AST but no probe exercises it,
so implementing it would claim coverage at n=0; `acc.n3b..n3e` are filesystem-provenance
constraints, not answer facts.

## 5. Comparison to the judge on the same probes (TASK 3)

`grade_v3` / `grade_v4` columns are their verdicts on the LR-01 fixture from the committed
`measure/grader-fitness.json` (same probes, same fixtures; not re-run, to avoid writing a
grade file). `det_verify` is intent-blind: it sees only the answer text and the AST.

| probe | checkpoint | intent | grade_v3 | grade_v4 | det_verify | reason |
|---|---|---|---|---|---|---|
| `p.cp0.ideal` | cp.0.t12 | correct | PASS | PASS | ACCEPT | asserted_value_matches |
| `p.cp0.para` | cp.0.t12 | correct | reject | reject | ACCEPT | asserted_value_matches |
| `p.cp0.para_np` | cp.0.t12 | correct | PASS | PASS | ACCEPT | asserted_value_matches |
| `p.cp0.wrong` | cp.0.t12 | incorrect | reject | reject | reject | asserted_value_mismatch |
| `p.cp0.neg` | cp.0.t12 | incorrect | PASS | PASS | reject | asserted_value_mismatch |
| `p.cp0.omit` | cp.0.t12 | omission | reject | reject | reject | no_asserted_value |
| `p.cp1.ideal` | cp.1.t24 | correct | PASS | PASS | ACCEPT | asserted_value_matches |
| `p.cp1.para` | cp.1.t24 | correct | reject | reject | ACCEPT | asserted_value_matches |
| `p.cp1.wrong` | cp.1.t24 | incorrect | reject | reject | reject | asserted_value_mismatch |
| `p.cp1.neg` | cp.1.t24 | incorrect | PASS | PASS | reject | asserted_value_mismatch |
| `p.cp1.omit` | cp.1.t24 | omission | reject | reject | reject | no_asserted_value |
| `p.cp2.ideal` | cp.2.t46 | correct | PASS | PASS | ACCEPT | call_shape_matches |
| `p.cp2.para` | cp.2.t46 | correct | PASS | PASS | ACCEPT | call_shape_matches |
| `p.cp2.wrong` | cp.2.t46 | incorrect | reject | reject | reject | call_not_named |
| `p.cp2.neg` | cp.2.t46 | incorrect | PASS | PASS | reject | call_negated |
| `p.cp2.negr1gap` | cp.2.t46 | incorrect | reject | reject | reject | call_negated |
| `p.cp2.para_noraising` | cp.2.t46 | correct | reject | reject | ACCEPT | call_shape_matches |
| `p.cp2.omit` | cp.2.t46 | omission | reject | reject | reject | keyword_mismatch |
| `p.rep.ideal` | repair.t30 | correct | PASS | PASS | HANDED BACK | undecidable |
| `p.rep.para` | repair.t30 | correct | PASS | PASS | HANDED BACK | undecidable |
| `p.rep.wrong` | repair.t30 | incorrect | reject | reject | HANDED BACK | undecidable |
| `p.rep.neg` | repair.t30 | incorrect | PASS | PASS | HANDED BACK | undecidable |
| `p.rep.omit` | repair.t30 | omission | reject | reject | HANDED BACK | undecidable |
| `p.acc.ideal` | acc.n2b | correct | PASS | PASS | HANDED BACK | undecidable |
| `p.acc.para` | acc.n2b | correct | PASS | PASS | HANDED BACK | undecidable |
| `p.acc.wrong` | acc.n2b | incorrect | reject | reject | HANDED BACK | undecidable |
| `p.acc.neg` | acc.n2b | correct | reject | reject | HANDED BACK | undecidable |
| `p.acc.evasion` | acc.n2b | incorrect | PASS | PASS | HANDED BACK | undecidable |

Restricted to the **same decidable checkpoints** over all four fixtures
(`comparison_to_judge_same_probes` in the matrix): `grade_v3` **FN 12/32 (37.5%), FP 12/28 (42.9%)**;
`grade_v4` **FN 10/32 (31.2%), FP 14/28 (50.0%)**; `det_verify` **FN 0/8, FP 0/7**.

Every defect the fitness control named is visible in the table and absent from
`det_verify`: `p.cp0.para`/`p.cp1.para` (`ANSWER: 64.` / `31.`) rejected by both judges and
accepted here; `p.cp0.neg`, `p.cp1.neg` (right numeral, asserted wrong value) accepted by
both judges and rejected here; `p.cp2.neg`/`p.cp2.negr1gap` (inverted call) accepted and
rejected here; `p.cp2.para_noraising` (correct, no `raising` token) rejected by both and
accepted here. `det_verify` and the judges now disagree in exactly the places where a
mention register must fail to read meaning.

**Fitness verdict, one sentence:** `det_verify` is **fit to be the quality metric for
`cp.0.t12`, `cp.1.t24` and `cp.2.t46`** (FN 0/8, FP 0/7, red-tested); it is **not** fit for
`repair.t30`, `acc.n2b`, or the acceptance checks it hands back, so no accuracy figure may
be claimed for those from this instrument — arm rankings restricted to the three
machine-decidable checkpoints are now defensible, and any broader `checkpoint_accuracy`
still measures the judge.

## 6. Errata (TASK 4)

[`ANCHOR-PREREG-V2-ERRATA.md`](../../experiments/ptr-engine/longrun/ANCHOR-PREREG-V2-ERRATA.md): the clause at
`ANCHOR-PREREG-V2.md:59-60` claiming `PtrBudgetExceededError` "carries `ptr` and `exceeded`
and `error`" is false under the document's own rule §1(a) (`:55-58`): a token with no
underscore has exactly one part, itself, so it carries **none** of them — as `:117` already
states for `budget`. Correct statement supplied; census impact **0/11 cells** (text defect
only); the hashed body is untouched, its rule-body digest reproduced as
`b16548301589593b8d1041325fce833ef60d3b39b8e8c0a205084ee35eb9ad57`
(whole-file sha256 `173f0c1c1e5f980fb7b0c23ca0f740e5c807bbb37402ebed7a8f43ebf8a844aa`).
R2 and R2.1 both remain frozen; neither is retired.

## 7. Reproduce

```
python3 experiments/ptr-engine/tools/det_verify.py                       # gate: exit 0
python3 experiments/ptr-engine/tools/tests/test_det_verify.py           # 17 tests, exit 0
DET_VERIFY_DEGRADE=naive python3 experiments/ptr-engine/tools/tests/test_det_verify.py   # exit 1
DET_VERIFY_DEGRADE=mention python3 experiments/ptr-engine/tools/tests/test_det_verify.py # exit 1
```

## 8. Assumptions recorded

- The grader columns come from the committed `grader-fitness.json` rather than a fresh run:
  re-running `grader_fitness.py` would write a grade file, which this card forbids.
- `cp.1.t24` counts classes over the **whole** cited module, not the fixture's stale
  `#L15-L142` range: the fixture's own expected value 31 equals the whole-file AST count
  (that range alone yields 20 classes; the module has 31), and the question
  asks what "errors.py defines".
- The gate's denominators are distinct probes, not fixture repetitions (§2).
- No file outside the card's declared write paths was written; the graders, fixtures,
  row/grade files and the two ANCHOR-PREREG documents are untouched.
