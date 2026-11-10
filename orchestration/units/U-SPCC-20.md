# U-SPCC-20 — why 40/50 TX-03 checks fail as `kind NONE != NUM`

**Status:** done (diagnosis only; nothing fixed, zero live requests).

**Run under diagnosis:** `experiments/ptr-engine/measure/rows-spcc-billedproof-2026-11-10.jsonl`
(arm `masking-no-fetch`, rep 1, 100 turns, `occamy-1.0`, T0/seed 42) against
`experiments/ptr-engine/longrun/tasks-v7/TX-03.v1.json` (`TX-03.v1`, gen-7).
Scorecard: `measure/score-spcc-billedproof-2026-11-10.json`, `checkpoint_accuracy 8/48`, 40 required fails.

## Finding

**Cause 1 — content evicted — accounts for 40/40 failures.** Every failing checkpoint is asked after its
fact's document body has been replaced in the prompt by the pointer marker `[MASKED <doc>@r1]`, which carries
no value. `ANSWER: NONE` is the arm behaving as designed. Causes 2 (present-but-unretrieved), 3 (contract too
strict) and 4 (fixture unanswerable) are each 0; unclassified 0.

Masking fires exactly once per fact, `WINDOW_TURNS = 4` (`longrun/arm_cd.py:39`) after that fact's intro turn:
turns 5, 12, 21, 28, 49, 56, 65, 72 for facts f01–f08 (intro turns 1, 8, 17, 24, 45, 52, 61, 68). The eight
passing probes are exactly the `d2` probes at `intro+2` (turns 3, 10, 19, 26, 47, 54, 63, 70) — asked *before*
the mask. Every `d5/d6/d8/d20/d32` probe is asked *after* it.

## Method (decisive test, byte-identical)

All 100 turn prompts were re-materialised by driving `longrun/run_longrun.py`'s own `run_cell` with
`send_chat` replaced by a recorder (the `prompt_at_turn.py` pattern), feeding each turn the settled row's real
answer. `sha256(user content)` matched the row's `prompt_sha256` on **100/100 turns, 0 mismatches**, so the
searched bytes are exactly what the endpoint received. `_http_get_json` was stubbed offline and the network
trip-wires stayed silent; cap-gate recorded `used_in_run=100 delta=0`.

Search: digit-boundary regex `(?<![\d.])<expected>(?![\d.])` plus the anchor `VAL_<X> = <expected>`; position by
`tiktoken cl100k_base` offset.

Result: **8/8 passes have the value present (1 hit, 1 anchor hit); 40/40 failures have 0 hits and 0 anchor
hits.** Pass probes retrieve at request-token fractions up to 0.74 (f08.d2: 1809/2455), so depth is not the
limiter — cause 2 excluded by data.

Verbatim post-mask T6 prompt segment (doc-fact-01 intro T1, masked T5):

```
QUESTION (T1): Work turn 1.
TOOL OUTPUTS:
[MASKED doc-fact-01@r1]
ANSWER (T1):
```

`3001` occurs 0 times in that prompt. `3000` survives only because T3's answer line
`ANSWER (T3): ANSWER: NUM 3000` is in the transcript, which is why the early probes pass.

## Two degenerate diagnostic fields (defects; must not be cited as evidence)

1. `expected_present` tests the **reasoning channel**, not the prompt —
   `longrun/run_longrun.py:2581`: `expected_present = bool(contains_expected(reasoning_raw, expected)) if expected else False`.
   With `thinking` off, `reasoning` is `""` on every row, so the field is `False` on all 48 checkpoints,
   **including the 8 that answered correctly** (`cp.TX-03.f01.d2`: expected 3000, answer `NUM 3000`, False).
2. `evicted` is dead under this arm — initialised `0` at `longrun/run_longrun.py:1453` and only assigned inside
   the `if arm == "transcript-grow":` FIFO branch (`:1476`). Hence `evicted=0` on all 100 rows *including T5*,
   where `masked_rows=1` and `masked_entry=[{'ref': 'doc-fact-01@r1', 'since_turn': 1}]`. The row claiming
   nothing was evicted is the row whose only fact was just removed. `masked_rows`/`masked_entry` is the field
   that actually records the removal.

## Artifacts

- `experiments/ptr-engine/measure/answer-shape-diagnosis-TX03.md` — full 48-row table, per-fact timeline,
  bucket counts, the two field defects, and the cause-1-vs-2 discriminator.

## Discriminator if cause 1 and 2 counts were close

0 hits vs ≥1 hit with an offset in the byte-identical prompt is the primary test. Confirmation test: re-render
the same turn with the fact body restored at its original position and again appended at the tail — pass in both
= cause 1 repaired by presence; pass only at the tail (or neither) = cause 2. Cause 2 predicts failure rising
with offset fraction at constant presence; cause 1 predicts failure fixed by the mask turn alone.

## Next

Re-score with the mask aware: a `NONE` at a probe turn whose fact was masked before the probe is a valid
arm-behaviour outcome, not a failed check. If the intent is to measure retention rather than masking, the
`d5+` probes must be moved inside the 4-turn window or the arm must use the pointer/fetch channel.
