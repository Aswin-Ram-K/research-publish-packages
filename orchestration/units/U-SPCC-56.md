# U-SPCC-56 — the index fix reaches the model, and the fetch arm's score is a lookup

Status: COMPLETE

## Target
Measurement only. No source, fixture, ledger or doc was changed. Artifacts:
`experiments/ptr-engine/measure/rows-e1-indexfix-2026-11-10.jsonl` (343 rows),
this card, and `orchestration/handoffs/U-SPCC-56.json`.

## Cell
```
TMPDIR=/home/zer0null/tmp-pytest .venv/bin/python experiments/ptr-engine/longrun/run_longrun.py \
  --fixture experiments/ptr-engine/longrun/tasks-v7/TX-03.v1.json \
  --arms spcc,masking-no-fetch,bounded-context-fetch --reps 1 --temperature 0 --seed 42 \
  --model occamy-1.0 --base-url http://192.168.2.168:8012/v1 \
  --tools read_file --claim-mode E1 --budget-cap 12094 \
  --run-id e1-indexfix-2026-11-10 \
  --rows experiments/ptr-engine/measure/rows-e1-indexfix-2026-11-10.jsonl
```
Exit 0. 343 requests (100 spcc + 100 masking + 143 fetch; the fetch arm's 143 = 100 turn
rows + 43 follow-up rows). The brake did not fire: 9,024 + 343 = 9,367 of 12,094, headroom
2,727.

## Acceptance 1 — integrity
0 failed turns, 0 truncated, 0 errors on all three arms. Reconciliation delta 0 on every
row that carries one (99 / 99 / 142; the first turn of each arm has no prior request to
reconcile against).

## Acceptance 2 — per-arm buckets (deduped to one row per checkpoint)
|arm|value|contract|NONE|wrong|unparsed|graded|rows|requests|billed|
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|`spcc`|20|19|27|1|0|48|100|100|17,187|
|`masking-no-fetch`|8|8|30|10|0|48|100|100|18,724|
|`bounded-context-fetch`|48|48|0|0|0|48|143|143|51,715|

Every arm's four buckets sum to 48 = graded. No discrepancy.

## Acceptance 3 — the prefetch diagnostic (the centrepiece)
43 fetches, all `OK`, all on a ref the index now advertises. **Prefetch count = 0**: no
fact was fetched before its delivery turn. But the fetch arm's score is still a lookup
score, by a different route:

|relation to the checkpoint|count|
|---|---:|
|fetched on the checkpoint turn itself (lookup at answer time)|41|
|fetched on an earlier turn than the checkpoint (true retention)|0|
|fetched on a work turn (no checkpoint)|2|
|checkpoint answered with no fetch at all (true retention)|7|

41 of 48 checkpoints were answered by fetching the fact body **in the same turn the
question was asked**: the turn's initial response carries the question, emits the fetch
call, the harness services it, and the follow-up answers from the returned body. The
model never has to retain anything. The 7 no-fetch checkpoints (`f01.d2`, `f03.d2`,
`f01.d32`, `f03.d20`, `f05.d2`, `f07.d2`, `f07.d8`) are the only genuine retention
successes.

**Therefore the fetch arm's 48/48 measures lookup, not retention, and the spcc-vs-fetch
comparison is not a retention comparison.** The index fix did not create this — it
removed the `NOT_FOUND` noise that was masking it.

## Acceptance 4 — NOT_FOUND
**0**, down from 12. No invented refs remain: every one of the 43 attempts used a
`doc-fact-NN@r1` ref the index advertises. The index fix reached the model.

## Acceptance 5 — rounds
`max(fetch_rounds_this_turn) = 1`. The multi-round loop (U-SPCC-54) is **not** exercised
above one round: the model emits all its calls in a single response, so one round services
them all. Multi-*ref* servicing does work — `fetch_rows` reaches 3 (turn 21) and 2
(turn 28), i.e. the per-turn cap of 3 is reached by batching, not by a second round.
`max(fetch_rounds_used) = 42` of the per-arm pool.

`cp.TX-03.f04.d8` (turn 32) **is now serviced**: `ANSWER: NUM 3303`, verified, via
`doc-fact-04@r1` → `OK`. The last harness loss U-SPCC-54 named is closed.

## Acceptance 6 — gaps against the ±2/48 (±4.2 pp) band
|arm|value|contract|billed|
|---|---|---|---|
|`spcc`|21→20 (−1, in band)|20→19 (−1, in band)|14,827→17,187 (+15.9%, **out**)|
|`masking-no-fetch`|8→8 (0, in band)|8→8 (0, in band)|14,007→18,724 (+33.7%, **out**)|
|`bounded-context-fetch`|17→48 (+31, **out**)|17→48 (+31, **out**)|40,965→51,715 (+26.2%, **out**)|

The spcc and masking value/contract moves are inside the band. The fetch arm's +31 is the
index fix removing 12 `NOT_FOUND` guesses and 12 unparsed answers — it is a real effect,
not noise, but it is a lookup effect (see Acceptance 3). Billed is outside the band on all
three arms: the index is 13 lines instead of 1, so every prompt is larger.

The masking arm's `wrong` moved 0→10 (turns 6, 7, 9, 13, 14, 22, 23, 25, 29, 30 answered a
confident wrong `NUM` where the previous cell abstained with `NONE`). The errors are
cross-fact confusions — turn 6 asks `VAL_B` of `doc-fact-01` (3001) and answers 4000, which
is `VAL_A` of `doc-fact-04`. That is a real behavioural change from the new prompt bytes,
well outside the band.

## Comparability
`b38db8a` changed the prompt bytes for both arms. Nothing measured before it is comparable
to this cell.
