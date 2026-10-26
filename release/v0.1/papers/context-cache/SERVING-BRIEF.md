# SERVING-BRIEF.md — what to run, what does not help, and the real capacity limit

**Audience.** Whoever operates the GB10 node behind `occamy-1.0`, and anyone deciding whether
to change the engine, the page size, the eviction policy, or the context budget.

**What this is.** A synthesis of measurements already on disk — it makes no new measurement and
issued no live request. One endpoint, two checkpoints, one GPU, synthetic serial corpora; the
honest scope is in *What this brief cannot tell you*.

**Evidence rule.** Every figure below is a row in the numbers table at the end, with its cell
and the one command that re-derives it. The table is generated from the cells; `serving_brief.py
--check` fails if a figure, a table row, or a prose number stops re-deriving. Dated 2026-10-23.

## The answer

- **Run SGLang on `occamy-1.0` with the production flag set.** It is the cheapest cell in the
  measured comparison, the production battery reproduces it at both depth bands, and the flags
  the operator already has are the ones measured. [S01] [S03] [S19]
- **Do not switch to vLLM to fix prefix reuse.** The engine, not the model, sets the reuse
  geometry and the per-turn cost. [S02] [S04] [S06]
- **Do not tune page size or the eviction policy.** Both were measured; neither buys anything. [S10] [S11] [S12]
- **Feed it shared prefixes and branch late.** The saving is bought by byte layout, not by
  cache knobs. [S08]
- **The capacity limit is the state cache, not the KV pool.** Plan for a couple of context
  windows of reusable prefix, not for the declared pool. [S14]
- **If you must compact, budget the per-turn cost after the boundary, not just the boundary
  turn.** [S15]
- **Instrument before you trust a hit rate.** A vLLM launch can silently report none. [S18]

## What to run

<!-- BEGIN SERVING-BRIEF MATRIX -->
| ID | Model | Engine | Reuse block | Hit fraction | Uncached/turn | Rows |
|---|---|---|---:|---:|---:|---:|
| S02 | occamy-1.0 (MoE) | vLLM 0.27.1 | 2096 | 0.901212 | 1682.7218 | 284 |
| S03 | occamy-1.0 (MoE) | SGLang | 64 | 0.957153 | 729.7641 | 284 |
| S04 | qwen3.5-9b (dense) | vLLM 0.27.1 | 1088 | 0.817432 | 879.0669 | 284 |
| S05 | qwen3.5-9b (dense) | SGLang | 64 | 0.956941 | 733.3697 | 284 |
<!-- END SERVING-BRIEF MATRIX -->

- **The engine is the whole effect.** Same weights, same GPU, same schedule: the SGLang rows sit
  together (both on the 64 grid) and the vLLM rows do not — on vLLM the MoE checkpoint costs
  far more per turn than the dense one — and the engine term is still the larger of the two,
  with the model term negative and engine-conditional: 0.5224x under vLLM against 1.0049x
  under SGLang. [S06]
- **MTP is part of this finding.** The Round-1 vLLM cell ran with `--speculative-config mtp`
  enabled, Round 2 with it disabled; removing it moved that cell by 2.54x. Decoder-speed
  features can change prompt-cache behaviour — that is a finding, not an apology.
- **Model choice is nearly free on SGLang and expensive on vLLM.** If the workload is dense and
  the engine is SGLang, the two checkpoints cost almost the same per turn; on vLLM the model
  term is far larger. [S07]
- **The production SGLang battery, both depth bands.** The deeper band costs only slightly more
  per turn than the shallower one, so depth alone is not a reason to compact. [S01]
- **Fan-out is bought by layout.** Keep the shared prefix byte-identical and branch late: the
  late-branch arm costs a fraction of the early-branch arm in uncached tokens. [S08]
- **Keep the flag set — of the knobs that were turned.** The measured production configuration is
  the one in the config capture, and of the knobs this brief measured (page size 64/128, one
  eviction policy at its default parameter) none pays. That is a statement about those knobs, not
  a licence for the whole flag set: the host tier and the four unrun policies were never turned
  (`GAPS.md` G16). [S19]

## What does not help

- **A different engine.** vLLM's reuse unit is the model's hybrid block, so a turn pays its
  growth plus the previous prompt's block remainder; SGLang pages at the engine's own unit on
  the same weights. The result is a multiple more uncached work per turn on vLLM. [S02] [S04] [S06]
- **Page size.** Page 64 against the production default changes almost nothing (the paired rows
  are nearly identical); page 128 moves the grid one block and is slightly worse per turn. [S10] [S11]
