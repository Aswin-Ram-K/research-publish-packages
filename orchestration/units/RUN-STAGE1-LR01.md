# RUN-STAGE1-LR01 — Stage 1 long-run instrument check

Status: done (instrument INVALID as configured; Stage 2 blocked)
Fixture: experiments/ptr-engine/longrun/runtime/LR-01.json (N=48, sha256 72c3832d…)
Arms: transcript-grow, transcript-compact, pointer-stable, lease-reopen × reps=1
Requests: 192 recorded turn requests (48/arm, 0 digest); ≤193 true after a mid-run harness
restart forced one `--resume` (pointer-stable T36 re-issued). Rows: 192, 0 parse errors, exit 0.
No HTTP failures, 0 usage_missing, 0 non-200.

## Per arm (TTFT over rows that carry it)
| arm | rows | ttft_n | p50 ms | p95 ms | mean_uncached | cached_share | completion |
|---|---|---|---|---|---|---|---|
| transcript-grow | 48 | 1 | 3560.9 | 3560.9 | 116.79 | 0.9502 | 6144 |
| transcript-compact | 48 | 41 | 630.1 | 1610.7 | 147.94 | 0.9635 | 5504 |
| pointer-stable | 48 | 12 | 525.9 | 2374.9 | 186.42 | 0.8840 | 5929 |
| lease-reopen | 48 | 39 | 1567.9 | 2448.4 | 60.42 | 0.6765 | 5463 |

## Findings
- Truncation dominates: 140/192 rows end exactly at max_tokens=128; 99/192 rows are empty.
- Checkpoints (T12 expect "64", T24 "31", T46 record_refusal line): all fail; only lease-reopen
  emitted prose at T12 and it said "1 ref".
- Repair turn T30: 0 of 4 arms performed it; all outputs truncated tool-call noise.
- Validity: cached_tokens yes; manifest sha256 yes; manifest exists yes; content non-empty NO;
  truncation recorded with turn NO (no finish_reason); is_checkpoint never set NO.
- Blocker: raise --max-tokens, capture reasoning_content + finish_reason, flag checkpoints from
  turns[].kind, then rerun Stage 1 (192 requests) before Stage 2.
