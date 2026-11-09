# UNIT TOOL-CHANNEL-ROOT-CAUSE

**Purpose (one):** explain, with a cited mechanism, where a tool call stops being a request and starts
being prose — and record which of the four candidate causes it is. **Diagnose only; no fix.**

**Bound:** 30 tool calls · ≤6 model requests outside the probe · exactly one live probe, 2 requests
(`thinking off`, `max_tokens 512`, no cell, no fixture).

**Write paths (declared):**
- `docs/TOOL-CHANNEL-ROOT-CAUSE.md`
- `measure/TOOL-CHANNEL-ROOT-CAUSE.json` (card-named path; the raw probe record sits at
  `experiments/ptr-engine/measure/probe-tool-channel-raw.json`)
- `experiments/ptr-engine/tools/tool_channel_root_cause_check.py`
- `experiments/ptr-engine/tests/test_tool_channel_root_cause.py`
- `orchestration/units/TOOL-CHANNEL-ROOT-CAUSE.md`
- `orchestration/handoffs/TOOL-CHANNEL-ROOT-CAUSE.json`
- `orchestration/journals/TOOL-CHANNEL-ROOT-CAUSE.jsonl`

**Forbidden (read only, never written):** `cell.py`, `run_longrun.py`, `run_a_star.py`, `analyze_stats.py`,
`grade_v5.py`, any fixture, pin, params, ledger, rows, grade file, published page.

**Kill condition:** if the live probe is refused by a gate (budget/ledger/endpoint), STOP and report the
refusal verbatim; do not raise a flag to get past it.

**Question answered:** `client_never_sends_tools` — `request_body()` (`client.py:317-346`) never carries
`tools`/`tool_choice`, so the model has no schema; the runner's `<tool_call>` text protocol
(`run_longrun.py:605-645`) is never requested by the prompt either. Probe: the same prompt with a `tools`
array returns `finish_reason="tool_calls"` and a structured `read_file` call; without it, prose refusal.
No server change; no operator approval.

**Evidence command:** `bash -lc '/usr/bin/python3 -m pytest experiments/ptr-engine/tests/test_tool_channel_root_cause.py -q'` → exit 0.
