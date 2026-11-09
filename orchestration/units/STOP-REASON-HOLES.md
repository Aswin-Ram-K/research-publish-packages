# STOP-REASON-HOLES

Close the three gaps between the closed stop vocabulary and what the writer records, found by
`V-INSTRUMENTS`: `runaway_turn` had no producer; a tool-call stream could be labelled
`empty_response`; `max_tokens` was missing from 99 stage-1 rows so `length` needed an external
manifest. Labelling only — no guard threshold, row, grade, fixture or grader was touched.

## Write paths
`experiments/ptr-engine/longrun/client.py`, `run_longrun.py`,
`experiments/ptr-engine/longrun/tests/test_stop_reason_producers.py`, `docs/STOP-REASON.md`, this card,
`orchestration/journal|handoffs/STOP-REASON-HOLES.*`.

## Result
- `runaway_turn` **has a producer**: the row that ends the cell on `--runaway-turns` carries
  `runaway_abort: true` (wall cap, digest wall cap, tool-followup wall cap, ceiling signature),
  and `stop_reason_for_row` maps it to `runaway_turn`; a capped turn the run survives stays
  `turn_wall_cap`. `error` keeps the wall that fired (`turn_wall_cap`).
- Any `tool_calls`/`function_call` delta now latches `tool_calls_present`; the derived reason is
  `tool_calls` even with no finish chunk and no text. `empty_response` = nothing produced.
- `make_row` always writes `max_tokens` (sent ceiling, configured cap as fallback, never None),
  so rule 3 is computable from the row alone. Precedence order recorded unchanged in
  `docs/STOP-REASON.md` except the added tool-call step.
- Future rows only: historical rows keep `stop_reason: null`; nothing historical was patched.

## Evidence
`test_stop_reason_producers.py` 8/8; red: hole → `empty_response`, runaway → `turn_wall_cap`
(exit 6), green after restore. Neighbours green (exit 0): `test_client_ttft` 8/8,
`test_wire_client` 18/18, `test_guards` 6/6, `test_tool_channel3` 5/5,
`test_record_stop_reason` 9/9, `test_projection_calibration` 4/4. Two pre-existing reds not
caused by this unit: `test_tool_channel` (per-turn cap 3 vs the test's 24) and
`test_tool_channel2` (frozen baseline prompt drift, +61 B/turn).
