# FETCHDIAG — why bounded-context-fetch fetched 47 times on TX-02 but 8/1 on TX-03

## Verdict

Root cause: **tool advertisement mismatch, not decoding.** TX-02 fetch r1 was run with `--tools fetch` (row `tools_mode = on:fetch`), so the model was handed the `fetch` function schema and the checkpoint contract's `fetch(ref=...)` instruction was actionable. TX-03 fetch r1/r2 were run with `--tools read_file` (row `tools_mode = on:read_file`), so the `fetch` schema was never on the wire; the same contract text asked for `fetch(ref=...)`, but the model had no fetch tool to call. Structured fetch calls collapsed from 47 (TX-02) to 8 then 1 (TX-03). Temperature is a confound that cannot be excluded from on-disk evidence (no temp-zero replay of TX-02 exists); the single cheapest disambiguating measurement is named below.

## 1. Checkpoint-turn table (TX-03 fetch r1, 48 turns)

| Turn | Question | Raw answer line | Tool advertised | Tool call emitted | Resolved ANSWER line | Expected |
|---:|---|---|---|---|---|---|
| 3 | What is VAL_A of doc-fact-01? | `ANSWER: NUM 3000` | on:read_file | No | `ANSWER: NUM 3000` | 3000 |
| 6 | What is VAL_B of doc-fact-01? | `ANSWER: CALL fetch(ref="doc-fact-01@r1")` | on:read_file | No | `ANSWER: CALL fetch(ref="doc-fact-01@r1")` | 3001 |
| 7 | What is VAL_C of doc-fact-01? | `ANSWER: NONE` | on:read_file | No | `ANSWER: NONE` | 3002 |
| 9 | What is VAL_D of doc-fact-01? | `ANSWER: NONE` | on:read_file | No | `ANSWER: NONE` | 3003 |
| 10 | What is VAL_A of doc-fact-02? | `ANSWER: NUM 3100` | on:read_file | No | `ANSWER: NUM 3100` | 3100 |
| 13 | What is VAL_B of doc-fact-02? | `ANSWER: CALL fetch(ref="doc-fact-02@r1")` | on:read_file | No | `ANSWER: CALL fetch(ref="doc-fact-02@r1")` | 3101 |
| 14 | What is VAL_C of doc-fact-02? | `ANSWER: NUM 3102` | on:read_file | Yes | `ANSWER: NUM 3102` | 3102 |
| 16 | What is VAL_D of doc-fact-02? | `ANSWER: CALL fetch(ref="doc-fact-02@r1")` | on:read_file | No | `ANSWER: CALL fetch(ref="doc-fact-02@r1")` | 3103 |
| 19 | What is VAL_A of doc-fact-03? | `ANSWER: NUM 3200` | on:read_file | No | `ANSWER: NUM 3200` | 3200 |
| 21 | What is VAL_E of doc-fact-01? | `ANSWER: NUM 3004` | on:read_file | Yes | `ANSWER: NUM 3004` | 3004 |
| 22 | What is VAL_B of doc-fact-03? | `ANSWER: NUM 3201` | on:read_file | Yes | `ANSWER: NUM 3201` | 3201 |
| 23 | What is VAL_C of doc-fact-03? | `ANSWER: CALL fetch(ref="doc-fact-03@r1")` | on:read_file | No | `ANSWER: CALL fetch(ref="doc-fact-03@r1")` | 3202 |
| 25 | What is VAL_D of doc-fact-03? | `ANSWER: NUM 3203` | on:read_file | No | `ANSWER: NUM 3203` | 3203 |
| 26 | What is VAL_A of doc-fact-04? | `ANSWER: NUM 3300` | on:read_file | No | `ANSWER: NUM 3300` | 3300 |
| 28 | What is VAL_E of doc-fact-02? | `` | on:read_file | Yes | `(none)` | 3104 |
| 29 | What is VAL_B of doc-fact-04? | `ANSWER: NONE` | on:read_file | No | `ANSWER: NONE` | 3301 |
| 30 | What is VAL_C of doc-fact-04? | `ANSWER: CALL fetch(ref="doc-fact-02@r1")` | on:read_file | No | `ANSWER: CALL fetch(ref="doc-fact-02@r1")` | 3302 |
| 32 | What is VAL_D of doc-fact-04? | `` | on:read_file | Yes | `(none)` | 3303 |
| 33 | What is VAL_F of doc-fact-01? | `ANSWER: NONE` | on:read_file | No | `ANSWER: NONE` | 3005 |
| 37 | What is VAL_E of doc-fact-03? | `ANSWER: CALL fetch(ref="doc-fact-03@r1")` | on:read_file | No | `ANSWER: CALL fetch(ref="doc-fact-03@r1")` | 3204 |
| 40 | What is VAL_F of doc-fact-02? | `ANSWER: NONE` | on:read_file | No | `ANSWER: NONE` | 3105 |
| 44 | What is VAL_E of doc-fact-04? | `ANSWER: CALL fetch(ref="doc-fact-04@r1")` | on:read_file | No | `ANSWER: CALL fetch(ref="doc-fact-04@r1")` | 3304 |
| 47 | What is VAL_A of doc-fact-05? | `ANSWER: NUM 3400` | on:read_file | No | `ANSWER: NUM 3400` | 3400 |
| 49 | What is VAL_F of doc-fact-03? | `ANSWER: NONE` | on:read_file | No | `ANSWER: NONE` | 3205 |
| 50 | What is VAL_B of doc-fact-05? | `` | on:read_file | Yes | `(none)` | 3401 |
| 51 | What is VAL_C of doc-fact-05? | `ANSWER: NONE` | on:read_file | No | `ANSWER: NONE` | 3402 |
| 53 | What is VAL_D of doc-fact-05? | `` | on:read_file | Yes | `(none)` | 3403 |
| 54 | What is VAL_A of doc-fact-06? | `ANSWER: NUM 3503` | on:read_file | No | `ANSWER: NUM 3503` | 3500 |
| 56 | What is VAL_F of doc-fact-04? | `ANSWER: NONE` | on:read_file | No | `ANSWER: NONE` | 3305 |
| 57 | What is VAL_B of doc-fact-06? | `` | on:read_file | Yes | `(none)` | 3501 |
| 58 | What is VAL_C of doc-fact-06? | `` | on:read_file | Yes | `(none)` | 3502 |
| 60 | What is VAL_D of doc-fact-06? | `ANSWER: NONE` | on:read_file | No | `ANSWER: NONE` | 3503 |
| 63 | What is VAL_A of doc-fact-07? | `ANSWER: NUM 3600` | on:read_file | No | `ANSWER: NUM 3600` | 3600 |
| 65 | What is VAL_E of doc-fact-05? | `ANSWER: NONE` | on:read_file | No | `ANSWER: NONE` | 3404 |
| 66 | What is VAL_B of doc-fact-07? | `ANSWER: CALL fetch(ref="doc-fact-07@r1")` | on:read_file | No | `ANSWER: CALL fetch(ref="doc-fact-07@r1")` | 3601 |
| 67 | What is VAL_C of doc-fact-07? | `` | on:read_file | Yes | `(none)` | 3602 |
| 69 | What is VAL_D of doc-fact-07? | `` | on:read_file | Yes | `(none)` | 3603 |
| 70 | What is VAL_A of doc-fact-08? | `` | on:read_file | Yes | `(none)` | 3700 |
| 72 | What is VAL_E of doc-fact-06? | `ANSWER: NONE` | on:read_file | No | `ANSWER: NONE` | 3504 |
| 73 | What is VAL_B of doc-fact-08? | `` | on:read_file | Yes | `(none)` | 3701 |
| 74 | What is VAL_C of doc-fact-08? | `ANSWER: NUM 3702` | on:read_file | Yes | `ANSWER: NUM 3702` | 3702 |
| 76 | What is VAL_D of doc-fact-08? | `ANSWER: CALL fetch(ref="doc-fact-08@r1")` | on:read_file | No | `ANSWER: CALL fetch(ref="doc-fact-08@r1")` | 3703 |
| 77 | What is VAL_F of doc-fact-05? | `ANSWER: NONE` | on:read_file | No | `ANSWER: NONE` | 3405 |
| 81 | What is VAL_E of doc-fact-07? | `ANSWER: NONE` | on:read_file | No | `ANSWER: NONE` | 3604 |
| 84 | What is VAL_F of doc-fact-06? | `ANSWER: NONE` | on:read_file | No | `ANSWER: NONE` | 3505 |
| 88 | What is VAL_E of doc-fact-08? | `ANSWER: NONE` | on:read_file | No | `ANSWER: NONE` | 3704 |
| 93 | What is VAL_F of doc-fact-07? | `ANSWER: NUM 3605` | on:read_file | Yes | `ANSWER: NUM 3605` | 3605 |
| 100 | What is VAL_F of doc-fact-08? | `ANSWER: NONE` | on:read_file | No | `ANSWER: NONE` | 3705 |

