# UNIT TOOL-CHANNEL-WIRE

**Purpose (one):** make the tool channel real on both ends — put the `read_file` schema on the wire
(gated so a tools-off body is byte-identical) **and** consume the structured `tool_calls` reply that a
tools-on turn returns, proving both halves offline with fake responses and zero network.

**Bound:** 40 tool calls · **0 model requests** (the mechanism is already proven by the live probes in
`docs/TOOL-CHANNEL-ROOT-CAUSE.md` §3; this card wires it and proves it with fake responses). No live
cell, no canary, no pin generation.

**Write paths (declared):**
- `experiments/ptr-engine/longrun/client.py`
- `experiments/ptr-engine/longrun/run_longrun.py`
- `experiments/ptr-engine/tests/test_tool_channel_wire.py` (new)
- `docs/TOOL-CHANNEL-WIRE.md` (new)
- `orchestration/units/TOOL-CHANNEL-WIRE.md`
- `orchestration/handoffs/TOOL-CHANNEL-WIRE.json`
- `orchestration/journals/TOOL-CHANNEL-WIRE.jsonl`

**Forbidden (read only, never written):** `cell.py`, `run_a_star.py`, `analyze_stats.py`, `grade_v5.py`,
any fixture, pin, params, ledger, row, grade file, published page. Do not re-run the canary.

**Contract (what the code must do):**
1. `client.request_body()` includes `tools=[read_file schema]` and `tool_choice` **only** when
   `tools_enabled(cfg)`; a tools-off body stays byte-identical (`request_digest` unchanged).
2. `client.send_chat()` surfaces `message.tool_calls` as data (name + parsed arguments + parse error),
   assembling streamed call deltas by index; `run_longrun.calls_from_response()` consumes structured
   calls FIRST and falls back to the text `<tool_call>` parser only when there are none.
3. A malformed arguments payload is refused and **recorded** (`error="malformed_tool_arguments"`,
   `billed=False`), never a silent no-op.
4. Row honesty: `tools_mode` keeps its declared meaning; every row now also carries `tools_declared`
   and `tools_schema_sent`. Historical `on:read_file` rows were a FALSE label (no schema was ever sent)
   and are not retrofitted — recorded instead.

**Kill condition:** if a fake-response proof cannot be made to pass without touching a forbidden file,
STOP and report the blocker with the failing assertion; do not reach for a live request.

**Pin consequence (must be stated, not acted on):** `client.py` and `run_longrun.py` are `HARNESS_FILES`,
so pin generation 5 is stale; generation 6 is the precondition of the next (live canary) card. This unit
does not generate it.
