# ATTACK-GRADE-V5 — an independent adversary's report on `grade_v5.py`

**Unit:** `ATTACK-GRADE-V5` · **Date:** 2026-10-26 · **Inference requests: 0**
**Judge:** [`grade_v5.py`](../longrun/grade_v5.py) — sha256 `1216b2751496eb77ffecc2d503787eda459d1675ea2fc23f0291343f8eb14d15`
**Citation/AST helper:** [`det_verify.py`](../tools/det_verify.py) — sha256 `12ccc74ea31c3843021f1ae6fa771b458082f78393e2117cd86960fd221b6439`
**Probe harness:** [`attack_grade_v5.py`](../tools/attack_grade_v5.py) · **Machine-readable:** [`attack-grade-v5.json`](attack-grade-v5.json)
**Re-run in one command:**

```
python3 experiments/ptr-engine/tools/attack_grade_v5.py
```

It prints the table below, rewrites `attack-grade-v5.json`, and exits **1** while a
defect-class attack is unsatisfied. No model is called; every probe is a literal
string; the judge, its tests (`test_grade_v5.py`), `LR-01.v5.json`, `LR-01.v6.json`,
`det_verify.py` and every row/grade file are read-only to this unit.

---

## 0. Verdict first

| | value |
|---|---|
| **FN** | **0 / 8** should-pass probes were rejected |
| **FP** | **3 / 22** should-fail probes passed |
| Probes | 41 (`P01`–`P41`), 8 with a fixed "must pass", 22 with a fixed "must fail", 11 "observe" |
| Attacks judged **correct** | 1, 2, 3, 4, 6, 9 (six of ten fully correct) |
| Attacks judged **documented limitation** | 5 (no NONE truth exists), 7 (`fail` absorbs "undecidable"), 8 (TEXT immunity holds for text, not for a lying row) |
| Attacks judged **defect** | **10** (our own): the NUM parser truncates a decimal — `ANSWER: 64.99` is graded as `64` and **passes** |

The claim `grade_v5` makes — *truth by AST, a typed value, `TEXT` never passes* —
**survives nine of the ten attacks**, and the one thing that breaks it is not the
citation rule, not negation, not the callee: it is that `det_verify.INT_RE`
(`(?<![\w.])\d+(?![\w])`) has no decimal guard and `answer_slot_end` only ends the
slot at a `.` followed by whitespace, so `64.99` yields the candidate `64`.
Two of the three FPs come from that one hole; the third (`P12`) is a
fixture-declared elision, not a judge bug.

---

## 1. Method — a fixture whose AST truth I control

The card's premise is that a real comparison has not been graded yet, so I could
not probe against it. Instead:

1. `attack_grade_v5.py` writes a temp tree: `resolve.py` (`DEFAULT_MAX_REFS = 64`,
   `_refuse` calling `ledger.record_refusal(scope=scope_name, serialized_ref=text,
   code=error.code)`), `errors.py` (three `Ptr*` classes) and a probe fixture
   `PROBE-LR-01.v5.json`.
2. The fixture's `sources` carry **absolute** paths. `grade_v5._source_map` does
   `os.path.join(dv.ROOT, path)` for any path containing a separator, and an
   absolute second argument wins — so `derive_truth` reads **my** modules, not the
   repo's. The derived truth is printed by the harness (`64`, `3`, the CALL) and
   stored in the JSON, so a later reader can see it was not copied from the fixture.
3. Each probe is a hand-written model reply, graded by the judge's own
   `parse_answer_contract` → `grade_cell` (and, for arm-level facts, `grade_rows`).
   Nothing in the judge is re-implemented or monkeypatched.
4. The temp tree is deleted unless `--keep-temp`; the only repo write is the JSON
   deliverable.

