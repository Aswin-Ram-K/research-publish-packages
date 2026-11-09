# ERA-B-GRADE-REHEARSAL — does the grader accept a correct era-B answer?

**Unit:** `ERA-B-GRADE-REHEARSAL` · **Date:** 2026-10-26 · **Live requests spent: 0** (offline, zero
sockets, no live endpoint contact, no `cell.py` edit).
**Artifact of record:** [`measure/ERA-B-GRADE-REHEARSAL.json`](../measure/ERA-B-GRADE-REHEARSAL.json) ·
**Code:** [`tests/test_era_b_grade_rehearsal.py`](../tests/test_era_b_grade_rehearsal.py) (8 tests).

**Verdict: `contract_rejects_correct_era_b_answer`.** The grid's quality precondition **fails**.

## 0 · What was loaded

| what | value | source |
|---|---|---|
| grader | `experiments/ptr-engine/longrun/grade_v5.py` | sha256 `056eb605e2baf5c91e0cb32d037cd0528e406e6c8527eec55a917a52d9f26772` — **matches the card** |
| grader version | `5.1` | `grade_v5.GRADER_VERSION` (`grade_v5.py:57`), recorded at runtime |
| rule | `ANSWER-CONTRACT v1` | `grade_v5.RULE` (`grade_v5.py:54`) |
| fixture | `experiments/ptr-engine/longrun/tasks-v6/LR-01.v8.json` | sha256 `0804b51575cce345…` (full value in the JSON) |
| truth | 12 cells from `grade_v5.derive_truth(fixture)` | **no hand-typed table** |

Truth is derived, never typed: each expected value below quotes the derivation line
`derive_truth` returned, and `derive_truth` itself aborts (`fixture_truth_mismatch`) if the
fixture's human `expected` string diverges from the AST (`grade_v5.py:446-453`, `:475`).

## 1 · The 12 ids, by kind (NUM 5 · CALL 4 · NONE 3)

| id | kind | expected (derived) | derivation source line |
|---|---|---|---|
| `cp.0.t06` | CALL | `ledger.record_resolution(block_size=scope.block(), bytes_appended=len(presented.encode('utf-8')), entry_text=entry.text, scope=scope.name, serialized_ref=presented)` | `experiments/ptr-engine/ptr_engine/resolve.py:159 ast.Call inside resolve -> ledger.record_resolution(scope=scope.name, serialized_ref=presented, bytes_appended=len(presented.encode('utf-8')), block_size=scope.block(), entry_text=entry.text)` |
| `cp.1.t08` | CALL | `scope.block()` | `experiments/ptr-engine/ptr_engine/resolve.py:163 ast.Call inside resolve -> scope.block()` |
| `cp.2.t12` | NUM | `64` | `experiments/ptr-engine/ptr_engine/resolve.py:39 ast.Assign DEFAULT_MAX_REFS = 64` |
| `cp.3.t14` | NONE | `NONE` | `experiments/ptr-engine/ptr_engine/resolve.py ast.Call *.record_refusal inside resolve -> absent` |
| `cp.4.t18` | NUM | `6` | `experiments/ptr-engine/ptr_engine/errors.py:176-211 ast.ClassDef count(^PtrLedger\w*$) = 6` |
| `cp.5.t20` | NONE | `NONE` | `experiments/ptr-engine/ptr_engine/resolve.py ast.Call *.resolved_count inside _refuse -> absent` |
| `cp.6.t24` | NUM | `31` | `experiments/ptr-engine/ptr_engine/errors.py:15-247 ast.ClassDef count(^Ptr\w*$) = 31` |
| `cp.7.t26` | NUM | `5` | `experiments/ptr-engine/ptr_engine/errors.py:217-247 ast.ClassDef count(^PtrLaw\w*$) = 5` |
| `cp.8.t32` | NUM | `2` | `experiments/ptr-engine/ptr_engine/errors.py:36-42 ast.ClassDef count(^PtrUnknown\w*$) = 2` |
| `cp.9.t36` | CALL | `ledger.resolved_count()` | `experiments/ptr-engine/ptr_engine/resolve.py:141 ast.Call (line-pinned) -> ledger.resolved_count()` |
| `cp.10.t42` | NONE | `NONE` | `experiments/ptr-engine/ptr_engine/resolve.py ast.Call *.block inside _refuse -> absent` |
| `cp.11.t46` | CALL | `ledger.record_refusal(code=error.code, scope=scope_name, serialized_ref=text)` | `experiments/ptr-engine/ptr_engine/resolve.py:69 ast.Call inside _refuse -> ledger.record_refusal(scope=scope_name, serialized_ref=text, code=error.code)` |

