# M1-R — Can a mid-context edit keep what precedes it? (prefix vs suffix)

**Status:** done. **One-line answer:** *the prefix half is already free and automatic, but it is
paid out in whole 64-token blocks, not "exactly k" tokens; the suffix half cannot be recovered by any
prefix-cache configuration — and on this hybrid model no cheap trick recovers it either. What actually
works is not caching: it is never rewriting the head.*

Card, bound and write paths: this file is the card. Bound: **≤40 tool calls, no live model request**
(honoured: 0 POSTs to the endpoint, 5 read-only GETs: `get_server_info` ×2, `get_model_info` ×1,
`metrics` ×2). Write paths: `orchestration/handoffs/M1-R.json`,
`orchestration/units/M1-R.md`, `scratch/m1r/`.

**Method.** Three evidence classes, kept separate throughout: (i) **live** measurements already on
disk, re-derived offline by `scratch/m1r/verify_laws.py` → `scratch/m1r/laws.txt`; (ii) **vendor docs**
fetched this session (digests in `scratch/m1r/provenance.txt`); (iii) **papers**, fetched this session
where marked *(fetched)*, otherwise taken from the verified table in
[`orchestration/handoffs/U-LIT-REVIEW.md`](orchestration/handoffs/U-LIT-REVIEW.md).

---

## A. The prefix side — what survives an edit at item 165

### A1. The law, and it is not "exactly k"

For a request whose token sequence first differs from a cached sequence at token `k+1`, the reusable
amount on this cluster is

```
cached_tokens = 64 * floor( min(k, L-1) / 64 )
```

i.e. **the longest byte-identical prefix, rounded down to a whole 64-token block**, with one
refinement at exact multiples of 64 (A5). Evidence, all re-derived this session:

| Evidence | Result | Source |
| --- | --- | --- |
| 44 warm repeats, L = 314…1550, 33 distinct residues | `cached == 64*floor(L/64)` on **44/44**; `uncached == L mod 64` on **44/44**; 0 violations | `experiments/context-cache/cells/U2/u2_rows.jsonl` (e.g. `:4` L=391 → cached 384), re-run in `scratch/m1r/laws.txt` |
| 15,787-token prompt | cached 15,744 = 64×246, residual 0 | [`orchestration/handoffs/U2.json`](orchestration/handoffs/U2.json) `e2_chunked_prefill_probe` |
| **954** non-zero cached counts across every jsonl under `experiments/context-cache/` | **0** are not divisible by 64 | `scratch/m1r/laws.txt` GLOBAL block |
| prompt of 42 tokens | cached **0** — nothing is cacheable below one block | [`orchestration/handoffs/U2.json`](orchestration/handoffs/U2.json):15 `boundary_under_64` |
| break at the head (fork root, ~3.1k prompt) | cached **64** on 187/190 rows — the invariant preamble is exactly one block | `experiments/context-cache/cells/U5/u5_raw.jsonl:4`; distribution in `scratch/m1r/laws.txt` |

So the honest answer to "is it exactly k, or floored?" is **floored**, and the floor is 64 on this
server for two stacked reasons: the radix tree matches whole edges, and — the binding one here — the
30/40 linear layers keep recurrent state that is only valid at a **checkpoint**. Vendor statements of
the mechanism: *"A recurrent state is valid only at an exact prefix checkpoint"* and FULL/SWA/MAMBA
components *"share the same token prefix, but not the same reusable boundary"*
([`U-LIT-REVIEW.md:44`](orchestration/handoffs/U-LIT-REVIEW.md), LMSYS unified-radix-cache blog);
*"Mamba state is stored only on the Mamba block grid, so a prefix-cache hit can resume only at a block
boundary"* (vLLM APC docs, `features/automatic_prefix_caching.html`, fetched); Marconi: in-place state
updates *"preclude rolling back cache entries for partial sequence overlaps, and instead mandate only
exact-match cache hits"* (arXiv:2411.19379, MLSys 2025, [`U-LIT-REVIEW.md:32`](orchestration/handoffs/U-LIT-REVIEW.md)).