**One asymmetry the card's own probes force me to state up front.** The contract
form is `ANSWER: CALL <callee>(...)`. Several literal probes in the card omit the
`CALL` keyword and the `=` on some kwargs
(`ANSWER: ledger.record_refusal(scope=wrong, serialized_ref, code)`). That string
is not one of the four contract forms, so it fails **on form**
(`not_a_contract_form`), not on value. I therefore test each CALL attack twice:
the card's literal text, and the same intent written in the contract form — because
the question "does a wrong *value* fail?" can only be answered by a string that
parses as a CALL at all.

---

## 2. The ten mandatory attacks

### Attack 1 — citation-numeral trap · **CORRECT**

| probe | expected | observed | defensible? |
|---|---|---|---|
| `P01` `ANSWER: 64 (resolve.py:39)` | pass | `pass` / `num_equal` | yes — the citation span is dropped, `64` is the asserted value |
| `P02` `ANSWER: 39` | fail | `fail` / `num_mismatch` | yes |
| `P03` `ANSWER: NUM 64 (resolve.py:39)` | pass | `pass` / `num_equal` | yes |
| `P04` `ANSWER: 39 (resolve.py:64)` | fail | `fail` / `num_mismatch` | yes — the *cited* numeral is the right value and still loses |

`det_verify`'s cited failure ("a citation numeral was read as the answer") does not
reproduce through v5: `asserted_number` takes the first survivor in the leading
clause, and the citation spans remove `39`/`resolve.py:64` before selection.

### Attack 2 — negation inversion · **CORRECT**

| probe | expected | observed | defensible? |
|---|---|---|---|
| `P05` `ANSWER: do NOT call ledger.record_refusal(scope, serialized_ref, code)` | fail | `fail` / `answer_not_contract` (`not_a_contract_form`) | yes, but for the *form* reason: v5 has no negation rule and does not need one — prose after `ANSWER:` that is not a callee-first CALL never parses |
| `P06` `ANSWER: CALL do NOT call ledger.record_refusal(scope, serialized_ref, code)` | fail | `fail` / `call_not_parsable` | yes — the denial cannot survive the `^callee\(` shape |
| `P07` `never call the retry loop twice.` ⏎ `ANSWER: CALL ledger.record_refusal(...)` | pass | `pass` / `call_equal` | yes — the asymmetry control: an unrelated `never` outside the graded line is never read |
| `P08` `ANSWER: CALL ledger.record_refusal(...) - avoid the retry loop.` | observe | `fail` / `call_not_parsable` | yes — the fixture's system prompt says *"emit exactly ONE line and nothing else"*, so same-line trailing prose is out of contract. (The judge's docstring says prose "before or after the single ANSWER line" is tolerated — that tolerance is about *lines*, and this probe sharpens the wording.) |

The inversion cannot pass: a denial and a `CALL` value are disjoint shapes. The
`det_verify` "`avoid calling …` accepted" defect is structurally absent here.

### Attack 3 — wrong value, right shape · **CORRECT**

