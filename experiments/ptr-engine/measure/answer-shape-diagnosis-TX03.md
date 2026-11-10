# Why 40/50 TX-03 checks fail as `kind NONE != NUM`

Run: `measure/rows-spcc-billedproof-2026-11-10.jsonl` (arm `masking-no-fetch`, rep 1, 100 turns, model `occamy-1.0`).
Fixture: `longrun/tasks-v7/TX-03.v1.json` (`TX-03.v1`, gen-7). Zero live requests were made for this diagnosis.

## Method (decisive test, not inference)

Prompts were **re-materialised for all 100 turns** by driving `longrun/run_longrun.py`'s own `run_cell` with
`send_chat` replaced by a recorder (the pattern of `longrun/tools/prompt_at_turn.py`): the runner's own
`Planner`/`arm_cd` state builds each turn's prompt and each turn is fed the settled row's real answer.

Provenance: for every one of the 100 turns, `sha256(user content)` of the materialised prompt was compared with
the `prompt_sha256` stamped on the settled row — **100/100 byte-identical, 0 mismatches**
(`sha_mismatch_turns: []`). The texts searched below are therefore the exact bytes the endpoint received.
Network trip-wires (`urllib.request.urlopen`, `socket.create_connection`) were armed, and the runner's
`_http_get_json` health probe was replaced by an offline stub before the drive; cap-gate recorded
`used_in_run=100 delta=0`.

The expected value was searched in each checkpoint turn's prompt with a digit-boundary regex
(`(?<![\d.])<expected>(?![\d.])`) plus the anchor `VAL_<X> = <expected>`; token offset via `tiktoken cl100k_base`.

## Per-checkpoint result (all 8 passes and all 40 failures)

