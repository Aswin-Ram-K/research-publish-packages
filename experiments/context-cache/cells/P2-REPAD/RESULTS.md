# P2-REPAD — the grid-aligned arm, re-measured with the pad precomputed

**Verdict: `padding_costs`.** On production occamy (`:8012`, the O1 substrate), aligning the
tail to the 64-token grid buys back a real but smaller amount of cache than the pad costs:
**+20.84 uncached tokens/turn [+9.86, +31.49]** against P1. Relative to whole-context resend
(P0) the aligned arm is **null (+6.50 [−35.46, +45.97])**. The earlier "−51.5 % / padding
halves cost" number does not survive a single-send measurement.

## What was wrong with the number being replaced

`O3-P2-REPEAT` recorded P2 at 389.41 unc/turn, and the original O3 run at −51.5 % vs P0.
Both were the **second send** of a same-turn alignment correction (68/71 rows in the repeat,
70/71 in the original): the row's `cached_tokens` was the *first* send's prompt, so the
recorded cost excluded a send. This run has **no correction path at all** — one request per
measured turn.

## Run

| | value |
|---|---|
| rows | **213** = 71 × (P0, P1, P2) |
| live requests | 224 (213 rows + 8 `/tokenize` spot checks + 3 G0) |
| `corrections_total` / `rows_with_correction` | **0 / 0** |
| `rows_multi_send` | **0** |
| P2 aligned rows | **71/71** (`prompt_tokens % 64 == 0`) |
| pad total / mean | 6,737 / 94.89 tokens/turn (range 64–127) |
| substrate | `:8012` occamy-1.0, page_size 1, `extra_buffer`, `lru`, `max_mamba_cache_size 64`, `mem_fraction_static 0.45`, ctx 131072 |
| salt / digests | `o3-repeat-20261024T11:05Z-a1`; P0/P1 `prefix_sha256` match `cells/R2-PROMPT/O3-REPEAT` 4/4 |
| pad precompute | `/tokenize` on turns 1,11,…,71 returned exactly `base_tokens + pad_target` every time (delta 0); `template_offset` 2 |

Pad rule: `pad_target = (−base_tokens) % 64`, raised to ≥64; `base_tokens` is the P1 row
measured **in this same run** for the same turn (P1's bytes are P2's bytes). Filler is
`" PAD"` repeated — the server's tokenizer shows it is exactly one token (59671) per
repetition, and the padded text always ends in the same fixed canary, so the boundary is
constant.

## Arms (n = 71 each, sequential, one request per turn)

| arm | mean unc/turn | bootstrap CI | t-CI | hit fraction | mean prompt |
|---|---|---|---|---|---|
| P0 whole-context | 541.07 | [500.72, 581.70] | [499.77, 582.37] | 0.9561 | 12,336 |
| P1 pointer + tail | 528.64 | [521.14, 536.27] | [520.93, 536.36] | 0.7705 | 2,300 |
| P2 P1 + grid pad | 549.49 | [542.17, 556.80] | [541.91, 557.06] | 0.7704 | 2,395 |

Hit fractions are not comparable across arms with different prompt denominators (the
`R2-PROMPT-SUSPECT` finding); **unc/turn is the comparable quantity**.

## Deltas (paired by turn, bootstrap 10,000 resamples, seed 20251024)

| contrast | mean Δ unc/turn | bootstrap CI | t-CI | reading |
|---|---|---|---|---|
| P1 / P0 | −14.34 | [−57.43, +26.96] | [−57.38, +28.69] | **null** (slightly negative point estimate) |
| P2 / P0 | +6.50 | [−35.46, +45.97] | [−35.30, +48.30] | **null** |
| P2 / P1 | **+20.84** | **[+9.86, +31.49]** | [+9.73, +31.96] | **costs** (+3.94 %) |

## Alignment effect, separated from cost

`alignment_gain = prompt_P2_aligned_len − cached_P2` on every first-attempt row:
**549.49** tokens/turn (i.e. 77.04 % of the aligned length is cached, 22.96 % is paid).

What the pad actually buys, measured on the same turn as P1:

- extra cached tokens vs P1: mean **74.06**, distribution **0 ×9, +64 ×41, +128 ×20**
- pad paid: mean **94.89**
- net: **+20.84** → only ~22 % of the pad is recovered; ~78 % of it is paid

Mechanism visible in the rows: an aligned request ends on a page boundary, so the next request
reuses **one further 64-token page** (41 turns: +64; 20 turns: +128). The pad is 64–127 tokens,
so the trade can never be positive on average and here it is not.

## Self-hit guard

The card's literal wording ("no row's `cached_tokens` equals a previously-sent prompt's
rounded length") fires **63** times — and is **degenerate on an aligned arm**: every P2 prompt
is a multiple of 64 by construction (a contiguous 576…4224 ladder), and every cached count
returned by the endpoint is a multiple of 64, so a legitimate hit equals some earlier P2
prompt length by pigeonhole. The decisive guard — `cached_tokens` equals the **immediately
preceding send's** whole prompt length (the correction artefact's signature) — fires **0**
times. `self_hit_guard.verdict = PASS`, basis `decisive_immediate_prior` + single-send.

## Where this goes

`state/r2-p2-repad.json` is the artefact. The matrix and the results doc are **not** edited
here (the merge card owns them); the sentence to withdraw is "grid-aligned padding halves
cost" for O3/O2/O4, and the replacement sentence is: *alignment recovers up to one page
(≤128 tokens) per turn and costs 64–127 tokens of pad, netting a small cost, null against
whole-context resend.*

Production was never stopped, restarted or reconfigured: `:8012` served every request of this
run and answers `occamy-1.0` / `max_model_len 131072` after it.