| probe | expected | observed | defensible? |
|---|---|---|---|
| `P09` `ANSWER: ledger.record_refusal(scope=wrong, serialized_ref, code)` (card's literal text) | fail | `fail` / `answer_not_contract` (`not_a_contract_form`) | yes, but the rejection is **shape**, not value: no `CALL` keyword, and `serialized_ref` has no `=` |
| `P10` `ANSWER: CALL ledger.record_refusal(scope=wrong, serialized_ref=text, code=error.code)` | fail on value | `fail` / `kwarg_value_mismatch:scope` | yes — the value rule is what fires |
| `P11` `…serialized_ref=wrong…` | fail on value | `fail` / `kwarg_value_mismatch:serialized_ref` | yes |
| `P12` `…scope=..., serialized_ref=text, code=error.code` | fail | **`pass` / `call_equal`** | **FP, but fixture-declared:** the fixture's `expected` documents `scope=...`, so `...` is an authorised elision (`grade_cell` line 385). The judge cannot require a value the fixture elides — but it also cannot tell "the fixture elided this" from "the model declined to answer it". |

### Attack 4 — right tokens, wrong callee · **CORRECT**

| probe | expected | observed | defensible? |
|---|---|---|---|
| `P13` `ANSWER: CALL ledger.write_audit(...)` (name exists only in my docstring) | fail | `fail` / `callee_mismatch` | yes |
| `P14` right callee, `code` kwarg dropped | fail | `fail` / `kwarg_set_mismatch` | yes |
| `P15` `ANSWER: CALL self.record_refusal(...)` | fail | `fail` / `callee_mismatch` | yes — receiver graded exactly |

### Attack 5 — docstring/string occurrence for a `NONE` item · **DOCUMENTED LIMITATION**

Three separate facts, all measured:

1. **A string occurrence is never evidence.** I built a second temp module whose
   `_refuse` mentions `ledger.record_refusal(scope=…, serialized_ref=…, code=…)`
   **only inside a docstring**. `det_verify.call_inside_function` on it raises
   `expected exactly one record_refusal() call in _refuse, found 0` — `ast.walk`
   sees `ast.Call`, never `ast.Constant`. So a docstring/string mention **cannot**
   flip a verdict, in either direction.
2. **A `NONE` truth cannot be declared at all.** Adding a checkpoint with
   `answer_spec.kind = "NONE"` aborts the whole run:
   `fixture_truth_mismatch: atk.none has no usable answer_spec`
   (`derive_truth` handles only `NUM` and `CALL`). The `ANSWER: NONE` form is in the
   contract and in the fixture's system prompt, but **no fixture can express a
   truth for it**.
3. **The NONE pass branch is unreachable dead code.** Hand-building the truth
   (`{"kind":"NONE","call_present":False}`) does yield
   `pass` / `none_confirmed_absent_in_source` — proof the branch exists and would
   pass a correct NONE — but `derive_truth` can never produce that truth, because
   the only derivation it offers (`call_inside_function`) *raises* when the call is
   absent instead of returning "absent".

Can it flip a verdict? **No.** It fails closed: a NONE checkpoint aborts grading
loudly rather than mis-grading. But the contract advertises a form the judge cannot
grade, and `checkpoint_accuracy` has no NONE cells by construction. If a future
fixture adds one, the run dies — safe, but the operator must know before a live cell.

### Attack 6 — format tolerance, both ways · **CORRECT**

| probe | observed | defensible? |
|---|---|---|
| `P17` `ANSWER:64` | `pass` / `num_equal` | yes — `[ \t]*` in the marker regex |
| `P18` `ANSWER: 64.` | `pass` / `num_equal` | yes — the period ends the answer slot at `.`+EOL |
| `P20` `ANSWER: 64. The default is defined in resolve.py; see line 39.` | `pass` / `num_equal` | yes — slot ends at the first `.`+space; the stale `39` is also swallowing by the citation rule |
| `P19` `answer: 64` (lowercase marker) | `fail` / `no_answer_line` | defensible: the contract line is uppercase `ANSWER:` in the fixture prompt; the regex is case-sensitive and says so nowhere |
| `P21` `ANSWER: The default is 64.` | `fail` / `not_a_contract_form` | defensible: four forms only; a numeral wrapped in prose is not `NUM` |
| `P22` `  ANSWER: 64` (indented) | `fail` / `no_answer_line` | defensible but **worth writing down**: `^ANSWER:` is column-0 anchored |
| `P23` `**ANSWER: 64**` (markdown) | `fail` / `no_answer_line` | same column-0 anchoring |
| `P24` `ANSWER: ledger.record_refusal(...)` (no `CALL` keyword) | `fail` / `not_a_contract_form` | defensible: the form is `ANSWER: CALL <callee>(...)` — and note the fixture's *documented* `expected` string is this bare shape, so a model copying the documentation rather than the contract line is rejected |
| `P25` `…serialized_ref='text'…` (quoted value) | `fail` / `kwarg_value_mismatch:serialized_ref` | defensible: "give each value as the source text shows it" |

### Attack 7 — the empty / absent answer · **DOCUMENTED LIMITATION**

| state | observed | right? |
|---|---|---|
| no `ANSWER:` line (`P26`) | cell `fail` / `answer_not_contract`, `answer_parse_error = no_answer_line` | non-pass: yes. But it lands in **`fail`**, not in an undecidable/missing state — v5 has no such state |
| pure prose (`P26` is this case; also `P21`) | same | as above |
| `ANSWER:` with nothing after it (`P27`) | `fail` / `answer_not_contract`, `answer_parse_error = empty_answer` | non-pass: yes; state: **`fail`** |
| `ANSWER:   ` whitespace only (`P28`) | same as `P27` | **`fail`** |
| turn absent from the rows | `fail` / `turn_missing` | **`fail`** — the only non-answer state with its own name |

Arm-level measurement (`grade_rows`, 3 checkpoints):

| arm | `checkpoint_accuracy` | `decidable` | `text_reported` | `verified_success` |
|---|---|---|---|---|
| all three answered correctly | 3/3 | 3 | 0 | **true** |
| one turn missing | 2/3 | **3** | 0 | false |
| one answer is prose only | 2/3 | **3** | 0 | false |
| every answer empty (`ANSWER:`) | 0/3 | **3** | 0 | false |
| one answer is `TEXT` | 2/3 | 3 | 1 | false |

**The denominator question, answered precisely.** No denominator is *inflated*: the
accuracy denominator is the fixed checkpoint count, and a missing answer cannot
become a pass. `verified_success` stays fail-closed — which is what the operator's
comparison needs. But the field **`decidable` counts cells where nothing was
decided**: in the missing-turn arm it reads `3`, and in the empty-answer arm `3`.
`failing_reasons` also collapses every parse error to `answer_not_contract`; the
specific parse error survives only in the per-cell `answer_parse_error`. So an arm
whose context overflowed (no answer) is indistinguishable from an arm that answered
wrongly, in the aggregate a reader is given. In FN/FP accounting against human
truth, that folding counts *formatting/absence* as *knowledge* failure — FN
inflation by construction. This is why I call it a limitation that must be written
down (or the field renamed `cells` and a real `undecidable` verdict added), not a
pass I can certify.

### Attack 8 — `TEXT` immunity · **LIMITATION (text path correct; row path not)**

| probe | observed |
|---|---|
| `P29` `ANSWER: TEXT the default is 64` (NUM truth) | verdict **`text`** / `text_not_auto_passed` — not a pass |
| `P30` `ANSWER: TEXT 64` (CALL truth) | `text` / `text_not_auto_passed` |
| `P31` `ANSWER: TEXT` (empty body) | `fail` / `empty_text` |

`grade_cell` returns `verdict = "text"` before any comparison, so **no textual
`TEXT` answer can pass**, on any checkpoint kind. Confirmed on both NUM and CALL
truths, and by code inspection: the only `pass` assignments are `num_equal`,
`call_equal`, and the unreachable `none_confirmed_absent_in_source`.

**The caveat that keeps this short of "correct":** `grade_rows` grades a row's
**parsed fields** when present, not its `content` (`_parsed_from_row`). A row
carrying `answer_kind="NUM", answer_value=64` with `content = "ANSWER: TEXT the
default is 64"` grades **`pass` / `num_equal`** (the `row_says_num` arm above). So
`TEXT never passes` is true of *answers* and false of *rows*. Reachability: the
shipped runner imports the same parser (`run_longrun.py:57`:
`from grade_v5 import parse_answer_contract`), so its rows cannot diverge; the hole
needs a different row producer or a hand-edited row file. Recorded as a trust
boundary, not a live defect.

### Attack 9 — numeric equivalence · **CORRECT (with two undocumented edges)**

| probe | truth | observed | is the rule stated? |
|---|---|---|---|
| `P32` `ANSWER: 0x40` | 64 | `fail` / `not_a_contract_form` (`^NUM_HEAD_RE` needs `\d+\b`; `0x40` has no boundary) | the contract says `<integer>`; "decimal only" is **not** stated anywhere |
| `P33` `ANSWER: NUM 0x40` | 64 | `fail` / `num_not_found` (`INT_RE`'s lookarounds reject both `0` and `40` in `0x40`) | same |
| `P34` `ANSWER: 64.0` | 64 | **`pass` / `num_equal`** | not stated anywhere — it passes because the decimal is silently discarded |
| `P35` `ANSWER: sixty-four` | 64 | `fail` / `not_a_contract_form` | `<integer>` covers this |
| `P36` `ANSWER: 640` | 64 | `fail` / `num_mismatch` | yes — no prefix matching |

The hex/word rejections are a defensible reading of `<integer>` *if written down*
(they are not). `64.0` passing is numerically right but by accident of the same
mechanism that makes `64.99` pass — see attack 10.

### Attack 10 — a pass that should be a fail, our own · **DEFECT**

| probe | truth | expected | observed | verdict |
|---|---|---|---|---|
| `P37` `ANSWER: 64.99` | 64 | fail | **`pass` / `num_equal`** | **defect** |
| `P38` `ANSWER: NUM 64.999` | 64 | fail | **`pass` / `num_equal`** | **defect** |

Mechanism, from the code: `INT_RE = re.compile(r"(?<![\w.])\d+(?![\w])")` has no
decimal-tail guard (`(?![.\d])` would be enough), and `answer_slot_end` ends the
slot only at `\.(?=\s|$)`, which `64.99` never satisfies — so the first candidate
`64` sits in the slot and wins. Every other wrong-value probe I wrote
(`P02`, `P04`, `P36`) is rejected, and the TEXT probe `P30` is reported as `text`,
never a pass; this one is not.

**Why it matters for the operator's comparison:** `verified_success` is
`not failed and not text_cells`. A NUM checkpoint answered `64.99` is `pass`, so an
arm that asserts a wrong number can still be reported *verified* — the very gate
the comparison rests on. The severity is bounded by plausibility: the NUM
checkpoints ask for integer values (`DEFAULT_MAX_REFS`, a class count), and `64.99`
is not a plausible answer to either. It is a defect, not a catastrophe.

Also recorded under this attack (all fail, none is a defect):
`P39` `ANSWER: 64%; the previous value was 31` → `pass` (the stale `31` is outside
the slot — correct); `P40` `ANSWER: 39` ⏎ `ANSWER: 64` → `fail` /
`multiple_answer_lines` (a *corrected* answer fails — stated in the docstring);
`P41` the same correct line twice → `fail` / `multiple_answer_lines` (stated, and
strictly consistent with "exactly ONE line").

---

## 3. FN / FP over the probe set

**Denominators.** 41 probes: **8** with a fixed "must pass" expectation, **22**
with a fixed "must fail", **11** "observe" (the card asks what happens rather than
asserting an outcome; they are excluded from FN/FP and reported in §2/§4).

- **FN = 0 / 8.** Every correct answer in the contract's own form passed:
  `P01, P03, P07, P16, P17, P18, P20, P39`. The two near-misses are correct *values*
  in out-of-contract *forms*: `P24` (correct call, `CALL` keyword omitted) and
  `P34` (`64.0` passes anyway). Neither is counted as FN because the contract form
  is normative and published in the fixture's system prompt — but `P24` is the one
  I would watch in a live run, because the fixture documents its own `expected`
  string in that bare shape.
- **FP = 3 / 22**: `P37` and `P38` (the decimal hole — genuine, attack 10), and
  `P12` (the fixture-declared `scope=...` elision — a pass on an unstated value,
  authored by the fixture, not by the parser).

Compared with the predecessor rates the card quotes (`grade_v3` FN 30.8 % / FP
45.5 %, `grade_v4` FN 26.9 % / FP 50.0 % against `grader_fitness.py`), **these are
not the same measurement** and must not be subtracted from them: mine are 41
hand-written probes on a synthetic fixture, not the fitness corpus. What they
license is narrower and stronger: *on the ten attacks, the v5 contract holds
except for non-integer NUM.*

---

## 4. Every probe, with the observed reason

| id | attack | truth | answer (truncated to 58 chars) | expected | observed | counted |
|---|---|---|---|---|---|---|
| P01 | 1 | NUM | `ANSWER: 64 (resolve.py:39)` | pass | pass/num_equal | |
| P02 | 1 | NUM | `ANSWER: 39` | fail | fail/num_mismatch | |
| P03 | 1 | NUM | `ANSWER: NUM 64 (resolve.py:39)` | pass | pass/num_equal | |
| P04 | 1 | NUM | `ANSWER: 39 (resolve.py:64)` | fail | fail/num_mismatch | |
| P05 | 2 | CALL | `ANSWER: do NOT call ledger.record_refusal(scope, serialized_ref, code)` | fail | fail/answer_not_contract | |
| P06 | 2 | CALL | `ANSWER: CALL do NOT call ledger.record_refusal(...)` | fail | fail/call_not_parsable | |
| P07 | 2 | CALL | `never call the retry loop twice.` + correct CALL | pass | pass/call_equal | |
| P08 | 2 | CALL | correct CALL + ` - avoid the retry loop.` | observe | fail/call_not_parsable | |
| P09 | 3 | CALL | `ANSWER: ledger.record_refusal(scope=wrong, serialized_ref, code)` | fail | fail/not_a_contract_form | |
| P10 | 3 | CALL | `ANSWER: CALL ledger.record_refusal(scope=wrong, …)` | fail | fail/kwarg_value_mismatch:scope | |
| P11 | 3 | CALL | `ANSWER: CALL …serialized_ref=wrong…` | fail | fail/kwarg_value_mismatch:serialized_ref | |
| P12 | 3 | CALL | `ANSWER: CALL …scope=...…` | fail | **pass/call_equal** | **FP** |
| P13 | 4 | CALL | `ANSWER: CALL ledger.write_audit(…)` | fail | fail/callee_mismatch | |
| P14 | 4 | CALL | `ANSWER: CALL ledger.record_refusal(scope=…, serialized_ref=text)` | fail | fail/kwarg_set_mismatch | |
| P15 | 4 | CALL | `ANSWER: CALL self.record_refusal(…)` | fail | fail/callee_mismatch | |
| P16 | 0 | CALL | correct CALL (baseline) | pass | pass/call_equal | |
| P17 | 6 | NUM | `ANSWER:64` | pass | pass/num_equal | |
| P18 | 6 | NUM | `ANSWER: 64.` | pass | pass/num_equal | |
| P19 | 6 | NUM | `answer: 64` | observe | fail/no_answer_line | |
| P20 | 6 | NUM | `ANSWER: 64. The default is defined in resolve.py; see line 39.` | pass | pass/num_equal | |
| P21 | 6 | NUM | `ANSWER: The default is 64.` | observe | fail/not_a_contract_form | |
| P22 | 6 | NUM | `  ANSWER: 64` | observe | fail/no_answer_line | |
| P23 | 6 | NUM | `**ANSWER: 64**` | observe | fail/no_answer_line | |
| P24 | 6 | CALL | `ANSWER: ledger.record_refusal(…)` (no `CALL`) | observe | fail/not_a_contract_form | |
| P25 | 6 | CALL | `ANSWER: CALL …serialized_ref='text'…` | observe | fail/kwarg_value_mismatch:serialized_ref | |
| P26 | 7 | NUM | `The default budget is 64 refs.` | fail | fail/no_answer_line | |
| P27 | 7 | NUM | `ANSWER:` | fail | fail/empty_answer | |
| P28 | 7 | NUM | `ANSWER:    ` | fail | fail/empty_answer | |
| P29 | 8 | NUM | `ANSWER: TEXT the default is 64` | fail | **text**/text_not_auto_passed | |
| P30 | 8 | CALL | `ANSWER: TEXT 64` | fail | text/text_not_auto_passed | |
| P31 | 8 | NUM | `ANSWER: TEXT` | fail | fail/empty_text | |
| P32 | 9 | NUM | `ANSWER: 0x40` | observe | fail/not_a_contract_form | |
| P33 | 9 | NUM | `ANSWER: NUM 0x40` | observe | fail/num_not_found | |
| P34 | 9 | NUM | `ANSWER: 64.0` | observe | pass/num_equal | |
| P35 | 9 | NUM | `ANSWER: sixty-four` | observe | fail/not_a_contract_form | |
| P36 | 9 | NUM | `ANSWER: 640` | fail | fail/num_mismatch | |
| P37 | 10 | NUM | `ANSWER: 64.99` | fail | **pass/num_equal** | **FP** |
| P38 | 10 | NUM | `ANSWER: NUM 64.999` | fail | **pass/num_equal** | **FP** |
| P39 | 10 | NUM | `ANSWER: 64%; the previous value was 31` | pass | pass/num_equal | |
| P40 | 10 | NUM | `ANSWER: 39` ⏎ `ANSWER: 64` | fail | fail/multiple_answer_lines | |
| P41 | 10 | NUM | `ANSWER: 64` ⏎ `ANSWER: 64` | fail | fail/multiple_answer_lines | |

`observed` is `verdict/reason`; where the reason is `answer_not_contract` the
parenthesis in §2/§4 names the parse error (`answer_parse_error`) that caused it.

---

## 5. What this judge cannot be trusted to decide

Written as limits on the operator's comparison, not as style notes.

1. **A non-integer NUM answer.** `64.99` grades as `64`. A wrong value can pass and
   can therefore produce `verified_success = true`. **Repair before a live
   comparison that can emit a decimal.** No one-character fix is safe: adding `.`
   to `INT_RE`'s lookahead also kills the tolerated `ANSWER: 64.` (`P18`) unless
   the slot-end rule runs first; the cheapest correct repair is to reject a `NUM`
   body that matches `\d+\.\d` (`empty_num`-style) instead of truncating it.
2. **"Did the model know it, or did it fail the format?"** Every
   `answer_not_contract`, `no_answer_line`, `empty_answer`, `multiple_answer_lines`
   and `turn_missing` lands in `verdict = "fail"`, inside a `decidable` count that
   includes it. The judge cannot tell the operator *why* an arm lost a checkpoint,
   so it cannot support any claim of the form "at equal-or-better verified
   quality" when one arm's losses are formatting and the other's are knowledge.
   It can support "verified_success", which is fail-closed.
3. **`NONE`.** The `ANSWER: NONE` form is advertised and cannot be graded: no
   fixture can declare a NONE truth, and `call_inside_function` raises rather than
   reporting absence. A NONE checkpoint aborts the run
   (`fixture_truth_mismatch`). Do not build one without repairing `derive_truth`.
4. **A row whose parsed fields disagree with its content.** `grade_rows` trusts
   `answer_kind`/`answer_value` over `content`, so the TEXT-immunity invariant is a
   property of textual answers only. Safe with the shipped runner (same parser,
   `run_longrun.py:57`); not safe for a hand-edited or third-party row file.
5. **Semantic equality of values.** `serialized_ref='text'` (quoted) is a value
   mismatch; whitespace is normalised, nothing else is. Also `scope=...` passes
   where the fixture elides a value. Both are defensible contract readings; neither
   is written where a reader of the *judge* (as opposed to the fixture prompt)
   would find it. The contract text lives in the fixture's `system_prompt` and
   `answer_contract`, not in [`grade_v5.py`](../longrun/grade_v5.py) — the module
   docstring lists the four forms but not the exact-form consequences (column-0
   marker, uppercase `ANSWER:`, no trailing same-line prose, decimal rejection).
6. **Anything outside these ten attacks.** I did not probe `count_classes` against
   adversarial class-name patterns, nor the `--red` self-test, nor a real row file;
   `det_verify`'s citation rule was exercised only through the two citation probes.

---

## 6. Appendix A — exact probe texts

```
P01  ANSWER: 64 (resolve.py:39)
P02  ANSWER: 39
P03  ANSWER: NUM 64 (resolve.py:39)
P04  ANSWER: 39 (resolve.py:64)
P05  ANSWER: do NOT call ledger.record_refusal(scope, serialized_ref, code)
P06  ANSWER: CALL do NOT call ledger.record_refusal(scope, serialized_ref, code)
P07  never call the retry loop twice.
     ANSWER: CALL ledger.record_refusal(scope=scope_name, serialized_ref=text, code=error.code)
P08  ANSWER: CALL ledger.record_refusal(scope=scope_name, serialized_ref=text, code=error.code) - avoid the retry loop.
P09  ANSWER: ledger.record_refusal(scope=wrong, serialized_ref, code)
P10  ANSWER: CALL ledger.record_refusal(scope=wrong, serialized_ref=text, code=error.code)
P11  ANSWER: CALL ledger.record_refusal(scope=scope_name, serialized_ref=wrong, code=error.code)
P12  ANSWER: CALL ledger.record_refusal(scope=..., serialized_ref=text, code=error.code)
P13  ANSWER: CALL ledger.write_audit(scope=scope_name, serialized_ref=text, code=error.code)
P14  ANSWER: CALL ledger.record_refusal(scope=scope_name, serialized_ref=text)
P15  ANSWER: CALL self.record_refusal(scope=scope_name, serialized_ref=text, code=error.code)
P16  ANSWER: CALL ledger.record_refusal(scope=scope_name, serialized_ref=text, code=error.code)
P17  ANSWER:64
P18  ANSWER: 64.
P19  answer: 64
P20  ANSWER: 64. The default is defined in resolve.py; see line 39.
P21  ANSWER: The default is 64.
P22    ANSWER: 64
P23  **ANSWER: 64**
P24  ANSWER: ledger.record_refusal(scope=scope_name, serialized_ref=text, code=error.code)
P25  ANSWER: CALL ledger.record_refusal(scope=scope_name, serialized_ref='text', code=error.code)
P26  The default budget is 64 refs.
P27  ANSWER:
P28  ANSWER:    \n\n          (marker, then spaces and blank lines)
P29  ANSWER: TEXT the default is 64
P30  ANSWER: TEXT 64
P31  ANSWER: TEXT
P32  ANSWER: 0x40
P33  ANSWER: NUM 0x40
P34  ANSWER: 64.0
P35  ANSWER: sixty-four
P36  ANSWER: 640
P37  ANSWER: 64.99
P38  ANSWER: NUM 64.999
P39  ANSWER: 64%; the previous value was 31
P40  ANSWER: 39
     ANSWER: 64
P41  ANSWER: 64
     ANSWER: 64
```

Truths used: `atk.num` = `64` (`DEFAULT_MAX_REFS`, `ast.Assign`),
`atk.count` = `3` (`count_classes(^Ptr\w*$)`, three `ast.ClassDef`),
`atk.call` = `ledger.record_refusal(scope=scope_name, serialized_ref=text,
code=error.code)` (`ast.Call` in `_refuse`, docstring mentions deliberately
present in the same module).

## 7. Appendix B — why the temp fixture is enough (and what it is not)

`grade_v5._source_map` builds `os.path.join(dv.ROOT, path)` for any `sources[].path`
containing `os.sep`; `os.path.join("/repo", "/tmp/x/resolve.py")` is
`"/tmp/x/resolve.py"`. So the fixture's truth is read from the temp tree, printed
by the harness, and cross-checked against my fixture's documented `expected` — which
means a divergence would have aborted (`fixture_truth_mismatch`) rather than
silently grading the wrong value. That is exactly what happened on my first run of
the `NONE` checkpoint, which is the evidence for §2 attack 5.

What it is **not**: a measurement of the judge against real model answers, or
against `grader_fitness.py`'s corpus. The FN/FP numbers above are counts over 41
hand-written strings and nothing else.
