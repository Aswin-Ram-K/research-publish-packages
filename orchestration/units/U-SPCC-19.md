# U-SPCC-19 — land the bounded bill: regenerate the scorecard, prove the tests, push

**Unit:** U-SPCC-19 · **Status:** done · **Date:** 2026-11-10
**Inputs:** `orchestration/units/U-SPCC-18.md` (the fix), `orchestration/handoffs/U-SPCC-18.json`
**Files owned:** `experiments/ptr-engine/measure/score-spcc-billedproof-2026-11-10.json`,
`orchestration/units/U-SPCC-19.md`, `orchestration/handoffs/U-SPCC-19.json`

## 1. Why this unit exists

`U-SPCC-18` changed how billing is computed but left the published scorecard on disk stale: it still
carried `"billed_tokens": 0` from before the rework. A correct fix behind a stale artifact is not a
landed fix — any reader of `measure/score-spcc-billedproof-2026-11-10.json` would have picked up a
number the code no longer produces.

## 2. What was done

| step | command | result |
|---|---|---|
| prove the tests | `.venv/bin/python -m pytest experiments/ptr-engine/longrun/tests/test_billed_tokens.py experiments/ptr-engine/longrun/tests/test_scorecard_guards.py -q` | `19 passed in 0.09s` |
| regenerate | `.venv/bin/python experiments/ptr-engine/longrun/score_longrun.py experiments/ptr-engine/longrun/tasks-v7/TX-03.v1.json experiments/ptr-engine/measure/rows-spcc-billedproof-2026-11-10.jsonl --pretty --out experiments/ptr-engine/measure/score-spcc-billedproof-2026-11-10.json` | exit **1** (answer-shape checks 8/48 — expected, not a regeneration failure) |
| no stale zero | `grep -c '"billed_tokens": 0' <scorecard>` | `0` |
| docs | `python3 tools/doc_check.py` | `OK`, exit `0` |

The scorecard was produced by its own generator only — no hand-editing — so the number on disk is
reproducible from the rows by anyone.

## 3. The published billing block

```
prompt_tokens            174047
cached_tokens            159744
uncached_tokens           13746
billed_tokens             14007   (alias of billed_tokens_known)
billed_tokens_known       14007
billed_upper_bound_tokens 14303
billed_unknown_rows           1   turns [5]   source "mixed"
cached_fraction_of_prompt      0.917821048337518
billed_coverage            0.99
reconcile_delta_total       557   tolerance 1740   within_tolerance true
```

14,007 is established; 14,303 is labelled an upper bound. The difference (296) is exactly turn 5's
prompt, the one row whose cache counter is absent.

## 4. Rule being landed (unchanged from U-SPCC-18, restated for the commit record)

| condition | billed quantity |
|---|---|
| `cached_tokens` present | `prompt − cached` |
| `cached_tokens` null at turn 1 | mechanism: no prior prefix, so full `prompt` |
| `cached_tokens` null later | **unknown** — excluded from the known sum, counted, widens the upper bound |
| `prompt_tokens` missing | unknown |

`billed_coverage 0.99` is 99 of 100 rows measured: turn 5 is unmeasured, not zero.
