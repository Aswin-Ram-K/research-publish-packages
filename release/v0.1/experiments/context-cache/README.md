# Context-cache experiment (U1 core)

Unit U1 builds the offline core of a cache-reuse experiment against SGLang
(`http://serving-host/v1`, model `occamy-1.0`). **No live calls happen in
this unit** — every unit test injects a fake `send` and a stub summariser.

## Record naming (`CX-` prefix)

Batch-1 verification records already occupy `orchestration/handoffs/V1.json`
and `orchestration/units/V1.md` (the 2026-10-08 kg/graphify verdict), and those
paths are restored to it. **Context-cache verifier records use the `CX-`
prefix**: a verifier of this experiment files `orchestration/handoffs/CX-V<n>.json`
and `orchestration/units/CX-V<n>.md`, never the bare `V<n>` names. The
context-cache V1 verdict was refiled this way as `CX-V1.json` / `CX-V1.md`
(byte-identical to the record it replaced) and the batch-1 originals were
restored from git (`git show HEAD:...`).

## Measured facts this core encodes

- Cache hits arrive as `usage.prompt_tokens_details.cached_tokens`.
- `prompt_tokens_details` is **`null`** (not `{"cached_tokens": 0}`) on a cold
  request; `normalise_cache` maps `null`/missing/`{}` to 0.
- An impossible pair (`cached_tokens > prompt_tokens`) is **clamped** to the
  prompt, counted in `meter.clamp_stats()["clamped"]` and reported as
  `max_overrun` — never silently passed through. The live gate should log
  `clamp_stats()` per cell.
- With `stream: true` + `stream_options.include_usage`, SGLang returns usage in
  the final chunk, so TTFT and cached tokens come from ONE request.
- Prefix reuse is on a 64-token grid: `uncached == prompt_tokens % 64`
  (measured 612→576, 807→768). `analyze.tax_error` scores deviation from it.

## Modules

| file | role |
| --- | --- |
| `client.py` | `ChatClient.chat` / `chat(...)` — httpx streaming wrapper, retry once on 5xx/timeout, returns the 7-tuple `(prompt, cached, completion, ttft_ms, wall_ms, status, text)` |
| `runner.py` | cell matrix `(policy, case, depth, rep)`; builds chains turn by turn, compacts on a token budget, records `CacheRow`s, flags evicted cells |
| `analyze.py` | pure functions `tax_error`, `hit_rate`, `per_turn_series`, `compaction_effect`, `summary_table`; `main()` reads a jsonl |

## Rendering rules (U8 fix)

1. **A message, once emitted, is never rewritten by a later turn.** Bodies are
   `node.text` verbatim, in chain order. Appending a turn appends one message;
   turn N's message list (and concatenated content) is a prefix of turn N+1's.
2. **`POINTER` and `NAIVE_APPEND` are equal-information** for the same chain —
   both send every body in order, byte for byte; `equal_information()` asserts
   it. The pointer distinction is *chain management* (content-addressed nodes,
   fork-instead-of-edit, one node shared across chains), not dropping earlier
   bodies. `POINTER_FORK` is the same rendering with the fork root labelled in
   the invariant preamble.
3. `NAIVE_MUTABLE` remains the deliberate sensitivity bound: volatile values
   are interpolated into message 0, so its prefix breaks every turn.

## Usage

```python
from resextract.context import RenderPolicy, CacheMeter
import importlib.util, pathlib
spec = importlib.util.spec_from_file_location(
    "ctx_runner", pathlib.Path("experiments/context-cache/runner.py"))
runner = importlib.util.module_from_spec(spec); spec.loader.exec_module(runner)

cells = runner.build_cells(
    policies=[RenderPolicy.POINTER, RenderPolicy.NAIVE_MUTABLE],
    cases=["case-01"], depths=[8], reps=3, salt_seed=7,
)
case = runner.Case("case-01", "You are a careful analyst.", (
    runner.Turn("Find the failing check.", {"step": "1"}),
    runner.Turn("Explain the failure.", {"step": "2"}),
))
meter = CacheMeter()
results = runner.run_matrix(cells, [case], send=my_send, meter=meter)
meter.to_jsonl("state/context-cache/rows.jsonl")
```

`send(messages)` must return the same 7-tuple as `client.chat`; the live gate
wires it as `functools.partial(ChatClient().chat, max_tokens=256)`.

## Invariants pinned by `tests/test_context_*.py`

1. Nodes are immutable content addresses; no `edit()` exists.
2. `POINTER` / `NAIVE_APPEND` are append-only: message lists, concatenated
   contents and canonical JSON (minus the closing `]`) are prefix-stable, and
   an emitted message is never rewritten when a turn is appended.
3. `POINTER` and `NAIVE_APPEND` render equal information for the same chain.
4. `NAIVE_MUTABLE` rewrites message 0 when a volatile value changes (the
   red→green pair: a policy implementation that made both identical fails).
5. `compact(FORK)` produces all-new node ids whose parents never enter the old
   chain.
6. Cold-request usage normalisation clamps impossible cache pairs *and counts
   them*; `CacheRow` JSON round-trips; the 64-token tax is asserted offline.