- **SLRU at its default parameter.** Under deliberate pressure it keeps only the newest band and
  the hit rate collapses; the measurement gives no reason to think the policy, rather than the
  pressure, explains the loss. **One policy of five:** SGLang also documents `lfu`, `tlru`
  (agentic/tail-latency, per the pinned policy page in `GAPS.md` G16) and `priority`, and
  `slru`'s own `protected_threshold` was left at its default 2 — none of those was run, so
  "eviction policy does not help" is not a finding this brief can make (`GAPS.md` G16).
  [S12] [S13]
- **An appended note past the window.** Once eviction starts, a note-shaped resend is not
  cheaper than a full resend; both hit nothing. [S13]
- **A bigger KV pool.** The pool is not the binding constraint, so buying more of it does not
  move the reusable window. [S14]
- **Cache accounting you did not enable.** A vLLM endpoint launched without the usage flag
  reports no cached-token field at all; the hit rate is unmeasurable from responses even though
  the engine is hitting. [S18]
- **Not measured here, so they are not recommendations against:** LMCache, HiCache, KV
  quantization, prefix routing and speculative decoding. No cell in this package tests them;
  treat any claim about them as unmeasured (the open gaps are listed in `GAPS.md`). The four
  the documents name as the capacity levers — HiCache's host tier on SGLang, `--kv-offloading-size`
  on vLLM (present in v0.27.1, unpinned flag), and four of SGLang's five radix policies — are
  named, unrun and untested here, not found wanting (CACHE-AUDIT, `GAPS.md` G16).

## The real capacity limit

The declared KV pool and the reusable window are different numbers. The pool is large; what
stays resident is small, and the binding constraint is the state cache. [S14]

- **Read the limit as documents, not tokens.** The measured resident window is a count of
  documents; its token size follows from how big those documents are. At this cell's document
  size it is on the order of a couple of context windows — far below the declared pool. [S14]
- **Past the window, only the newest band is reusable.** The replay under pressure hits the
  newest documents and neither the middle nor the oldest ones. [S13]
- **Compaction is a persistent per-turn cost, not a one-off.** After the boundary most
  compacting arms pay more uncached tokens per turn for the rest of the run; the quoted range is
  a range of arm means, and a single turn can be far above or below its arm's mean. [S15]
- **Appending is cheap per turn and unbounded.** The append arm keeps a high hit rate but its
  window grows every turn; the win over summarise-in-place is real and so is the bill. [S16]
- **A miss is expensive, a hit is nearly free.** The latency table is the reason the hit rate
  matters: at long prompts a miss costs seconds while a hit costs a fraction of that. [S17]
- **Boundary lengths are special.** A prompt whose length is an exact multiple of the engine's
  unit misses on the immediate repeat; nudging it off the boundary restores the hit. [S09]

## What this brief cannot tell you

- **One endpoint, two checkpoints, one GPU, one seed.** The engine comparison is a measured
  four-cell matrix at one band, not a law over engines or models; the model axis carries size and
  architecture together. See `GAPS.md` G4 and G12.
- **The mechanism behind the capacity bound is not established.** The state-cache reading is
  consistent with the numbers, not proven: the pure-attention control that would separate the
  hybrid-attention explanation has not run (G4, G7), and the cache numbers are the server's own
  accounting (G13).
- **Compaction was measured at two budgets on one corpus.** The direction is measured; the
  magnitude is one cell's (C62 scope).
- **Nothing here licenses choosing a vLLM block size or a page size as a tuning knob** — the
  measured units are what the engines chose, not knobs an operator can set to a target.
- **No unmeasured feature is recommended against.** LMCache, HiCache and friends are absent
  because no cell tests them, not because they were measured to fail.

## Every number, its cell, and its recompute command

