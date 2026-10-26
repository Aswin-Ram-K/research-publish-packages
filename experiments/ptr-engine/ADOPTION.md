# ADOPTION — what Duval would have to do to use the pointer engine

Everything here is derived from [`RECORD.md`](RECORD.md). The failure-mode numbers rest on measured rows — items 15/17 on `experiments/ptr-engine/measure/rows.jsonl` and the 2026-10-26 live cells (`measure/rows-live-2026-10-26.jsonl`) — so only the assembly is new, not the measurements.

## The three decisions this changes

1. **What travels in the prompt.** Bodies stop being re-sent; the turn carries a 12-line index (447 B for 12 bodies of ~2500 B) and the model fetches by reference. Measured saving at that corpus: 30000 B of body behind a 447 B index, r = 67.1x, and 78.3x with the compact index. This is an index-encoding choice, not a constant — at a different body count the ratio moves. `RECORD.md` §1.
2. **How bodies are retained.** Three measured policies: keep everything (task 3/3), keep the last 3 (0/3, but **33/33 honest `PTR_STORE_MISS` refusals, zero silent wrong answers**), destroy-by-compaction to 200 B (3/3 while the fact body survives). Retention is a capability decision, not a cost one: cost could not rank "keep" against "compact" at 3 reps. `RECORD.md` §4.
3. **How a bill is computed.** Not from prompt-token arithmetic. A law-computed bill was 57.6× low against the server's own cache counters, because the append length was fed the whole prefix. Endpoint matters: `meta_info.cached_tokens` is a `/generate` field, while the engine's own runners post `/v1/chat/completions` (`experiments/ptr-engine/measure/run_cells.py:109`), where it is absent — on that path read `usage.prompt_tokens_details.cached_tokens` per turn. Expect that field to be null where something *was* cached only in the residue-{0,1} regime; at residues 2–5 on `:8012` it reports 384/320/320 in `measure/rows.jsonl`. `RECORD.md` §3, §5 C1/C3.

## Preconditions, as measured (not as recommended)

| item | value measured | source |
|---|---|---|
| endpoint / model / engine | `:8012`, `occamy-1.0`, SGLang, `page_size=1`, `enable_cache_report=True`, `max_model_len=131072` | `RECORD.md` §2; `experiments/miss-law/LAW.md:27` |
| block size B | 64 (SGLang); 1056 on the vLLM half | `RECORD.md` §2 |
| mamba cache / hybrid-state settings | `max_mamba_cache_size: 64` recorded for `:8012` (captured once 2026-10-20T23:03:42Z, `cells/U2/server_config.json`); not swept by this package — do not tune it from this page | `papers/context-cache/EVIDENCE.md:16` |
| index | 12 lines, 447 B, 37.25 B/line, deterministic sha256 across processes and warmpool roots | `RECORD.md` §1 |
| Python | 3.11+ (executed on CPython 3.14.4), no third-party dependency | `RECORD.md` §1 |
| warmpool location | outside the repository; inside is refused with `PTR_WARMPOOL_INSIDE_REPO` | `RECORD.md` §1 |
| append framing | `L = n_payload + 12` | `RECORD.md` §2 |

## Failure modes measured

- **Body absent under retention cap** → `PTR_STORE_MISS` reaches the model as text, 33/33, and the model abstains. The engine says so rather than returning nothing.
- **Prompt lands on residue 0 or 1** → the cached prefix is lost. On SGLang the `BILL-AUDIT` reading — a reading, not the record's verdict — is one block: 64 + L at residue 0, 1 + L at residue 1; `RECORD.md:114` (C1) calls that magnitude UNDECIDABLE, and the padded residue-0 cell reports `cached_tokens: null` (cell C, pad 58, P1 384), so only the 2026-10-26 unpadded cell A 397/320 fixes residue 0 (`RECORD.md:153`). On vLLM the whole prefix re-bills with an 8.5× TTFT jump (warm-vs-warm, cell G6, `RECORD.md:145`). Recovering costs one request.
- **Cache-field null** → `usage.prompt_tokens_details = null` occurs on the *warm* request too, so a client reading only that field records a total miss where one block was billed. One client did; the "overstated an append 5.2×" reading that followed is WITHDRAWN and its magnitude re-classified UNDECIDABLE (`RECORD.md:114`, C1). The surviving advice is the narrow one: do not read `cached_tokens` alone.
- **Superseded revision** → a reference pinned to an old revision is refused `PTR_REVISION_MISMATCH` while its bytes survive; that is deliberate, not a bug.
- **Index-only prompt** → the model does not refuse; it echoes a digest (0/3 task success, 0 bodies resolved). An index-only arm needs a firm "no body" control or it looks like an answer.

## Do not do this

- Do not pad the prompt to a "safe" residue hoping to buy insurance. Padded cycles *are* measured — cells B/C/D of `experiments/ptr-engine/measure/rows.jsonl` at pads 60/58/50, 3 reps each — and at residue 2 they obey the law: predicate `pad_tokens > 0` with `cached_reported: true` gives cell B P1 386 → cached 384 / uncached 15 and cell D P1 322 → cached 320 / uncached 15 (`uncached = residue + L`, L = 13). What does not exist is a compact-**index**-unpadded cell (gap #17, NEEDS-LIVE), so the padding study remains an uncalibrated offline model.
- Do not quote a per-turn cost from `Σ prompt_tokens` plus a law term; that is the exact method that was 57.6× low.
- Do not treat `cached=null` as zero, and do not treat a self-consistent replay (387/387) as wire confirmation — it reused the same file's own field.
- Do not cap retained bodies and call the token saving a win: the cheap arm was cheap because it failed.
- Do not cite the quality arm's 34.4 k billed-token figures, or any A-vs-C cost gap, as measurements. Its own "billed telescopes exactly" claim is refuted by its rows: C rep2 carries a **+17,193** residual, and `usage.prompt_tokens_details.cached_tokens` never reaches `rows.jsonl` (`orchestration/handoffs/V-QUALITY-ARM.json:checks[5]`).
- Do not use the harvested 378 avalanche rows as SGLang evidence: `experiments/miss-law/avalanche/HARVEST.md` consumed 270 of them (141 show the avalanche, `cached>0`; 129 do not) on one vLLM profile only (`:8014`, `qwen3.5-9b`, B = 1056), where the residue effect is not separable from P1 (`RECORD.md:132`, C9).
- Do not carry a test count without naming the branch: 95 / 100 / 108 / 153 / 171 are five numbers for "the engine's tests".

*Corrections 2026-10-26: eight items rewritten after the independent audit in `orchestration/handoffs/ADOPTION-AUDIT.json` (items 6, 7, 10, 15, 17, 20, 25, 27); every re-derived number is quoted with its row predicate. Pass recorded as `ADOPTION-FIX`.*
