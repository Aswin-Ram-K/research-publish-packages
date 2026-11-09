# UNIT HARNESS-GUARDS — stop a cell from running away

Status: **done** (see `orchestration/handoffs/HARNESS-GUARDS.json`).
Bound: ≤30 tool calls, **zero inference requests** (every stream faked; 192.168.2.168 never
contacted). Offline: `--dry-run` untouched and still offline.

## Purpose

`LIVE-SMOKE-CELL` (`dbed0e9d`, cancelled) produced a 16,384-token, 475,873 ms turn and had
to be stopped by a human. The measurement path was sound; the RUN was unguarded. This unit
adds the guard at three layers: the request, the turn, and the preflight projection.

## TASK 1 — the request always carries a finite `max_tokens` (`client.py`)

- `client.DEFAULT_MAX_TOKENS = 4096`; `DEFAULT_THINKING = "off"`.
- `coerce_max_tokens(value)` refuses `None`/0/negative/bool with `ValueError`.
- `request_body(cfg, messages, max_tokens=None)` always sets `max_tokens` — explicit
  argument > `cfg.max_tokens` > 4096. There is no path that omits it.
- `send_chat(..., max_tokens=None, wall_cap_s=None)` sends that value and reports it in the
  row (`max_tokens`), so the row stays truthful.
- Runner default `--max-tokens` is now **4096** (was 16384) and `--thinking` defaults to
  **off**; every row already carries `thinking` and `max_tokens`.

## TASK 2 — a per-turn wall ceiling (`client.py` + `run_longrun.py`)

- `client.collect_stream(..., wall_cap_s=...)` checks the clock on every chunk. Past the
  cap it abandons the fold and raises `client.TurnWallCap`, which carries the partial fold;
  the caller's `with opener(...)` closes the socket, so the stream is **not drained**.
- The row is written with `error="turn_wall_cap"`, `truncated=true`, and honest partial
  fields (`ttft_source`, `first_token_kind`, `completion_tokens` = emitted delta pieces,
  `wall_ms`, `max_tokens`, `turn_wall_cap_s`).
- `run_longrun.py --turn-wall-cap` (default **180** s). Escalation is one stderr line:
  `RUNAWAY T<n> (kind): wall=…s completion_tokens=… cap=…s — stream CLOSED, turn ABORTED, …`
- `--runaway-turns` (default **2**). A runaway turn is (1) one that hit the wall cap, or
  (2) **predicate 2**: a turn whose `completion_tokens` reaches/exceeds `max_tokens`
  (`truncated` at the ceiling — the turn-5 signature) or exceeds it (a server ignoring the
  ceiling). When that many have been seen the runner prints `RUNAWAY ABORT`, keeps the
  partial rows, and exits **6**.

## TASK 3 — preflight projection, exit 8 (`cell.py`)

- New flags `--turn-wall-cap` (180), `--runaway-turns` (2), `--max-wall` (3600), forwarded
  to the runner.
- `stage_projection` computes `projected_wall = projected_requests x --turn-wall-cap`
  (`projected_requests` is the runner dry-run's `would_send_total`; every request may burn
  the full per-turn cap) and refuses with **exit 8** when it exceeds `--max-wall`. One line:
  `cell: 3b/7 projection turns=48 projected_requests=48 projected_wall=8640s cap=3600s …`
- **Placement deviation (recorded):** the check runs immediately after `stage_budget`,
  before `stage_run`, not inside stage 1. It consumes that stage's `would_send_total`, and
  running it earlier would preempt the contracted budget refusal (exit 3) on
  `tests/test_cell.py::check_budget_refusal` (`--turns 48`, `--budget 100`). No live request
  has been sent at that point: the only process run was the offline `--dry-run`.
- For a 48-turn v5 cell the projection is **8640 s** against the 3600 s default → refused
  before a single request. That is the check the cancelled cell lacked.

## TASK 4 — the evidence is written down

`experiments/ptr-engine/measure/RUNAWAY-INCIDENT.md`: the five-row table, the sixth row
(second runaway), the `ttft_source`/`first_token_kind`/`cached_source` proof that the
measurement path is sound, `ttft_ms != wall_ms`, and the sentence that the cell was stopped
by a human decision — the defect this card removes.

## TESTS — `experiments/ptr-engine/longrun/tests/test_guards.py`, offline, red→green each

`6/6 GREEN`, exit 0. Each case also runs its red half:

- (a) captured outgoing payload always has `max_tokens == configured` (777, override 321,
  default 4096 when the attribute is absent); the pre-fix body fails the contract. Invalid
  caps raise.
- (b) a fake endless stream trips the cap → `TurnWallCap`, stream `closed == True`, row
  fields `truncated=true`; the same fold without the cap reads to the end.
- (c) a fake localhost SSE server: `--runaway-turns 2` → **exit 6**, exactly 2 partial rows,
  each `error="turn_wall_cap"`, `truncated=true`; with `--runaway-turns 99` the same cell
  runs all 4 turns and exits 0 (the stop is the guard's).
- (c2) cap row records `error`/`truncated`, `ttft_source="first_delta"`,
  `first_token_kind="reasoning"`, `ttft_ms != wall_ms`, `max_tokens=4096`.
- (d) `cell.py` exits **8** with `projected_wall=8640s` before the runner is invoked (marker
  file absent); with `--max-wall 0` the runner IS invoked (red).
- (e) `DEFAULT_THINKING == "off"`, the payload sends `enable_thinking: false`, the row
  records `thinking="off"`; `auto` omits the switch (red).

## Verification run

- `python3 experiments/ptr-engine/longrun/tests/test_guards.py` → `6/6 GREEN`, exit 0.
- `python3 tests/test_cell.py` → `Ran 7 tests … OK` (unchanged).
- `python3 experiments/ptr-engine/longrun/tests/test_client_ttft.py` → `8/8 cases green` (unchanged).
- `python3 experiments/ptr-engine/longrun/tests/test_wire_client.py` → `18/18 assertions passed` (unchanged).
- `python3 experiments/ptr-engine/longrun/tests/test_tool_channel.py` → fails at `assertion_f_followup_accounting`
  (`rounds == 3`, expected `TOOL_FETCH_ROUNDS_PER_ARM`). **Pre-existing and unrelated**: the
  failing assertion is fetch-round accounting, which this unit does not touch.
- `pytest tests_thinking_flag.py` → `test_unknown_setting_is_refused` fails
  (`thinking_kwargs("maybe")` does not raise). **Pre-existing**: `thinking_kwargs` was not
  modified by this unit.

## Assumptions (recorded)

1. `--turn-wall-cap` is checked when a chunk arrives; a server that stalls without emitting
   is bounded by `--timeout` (unchanged) rather than by the turn cap.
2. `completion_tokens` on an aborted turn is the count of emitted delta pieces, not a
   server-reported usage figure (the usage chunk never arrives on a closed stream).
3. A wall-cap on a *digest/planning* request aborts the whole cell with exit 6 immediately
   (rare; no partial turn to resume).
4. `--max-wall 0` disables the projection (used by the red half of test (d)).
