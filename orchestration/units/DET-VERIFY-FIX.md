# UNIT DET-VERIFY-FIX — repair the deterministic verifier after V-DET's fail

**Status:** done · **Author of `det_verify.py` is not the verifier here.** Offline, zero requests.

## Why

`V-DET` (`orchestration/handoffs/V-DET.json`) returned `overall: fail`. Its decisive attack
passed (AST-derived ground truth survived a `/tmp/vdet` mirror with `DEFAULT_MAX_REFS=99` and a
renamed `Ptr*` class), so the *approach* stands. Three implementation claims did not:

1. **FN** — the numeral parser took the last surviving numeral, so `ANSWER: 64 (resolve.py:39)`
   asserted 39 and was rejected.
2. **FP** — `NEGATION` had no `avoid` branch, so "the handler should avoid calling
   ledger.record_refusal with scope, serialized_ref and code" was ACCEPTED.
3. **Coverage overstated** — `7/12` was prose; only 3 checks were code-decided, and the matrix
   had 13 entries, not 12.

## What was done

### Task 1 — numeral rule as a rule
Rule stated in the module docstring, implemented as `CITATION_SPANS` + `asserted_number`:
the asserted value is the numeral the answer presents as the answer; a numeral inside a
citation (`<path>:<n>`, `#L<n>`/`L<n>`, `line <n>`, `<n> of <m>`, a parenthetical naming a file)
or retracted by the answer is not a candidate; among survivors, the first candidate in the
answer slot (leading clause after the last `ANSWER:`), else the first candidate in the segment.
No probe string is special-cased. **8 new corpus cases** (`p.num.cite.*`), each red under the
old last-survivor rule (asserted in `NumeralRule.test_each_case_was_red_under_the_old_rule`).

### Task 2 — negation as a lexicon
`NEGATION` extended to `avoid` (verb-object bound), `shouldn't`/`should not`, `must not`,
`won't`/`will not`, `without calling`, `instead of calling`, `fails to call`, `skips`/`skipped`,
`doesn't`, `not calling`, plus the existing forms. **10 new negation probes** (`p.neg.*`), all
rejected with reason `call_negated`. **Asymmetry test:** two correct probes where `avoid` sits in
an unrelated clause (`avoid the retry loop; ANSWER: ledger.record_refusal(...)`) must still PASS
— both do.

### Task 3 — coverage settled honestly
`acc.cp1`, `acc.cp2`, `acc.cp3`, `acc.1` are real handlers over the same AST-derived facts as
their `cp.*` mirrors, with their own probes; `acc.4` is implemented as an `ast.FunctionDef` count
of `def test_*` over the pinned path named by `acc.n3d`. `COVERAGE` is built in code from
`CHECK_HANDLERS` over the 13-entry `CHECK_ORDER`; `COVERAGE_SUMMARY` reports

**decidable 8/13** = `cp.0.t12, cp.1.t24, cp.2.t46, acc.cp1, acc.cp2, acc.cp3, acc.1, acc.4`;
undecidable = `acc.2, acc.3, acc.n2b, acc.n3b..acc.n3e, repair.t30`.

### Task 4 — the gate, stated with denominators
Gate over **48 implemented probes** (23 correct-intent, 22 incorrect-intent, 3 omission
controls) of 58 in the corpus; **10 excluded** because their checkpoint is decided by no handler:
`repair.t30` ×5 and `acc.n2b` ×5. This is a gate over implemented probes, **not** over the
acceptance checks as a whole — the matrix carries that sentence in `definition.gate_scope`.

## Evidence

| command | result |
|---|---|
| `python3 experiments/ptr-engine/tools/det_verify.py` | exit 0 · POOLED FN **0/23**, FP **0/22**, omission 3/3 |
| `python3 experiments/ptr-engine/tools/tests/test_det_verify.py` | exit 0 · 31 tests OK |
| `DET_VERIFY_DEGRADE=naive python3 …/test_det_verify.py` | exit 1 (FN: `p.cp0.para` "ANSWER: 64." rejected) |
| `DET_VERIFY_DEGRADE=mention python3 …/test_det_verify.py` | exit 1 (FP: negated call claims accepted) |

## Write paths (exactly these)

- `experiments/ptr-engine/tools/det_verify.py`
- `experiments/ptr-engine/tools/tests/test_det_verify.py`
- `experiments/ptr-engine/measure/det-verify-matrix.json`
- `orchestration/units/DET-VERIFY-FIX.md`
- `orchestration/handoffs/DET-VERIFY-FIX.json`

Not touched: `grade_v3.py`, `grade_v4.py`, `grader_fitness.py`, `anchor_classify.py`,
`anchor_probes.py`, `ANCHOR-PREREG*.md`, `V-DET`'s handoff, any fixture, any row/grade file.
`EXTRA_PROBES` lives in `det_verify.py`; the graders' `PROBES` are still imported read-only.
