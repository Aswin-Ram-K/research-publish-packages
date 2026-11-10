# U-SPCC-54 — the fetch arm services up to the per-turn cap, not one round

Status: COMPLETE

## Target
`experiments/ptr-engine/longrun/run_longrun.py` (the `arm == arm_cd.ARM_D` follow-up loop),
`experiments/ptr-engine/longrun/tests/test_fetch_multi_round.py` (new). No other path touched.

## Defect closed
`TOOL_FETCH_ROUNDS_PER_TURN = 3` (`run_longrun.py:460`) and `fetch_rounds_cap_per_turn` was
stamped `3` on every row, but the D arm sent exactly ONE `_resp2` follow-up per turn:
`max(fetch_rounds_this_turn) == 1` across all 125 fetch rows of
`measure/rows-e1-parserfix-2026-11-10.jsonl`. A second call emitted on the same turn was
never serviced. `cp.TX-03.f04.d8` (turn 32) is the last harness loss it caused — the fetch
succeeded and the follow-up's own tool call was dropped.

## Changes
1. The D block is now `while _calls:` and services up to `fetch_rounds_per_turn(cfg)` rounds.
   After each follow-up it re-parses that response with
   `arm_cd.parse_fetch_calls_from_response(resp, tool_names=fetch_call_tool_names(cfg))` and,
   if the per-turn cap and the per-arm pool both allow, services the calls and sends again.
   It stops on: no further declared calls, `rounds_this_turn >= per_turn_cap`, or
   `fetch_rounds_used >= fetch_rounds_per_arm(cfg)`.
2. `rounds_this_turn` is now incremented on the D path, so `fetch_rounds_this_turn` and
   `send_index` on the turn row state the real per-turn round count (they were pinned at 0).
3. `_flush_d_rows(final=False)` — a new idempotent writer (`_d_initial_written` /
   `_d_flushed`) that persists the turn's paid rows in wire order. It is called at the TOP of
   each round after both guards pass, so every request already sent has its row on disk
   before the next one reaches the wire, and a round that turns out to be the LAST is never
   flushed early (the turn row still stands in its slot, so rows == sends).
4. The four failure handlers (`BudgetExhausted`, `CapRefusal`, `RequestFailure`,
   `TurnWallCap`) and the post-loop writer now call `_flush_d_rows()` instead of writing
   `kind="turn-initial"` inline, so no path can write one request's row twice.
5. `extras["tool_call_ids"]` accumulates across rounds instead of being overwritten.

## Unchanged
The per-turn cap, the per-arm pool, the answer contract and the scoring. A single response
carrying several calls is still serviced in ONE round (`service_fetches` batches), asserted
by `test_calls_in_one_response_share_one_round` so the fix cannot silently change it.

## Ref availability (reported, not changed)
The ARM_D prompt does NOT list the available refs. `Planner.build` (`run_longrun.py:1732`)
starts from `working_set_block` (`run_longrun.py:1747`), whose INDEX lines come from
`index_lines` (`run_longrun.py:366-373`) and read
`- @knowledge:{item['id']}@1 {hash8} {len}` — item ids in the `@knowledge:` namespace, not
`doc-<name>@r<rev>` refs. The only real refs a model can see are (a) `[MASKED <ref>]` markers
on masked turns (`run_longrun.py:1760`, `make_ref` = `{doc_id}@r{revision}`) and (b)
`TOOL_OUTPUT (doc_id@rev)` lines on the delivery turn. `checkpoint_prompt`
(`run_longrun.py:2366-2385`) teaches the ref FORM and three example refs
(`doc-config@r1`, `doc-constants@r1`, `doc-errors@r1`) that need not exist. So a model that
guesses from the INDEX produces exactly the 12 observed bad refs: `knowledge/item-1@1` and
`knowledge/item-1` are the INDEX id form, `ptr_engine/resolve.py` and
`knowledge/doc-fact-02.txt` are path-shaped guesses.

## Tests added (`tests/test_fetch_multi_round.py`, offline, fake client)
- `test_two_calls_on_one_turn_are_both_serviced` — a call on the turn's reply and another on
  the follow-up's reply: 3 sends, 2 rounds, 2 follow-up rows, both ids on the turn row.
- `test_calls_in_one_response_share_one_round` — unchanged batching: 2 calls, 1 round.
- `test_four_calls_stop_at_the_per_turn_cap` — 4 calls, cap 3: 4 sends, 3 rounds, the fourth
  call not serviced.
- `test_per_arm_pool_exhaustion_stops_the_loop` — pool 1: 2 sends, 1 round.
- `test_one_row_per_send_and_rows_precede_the_next_send` — 3 rounds: rows == sends (4), wire
  order `turn-initial, tool-followup, tool-followup, turn`, and the row count on disk at each
  send proves follow-up 1's row precedes send 3 and follow-up 2's row precedes send 4.

## Verification
Red (HEAD `run_longrun.py`, new test): `5 failed in 0.20s`, the headline being
`AssertionError: 2 != 3 : the turn's own send + one follow-up per serviced call`.
Green: `5 passed in 0.20s`.
Five-file suite: `25 passed, 2 subtests passed in 0.69s`.
`tools/doc_check.py` → `OK docs clean`, exit 0.