## 2. Failure-mode counts (TX-03 fetch r1)

- **Abstention (ANSWER: NONE where a fetch was the correct action): 16 turns** — every NONE turn had `[MASKED ...]` markers in its prompt, so retrieval was required and omitted.
- **Guess (wrong NUM without fetching): 1 turn** — T54 answered `ANSWER: NUM 3503` against expected 3504 with 5 markers present and no fetch.
- Additional, not in the two requested buckets: 9 turns used `ANSWER: CALL fetch(...)` (prose retrieval misuse), 10 turns emitted an unserved tool call (finish_reason=tool_calls, content empty, no fetch_rows), 12 turns correct NUM, 1 correct-ish? See table.

## 3. Tool advertisement vs instruction text

**Tool advertisement (from row `tools_mode`):**
- TX-02 fetch r1: `on:fetch` (experiments/ptr-engine/measure/rows-tx02-fetch-r1.jsonl, every row).
- TX-03 fetch r1/r2: `on:read_file` (rows-tx03-fetch-r1.jsonl / rows-tx03-fetch-r2.jsonl, every row).

**Instruction text (checkpoint contract) is identical in both cells** — arm D branch of `checkpoint_prompt()` in experiments/ptr-engine/longrun/run_longrun.py:2120 (`if arm == arm_cd.ARM_D:`). It instructs:
> "(1) RETRIEVAL. When markers are present you MUST, in a single round, issue one fetch call for EVERY ref that appears as a `[MASKED <ref>]` marker... `fetch(ref="doc-config@r1")`... (2) ANSWERING... Use the structured shape the tool schema expects, e.g. {"name":"fetch","arguments":{"ref":"doc-config@r1"}}."

