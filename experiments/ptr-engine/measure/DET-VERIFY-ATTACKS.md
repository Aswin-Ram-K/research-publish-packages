# DET-VERIFY-ATTACKS — independent attack pass on the repaired `det_verify.py`

Verifier: `V-DET-2` (not the author of `det_verify.py`, `test_det_verify.py`, the matrix, or `DET-VERIFY-FIX`).
Target under test: `experiments/ptr-engine/tools/det_verify.py` sha256 `12ccc74ea31c3843021f1ae6fa771b458082f78393e2117cd86960fd221b6439`;
tests `experiments/ptr-engine/tools/tests/test_det_verify.py` sha256 `5cd5000d3520bb69d2387dee10bbcdaa800624382c1bf8dad288a158f8cda910`.
All probes below were run by importing the module read-only (`det_verify.verify_probe`, `Truth()`, `check_call`, `check_numeric`) and calling it directly; none of them were added to the corpus.

## Baseline reproduced (own command output)

| command | observed |
|---|---|
| `python3 experiments/ptr-engine/tools/tests/test_det_verify.py` | exit **0**, `Ran 31 tests ... OK` |
| `DET_VERIFY_DEGRADE=naive ... test_det_verify.py` | exit **1** (17 FAIL lines) |
| `DET_VERIFY_DEGRADE=mention ... test_det_verify.py` | exit **1** (15 FAIL lines) |
| `python3 experiments/ptr-engine/tools/det_verify.py` | exit **0**, `POOLED FN 0/23 FP 0/22 omission_rejected 3/3 gate=True` |

`Truth()` in the same process read `DEFAULT_MAX_REFS=64` at `resolve.py:39` (sha `71a14c2c…`), **31** `Ptr*` classes,
and `_refuse`'s call `ledger.record_refusal(scope=scope_name, serialized_ref=text, code=error.code)` at line 69.

## Attack 1 — shadowing (the decisive one)

Truth call: `ledger.record_refusal(scope=scope_name, serialized_ref=serialized_ref, code=code)`.
Gate: `check_call` (`det_verify.py:492-510`), wrong-callee compare at `:501-502`, keywords set-equality at `:504`.

| # | answer | result |
|---|---|---|
| 1a | `ANSWER: ledger.add(scope=scope_name, serialized_ref=serialized_ref, code=code)` | **pass=False, call_not_named** ✅ |
| 1b | `ANSWER: it calls ledger.record_refusal(scope=scope_name, text=text, code=error.code)` | **pass=False, keyword_mismatch** (claimed `code,scope,text`) ✅ |
| 1c | control, exact truth call | pass=True, call_shape_matches |
| 1d | `ANSWER: the signature is ledger.record_refusal(scope=scope_name, serialized_ref=serialized_ref, code=code), but the code path actually calls ledger.add` | **pass=True, call_shape_matches** ❌ FP |
| 1e | `ANSWER: ledger.add(…same kwargs…); record_refusal appears only in the docstring` | pass=False, keyword_mismatch ✅ (but by empty-keyword accident) |
| 1f | kwargs only, no callee named | pass=False, call_not_named ✅ |

Both demanded forms are rejected: **1a `pass=False, call_not_named`**, **1b `pass=False, keyword_mismatch`**. The grader is not a bag of tokens.
**Residual shadowing FP (1d):** naming the true callee as a *signature* while asserting a different callee does the work is accepted, because
`call_claim` (`:440-475`) keys on the first *mention* of the truth callee in the answer segment and never checks which callee the
governing predicate attaches to. 1e shows the neighbouring case survives only because the trailing mention yields an empty keyword set.

## Attack 2 — numeral, my own cases (none copied from either handoff)

Truth 64. Rule: first non-citation survivor in the leading clause (`asserted_number`, `det_verify.py:149-178`), citations at `:108-121`.

| # | answer | result | judgement |
|---|---|---|---|
| 2.1 | `ANSWER: 64 of 100 refs` | pass=False, `no_asserted_value` | **FN** — the `\d+ of \d+` citation span (`:117`) swallows *both* numerals |
| 2.2 | `ANSWER: sixty-four` | pass=False, `no_asserted_value` | FN by design (defended in `DET-VERIFY-FIX.json:34`) |
| 2.3 | `ANSWER: 64 refs` | pass=True | ✅ |
| 2.4 | `ANSWER: the cap is as follows: 64` | pass=True | ✅ |
| 2.5 | `per resolve.py:39, ANSWER: 64` | pass=True | ✅ (pre-marker text is outside the segment, `:86-95`) |
| 2.6 | `ANSWER: not 64` | **pass=True** | ❌ FP — a denial of 64 is read as the assertion |
| 2.7 | `ANSWER: 1,064` | pass=False, asserted=1 | outcome right, tokenization wrong (`1` then `064`→64 dropped by first-slot) |
| 2.8 | ``ANSWER: `64` `` | pass=True | ✅ |
| 2.9 | `ANSWER: 100 refs of 64` | pass=False, asserted=100 | ✅ |

Invented numeral tally: **FN 2/5** correct-intent (2.1, 2.2), **FP 1/1** incorrect-intent (2.6).

