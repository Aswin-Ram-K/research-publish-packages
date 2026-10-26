# TRACK-INTERVAL — does `--mamba-track-interval` move the cache grid?

**Measured on** `occamy-1.0` / SGLang `0.0.0.dev1+g4ccff141d` at `192.168.2.168:8012`, three restart-level arms (T0 256, T1 128, T2 64), each 5 prompt arms x 71 turns at a 32768-token budget (355 rows), then a pressure run at 1.54x pooled capacity. The cell is `PROMPT-O1` verbatim (same renderers, salts, budgets); only the serving interval changed. 1,065/1,065 rows HTTP 200, 0 null `cached_tokens`, warm-up call 2 `cached_tokens = 5568` in all three arms (G0 alive).

## What the source says

`/sgl-workspace/sglang/python/sglang/srt/server_args.py:2575-2577`:

```python
mamba_track_interval: A[
    int, "The interval to track the mamba state during decode.", NS("exec.mamba")
] = 256
```

Constraint inside `_validate_mamba_extra_buffer` (`server_args.py:5861-5864`):

```python
if view.speculative_num_draft_tokens is not None:
    assert view.mamba_track_interval >= view.speculative_num_draft_tokens
if view.page_size is not None:
    assert view.mamba_track_interval % view.page_size == 0
```

So the binding rule is **divisibility by `--page-size`** (live 1, not 64) plus `>= speculative_num_draft_tokens`; the semantics — "every `--mamba-track-interval` tokens the state is handed to the radix tree" — are at `scratch/vm1/llms-full.txt:48037` (arg table `:77456-77458`).

**Production value:** 256, from `/get_server_info`. The container argv also carries `--mamba-track-interval 256` **explicitly** — production was not running the implicit default, contrary to the card's premise.

## One table, three rows

| arm | R | A | C | H | C0 | gcd(cached) | resident window | max_total_num_tokens |
|---|---|---|---|---|---|---|---|---|
| T0 · 256 | 600.3 [558.9, 641.6] | 529.3 [521.6, 537.0] | 547.1 [539.5, 554.7] | 962.0 [739.4, 1184.6] | 709.9 [658.6, 761.1] | 64 (0 off-grid) | 2 docs / 199,538 tok | 1,514,033 |
| T1 · 128 | 600.3 [558.9, 641.6] | 527.5 [519.8, 535.2] | 547.1 [539.5, 554.7] | 962.0 [739.4, 1184.6] | 709.9 [658.6, 761.1] | 64 (0 off-grid) | 6 docs / 598,614 tok | 1,512,903 |
| T2 · 64 | 600.3 [558.9, 641.6] | 524.8 [517.3, 532.3] | 547.1 [539.5, 554.7] | 960.2 [737.4, 1183.0] | 709.9 [658.6, 761.1] | 64 (0 off-grid) | 7 docs / 698,383 tok | 1,512,950 |

*uncached tokens per turn, mean [95% t-CI, n=71]; grid over all 355 rows; resident window = 100k-token documents still fully cached after 2,337,132 unique tokens (1.544x capacity).*

Paired deltas against T0 (same prompt, same turn):

| interval | R | A | C | H | C0 |
|---|---|---|---|---|---|
| 128 vs 256 | 0.00 [0.00, 0.00] | -1.80 [-5.40, 1.79] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] |
| 64 vs 256 | 0.00 [0.00, 0.00] | -4.51 [-12.33, 3.31] | 0.00 [0.00, 0.00] | -1.80 [-4.33, 0.72] | 0.00 [0.00, 0.00] |

## Three separate questions, three separate answers

1. **Grid — did NOT move.** `gcd(cached_tokens) = 64` at 256, 128 *and* 64; 0 of 1,065 rows sits off the 64 grid. The reuse unit is already 64 tokens at the production interval: `_mamba_cache_chunk_size = 64` (runtime), not `--mamba-track-interval` 256. The premise that up to 255 tokens per turn are unreusable because of a 256 cadence is refuted — there is nothing for 64 to recover.
2. **Cost — did not move beyond noise.** Lowering to 64 changes A by -4.51 [-12.33, 3.31] unc/turn and H by -1.80 [-4.33, 0.72]; R, C and C0 are bit-identical (0.00 [0.00, 0.00]). At 128, A is -1.80 [-5.36, 1.79]. No CI excludes zero; point estimates are <=0.9 % of the arm means.
3. **Capacity — no cost detected; the finer arms retained more, not less.** `max_total_num_tokens` is flat (1,514,033 / 1,512,903 / 1,512,950; -0.07 % at 64, inside the restart re-profiling drift this stack shows) and the 1.54x pressure window reads 2 -> 6 -> 7 resident 100k documents (200k -> 599k -> 698k tokens). It did not shrink. Caveat: one boundary observation per arm at 100k-document granularity, so the 128-vs-64 ordering is unresolved; what the data exclude is a capacity *drop* at 64.

**Baseline reproduction.** A 529.3, C 547.1, H 962.0, C0 709.9 reproduce PROMPT-O1 to 0.1 token; R reads 600.3 against the published 583.1 (+2.9 %, and R has the widest CI), so the arms sit on the same instrument.

**Recommendation: ship `--mamba-track-interval 256` (the SGLang default).** At 128 and 64 neither the 64-token grid, the per-prompt-arm uncached cost, nor the pooled capacity moves; the finer cadence only buys 2x/4x more state donation per slot.

