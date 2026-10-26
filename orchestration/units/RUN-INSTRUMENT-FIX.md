# RUN-INSTRUMENT-FIX — runner defects from RUN-STAGE1-LR01

Purpose: make `experiments/ptr-engine/longrun/run_longrun.py` a valid instrument after Stage 1
(`orchestration/handoffs/RUN-STAGE1-LR01.json`: 140/192 rows at the 128-token cap, 99/192 empty
because the parser read only `delta.content`). Bound: 60 requests, 30 tool calls.

## What was changed (card points 1-5)
1. `--max-tokens` default 128 -> 16384, configurable; every row carries `finish_reason`,
   `truncated`, `max_tokens`; the summary counts truncated rows and the smoke fails on any.
2. Both channels parsed: `delta.reasoning_content` -> `reasoning`, `delta.content` -> `content`;
   `content_source` in {content, reasoning, both, none}; `content` holds the answer-bearing text
   (falls back to the reasoning channel only when the content channel is empty).
3. TTFT per row: dispatch -> first token on EITHER channel, `ttft_ms` added beside `ttft_s`;
   `ttft_n` counted from rows, so it must equal the row count.
4. `--smoke`: 4 arms x 3 turns = 12 requests, per-row table, non-zero exit on any truncated row or
   any row with `content_source == "none"`. Also added `--max-turns` (resume-safe partial cells).
5. Contracted row keys unchanged; all new fields are additions.

## Write paths touched
`run_longrun.py`, the fix row file, `longrun/manifests/fix-*`, this card, and the handoff.

## Outcome
See the handoff. Headline: parsing/TTFT defects are fixed and proven; truncation is reduced by the
larger cap but is NOT eliminated — the endpoint itself is nondeterministic at temperature 0 (the same
T1 prompt answered in 639 tokens in one arm and rambled to the full 16384 in the next).