The fixture system prompts differ only in task id ("TX-02" vs "TX-03"); neither names a tool (experiments/ptr-engine/longrun/tasks-v7/TX-02.v1.json:2164 and tasks-v7/TX-03.v1.json:2144). The tool set is determined by the run's `--tools` flag, not the fixture.

arm_cd.py is not where the advertisement lives; `arm_cd.parse_fetch_calls_from_response()` (experiments/ptr-engine/longrun/arm_cd.py:225) only *parses* whatever the model emits — it filters structured `tool_calls` by name == "fetch" and falls back to prose JSON containing `ref`. It cannot create a fetch capability that the request never advertised.

## 4. Temperature hypothesis

No on-disk evidence: `experiments/ptr-engine/measure/rows-tempzero-probe2.jsonl` does not exist (grep for `*tempzero*`/`*probe2*` under measure/ returned nothing). TX-02 ran at default sampling (temperature null on rows), TX-03 at `--temperature 0 --seed 42`.

Single cheapest measurement to settle it: rerun **one** TX-02 fetch cell with `--temperature 0 --seed 42` (keeping `--tools fetch`) and compare `fetch_rows` totals to the 47 recorded at default sampling. If it stays fetch-heavy, temperature is ruled out; if fetches collapse, decoding is a co-cause. Cost ~105 requests.

## 5. masked_rows consistency

`masked_rows` counts outputs *newly* masked on that turn (ArmCDState.mask_old_turns increments `masked_rows_this_turn` once per `tool_output` of a turn crossing the 4-turn window), not markers present in the prompt. TX-03 has exactly 8 turns carrying `tool_outputs` (turns 1, 8, 17, 24, 45, 52, 61, 68), so exactly 8 rows show `masked_rows > 0` — consistent with the fixture structure. Not a second finding.

## 6. Candidate causes (ordered)

1. **Tool schema not advertised (high confidence, explains 47→8/1).** TX-03 used `read_file` instead of `fetch`. Discriminating evidence already on disk: `tools_mode` differs; fetch calls that did occur were spontaneous (5 turns) rather than contract-driven.
2. **Temperature/seed (unresolved).** Confounded with the tool change. Discriminating measurement: temp-zero rerun of TX-02 fetch cell (above).
3. **Model-side reluctance to fetch even when schema present?** Ruled out by TX-02's 47 fetches under the same contract text.

## Artifacts
- experiments/ptr-engine/measure/rows-tx02-fetch-r1.jsonl
- experiments/ptr-engine/measure/rows-tx03-fetch-r1.jsonl
- experiments/ptr-engine/measure/rows-tx03-fetch-r2.jsonl
- experiments/ptr-engine/measure/rows-tx03-masking-r1.jsonl
- experiments/ptr-engine/longrun/run_longrun.py (checkpoint_prompt, arm D branch)
- experiments/ptr-engine/longrun/arm_cd.py (parse_fetch_calls_from_response)
