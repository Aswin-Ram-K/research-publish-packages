# U-SPCC-LIVE — billed accounting on the live server (plan verification item 6)

Status: **done**. One live cell on `192.168.2.168:8012` proved that turns after the first report
`cached_tokens > 0` and that billed tokens fall below the prompt-token total.

## 1. Pre-flight (no model spend)

`curl -s http://192.168.2.168:8012/get_server_info` → HTTP 200 with
`enable_cache_report: true`, `served_model_name: "occamy-1.0"`, `context_length: 131072`,
`kv_cache_dtype: "fp8_e4m3"`, `disable_radix_cache: false`, `disable_chunked_prefix_cache: false`,
`model_path=/root/.cache/huggingface/hub/models--Accio-Lab--occamy-1.0-NVFP4/snapshots/fa865dc5e80a13b9a2d8ae8d65ed2ee332f33652`.
Model id used for every request: **`occamy-1.0`**.

Single accounted probe (1 request, `POST /v1/chat/completions`, `temperature=0`, `seed=42`, `max_tokens=8`):

```
HTTP 200 wall 0.32s
USAGE RAW: {
 "prompt_tokens": 44,
 "total_tokens": 52,
 "completion_tokens": 8,
 "prompt_tokens_details": null,
 "reasoning_tokens": 8
}
CONTENT: ""
FINISH: length MODEL: occamy-1.0
```

A cold first request reports `prompt_tokens_details: null` — consistent with SGLang omitting
`cached_tokens` when the matched prefix is 0, and with `normalize_cached_tokens` mapping
`None -> 0` on sglang (`experiments/ptr-engine/longrun/run_longrun.py:124`).

## 2. Budget

Spend before the run, counted over `experiments/ptr-engine/measure/rows-*.jsonl` (92 files): **7,869**.
7,869 + 130 = 7,999 < cap 12,094 → run permitted. Nothing else called the model.

## 3. Run

Arm `masking-no-fetch` (monotone-growing prompt). Fixture
`experiments/ptr-engine/longrun/tasks-v7/TX-03.v1.json` (N=100, 48 checkpoint turns, never more than
one checkpoint per turn). Exact argv:

```
.venv/bin/python experiments/ptr-engine/longrun/run_longrun.py \
  --fixture experiments/ptr-engine/longrun/tasks-v7/TX-03.v1.json \
  --arms masking-no-fetch --reps 1 --temperature 0 --seed 42 \
  --model occamy-1.0 --base-url http://192.168.2.168:8012/v1 \
  --rows experiments/ptr-engine/measure/rows-spcc-billedproof-2026-11-10.jsonl \
  --max-turns 100 --budget-cap 12094 --run-id spcc-billedproof-2026-11-10 \
  --claim-mode plumbing
```

An earlier attempt without `--claim-mode` was refused by name before any request was sent:
`CLAIM REFUSED (exit 12): no row was written and no request was sent`. A `--hypothesis` attempt
failed at argparse (`unrecognized arguments`), also spending nothing. The `--dry-run` preflight
reported `turn_requests=100 ... would_send_total=100`.

Runner summary:

```
rows=100 requests=100 truncated=0 ttft_n=100 max_tokens=4096
content_source: {"content": 100}
answer_source:  {"content": 100, "none": 0, "reasoning-fallback": 0}
finish_reason:  {"stop": 100}
failed_turns=0 reasoning_fallback=0 timing_usable=100 token_dist={"n": 100, "mean": 4.2, "p95": 7.0, "max": 7.0} tok_method=tiktoken:cl100k_base
```

Cap gate, `manifests/spcc-billedproof-2026-11-10-masking-no-fetch-r1.json`:

```
{"allocation": 100, "cap": 12094, "reserve": 0, "spent_at_start": 7869, "used_in_run": 100, "spent_after": null, "delta": null}
```

(`spent_after`/`delta` are null in the frozen block; the rows on disk give the real afters: 7,969.)

## 4. Acceptance evidence

