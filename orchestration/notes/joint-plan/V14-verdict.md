# V14 Verify — Verdict

## Checks
1. pointer_table.py: bodies keyed by `(task_id, ref)` via `_BODIES[(tid, ref)]`; `reset_bodies()` has live callers (mask path + tests); no `except Exception` or defaulting introduced in body lookup (only explicit `PtrStoreMissError`). Keying line: `_BODIES[(tid, ref)] = body`. Lookup lines: `key = (tid, safe_ref); if key in _BODIES: body = _BODIES[key]`.
2. Collision probe: two tables same ref different bodies → each fetch returns its own body (A=BODY-A, B=BODY-B). Declared-but-unstored ref raises `PtrStoreMissError`.
3. Arm-D row: `tool_call_id` non-null equal to parsed call id; `fetch_rows`=1; `masked_rows` in (0,None). FAIL: `tokenizer_calls`=0, `tokenizer_reused`=False, `reused`=False (no reuse marker consistent with body delivered).
4. grep: missing id raises `ValueError("fetch request missing tool_call_id")` in `batched_fetch`; no null write.
5. pytest: 24 passed, 1 failed (`test_fetch_row.py::test_fetched_turn_row`).

## Verdict
- overall: FAIL (1/25)
- pointer_table: PASS (keying + reset_bodies intact; no except-Exception/defaulting)
- fetch-row fields: tool_call_id + fetch_rows real; tokenizer reuse marker NOT wired (default 0/False)
- blocker: arm-D row lacks tokenizer_calls/reused marker consistent with delivered body
- next_unit_hint: W1FetchRow must populate tokenizer_calls or reused marker in run_longrun row
- not_reproduced: n/a
- overstated: W1FetchRow claimed fetch-row fields real
- unverified: tokenizer reuse marker wiring
- tool_calls: 5
- bound: V14-VERIFY