# TOOLCALLFIX

Status: done

Offline fix:
- Rewrote D-arm checkpoint instruction in `run_longrun.checkpoint_prompt` so retrieval tool calls and the `ANSWER:` line are separate protocols; `ANSWER: CALL fetch(...)` is reserved for call-valued answers only. Shows structured shape `{"name":"fetch","arguments":{"ref":"doc-config@r1"}}` and a three-call round.
- Added guard `protocol_violation="answer_wrapped_tool_call"` on the row when an `ANSWER:` payload begins with `CALL fetch(`, exposed via `protocol_violation()` and `checkpoint_answer_fields()`.

Offline proof:
- Emitted instruction text at turn 20 printed for both arms (C uses retrieval-unavailable contract; D uses new two-protocol contract).
- Unit checks: `ANSWER: CALL fetch(...)` sets the violation field; `ANSWER: CALL foo(bar=1)` does not.

Live check (D arm only, turns 1-24, TX-01):
- Requests: 27 (24 turns + 3 fetch follow-ups). Cap 2840 -> 2867.
- T20: initial stop_reason=tool_calls (tool call issued yes), fetch_rows=3, refs doc-config@r1/doc-errors@r1/doc-constants@r1, outcomes OK/OK/OK, final answer_raw="ANSWER: NUM 3", answer_kind=NUM, matches expected 3.
- T22: initial stop_reason=tool_calls (tool call issued yes), fetch_rows=3, same refs/outcomes, final answer_raw="ANSWER: NUM 30", answer_kind=NUM, matches expected 30.

Accounting: 27 rows, all task_id TX-01, one fixture_sha256 44a1b4356536a0a55757ed2a4c90f5ef7f9d0541836007dc195a50ab3db2ec21. Cap advanced by exactly 27.

Rows: experiments/ptr-engine/measure/rows-toolcallfix-d-20261109T064028Z.jsonl
Handoff: orchestration/handoffs/TOOLCALLFIX.json
