# V-FOLD-RESIDUAL — settles the two `unverified` items from V-FOLD

Verifier, read-only, offline, 2026-10-25. Closes `orchestration/handoffs/V-FOLD.json:unverified[1]` and `[2]`.

## Q1 — does MANUSCRIPT.md cite pointer-structured context as related work?

**Verdict: TRUE, at the location the proposal names.** `papers/context-cache/MANUSCRIPT.md:926` —
`### 10a.3 Retrieval-structured or pointer-based context versus a plain transcript`. `MANUSCRIPT.md:928-929`: "Reusing KV
that is *not* a prefix is the class the pointer layout of Sections 3 and 9d starts from, and several surveyed methods go
further than this paper's scope." It cites Prompt Cache (arXiv:2311.04934, 8x-60x TTFT), EPIC/LegoLink (arXiv:2410.15332,
8x TTFT / 7x throughput) and CacheBlend (arXiv:2405.16444) to `docs/serving-options/R-CROSS.md` rows 1-3, then at
`:938-941`: "Against that class, this paper's pointer result is deliberately weaker in mechanism and stronger in
attribution". Line 9 needs no repair; only the label differs from the heading. Caveat: `:882-887`, `:921-923` mark 10a as a
bounded, no-bibliography section (GAPS.md G16), so the paper is not presented as fully positioned against the class.

## Q2 — where do the vLLM TTFT rows come from?

**Verdict: NOT FOUND as claimed.** `experiments/miss-law/vllm2/rows.jsonl` — 133 rows: 59 `role=prime`, 74
`role=measure`, over **9 cells** (CAL, CAL-T, G1..G7). Nine *cells*, not nine arms; no TTFT table compares nine arms.

- `1.585 s` is a **cold prime**, not an avalanche row: `pair_id G1-P6336-r0`, `role prime`, `P1_target 6336`,
  `cached_tokens 0`, `ttft_server_s 1.585238` (line 26; rep1 `1.585509`, line 32).
- `0.216 s` is a **warm measure**: cell G1 round 1, `P1=7450`, `cached_tokens 6336`, `ttft 0.216020 / 0.215932`.
  The proposal's `0.217` occurs 0 times in the file.
- Ratio **derived**: 1.585238/0.216020 = 7.338 (the record's 7.4 = 1.59/0.216) — different roles and lengths
  (6336 vs 7450 tokens), a cold-vs-warm contrast, not residue-0 vs residue-2.
- The real residue-0/1 rows are 1.235/1.242 (6336/6337), 1.788-1.792 (7392/7393), 2.218-2.226 (8448/8449).

## Disposition

- **Q1 survives:** "`§10a.3` (MANUSCRIPT.md:926, *Retrieval-structured or pointer-based context versus a plain
  transcript*) cites the non-prefix reuse class — Prompt Cache, EPIC/LegoLink, CacheBlend — and states this paper's
  pointer result is deliberately weaker in mechanism and stronger in attribution."
- **Q2 needs rewording:** "On vLLM a cold 6,336-token first send prefilled at TTFT 1.585 s (`vllm2/rows.jsonl`,
  `G1-P6336-r0`) while a warm turn with 6,336 cached tokens at 7,450 tokens served at 0.216 s, a derived 7.3x that
  contrasts cold with warm rather than residue 0 with residue 2."

Blocker: none. `overall=partial` only because the nine-arm provenance does not exist as described.
