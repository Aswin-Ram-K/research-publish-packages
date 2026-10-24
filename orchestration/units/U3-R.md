# U3-R — prefix volatility (E1)

**Purpose (one).** Measure how much of the served prefix survives in the KV cache when the SAME
logical transcript is rendered three ways that differ only in WHERE volatile values (timestamps,
counters, run ids) live.

## Inputs (read-only)
- `experiments/context-cache/corpora/volatility.json` (4 scenarios x 48 turns, depths
  2/4/8/16/32/48, sha256 `6e2fe897…e2bc7db` — re-verified at run time, `plan.json.corpus_sha_match`)
- `experiments/context-cache/{client,runner,analyze}.py`, `src/resextract/context/{render,nodes,meter,salt}.py`
  — imported, never edited.

## Arms
| arm | policy | where volatile values live |
|---|---|---|
| `pointer` | `RenderPolicy.POINTER` | only in the final delta; history append-only |
| `naive_append` | `RenderPolicy.NAIVE_APPEND` | same; recipe control — byte-identical to `pointer` |
| `naive_mutable` | `RenderPolicy.NAIVE_MUTABLE` | interpolated into the mutable system/header block |

Volatile dict per turn (deterministic in scenario+turn+seed, never a clock): `ts`, `counter`,
`run_id`, `tool_calls` — all four change every turn.

Salt: `U3-R:e1:20261021:<scenario>` for `pointer` **and** `naive_append` (they are equal
information, so the control must be byte-identical); `…:naive_mutable` for the third arm.
Radix-crossing is prevented structurally: arms run as separate passes, every turn is a strict
prefix extension.

## Design (pre-registered)
| item | value |
|---|---|
| turns per scenario | 16 (depths 2/4/8/16 covered; 32/48 named as remainder) |
| scenarios | S1..S4 (all 4) |
| arms | 3 |
| request plan | 3 x 4 x 16 = **192** of 200 |
| max_tokens / thinking | 8 / `false` |
| cache | server-side prefix cache as configured (no flush requested — not ours to toggle) |

Deviation vs all six depths: 3 x 4 x 48 = 576 requests, 2.9x over the hard bound. Turn 16 is the
largest depth covering 4 of 6 registered depths inside 200. Depths 32 and 48 are the named remainder.

## Method
1. **Offline plan** (`--mode plan`) before any live call: build both chains turn by turn, assert
   `pointer` ≡ `naive_append` (0 first-diff, equal chars) and `naive_mutable` differs on every
   turn at a byte offset inside the header. Written to `cells/U3/plan.json`.
2. **Live**: strictly serial, one request in flight; `flock(LOCK_EX)` on `.occamy.lock` for the
   whole batch from before the first request to after the last; 600 s acquisition deadline.
3. Rows: arm, scenario, turn, prompt_tokens, cached_tokens, uncached, ts (+ ttft, wall, status,
   prompt sha256, chars) — one row per request, flushed every 8 turns.
4. **Retention** for an arm at turn t: `r(t) = cached(t)/cached_max(t)` where `cached_max` is the
   largest `cached_tokens` that arm reaches on that scenario. Cold turn 1 is 0 by construction and
   is excluded from the after-turn-2 kill test.

## Bound (hard)
<= 200 live requests (plan 192). Stop at 200 or all cells covered. **3 consecutive failures ->
STOP, report failed with the verbatim error.** Lock timeout 600 s -> partial.

## Kill condition (pre-registered; not redefined here)
If `naive_mutable` retains **> 50 %** of its cached tokens after turn 2, the volatility claim has
no support and must be reported **REFUTED**.

## Write paths (mine alone)
`experiments/context-cache/cells/U3/**`, `orchestration/handoffs/U3-R.json`,
`orchestration/units/U3-R.md`. Nothing else — `cells/E1/**` belongs to a different concurrent unit
(fork-break-cost) and is not touched.
