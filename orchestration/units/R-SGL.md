# R-SGL — SGLang cache/serving-option survey (literature only)

**Status:** done (2026-10-21) — deliverable at `docs/serving-options/R-SGL.md`, handoff at `orchestration/handoffs/R-SGL.json`
**Purpose (one):** Web research on what cache- and serving-level options **SGLang itself** ships, and what
performance each claims — so a later phase can pick comparable serving setups. **No experiments.**
**Parent:** `session-b61634cb-606d-4220-9b7e-eeb2b9a9e2a7`

## Hard constraints (from card)
- **0 live model requests.** No `.occamy.lock`, no restart/reconfigure of Occamy `192.168.2.168:8012`.
  At most 3 read-only GETs permitted; not needed if docs answer. **Honoured: 0 requests made, 0 GETs made.**
- No writes outside: `orchestration/units/R-SGL.md`, `docs/serving-options/R-SGL.md`,
  `orchestration/handoffs/R-SGL.json`.
- Bound: **max 40 tool calls**; parallel search bursts; `local_web_search` first, `local_web_crawl` on
  primary docs (docs.sglang.io, lmsys.org blog, GitHub).
- Automated session: never ask the user; missing value -> conservative default recorded in `assumptions`.

## Deployment under characterisation (fixed, not to be changed)
SGLang on a single GB10-class "GX10" node, Qwen3.5-MoE hybrid-attention, `max_model_len=131072`.
Live: `page_size=1`, `disable_radix_cache=false`, `radix_eviction_policy=lru`, `chunked_prefill_size=8192`,
`max_total_num_tokens=1306681`, `enable_hierarchical_cache=false`, `hicache_storage_backend=null`,
`enable_lmcache=false`, `enable_session_radix_cache=false`, `uses_mamba_radix_cache=true`,
`mamba_radix_cache_strategy=extra_buffer`, `max_mamba_cache_size=64`.
Measured: cache hits land on a 64-token grid; `cached = 64*floor((L-1)/64)`; exact-multiple-64 prompts
miss on first immediate repeat, hit on second.

## Method
Search bursts -> primary-doc crawls -> per-option record (flag, mechanism, strongest measured claim +
workload, source URL, runnability on our stack, risk/cost). Deliverable: 20-row table +
"what a reviewer would demand we test, in priority order" (9 items).

## Findings (headline)
1. **The 64-token grid is a mamba/GDN checkpoint grid, not a paging grid.** `page_size=1` makes the full-attention
   KV component token-granular, but `FLA_CHUNK_SIZE` is 64 and under `extra_buffer` the recurrent state is handed to
   the radix tree every `--mamba-track-interval` tokens (published Qwen3.8 recipes use 64). Unified radix matching
   takes the deepest node **all** component validators accept, so the reusable prefix is floored to 64 →
   `cached = 64*floor((L-1)/64)`. Commit timing is undocumented → the "miss once, hit twice" shape stays a hypothesis.
   Our `extra_buffer` + `page_size=1` pairing is also undocumented (the cookbook pairs `extra_buffer` with `--page-size 64`).
2. **HiCache** is the best-documented lever: up to 6× throughput / 80% TTFT reduction (team), −56% TTFT + 40%→80% hit
   rate (Novita/3FS), 84% TTFT reduction (Ant/Mooncake PD), L3 hit rates 96.8–98% (unified radix multi-turn).
   Its L3 backend can be attached/detached **at runtime, no restart** — the only cache lever testable on a frozen server.
3. **MTP/NEXTN** is the only lever with a same-family measured claim (+10% throughput, 2.33× per-user, accept 3.3 on
   Qwen3.8 day0), but it silently caps concurrency at 48 and needs ReplaySSM to compose with radix reuse.
4. **Cache-aware routing (+92% throughput, 20%→75% hit rate) and PD disaggregation (84% TTFT)** have the largest
   published gains and are both **needs-multi-node** — recorded as out of scope for the single GX10.
5. Cheap restart-only levers a reviewer will ask about: `--page-size` (1 vs 64), `--radix-eviction-policy`,
   `--chunked-prefill-size` × `--linear-attn-prefill-backend` (our 8192 sits exactly on the FlashInfer GDN
   auto-selection boundary), and cache telemetry (`--enable-cache-report`/`--enable-metrics`).
