# V-TOOL-CHANNEL — verifier unit card

**Card:** `f6280fe0-2d24-4146-857c-3e86bf4851ce`, execution `6c1e3e8b-3647-44fc-999a-a072bb6d7b4a`
**Date:** 2026-10-26 · **Bound:** 30 tool calls · **Model requests:** 0 · **Network:** 0
**Posture:** autonomous verifier; did not write the change under test.

## Objective

Try to break `TOOL-CHANNEL-WIRE`'s claim on its own terms: byte neutrality of the tools-off
request body, single consumption when a reply carries both structured and text calls, malformed
arguments as recorded refusals, empty-content turns, text-fallback backwards compatibility,
`tools_schema_sent` label honesty, and finally whether a tools-on call reaches the fetch code and
puts a `<tool_result>` in the next prompt end-to-end in a fake harness.

## Claim under test

`TOOL-CHANNEL-WIRE` (author execution `dda84411`, PASS `f17663d1`): sends a `read_file` schema +
mode-derived `tool_choice` only when `tools_enabled`, surfaces structured `tool_calls`, consumes
them before the text parser, records malformed arguments as refusals, stamps `tools_declared` +
`tools_schema_sent`, and leaves tools-off bytes at digest `f0499dd1…`.

## Method

1. Read the author's handoff + `docs/TOOL-CHANNEL-WIRE.md`, then the code
   (`client.py` body gate / `send_chat` stamp, `run_longrun.py` `calls_from_response`,
   `fetch_rounds`, `execute_tool_call`, `make_row`, `provenance_for`).
2. Build the two request bodies and hash them; attempt eight tools-off cfg shapes plus
   mutate-after-build to make a tools-off body gain a `tools` key.
3. Drive `fetch_rounds` with fake replies folded through the real `client.send_chat`: structured +
   text in one reply, four malformed shapes, empty content, text-only, and a full fetch.
4. Red→green: revert the gate in memory and confirm the byte-neutrality guard fails.
5. Quantify historical `on:read_file` rows across row files (labels only; no rewrite).

## Result

**overall: `partial`** — the wire and the consumer work (one call → one round → a real
`<tool_result>` in the next prompt), but: `start_line > end_line` is silently swapped instead of
refused; `execute_tool_call` drops `source`/`call_id` so rows cannot name the structured channel;
and three label paths (failure row `resp=None`, `TurnWallCap.as_response`, dry-run
`provenance_for`) can claim `tools_schema_sent=true` with no schema on any wire.

Artefacts: `experiments/ptr-engine/tests/test_tool_channel_attack.py` (22 pass + 1 strict xfail),
`docs/V-TOOL-CHANNEL.md`, `orchestration/handoffs/V-TOOL-CHANNEL.json`.

## Verdict row

`PASS f17663d1 bash -lc '/usr/bin/python3 -m pytest experiments/ptr-engine/tests/test_tool_channel_attack.py -q'`
(recorded before the handoff write).

## Containment

Forbidden paths untouched by this unit; `client.py` and `run_longrun.py` sha256 identical before
and after (`9b12b2ea…`, `4f40dde1…`). No row, fixture, grade or published page written.
**External change:** `cell.py` moved `a6446bfc… -> 0bddd4e0…` at 19:14:55 during the run, changed
by a concurrent gen-6 pin/launcher unit (its handoffs appeared in the same window), not by this
verifier; recorded in the handoff's `externalChanges`.
