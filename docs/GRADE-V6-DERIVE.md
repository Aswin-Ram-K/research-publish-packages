# GRADE-V6-DERIVE — making `LR-01.v6.json` gradeable end to end

Unit `GRADE-V6-DERIVE`. Offline, zero inference requests, no v6 rows created.
`LR-01.v5.json` and `LR-01.v6.json` were **not** edited (the v6 fixture is the gate's
output; the contract is to make the grader able to grade it, not to re-author it).

## 1. The measured gap, re-derived independently

Probing `grade_v5.derive_truth` one checkpoint at a time over
`experiments/ptr-engine/longrun/tasks-v5/runtime-v5/LR-01.v6.json` reproduces the
unit's split **exactly: 8 gradable / 4 not**. No divergence from the unit's report.

| # | id | `answer_spec.kind` | before | after (derived truth) |
|---|----|--------------------|--------|------------------------|
| 1 | `cp.3.t06` | CALL / `call_inside_function` | `ledger.record_resolution(scope=scope.name, serialized_ref=presented, bytes_appended=len(presented.encode('utf-8')), block_size=scope.block(), entry_text=entry.text)` @ `resolve.py:159` | unchanged |
| 2 | `cp.4.t08` | CALL / `call_inside_function` | `scope.block()` @ `resolve.py:163` | unchanged |
| 3 | `cp.0.t12` | NUM / `constant_value` | `64` @ `resolve.py:39` | unchanged |
| 4 | `cp.5.t14` | NONE / `no_attr_call_inside_function` | `SystemExit: fixture_truth_mismatch: cp.5.t14 has no usable answer_spec` | `NONE` — `*.record_refusal` **absent** inside `resolve` (`call_present=False`) |
| 5 | `cp.6.t18` | NUM / `count_classes` | `6` @ `errors.py:176-211` | unchanged |
| 6 | `cp.7.t20` | NONE / `no_attr_call_inside_function` | `SystemExit: fixture_truth_mismatch: cp.7.t20 has no usable answer_spec` | `NONE` — `*.resolved_count` **absent** inside `_refuse` |
| 7 | `cp.1.t24` | NUM / `count_classes` | `31` @ `errors.py:15-247` | unchanged |
| 8 | `cp.8.t26` | NUM / `count_classes` | `5` @ `errors.py:217-247` | unchanged |
| 9 | `cp.9.t32` | NUM / `count_classes` | `2` @ `errors.py:36-42` | unchanged |
| 10 | `cp.10.t36` | CALL / `call_at_line` | `KeyError: 'function'` | `ledger.resolved_count()` @ `resolve.py:141` (line-pinned) |
| 11 | `cp.11.t42` | NONE / `no_attr_call_inside_function` | `SystemExit: fixture_truth_mismatch: cp.11.t42 has no usable answer_spec` | `NONE` — `*.block` **absent** inside `_refuse` |
| 12 | `cp.2.t46` | CALL / `call_inside_function` | `ledger.record_refusal(scope=scope_name, serialized_ref=text, code=error.code)` @ `resolve.py:69` | unchanged |

The unit's diagnosis was correct: the dispatcher
(`experiments/ptr-engine/longrun/grade_v5.py`) had branches only for
`constant_value` / `count_classes` (NUM, hardcoded to `resolve.py` + `errors.py`) and
`call_inside_function` (CALL). There was no `NONE` branch and no `call_at_line` branch,
so a NONE item fell through to the catch-all and a `call_at_line` item crashed on
`derive["function"]`.

## 2. The two new branches

### `NONE` / `no_attr_call_inside_function`
Semantics: *the named attribute is never called inside the named function*.

* The spec must name both `function` and `attr` (`file` optional, defaults to
  `resolve.py`); a spec missing either raises the actionable
  `fixture_truth_mismatch` line instead of deriving a guess.
* Derivation walks the AST of the named function and collects **every** `ast.Call`
  whose callee resolves to that attribute: `ast.Attribute.attr == attr` covers
  `self.attr(...)`, `module.attr(...)` and `ledger.attr(...)` (one AST shape after
  parsing, so the `self`/module spellings cannot hide a call), and
  `ast.Name.id == attr` covers a direct or aliased bare call.
* The derived truth is the **boolean absence** (`call_present`), plus
  `forbidden_attr` / `forbidden_function` / `call_lines` / `callees`. The documented
  `expected` string is recorded (`documented_agrees`) but never overrides the AST.
* **Failure case is explicit:** if the attribute *is* called inside the function, the
  truth says so (`call_present=True`) and an `ANSWER: NONE` grades
  `fail` — reason
  `none_contradicted_by_source: <attr>() IS called inside <function> at <callee>:L<n>`
  — it does not abort.

### `CALL` / `call_at_line`
Semantics: callee plus keyword arguments at an exact line, for a callee with several
identical call sites (`resolve.py` calls `ledger.resolved_count()` at L141, L143 and
L146).

* The line comes from `derive["line"]`; the callee name comes from `derive["callee"]`
  if declared, otherwise from the documented `expected` string.
* Derivation selects the `ast.Call` whose `lineno` matches (full dotted-callee match,
  then last-component match — never a substring, so `fn()` cannot bind `other_fn()`).
  The value is parsed by the same `_parse_call` the CALL branch already used, so
  grading semantics are identical.
* **Refusal:** if no call of that name starts on that line, the grader raises
  ```text
  fixture_truth_mismatch: item <id>: answer_spec kind 'CALL', rule 'call_at_line'
  finds no call named '<callee>' at <file>:<line>; fix the answer_spec line or the
  cited source <file>
  ```
  — a `SystemExit`, never a `KeyError`.

## 3. `fixture_truth_mismatch` is never silent (Task 3)

