# R-CROSS — cross-stack cache-reuse landscape (literature only)

**Status:** in progress (card written first per unit contract)
**Purpose (one):** Web research the cross-stack landscape of systems/techniques claiming to beat
plain prefix caching, independent of engine. Goal: which claims are credible enough to reproduce,
which need hardware we lack, and which would falsify our current conclusions. **Zero experiments.**
**Parent:** `session-b61634cb-606d-4220-9b7e-eeb2b9a9e2a7`

## Hard constraints (from card)
- **0 experiments, 0 requests to the Occamy server, no `.occamy.lock`, no connection.** Offline only.
- No writes outside: `orchestration/units/R-CROSS.md`, `docs/serving-options/R-CROSS.md`,
  `orchestration/handoffs/R-CROSS.json`.
- Bound: **max 40 tool calls**; parallel search bursts; `local_web_search` first, `local_web_crawl` on
  primary sources (arXiv, proceedings, repos, engineering blogs).
- Automated session: never ask the user; missing value -> conservative default recorded in `assumptions`.
- Touch nothing else in `docs/`.

## Baseline under characterisation (fixed, not to be changed)
One SGLang deployment, Qwen3.5-MoE hybrid attention, plain radix cache, no hierarchical cache, no
LMCache, `chunked_prefill_size=8192`. Measured: cache hits land on a **64-token grid**; a mid-context
edit breaks the cache **from the edit point onward** and lands within one 64-block; the stack has **no
suffix-recovery mechanism**. All of our measurements are **exact-prefix**.

## Method
Search bursts -> primary-source crawls -> per-method record with: name, venue/year, primary URL,
one-sentence mechanism, strongest measured claim (number + workload), **exactness**
(byte-exact vs approximate — decisive for us), feasibility on a single GB10-class node with a
hybrid-attention MoE (`yes` / `needs-cluster` / `needs-training` / `approximate-only`), and what it
would falsify. Deliverable: `docs/serving-options/R-CROSS.md` — method table, then the three claims
most likely to falsify our results + the cheapest experiment for each.

## Tool-call ledger (final: 35 / 40)
| # | call | outcome |
|---|------|---------|
| 1–3 | read `AGENTS.md`, ls workspace/docs/units, read `orchestration/units/R-SGL.md` | contract read; `docs/serving-options/` empty; sibling R-SGL = SGLang-native only, no overlap |
| 4 | write this card | done |
| 5–35 | 13 `local_web_search` bursts, 6 crawls/scrapes (arXiv abs ×4, DigitalOcean blog ×2, USENIX ×1 404), 2 failed `web_search` (no `DEEPSEEK_API_KEY`) | all nine requested items covered; 4 rows left `unverified` on purpose |
| 36–37 | correct budget line in the note; this ledger | done |
| 38–40 | write handoff, validate JSON, report to parent | done |

**Result:** `status = done` (with 4 explicitly `unverified` provenance rows). Deliverable:
`docs/serving-options/R-CROSS.md`. **0 requests to Occamy, no lock, 0 experiments.**
