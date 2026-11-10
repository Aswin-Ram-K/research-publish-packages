# U-SPCC-57 — record the final E1 cell

**Status:** DONE. Record-only unit: 0 endpoint requests, 0 model calls.

## What was recorded

`experiments/ptr-engine/measure/rows-e1-indexfix-2026-11-10.jsonl`, commit `2e22310`, 343
requests, 0 failed, 0 truncated, reconciliation delta 0. Programme spend 9,367 of 12,094;
headroom 2,727.

| arm | value | contract | NONE | wrong | unparsed | requests | billed |
|---|---:|---:|---:|---:|---:|---:|---:|
| `spcc` | 20 | 19 | 27 | 1 | 0 | 100 | 17,187 |
| `masking-no-fetch` | 8 | 8 | 30 | **10** | 0 | 100 | 18,724 |
| `bounded-context-fetch` | **48** | **48** | 0 | 0 | 0 | 143 | 51,715 |

Buckets sum to 48 on all three arms.

## The finding

The fetch arm's 48/48 is a **lookup score, not a retention score**. 41 of its 48 checkpoints
were answered by fetching the fact body **in the same turn the question was asked** — the
initial response carries the question, emits the fetch, and the follow-up answers from the
body. Prefetch (fetching before delivery) is **0**, so the specific prefetch concern did not
trigger; the model simply never retains anything. Only **7** checkpoints are genuine
retention successes (`f01.d2`, `f03.d2`, `f01.d32`, `f03.d20`, `f05.d2`, `f07.d2`, `f07.d8`).

Therefore **`spcc`-vs-fetch is not a retention comparison** and must not be reported as one.
The correct statement is: when lookup is available on the question turn, retention is
unnecessary; the fetch arm answers everything and costs **3.0× `spcc`'s billed tokens**
(51,715 vs 17,187).

## Five secondary findings

1. **`NOT_FOUND` collapsed 12 → 0.** Every fetch attempt used an advertised
   `doc-fact-NN@r1`. The index fix (`b38db8a`) reached the model.
2. **The masking arm's wrong answers went 0 → 10** (turns 6, 7, 9, 13, 14, 22, 23, 25, 29,
   30) while its value score stayed 8. The index now advertises 13 refs where it previously
   advertised 1, so the masking arm sees fact names it cannot fetch and confabulates values
   instead of answering `NONE`. **Advertising addressable refs to an arm that cannot address
   them converts abstention into confabulation.**
3. **The multi-round loop is dead code in practice.** `max(fetch_rounds_this_turn) == 1`
   because the model batches all calls into one response. Multi-REF servicing does work
   (`fetch_rows` reaches 3 at turn 21, 2 at turn 28). `cp.TX-03.f04.d8` (turn 32) is now
   serviced and correct (`NUM 3303`).
4. **Billed rose on every arm** because the index is 13 lines instead of 1: `spcc` +15.9 %,
   masking +33.7 %, fetch +26.2 %. A prompt-size effect, not a treatment effect.
5. **The index fix changed the prompt bytes for all three arms**, so no cell before
   `b38db8a` is comparable to this one. The `spcc` 21 and fetch 17 from `c73dfc4` are
   superseded, not replicated.

## The verdicts

- `spcc` > masking aggregate: **survives** — 20 vs 8, +12, outside the band.
- `billed ≤ masking`: **FALSIFIED** — `spcc` 17,187 vs masking 18,724 is now *below*, but the
  direction flipped between cells (+2,868, +820, −1,537), so the billing comparison is
  **unstable** and no direction is established.
- `spcc` ≥ fetch: **falsified on the number, void as a retention claim** — fetch 48 vs `spcc`
  20, but by lookup.
- Falsifier: fired in the earlier cells on billing; in this cell `spcc` bills *less* than
  masking, so it does not fire here. Record the instability rather than picking a cell.

## Writes

`experiments/ptr-engine/research-seed-concepts/FINDINGS-LEDGER.md` (one 7-column row; column
count 19→20 rows at 7 columns, unchanged), `docs/STATE.md`, `journal/2026-11-10.md`,
`orchestration/STATUS.md`, `orchestration/units/U-SPCC-57.md`,
`orchestration/handoffs/U-SPCC-57.json`. `PREREG-SPCC.md` and its companion JSON untouched.