| checkpoint | turn | dist | expected | answer text | parsed kind | value in prompt | position (tok/total, frac) |
|---|---|---|---|---|---|---|---|
| cp.TX-03.f01.d2 | 3 | 2 | 3000 | `ANSWER: NUM 3000` | NUM | yes | 74/268 = 0.276 |
| cp.TX-03.f01.d5 | 6 | 5 | 3001 | `ANSWER: NONE` | NONE | no | — |
| cp.TX-03.f01.d6 | 7 | 6 | 3002 | `ANSWER: NONE` | NONE | no | — |
| cp.TX-03.f01.d8 | 9 | 8 | 3003 | `ANSWER: NONE` | NONE | no | — |
| cp.TX-03.f02.d2 | 10 | 2 | 3100 | `ANSWER: NUM 3100` | NUM | yes | 255/455 = 0.560 |
| cp.TX-03.f02.d5 | 13 | 5 | 3101 | `ANSWER: NONE` | NONE | no | — |
| cp.TX-03.f02.d6 | 14 | 6 | 3102 | `ANSWER: NONE` | NONE | no | — |
| cp.TX-03.f02.d8 | 16 | 8 | 3103 | `ANSWER: NONE` | NONE | no | — |
| cp.TX-03.f03.d2 | 19 | 2 | 3200 | `ANSWER: NUM 3200` | NUM | yes | 490/684 = 0.716 |
| cp.TX-03.f01.d20 | 21 | 20 | 3004 | `ANSWER: NONE` | NONE | no | — |
| cp.TX-03.f03.d5 | 22 | 5 | 3201 | `ANSWER: NONE` | NONE | no | — |
| cp.TX-03.f03.d6 | 23 | 6 | 3202 | `ANSWER: NONE` | NONE | no | — |
| cp.TX-03.f03.d8 | 25 | 8 | 3203 | `ANSWER: NONE` | NONE | no | — |
| cp.TX-03.f04.d2 | 26 | 2 | 3300 | `ANSWER: NUM 3300` | NUM | yes | 677/877 = 0.772 |
| cp.TX-03.f02.d20 | 28 | 20 | 3104 | `ANSWER: NONE` | NONE | no | — |
| cp.TX-03.f04.d5 | 29 | 5 | 3301 | `ANSWER: NONE` | NONE | no | — |
| cp.TX-03.f04.d6 | 30 | 6 | 3302 | `ANSWER: NONE` | NONE | no | — |
| cp.TX-03.f04.d8 | 32 | 8 | 3303 | `ANSWER: NONE` | NONE | no | — |
| cp.TX-03.f01.d32 | 33 | 32 | 3005 | `ANSWER: NONE` | NONE | no | — |
| cp.TX-03.f03.d20 | 37 | 20 | 3204 | `ANSWER: NONE` | NONE | no | — |
| cp.TX-03.f02.d32 | 40 | 32 | 3105 | `ANSWER: NONE` | NONE | no | — |
| cp.TX-03.f04.d20 | 44 | 20 | 3304 | `ANSWER: NONE` | NONE | no | — |
| cp.TX-03.f05.d2 | 47 | 2 | 3400 | `ANSWER: NUM 3400` | NUM | yes | 1194/1388 = 0.860 |
| cp.TX-03.f03.d32 | 49 | 32 | 3205 | `ANSWER: NONE` | NONE | no | — |
| cp.TX-03.f05.d5 | 50 | 5 | 3401 | `ANSWER: NONE` | NONE | no | — |
| cp.TX-03.f05.d6 | 51 | 6 | 3402 | `ANSWER: NONE` | NONE | no | — |
| cp.TX-03.f05.d8 | 53 | 8 | 3403 | `ANSWER: NONE` | NONE | no | — |
| cp.TX-03.f06.d2 | 54 | 2 | 3500 | `ANSWER: NUM 3500` | NUM | yes | 1381/1581 = 0.874 |
| cp.TX-03.f04.d32 | 56 | 32 | 3305 | `ANSWER: NONE` | NONE | no | — |
| cp.TX-03.f06.d5 | 57 | 5 | 3501 | `ANSWER: NONE` | NONE | no | — |
| cp.TX-03.f06.d6 | 58 | 6 | 3502 | `ANSWER: NONE` | NONE | no | — |
| cp.TX-03.f06.d8 | 60 | 8 | 3503 | `ANSWER: NONE` | NONE | no | — |
| cp.TX-03.f07.d2 | 63 | 2 | 3600 | `ANSWER: NUM 3600` | NUM | yes | 1622/1816 = 0.893 |
| cp.TX-03.f05.d20 | 65 | 20 | 3404 | `ANSWER: NONE` | NONE | no | — |
| cp.TX-03.f07.d5 | 66 | 5 | 3601 | `ANSWER: NONE` | NONE | no | — |
| cp.TX-03.f07.d6 | 67 | 6 | 3602 | `ANSWER: NONE` | NONE | no | — |
| cp.TX-03.f07.d8 | 69 | 8 | 3603 | `ANSWER: NONE` | NONE | no | — |
| cp.TX-03.f08.d2 | 70 | 2 | 3700 | `ANSWER: NUM 3700` | NUM | yes | 1809/2009 = 0.900 |
| cp.TX-03.f06.d20 | 72 | 20 | 3504 | `ANSWER: NONE` | NONE | no | — |
| cp.TX-03.f08.d5 | 73 | 5 | 3701 | `ANSWER: NONE` | NONE | no | — |
| cp.TX-03.f08.d6 | 74 | 6 | 3702 | `ANSWER: NONE` | NONE | no | — |
| cp.TX-03.f08.d8 | 76 | 8 | 3703 | `ANSWER: NONE` | NONE | no | — |
| cp.TX-03.f05.d32 | 77 | 32 | 3405 | `ANSWER: NONE` | NONE | no | — |
| cp.TX-03.f07.d20 | 81 | 20 | 3604 | `ANSWER: NONE` | NONE | no | — |
| cp.TX-03.f06.d32 | 84 | 32 | 3505 | `ANSWER: NONE` | NONE | no | — |
| cp.TX-03.f08.d20 | 88 | 20 | 3704 | `ANSWER: NONE` | NONE | no | — |
| cp.TX-03.f07.d32 | 93 | 32 | 3605 | `ANSWER: NONE` | NONE | no | — |
| cp.TX-03.f08.d32 | 100 | 32 | 3705 | `ANSWER: NONE` | NONE | no | — |

**8/8 passing checkpoints have the value present with exactly 1 hit and 1 anchor hit. 40/40 failing
checkpoints have 0 hits and 0 anchor hits.** Presence/absence is binary and separates pass from fail perfectly.

## Per-fact timeline (why the split is exactly d2 vs everything else)

`WINDOW_TURNS = 4` (`longrun/arm_cd.py:39`); masking fires at `cutoff = t - WINDOW_TURNS`.

| fact | intro turn | mask turn (ref `doc-<fact>@r1`) | checkpoint turns | outcomes |
|---|---|---|---|---|
| fact-01 | 1 | 5 |  |  |
| fact-02 | 8 | 12 |  |  |
| fact-03 | 17 | 21 |  |  |
| fact-04 | 24 | 28 |  |  |
| fact-05 | 45 | 49 |  |  |
| fact-06 | 52 | 56 |  |  |
| fact-07 | 61 | 65 |  |  |
| fact-08 | 68 | 72 |  |  |

Every checkpoint at `intro+2` (turns 3, 10, 19, 26, 47, 54, 63, 70) runs **before** its fact's mask at
`intro+4`, so the body is still in the prompt and the model answers correctly. Every `d5/d6/d8/d20/d32`
checkpoint runs **after** the mask and the body is gone.

Post-mask rendering, verbatim from the materialised T6 prompt (`doc-fact-01` introduced at T1, masked at T5):

