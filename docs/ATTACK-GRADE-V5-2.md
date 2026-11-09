# ATTACK-GRADE-V5-2 — a second, disjoint attack on the repaired `grade_v5`

**Unit** `ATTACK-GRADE-V5-2` · **gate** `GRADE-V5-REPAIR` (`c470ff85-7953-47e6-a6b4-2ee02a3016ac`,
settled `done`, execution `31c83a58` succeeded) · **inference requests** 0 · **network** none.

**Judge under attack:** `experiments/ptr-engine/longrun/grade_v5.py`,
sha256 `6893d559518168e3ba4fc4a9f5d7642d213d61e2e3c3d0b0a8f01e3379af3077`.
**Tool:** `experiments/ptr-engine/tools/attack_grade_v5_2.py` (new, 45 probes + 10 row probes).
**Measurement:** `experiments/ptr-engine/measure/ATTACK-GRADE-V5-2.json`.

Why a second corpus: a repair tested only against the probes that found the bug is a fit to those
probes. `grade_v3`→`grade_v4` traded FN 30.8 %→26.9 % for FP 45.5 %→**50.0 %** exactly that way.

## 1. Non-overlap with the first corpus

The check is mechanical, not asserted: the tool loads `attack_grade_v5.PROBES` (41 strings) and
diffs its own corpus against them.

