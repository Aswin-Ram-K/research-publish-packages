# UNIT `ATTACK-GRADE-V5` — adversarially probe `grade_v5.py` before it grades a real comparison

**Status:** done · **Date:** 2026-10-26 · **Bound:** ≤32 tool calls, zero inference requests (used: 17)
**Mode:** automated (no human; never ask). Card `10e76580-b891-4baa-9099-374c2505f334`.

## One purpose

Try to break the judge `experiments/ptr-engine/longrun/grade_v5.py` before it grades
the operator's arm comparison ("p95 TTFT and tokens-to-verified-success at
equal-or-better verified quality"), and report whether it may grade that comparison.
The judge had only been tested by its author (`test_grade_v5.py` 26/26 green,
`--red` 26/26 fail). Predecessors measured `grade_v3` FN 30.8 % / FP 45.5 % and
`grade_v4` FN 26.9 % / FP 50.0 % against `grader_fitness.py`; `det_verify.py`
failed its own attack (`V-DET`: a citation numeral read as the answer; a
`avoid calling …` negation accepted).

## Method (no repo file edited; judge/tests/fixtures read-only)

`experiments/ptr-engine/tools/attack_grade_v5.py` builds a temp fixture —
`resolve.py` (`DEFAULT_MAX_REFS = 64`, `_refuse` calling
`ledger.record_refusal(scope=scope_name, serialized_ref=text, code=error.code)`),
`errors.py` (three `Ptr*` classes), and `PROBE-LR-01.v5.json`. The fixture's
`sources` use **absolute** paths, and `grade_v5._source_map` joins any path
containing a separator onto `dv.ROOT` — an absolute second argument wins — so
`derive_truth` reads the temp tree. 41 hand-written probe answers are graded through
`parse_answer_contract` → `grade_cell`, plus arm-level runs through `grade_rows`.
Zero inference requests; every probe is a literal string.

## Attacks and result

| # | attack | probes | class |
|---|---|---|---|
| 1 | citation-numeral trap | P01–P04 | correct |
| 2 | negation inversion + asymmetry control | P05–P08 | correct |
| 3 | wrong value, right shape | P09–P12 | correct, FP on the fixture-declared `scope=...` elision (P12) |
| 4 | right tokens, wrong callee | P13–P15 | correct |
| 5 | docstring occurrence for a `NONE` item | docstring module + NONE fixture | limitation: strings never evidence; **no NONE truth is declarable** |
| 6 | format tolerance both ways | P17–P25 | correct (rejections defensible, some undocumented) |
| 7 | empty / absent answer | P26–P28 + arms | limitation: all land in `fail`; `decidable` counts undecided cells |
| 8 | `TEXT` immunity | P29–P31 + row spoof | limitation: text path immune; a row's parsed fields are trusted over its content |
| 9 | numeric equivalence | P32–P36 | correct; hex/word rejected, `64.0` passes, rule not stated anywhere |
| 10 | our own | P37–P41 | **defect**: `ANSWER: 64.99` and `ANSWER: NUM 64.999` pass as `64` |

**FN 0 / 8 · FP 3 / 22** over probes with a fixed expectation (41 probes total).

## Deliverables (the only writes)

- `experiments/ptr-engine/measure/ATTACK-GRADE-V5.md`
- `experiments/ptr-engine/tools/attack_grade_v5.py`
- `experiments/ptr-engine/measure/attack-grade-v5.json`
- `orchestration/units/ATTACK-GRADE-V5.md` (this card)
- `orchestration/handoffs/ATTACK-GRADE-V5.json`
- journal: `orchestration/journals/ATTACK-GRADE-V5.jsonl`

## Reproduction

```
python3 experiments/ptr-engine/tools/attack_grade_v5.py      # exit 1 while a defect stands
```

## Assumptions (automated-session rule: missing value → conservative default, recorded)

1. The card's literal CALL probes omit the `CALL` keyword and some `=` signs, which
   are not one of the four contract forms. Each CALL attack is therefore run twice:
   the card's literal text (fails on form) and the same intent in contract form
   (the real value/callee test). Recorded in the report §1.
2. The card's 5-call `partial` handoff checkpoint was not written: the probe set ran
   and the first complete result existed inside the same short window, so a partial
   card would have contained no more than this one does. The final handoff carries
   status `done` rather than a false `partial`.
3. `P08` (same-line trailing prose after a correct CALL) is classed defensible, not a
   defect, because the v5 fixture's system prompt says "emit exactly ONE line and
   nothing else"; `grade_v5`'s own docstring tolerance is about surrounding *lines*.
