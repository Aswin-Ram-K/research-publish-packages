# RESULTS-FETCH-INSTRUCTED — instructed fetch policy on TX-AGG and TX-HOP

## Run identity

| Fixture | Run id | Rows file | Turns |
|---|---|---|---|
| TX-AGG | agg3-instructed | `experiments/ptr-engine/measure/rows-agg3-instructed.jsonl` | 100 turns, 48 checkpoints |
| TX-HOP | hop3-instructed | `experiments/ptr-engine/measure/rows-hop3-instructed.jsonl` | 180 turns, 48 checkpoints |

Both runs: `--temperature 0 --seed 42 --tools fetch --fetch-policy instructed --claim-mode smoke`,
model `occamy-1.0`, endpoint `http://192.168.2.168:8012/v1`, arm `bounded-context-fetch`, rep 1.

## Row-1 gate

| Field | AGG | HOP |
|---|---|---|
| task_id | TX-AGG | TX-HOP |
| fixture_sha256 | 178042c254f7b732f57603985de35adf8e3722f80507219103c0f7b259e81b03 | 860aad568c97d227a756111c359df19bdd2412e8db44f52644e8b23e2962fca0 |
| temperature | 0 | 0 |
| seed | 42 | 42 |
| tools_mode | on:fetch | on:fetch |
| fetch_policy | instructed | instructed |

Gate: **PASS** on both.

## Activation gate

| Fixture | Policy | Fetching turns (turns with `fetch_rows>0`) | Floor 40 | Status |
|---|---|---:|---:|---|
| TX-AGG | instructed | 22 | 40 | **FAIL (shortfall 18)** |
| TX-HOP | instructed | 17 | 40 | **FAIL (shortfall 23)** |

Neither instructed run reaches the 40-turn activation floor, so neither counts as a retrieval result
under the preregistered gate. They are reported but not scored as retrieval.

Strict baseline for reference (already on disk): AGG 29 fetching turns, HOP 28 fetching turns.

## Comparison table

| Fixture | Policy | Fetching turns | Total fetch calls | Contract /48 | Value /48 | d=2 | d=6 | d=20 | d=32 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| TX-AGG | strict | 29 | 82 | 4 | 4 | 0 | 0 | 1 | 3 |
| TX-AGG | instructed | 22 | 49 | 1 | 1 | 0 | 0 | 0 | 1 |
| TX-HOP | strict | 28 | 30 | 9 | 9 | 9 | 0 | 0 | 0 |
| TX-HOP | instructed | 17 | 18 | 5 | 5 | 3 | 2 | 0 | 0 |

Per-bucket counts are contract-level (== value-level here) correct checkpoints out of 12.

## Retrieval outcomes

- AGG instructed: 47 OK, 1 STALE_OR_REVOKED, 1 NOT_FOUND (49 fetches).
- HOP instructed: 16 OK, 2 NOT_FOUND (18 fetches).

## Over-fetching analysis

Fetches per checkpoint (`fetch_rows` on the turn row):

- AGG instructed: distribution {1: 4 turns, 2: 13, 3: 1, 4: 4}; turns with ≥3 fetches: T30, T36, T68, T77, T87.
- HOP instructed: distribution {1: 16 turns, 2: 1 turn}; no turn made ≥3 fetches.

Displacement check (d=2 buckets, where masking scores 11–12 of 12):

- AGG instructed d=2: 0/12 correct; only one of those checkpoints (T50) actually fetched (1 fetch) and returned a wrong value (51589 vs expected 234704). The remaining 11 d=2 misses did not fetch, so the regression is not attributable to fetch displacement; the instructed arm simply failed to answer correctly at d=2.
- HOP instructed d=2: 3/12 correct vs masking 12/12. No instructed checkpoint at d=2 made a fetch, so the drop is not caused by over-fetching; the policy did not improve (and slightly hurt) accuracy.

## Is the instructed policy worth adopting?

**No for these task kinds.** The instructed policy did not lift engagement (22 and 17 fetching turns vs strict 29 and 28, both below the 40-turn floor) and did not improve accuracy (AGG 1/48 vs 4/48; HOP 5/48 vs 9/48). Over-fetching is modest (only 5 AGG turns made ≥3 fetches, none on HOP) and does not explain the accuracy drop, but the policy also produced no benefit. Recommendation: keep `strict` as default; do not adopt `instructed` for TX-AGG/TX-HOP-style tasks without a redesigned policy that actually increases fetch engagement.

## Budget arithmetic

- Cap: 12,094 requests.
- Observed spent before this unit (rows on disk in `experiments/ptr-engine/measure/rows-*.jsonl`): 6,528
  (contract-stated figure was 6,577; observed ledger count is 6,528).
- This unit added: AGG 122 rows + HOP 197 rows = 319 requests.
- Observed spent after this unit: 6,847.
- Remaining headroom: 5,247.

## Limitations

- Single replication (rep 1) per fixture; no second replication run (per task constraints).
- Masking arm was not re-run; masking d=2 accuracy (11–12/12) is taken from the prior masking runs already on disk.
- Claim mode `smoke` (no hypothesis claim); rows are not comparison-eligible.
- The instructed prompt variant is the only change; model, temperature, seed, tools, and fixtures are identical to the strict runs.
