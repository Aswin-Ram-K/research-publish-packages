# UNIT LAZY-LOAD-CROSSOVER-2

**Status:** see `orchestration/handoffs/LAZY-LOAD-CROSSOVER.json` (authoritative).
**Bound:** 40 tool calls. **Mode:** automated — no human present, never ask, never wait.
**Supersedes:** `LAZY-LOAD-CROSSOVER` (swept mid-build; its corpus builder and harness are reused, not rebuilt).

## Purpose (one purpose per unit)

Locate the corpus-size crossover between two answer strategies: **C0** (every item body
inlined in the prompt) and **L1** (compact index + a text-emulated `FETCH <id>` tool that
pulls bodies on demand). The decision variable is **billed tokens**, `prompt − cached`,
not prompt tokens: the first arm established that lazy loading trades prompt tokens for
cache hits, so under a warm prefix the smaller L1 prompt can still cost more.

## Design

| Axis | Values |
|---|---|
| Corpus size (body characters, exact) | **3,000**, **30,000** |
| Needed fraction | **2-of-12** at both sizes; **6-of-30** at 30k only |
| Arms | `c0` (all bodies inlined), `l1` (projection + one fetch tool) |
| Cache state | `cold` (fresh nonce per request — salt isolation), `warm` (steady prefix, no nonce; round 1 primes, round 2 is the measured response) |
| Models | `occamy-1.0` @ `:8012/v1`, `qwen3.5-9b` @ `:8014/v1` |
| Reps | **1** — a crossover *location* run, not a significance test |
| Protocol | **text-emulated** `FETCH <id>` / `ANSWER` on **both** models, so the cross-model comparison is clean; `protocol=text_emulated` recorded per row |

Neither server is restarted and `/flush_cache` is never called; cold isolation is by
per-request nonce only, and `cached_tokens / prompt_tokens` proves the regime rather than
asserting it.

## Kill-resistance (the reason this unit exists)

Two mechanisms, both required by the card:

1. `run_cx.py` keeps `rows.jsonl` open in **append** mode and calls `flush()` + `fsync()`
   after **every request** (`_ROWS_FH`, `emit()`). A kill loses at most the in-flight request.
2. `runs.json` is rewritten atomically (`tmp` + `os.replace`) after every completed run.
3. `orchestration/handoffs/LAZY-LOAD-CROSSOVER.json` is written `partial` **before** the
   first measurement and updated **after every completed cell**.

## Deliverables

- `experiments/agentic-lazy/crossover/RESULTS.md` — per-cell table, `saving_billed`,
  `saving_prompt`, the crossover point, one-sentence verdict.
- `experiments/agentic-lazy/crossover/{rows.jsonl,runs.json,run_cx.log}` — evidence.
- `orchestration/handoffs/LAZY-LOAD-CROSSOVER.json` — partial first, then final.

## Write paths

`experiments/agentic-lazy/crossover/**`, `orchestration/units/LAZY-LOAD-CROSSOVER-2.md`,
`orchestration/handoffs/LAZY-LOAD-CROSSOVER.json`. Nothing else is touched.

## Stop condition

If a model server is unreachable: ship the harness plus the `--dry-run` proof, and report
`partial` naming exactly which cells are unmeasured. Do not tune corpus, task or reps to
manufacture a positive result, and do not drop a bad cell.
