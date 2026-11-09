# UNIT WIRE-CLIENT — the measured path runs the fixed client

**Status:** done · **Bound:** 28 tool calls · **Used:** 26 · **Requests sent: 0** (offline, every
stream faked; 192.168.2.168 never contacted).

## Why this unit exists

`WAVE-ABC-VERIFY` found the fixed TTFT latch living only in `experiments/ptr-engine/longrun/client.py`
while the runner kept executing its own inline stream loop with the old latch at
`run_longrun.py:1084-1085`:

    if (piece_c or piece_r) and ttft is None:
        ttft = time.perf_counter() - t0

blind to a first delta carrying only `tool_calls` — the exact contamination the survey found in the
p95 (grow 838.85 / compact 224.08 / stable 356.12 / lease-reopen 201.78 ms are NOT to be reused).
The fix was dead code for measured rows.

## What changed

1. **One implementation.** Deleted `run_longrun.py:959-1137` — the inline SSE parse, the duplicated
   TTFT latch, and the duplicated `RequestFailure` / `thinking_setting` / `thinking_kwargs` /
   `request_body` / `extract_usage`. `import client` at `run_longrun.py:62`; `send_chat` is now a
   one-line delegation at `run_longrun.py:998-1006`:
   `return client.send_chat(cfg, messages)`. The name is kept (and `request_body`, `thinking_*`,
   `extract_usage`, `RequestFailure` are re-exported from `client`) because the tool-channel tests
   monkeypatch `run_longrun.send_chat` and the manifest/dry-run hash bodies through `request_body`.
   The adapter parses nothing, times nothing, scrapes nothing.
2. **Row fields.** `make_row` now carries, unchanged from the client:
   `ttft_source`, `first_token_kind`, `cached_source`, `engine_metrics_before`, `engine_metrics_after`,
   `wall_ms`, `metrics_scrape` (`run_longrun.py:1190-1197`) plus `cached_tokens` (the client's seam
   value, so a measured `0` stays `0`). The legacy null-semantics reading is preserved beside it as
   `cached_tokens_normalized` so nothing historic loses a comparable column.
3. **Flags.** `client.add_metrics_scrape_argument(ap)` at `run_longrun.py:1793` gives
   `--metrics-scrape` / `--no-metrics-scrape`; the effective value is frozen in the manifest at
   `run_longrun.py:885` and stamped on every row. Precedence (`PTR_METRICS_SCRAPE`, default on) is
   the client's alone — the runner never re-implements it.
4. **Tests.** `experiments/ptr-engine/longrun/tests/test_wire_client.py`: (a) monkeypatched `client.send_chat` proves the runner
   calls it; (b) source audit forbidding any perf_counter/clock delta assigned to a ttft variable and
   any second SSE parse; (c) `ttft_ms=None` + `ttft_source="unavailable"` reaches the row as null and
   `wall_ms` is never substituted; (d) `cached_tokens=0` survives as 0; (e) `--no-metrics-scrape`
   reaches the client config. Each case carries its own RED assertion (`--red`, 5/5).
5. **`test_answer_contract.py` label.** The summary line printed the COMPLEMENT of the failure count
   while reading "FAILED" (`--red` → "0/26 assertions FAILED" beside a 26/26 header). It now prints
   `len(failures)/total FAILED`, and the pass case prints `26/26 assertions passed`. No other change.

## Evidence

| check | result |
|---|---|
| `experiments/ptr-engine/longrun/tests/test_wire_client.py` | 18/18 passed, rc 0 |
| `experiments/ptr-engine/longrun/tests/test_wire_client.py --red` | 5/5 pre-fix assertions failed as intended |
| `experiments/ptr-engine/longrun/tests/test_client_ttft.py` | 8/8 green, rc 0 |
| `experiments/ptr-engine/longrun/tests/test_answer_contract.py` | 26/26 passed; `--red` 26/26 FAILED |
| `experiments/ptr-engine/longrun/tests/test_grade_v5.py`, `test_analyze_stats.py` (8/8), `test_cell.py` | rc 0 |
| `experiments/ptr-engine/longrun/tests/test_tool_channel2.py`, `test_tool_channel3.py` | rc 0 |
| `experiments/ptr-engine/longrun/tests/test_tool_channel.py` | rc 1 `AssertionError: 3` — **pre-existing**, proved by rerunning with this unit's row edits reverted in place (same failure) |
| `--dry-run` (fixture `tasks-v5/runtime-v5/LR-01.v5.json`) | `would_send_total=192` before and after; prompts + all printed request bodies byte-identical (sha `ee367780684bb0cd`) |

## Assumptions

- `cached_tokens` on a row is now the client's seam value; the old `normalize_cached_tokens()` reading
  is kept as `cached_tokens_normalized` rather than overwritten, because the card requires the client
  value to reach the row unchanged while `normalize_cached_tokens`'s SGLang-null→0 rule is a
  documented invariant of the repo.
- `run_longrun.py` keeps module-level `send_chat`/`request_body`/`thinking_*`/`RequestFailure` names as
  aliases of the client's, so existing tests and callers keep working (CLI unchanged, so no new
  required flag and no changed default).

## Write paths

`experiments/ptr-engine/longrun/run_longrun.py`, `experiments/ptr-engine/longrun/tests/test_wire_client.py`,
`experiments/ptr-engine/longrun/tests/test_answer_contract.py` (label only),
`orchestration/units/WIRE-CLIENT.md`, `orchestration/handoffs/WIRE-CLIENT.json`.
(`client.py` needed no extension: it already exposes the seam fields, the precedence rule and the
parser hook; nothing was added.)