All derivation failures now go through one shape:

```text
fixture_truth_mismatch: item <id>: answer_spec kind '<KIND>', rule '<rule>': <detail> (fix the answer_spec at <file>)
```

It carries the item id, the spec kind, the rule and the source file — the three things
Task 3 requires. Coverage:

* unknown `answer_spec.kind` (anything outside NUM/CALL/NONE) — e.g.
  `kind 'PROSE'` -> the line above, naming `resolve.py`;
* unknown/absent `derive.rule` inside a known kind;
* a missing required derive key (`function`, `attr`, `symbol`, `pattern`, `line`) —
  the `KeyError` that used to escape (`KeyError: 'function'`) is caught and re-raised
  through the same line;
* a documented `expected` that disagrees with the AST for NUM or CALL;
* a named function that does not exist in the cited source.

## 4. Red -> green (observed output)

Transcript from the probe harness, red = the pre-change dispatch monkeypatched back in
(no NONE branch, no `call_at_line` branch), green = this change:

```text
== RED (pre-change dispatch) ==
RED   (a) all-12 derive        : SystemExit: fixture_truth_mismatch: cp.5.t14 has no usable answer_spec
RED   (b) NONE red (is called) : SystemExit: fixture_truth_mismatch: cp.5.t14 has no usable answer_spec
RED   (c) call_at_line red      : KeyError: 'function'          # TASK 1 probe, raw pre-change
== GREEN (this change) ==
GREEN (a) all-12 derive        : 12/12 derived, 12/12 grade pass
GREEN (b) NONE red (is called) : call_present=True verdict=fail reason=none_contradicted_by_source: record_refusal() IS called inside _refuse ...
GREEN (c) call_at_line red      : SystemExit: fixture_truth_mismatch: item cp.10.t36: answer_spec kind 'CALL', rule 'call_at_line' finds no call named 'ledger.resolved_count' at .../resolve.py:69 ...
```

Test suite:

```text
$ python3 -m pytest experiments/ptr-engine/longrun/tests/test_grade_v6_derive.py -q
14 passed in 0.05s

$ python3 -m pytest experiments/ptr-engine/longrun/tests/test_grade_v5.py \
      .../experiments/ptr-engine/longrun/tests/test_answer_contract.py .../experiments/ptr-engine/longrun/tests/test_decidability_seam.py -q
4 passed in 0.62s
```

`experiments/ptr-engine/longrun/tests/test_grade_v6_derive.py` covers: (a) 12/12 derive + pass on own answer + fail
on a wrong one; (b) the NONE red half (attribute IS called -> `fail`, reason names it)
and the missing-spec-field line; (c) the `call_at_line` red half (different callee at
the pinned line -> named refusal, not a crash) plus a declared-callee override;
(d) TEXT never passes for any of the 12, unknown kind names id+kind+file, missing
`function` is not a `KeyError`, and the 8 pre-change `expected` values are asserted
byte-identical; (e) the score mirror grades 12, and a wrong answer flips one to `fail`.

## 5. The mirror in `score_longrun.py` (Task 5) — applied

`score_longrun.py` already reads `fixture["acceptance"]["checks"]`, so the "mirror" was
fixture data, and on the v6 fixture those hand-written entries (`acc.cp1`..`acc.cp3`)
reference `checkpoints[0..2]` only — the other nine decidable checkpoints had no entry
on that path. The fixture is frozen by this card, so the mirror was brought up in
**code**, not by editing the fixture:

* new `mirror_answer_contract(fixture, run, checks)`, called as stage `3b` from
  `score()`, immediately after the fixture's own acceptance checks;
* for every checkpoint carrying an `answer_spec` it derives truth with
  `grade_v5.derive_truth` (canonical, imported not copied), parses the contracted line
  from the run with `grade_v5.parse_answer_contract`, and grades it with
  `grade_v5.grade_cell` under the check id `acc.derive.<checkpoint id>`;
* a missing turn -> `fail`; TEXT -> `fail` (`grade_cell` never passes TEXT); a spec the
  derivation cannot handle raises grade_v5's one-line `fixture_truth_mismatch` rather
  than being skipped;
* **no-op on authored fixtures**: a fixture with no `answer_spec` anywhere (the v4/v5
  shape) adds zero checks and every pre-existing check keeps its behaviour. The
  existing `acc.cp*` entries are untouched.

Verified in `experiments/ptr-engine/longrun/tests/test_grade_v6_derive.py::test_mirror_grades_all_12_not_just_three`
(12 checks, all `pass`, turns in checkpoint order) and
`::test_mirror_red_half_a_wrong_answer_fails`.

## 6. Constraints honoured

* Zero inference requests: no cell, no model call, no row file. Every artefact here is
  AST/strings over the pinned source tree.
* `LR-01.v5.json` (sha256 `967cef03…`) and `LR-01.v6.json` unedited; `cell.py`,
  `client.py`, `run_longrun.py`, `analyze_stats.py`, `fixture_coverage.py`,
  `matrix_audit.py` unedited.
* `grade_v5.py`: the existing NUM and CALL/`call_inside_function` derivations produce
  byte-identical `expected` values (asserted in the test) and `grade_cell`'s NUM/CALL
  verdict paths are untouched; only the answer kind `NONE` gained a truth-kind-aware
  branch, and TEXT still grades `text` / `text_not_auto_passed`.

## 7. Answer to the card

`LR-01.v6.json` is now fully gradeable end to end: 12/12 checkpoints derive a truth,
each grades `pass` on its own expected answer and `fail` on a wrong one, both new
branches have a demonstrated red half, and `score_longrun.py`'s acceptance path now
grades all 12 rather than 3.
