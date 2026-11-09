# UNIT HANDOFF-SHAPE-DECISION

Automated, offline (zero requests, never `ask_user_question`). Bound: **24 tool calls**.
Written on the evidence of verifier `V-HANDOFF-SHAPE` (`orchestration/handoffs/V-HANDOFF-SHAPE.json`,
`overall: fail`).

## Purpose

Record — do not re-litigate, do not re-classify, do not loosen — the shape decision the verifier said was
owed for the documents that carry **both** `overall` and the full 7-key unit contract, so a genuinely
missing `checks` on a verdict-role document is an **expected, visible, dated gap** instead of a silent pass.

## Inputs read

- `orchestration/handoffs/V-HANDOFF-SHAPE.json` (fail; per-document findings; recommendation)
- `tests/test_orchestration_handoffs.py` (classify(), the pinned baselines, the existing tests)
- `state/logs/U8.18/verifier_shape_baseline.json` (schema: `gaps` = `{name: [missing keys]}`)
- `docs/HANDOFF-SHAPE.md` (append target)
- The live corpus: 1095 parseable handoffs; measured 10 carrying both `overall` and the 7 unit keys, of
  which exactly 3 lack `checks` (`RECORD-REFRESH.json`, `VERDICT-DISPUTE.json`,
  `VERDICT-REFUSAL-SEMANTICS.json`); the other 7 carry the complete verifier contract too (`missing=none`).

## The decision of record

| file | role | reason | gap |
|---|---|---|---|
| `VERDICT-DISPUTE.json` | verdict | adjudicated another card's PASS; `overall: fail` is a judgement | recorded `['checks']` |
| `VERDICT-REFUSAL-SEMANTICS.json` | verdict | triage/reopening of two cards; `overall: PASS` is a judgement | recorded `['checks']` |
| `RECORD-REFRESH.json` | unit | `overall: PASS` self-reports its own insertion work; `checks` was never its key | none, no baseline entry |

The classifier stays as it is — shape first, name second. It is **not** loosened further and **not**
reverted: the 11 narrowed false positives were real.

## Deliverables

1. Baseline entries + pin update in exactly one place (baseline `5f8bbd35…` → `c6929351…`).
2. A non-failing REPORT (`_ambiguity_report`, printed **and** warned so it is visible under `-q`) listing
   every both-shape handoff with its missing verifier keys and its recorded role (`UNDECIDED` if none).
3. `docs/HANDOFF-SHAPE.md` appended: decision table, the verifier's quote that produced the `fail`, the rule
   in one sentence, and the recorded-gap-vs-loosened-classifier sentence.
4. Tests: guard green; both red cases still bite by name; the report appears and does not change exit status.

## Write paths (exactly)

`tests/test_orchestration_handoffs.py` · `state/logs/U8.18/verifier_shape_baseline.json` ·
`docs/HANDOFF-SHAPE.md` (append) · `orchestration/units/HANDOFF-SHAPE-DECISION.md` ·
`orchestration/handoffs/HANDOFF-SHAPE-DECISION.json` · `orchestration/journals/HANDOFF-SHAPE-DECISION.jsonl`

No handoff, `cell.py`, `run_longrun.py`, fixture, grader, analyser or published number was touched.

## Kill condition

If the baseline edit had required re-freezing unrelated pins, STOP and report the conflict. It did not: the
`gaps` schema takes a per-document missing-key list, so only the verifier pin moved.
