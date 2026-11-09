# UNIT V-FIXTURE-V7 — independent re-derivation of `LR-01.v7.json`'s 12 truths

**Tag:** `automated` · OFFLINE (zero inference) · verifier unit, not the author.
**Bound:** 24 tool calls, `partial` by call 5. **Used:** 17.
**Status:** `pass` — 12/12 `agree`, 0 `disagree`, 0 `ambiguous`.

## Purpose

`CHECKPOINT-ITEMS-V2` (`77d8a88e`) authored the 12 expected answers of
`experiments/ptr-engine/longrun/tasks-v6/LR-01.v7.json` and reported 12/12 decidable. Its own
derivation is the only check those truths had, and `RUN-A*` grades 4 arms × 48 turns × 3 reps
against them for H3. A wrong truth does not fail loudly; it moves the quality column.

## Method (order matters)

1. Hash sources + fixture; read `ptr_engine/resolve.py` (L1–169) and AST-census
   `ptr_engine/errors.py`; pin the verifier's own question→fact map to `/tmp` **before**
   opening `checkpoints[].expected`.
2. Derive the integer at each NUM id, the callee + kwarg name set + value texts at each CALL
   id, and the absence at each NONE id — by the verifier's own `ast` walk
   (`experiments/ptr-engine/tools/fixture_v7_audit.py`). Nothing imported from
   `CHECKPOINT-ITEMS-V2`, `grade_v5`, or `det_verify`.
3. Then diff per id (`agree` / `disagree` with both values / `ambiguous`).
4. Prove the three NONE ids by naming the source fact that would have to exist.
5. Establish the decode path (`\u003d` → `=`) and check the CALL kwarg sets for subset risk.
6. Red case in `/tmp`: mutate one expected value, require `disagree` on exactly that id and a
   non-zero exit; restore, require 12/12 and exit 0.

**Contamination disclosed:** the first raw dump of the fixture was truncated but its
`acceptance.checks` mirror was visible, leaking three answers (`64`, `31`, the
`record_refusal` shape). Those three ids are not blind; all twelve were nonetheless
re-derived from source, and the other nine were blind.

## Result

- **12/12 agree.** Kinds NUM 5 · CALL 4 · NONE 3, matching the fixture and `PARM-1-ERRATA`.
- No source drift: `resolve.py` `71a14c2c…`, `errors.py` `402dc958…` equal the shas the
  fixture itself records under `sources[]`.
- **NONE ids**: all three are *decidable* (absence is provable and `grade_v5` names the
  offending call site when it is present), not "unanswerable"; all three are constant
  `ANSWER: NONE` → a constant-NONE arm banks 3/12 for free (E1 confirmed independently).
- **CALL name sets**: exact for all four (`5`, `0`, `0`, `3` kwargs) — no subset, no
  superset. `grade_v5._check_documented_call` aborts grading on a name-set divergence, so a
  subsetting fixture could not pass silently.
- **Real false-positive surface (finding F1)**: value *elision*, not name subsetting.
  `cp.0.t06` elides 2/5 values, `cp.11.t46` elides 1/3 (`scope`, the value that separates
  `scope=scope_name` from `scope=scope.name`). `grade_cell` accepts a literal `...` for any
  elided kwarg ⇒ 3 of 8 substantive CALL values can be answered `...` and still `pass`; an
  arm naming callee + kwarg names passes all four CALL ids.
- **F2**: the two CALL `expected` strings are in *source* order and `cp.11.t46`'s carries
  trailing prose (`, before re-raising`) — neither is a contract-valid answer, though order
  is ungraded (`kwargs_as_written` is reported, never graded).
- **F3 / residual**: `cp.3.t14`'s truth rests on the word "itself" in the question (the
  source *does* write a refusal row via `_refuse` one frame down); and `grade_v5` derives
  truth from the **live** tree, so the truths are stable only while `acc.n3b` (no write to
  `ptr_engine/resolve.py`) holds — an arm that writes it can flip `cp.3.t14` from NONE to a
  CALL.

## Red / green

```
RED 1  cp.6.t24 expected 31 -> 30 : [disagree] cp.6.t24 t24 NUM ours="31" / fixture: "30",
       {"agree": 11, "disagree": 1, "ambiguous": 0}, EXIT=1
RED 2  cp.11.t46 drops kwarg 'code': [disagree] ... "kwarg name set: SUBSET: fixture omits
       ['code']", {"agree": 11, "disagree": 1}, EXIT=1
GREEN  original fixture           : {"agree": 12, "disagree": 0, "ambiguous": 0}, EXIT=0
GREEN  every '=' escaped \u003d   : {"agree": 12, "disagree": 0}, EXIT=0
```

## Write paths (exactly these, nothing else)

`docs/V-FIXTURE-V7.md` · `experiments/ptr-engine/measure/v-fixture-v7.json` ·
`experiments/ptr-engine/tools/fixture_v7_audit.py` · `orchestration/units/V-FIXTURE-V7.md` ·
`orchestration/handoffs/V-FIXTURE-V7.json` · `orchestration/journals/V-FIXTURE-V7.jsonl` ·
`/tmp/**`.

## Kill condition

If the audit cannot derive a source fact for an id within 3 attempts, report `partial` naming
that id. Not triggered.
