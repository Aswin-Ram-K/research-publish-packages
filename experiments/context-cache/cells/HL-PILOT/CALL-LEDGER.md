# Call ledger — HL pilot, 2026-11-04

Every model request this pilot sent, per run. The plan's hard cap is **1,000 requests**;
`/tokenize` and `/flush_cache` calls are HTTP requests to the same server but are **not**
model requests and are excluded from the cap (they are counted separately in each run's
envelope notes).

| Run | Envelope | Model calls | Status | What it measured |
|---|---|---|---|---|
| PREFLIGHT | `envelopes/PREFLIGHT.json` | 3 | valid | does this build emit `prompt_tokens_details` on cold / repeat / rewritten head |
| E1 | `envelopes/E1.json` | 39 | **invalid** | boundary sweep; reps 2–3 were byte-identical to rep 1, two rewrites were no-ops, branches thrashed the mamba cache |
| E1B | `envelopes/E1B.json` | 14 | **aborted** | cell-isolated sweep, killed by its own no-op assertion (rotation shift 26 = identity) |
| E1C | `envelopes/E1C.json` | 48 | valid | boundary sweep, cell-isolated, per-rep distinct rewrites |
| E2 | `envelopes/E2.json` | 93 | valid | checkpoint cost over a 30-step trajectory, three arms, no-op controls |
| E4 | `envelopes/E4.json` | 264 | **quality void** | cost valid on LR-04 + LR-01; thinking was off and only pointed excerpts were embedded, so every arm failed the arithmetic checkpoints |
| E5 LR-04 | `envelopes/E5.json` | 120 | valid | three arms on the discovery fixture, thinking on, full sources |
| E5 LR-01 | `envelopes/E5.json` | 30 | **aborted** | 29 rows that raced a killed process, plus one whose 1200-token budget went entirely to reasoning and returned empty content; quarantined to `rows/e5-lr01-aborted.jsonl` |
| E5B LR-01 | `envelopes/E5B.json` | 8 + 144 | **first 8 void** | held-out arms after the ask-string fix; the first launch iterated every fixture and re-ran LR-04 by mistake (rows in `rows/e5b-lr04-duplicates.jsonl`), then the corrected 144 |
| probes | none | 4 | valid | 2 for thinking-on vs thinking-off answer shape, 2 for the ask-string sensitivity that produced `USER_ASK` |
| **Total** | | **765** | | under the 1,000-request cap |

Arithmetic: 3 + 39 + 14 + 48 + 93 + 264 + 120 + 30 + 8 + 144 + 4 = 765.

## Honest accounting notes

- **E1's 39 calls are counted even though the run is invalid.** A request that cannot be
  analysed was still a request. The defects are named in `envelopes/E1C.json`
  (`supersedes`) and in `rows/e1.jsonl`, which is kept unedited as evidence.
- **E1B's 14 calls left no rows.** The runner wrote rows only at the end of a run, and the
  run aborted at its own assertion. The 14 printed rows are summarised in
  `envelopes/E1C.json › supersedes`; the row file was never created. That defect is why
  E1C and every later runner appends and flushes each row as it is made.
- **E4's 264 calls produced no usable quality datum**, but they did produce a valid cost
  measurement of the same arms (E4 rows are kept). Its generation config, not the arms,
  caused the uniform failure, and the probe two calls later showed why.
- **The two PROBE calls are pre-registration evidence**, not part of any envelope: they are
  what justified repairing the instrument before E5 rather than after it.
- **Retries are counted.** The adapter never retries internally; E5's runner retries a failed
  call at most once and records the failed attempt as its own row with `retry_of`.

## Request-ledger book value

`experiments/ptr-engine/measure/REQUEST-LEDGER.json` (main checkout) recorded **2,591 requests
spent, 1,729 remaining** before this pilot. This pilot's ≈ 756 requests are not yet written
back into that ledger: it lives in the main checkout, and this pilot wrote nothing outside
its own worktree. `pins.py` records its digest (`8ebf4ed5…`) so the arithmetic can be
reconciled later by whoever owns that file.
