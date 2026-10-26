# UNIT LAZY-LOAD-CROSSOVER

**Objective.** Find where lazy instruction loading actually pays, or show that it never
does — extending the completed first arm into a cold/warm crossover sweep.

**Status: partial** (66 of 144 runs). Verdict from the measured cells: **CONDITIONAL** —
pays only with a cold prefix and a corpus ≥ ~30,000 chars at 17 % needed; never pays
against a warm prefix in the swept range.

## Design

| axis | values |
|---|---|
| corpus size | 3,000 / 10,000 / 30,000 chars, exact, seed 20261024 |
| needed fraction | 2 of 12 (17 %) / 6 of 30 (20 %) |
| arms | C0 full-inline / L1 index + text-emulated `FETCH <id>` |
| cache state | cold (per-request nonce) / warm (identical request sent twice, 2nd recorded) |
| models | occamy-1.0 `:8012`, qwen3.5-9b `:8014` (LAN `192.168.2.168`) |
| reps | 3 |
| protocol | text-emulated on **both** models, removing the first arm's confound |

No `/flush_cache`, no server restart. Every row records its nonce and
`cached_tokens / prompt_tokens` so the regime is proved, not assumed.

## Result

- Cold crossover at **30,000 chars / 12 items**: billed +44.8 %, 6,492 → 3,582 uncached
  tokens (−45 %). At 10,000 chars a wash (−2.5 %); at 3,000 chars a large loss (−107 %).
- Warm: **no crossover in range**; L1 loses in all four measured warm cells (+77 to
  +570 uncached tokens).
- Realised saving is negative everywhere (−288 % to −910 %) because L1 re-sends its index
  every round trip.
- Correctness: C0 30/30 reps, L1 28/30; every L1 failure was an early `ANSWER`, never a
  wrong number. Fetches were exactly the needed items — zero wasted fetches.
- Regime proof: occamy 0.0 % cold, 99.1 % / 93.9 % warm. **qwen returns
  `prompt_tokens_details: null` on every call** — its cache regime is unprovable, not
  cold.

## Unmeasured

qwen 12/10,000 (1 of 6), qwen 12/30,000, all qwen 30-item cells; occamy 30/10,000
(5 of 6) and 30/30,000. Resume: `python3 run_cx.py --resume --tag _occamy` / `--tag _qwen`.

## Bound and write paths

Bound 70 tool calls. Write paths: `experiments/agentic-lazy/crossover/**`,
`orchestration/units/LAZY-LOAD-CROSSOVER.md`,
`orchestration/handoffs/LAZY-LOAD-CROSSOVER.json`. The first arm's files were read only.

## Assumptions

1. `:8012`/`:8014` mean `192.168.2.168:8012`/`:8014` (no localhost listener).
2. `max_tokens` 1024 (first arm 2048) to bound batch time; 4× the 269 tokens observed.
3. `MAX_ROUNDS` 20 (6-fact emulated needs ~8).
4. qwen billed column assumes 0 cached because the server reports nothing.
5. `fetched_body_tokens` = `fetched_body_chars × chars_per_token`, ratio measured on the
   same model's C0 request for the same corpus.
6. A duplicate unit (`LAZY-LOAD-CROSSOVER-2`) shared these write paths; my runs were
   isolated behind `--tag _occamy` / `--tag _qwen` and the canonical files published
   from those.