**The constant 64 itself is measured, not documented.** SGLang does expose a related knob —
`--mamba-track-interval` (default **256**, "*only used when `--mamba-radix-cache-strategy` is
`extra_buffer`*") — but it governs decode-time state tracking, and this server does not set it. The
64 comes from the data (954 counts, zero exceptions). Treat "64" as an **empirical invariant of this
deployment**, re-checkable in one command, not as a published constant.

### A2. In-place replacement vs insertion

**For the prefix, they are identical.** Both break at the first differing token; reuse is
`64*floor(min(k, L-1)/64)` either way. An in-place replacement of equal token count does not buy a
single extra block. They differ only downstream:

* **Insertion** shifts every later token's absolute position → the suffix's *content* is unchanged but
  its *position* is wrong (a fixable defect, in principle — B2);
* **In-place change** keeps positions but changes content → the suffix's KV is wrong in a way no
  positional adjustment can fix;
* **Insertion also changes `L`**, so it moves the prompt across the 64-grid and can trip the
  multiple-of-64 penalty (A5).

The literature's framing of why this is the whole problem: *"prefix caching can only save the prefill
of the first text chunk"* (CacheBlend, arXiv:2405.16444v3, fetched).

### A3. Reconciling our two measurements — one law, not two results

The two readings are **not in tension**; they are the same law evaluated at two different prefix
lengths. The discriminating variable is *how many whole 64-token blocks of byte-identical prefix
remain*, not "matchable boundary" vs "not":

| Test | Measured | What the law says | Reading |
| --- | --- | --- | --- |
| marker spliced at char ~2000 of an 807/813-token prompt | `cached = 0` | break inside block 0 (byte-identical prefix < 64 tokens, or the head itself re-rendered) → `64*floor(k/64) = 0` | the prefix was **not** destroyed; it rounded down to zero blocks. 813 is not a multiple of 64 (813 mod 64 = 45), so A5 does not apply |
| `PREFIX \| INSERT \| SUFFIX` structural test | `cached = 384` | `384 = 64×6` → the byte-identical prefix must have been **384–447 tokens** | the prefix *was* preserved — floored to 6 blocks. 384 is not a special "matchable boundary"; it is the grid floor of a ~400-token prefix |

The second test therefore does **not** show that a mid-prompt break is matchable. It shows the grid
doing its job on a prefix long enough to survive rounding. Corroboration that `cached` is always a
grid multiple — never "k" — is the 954/954 result in A1, plus 384 appearing only as `64×6` in the U2
sweep (`u2_rows.jsonl:4` and `:5` are the two L-values that land in the 384–447 window for a
different reason: 391 and 445 tokens are *whole* prompts, so `64*floor(L/64) = 384`).

⚠️ **Limit of this reconciliation.** The second test's artifacts are **not on disk** (searched:
`experiments/`, `state/`, `strategy/`, `papers/`, `orchestration/` — no PREFIX/INSERT/SUFFIX cell, no
run log). Its construction is reconstructed from the number itself. The arithmetic is forced, but the
*input* is not re-derivable. The first test is recorded only as an in-hand prior:
[`orchestration/handoffs/U-BENCH-PROTOCOL.json:238`](orchestration/handoffs/U-BENCH-PROTOCOL.json)
records *"0/813 cached for a marker at char 2000 of an 807-token prompt"*, and the protocol that was
meant to settle it (phase **C3**) has `experiments_run: False` — it was designed and never run.

### A4. Hybrid caveat: the prefix is *not* purely positional here

Because 30/40 layers are linear, the cached prefix is not just "KV rows at positions 1…m". It is
`(KV rows, recurrent state)` where the state is a **fold over the whole prefix**, valid only where a
checkpoint was stored. Two consequences the operator must know:

1. A prefix hit at a checkpoint boundary gives *bit-identical* state (SGLang's `extra_buffer` strategy
   keeps a second slot so the running request mutates its own copy — `--mamba-radix-cache-strategy`,
   this server: `extra_buffer`; docs fetched).
2. Any shortcut that *doesn't* land on a checkpoint is not "slightly stale" — it is invalid. Tail-Replay
   (arXiv:2608.30310, [`U-LIT-REVIEW.md:33`](orchestration/handoffs/U-LIT-REVIEW.md)) buys back
   non-aligned reuse with a **5–10 % replay budget** and still only retains **92.8–99.9 %** of
   full-prefill quality, at **9.1–14.3×** speedup at 32K.

### A5. The multiple-of-64 penalty (operational, easily missed)

