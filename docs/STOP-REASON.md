# STOP-REASON — a stop is explainable from the row alone

**Unit:** `RECORD-STOP-REASON` · **Status:** recording change only (no verdict, grader, guard
semantics or historical row was touched) · **Zero inference requests:** every stream in the
tests is a hand-built SSE fixture.

## Why

`STOP-REASON-AUDIT` (`10195e9e`) classified seven arm-checks as **`cap-exhausted`**: content
`""`, the sha of the empty string, `completion_tokens` **128 on all 99 empty rows**,
`http_status null`, `error null` — and **no `finish_reason`, no `truncated`, no `max_tokens`
and no `reasoning` on the row**. The 128 was a harness cap from
`experiments/ptr-engine/longrun/manifests/stage1-lr01-*`.

The consequence was structural: **a cap-exhausted generation and a silent refusal were
indistinguishable in the rows**, so the run had to be explained with sha-hunting and token
arithmetic instead of a `group by`. `HARNESS-GUARDS` raised the default ceiling and closes the
stream at a wall cap; this unit makes the row *say* why the response ended.

## The closed vocabulary

Recorded as `stop_reason` on every row. Nothing outside this tuple is ever written.

| `stop_reason` | meaning |
|---|---|
| `stop` | the server's own `finish_reason: "stop"` |
| `length` | a completion ceiling cut the generation short (server `finish_reason: "length"`, **or** no finish chunk with `completion_tokens >= max_tokens`) |
| `tool_calls` | the response ended with tool calls (`finish_reason: "tool_calls"`/`"function_call"`) |
| `content_filter` | server `finish_reason: "content_filter"` |
| `turn_wall_cap` | the harness closed the stream at `--turn-wall-cap` (`client.TurnWallCap`) |
| `runaway_turn` | the harness ended the cell on a runaway signature (`--runaway-turns` reached: the `--turn-wall-cap` abort, a planning-request wall abort, or the ceiling-consume signature). The row that ends the cell carries `runaway_abort: true`; a capped turn the run survives stays `turn_wall_cap` |
| `http_error` | the request failed with an HTTP status (`RequestFailure.status` set) |
| `stream_error` | the stream broke with no HTTP status |
| `empty_response` | no finish chunk and no usable content, under the ceiling |
| `unknown` | none of the above — never guessed |

Derivation precedence (`client.derive_stop_reason`, one implementation, used by both the
client and the row writer), unchanged in order since `STOP-REASON-HOLES` except for the
tool-call step it added:

1. harness error code (a code already in the vocabulary wins);
2. server `finish_reason` when it maps — an unmappable string is `unknown`, never a neighbour;
3. **no finish chunk but ANY `tool_calls`/`function_call` delta → `tool_calls`** (a dispatched
   call is a production, even with no text and no finish chunk);
4. no finish chunk with `completion_tokens >= max_tokens` (**this is the old 128-token case,
   and it is `length`**) — computable from the row alone, because every row now carries
   `max_tokens`;
5. no finish chunk, no tool-call delta and nothing produced (`empty_response`);
6. anything else: `unknown`.

## The fields, and where they land

`client.send_chat` returns, and `run_longrun.make_row` writes on **every** row:

- `finish_reason` — the finish reason that ended the stream;
- `finish_reasons` — **per choice**, `[{"index": 0, "finish_reason": "length"}, …]`, captured
  from the SSE stream and from the final chunk;
- `max_tokens` — the ceiling **as actually sent on the request**, read back out of the request
  body (`sent_cap`), never re-derived;
- `stop_reason` — one word of the closed vocabulary above;
- `truncated` — `true` iff `stop_reason == "length"`; `null` only when no response completed
  (`empty_response`, `http_error`, `stream_error`); `false` otherwise. `TurnWallCap` keeps
  `truncated: true` — a wall-capped turn *did* generate and *was* cut short, and the harness
  guards read that truthiness;
