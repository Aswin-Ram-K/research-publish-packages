# U-SPCC-48 — the fetch arm fetched: E1's three-arm cell, first non-degenerate run

## What was run

The cell from the shared context, verbatim, against the live SGLang endpoint:

```
run_longrun.py --fixture experiments/ptr-engine/longrun/tasks-v7/TX-03.v1.json \
  --arms spcc,masking-no-fetch,bounded-context-fetch --reps 1 \
  --temperature 0 --seed 42 --model occamy-1.0 \
  --base-url http://192.168.2.168:8012/v1 --tools read_file --claim-mode E1 \
  --budget-cap 12094 --run-id e1-tools-2026-11-10 \
  --rows experiments/ptr-engine/measure/rows-e1-tools-2026-11-10.jsonl
```

`--arms` is comma-separated (`run_longrun.py:4086`), so the three-arm form is correct as
written. The `U-SPCC-46` guard did not fire: `--tools read_file` reached the arm.

## Integrity

`rows=318 requests=318 truncated=0 failed_turns=0`, all `finish_reason` in
`{stop: 304, tool_calls: 14}`, `content_source` `{content: 305, none: 13}`.

Per-arm cap-gate reconciliation, all delta 0:

| arm | spent_at_start | used_in_run | spent_after | delta |
|---|---:|---:|---:|---:|
| `spcc` | 8381 | 100 | 8481 | 0 |
| `masking-no-fetch` | 8481 | 100 | 8581 | 0 |
| `bounded-context-fetch` | 8581 | 118 | 8699 | 0 |

Programme spend after the cell: **8,699 of 12,094** (headroom 3,395).

## `tools_mode` — the check `e4692f8` failed

The manifest carries no `tools_mode` / `tools_schema_sent` key (its `tools` block is the
launch-time policy, not the wire fact). The wire fact is stamped on every row:

| arm | `tools_mode` | `tools_schema_sent` | `tools_declared` |
|---|---|---|---|
| `spcc` | `on:read_file` ×100 | `true` ×100 | `true` ×100 |
| `masking-no-fetch` | `off` ×100 | `false` ×100 | `false` ×100 |
| `bounded-context-fetch` | `on:read_file` ×118 | `true` ×118 | `true` ×118 |

`masking-no-fetch` is `off` by design — `run_cell` clears `cfg.tools` for `ARM_C`.

## Scores (`score_answer_contract_rows`, one call per arm)

| arm | value_correct | contract_correct | NONE | wrong | unparsed | graded | total | requests |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `spcc` | 22 | 21 | 26 | 0 | 0 | 48 | 48 | 100 |
| `masking-no-fetch` | 8 | 8 | 40 | 0 | 0 | 48 | 48 | 100 |
| `bounded-context-fetch` | 22 | 22 | 11 | 4 | 10 | 48 | 48 | 118 |

`spcc`'s 22 value vs 21 contract is the same `TEXT 3700` kind-mismatch row as `e4692f8`
(`kind_mismatch_value_correct: 1`). `spcc` and `masking-no-fetch` reproduce `e4692f8`
exactly (22/21 and 8/8), which is the expected result of a byte-identical prompt path.

## The fetch arm actually fetched

- **18 of 48 fetch rounds used** (`sum(fetch_rounds_this_turn) = 18`; 18 `turn` rows carry
  `fetch_rows >= 1` and a `retrieval_attempt` with `outcome: OK`). 20 fetch rows returned
  in total — one round returned 3 rows, the other 17 returned 1.
- **18 checkpoints were answered on a follow-up request whose prompt carried a fetched
  body** (`fetch_tokens` 20 on 17 rows, 60 on 1). 15 of those 18 were correct.
- `fetch_prompt_serves = 0` on every row: the serve-from-prompt optimisation never fired,
  so every one of the 18 rounds was a real disk read.
- Refs fetched: `doc-fact-01@r1` ×4, `-02` ×1, `-03` ×3, `-04` ×3, `-05` ×1, `-06` ×2,
  `-07` ×2, `-08` ×2.

## Protocol violations

16 rows carry `protocol_violation: answer_wrapped_tool_call`, all on `bounded-context-fetch`
`turn-initial` rows — the model wrote `ANSWER: CALL fetch(ref="doc-fact-01@r1")` as text
instead of emitting a native tool call. The harness still parsed it and bought the
follow-up, so these are not stranded: each has a matching `turn` row with the fetched
answer. 2 of the 18 `turn-initial` rows (turns 21, 73) carry no violation.

## The fetch arm's 10 unparsed checkpoints

10 checkpoints ended on a `turn` row with `finish_reason: tool_calls`, `content: ""`,
`content_source: none`, `tool_calls: []`, `tool_call_ids: null`, `fetch_rows: null` and
`fetch_rounds_this_turn: null` — the model emitted a native tool call that the harness did
not capture into `turn_calls`, so no fetch ran and no follow-up was bought. They grade
`unparsed`. Affected: `f01.d8`, `f02.d5`, `f03.d8`, `f04.d32`, `f05.d6`, `f06.d6`, `f06.d8`,
`f07.d6`, `f08.d6`, `f08.d8`. A further checkpoint, `cp.TX-03.f02.d8` (turn 16), has only
an interim row and is `ungradeable`.

The 4 wrong values are all `d2` probes answered with a neighbouring fact's value:
`f02.d2` 3003≠3100, `f02.d6` 3100≠3102, `f04.d2` 3203≠3300, `f08.d2` 3703≠3700.

## Gaps against the noise band

Measured noise floor: ±2/48 = ±4.17 pp (temperature 0 + seed 42 is not reproducible on this
endpoint; 6/100 turns flip on byte-identical prompts).

| comparison | value gap | contract gap | exceeds ±4.17 pp? |
|---|---:|---:|---|
| `spcc` − `masking-no-fetch` | +14/48 = +29.2 pp | +13/48 = +27.1 pp | **yes, both** |
| `bounded-context-fetch` − `masking-no-fetch` | +14/48 = +29.2 pp | +14/48 = +29.2 pp | **yes, both** |
| `bounded-context-fetch` − `spcc` | 0 | +1/48 = +2.1 pp | no, both |

The only arm-to-arm difference that survives the noise band is the masking contrast: both
tool-enabled arms beat `masking-no-fetch` by ~29 pp. The fetch arm is **not** separable
from `spcc` on this cell — its 22/48 value and 22/48 contract sit inside the band of
`spcc`'s 22/21, and it pays 18 extra requests and 10 unparsed checkpoints for that.

## Two stamping defects found (not fixed — out of scope, would change `harness_sha256`)

1. `fetch_rounds_used` is initialised to 0 at `run_longrun.py:3359` and **never
   incremented**; it is only ever set from a resume. Every row stamps 0 (52 rows) or null
   (66 rows), and the manifest's `tools.fetch_rounds_used` stays 0. The working counter is
   `fetch_rounds_this_turn`, which sums to the correct 18.
2. The manifest's `tools` block is frozen at launch and never updated at finalisation, so
   `tools.fetch_rounds_used` reports 0 for a run that spent 18.

## Not done

No ledger, `docs/STATE.md`, `FINDINGS-LEDGER.md`, journal or `orchestration/STATUS.md`
write — the numbers are reported for the main agent to record.