If the prompt length is an **exact multiple of 64**, the *first* repeat pays a **full prefill**:
`cached = 0`, and only the *third* send hits (with the full `L`). Measured 10/10 vs 0/15, Fisher exact
p = 3.06e-07; a 0.25–2.0 s delay does not help, and an intervening unrelated request does not help
([`orchestration/handoffs/U10.json`](orchestration/handoffs/U10.json) `per_length_table`,
`delay_test_at_L1088`, `insert_test_at_L1088`; rows at
`experiments/context-cache/cells/U10/u10_rows.jsonl:3-4` → L=1024: rep1 cached **0**, rep2 cached
**960** = 64×15). For a 200-item list, item boundaries are content-dependent, so this is a genuine
lottery: pad the prompt off the 64-boundary.

---

## B. The suffix side — why 166…200 is stale, and what gets around it

### B1. The causal argument, in one paragraph

Each token's KV is `f(x_i, KV_{<i})`. Change token 165 → its hidden state and KV change → every token
`j > 165` attends over the *new* `KV_165`, so its own hidden state changes → its KV changes. The
staleness therefore propagates to the end of the sequence: it is not a positional bookkeeping problem
but a semantic one. CacheBlend states exactly this as the reason reuse "regardless prefix or not" is
hard: a reused non-prefix chunk's KV *"ignores the cross-attention between the chunk and the preceding
text … Ignoring cross-attention can lead to a wrong response"* (arXiv:2405.16444v3, fetched). The
empirical size of the error when you ignore it is not small: prefix-conditioned composition preserves
only **47.2 %** (HotpotQA-500) and **37.8 %** (2Wiki-500) of full-prefill answers (SAFE-KV,
arXiv:2610.15186, [`U-LIT-REVIEW.md:29`](orchestration/handoffs/U-LIT-REVIEW.md)); direct non-prefix
reuse across agents with conflicting tasks costs *"up to a 90 % drop"* (LatentRemedy, arXiv:2610.18014,
[`U-LIT-REVIEW.md:30`](orchestration/handoffs/U-LIT-REVIEW.md)).

### B2. The methods, and exactly what each one breaks