- `stop_evidence` — `true` when the row is a **contentless** `length` / `empty_response` /
  `http_error` stop: then `content_sha256` is the sha of the content it has (the **empty
  string's** sha when it has none) and `completion_tokens` is recorded even though no usage
  chunk ever arrived (`completion_tokens_source: "client_observed"`, `0` = the client observed
  nothing generated). A streamed response keeps `completion_tokens_source: "usage"`.

Row kinds that carry them: **turn rows**, **`kind="tool-followup"` rows** (written by
`run_longrun.fetch_rounds` through the same `make_row`) and the **failure rows**
(`resp=None` + `extra.error`). A follow-up the request allowance suppresses writes **no row of
its own** — the refusal is already recorded per call as `followup_suppressed` on the turn's
`tool_calls`; this unit adds the count `fetch_suppressed` to that turn row, whose `stop_reason`
is the response that ended the turn. No row count changes.

`run_longrun.summary_counts` now also reports `stop_reasons` (a `StopReason -> count` map), so
the audit is a `group by` over rows, not a sha hunt.

## Read-only re-derivation of `rows-cell-pointer-stable-20261026T145758Z.jsonl`

The file was **read only** — sha256 `5ac9dd992f5d8715696925f56c225024e172cb98b4b9a937a0ee63bd099e9800`
before and after the scan, unchanged. It holds **6** rows (the card said five; the file has
six — recorded, not corrected) and each already carries `finish_reason` and
`max_tokens: 16384`.

| # | turn | completion_tokens | stop_reason now | truncated |
|---|---|---|---|---|
| 1 | T1 | 7771 | `stop` | false |
| 2 | T2 | 1415 | `stop` | false |
| 3 | T3 | 856 | `stop` | false |
| 4 | T4 | 275 | `stop` | false |
| 5 | T5 | **16384** (= the ceiling) | **`length`** | **true** |
| 6 | T6 | 13126 | `stop` | false |

None of the six is a refusal; the one 16,384-token turn is a cap stop and the row now says so.
The audit's 99 empty 128-token rows live in a different file and were not rewritten.

## Evidence

- `experiments/ptr-engine/longrun/tests/test_record_stop_reason.py` — 9 checks (a)–(h), green
  `9/9`, and **red `9/9 FAILED`** when the change is reverted at its observation points.
- Regressions green: `test_guards.py` `6/6`, `test_client_ttft.py` `8/8`,
  `test_wire_client.py` `18/18`, `test_analyze_stats.py` `8/8` — the guards' semantics are
  unchanged, only what is written changed.


## `STOP-REASON-HOLES` — the three gaps a verifier found, and their producers

`V-INSTRUMENTS` (which wrote none of this code) measured three defects between the vocabulary
above and what the writer actually recorded. Each fix is **labelling only**: no guard
threshold was touched (180 s turn cap, `--runaway-turns`, the 4,096-token ceiling), and no
row, grade, fixture or grader was edited.

### 1. `runaway_turn` had no producer — it has one now

Before: `client.send_chat` derived the reason without an error code and nothing wrote
`error="runaway_turn"`, so `run_longrun` recorded the `--runaway-turns` abort as
`error=turn_wall_cap`. A runaway abort and a single slow turn were indistinguishable, and the
16,384-token guard left no trace of having fired.

After: the row that **ends the cell** on `--runaway-turns` is written with
`runaway_abort: true` and derives `stop_reason: runaway_turn`. Three abort paths carry it —
the turn `--turn-wall-cap` abort (`run_longrun.py`, `fail_extra`), the tool-follow-up wall
abort, and the planning (`digest`) request wall abort, which always ends the cell; plus the
ceiling-consume signature (`_runaway_signature`) when it reaches the limit, where the row is
relabelled **before** it is appended. `stop_reason_for_row` gives this marker precedence over
the client's partial fold, because both a wall cap and a ceiling signature reach the writer as
a capped turn — only the run-ending one is a runaway.

The harness event itself is unchanged: `error` stays `turn_wall_cap` (the wall that fired), and
`truncated` stays `true`. `turn_wall_cap` now means exactly one thing: a per-turn cap the run
survived.

### 2. A tool-call stream is no longer `empty_response`

Before: `derive_stop_reason` received no tool-call signal and tested only `content_present`, so a
dispatched tool call whose stream ended with no finish chunk and no text was labelled
`empty_response` — the row said the model produced nothing when it had produced a call.

After: `collect_stream` latches `tool_calls_present` on **any** `tool_calls`/`function_call`
delta (id, name, or argument fragment), `send_chat` passes it to the single derivation, and the
response carries it. `empty_response` now means *nothing was produced at all*.

### 3. `max_tokens` is on every row (`length` from the row alone)

Before: 99 stage-1 rows carried no `max_tokens`, so re-derived **without** the frozen manifest
cap 128 they were 99/99 `empty_response`; with it, 99/99 `length`. A stop reason that depends on
an external manifest is not a property of the row.

After: `make_row` always writes the ceiling — the value as sent on the wire when the response
carries it, the configured cap otherwise (never `None`, including failure rows with `resp=None`),
and the client already records the sent ceiling. `test_stop_reason_producers.py` re-derives
`length` from `completion_tokens`/`max_tokens`/`finish_reason` **out of the row dict only**.

### Scope — future rows only

This is a producer/recorder change. **The historical corpus is not patched:** rows written
before this unit keep `stop_reason: null`, exactly as `RECORD-STOP-REASON` left them, and the
99 stage-1 empty rows keep their recorded shape. Only rows written by the runner after this
change carry the new labels.

### Evidence

- `experiments/ptr-engine/longrun/tests/test_stop_reason_producers.py` — 8/8 green; red
  demonstrations, both measured on the real abort path and the real client fold:
  - tool-call signal removed → `stop_reason == "empty_response"` (expected `tool_calls`),
    the hole test and the fragment test fail;
  - runaway producer removed → `stop_reason == "turn_wall_cap"` (expected `runaway_turn`),
    exit 6 still, the runaway test fails;
  restored → the same two checks pass.
- Neighbours: `test_client_ttft` 8/8, `test_wire_client` 18/18, `test_guards` 6/6,
  `test_record_stop_reason` 9/9, `test_projection_calibration` 4/4, `test_tool_channel3` 5/5
  (all exit 0). Two **pre-existing** reds, not caused by this unit and not edited:
  `test_tool_channel` (exit 1: asserts `rounds == TOOL_FETCH_ROUNDS_PER_ARM` (24) while the
  later per-turn cap `TOOL_FETCH_ROUNDS_PER_TURN = 3` is in force, so it gets 3) and
  `test_tool_channel2` (exit 1: its frozen `manifests/v4tools2-baseline-pre.py` dry-run prompt
  is 61 bytes shorter per turn than the current runner's, a prompt-construction drift that
  predates this unit — this unit changes no request body).
