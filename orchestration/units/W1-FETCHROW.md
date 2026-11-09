# W1-FETCHROW — fetched turn row id + tokenizer accounting

- `fetch_tool.py`: `parse_fetch_calls` raises on missing call id and always emits `tool_call_id`/`id`; `batched_fetch` threads id into every branch (including INVALID_ARGS) and raises when absent.
- `pointer_table.py`: `FetchResult` gains `tokenizer_reused`/`tokenizer_cache_hit`/`reused`; fetch records cache reuse instead of a silent zero.
- `arm_cd.py`: `parse_fetch_calls_from_response` synthesises a deterministic id for text-rendered calls; `service_fetches` raises on missing id.
- `run_longrun.py`: arm-D rows stamp `tool_call_id`, `tool_call_ids`, `tokenizer_reused`, `tokenizer_cache_hit`, `reused` beside `tokenizer_calls`.
- `tests/test_fetch_row.py`: asserts fetched turn tool_call_id == parsed id, fetch_rows==1, tokenizer_calls>=1 or reuse marker, masked_rows consistent.