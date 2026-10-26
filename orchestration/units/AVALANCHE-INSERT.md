# UNIT AVALANCHE-INSERT — characterise the residue-{0,1} insertion avalanche (vLLM :8014, B=1056)

**Status:** running · **Bound:** 40 tool calls · **Sole writer on:** `:8014` (vLLM `qwen3.5-9b`)

## Purpose
Two units found the avalanche independently and neither explained it. MISS-LAW-2 localised it to
INSERTION (at `P1 mod B = 0` a byte-identical re-send of the prime matches nothing, while at residue 2 it
matches `6336`), which makes it a hash-chain/insertion defect, not a matching failure. This unit measures
the window, decides residue-vs-ceil, traces the "one block low" recovery, produces a minimal repro, and
states a mechanism with its discriminating evidence — or states the ambiguity.

## Questions
1. Window width: `{0,1}` or wider? measured, not predicted.
2. `P1 mod B` or `ceil(P1/B)`? exact multiples at nB for n = 1..5,7.
3. Is the anchor the last block or a lookahead? Recovery trace over 6 appends.
4. Minimal repro at `B`, `B+1`, `2B`, `2B+1`.
5. Mechanism + the cell that excludes each alternative.

## Method
- Cell shape = MISS-LAW-2 `G6` exactly: prime → **byte-identical re-send** → append of ONE token.
- Instruments: Δ`vllm:prompt_tokens_cached_total` (tokens) across one serialized request; **plus** client
  TTFT with a time-to-first-byte fallback (the previous probe logged `None`, which is why its TTFT column
  was empty on 1-token generations).
- Coldness: unique 10-token NONCE permutation per rep → constant length, unique prefix. No `/flush_cache`,
  no restart.
- Exact lengths: `prompt_tokens` is read back from the server on every prime and every cycle is appended
  with its measured length; a `LENGTH-MISMATCH` flag goes into the row when the server disagrees with the
  aimed length.
- `rows.jsonl`: one row per request, `flush()` + `fsync` per row.

## Write paths
`experiments/miss-law/avalanche/` (probe.py, rows.jsonl, log.txt), `orchestration/units/AVALANCHE-INSERT.md`,
`orchestration/handoffs/AVALANCHE-INSERT.json`. Nothing under `vllm2/`, `LAW.md`, `rows.jsonl`, `law_fit.json`,
`run.py`, `grid2.py`, `agg.py`. Never `:8012`. Never `/home/zer0null/Duval`.
