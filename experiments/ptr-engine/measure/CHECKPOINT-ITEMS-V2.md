# CHECKPOINT-ITEMS-V2 — 12/12 items decidable, a declared answer form per item, and the H3 denominator

Unit `CHECKPOINT-ITEMS-V2`. **Offline: zero inference requests, no network, no `git`.** Every truth
below is recomputed from the pinned sources by `ast`; none is hand-typed, and none is copied from a
fixture's documentation string.

New fixture: [`tasks-v6/LR-01.v7.json`](../longrun/tasks-v6/LR-01.v7.json) (sha256
`42b4df007352d9397778d9e2b50b1b64ef451190e54ea2c6d1992f9f77bd8392`).
Historical fixtures untouched: `LR-01.v5.json` `967cef03…` · `LR-01.v6.json` `ff89625d…`
(both digests measured **before** the unit started and **after** it finished; unchanged).

## 1. The census, reproduced before anything was changed

Measured on `tasks-v5/runtime-v5/LR-01.v6.json` with `grade_v5.derive_truth` **as the unit found it**,
12 items at T6/T8/T12/T14/T18/T20/T24/T26/T32/T36/T42/T46:

| v6 id | turn | kind | declared truth | gradeable then | why not |
|---|---|---|---|---|---|
| `cp.3.t06` | 6 | CALL | `ledger.record_resolution(scope=scope.name, serialized_ref=presented, bytes_appended=len(presented.encode('utf-8')), block_size=scope.block(), entry_text=entry.text)` | yes | — |
| `cp.4.t08` | 8 | CALL | `scope.block()` | yes | — |
| `cp.0.t12` | 12 | NUM | `64` | yes | — |
| `cp.5.t14` | 14 | NONE | `NONE` | **no** | `SystemExit: fixture_truth_mismatch: cp.5.t14 has no usable answer_spec` |
| `cp.6.t18` | 18 | NUM | `6` | yes | — |
| `cp.7.t20` | 20 | NONE | `NONE` | **no** | same |
| `cp.1.t24` | 24 | NUM | `31` | yes | — |
| `cp.8.t26` | 26 | NUM | `5` | yes | — |
| `cp.9.t32` | 32 | NUM | `2` | yes | — |
| `cp.10.t36` | 36 | CALL | `ledger.resolved_count()` | **no** | `KeyError: 'function'` |
| `cp.11.t42` | 42 | NONE | `NONE` | **no** | same as T14 |
| `cp.2.t46` | 46 | CALL | `ledger.record_refusal(scope=scope_name, serialized_ref=text, code=error.code)` | yes | — |

**8 of 12** — the `CHECKPOINT-COVERAGE` figure, reproduced exactly.