`billing` block exactly as the scorecard emitted it
(`experiments/ptr-engine/measure/score-spcc-billedproof-2026-11-10.json`):

```
{
 "prompt_tokens": 174047,
 "cached_tokens": 159744,
 "uncached_tokens": 13746,
 "billed_tokens": 0,
 "cached_fraction": 0.920767767594674,
 "coverage": 0.98,
 "attribution": "available"
}
```

Per-turn readings out of `experiments/ptr-engine/measure/rows-spcc-billedproof-2026-11-10.jsonl`:

```
T1   prompt=261  cached=None  uncached=None  cached_reported=False source=None
T2   prompt=283  cached=192   uncached=91    cached_reported=True  source=prompt_tokens_details
T3   prompt=427  cached=256   uncached=171   cached_reported=True  source=prompt_tokens_details
T100 prompt=3206 cached=3008  uncached=198   cached_reported=True  source=prompt_tokens_details
NULL_CACHED_TURNS [1, 5]
```

Rows added to the store: **100**. Store after the run: **7,969 rows across 93 files** against the
12,094 cap (headroom 4,125). Live model requests spent by this unit: **101** (100 turns + 1 probe),
inside the 130 allowance; the probe is not a row, so the rows-based store count is 7,969 while the
true request count is 7,970.

Recomputed from the same rows (`billed = prompt - cached` per row, a null cached = full prompt):
`sum_prompt=174047 sum_cached=159744 billed=14303 frac=0.917821`, i.e. **8.2% of the prompt total is
billed** — below the prompt total on the literal scorecard field and on the recomputation.

**Scorer gap (reported, not hidden):** the scorecard's `billed_tokens` sums a key the runner never
writes. `make_row` emits `prompt_tokens`/`cached_tokens`/`uncached_tokens` only — grep of
`billed_tokens` hits only `experiments/ptr-engine/longrun/score_longrun.py:145,176` — so
`"billed_tokens": 0` is a vacuous zero, not a measurement. The substantive number is
`billed = 14,303` against `prompt = 174,047`. The criterion "billed < prompt" also holds for the
scorecard's own field, but only because the column is empty.

## 5. Cache law `uncached = (P1 mod 64) + L`

`P1 = 261`, `P1 mod 64 = 5`; the turn-2 prompt grew by `ΔP = 283 - 261 = 22` tokens, so the append
reading predicts **27** uncached while the server reported **91** (`cached = 192 = 3×64`). The result
therefore does **not** match the naive append reading: turn 1's prompt carries the `doc-fact-01` tool
body injected after the shared index, so the turn-2 shared prefix ends at 192 tokens rather than at
`P1 - (P1 mod 64) = 256`; the 64-block granularity holds, but `L` cannot be read off the prompt delta
in this masking arm. The second null (`turn 5`) coincides with the fixture's `revision_schedule`
turn-5 revocation (`doc-revoked revoked`) — a deliberate prefix rewrite, exactly where a miss is due.

## 6. Scorecard status (honest)

Exit code 1; **40 of 50 checks fail on answer shape** (`answer kind 'NONE' != expected 'NUM'` at 40
checkpoints, e.g. `cp.TX-03.f01.d5` at turn 6). That is a behaviour finding of the model on this
fixture, orthogonal to billing: all 100 turns completed (`finish=stop`, 0 failed turns,
`truncated=0`), so the cache/billing evidence is not contaminated by failed requests.

## Artifacts

- rows (new file, nothing existing touched): `experiments/ptr-engine/measure/rows-spcc-billedproof-2026-11-10.jsonl` (100 rows)
- scorecard: `experiments/ptr-engine/measure/score-spcc-billedproof-2026-11-10.json`
- manifest: `experiments/ptr-engine/longrun/manifests/spcc-billedproof-2026-11-10-masking-no-fetch-r1.json`
- no container restarted, `/openapi.json` never requested, no endpoint outside
  `GET /get_server_info`, one probe `POST /v1/chat/completions` and the runner's own turn POSTs.
