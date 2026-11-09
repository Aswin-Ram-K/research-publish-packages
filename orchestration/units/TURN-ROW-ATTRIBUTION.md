# TURN-ROW-ATTRIBUTION

Give a turn's own send its own measurement; state which published per-turn figures were computed
on the wrong request. Bound 34 calls. Offline: zero inference requests. Never edit a rows file or a
grade file.

## What was done
1. `run_longrun.py`: the initial send keeps its own response object (`initial_resp`, :2116), gets
   its own row `kind="turn-initial"` (`send_index=0`, `initial_send=true`), written in wire order
   ahead of the follow-ups (:2240-2258). The last follow-up's row IS the `kind="turn"` row
   (`send_index=k`, `fetch_followup=true`, `fetch_round_final=true`), so no request is measured
   twice and the row count per turn is unchanged (k+1). `send_index` on every row; new extras
   (`row_measurement_source`, `final_round_billed`, `final_round_prompt_served`,
   `next_request_kind`) are additive; no existing field changed meaning. The abort paths
   (`TurnWallCap`, fetch `RequestFailure`) also write the initial row.
2. `docs/ROW-MODEL.md`: the stated model (which row carries which request, per-request vs
   per-turn fields), the invariant, the mirror accounting per tools grid, and the
   `attribution_disputed` list of published figures.
3. `experiments/ptr-engine/longrun/tests/test_row_attribution.py`: k=0,1,2,3 end-to-end through `run_cell` with a canned
   `send_chat` (zero requests); one row per send, distinct ttft per send, turn prompt hash; the
   red->green reverts the fix **in memory** (`attribute_initial_send=lambda: False`).
4. `tools/row_attribution_audit.py` -> `measure/ROW-ATTRIBUTION.json`: mirrors per tools grid
   (G7 17/48, G8 3/48, G9 13/48; all tools-off grids 0), disputed published figures, and the
   rows-file sha256 before/after (identical).

## Result
- invariant now holds: distinct `request_sha256` per turn == sends; no duplicate measurement.
- red->green: 4 green cases; red run = 3 rows / 3 sends / 2 distinct measurements.
- disputed: G7 p50, **G8 p50 `143.91` and p95 `397.41 n=70`**, **G9 p50 `147.59` and p95
  `429.70 n=61`** - the only two published p95 values left are both attribution-disputed.
- rows files: sha256 unchanged (yes).
- future cell must read `kind="turn-initial"` for the turn's own request, `kind="turn"` for the
  final response, and count requests by distinct `request_sha256`.

## Not touched / reported
`experiments/ptr-engine/longrun/tests/test_cap_gate.py:205` (literal kind expectation superseded by one-row-per-send; its intent
still passes), `test_tool_channel.py:201`, `test_tool_channel2.py:294`, `test_regrade.py:57`,
`test_guards`, `test_projection_calibration` (pre-existing), `test_decidability_seam` (out of scope).
