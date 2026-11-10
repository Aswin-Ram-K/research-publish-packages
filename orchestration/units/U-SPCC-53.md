# U-SPCC-53 — the fetch arm's calls are serviced, and the arm is worse than the floor

**Status:** DONE. 325 endpoint requests, 0 failed turns, 0 truncated, reconciliation delta 0.

## Why this cell exists

`U-SPCC-52` (`1f0fcbc`) fixed the name drift: `ptr_engine/fetch_tool.py` kept only calls
named `fetch` while the wire schema declares `read_file`, so every `read_file` call was
filtered out, no follow-up was bought, and the checkpoint scored `unparsed`. The
previous cell's fetch figure of 22/48 was a **floor**, not a measurement, because 10
checkpoints at turns 9, 13, 25, 51, 56, 58, 60, 67, 74, 76 were stranded that way.

This is the first cell in which a `read_file` call is actually serviced.

## Prereg gate

The first invocation was refused before any request was sent:

```
G3 prereg: experiments/ptr-engine/research-seed-concepts/PREREG-SPCC.md has changed
(sha256 2f7790ad8f2915b8efa55eec87967eb9cf75c8d95e5d07f226c2500627ec0ee5) since
.../PREREG-SPCC.json was transcribed from it (pinned 5b7007ab...) — re-derive the
companion before an E* claim is adjudicated
PREREG REFUSED (exit 2): no row was written and no request was sent
```

The `.md` gained a dated deviation note (instrument observation + measured noise floor)
at 10:06; the companion was transcribed at 08:42. The note states in terms that "the
prediction, falsifier, controls and budget ceiling above remain binding and unedited".
E1's hypothesis, design, controls, falsifier and 200–500 request ceiling were re-read
against the prose and are unchanged, so only `doc_sha256` moved, plus a `provenance`
sentence recording the re-derivation. `PREREG-SPCC.md` itself was not touched.

## The cell

```
--fixture tasks-v7/TX-03.v1.json --arms spcc,masking-no-fetch,bounded-context-fetch
--reps 1 --temperature 0 --seed 42 --model occamy-1.0
--base-url http://192.168.2.168:8012/v1 --tools read_file --claim-mode E1
--budget-cap 12094 --run-id e1-parserfix-2026-11-10
--rows measure/rows-e1-parserfix-2026-11-10.jsonl
```

`rows=325 requests=325 truncated=0 failed_turns=0`, `finish_reason {"stop": 289,
"tool_calls": 36}`, `content_source {"content": 292, "none": 33}`,
`token_dist {"n": 325, "mean": 4.4, "p95": 7.0, "max": 71.0}`,
`tok_method=tiktoken:cl100k_base`. Fetch arm: `requests_sent=125 (budget 148; fetch
rounds 25/48)`.

## Per-arm result

| arm | value | contract | NONE | wrong | unparsed | graded | requests | billed |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `spcc` | 21 | 20 | 26 | 1 | 0 | 48 | 100 | 14,827 |
| `masking-no-fetch` | 8 | 8 | 40 | 0 | 0 | 48 | 100 | 14,007 |
| `bounded-context-fetch` | 17 | 17 | 18 | 1 | 12 | 48 | 125 | 40,965 |

The four buckets sum to 48 on every arm (21+26+1+0, 8+40+0+0, 17+18+1+12). An
independent per-checkpoint tally over the fixture's 48 ids reproduces the scorer exactly.
`billed` is the sum of `billed_tokens` over every row of the arm, the same convention as
`U-SPCC-51`; `masking-no-fetch` is byte-identical at 14,007, which is the check that the
convention did not move.

Programme spend 8,699 → **9,024 of 12,094**; headroom 3,070.

## The ten previously-stranded turns

| turn | checkpoint | what happened | outcome |
|---|---|---|---|
| 9 | `cp.TX-03.f01.d8` | follow-up, `doc-fact-01@r1` OK | **correct** 3003 |
| 13 | `cp.TX-03.f02.d5` | follow-up, `doc-fact-02@r1` OK | **correct** 3101 |
| 25 | `cp.TX-03.f03.d8` | follow-up, `doc-fact-03@r1` OK | **correct** 3203 |
| 51 | `cp.TX-03.f05.d6` | no call emitted at all | NONE |
| 56 | `cp.TX-03.f04.d32` | follow-up `knowledge/doc-fact-04.md` → NOT_FOUND | unparsed |
| 58 | `cp.TX-03.f06.d6` | follow-up, `doc-fact-06@r1` OK | **correct** 3502 |
| 60 | `cp.TX-03.f06.d8` | follow-up, `doc-fact-06@r1` OK | **correct** 3503 |
| 67 | `cp.TX-03.f07.d6` | no call emitted at all | NONE |
| 74 | `cp.TX-03.f08.d6` | no call emitted at all | NONE |
| 76 | `cp.TX-03.f08.d8` | follow-up `ptr_engine/resolve.py` → NOT_FOUND | unparsed |

