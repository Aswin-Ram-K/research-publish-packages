# REASONING-PILOT-OFF — does `--thinking off` cut per-turn wall clock?

**Verdict: blocked** — the 600 s hard rule fired twice (A T3 640.96 s, B T1 686.54 s), so B stopped at n=1.
6/10 requests spent; A completed n=5. Rows: `rows-pilot-thinking-2026-10-26.jsonl`, never pooled.

## Pre-registered rule (verbatim)
ACCEPT `off` iff (i) ≥4/5 A-turns carry non-empty `content`, AND (ii) A mean `latency_s` ≤ 0.3 × B mean
`latency_s`, AND (iii) A mean `completion_tokens` < B mean `completion_tokens`. Otherwise REJECT.

## Numbers
| setting | n | content≠∅ | mean lat | median | p95 | mean comp | mean prompt | mean cached | finish |
|---|---|---|---|---|---|---|---|---|---|
| A `off` | 5 | 5 | 183.782 s | 83.476 | 640.96 | 4470.2 | 13013.4 | 8089.6 | stop×5 |
| B `on` | 1 | 1 | 686.540 s | 686.540 | 686.540 | 16384.0 | 1870.0 | 1856.0 | length×1 |

A (t,lat,comp,prompt,cached): (1,179.86,4465,1872,1856) (2,83.48,2027,6389,1856) (3,640.96,15624,8453,6336)
(4,9.38,119,24103,6336) (5,5.23,116,24250,24064). B1: finish=length, truncated=true, failed_turn=true,
timing_usable=false, content_source=both (reasoning≈143 tok, content≈32436 tok) — cap-truncated, not clean.
No checkpoint turn in T1..T5 → `content` never carries a checkpoint value (expected=null everywhere).
Clauses on raw numbers (advisory, B is n=1): (i) true 5/5 · (ii) true 183.782 ≤ 205.962, ratio 0.2677 ·
(iii) true 4470.2 < 16384. Not decision-grade: B has no timing-usable mean.

## Payload diff (same builder, dry-run preview, zero requests)
off 7368 B `{"chat_template_kwargs":{"enable_thinking": false}, "max_tokens":16384, "messages":<sha16 3f9c6eefdcc7b8de>, "model":"occamy-1.0-NVFP4", "stream":true, "stream_options":{"include_usage":true}, "temperature":0}`
on 7367 B same body with `{"enable_thinking": true}` — messages byte-identical, only that key differs.
Target `GET :8012/v1/models` → 200, id `occamy-1.0` (served alias; not literally NVFP4). No substitute endpoint.
Projection: 192 requests × A → 9.80 h mean, 4.45 h median, 34.18 h p95 (cheap, with a heavy tail).
Next: 4 requests left — `--run-id pilot-on-lr01-r1 --resume` to finish B, then settle.
