# X1-CODE — pointer/fetch fixture fixes

Implemented X1.1, X1.2, X1.6, X1.7, X1.9, X1.10 in owned paths.

- `pointer_table.py`: bodies stored on `PointerEntry.body` (namespaced per entry) plus legacy `_BODIES`; added `reset_bodies()`. `FetchResult.tool_call_id` threaded via `fetch(..., tool_call_id=)`.
- `fetch_tool.py`: `parse_fetch_calls` captures call `id`; `batched_fetch` threads it into `FetchResult`; render emits non-null id.
- `arm_cd.py`: renamed `ARM_C`/`ARM_D`; memoised `_doc_entries` per `(fixture, tokenizer, turn)`; `resolve_fetch_budget` reads `fixture["fetch_budget_tokens"]` (raises ValueError if missing); `service_fetches` threads tool_call_id.
- `run_longrun.py`: markers via `make_ref` with missing revision raising ValueError; resolved fetch budget stamped as `fetch_budget_tokens` (and `tool_call_id`/`tool_call_ids`) on arm-D rows.

Leftover references in files not owned: `longrun/tests/test_arm_cd_wiring.py` still uses old arm names (`bounded-fetch`) and lacks `fetch_budget_tokens` in its fixture; sibling owns tests/fixtures and is expected to update. Checker not modified.