5 of 10 now buy a follow-up and grade correct. 2 of 10 buy a follow-up that returns
`NOT_FOUND` because the model invents the ref. 3 of 10 never emit a call and answer
`NONE` — they were never parser casualties.

## Why the arm fell from 22 to 17

The 22 was a floor produced by a parser that dropped the calls. Servicing them changes
the trajectory: the fetched body enters the context and every later turn is conditioned
on it. The arm now spends 25 rounds and lands at 17/48, with 12 `unparsed`.

All 12 `unparsed` checkpoints are turns where the model called `read_file` with a ref
that does not exist:

| ref requested | outcome | count |
|---|---|---:|
| `doc-fact-0N@r1` | OK | 13 |
| `ptr_engine/resolve.py` | NOT_FOUND | 4 |
| `knowledge/item-1@1` | NOT_FOUND | 3 |
| `knowledge/doc-fact-02.txt` | NOT_FOUND | 1 |
| `knowledge/doc-fact-02@r1` | NOT_FOUND | 1 |
| `knowledge/doc-fact-04.md` | NOT_FOUND | 1 |
| `knowledge/doc-fact-06@r1` | NOT_FOUND | 1 |
| `knowledge/item-1` | NOT_FOUND | 1 |

25 attempts, 13 OK, 12 NOT_FOUND. Every NOT_FOUND turn ends with no answer.

`cp.TX-03.f04.d8` (turn 32) is the one exception: the fetch returned **OK** and the turn
still produced no answer, because the follow-up response was itself a `tool_call` and
the loop sends exactly one follow-up per turn. `fetch_rounds_cap_per_turn` is stamped
`3` on every row but `max(fetch_rounds_this_turn) == 1` across all 125 fetch rows: the
per-turn cap is declared and not implemented. That is the mechanism that strands the
second call, and it is why 12 checkpoints are `unparsed` rather than answered.

## Round pool

**Not binding.** 25 of 48 rounds used; the arm's request budget was 148 and it sent 125.
The pool that binds is the per-turn one, at 1.

## Partial range

**None.** No row in the file contains `start_line` or `end_line`; every `read_file` call
carried only `path`. The whole-body fallback for a partial-range request was never
exercised, so the deliberate non-mapping of `start_line`/`end_line` onto `range` is
untested by this cell.

## Protocol violations

`protocol_violation='tool_call_unserviced'`: **0 rows**. The name-drift label no longer
fires, which is the direct confirmation that `1f0fcbc` works.

`protocol_violation='answer_wrapped_tool_call'`: 3 rows, all fetch arm, turns 6, 7, 63
(`cp.TX-03.f01.d5`, `cp.TX-03.f01.d6`, `cp.TX-03.f07.d2`). Each has a matching turn row
that did fetch, so none stranded.

## Gaps against the ±2/48 band

| comparison | value | contract | billed |
|---|---|---|---|
| `spcc` − `masking` | +13 (outside) | +12 (outside) | +820 (spcc **above** masking) |
| `fetch` − `masking` | +9 (outside) | +9 (outside) | +26,958 |
| `spcc` − `fetch` | +4 (outside, 2.8 sd) | +3 (outside, 2.1 sd) | −26,138 |

E1's falsifier has three clauses and **one fires**: `spcc` billed tokens are above
masking (14,827 vs 14,007). The other two do not — `spcc` is not below fetch on
single-fact (21 vs 17), and `spcc` is strictly above masking on every distance class
(7/8, 4/8, 5/8, 3/8, 2/8, 0/8 vs 8/8, 0/8, 0/8, 0/8, 0/8, 0/8). The retention claim
from `U-SPCC-51` survives — `spcc` and `fetch` both beat masking by a wide margin — but
the "costs no more billed tokens than masking" clause does not.

## Writes

`orchestration/units/U-SPCC-53.md`, `orchestration/handoffs/U-SPCC-53.json`,
`experiments/ptr-engine/measure/rows-e1-parserfix-2026-11-10.jsonl`,
`experiments/ptr-engine/research-seed-concepts/PREREG-SPCC.json` (pin only).
No ledger, no `docs/STATE.md`, no `journal/`, no `orchestration/STATUS.md`, no
`PREREG-SPCC.md`, no fixture, no `ptr_engine/layers.py`, no `longrun/arm_cd.py`,
`longrun/claim_mode.py`, `longrun/cell.py`.