The fix's own 8 `p.num.cite.*` cases: all `pass=True` now, and each is genuinely **red under the pre-fix last-survivor rule** —
re-implemented as `last integer in the answer segment`: old value 39, 3, 12, 39, 39, 39, 30, 142 vs truth 64/31. That claim holds.

## Attack 3 — negation, my own forms

All ten `p.neg.*` variants in the corpus return `call_negated` (verified per probe), and both asymmetry probes pass
(`p.neg.asym_clause`, `p.neg.asym_tail` → `call_shape_matches`).

| # | answer | result | judgement |
|---|---|---|---|
| 3.1 | `ANSWER: the fix aims to avoid a second ledger.record_refusal` | pass=False, **keyword_mismatch** | right outcome, wrong mechanism (`AVOID_VERB_RX :211-215` doesn't match "a second X") |
| 3.2 | `ANSWER: there is no ledger.record_refusal call in this path with scope, …` | **pass=True** | ❌ FP — `no … call` with the object *after* the mention: `:194` needs `call` within 3 words after `no`, tail scan (`:454`) has no `no` |
| 3.3 | `ANSWER: the path declines to call ledger.record_refusal with scope, …` | **pass=True** | ❌ FP — "declines to call" absent from lexicon (`:184-205`) |
| 3.6 | `ANSWER: the handler refuses to invoke ledger.record_refusal with scope, …` | **pass=True** | ❌ FP — "refuses to invoke" absent |
| 3.4 | `avoid calling ledger.flush; it calls ledger.record_refusal(…)` | pass=True | ✅ requested opposite asymmetry |
| 3.5 | `it does not call ledger.flush, but it does call ledger.record_refusal(…)` | pass=True | ✅ but only by accident: `clause_before` (`:246-250`) cuts at the **dot inside `ledger.flush`** |
| 3.7 | `it does not call flush but it does call ledger.record_refusal(…)` | **pass=False, call_negated** | ❌ FN — same sentence without the dotted callee |

Invented negation tally: **FP 3/3** incorrect-intent (3.2, 3.3, 3.6), **FN 1/3** correct-intent (3.7).
The asymmetry the fix claims is real but fragile: it is produced by tokenization of the *other* callee's name, not by clause attachment.

## Attack 4 — no old expectation flipped

Pre-fix corpus = `grader_fitness.PROBES` (28 probes, the graders' list the fix imports read-only).
Current corpus = 58 probes: **28 shared, 30 new, 0 dropped, 0 duplicate ids**.
For every shared id the `intent` (the expected pass/fail label) is **identical**, and the probe text is byte-identical
(`shared-id text changed []`). Every `EXTRA_PROBES` id is new. Growth 28→58, in-scope 15→48: **no re-labelling, no flips**.

## Attack 5 — coverage honesty

`COVERAGE` is built by loop from `CHECK_HANDLERS` at `det_verify.py:606-624`; `COVERAGE_SUMMARY` is derived, not typed:
`{"total": 13, "decidable_count": 8, "ratio": "8/13"}`, and `len(COVERAGE) == len(CHECK_ORDER) == 13`. Measured **8/13**.

Handlers are source-derived, not aliases of the `cp.*` expected strings — each `verify_probe` call re-derives through `Truth()`:

| check | handler (`:516-525`) | truth value it compared against |
|---|---|---|
| `acc.cp1` | constant → `check_numeric(answer, truth.default_max_refs)` | 64 from `ast.literal_eval` of `resolve.py:39` |
| `acc.cp2` | class_count → `len(truth.ptr_classes)` | 31 `ast.ClassDef` matching `^Ptr\w*$` |
| `acc.cp3` | call_shape → `truth.refuse_call` | `ast.unparse` of the single call in `_refuse` (line 69) |
| `acc.4` | test_count → `len(truth.test_functions)` | **9** `def test_*` in `tests/test_scope.py` (names printed; sha `00f54ed8…`) |

`acc.4` is not copied from `cp.*` at all: it reads a different file and a different AST node type. So are the three `acc.cp*`.

Undecidable never contributes: `verify_probe` returns `(None, "undecidable")` at `:531-533` for `acc.2`, `acc.n2b`, `repair.t30`, `acc.n3b`
(confirmed `pass=None`), and `evaluate` `continue`s before any rate slot at `:830-831`.

## Attack 6 — denominator sanity

Counted independently by iterating `load_probes()` and calling `verify_probe` per probe, not by reading the summary:

```
corpus 58 in_scope 48 correct 23 incorrect 22 omission 3
FN 0/23 FP 0/22 omission_rejected 3/3
excluded: acc.n2b (3 correct, 2 incorrect), repair.t30 (2 correct, 2 incorrect, 1 omission)
FN ids [] FP ids []
```

Matches the claimed `0/23`, `0/22`, `3/3`, `48/58`, `10 excluded` exactly. The printed gate line is computed by `build()`
(`det_verify.py:877-887`) from the same tally loop — it is not a hand-written string, and my independent loop agrees with it.

## Contained defect statement

The instrument is sound on the two failure modes it was repaired for and its coverage/denominator arithmetic is honest.
It is **not yet safe for a quality number**: it still accepts an answer that attributes the call to the wrong callee while
naming the right one as a signature (1d), accepts three natural negations (3.2, 3.3, 3.6), and rejects the natural
correct form `64 of 100 refs` (2.1). Those are the same *classes* the fix targeted, on phrasings it did not cover.
