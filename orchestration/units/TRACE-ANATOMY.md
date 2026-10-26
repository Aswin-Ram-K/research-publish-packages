# TRACE-ANATOMY — where the tokens go in a real agent run (relaunch)

**Status: PARTIAL — the pinned file is not an agent transcript.**

## Objective
Measure where context tokens in a real agent run go, to judge whether a
pointer + warmpool design would remove waste.

## Inputs (pinned, digest-verified)
- `dockets/duval/duval-u55-pinned/material/data/2026-09-28-duval-m0.jsonl`
  - 866,816 bytes · 573 records · sha256 `431605e624ca90596ec8c5890fc40da08715ae1ffa6759b689255f1670af4ecb` ✅ matches the card.
  - **Content: a docket event ledger**, not a session transcript.

## Hard bound
≤30 tool calls, one pass; stop after 3 failed schema attempts. Used 13 calls, 5 schema probes.

## Finding (the schema defeats steps 2–6)
Every one of the 573 records has the same shape:

```
{'seq','ts','session','kind','subject','detail','hash','refs'}  (516 + 'evidence',
                                                                 15/19 + 'discoveredBy')
```

- `kind`: `commit` 527, `measurement` 14, `mistake` 10, `fix` 8, `decision` 7, `eval.run` 4, `discovery` 3.
- one `session` for all 573: `2026-09-28-duval-m0`; ts range 2026-09-28T12:35:11-05:00 → 2026-10-08T11:03:45.677Z.
- `detail` = commit-message prose, **max 4,000 chars** (2 records exactly 4,000 — truncated in the source), total 606,833 chars.
- `evidence` = a **one-line** proof string, 520 records, 29,286 chars total, mean 56.3 chars
  (e.g. `"npm run typecheck → exit 0 with the deliberate error present"`).
- `refs` keys: `commit` 572, `eval` 20, `file` 12, `path` 1.

**There are no `messages`, no `role`, no `tool_calls`, no `tool_result` bodies, no prefix field, no
token/cache metadata, and no turn boundaries.** The unit's steps 2–6 (per-turn prefix reconstruction,
content-block classification, token-turn ledger over tool results, referenced-later heuristic,
top tool results, CF1–CF3 on tool results) are therefore **not computable**. Reported partial rather
than fabricating turn structure out of commit events.

Confirmed no substitute exists on disk: `grep -rl '"tool_result"|"role"|"tool_calls"'` over `*.jsonl`
matches only (a) synthetic experiment cells under `release/v0.1/experiments/context-cache/cells/*`
whose `messages` are *constructed* prompt payloads, and (b) prose mentions inside this ledger's own
`detail` text. No agent session transcript with real tool results is present.

## What IS measurable (analogue, labelled as such)
If the ledger were replayed as a growing context, the bill would be:

| quantity | chars | tokens @4.0 | tokens @2.11 |
|---|---|---|---|
| total record chars | 680,402 | 170,101 | 322,465 |
| **prefix chars summed over all records (token-turns)** | **180,551,180** | **45,137,795** | **85,569,280** |

Growth: turn 1 = 704 · 25% = 137,407 · 50% = 311,517 · 75% = 489,307 · 100% = 680,402 chars.
Mean 1,187.4 chars/record (median 683, σ 1,178); largest single jump 4,153 chars (seq 535).

By kind (share of ledger chars): `commit` 98.13% (527 records, mean 1,266.9) · `mistake` 0.54% ·
`decision` 0.43% · `fix` 0.34% · `measurement` 0.24% · `discovery` 0.17% · `eval.run` 0.15%.
So 98% of the mass is one class, and the 16 largest records are all at/near the 4,000-char cap.

Counterfactual **analogues** (same definitions, applied to ledger records instead of tool results):

| CF | assumption | token-turns | % of total |
|---|---|---|---|
| CF1 dedupe exact repeats | 34 of 50 duplicate-group records (16 groups) replaced by pointer | 176,956,040 | **1.99%** |
| CF2 body-out, >2 old → 120-char pointer | 120-char pointer `<seq> <kind> <size> <first line>` | 19,492,695 | **89.20%** |
| CF3 cap: keep newest 3 bodies, drop older | nothing kept for older records | 2,096 | **100.00%** |

CF2 keeps 19,490,599 token-turn chars (10.8% of base) that CF3 drops — and that residual is
*exactly the retrievable history*: the 68,400-char/turn pointer floor plus the newest 3 bodies.
The instruction that matters: **CF3's 100% is not a saving, it is the deletion of the history.**
On a monotonically appended log, "cap" looks ~9,300× cheaper than "body-out" (2,096 vs 19,492,695
token-turn chars) precisely because it stops being a context at all.

## What the trace cannot tell you
1. It is **not a run**. Zero turns, zero tool calls, zero tool results — nothing about an agent loop.
2. One artefact, one project (`duval` M0 window), one model family claimed only in prose.
3. No cache metadata (no `cached_tokens`), so prefix-cache hit rate is unknowable here.
4. No billing/price data, no TTFT/latency, no per-request token counts.
5. `detail` is the agent's *claim* about what happened, post-hoc and author-truncated at 4,000 chars;
   it is not what the agent read.
6. Retrieval relevance ("was result X needed later?") is undefined without message ordering.
7. The analogue above is a growth shape, not a measurement of tool-result waste; it must not be
   quoted as the latter.

## Blocker
No agent-run transcript with tool results exists in the pinned material or anywhere in the workspace.

## Next unit hint
Source a genuine transcript (a run dir containing message arrays with `role`/`tool_calls`/
`tool_result`, ideally with `cached_tokens` per request) before attempting TRACE-ANATOMY's steps 2–6.
Candidate acquisition routes: Duval's own harness run logs, an `opencode`/`dsh` session JSONL, or a
fresh instrumented run with cache metadata recorded. Everything else in the card is ready to run
unchanged once such a file is pinned.