```
QUESTION (T1): Work turn 1.
TOOL OUTPUTS:
[MASKED doc-fact-01@r1]
ANSWER (T1):
```

The body `# doc-fact-01 / VAL_A = 3000 / VAL_B = 3001 ...` is replaced by a 29-byte pointer marker carrying no
value. `3001` occurs 0 times in the T6 prompt. The one number still reachable at T6 is `3000`, and only because
T3's *answer line* `ANSWER (T3): ANSWER: NUM 3000` sits in the transcript — which is exactly why the early
probes pass and nothing after them does.

## Classification of the 40 failures

| bucket | n |
|---|---|
| 1. content evicted (fact masked out of the prompt before the probe) | **40** |
| 2. content present but not retrieved (position/attention) | 0 |
| 3. answer contract too strict (parser rejected a correct prose value) | 0 |
| 4. fixture unanswerable at that distance | 0 |
| unclassified | 0 |
| **total** | **40** |

The non-`d2` buckets are five widths (`d5`/`d6`/`d8`/`d20`/`d32`) × 8 probes = **40**, consistent with
`d2`'s 8. Bucket 2 is zero because no failing prompt contained the value at all: that is content absence,
not evidence that position has no effect. This run never holds a present value at two distances, so
position remains untested here — E3 (`experiments/ptr-engine/research-seed-concepts/PREREG-SPCC.md`) is the
arm that keeps the body present and varies distance.

- Cause 2 is not observed in this run, and is **not excluded as a mechanism**: all 40 failing prompts contain
  0 occurrences of the value, so they cannot exhibit present-but-unretrieved content. The 8 passing probes do
  retrieve at prompt fractions up to **0.74** of the request (f08.d2, token offset 1809 of 2455 request
  tokens), so a present value at depth is recoverable on this arm — but every passing probe is pre-mask `d2`,
  and no probe here holds the value present at two distances. Position therefore stays untested; see the note
  above the bucket table and E3 (`experiments/ptr-engine/research-seed-concepts/PREREG-SPCC.md`).
- Cause 3 is excluded: all 40 answers are the literal well-formed line `ANSWER: NONE`, parsed to
  `answer_kind=NONE` with `answer_parse_error=null`. Nothing was mis-parsed.
- Cause 4 is excluded: the source text was surfaced verbatim in the tool output at each fact's intro turn, and
  the `d2` probe on the same fact/doc answers correctly.

**Dominant cause: 1 — content evicted.** `ANSWER: NONE` is the arm behaving as designed; the scorecard's
`kind NONE != NUM` measures the mask, not a model defect. Evidence line: the T6 prompt contains
`[MASKED doc-fact-01@r1]` in place of the body and the string `3001` occurs 0 times in it.

## Two degenerate diagnostic fields (defects — do not cite as evidence)

1. **`expected_present` is meaningless.** `longrun/run_longrun.py:2581`:
   `expected_present = bool(contains_expected(reasoning_raw, expected)) if expected else False`
   — it tests the **reasoning channel**, not the prompt. `thinking` is off for this run, so `reasoning` is `""`
   on every row and the field is `False` on all 48 checkpoints **including the 8 that answered correctly**
   (`cp.TX-03.f01.d2`: expected `3000`, answer `NUM 3000`, `expected_present=False`). A field constant across
   success and failure cannot support any claim about absence.
2. **`evicted` is dead under this arm and contradicts `masked_entry`.** Initialised to `0` at
   `longrun/run_longrun.py:1453` and only assigned in the `transcript-grow` FIFO-truncation branch (`:1476`).
   Arm `masking-no-fetch` never enters that branch, so `evicted=0` on all 100 rows — including T5, where
   `masked_rows=1` and `masked_entry=[{'ref': 'doc-fact-01@r1', 'since_turn': 1}]`. The row that says "nothing
   evicted" is the row whose only fact was just removed; a reader trusting `evicted` would conclude masking
   never happened.

The field that does record removal is `masked_rows`/`masked_entry`, firing once per fact at `intro+4` for all
eight facts: turns 5, 12, 21, 28, 49, 56, 65, 72.

## What would distinguish cause 1 from cause 2 if the counts were close

Cause 1 is absence from the prompt; cause 2 is presence with failed retrieval. The discriminator is the
byte-identical prompt search above: 0 hits vs >=1 hit plus a token offset. If the counts were close, the
additional test is a **within-row paired probe** — re-render the same turn twice, once with the fact's body
restored at its original position and once appended at the tail; passing in both is cause 1 repaired by
presence, passing only at the tail (or neither) is cause 2. Prompt-length matching separates them too: cause 2
predicts failure rising with offset fraction at constant presence, whereas cause 1 predicts failure determined
solely by the mask turn, independent of offset.
