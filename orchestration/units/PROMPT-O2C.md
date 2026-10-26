# PROMPT-O2C — page_size=1 variant measured with the 9B stopped

**Status: done.** One launch (`gx10-p-o2`, image `72457f09d20e`, mem-fraction 0.22) with
`gx10-qwen9b` stopped for the run; 5 arms x 71 turns = **355 rows**; production restored.

## Launch
`--page-size 1 --mamba-radix-cache-strategy no_buffer --disable-overlap-schedule` (+
`--enable-cache-report`, required or `usage.prompt_tokens_details` is always null — the
production occamy container carries the same flag). Resolved startup:
`page_size=1, c128_page_size=16`; KV 114645 tokens, avail 51.84 GB at 0.22.

Memory: available **57003 MB -> 71784 MB** after `docker stop gx10-qwen9b` (+14781 MB).
No KV retry was needed (one launch at 0.22).

## Grid probe (3 calls, ascending prefixes, page-unfloored expectation)
L=957 -> prompt 957, cached 0; L=1013 -> cached 0; L=1121 -> cached 0. gcd(0) undefined.
An identical 7201-token repeat also returned `cached_tokens=0`. So at page_size=1 there is
**no 1k-token page grid at all**; the page-64 law `cached = 64*floor((L-1)/64)` is not
reproduced by this flag set. Hits do appear in the battery, but only from the 16384-token
chunk boundary (R and C0: 47/71 turns), giving grid_unit = 8192 over the rows.

## Per-arm (uncached tokens/turn, 95% t-CI, hit fraction)
R (4370.8, [3816.4, 4925.1], 0.6456); A (2300.2, [2047.3, 2553.0], 0.0); C (2312.0, [2059.2, 2564.9], 0.0); H (2416.8, [2147.5, 2686.2], 0.0); C0 (4437.4, [3877.2, 4997.6], 0.6454)

Deltas vs R: A-R (-2070.6, [-2601.8, -1539.4], True); C-R (-2058.7, [-2589.9, -1527.5], True); H-R (-1953.9, [-2488.2, -1419.6], True); C0-R (66.6, [-162.9, 296.2], False)
(ARMS_IDENTICAL guard: no collisions.)

## Interpretation
With the 9B stopped and 0.22, the legal page_size=1 stack runs, but it buys almost nothing:
A/C/H never reuse (0 of 71 turns); R and C0 reuse only beyond the 16k chunk boundary.
The win in unc/turn is an artefact of different prompt lengths per arm, not of prefix reuse —
C0 (same body, no index) is statistically indistinguishable from R (+66.6, CI crosses zero).

## Restore
`gx10-p-o2` removed; `gx10-qwen9b` started. `:8014` 200 `qwen3.5-9b`, `:8012` 200
`occamy-1.0`, both production containers Up; `gx10-occamy-nvfp4` never touched.