| check | result |
|---|---|
| exact duplicates (case-sensitive, trailing newlines trimmed) | **0** |
| near-neighbours (difflib ≥ 0.92 on whitespace-collapsed, caseless text) | 22, all sharing the `ANSWER:` prefix and a `64` payload |
| declared semantic overlaps | 3 — `N37`/`N38` (empty `ANSWER:` body, tab / NBSP filler) vs `P27`/`P28`; `N43` (`ANSWER: 64`, the card's mandated control) vs `P19`/`P22` |

The three declared overlaps are **required surfaces** from this card's own brief ("empty after
`ANSWER:`", "`ANSWER: 64` must still pass"). They are named here rather than dropped or disguised;
no other probe reuses a first-corpus string, and every other near-neighbour changes the adversary
(e.g. `N12` `ANSWER: 64%` vs `P39` `ANSWER: 64%; the previous value was 31` — a unit suffix versus
trailing prose with a stale numeral).

## 2. Method

The tool builds **its own** temp fixture (a `resolve.py`/`errors.py` pair that is not repo source and
not the first attack's source: `RETRY_CEILING = 64`, `_decline(...)` calling
`ledger.record_refusal(scope=reason, serialized_ref=blob, code=exc.code)`, `_quiet()` naming the call
in a docstring only) and wires it in through absolute `sources` paths. Truth is derived by
`grade_v5.derive_truth` — never hand-passed to the grader. Probes are graded through
`parse_answer_contract` + `grade_cell`; row probes go through the real `grade_rows` path on row
dicts. The 41 old probes are re-run from `attack_grade_v5`'s own fixture and diffed against the
verdicts recorded in `measure/attack-grade-v5.json`.

Expectation classes: `pass` (correct answer) · `fail` (wrong value asserted) · `undecidable`
(asserts nothing — an omission) · `text` · `nofalsepass` (must not pass, finer verdict not
prescribed) · `observe` (no binary expectation). `right=True` marks a correct answer (FN
denominator); `right=False` marks a wrong answer or an omission (FP denominator). `firm=False`
marks a probe whose expectation is a *formatting judgment call* — reported as a borderline FN,
never tuned away by weakening the probe.

## 3. Results — own corpus (45 probes, 10 row probes)

**FN 0/16** (right answers that must pass) · **FP 0/27** (wrong answers that must not pass) ·
**omissions rejected 8/8** (all non-answers landed `undecidable`, outside `decidable`).

| group | outcome |
|---|---|
| number surface | `6.4e1`, `NUM 64.0` → `fail/num_not_integer`; `064`, `NUM 64.`, `64 refs`, `64, not 63`, `64%` → `pass`; `6,4` → `fail/num_mismatch` (read as 6); Roman `ⅭⅩⅣ` and `sixty-four` → `undecidable`; `-64` → `undecidable` (**escape**, see §6) |
| citation vs assertion | `64 (see resolve.py:39)`, `64, per line 39` → `pass`; `31, compared with line 39` → `fail` (citation numeral does not rescue a wrong leading value) |
| negation / denial | all 8 denials (`avoid calling`, `declines to call`, `refuses to invoke`, `no … call anywhere`, `never deleted the tests`, `instead of calling`, `must not call`, `fails to call`) → `undecidable`/`unparseable`, **none passes**; the denial wrapped in `TEXT` → `text`, never a pass |
| NONE truth | `NONE` → `pass`; a CALL asserted where no call exists → `fail`; `NONE ledger.record_refusal` → `fail` |
| CALL form | correct control → `pass`; wrong callee → `fail/callee_mismatch`; missing kwarg → `fail/kwarg_set_mismatch` |
| non-answers | empty turn, tab-only body, NBSP-only body, prose only, `ANSWER: ???`, `ANSWER: NUM` → all `undecidable` |
| controls | `ANSWER: 64`, `ANSWER: NUM 64` → `pass`; `ANSWER: 31` → `fail`; mandated CALL control → `pass` |

**Borderline FN (5/16):** `N03 +64`, `N08 sixty-four`, `N11 (64)`, `N17 resolve.py:39 = 64`,
`N19 lines 39-40 give 64` — each asserts the right value in a form the contract does not lead with.
I read `+64` and `(64)` as integers a fair contract should accept, and `resolve.py:39 = 64` as a
natural correct answer; the grader returns `undecidable/unparseable`. This is **strictness, not
unsoundness** — it costs recall and never manufactures a pass — but it is a real FN class and I
report it rather than reclassifying it to zero.

## 4. Row-trust attacked directly (10 row probes, all agree)

| probe | row fields | content | verdict |
|---|---|---|---|
| `R01` | `answer_kind=NUM, answer_value=64` | `The handler declined to record anything.` | `fail/row_fields_disagree_with_content` |
| `R02` | `answer_kind=NUM, answer_value=64` | `ANSWER: TEXT the default is 64` | `fail/row_fields_disagree_with_content` |
| `R03` | *(absent)* | `ANSWER: 64` | `pass/num_equal` — content alone decides |
| `R04` | `NUM 64` | `ANSWER: NUM 64.99` | `fail/row_fields_disagree_with_content` |
| `R05` | `answer_parse_error=prose_only` | `ANSWER: 64` | `fail/row_fields_disagree_with_content` |
| `R09` | `answer_kind=TEXT` | `ANSWER: 64` | `fail/row_fields_disagree_with_content` |
| `R10` | `answer_kind=NONE` | the correct CALL | `fail/row_fields_disagree_with_content` |
| `R06` | `NUM 64` but `answer_raw=ANSWER: 39` | `ANSWER: 64` | `pass` — `answer_raw` is not compared |

No field is trusted over content: every disagreement fails and names both sides, and a row with no
fields grades from its content. `R06` is the one residual: `answer_raw` is metadata that can
contradict content silently. It cannot change a verdict (the value comes from content), so it is a
bookkeeping observation, **not** a trust defect.

## 5. Regression table — the 41 old probes

Re-run now, 41/41 re-derived: **0 changes** against the recorded verdicts in
`measure/attack-grade-v5.json` (same judge sha256). No probe moves fail→pass on a wrong answer and
none moves pass→fail on a right answer.

Relative to the *pre-repair* run recorded by `GRADE-V5-REPAIR` (FN 0/8, FP 3/22, `P12`, `P37`,
`P38` passing): `P37` and `P38` (decimal truncation) now `fail/num_not_integer` — **fixes, not
regressions**.

**One old probe's expectation is wrong, and I say so instead of tuning:** `P12` expects `fail` for
`scope=...`, but the first fixture's documented `expected` string elides `scope`, and the v5
contract accepts a literal `...` for an elided kwarg — its own note admits this ("the answer may
write a literal `...`"). Independently confirmed here: my `N33` writes `...` at the same elided
position and passes. So the old corpus is **FP 0/21 corrected** (1/22 as recorded), and the defect
is the probe, not the grader.

## 6. Defects found by this attack

1. **T3 residual — a non-answer is still decidable.** `ANSWER:\nANSWER:` (two empty markers) is
   `fail/answer_not_contract:multiple_answer_lines`, i.e. it sits in `decidable` (pass+fail).
   `multiple_answer_lines` is not in `NON_ANSWER_ERRORS`. This is exactly the T3 class: the row
   asserts nothing, yet it is counted as a wrong answer. Same shape for
   `ANSWER: ???\nANSWER: 64`.
2. **A wrong answer can escape into `undecidable`.** `ANSWER: -64` is `undecidable/unparseable`
   (`NUM_HEAD_RE` requires a leading digit). It does not pass, so it is not an FP, but a wrong
   value leaves the decidable denominator entirely — the mirror image of defect T3.
3. **Correct-but-non-leading values are FNs** (5 named in §3).

Everything else in the brief held: no crash on any probe, no FP, no regression, and no field
over content.

## 7. Per-defect verdict on the three old defects

| defect | verdict | evidence |
|---|---|---|
| **T1** NUM decimal truncation (`64.99` graded 64 → pass) | **fixed** | `N02 ANSWER: NUM 64.0` → `fail/num_not_integer`; `P37`/`P38` now fail; no decimal in 45 probes passes |
| **T2** row-field spoofing of TEXT/NUM | **fixed** | `R01`,`R02`,`R04`,`R05`,`R09`,`R10` all `fail/row_fields_disagree_with_content`; `R03` proves content-only rows still pass |
| **T3** non-answers counted inside `decidable` | **partially fixed** | 8/8 ordinary non-answers are `undecidable` (fixed), but `N42` shows `multiple_answer_lines` still lands in `decidable` (remaining) |

## 8. Verdict

The card's bar — FN = 0 **and** FP = 0 **and** no regression on either corpus, with defensible
expectations:

* own corpus: **FN 0/16, FP 0/27**, omissions rejected 8/8
* combined (own + 41 re-derived): **FN 0/24, FP 0/48 corrected** (0/48 + the one recorded-but-wrong
  `P12` expectation = 1/49 as recorded)
* regressions on the 41: **none**
* per-defect: T1 fixed · T2 fixed · T3 **partial**
* expectations I think were wrong, stated not tuned: `P12` (§5), `N05`/`N14` left as `observe`
  because the string does not assert a single value, and the five borderline FNs (§3)

**Verdict: `pass`** on the FN/FP/regression bar, with one open defect (T3 residual, `N42`) that the
bar does not measure and that cannot turn a wrong answer into a pass.

**May `grade_v5` now grade the operator's arm comparison?** Yes — no wrong answer in 48 wrong-answer
probes passes, no correct answer regresses, and the only remaining gap (`ANSWER:\nANSWER:` →
`fail`) cannot inflate an arm's score; the one thing to keep in mind is that it must **not** be
repaired into leniency, and that the 5 borderline FNs under-count correct answers in unusual
formats.