| Method | What it does about the stale suffix | What breaks / cost | Serving-stack change? |
| --- | --- | --- | --- |
| **Position-shift / RoPE re-alignment** (Prompt Cache arXiv:2311.04934; EPIC arXiv:2410.15332; TurboRAG, EMNLP 2025) | Re-uses a chunk's KV by re-rotating it to its new absolute position. Prompt Cache prefills chunk `C2` behind a **dummy prefix of length ≥ C1** so its positions are right, keeping per-chunk buffers | **Only fixes position, never content.** Valid for *insertion of new text before an unchanged suffix*; useless for a *changed* token 165. Prompt Cache must precompute each chunk once per position it can occupy — *"each chunk's KV cache will have to be precomputed multiple times"* | Yes: model-side positional handling + cache layer (Prompt Cache is a prototype server, MLSys 2024) |
| **Under a hybrid linear model** | — | **Breaks completely.** You cannot re-rotate a recurrent state: it is a fold, not per-token KV. Marconi mandates exact-match hits; Tail-Replay allows replay only from stored checkpoints | — |
| **CacheBlend** (arXiv:2405.16444v3, EuroSys'25) | Reuses chunk KV *"regardless prefix or not"* and **selectively recomputes a small subset of tokens** to restore cross-chunk attention | Recompute budget **5 %–18 %** of tokens; quality loss **≤0.002 F1 / Rouge-L** vs full recompute; TTFT **2.2–3.3×** better than KV-reuse baselines / **4.1–6.6×** vs full recompute; throughput **2.8–5×** (all quoted from the fetched paper) | Yes: a cache/fusion layer (reference implementation lives in **LMCache**) |
| **Prompt Cache** (arXiv:2311.04934v2, MLSys 2024) | A **schema of prompt modules**; each module's attention states precomputed and reused wherever the module appears. A *changed* module is a different module → **hash miss → full recompute of that module**; only unchanged modules are reused | Positional accuracy is handled (§ above); cross-attention is **not** — this is exactly what CacheBlend criticises it for. Latency win: **8× (GPU) to 60× (CPU)** TTFT | Yes: schema + inference-server support |
| **LMCache** (arXiv:2510.09665) | Cache layer for vLLM/SGLang; prefix reuse + offload + PD disaggregation | **Non-prefix only via CacheBlend**, which LMCache ships: in-process `LMCACHE_ENABLE_BLENDING=True`, `LMCACHE_BLEND_SPECIAL_STR`, `LMCACHE_USE_LAYERWISE=True`, `LMCACHE_BLEND_CHECK_LAYERS=1`, `LMCACHE_BLEND_RECOMPUTE_RATIOS=0.15`; MP mode `lmcache server --engine-type blend` (docs fetched) | Yes — and note **both LMCache CacheBlend pages mention SGLang 0 times**: the blend engine is documented against vLLM |
| **vLLM APC** (docs fetched) | Prefix only, block-hash chained. On hybrid Mamba models: *"a prefix-cache hit can resume only at a block boundary"*; `--enable-mamba-shared-prefix-checkpoint` adds a checkpoint at the shared-prefix junction; `--prefix-match-unit 64` sets granularity | Longest-common-prefix only; nothing for a changed mid-token | Different engine |
| **SGLang HiCache / radix / sessions** (docs fetched) | **Nothing.** HiCache is a *tiering* change (GPU → host → storage); session-aware radix cache is an *eviction* change. Its own doc lists the referenced data as *"the reusable prefix path from the registered leaf to the root"* | Preserves prefix; recovers no suffix | Flags only (C, below) |
| **Item-level isolation** (per-item KV, independent recomputation — what a 200-item list would need) | The only structurally correct answer: each item is a chunk with its own KV, re-derived independently, then fused. = CacheBlend/RAGCache/EPIC territory | Fusion is *lossy without recompute* (B1 numbers); on this hybrid model the *recurrent* half cannot be chunk-localised at all, so fusion degrades to replay-from-checkpoint | Yes: new cache layer |

**The one-line upshot of B2:** every method that "recovers the suffix" is really *recomputing* the
suffix (or a sampled part of it). None of them *reuses* stale KV; the honest framing is
**recompute budget**, and the only question is how little you can get away with — 5–18 % on
full-attention models (CacheBlend), 5–10 % replay on hybrid models (Tail-Replay). SGLang has **no**
non-prefix path at all: `docs.sglang.io/llms-full.txt` (5,518,111 chars, fetched) contains **0**
occurrences of `non-prefix`, `CacheBlend`, or `match_prefix`.

---

## C. What *this* stack can do today

Read-only `GET http://192.168.2.168:8012/get_server_info` and `/metrics`, 2026-10-21. Raw captures:
`scratch/m1r/metrics.txt`; config keys quoted below are verbatim from the JSON.

| Key | Value | Meaning |
| --- | --- | --- |
| `disable_radix_cache` | `false` | **prefix cache is ON** |
| `radix_cache_backend` | `null` | built-in selection chain; `/metrics` shows `cache_type="UnifiedRadixCache"`, so the hybrid-aware tree is live |
| `radix_eviction_policy` | `"lru"` | alternatives documented: `lfu`, `slru`, `priority`, `tlru` (needs unified tree) |
| `enable_hierarchical_cache` | `false` | **HiCache L2/L3 OFF** |
| `hicache_storage_backend` | `null` | no L3 (`file`/`mooncake`/`hf3fs`/`nixl`/`aibrix`) |
| `hicache_ratio` / `hicache_size` | `2.0` / `0` | inert while HiCache is off |
| `enable_session_radix_cache` | `false` | **off**; supported by `UnifiedRadixCache`, i.e. flippable on this build |
| `enable_lmcache` / `lmcache_config_file` | `false` / `null` | **LMCache (and therefore CacheBlend blending) unavailable** |
| `page_size` / `chunked_prefill_size` | `1` / `8192` | — |
| `max_total_num_tokens` | `1,306,681` | — |
| `uses_mamba_radix_cache` / `mamba_radix_cache_strategy` | `true` / `"extra_buffer"` | hybrid recurrent cache is active |
| `max_mamba_cache_size` | `64` | slots, not a token interval |
| `enable_cache_report` | `true` | `/metrics` carries `cache_hit_rate` (0.9748) and `cached_tokens_total` (3.80e6) |

**Verdict:** everything that preserves `1…164` is already on (plain radix, hybrid-aware); every
mechanism in B2 that could touch `166…200` is **off, absent, or unsupported**:

* `--enable-session-radix-cache` — **possible, one flag**, but it is eviction protection, not a
  matcher change ("*The ID labels cache references only, so each request must still contain the
  intended prompt*"). Buys retention, not suffix reuse.
* `--enable-hierarchical-cache` + `--hicache-storage-backend …` — **possible, needs a restart and a
  backend**; buys capacity/cross-instance, not suffix reuse.
* `--radix-cache-backend` — **not a deployment flag in practice**: the docs define it as *"a
  radix-cache backend previously registered via `register_radix_cache_backend`"*, i.e. **server-side
  code**. It is the only in-tree hook where a non-prefix matcher could be injected, and it is a code
  change on the serving host, not a config line.
* **CacheBlend / blending — not reachable through SGLang today** (`enable_lmcache: false`, and the
  blend engine is documented only for vLLM). Reaching it means changing the serving engine.

---

## D. Ranked recommendation

Ranked by (a) preserves 1…164, (b) recovers 166…200, (c) effort, (d) evidence strength.

| # | Method | (a) 1…164 | (b) 166…200 | (c) Effort | (d) Evidence | Why here |
| --- | --- | --- | --- | --- | --- | --- |
| **1** | **Never rewrite the head — turn the edit into a tail append** (keep item 165 as sent, append a correction/`[note]`) | ✅ full, floored to 64 | ✅ **nothing is invalidated** — 166…200 stay valid | **Low** — prompt-assembly only, no serving change | **Strong, live on this server.** U15 arms A vs R, 40 turns each: at the compaction turn, arm R (head rewritten) cached **0 of 1,928**; arm A (append) cached **8,448 of 9,263** (`experiments/context-cache/cells/U15/rows.jsonl:18` vs `:98`). Arm hit rates 0.927 (A) / 0.924 (C) / 0.763 (F) / 0.737 (R) | This is the *only* option that recovers the suffix without recomputing it. Cost is a semantic one (the model sees the old value then a correction) — measure it before shipping |
| **2** | **Status quo: plain radix prefix** | ✅ floored to 64 | ❌ 0 | **Zero** | **Strongest.** 954/954 cached counts are 64-multiples; 44/44 warm repeats obey `64*floor(L/64)` (`scratch/m1r/laws.txt`) | This *is* the operator's "at least preserve 1…164", already satisfied. Nothing to build — unless the head is volatile, in which case it silently collapses to 0 |
| **3** | **`--enable-session-radix-cache`** | ✅ | ❌ | **Low** (1 flag, restart) | Medium — vendor docs; LMSYS reports 2.9–16.6 % TTFT for session-aware eviction, **not** a suffix win | Worth doing anyway: it protects the 1…164 prefix from eviction under memory pressure, which is the *other* way the operator loses the prefix |
| **4** | **HiCache L2/L3** (`--enable-hierarchical-cache`, `--hicache-storage-backend`) | ✅ | ❌ | **Low–med** (flags + backend + restart) | Medium-strong (vendor docs; LMCache 15× throughput on vLLM, arXiv:2510.09665) | Capacity, not matching. Buys prefix survival across evictions/instances |
| **5** | **CacheBlend / LMCache blending** | ✅ (as chunk prefix) | ⚠️ **partial**: 5–18 % recompute, ≤0.002 F1 loss | **High** — different engine (vLLM + LMCache `--engine-type blend`); prompt must be **chunk-separated and pre-tokenised per chunk** | Strong on full-attention models (paper numbers), **unverified on a hybrid model** | The genuine "item-level KV" answer — but it recomputes, and its recurrent half cannot be chunk-localised (B2) |
| **6** | **Position-independent caching** (Prompt Cache / EPIC / TurboRAG) | ✅ | ⚠️ only for *unchanged* text at shifted positions | **High** — model-side PE handling | Medium (MLSys 2024 / arXiv:2410.15332 / EMNLP 2025) | Wrong tool for a *changed* item; inapplicable to 30/40 linear layers |
| **7** | **Item-level isolation (per-item requests)** | n/a | ✅ by construction | **Medium** — N calls, loses cross-item attention | Weak for this workload | Only if the operator will trade context for isolation |

**Recommendation to the operator, in one sentence.** You already get 1…164 for free and you cannot
make 166…200 reusable — so stop trying to make the *suffix* cacheable and make the *edit* be the
suffix: keep the 200 items as an append-only prefix and, when item 165 changes, append the
correction instead of re-rendering the list. That is measured, not theorised (8,448/9,263 vs
0/1,928), and it needs no change to the server.

---

## E. Verified vs not (read before citing)

**Verified this session**
1. Law + grid: 44/44 (U2), 139 rows with 0 violations of `64*((L-1)//64)` (U9), 954/954 64-multiples
   (global scan) — `scratch/m1r/laws.txt`.
2. Multiple-of-64 penalty: 10/10 first-repeat misses, rep2 = grid value (U10 rows `:3-4`).
3. Head-rewrite collapse vs append survival on this server: U15 rows `:18` vs `:98`.
4. Live config: all keys in §C read from `/get_server_info`, 2026-10-21.
5. CacheBlend and Prompt Cache abstract/body quotes — fetched from `arxiv.org/abs/…` and
   `arxiv.org/html/2405.16444v3`; CacheBlend's 5–18 % / 0.002 / 4.1–6.6× are body text, the
   2.2–3.3× / 2.8–5× are abstract.
6. SGLang flag semantics + `--mamba-track-interval` default 256 + "0 hits for non-prefix" — fetched
   `llms-full.txt` (sha256 `671770ab…` in `provenance.txt`).
7. LMCache blending env keys and MP-mode command — fetched LMCache docs.

**Not verified / carried as gaps**
1. **The `PREFIX | INSERT | SUFFIX` 384-token test has no artifact on disk.** Its prefix length
   (384–447 tokens) is *inferred* from the grid law. Do not cite "384" as a measured construction
   until the cell is found or re-run.
2. **The 0/813 probe is an in-hand prior** (`U-BENCH-PROTOCOL.json:238`); its construction is not
   recorded, and the protocol phase meant to settle it (C3) never ran (`experiments_run: false`).
3. **No mid-prompt insertion has ever been measured on this server.** The prefix law is measured on
   *whole-prompt repeats* and on *head rewrites*; the mid-prompt case is inference from those. The
   next unit should close it with a bounded probe (below).
4. **"30 of 40 layers linear" is the operator's premise**, consistent with
   `uses_mamba_radix_cache: true` / `Qwen3_5MoeForConditionalGeneration` but not independently
   re-derived (no layer config on this host).
5. **CacheBlend's numbers are not verified on any hybrid model** — its 5–18 % budget is calibrated on
   full-attention LLMs (three open-source models, four datasets).
6. Semantic cost of the append-only correction is **unmeasured on this workload** (U15 is a cache
   unit; U5's accuracy comparison was fork vs summarise, within 2.63 points).

---

## F. Reproduce

```bash
# 1. prefix laws, offline, no network — prints every number cited in A1/A5/D
.venv/bin/python scratch/m1r/verify_laws.py        # -> scratch/m1r/laws.txt

# 2. live read-only config (GETs only)
curl -s http://192.168.2.168:8012/get_server_info | .venv/bin/python -c \
  'import json,sys;d=json.load(sys.stdin);print({k:d.get(k) for k in ["enable_hierarchical_cache","hicache_storage_backend","radix_cache_backend","enable_session_radix_cache","radix_eviction_policy","enable_lmcache","page_size","mamba_radix_cache_strategy","max_mamba_cache_size"]})'
curl -s http://192.168.2.168:8012/metrics | grep -E 'cache_hit_rate|cached_tokens_total|cache_type='

# 3. the two rows behind §D rank 1
sed -n '17,19p;97,99p' experiments/context-cache/cells/U15/rows.jsonl | \
  .venv/bin/python -c 'import sys,json;[print(r["arm"],"turn",r["turn"],"cached",r["cached_tokens"],"/",r["prompt_tokens"]) for r in map(json.loads,sys.stdin)]'
```

**Next unit (bounded, 8–12 live requests):** close gap E3 — send `PREFIX(≈400 tok) | X | SUFFIX`,
then `PREFIX | X' | SUFFIX` (in-place, same length) and `PREFIX | X''' | SUFFIX` (insertion, +7
tokens), and read `cached` each time. Prediction to falsify: `cached = 64*floor(len(PREFIX)/64)` in
all three cases (≈384), with the suffix contributing 0. If the insertion case shows *any* suffix
reuse, this report's Part B is wrong.