Two fixture elisions matter for grading: `cp.0.t06` declares `bytes_appended` and `entry_text` elided
(`...`), and `cp.11.t46` declares `scope` elided — `grade_cell` accepts either the source text or `...`
for those names (`grade_v5.py:686-687`).

## 2 · Method

Every answer below was built **from the derived truth**, parsed with
`grade_v5.parse_answer_contract` and graded with `grade_v5.grade_cell` against the derived cell. No
contract rule was re-implemented; `grade_v5.py` was not edited. Because every row asserts the *true*
value, **any non-pass is a rejection of a correct answer**.

Shapes rehearsed (card shape → ids):

| label | shape | ids |
|---|---|---|
| `a` | the fixture's own canonical form, kwargs alphabetical | all 12 |
| `b` | canonical + sentence-final period | all 12 |
| `c` | two lines: `ANSWER:` first, one-line justification after | all 12 |
| `d` | short tool-use narration line (`Read `resolve.py:36-110`.`), then the answer | all 12 |
| `e1` | CALL, kwargs in reverse alphabetical order | 4 CALL |
| `e2` | `e1` **plus** the provenance detail appended after the closing paren | 4 CALL |
| `f` | `ANSWER: NONE — the source defines no such call` | 3 NONE |
| `g` | NUM + trailing provenance citation (the contract's own `ANSWER: 6 (scope.py:3)` case) | 5 NUM |

`not_rehearsed: []` — every requested shape was constructible. 64 correct-answer rows in total.

## 3 · The matrix (`P` pass · `F` fail · `U` undecidable · `·` shape does not apply)

| id | kind | expected | a | b | c | d | e1 | e2 | f | g |
|---|---|---|---|---|---|---|---|---|---|---|
| `cp.0.t06` | CALL | `ledger.record_resolution()` | P | F | P | P | P | F | · | · |
| `cp.1.t08` | CALL | `scope.block()` | P | F | P | P | P | F | · | · |
| `cp.2.t12` | NUM | `64` | P | P | P | P | · | · | · | P |
| `cp.3.t14` | NONE | `NONE` | P | U | P | P | · | · | F | · |
| `cp.4.t18` | NUM | `6` | P | P | P | P | · | · | · | P |
| `cp.5.t20` | NONE | `NONE` | P | U | P | P | · | · | F | · |
| `cp.6.t24` | NUM | `31` | P | P | P | P | · | · | · | P |
| `cp.7.t26` | NUM | `5` | P | P | P | P | · | · | · | P |
| `cp.8.t32` | NUM | `2` | P | P | P | P | · | · | · | P |
| `cp.9.t36` | CALL | `ledger.resolved_count()` | P | F | P | P | P | F | · | · |
| `cp.10.t42` | NONE | `NONE` | P | U | P | P | · | · | F | · |
| `cp.11.t46` | CALL | `ledger.record_refusal()` | P | F | P | P | P | F | · | · |

Totals: **50 / 64 correct rows pass; 14 do not** (11 of them are card-required shapes). Per shape:
`a` 12/12 · `c` 12/12 · `d` 12/12 · `e1` 4/4 · `g` 5/5 pass; `b` 5 pass / 4 fail / 3 undecidable;
`e2` 0/4; `f` 0/3.

**The channel fix works.** The era-B turn shape a model actually emits — a tool-narration line followed
by the contract line (`d`), a two-line answer (`c`), and the canonical one-liner (`a`) — is accepted at
**all 12** checkpoints, including the tool-call-then-answer shape that era A never produced. A CALL with
reordered kwargs (`e1`) is also accepted at all 4.

## 4 · Verbatim reasons for every rejected correct shape

| shape | affected ids | reason string (verbatim, from `grade_cell`) |
|---|---|---|
| `b` trailing period, CALL | `cp.0.t06`, `cp.1.t08`, `cp.9.t36`, `cp.11.t46` | `answer_not_contract:call_not_parsable` |
| `b` trailing period, NONE | `cp.3.t14`, `cp.5.t20`, `cp.10.t42` | `unparseable` *(verdict `undecidable`, not `fail` — but never a pass)* |
| `e2` reordered + provenance, zero-kwarg CALL | `cp.1.t08`, `cp.9.t36` | `answer_not_contract:call_arg_not_kwarg:) (resolve.py:163` / `…) (resolve.py:141` |
| `e2` reordered + provenance, multi-kwarg CALL | `cp.0.t06`, `cp.11.t46` | `kwarg_value_mismatch:block_size` / `kwarg_value_mismatch:code` |
| `f` NONE + em-dash justification | `cp.3.t14`, `cp.5.t20`, `cp.10.t42` | `answer_not_contract:trailing_after_none` |

Mechanism, read off the code: `CALL_RE` (`grade_v5.py:69`) pins the call to `\)\s*$`, so a period after
the closing paren breaks the parse; `parse_answer_contract` requires `head == "NONE"` with an **empty**
`rest` (`grade_v5.py:228-233`), so any justification is `trailing_after_none`; and unlike NUM — where
`det_verify.asserted_number` drops a trailing citation — `_parse_call` (`grade_v5.py:155`) has no
citation rule, so `header:` text after the call either becomes a non-kwarg argument or is folded into
the **last** kwarg's value.

## 5 · Negative controls — none passes

| control | id attacked | verdict | reason (verbatim) |
|---|---|---|---|
| wrong number `ANSWER: NUM 32` | `cp.2.t12` | fail | `num_mismatch` |
| wrong callee `ledger.record_resolved(...)` | `cp.0.t06` | fail | `callee_mismatch` |
| wrong keyword value `block_size=64` | `cp.0.t06` | fail | `kwarg_value_mismatch:block_size` |
| truncated `ANSWER: CALL ledger.record_resolution(scope=scope.name` | `cp.0.t06` | fail | `answer_not_contract:call_not_parsable` |
| truncated `ANSWER: NUM` | `cp.2.t12` | undecidable | `empty_num` |
| prose asserting a wrong value, no `ANSWER:` line | `cp.2.t12` | undecidable | `prose_only` |
| `NONE` item answered by naming a call (×3) | `cp.3.t14`, `cp.5.t20`, `cp.10.t42` | fail | `kind_mismatch:NONE_expected` |

The grader is **not** permissive: 0 of 9 wrong answers passes. The two `undecidable` controls are the
deliberate repair-T3 rule (`grade_v5.py:595-606`): an answer that expresses no typed value has nothing
to grade and is excluded from the decidable denominator — it is **not** counted as a pass, and it
inflates no accuracy figure.

## 6 · Verdict, and what it sentences

**`contract_rejects_correct_era_b_answer`.** The grid's quality precondition — every correct era-B
answer passes — **does not hold**: 14 of 64 correct rows are non-pass, 11 of them in shapes the card
requires.

One sentence each, as required (nothing was fixed here; repairs are `GRADE-V5-REPAIR`'s):

- **`e2` (CALL + trailing provenance citation)** is a **grader-rule problem**: the fixture's own system
  prompt states *"A citation written after the value is allowed and is not the value"* and
  `det_verify.asserted_number` strips citations for NUM, but grade_v5 has no CALL equivalent — the fix
  is to strip a trailing parenthetical citation before `_parse_call`, in
  `experiments/ptr-engine/longrun/grade_v5.py`.
- **`b` (trailing period on CALL/NONE)** is a **grader-rule problem**: `_integral_numeral` already
  treats a sentence-final period as punctuation for NUM, but `_parse_call`'s `\)\s*$` and NONE's exact
  head match do not — the same strip belongs in `experiments/ptr-engine/longrun/grade_v5.py`.
- **`f` (NONE + em-dash justification)** is a **fixture-wording problem**: the fixture's form is the
  bare `ANSWER: NONE`, and the parser enforces it — the fixture contract line in
  `experiments/ptr-engine/longrun/tasks-v6/LR-01.v8.json` (`system_prompt`) is where the allowance
  would have to be stated (or `trailing_after_none` relaxed in `grade_v5.py`).

**Why the grid is at risk.** Era B's channel fix is necessary but not sufficient: the canonical,
two-line and tool-narration-then-answer shapes pass 12/12, so the 0/12 modal reading will not simply
repeat — but on any turn where era B appends a source citation after a CALL value (which the fixture
invites) or writes a sentence-final period, the checkpoint grades `fail`, manufacturing a fifth zero in
a 1,016-request grid. The precondition therefore fails **before** the grid is launched.

## 7 · Reproduce

```
$ python3 tests/test_era_b_grade_rehearsal.py          # rebuilds measure/ERA-B-GRADE-REHEARSAL.json
$ PYTHONPATH=src python3 -m pytest -q tests/test_era_b_grade_rehearsal.py
........                                                                 [100%]
8 passed
```