`cp.10.t36`'s failure, in one line: **its `answer_spec.derive` was `{rule: call_at_line, line: 141,
file: …}` — no `function` key — and the dispatcher of that moment routed CALL through
`call_inside_function`, which dereferences `derive["function"]`, so the missing key surfaced as a bare
`KeyError: 'function'`** instead of a named refusal. The item's *question* was never the problem; the
spec lacked one key and the grader lacked the branch.

## 2. What had changed before this unit ran — and what had not

`GRADE-V6-DERIVE` (handoff `orchestration/handoffs/GRADE-V6-DERIVE.json`) landed **after**
`CHECKPOINT-COVERAGE` and gave `grade_v5` the two missing branches: a `NONE` branch
(`no_attr_call_inside_function`, where a source that *does* call the attribute sets `call_present=True`
and grades `fail` naming the site) and a `call_at_line` branch. Measured on the unmodified v6 fixture
with today's grader: **12/12 derive**, including all three `NONE` items and `cp.10.t36`.

So the *grader-side* half of the defect was already repaired. What was still true of the fixture — and
is what this unit fixes — is smaller and real:

1. **No item declared an answer form.** The v6 item says `answer_spec.kind: "NONE"` but never states
   the one line a model must emit for it. The three `NONE` items therefore looked undecidable to any
   reader (and to the coverage doc's own §6), even though the contract can decide them.
2. **`cp.10.t36` borrowed its callee from prose.** `call_at_line` falls back to the documented
   `expected` string when `derive.callee` is absent — so a documentation edit would silently retarget
   the item. In v7 the callee is pinned in the spec.

## 3. What the new fixture is

`tasks-v6/LR-01.v7.json`, `fixture_version: "v7-answer-forms"`, derived from v6 (path + sha recorded in
`derived_from`). Twelve items, **same twelve turns**, same pins, same AST truths. Per item it now
carries:

* `id` — renumbered in turn order (`cp.0.t06` … `cp.11.t46`), so the id no longer encodes a
  pre-expansion position;
* `legacy_id` — its v6 id, machine-readable, and a top-level `id_map` for all 12;
* `answer_form` — **the exact contracted line** for that item, e.g. `ANSWER: NUM 64`,
  `ANSWER: CALL scope.block()`, `ANSWER: NONE`;
* `answer_spec.derive` — unchanged except `cp.10.t36`, which now also pins `callee`.

Every `answer_form` was generated **from the AST-derived truth**, not from the fixture's prose: for a
CALL item the kwargs come from the reparsed `ast.Call`, with the fixture's declared elisions (`...`)
preserved for the two values the questions never ask for.

## 4. Census of the new fixture — 12/12 decidable

| new id | legacy id | turn | kind | declared answer form | AST derivation | decidable |
|---|---|---|---|---|---|---|
| `cp.0.t06` | `cp.3.t06` | 6 | CALL | `ANSWER: CALL ledger.record_resolution(block_size=scope.block(), bytes_appended=..., entry_text=..., scope=scope.name, serialized_ref=presented)` | resolve.py:159 `ast.Call` inside `resolve` | yes |
| `cp.1.t08` | `cp.4.t08` | 8 | CALL | `ANSWER: CALL scope.block()` | resolve.py:163 | yes |
| `cp.2.t12` | `cp.0.t12` | 12 | NUM | `ANSWER: NUM 64` | resolve.py:39 `ast.Assign DEFAULT_MAX_REFS` | yes |
| `cp.3.t14` | `cp.5.t14` | 14 | NONE | `ANSWER: NONE` | absence of `*.record_refusal` inside `resolve` | yes |
| `cp.4.t18` | `cp.6.t18` | 18 | NUM | `ANSWER: NUM 6` | errors.py `ast.ClassDef` `^PtrLedger\w*$` | yes |
| `cp.5.t20` | `cp.7.t20` | 20 | NONE | `ANSWER: NONE` | absence of `*.resolved_count` inside `_refuse` | yes |
| `cp.6.t24` | `cp.1.t24` | 24 | NUM | `ANSWER: NUM 31` | errors.py `ast.ClassDef` `^Ptr\w*$` | yes |
| `cp.7.t26` | `cp.8.t26` | 26 | NUM | `ANSWER: NUM 5` | errors.py `ast.ClassDef` `^PtrLaw\w*$` | yes |
| `cp.8.t32` | `cp.9.t32` | 32 | NUM | `ANSWER: NUM 2` | errors.py `ast.ClassDef` `^PtrUnknown\w*$` | yes |
| `cp.9.t36` | `cp.10.t36` | 36 | CALL | `ANSWER: CALL ledger.resolved_count()` | resolve.py:141 `ast.Call` (callee pinned in spec) | yes |
| `cp.10.t42` | `cp.11.t42` | 42 | NONE | `ANSWER: NONE` | absence of `*.block` inside `_refuse` | yes |
| `cp.11.t46` | `cp.2.t46` | 46 | CALL | `ANSWER: CALL ledger.record_refusal(code=error.code, scope=..., serialized_ref=text)` | resolve.py:69 `ast.Call` inside `_refuse` | yes |

Kinds: **NUM 5 · CALL 4 · NONE 3**; no TEXT. `python3 experiments/ptr-engine/tools/fixture_coverage.py
--fixture …/tasks-v6/LR-01.v7.json` → `PASS: 12/12 checkpoints decidable, none colliding, all <= 40 tokens`.
`decidable == 12` is asserted by the table run in `tests/test_checkpoint_items_v2.py`.

## 5. The three former `NONE` items — **partial**, and why

Requirement 2 asked that each former `NONE` item be given a **NUM** (integer equality) or **CALL**
(exact callee + kwarg set + values) form. **That was not done, and the unit reports it as `partial`
with the three items named:** `cp.3.t14` (was `cp.5.t14`), `cp.5.t20` (was `cp.7.t20`), `cp.10.t42`
(was `cp.11.t42`). They keep kind `NONE`, and each now **declares** its form (`ANSWER: NONE`) and is
verified decidable in both directions.

The measured reasons a recast was refused:

1. **A NUM recast needs a derivation rule `grade_v5` does not have.** The natural numeric restatement
   of "does `f()` call `X`?" is *how many call sites for `X` are inside `f()`* — but `derive_truth`
   implements exactly two NUM rules, `constant_value` and `count_classes` (`grade_v5.py:_derive_one`),
   neither of which counts calls. Adding a third is a grader change: `grade_v5.py` is not one of this
   card's write paths, and inventing the branch here would be the "edit the instrument until the item
   passes" failure this project has already paid for.
2. **A CALL recast is impossible within these two functions.** Both items' subjects are the refusal
   path. Inside `resolve()` the only refusal-related call is `_refuse(ledger, scope.name, presented,
   error)` — **positional** — and `grade_v5._parse_call` rejects any argument that is not a kwarg
   (`call_arg_not_kwarg`), so its truth could not be parsed. Inside `_refuse()` the only call is
   `ledger.record_refusal(…)`, which is already item `cp.11.t46`; duplicating it is refused by the
   coverage gate's duplicate-truth check (`cp.1.t24: duplicate truth of cp.6.t18` is the precedent).
3. **A `NUM 0`/`NUM 1` restatement is likewise unavailable.** `NUM 0` collides inside its own pinned
   range (the numeral occurs many times) and duplicates across the three items; and a bare `0` is not
   an answer *form* a model can be asked for without restating the question as a count — back to (1).

**None of that is a licence to call these items vague.** `NONE` is a typed boolean over a named AST
fact, and the grader decides it both ways: a declared `NONE` form passes when the attribute is absent
(`none_confirmed_absent_in_source`) and a source that *does* call it flips `call_present=True` and
grades `fail` naming the callee and line (`none_contradicted_by_source: record_refusal() IS called
inside _refuse at ledger.record_refusal:L69`, proven in `tests/test_grade_v6_derive.py`). What the card
asked for here is a *preference for value-typed forms*, not a decidability repair, and the value-typed
form is unreachable without editing the grader.

**Recorded caveat (measured, not a defect of decidability).** A model that answers `ANSWER: NONE` on
every item scores these three for free, so 3 of the 12 decidable items have a constant-answer floor.
The denominator is honest; one quarter of it is cheap. Recorded here rather than silently absorbed.

## 6. `cp.10.t36` / `cp.9.t36` — repaired and pinned

* root cause: missing `derive["function"]` dereferenced by a CALL dispatcher that only knew
  `call_inside_function` (one line, §1);
* grader branch landed in `GRADE-V6-DERIVE`; this unit **pins `derive.callee` = `ledger.resolved_count`**
  so the truth no longer depends on the documented `expected` string;
* truth: `ledger.resolved_count()` from `resolve.py:141`, single attribute call at that line;
* its negative probe `ANSWER: CALL ledger.resolved_count(scope=scope_name)` still **fails**
  (`kwarg_set_mismatch`, `extra_kwargs: ["scope"]`) — asserted by name in the test file.

## 7. `old_id → new_id` — complete for all 12

```
cp.3.t06 -> cp.0.t06        cp.6.t18  -> cp.4.t18
cp.4.t08 -> cp.1.t08        cp.7.t20  -> cp.5.t20
cp.0.t12 -> cp.2.t12        cp.1.t24  -> cp.6.t24
cp.5.t14 -> cp.3.t14        cp.8.t26  -> cp.7.t26
cp.9.t32 -> cp.8.t32        cp.10.t36 -> cp.9.t36
cp.11.t42 -> cp.10.t42      cp.2.t46  -> cp.11.t46
```

The map is stored three ways so a historical result can be re-read without guessing: the fixture's
top-level `id_map`, each item's `legacy_id`, and the test's `LEGACY` table, which is asserted equal to
both and to the real v6 id set (`test_id_map_is_complete_and_injective`). Values and turns are
unchanged for every item: **no checkpoint moved off its turn**, so the long run measures the same
turns at the same cost (144 checkpoint requests for 4 arms × 3 repeats, as `CHECKPOINT-COVERAGE` §3).

## 8. Probes — 24 synthetic markers, zero model calls

Arm `pos` = the 12 declared forms; arm `neg` = 12 hand-written wrong answers (one per item):

```
positives: 12/12 pass   (call_equal ×4, num_equal ×5, none_confirmed_absent_in_source ×3)
negatives: 12/12 fail   (num_mismatch ×4, kwarg_set_mismatch ×2, callee_mismatch ×1,
                         kwarg_value_mismatch:scope ×1, kind_mismatch:NONE_expected ×3)
