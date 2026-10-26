# UNIT MISS-LAW-2 — re-derive the vLLM `+1056` term with an independent instrument

**Status:** done · **Bound:** 40 tool calls (used 23) · **Server:** vLLM 0.27.1 `qwen3.5-9b` `:8014`, sole writer
**Write paths:** `experiments/miss-law/vllm2/`, `orchestration/units/MISS-LAW-2.md`,
`orchestration/handoffs/MISS-LAW-2.json`
**Hard rules:** no `:8012` writes, no restart, no `/flush_cache`, no `/home/zer0null/Duval`, no edits to
`LAW.md` / `rows.jsonl` / `law_fit.json` / `run.py` / `grid2.py` / `agg.py` (reused by import, never modified).

## Why this unit exists

MISS-LAW's own handoff named the gap: on this build `usage.prompt_tokens_details` is `null` on every
request, `vllm:prefix_cache_hits_total` turned out to count **tokens**, so the vLLM half of the law rested
on one quantity (the delta of `vllm:prompt_tokens_cached_total`). One instrument is not a measurement.

## Objective (as given)

1. Enumerate what `:8014/metrics` exposes with TYPE and unit — do not infer a unit from a name.
2. Find a **second, independent** observable for cached tokens.
3. Re-test the plateau (5280 over P1 = 7000…7330) and the step (6336 at 7396) with it.
4. Test whether `+1056` is stable or grows with the number of appends (2, 3, 5 rounds).
5. State the model believed now; say whether `+1056` survives, needs correction, or was an artefact.

## What was done

- Full `/metrics` inventory; live-total identity check across 952,868 prompt tokens.
- Asserted unit of every cache series against live values, not names.
- Three instruments per serialized request: A = cached-token counter delta, B =
  `request_prefill_kv_computed_tokens_sum` delta, C = TTFT (server histogram per request in stage 1,
  client wall clock on non-stream requests in stage 2).
- Grids: 19 `P1` cells in three block-multiple bands (6B/7B/8B) × 2 reps; six one-token appends in one
  session; a session whose appends cross 7B; identical-repeat; cold control; cold TTFT calibration.
- 133 rows, one per request, `flush()`+`fsync` per row; `kvcomp_count_delta = 1` and
  `ttft_server_count_delta = 1` on every row (proves one-request attribution); `errors = 0`.

## Result

- **B is not independent** — `unc_k − unc_c = 0` on 74/74 measure rows and the aggregate is an exact
  identity of A. Declined as corroboration, exactly as the unit demanded.
- **C is independent** and confirms the term: at fixed total prompt length, crossing a block multiple costs
  **+188.9 / +191.2 / +195.6 ms** for a 1052-token compute step at block 6/7/8 → 0.180–0.186 ms/token vs an
  independently measured 0.171 ms/token cold-prefill slope; the no-`+1056` alternative predicts ≈0.7 ms.
- **`+1056` survives**, constant (exactly 1056) across 6 append rounds and 3 crossing rounds, so it is
  per-request, not cumulative.
- **Correction to the law:** vLLM also avalanches — `cached = 0`, `unc = P1 + L` — when
  `P1 mod 1056 ∈ {0,1}` (measured at 6336/6337, 7392/7393, 8448/8449, with TTFT 1.24–2.22 s vs 206–216 ms
  for the residue-2 neighbour). The parent law carries this discontinuity for SGLang only.
- Stage 1's streamed-TTFT parser returned `None` (my SSE `delta.content` check); stage 1 therefore reports
  **server** TTFT and stage 2 adds client wall clock. Not back-filled.

## Deliverables

`experiments/miss-law/vllm2/{rows.jsonl, REPORT.md, probe2.py, probe3.py, summary.txt, metrics_raw.txt}`,
this card, and `orchestration/handoffs/MISS-LAW-2.json`.