<!-- BEGIN SERVING-BRIEF NUMBERS -->
| ID | Operator question | Measured value | Cell | Recompute from |
|---|---|---|---|---|
| S01 | Production SGLang battery, both depth bands | 888 rows, all 888 OK, 880 steady · hit 0.974242 · 739.2 uncached/turn (32k 725.74; 64k 746.01) | G3 | recompute.py C47 |
| S02 | occamy-1.0 (MoE) on vLLM 0.27.1, 32k band | hit 0.901212 · 1682.7218 uncached/turn · block 2096 · 284 rows | MOE-VLLM | recompute.py C63 |
| S03 | occamy-1.0 (MoE) on SGLang, 32k band | hit 0.957153 · 729.7641 uncached/turn · block 64 · 284 rows | G3 | recompute.py C63 |
| S04 | qwen3.5-9b (dense) on vLLM 0.27.1, 32k band | hit 0.817432 · 879.0669 uncached/turn · block 1088 · 284 rows | WIN-VLLM | recompute.py C63 |
| S05 | qwen3.5-9b (dense) on SGLang, 32k band | hit 0.956941 · 733.3697 uncached/turn · block 64 · 284 rows | DENSE-SGL | recompute.py C63 |
| S06 | Engine main effect vs model main effect | engine costs 2.3058x (MoE) / 1.1987x (dense) · engine effect 549.33 vs model -400.02 uncached tokens/turn · engine share 0.5459 | four cells | recompute.py C63 |
| S07 | Does the model choice matter on each engine? | model ratio 1.0049 under SGLang vs 0.5224 under vLLM · vLLM/SGLang model effect -222.8887 | four cells | recompute.py C63 |
| S08 | Fan-out: branch late, keep shared bytes identical | late branch B/A = 6.7443 [4.0454, 9.4432] · A 20,328 vs B 123,256 uncached tokens · 8 fan-outs, 64 branches | G5 | recompute.py C53 |
| S09 | Boundary lengths pay a full re-prefill on a warm repeat | 1,024 and 1,088 (exact unit multiples): 5/5 and 5/5 miss on the immediate repeat; 1,008 / 1,023 / 1,025: 0 misses each; pooled 35/35 vs 0/15, p 4.44e-13 · missed prefill 268.4 ms TTFT | U10 | recompute.py C40, C41 |
| S10 | Page size: 64 and 128 against the production default | S1 (page 64) 740.4 vs S2 (page 128) 752.6 vs S0 (production) 739.2 uncached/turn · S1 vs S0 identical on 887/888 paired rows · grid 64/64/128 | WIN-SGL, G3 | recompute.py C46, C47, C57 |
| S11 | The one page-size condition that moved the grid | 900 paired rows: 534 identical, 353 lower by 64, 13 higher · TTFT ratio median 1.005 · 740.4 vs 752.58 uncached/turn | WIN-SGL | recompute.py C58 |
| S12 | SLRU eviction policy under deliberate pressure | hit 0.034474 · 8,305.0 uncached/turn (11.2344x production) at 1.505083x pressure · bands newest 10/10, middle 0/10, oldest 0/10 · policy slru | TUNED | recompute.py C59, C60 |
| S13 | LRU at pressure, and whether an appended note survives it | replay bands: newest 0.997, middle 0.000, oldest 0.000 · append-note under pressure: hit 0.000 both shapes, 78.7 tokens appended | M4 | rows.jsonl phase R + analysis.json phase_d |
| S14 | Declared KV capacity vs resident reusable capacity | declared 1,620,892 tokens · resident 30-31 docs = 258,035-266,636 tokens = 0.1592-0.1645 of capacity · 283 docs, 1.501724x pressure, 2,434,133 tokens · binding constraint state_cache (consistent_with_lru; token-pool LRU 188.45 docs excluded) | M4 | recompute.py C54 |
| S15 | Compaction at a real 32k/64k boundary | 18 compactions in 2,780 rows · post-boundary +134.6 to +747.2 uncached/turn on average · per turn -927.0 to +5,473 · boundary turn 1,826-3,033 vs baseline drop 1,236-1,321 | G3-LIMIT-V2 | recompute.py C62 |
| S16 | Append-a-note: cheap per turn, unbounded window | append window 1,186 -> 19,583 tokens (16.5118x) · total prompt 412,177 vs control 403,259 · A beats summarise-in-place by 1.7002x | U15 | recompute.py C25, C21 |
| S17 | What a cache hit is worth in latency | 31,415-token prompt: 7,541.9 ms miss -> 231.6 ms hit (0.0307) · hit 4.66 us/token vs miss 0.240736 ms/token | U9 | recompute.py C32, C34 |
| S18 | vLLM without the usage flag cannot report cache hits | cached_tokens field absent from every response · engine counter moves exactly 1,056 tokens per repeat · 3 rows, 3 live requests | CROSS-HTTP | analysis.json cache_signal + engine_counters |
| S19 | The production flag set a reader must not change blind | context 131,072 · page_size 1 · max_mamba_cache_size 64 · mem_fraction_static 0.45 · disable_chunked_prefix_cache true | no cell; pinned config capture | state/config/live-server-config.json |
<!-- END SERVING-BRIEF NUMBERS -->

Re-check the whole brief (no live requests, no writes):

```bash
.venv/bin/python papers/context-cache/serving_brief.py --check
```
