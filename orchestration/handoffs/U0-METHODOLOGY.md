# U0 — Cache-Methodology Note: measuring prompt-cache reuse against an SGLang server

**Unit:** U0 `occamy-cache-methodology` · **Date:** 2026-10-20 · **Tool calls used:** 21 of 35
**Scope:** methodology + pitfalls only. **No live model calls were made.** Nothing was sent to `192.168.2.168:8012`.
**Target server facts assumed from the parent (not re-measured by this unit):** `page_size=1`,
`chunked_prefill_size=8192`, `--enable-session-radix-cache` **OFF**, server cannot be restarted,
server is **shared with other users**, `cached_tokens` observed `null` on cold requests and
`612→576`, `807→768` on warm ones.

**Verification legend.** `YES` = primary doc/source read in this unit. `YES-2°` = read in this unit
from a source that itself cites the SGLang `file:line`; the code line was not re-opened here.
`PARTIAL` = the surrounding claim is verified, the specific sub-claim is not. `UNVERIFIED` = could
not be fetched; **do not cite it as fact**. `INTERNAL` = evidence from this workspace, not from the web.

---

## 1. Claim table

| Claim | Source (URL) | Verified? | What it means for our measurement |
|---|---|---|---|
| Prefix caching is a radix tree keyed by **token sequences**; before prefill the tree finds the longest reusable prefix and returns its KV locations to the scheduler. | https://www.lmsys.org/blog/2026-08-11-unified-radix-cache/ · https://docs.sglang.io/docs/advanced_features/radix_eviction_policy | YES | The unit of reuse is a prefix, never a suffix or an interior span. A measurement that varies only the *prefix* is the only kind that can be interpreted. |
| Under Unified Radix Cache, **traversal depth ≠ reusable depth**: the walk follows the full-attention path and visits up to n4, but the reported boundary stays at the deepest node **acceptable to every component validator** (example: n2). | https://www.lmsys.org/blog/2026-08-11-unified-radix-cache/ | YES | A large full-KV match can be silently truncated by a non-attention component. Reported `cached_tokens` < "how much of my prompt matched". |
| Recurrent/linear-attention state is **valid only at an exact prefix checkpoint** — "a recurrent state is valid only at an exact prefix checkpoint". | https://www.lmsys.org/blog/2026-08-11-unified-radix-cache/ | YES | This is the root cause of a discrete reuse grid on hybrid models. |
| Usable prefix = deepest node on the matched path that **actually holds a Mamba state** on device or host (`mamba_boundary_len = device_prefix_len + host_hit_length`); KV matched beyond that point is recomputed. | https://github.com/outerarc-ai/state-bench/blob/main/docs/SGLANG_MAMBA_CHECKPOINTS.md (cites `mem_cache/unified_cache/components/mamba.py:146-168`) | YES-2° | Explains why a page_size=1 tree still refuses fine-grained boundaries. |
| `cache_chunk_size = max(model mamba_chunk_size, else FLA chunk size 64; page_size)` | same doc (`arg_groups/overrides.py:1831`) | YES-2° | The constant 64 is an **FLA kernel chunk size**, not a page size and not a server flag. |
| `checkpoint_grid = lcm(cache_chunk_size, radix page size)`; worked example in the doc: **"Qwen3.5 (GDN) with `page_size=1` gives `cache_chunk_size = 64`, `checkpoint_grid = 64`, `track_grid = 256`"** | same doc (`runtime_context.py:1959,1967`) | YES-2° | **Exactly our configuration and exactly our 64 grid.** page_size=1 does not shrink the grid. |
| The matcher floors to the grid: `branching_seqlen = floor(full_kv_hit / checkpoint_grid) * checkpoint_grid` | same doc (`mem_cache/unified_cache/components/mamba.py:175-180`) | YES-2° | Predicted residue: reported cached = 64·⌊len/64⌋ ⇒ `uncached == len mod 64`. Confirmed by 612→576 (rem 36) and 807→768 (rem 39). |
| A match covers at most `input_len - 1` tokens, so an exact repeat cannot resume from a state **at** the prompt's end. | same doc (`managers/schedule_batch.py:1689-1699`) | YES-2° | A "repeat the identical prompt" test cannot yield 100 % printed reuse on some paths; don't treat that as a bug. |
| Prefill snapshot position is aligned **relative to the chunk start**, recorded only when `extend_len >= checkpoint_grid`; "If `prefix_len` is off the absolute grid, so is the snapshot." | same doc (`managers/schedule_batch.py:3044-3051`) | YES-2° | Snapshot positions are **path-dependent**, not a global 64 lattice. Two prompts of equal length can report different residues. |
| Each prefill chunk takes the remaining `chunked_prefill_size`, **measured from the matched prefix rather than an absolute grid**; exact chunk fill is disabled when Mamba prefix sharing is on. Open PR #41701 and draft #43135 aim to align chunk boundaries to the grid. | same doc (`managers/schedule_policy.py:1277,611-618`) | YES-2° | chunked prefill **can** move snapshots. 8192 = 128×64 keeps boundaries on-grid *today*, but this is a version-dependent accident, not a guarantee. |
| Every prefill chunk is inserted, and **inserted KV stops at the latest snapshot** (page-aligned); KV computed past it is not inserted for an unfinished request. Completion inserts the latest track snapshot, **not** the sequence end. | same doc (R9–R13, `unified_radix_cache.py:1084-1128`, `mamba.py:541-605`) | YES-2° | A long prompt can leave its reusable boundary at an intermediate chunk boundary rather than at its end. |
| Eviction considers only **evictable leaves**: KV present, unlocked, not shadowed by a child holding KV; the root is never evictable; lowest score evicted first; default policy `lru`; **a policy only scores and cannot pin KV**. | https://docs.sglang.io/docs/advanced_features/radix_eviction_policy | YES | Prefixes are evicted tip-to-root. A hit on a specific deep prefix is never guaranteed on a shared server, and no policy can protect it. |
| `/flush_cache` exists as a **native endpoint**, `POST`, query param `timeout` (float seconds, default `0` = *fail fast if not idle*; non-zero waits for idle; **400** if HiCache async ops are in flight). It is also auto-triggered by `/update_weights`. | https://docs.sglang.io/docs/basic_usage/native_api.md | YES | **It exists.** It is process-global. See §3(b) for blast radius. |
| `/server_info` returns **CLI arguments, token limits and memory-pool sizes**; it merges the deprecated `get_server_args`, `get_memory_pool_size`, `get_max_total_num_tokens`. | https://docs.sglang.io/docs/basic_usage/native_api.md | YES | We can read `page_size`, `max_total_num_tokens`, `chunked_prefill_size`, `schedule_policy` and whether `--enable-session-radix-cache` is on **without restarting anything**. This is the cheapest and most important first step. |
| Session-aware radix cache **requires `--enable-session-radix-cache` at launch** and is *"implemented only by `UnifiedRadixCache`"*. `session_id` labels cache references only — it does not append context. `/close_session` removes references but **does not immediately free KV**. | https://docs.sglang.io/docs/advanced_features/session_radix_cache | YES | Confirms the flag. With it OFF, the whole feature is inert (see §3(e)). |
| Session references are **soft protection, not memory pins**: referenced KV can still be evicted when reclaiming unreferenced KV is insufficient. | https://docs.sglang.io/docs/advanced_features/session_radix_cache | YES | Even with the flag ON, session retention is best-effort — a hit-rate ceiling exists that no protocol can remove. |
| `sglang:time_to_first_token_seconds` "measures the time from request creation in the API server to the first token. For streaming requests it ends when the first output arrives **after detokenization, which may contain no printable text**. Non-streaming clients only see the final response, so for them it ends **when the scheduler produced the first token**." | https://docs.sglang.io/docs/references/production_metrics.md | YES | Streaming and non-streaming TTFT measure different events and are not interchangeable. Also: the first byte you *see* is not the first token the *scheduler* produced. |
| `sglang:cache_hit_rate` is a **server-side gauge** (global ratio), alongside `sglang:prompt_tokens_total`, `sglang:token_usage`. | https://docs.sglang.io/docs/references/production_metrics.md | YES | The gauge is not a per-request quantity; do not mix it into per-request tables. |
| `--schedule-policy lpm` (longest prefix match) **reorders requests to encourage more cache hits** and adds scheduling overhead. | https://docs.sglang.io/docs/advanced_features/hyperparameter_tuning.md | YES | Hit rate is partly a property of the *server's* scheduler and *other* tenants' traffic, not only of our prompts. |
| `max_total_num_tokens` is the KV pool size in tokens, printed in the startup log and set indirectly by `--mem-fraction-static` (`mem_fraction_static = (weights + KV pool) / GPU cap`). Reference startup line: `max_total_num_tokens=665690, chunked_prefill_size=8192, max_prefill_tokens=16384, …`. | https://docs.sglang.io/docs/advanced_features/hyperparameter_tuning.md | YES | `chunked_prefill_size=8192` is the **default**, consistent with our server; pool pressure is what converts a hit into a miss. |
| SGLang omits `prompt_tokens_details` on a **cache miss** instead of reporting `cached_tokens: 0` (open, labelled `backend::sglang`). | https://github.com/ai-dynamo/dynamo/issues/16533 (issue **title**, rendered) | YES (title only) | Explains our `null` on cold requests: **absent ≠ unknown, it means 0.** Any code that drops nulls silently deletes every miss and inflates the hit rate. |
| …that the flag gating it is `--enable-cache-report` and that `meta_info["cached_tokens"]` is filled for every non-embedding request regardless of that flag. | search-engine snippet of the same issue (body did **not** render) | **UNVERIFIED** | Do not assert the flag semantics. Treat as a hypothesis to confirm from `/server_info`. |
| Hybrid models' "in-place state updates for recurrent layers **precludes rolling back cache entries for partial sequence overlaps**, and instead mandates only **exact-match cache hits**". | https://arxiv.org/abs/2411.19379 (Marconi, MLSys 2025) | YES | Independent, model-side confirmation: recurrent state is not arbitrarily addressable. |
| Token-level matches are "directly usable **only at positions aligned with stored checkpoints**, constraining prefix reuse to a **discrete set of boundaries**"; the paper targets **Gated DeltaNet** hybrids. | https://arxiv.org/abs/2608.30310 (Tail-Replay, v2 2026-10-15) | YES | A 64-token reuse lattice is the *expected*, documented consequence of hybrid caching — not an SGLang bug. |
| PrefixBench-H100 measures TTFT / ITL / e2e / cache-hit stats across shared-prefix length, suffix diversity, arrival pattern, concurrency, output length and cache config on one H100, across two runtimes; "cache effectiveness itself is largely insensitive to concurrency and output length; the cross-runtime differences that remain arise above the cache, in the scheduling layer". | https://arxiv.org/abs/2609.19657 | YES | Supports: vary **one** factor at a time, hold concurrency fixed, and attribute latency differences to the scheduler, not only the cache. |
| SCBench evaluates long-context methods across the KV-cache **lifecycle** (generation, compression, retrieval, loading) on **shared-context** tasks. | https://arxiv.org/abs/2412.10319 (ICLR 2025) | YES | Precedent that shared-context evaluation must be designed, not incidental. |
| …that SCBench (or PrefixBench) describes an explicit **cache-state flush/reset protocol**. | — | **UNVERIFIED** | Do not claim either paper prescribes a flush. Their abstracts describe workload control, not reset APIs. |
| `page_size` sets radix **key granularity** (keys are page-aligned; the blog's hybrid example runs `--page-size 64`, and `cache_chunk_size` takes `max(…, page_size)`). | https://www.lmsys.org/blog/2026-08-11-unified-radix-cache/ + state-bench doc | PARTIAL | Consequence to keep in view: **`page_size=64` would reproduce our exact 64 grid with no recurrent layer involved.** Must be excluded from `/server_info`. |
| `--enable-cache-report` exists and what it gates. | — | **UNVERIFIED** | Appears in the lmsys blog command outline but was not defined anywhere fetchable. |
| `cachedTokens` is a **pure pass-through of the provider `usage` object**, read straight from the API payload, with `inputTokens` from the same payload. | workspace `orchestration/handoffs/U-CACHE-INSTRUMENT.json` | INTERNAL | The number cannot be a local estimate. But "provider-reported" ≠ "exact", see §3(a). |

---

## 2. PITFALLS THAT WOULD INVALIDATE OUR RESULTS

1. **Null dropped instead of read as zero.**
   *Symptom:* per-request tables contain no rows with `cached_tokens == 0`; the mean hit rate is
   suspiciously high and moves when row counts change.
   *Why:* SGLang omits `prompt_tokens_details` on a miss rather than sending `0`.
   *Mitigation:* `cached = resp.usage.prompt_tokens_details.cached_tokens if … else 0`, and log the
   coercion. Count misses explicitly. Assert `0 ≤ cached ≤ prompt_tokens`.

2. **No unique salt ⇒ cross-tenant contamination.**
   *Symptom:* the **first** request of a "cold" measurement already reports non-zero cached tokens.
   *Why:* the server is shared; another user's prefix (or our own earlier run, or a system prompt)
   is already in the tree, and eviction is not guaranteed.
   *Mitigation:* prepend a fresh random nonce (a UUID, ≥ the checkpoint grid in tokens) to every
   measured prompt family; treat any non-zero `cached` on the first request as proof of
   contamination and discard the batch.

3. **Assuming `cached_tokens` equals the shared prefix length.**
   *Symptom:* the residual `uncached` is a constant-looking small number that equals `len mod 64`.
   *Why:* the boundary is floored to the checkpoint grid (§3(d)).
   *Mitigation:* compute the expected value as `64·⌊len/64⌋` (for this server) and report the
   residual as a *finding about the engine*, never as measurement error.

4. **Prompts shorter than the grid.**
   *Symptom:* exact-repeat pairs both report `cached = 0`.
   *Why:* any `len < 64` floors to 0.
   *Mitigation:* never measure reuse with prompts shorter than a few multiples of the grid; keep a
   minimum of 512 tokens.

5. **Serving a concurrent pair to demonstrate a hit.**
   *Symptom:* two identical prompts submitted together both report low `cached`, or the second one
   only partially hits.
   *Why:* KV for an in-flight request is not yet insertable (nodes are locked / not yet complete),
   and under load both prefill simultaneously.
   *Mitigation:* fully serialize the measurement — one request in flight, wait for the response,
   then submit the dependent request. Assert zero outstanding requests before each step.

6. **Treating TTFT as one quantity.**
   *Symptom:* TTFT for the same prompt is ~an order of magnitude larger in one arm than another.
   *Why:* streaming TTFT ends at first *detokenized output*; non-streaming TTFT ends when the
   *scheduler* produced the first token, and the client sees only the finished response.
   *Mitigation:* pick **streaming**, and state it. Use `max_new_tokens` small but non-zero and
   identical across arms. Never mix stream and non-stream in one table.

7. **First-request / cold-start artefacts.**
   *Symptom:* the first request of a process is slow and low-hit regardless of cache state;
   measurements taken immediately after a restart look catastrophic.
   *Why:* CUDA-graph capture, kernel autotune, allocator warmup, tokenizer/template caches — all
   independent of the radix cache.
   *Mitigation:* discard the first ≥3 requests, and never use a process's first request as a data
   point. Do the warmup with a *different* (nonce) prefix so it cannot pollute the measured prefix.

8. **Reading the global gauge as a per-request number.**
   *Symptom:* `sglang:cache_hit_rate` disagrees with the mean of per-request `cached/prompt`.
   *Why:* the gauge is a server-wide ratio over *all* tenants and both stream and batch work.
   *Mitigation:* quote per-request `cached_tokens` for the measurement; quote the gauge only as
   context, always with the caveat that other users are inside it.

9. **Falling for the flush temptation.**
   *Symptom:* a beautifully clean cold baseline, followed by complaints; other users' TTFT spikes;
   occasional `400` from a non-idle flush.
   *Why:* `/flush_cache` is process-global (§3(b)).
   *Mitigation:* do not call it. Isolation comes from nonce prefixes, not from resetting a shared
   server. If a flush is ever required, it needs explicit approval and a stated maintenance window.

10. **Aggregating ratios by summing.**
    *Symptom:* the headline hit rate is far above the median session's hit rate.
    *Why:* token-weighted sums are dominated by a few huge high-hit sessions.
    *Mitigation:* report the **median over units** (sessions/requests) as the headline and keep the
    token-weighted sum as a secondary, clearly labelled number.

11. **Mistaking the gateway for the engine.**
    *Symptom:* `cached_tokens` values the SGLang tree could not possibly hold; or the field appears
    on a request the server log shows as a plain miss.
    *Why:* we address an alias (`occamy-1.0`) through `/v1`; a proxy may synthesize or forward
    `usage` from its own layer.
    *Mitigation:* corroborate at least one arm against the server's own view
    (`/server_info`, startup log, `sglang:cache_hit_rate`) before attributing numbers to SGLang.

12. **Assuming the prompt is what you typed.**
    *Symptom:* `prompt_tokens` ≠ your local token count; the residual `len mod 64` is not stable
    across a chat turn.
    *Why:* chat templates inject system/turn scaffolding and the template may be applied server-side.
    *Mitigation:* take `prompt_tokens` **from the response**, never from a local tokenizer; use the
    same endpoint (prefer raw `/generate` text) for every arm of a comparison.

13. **Comparing runs across a restart or a weight update.**
    *Symptom:* the post-restart arm has systematically lower hits.
    *Why:* a restart builds an empty tree, and `/update_weights` **auto-triggers** a cache flush.
    *Mitigation:* record server start time / uptime and weight version with every batch; never splice
    arms measured across a restart.

14. **Expecting a 100 % hit on an exact repeat.**
    *Symptom:* the repeat reports `len - r` rather than `len`.
    *Why:* matches stop one token short of the input, and inserted KV stops at the last checkpoint.
    *Mitigation:* define the success criterion in grid units (`expect 64·⌊len/64⌋`), not as "100 %".

---

## 3. ANSWERS TO THE FIVE DESIGN QUESTIONS

### (a) Is `cached_tokens` exact?
**Exact as an integer, but it is not the quantity most people think it is.**
It is the server's internally computed reusable-boundary length for that request, reported as an
integer token count (no float, no percentage, no client-side estimate — `INTERNAL`, corroborated by
the OpenAI schema and by two independent records of the same numbers). Three qualifications, all
load-bearing:

* **It is floored, not rounded**, on hybrid models: `floor(hit / checkpoint_grid) · checkpoint_grid`.
  So the value is *exact about the boundary it reports* and *systematically below the true token
  overlap*. It never over-reports reuse.
* **It is absent on a miss** (SGLang omits `prompt_tokens_details` rather than sending `0`), so
  "exact" requires you to supply the zero.
* **It is a server claim, not an observed computation.** Nothing in the payload proves the KV was
  actually reused rather than merely found eligible. It is a `PARTIAL`-grade instrument: fine for
  correlated measurement, not for a causal claim of the form "N tokens were not recomputed".

Practical rule: report `cached_tokens` and `uncached = prompt_tokens − cached_tokens` together with
`prompt_tokens`, and state the grid.

### (b) Can we flush, and at what risk?
**Yes — `POST /flush_cache` exists** (`timeout` query param, seconds, default `0` = fail fast if not
idle; non-zero waits for idle; returns `400` when HiCache async operations are in flight; the same
flush is auto-triggered by `/update_weights`). Verification: **YES**, official native-API docs.

**Blast radius: the whole server process, for every tenant.**
* It resets the **shared** radix cache: the next request from *any* user — not just us — pays a full
  cold prefill. On a box with other active users that is a visible, attributable latency spike, and
  it silently corrupts anyone else's concurrent measurement.
* It cannot be made per-prefix or per-session; there is no scoped flush.
* It fails fast (`400`) if the server is not idle, so a "successful" flush also proves the server was
  idle at that instant — which is itself information we should not take for free.
* It clears the radix tree, which is **not** the same as proving cold state: HiCache L2/L3 tiers, the
  CUDA-graph/kernel warmup state, and any proxy-side cache are outside its contract
  (**UNVERIFIED** whether `/flush_cache` drains HiCache tiers; do not assume it does).

**Recommendation: do not call it.** We do not need it — a fresh nonce prefix per measurement gives
us a cold prefix *inside* a warm server without touching anyone else. Escalate for approval only if
a reviewer demands a globally-cold server, and then schedule it as a maintenance action with the
other users notified, not as a step inside a benchmark loop.

### (c) Does chunked prefill (`8192`) distort matching?
**Yes, in a bounded and currently benign way — but it is a version-dependent accident.**
* Chunk boundaries are computed as *remaining `chunked_prefill_size` measured from the matched
  prefix*, **not** from an absolute token grid (`schedule_policy.py:1277`), and exact chunk fill is
  disabled when Mamba prefix sharing is on (`:611-618`).
* Therefore the chunk end is at `matched_prefix + k·8192`. Since our grid is 64 and 8192 = 128·64,
  and `matched_prefix` is itself a multiple of 64, **today's boundaries stay on-grid** — which is why
  we see no chunk-induced anomaly.
* But snapshot alignment is *relative to the chunk start* (`schedule_batch.py:3044-3051`): "if
  `prefix_len` is off the absolute grid, so is the snapshot". Any future `chunked_prefill_size` that
  is not a multiple of 64 (e.g. 4096 is fine, 6000 is not), or any off-grid matched prefix, moves
  snapshots off the 64 lattice. Open PR #41701 and draft #43135 exist precisely to align chunk
  boundaries to the grid — proof the maintainers consider this a live defect.
* Two further effects that matter for a *long* prompt (> 8192): every prefill chunk is inserted, and
  **inserted KV stops at the latest snapshot**; KV computed past it is not inserted for an unfinished
  request. So a 12 000-token prompt can leave its reusable leaf at a chunk boundary rather than at
  12 000, and the next request's `cached_tokens` reflects that.

**Consequence for us:** keep all comparison prompts **below `chunked_prefill_size`** so every arm is
a single chunk, or hold `chunked_prefill_size` fixed and state it. Never compare a >8192 prompt
against a <8192 one and attribute the difference to cache behaviour.

### (d) Why does `page_size=1` still produce a hard 64-token grid? (the mechanism)
Because on this server the 64 grid is **not** page alignment at all — it is the **recurrent-state
checkpoint grid of a hybrid (linear-attention/Mamba-class) model**, and `page_size=1` does not
participate in it:

1. The radix tree's key granularity is `page_size` → 1 → keys can in principle split at any token.
   So the tree is *capable* of token-level matches.
2. But the model has a recurrent/linear-attention component. Its state is updated **in place** and
   cannot be rolled back to an arbitrary prefix (Marconi: in-place state updates "preclude rolling
   back cache entries for partial sequence overlaps, and instead mandate only exact-match cache
   hits"; Tail-Replay: matches are "directly usable only at positions aligned with stored
   checkpoints, constraining prefix reuse to a discrete set of boundaries"). SGLang therefore stores
   recurrent checkpoints only on a fixed lattice, and a request may resume **only from the deepest
   node that actually holds a state**.
3. The lattice constant is computed as
   `cache_chunk_size = max(model mamba_chunk_size, else FLA chunk size 64; page_size)`
   → `max(64, 1) = 64`, and
   `checkpoint_grid = lcm(cache_chunk_size, radix page size)` → `lcm(64, 1) = 64`.
   The documented worked example is literally our case: *"Qwen3.5 (GDN) with `page_size=1` gives
   `cache_chunk_size = 64`, `checkpoint_grid = 64`, `track_grid = 256`."*
4. The matcher then **floors** the full-KV hit onto that grid:
   `branching_seqlen = floor(full_kv_hit / checkpoint_grid) · checkpoint_grid`.
   So `cached_tokens = 64·⌊len/64⌋` whenever our nonce prefix is itself grid-aligned, and
   `uncached == len mod 64`.

**Check against the two observations:** 612 → 9×64 = 576, residue 36 ✓. 807 → 12×64 = 768,
residue 39 ✓. Both fit with no free parameters. The 64 is an **FLA kernel chunk size**, unrelated to
pages, unrelated to the 8192 prefill chunk, and unrelated to any flag we can set.

**The competing hypothesis must be excluded first, and it is cheap.** `page_size=64` would produce
*the identical signature* through pure radix-key alignment, with no recurrent layer in the model at
all. Before this note is cited as "hybrid checkpointing", read `page_size` back from `/server_info`
(it merges `get_server_args`) and confirm the model's architecture from `/get_model_info`
(`model_type` / `architectures`). If `page_size` is really 1 **and** the architecture has a
linear-attention/recurrent family, the mechanism above is the only known explanation that survives.
If `page_size` is 64, the whole 64 lattice is mundane page alignment and this section is
inapplicable. **This unit did not read the server; treat the `page_size=1` premise as inherited, not
re-verified.**

### (e) What is untestable with session cache disabled (flag OFF, no restart)?
`--enable-session-radix-cache` is required at launch, and the feature is *"implemented only by
`UnifiedRadixCache`"* — so with it off, everything session-scoped is **inert by construction**, not
merely unmeasured:

* **Untestable:** session-registered retention; the "unreferenced first, then referenced" eviction
  preference; whether a session's KV survives memory pressure; `/close_session` semantics (closing
  removes references but does not free KV); any multi-turn hit rate that depends on keeping one
  conversation's prefix resident; the session-aware HiCache/SWE-bench TTFT improvements reported in
  the LMSYS blog (2.9 %–16.6 % lower TTFT).
* **Also untestable, because the same gate likely rules it out:** any claim that *Unified* radix
  tree component semantics (FULL/SWA/MAMBA validators, component-level eviction) are active on this
  server, unless `/server_info` independently shows unified radix cache enabled. Mark such claims as
  conditional.
* **Testable with the flag OFF:** plain prefix reuse and its grid; the cold-vs-warm delta; the
  effect of a nonce prefix; the presence/absence of `prompt_tokens_details`; single-chunk vs
  multi-chunk prompt behaviour. In other words: **every single-turn, single-prefix measurement we
  actually need is available.** Session behaviour is the only casualty.
* **Cannot be worked around** by sending `session_id` from the client: the docs are explicit that the
  ID labels references only and does not reconstruct context, and the server-side flag is what makes
  references exist at all. Sending the field to a server without the flag is a no-op.

---

## 4. RECOMMENDED MEASUREMENT PROTOCOL

1. **Read the config before the first request.** `GET /server_info`; record `page_size`,
   `chunked_prefill_size`, `max_total_num_tokens`, `schedule_policy`, `mem_fraction_static`, whether
   unified radix cache and `enable_session_radix_cache` are on, plus server start time / uptime.
   Archive the response verbatim with the results.
2. **Record the model identity** from `/get_model_info` (`model_path`, `model_type`,
   `architectures`). The 64-grid claim is only interpretable against the architecture.
3. **Never call `/flush_cache`.** Isolation is achieved with a **fresh random nonce prefix** (≥512
   tokens, grid-aligned in length) per measurement family. If a globally cold server is ever
   required, stop and escalate for approval with a stated maintenance window.
4. **Warm up and throw it away.** Send ≥3 warmup requests on a *different* (nonce'd) prefix; the
   first request of a process is never a data point.
5. **Serialise.** Exactly one request in flight at all times; wait for the full response (or the
   stream end) before the next. Assert in-flight == 0 between steps.
6. **Use streaming and say so.** Streaming TTFT, identical `max_new_tokens` (small but > 0) in every
   arm, identical endpoint and chat template. Never mix stream and non-stream in one table.
7. **Take token counts from the response, never from a local tokenizer.** Log `prompt_tokens`,
   `cached_tokens` (with `null → 0` coerced and counted), `completion_tokens`, and the raw usage
   object per request.
8. **Submit each measured prompt as a pair:** (i) first send on a fresh nonce ⇒ expect `cached = 0`;
   (ii) immediate resend of the byte-identical body ⇒ expect `cached = 64·⌊len/64⌋`. Discard the
   pair if (i) is non-zero (contamination) or (ii) exceeds the expectation by more than one grid step.
9. **Hold prompt length in grid units.** Build prompts as `n·64 + 0` tokens for the clean case, and
   include at least one deliberate off-grid length to *characterise* the residue rather than to
   measure reuse.
10. **Keep every prompt below `chunked_prefill_size` (8192)** so each request is a single chunk; if a
    long-prompt arm is unavoidable, hold the flag fixed, cross the boundary in a separate labelled
    arm, and never compare across it.
11. **Log the grid explicitly** in every results table: `page_size`, `checkpoint_grid = 64`,
    `chunked_prefill_size`, and the URL/endpoint. A hit-rate number without these is not
    interpretable.
12. **Report medians over units, not sums.** Headline = median of per-request hit fraction (or
    per-session); token-weighted totals labelled secondary. Report `n`, number of misses, and the
    number of coerced nulls.
13. **Interleave arms in time** (A,B,A,B…) rather than running all A then all B, so that other
    tenants' traffic and eviction drift hit both arms equally.
14. **Sanity-trip every batch** on three invariants: `0 ≤ cached ≤ prompt_tokens`;
    `cached mod 64 == 0`; and no `cached > 0` on a fresh-nonce first request. A batch that trips any
    invariant is discarded and reported, not repaired.
15. **State the instrument's limits in the paper text:** `cached_tokens` is a server-reported
    reusable-boundary length that is floored to a 64-token recurrent-checkpoint grid, absent-means-zero
    on misses, and semantically unable to distinguish "eligible" from "actually reused".

---

### Unverified / do-not-cite
* `--enable-cache-report` semantics and its gating of `prompt_tokens_details` (hypothesis only).
* Whether `/flush_cache` drains HiCache L2/L3 tiers (only that it flushes "the radix cache").
* Whether SCBench or PrefixBench-H100 define an explicit cache-reset protocol (their abstracts
  describe workload control, not a reset API; full texts were not read).
* The served model's identity and the server's actual `page_size` — inherited from the parent, not
  re-measured here. `/server_info` + `/get_model_info` resolve both in two read-only GETs.
* Whether the local SGLang version's `checkpoint_grid` matches the commit read by the state-bench
  doc (`166b4ae7f`); the file:line citations are second-hand. One `grep` of the installed
  `sglang/srt/mem_cache/unified_cache/components/mamba.py` (if the package is present) would close this.
