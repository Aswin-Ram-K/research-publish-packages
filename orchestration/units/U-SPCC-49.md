# U-SPCC-49 — the fetch arm's dropped tool calls

**Status:** done. **Scope:** `experiments/ptr-engine/longrun/run_longrun.py` (response
parsing + `turn_calls` extraction for the fetch arm) and a new test file. `arm_cd.py`,
the answer contract, the scoring and the fetch budget are untouched.

## 1. The ten stranded checkpoints

`experiments/ptr-engine/measure/rows-e1-tools-2026-11-10.jsonl`, `arm ==
"bounded-context-fetch"`, `finish_reason == "tool_calls"`, `checkpoint != null`,
`tool_call_ids == null` — exactly ten rows, all `kind == "turn"`, all
`answer_parse_error == "no_answer_line"`, all `answer_kind == null`:

| turn | checkpoint | finish_reason | content | tool_calls | tool_call_ids | reasoning | completion_tokens | first_token_kind |
|---:|---|---|---|---|---|---|---:|---|
| 9 | `cp.TX-03.f01.d8` | tool_calls | `''` | absent | null | `''` | 33 | tool_call |
| 13 | `cp.TX-03.f02.d5` | tool_calls | `''` | absent | null | `''` | 57 | tool_call |
| 25 | `cp.TX-03.f03.d8` | tool_calls | `''` | absent | null | `''` | 53 | tool_call |
| 51 | `cp.TX-03.f05.d6` | tool_calls | `''` | absent | null | `''` | 57 | tool_call |
| 56 | `cp.TX-03.f04.d32` | tool_calls | `''` | absent | null | `''` | 53 | tool_call |
| 58 | `cp.TX-03.f06.d6` | tool_calls | `''` | absent | null | `''` | 33 | tool_call |
| 60 | `cp.TX-03.f06.d8` | tool_calls | `''` | absent | null | `''` | 57 | tool_call |
| 67 | `cp.TX-03.f07.d6` | tool_calls | `''` | absent | null | `''` | 53 | tool_call |
| 74 | `cp.TX-03.f08.d6` | tool_calls | `''` | absent | null | `''` | 57 | tool_call |
| 76 | `cp.TX-03.f08.d8` | tool_calls | `''` | absent | null | `''` | 34 | tool_call |

Three further checkpoint turns ended on `tool_calls` and were **serviced** (a
`turn-initial` row plus a graded `turn` row): turns 21, 73, 84. So the arm's tool-call
channel worked on 3 of 13 checkpoint turns and silently dropped the other 10.

`first_token_kind == "tool_call"` on all ten is the load-bearing field: the stream's
first token was a `delta.tool_calls` fragment, so the server DID signal a call and
`client.collect_stream` DID assemble it (`_accumulate_tool_call_deltas` →
`structured_tool_calls`). The loss is downstream of the client.

## 2. The cause

`run_cell`'s `arm == arm_cd.ARM_D` block (`run_longrun.py:3677`) reads the reply through
`arm_cd.parse_fetch_calls_from_response`, which delegates to
`ptr_engine/fetch_tool.py:82 parse_fetch_calls`. That parser keeps only calls whose
`function.name` is `"fetch"`:

```python
name = fn.get("name")
if name != "fetch":
    # still parse? spec says fetch calls; filter by name
    if name is not None and name != "fetch":
        continue
```

The schema actually on the wire is `read_file` (`TOOL_NAMES = ("read_file",)`,
`tools_mode="on:read_file"`, `tools_schema_sent=true` on every one of these rows). A
`read_file` call is therefore filtered out, `_calls` is empty, no follow-up is bought,
`content` stays `''`, and `checkpoint_answer_fields` parses it as `no_answer_line`. The
call is dropped **silently**: nothing on the row records that a call was ever signalled.

The generic path is not affected — `calls_from_response` (`run_longrun.py:990`) accepts
any structured call and `_call_from_arguments` reads `path`/`start_line`/`end_line`, so
`read_file` is serviced there. Only the D arm's fetch-only parser drops it.

## 3. The fix

`run_longrun.py` only:

* `unserviced_structured_calls(resp, calls)` — the structured calls the fetch parser did
  not consume (nothing consumed → all of them; otherwise those whose `id` is absent from
  the consumed ids).
* In the ARM_D block, any such call is preserved verbatim on the row
  (`tool_calls`, `unserviced_tool_call_ids`) and labelled
  `protocol_violation="tool_call_unserviced"`.
* The label is re-applied after `checkpoint_answer_fields` (turn row and `turn-initial`
  row), because those fields are derived from the empty content and would erase it.
* `row_extra["tool_calls"] = turn_calls` no longer overwrites a preserved call list.

Recording buys no request and spends no round: the answer contract, the scoring and the
fetch budget are unchanged. The row stops being *silently* unparsed.

## 4. Red → green

Red, against the pre-fix code (`tests/test_tool_call_capture.py`):

```
AssertionError: None != 'tool_call_unserviced' : a tool call the server signalled was
dropped silently: protocol_violation=None tool_calls=None answer_parse_error='no_answer_line'
AssertionError: None != 'tool_call_unserviced' : work-turn drop: tool_calls=[]
AttributeError: module 'run_longrun' has no attribute 'unserviced_structured_calls'
3 failed, 1 passed
```

The first line reproduces the ten real rows field for field. Green after the fix:

```
4 passed in 0.23s
```

Required trio: `test_tool_call_capture.py test_fetch_arm_row_persistence.py
test_arm_cd_wiring.py` → **15 passed**. `tools/doc_check.py` → exit 0.

## 5. What this does NOT do

The ten checkpoints still score `unparsed` — the model emitted no `ANSWER:` line, and
changing that would change the answer contract. What changed is that the row now carries
the call and the violation, so the loss is attributable instead of invisible. Servicing
`read_file` on a checkpoint turn would buy requests and spend rounds, which is a budget
change and out of scope for this unit.