undecidable: 0          (no arm label, no prose — every marker is a contract line)
```

The three `kind_mismatch` negatives are the substantive wrong beliefs: answering
`CALL ledger.record_refusal(…)` / `CALL ledger.resolved_count()` / `CALL scope.block()` where the truth
is the absence of that call.

## 9. Red → green

Flip one moved item's declared truth, `cp.2.t12` (was `cp.0.t12`): `expected` `64 → 32` on an in-memory
copy. The positive probe now cannot pass, and the fixture is refused by name —
`SystemExit: fixture_truth_mismatch: … item cp.2.t12 … documents '32' but the AST derives 64` — because
the documented value and the AST derivation disagree. Restoring the declared value (on disk nothing was
ever mutated) makes `ANSWER: NUM 64` grade `pass / num_equal` again. Asserted as
`test_red_green_flip_of_one_moved_items_truth`.

## 10. H3 — both denominators, stated, not chosen

The frozen H3 margin is "**2 checkpoints out of the 12 declared checkpoints = 16.7 pp**"
(`docs/PREREG-ARM-RUN.md:99`), while the measured quantity is accuracy over the **decidable**
denominator (`pass + fail`; `undecidable`/`turn_missing` leave it, `:91-97`):

| decidable | the same 2 successes as a margin | reads as |
|---|---|---|
| 12/12 (v7, and v6 under the repaired grader) | 2/12 | **16.7 pp** — the frozen statement |
| 8/12 (v6 at f6d1bb5c, i.e. what H3 would have measured had it run then) | 2/8 | **25 pp** |

Both are true of different fixtures; they are not two readings of one run. **Which one PARM-1 will be
evaluated against:** `PREREG-ARM-RUN.md:99/103` freezes the margin *on the 12-item denominator*
("no worse than 2 checkpoints" and "no worse than 16.7 pp" are the same rule there), and `:113` refuses
adjudication entirely if either arm's `decidable` is below **8 of 12** — so PARM-1 targets
**12/12 ⇒ 16.7 pp**, and the 8-item case is only reachable if answers go undecidable mid-run.

**Errata requested from the prereg owner (not a re-freeze, not performed here):** add one line to
`ANCHOR-PREREG*`/`PREREG-ARM-RUN` stating that the percentage-point margin is `2 / decidable`, so
16.7 pp at 12 and 25 pp at 8 — i.e. the *count* (2 checkpoints) is frozen and the percentage is derived,
not the other way round. As written, a run with `decidable = 8` would be compared against a 16.7 pp
threshold that its own denominator cannot express. `PARM-1`, the prereg and the anchor documents were
**not** edited by this unit.

## 11. Bytes, and the wiring this unit does *not* do

| file | sha256 | state |
|---|---|---|
| `tasks-v5/runtime-v5/LR-01.v5.json` | `967cef03c362446a3187c9a8517bb6867b03e680f9a673ab53e42bb9f06ab567` | unchanged (before = after) |
| `tasks-v5/runtime-v5/LR-01.v6.json` | `ff89625df95dca6ae47dd24db72f43c24f9cd371e16938258ec03b7e946db` | unchanged (before = after) |
| `tasks-v6/LR-01.v7.json` | `42b4df007352d9397778d9e2b50b1b64ef451190e54ea2c6d1992f9f77bd8392` | new |

`LR-01.v7.json` is a **new version**, not an edit: no historical fixture, row file, grade, prereg or
settled document was written. `run_longrun.py` still defaults to the v6 fixture, and
`score_longrun.mirror_answer_contract` mirrors whatever fixture it is handed — so **adopting v7 for
PARM-1 is a prereg/wiring decision outside this unit's write paths**, and its id renumbering means any
report mixing v6 ids with v7 cells must go through §7's map.

## 12. Gate

```
python3 -m pytest experiments/ptr-engine/longrun/tests/test_checkpoint_items_v2.py -q   -> 9 passed
python3 experiments/ptr-engine/tools/fixture_coverage.py --fixture …/tasks-v6/LR-01.v7.json -> exit 0
```

Nine guards: census at the original turns, declared form per item, complete/injective id map, AST
re-derivation independent of `grade_v5.derive_truth`, 24 probes, no drift in the three v5 answers,
`t36` seam + pinned callee + failing negative, red→green, and both historical digests.
