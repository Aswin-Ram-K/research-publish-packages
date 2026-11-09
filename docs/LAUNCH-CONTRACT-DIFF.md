# LAUNCH-CONTRACT-DIFF — every number the launch depends on, side by side

**Unit:** `LAUNCH-CONTRACT-DIFF` · **Offline:** 0 requests, 0 network events, 0 live cells.
**Machine-readable twin:** [`measure/LAUNCH-CONTRACT-DIFF.json`](../measure/LAUNCH-CONTRACT-DIFF.json) (one entry per number).
**Guard:** `python3 experiments/ptr-engine/tools/launch_contract_diff.py --check` — exit **1** on any DISAGREES/UNRESOLVED, **0** when the contract is single-valued.

A launcher reads *values*, not files. This page puts every value the 1,016-request launch
depends on beside every other place it is written down, and names the one that wins.
Nothing here reconciles a disagreement: the sources are untouched and each conflict is reported.

## 1. Verdict counts

| status | numbers |
|---|---|
| **AGREES** | 15 |
| **STALE-BY-DESIGN** | 4 |
| **DISAGREES** | 3 |
| **ABSENT** | 0 |
| **total** | **22** |

`--check` on this tree exits **1** (disagreements: `harness_pin_digest`, `per_cell_budget`, `per_arm_round_cap`).

## 2. The table

| # | number | value a launcher must use | status | every place it appears (`path:line = value`) |
|---|---|---|---|---|
| 1 | harness pin digest (--expect-harness) | `fa6fd8cc519f5a2794b54fe5f215c808f781b136de657bdece7f5eb4bf37e8ac` | **DISAGREES** | `experiments/ptr-engine/measure/HARNESS-PIN.json:-` = `fa6fd8cc519f5a2794b54fe5f215c808f781b136de657bdece7f5eb4bf37e8ac`<br>`experiments/ptr-engine/tools/run_a_star.py:51` = `fa6fd8cc519f5a2794b54fe5f215c808f781b136de657bdece7f5eb4bf37e8ac`<br>`<computed:pin digest over recorded per-file hashes>:-` = `fa6fd8cc519f5a2794b54fe5f215c808f781b136de657bdece7f5eb4bf37e8ac`<br>`<computed:pin digest over bytes on disk now>:-` = `fa6fd8cc519f5a2794b54fe5f215c808f781b136de657bdece7f5eb4bf37e8ac`<br>`docs/GRID-RUNBOOK.md:68` = `fa6fd8cc519f5a2794b54fe5f215c808f781b136de657bdece7f5eb4bf37e8ac`<br>`docs/GRID-RUNBOOK.md:119` = `fa6fd8cc519f5a2794b54fe5f215c808f781b136de657bdece7f5eb4bf37e8ac`<br>`docs/GRID-RUNBOOK.md:86` = `2b4d4808cf906582a378c47c340113022588284fc2b58640e83a95fc6bc23871` **(stale-by-design)**<br>`experiments/ptr-engine/measure/GRID-PARAMS.json:-` = `2b4d4808cf906582a378c47c340113022588284fc2b58640e83a95fc6bc23871` |
| 2 | fixture sha256 (LR-01.v8.json) | `0804b51575cce3454a1c628a9a2447a01856321e67ac3fd1ff8c9baa48467641` | **AGREES** | `experiments/ptr-engine/measure/HARNESS-PIN.json:-` = `0804b51575cce3454a1c628a9a2447a01856321e67ac3fd1ff8c9baa48467641`<br>`<computed:fixture bytes on disk>:-` = `0804b51575cce3454a1c628a9a2447a01856321e67ac3fd1ff8c9baa48467641`<br>`docs/GRID-RUNBOOK.md:33` = `0804b51575cce3454a1c628a9a2447a01856321e67ac3fd1ff8c9baa48467641`<br>`docs/GRID-RUNBOOK.md:75` = `0804b51575cce3454a1c628a9a2447a01856321e67ac3fd1ff8c9baa48467641` |
| 3 | launch price (total) | `1016` | **AGREES** | `experiments/ptr-engine/measure/GRID-PARAMS.json:-` = `1016`<br>`<computed:tranche + canary + warm-ups>:-` = `1016`<br>`docs/GRID-PARAMS.md:56` = `1016`<br>`docs/GRID-RUNBOOK.md:3` = `1016`<br>`docs/GRID-RUNBOOK.md:71` = `1016` |
| 4 | tranche price (turns + rounds + digests) | `964` | **STALE-BY-DESIGN** | `experiments/ptr-engine/measure/GRID-PARAMS.json:-` = `964`<br>`docs/GRID-PARAMS.md:43` = `964`<br>`experiments/ptr-engine/measure/GRID-SHAPE.json:-` = `724` **(stale-by-design)** |
| 5 | headroom after the launch price | `2176` | **STALE-BY-DESIGN** | `experiments/ptr-engine/measure/GRID-PARAMS.json:-` = `2176`<br>`docs/GRID-PARAMS.md:58` = `2176`<br>`docs/GRID-RUNBOOK.md:71` = `2176`<br>`experiments/ptr-engine/measure/GRID-SHAPE.json:-` = `2468` **(stale-by-design)**<br>`docs/GRID-PARAMS.md:46` = `2228` **(stale-by-design)** |
| 6 | per-cell --budget | `108` | **DISAGREES** | `experiments/ptr-engine/measure/GRID-PARAMS.json:-` = `108`<br>`experiments/ptr-engine/tools/run_a_star.py:241` = `108`<br>`experiments/ptr-engine/tools/run_a_star.py:366` = `108`<br>`experiments/ptr-engine/tools/run_a_star.py:367` = `67`<br>`docs/GRID-PARAMS.md:125` = `108`<br>`experiments/ptr-engine/measure/GRID-SHAPE.json:-` = `67` **(stale-by-design)** |
| 7 | --fetch-followup-allowance (G1 reserve) | `48` | **STALE-BY-DESIGN** | `experiments/ptr-engine/measure/GRID-PARAMS.json:-` = `48`<br>`experiments/ptr-engine/tools/run_a_star.py:44` = `48`<br>`experiments/ptr-engine/measure/GRID-SHAPE.json:-` = `24` **(stale-by-design)**<br>`experiments/ptr-engine/measure/GRID-SHAPE.json:-` = `24` **(stale-by-design)** |
| 8 | per-arm fetch-round cap | `48` | **DISAGREES** | `experiments/ptr-engine/longrun/run_longrun.py:230` = `48`<br>`experiments/ptr-engine/longrun/run_longrun.py:2857` = `ap.add_argument("--fetch-rounds-per-arm", type=int, default=TOOL_FETCH_ROUNDS_PER_ARM` **(evidence)**<br>`experiments/ptr-engine/measure/GRID-PARAMS.json:-` = `48`<br>`experiments/ptr-engine/measure/GRID-SHAPE.json:-` = `24` **(stale-by-design)**<br>`docs/GRID-SHAPE.md:86` = `24` **(stale-by-design)**<br>`docs/GRID-PARAMS.md:90` = `24` |
| 9 | per-turn fetch-round cap | `3` | **AGREES** | `experiments/ptr-engine/longrun/run_longrun.py:236` = `3`<br>`experiments/ptr-engine/measure/GRID-PARAMS.json:-` = `3` |
| 10 | canary arms | `4` | **AGREES** | `<computed:CANARY_ARMS tuple length>:-` = `4`<br>`docs/GRID-RUNBOOK.md:123` = `4` |
| 11 | canary turns per arm | `12` | **AGREES** | `experiments/ptr-engine/tools/run_a_star.py:387` = `12`<br>`experiments/ptr-engine/measure/GRID-PARAMS.json:-` = `12`<br>`docs/GRID-RUNBOOK.md:123` = `12` |
| 12 | canary requests | `48` | **AGREES** | `experiments/ptr-engine/measure/GRID-PARAMS.json:-` = `48`<br>`<computed:arms x turns>:-` = `48`<br>`experiments/ptr-engine/measure/GRID-PARAMS.json:-` = `48` |
| 13 | canary --max-wall | `900` | **AGREES** | `experiments/ptr-engine/tools/run_a_star.py:214` = `900` |
| 14 | canary --hypothesis | `smoke` | **AGREES** | `experiments/ptr-engine/tools/run_a_star.py:385` = `smoke` |
| 15 | grid cells | `10` | **AGREES** | `experiments/ptr-engine/measure/GRID-SHAPE.json:-` = `10`<br>`docs/GRID-RUNBOOK.md:3` = `10` |
| 16 | grid total turn rows | `480` | **AGREES** | `experiments/ptr-engine/measure/GRID-SHAPE.json:-` = `480`<br>`experiments/ptr-engine/measure/GRID-PARAMS.json:-` = `480` |
| 17 | grid per-cell --max-wall | `2880` | **AGREES** | `experiments/ptr-engine/tools/run_a_star.py:400` = `2880`<br>`experiments/ptr-engine/measure/GRID-SHAPE.json:-` = `2880` |
| 18 | grid --hypothesis | `H2` | **AGREES** | `experiments/ptr-engine/tools/run_a_star.py:399` = `H2`<br>`experiments/ptr-engine/measure/GRID-SHAPE.json:-` = `H2` |
| 19 | ledger spent | `1128` | **STALE-BY-DESIGN** | `experiments/ptr-engine/measure/REQUEST-LEDGER.json:-` = `1128`<br>`experiments/ptr-engine/measure/LEDGER-GRID-BASELINE-2.json:-` = `1128`<br>`experiments/ptr-engine/measure/LEDGER-GRID-BASELINE-2.json:-` = `1101` **(stale-by-design)** |
| 20 | ledger remaining | `3192` | **AGREES** | `experiments/ptr-engine/measure/REQUEST-LEDGER.json:-` = `3192`<br>`experiments/ptr-engine/measure/LEDGER-GRID-BASELINE-2.json:-` = `3192`<br>`experiments/ptr-engine/measure/GRID-PARAMS.json:-` = `3192` |
| 21 | ledger cap | `4320` | **AGREES** | `experiments/ptr-engine/measure/REQUEST-LEDGER.json:-` = `4320`<br>`experiments/ptr-engine/measure/LEDGER-GRID-BASELINE-2.json:-` = `4320`<br>`experiments/ptr-engine/longrun/cell.py:139` = `4320` |
| 22 | n>=60 order-statistic floor for p95 | `60` | **AGREES** | `<computed:min_n_for(0.95) from TAIL_MIN=3, MIN_N=20>:-` = `60`<br>`docs/GRID-RUNBOOK.md:310` = `60`<br>`docs/GRID-RUNBOOK.md:341` = `60`<br>`docs/GATE-CHAIN.md:292` = `60` |

Values that are stale are shown in the occurrence cell as *stale-by-design*; a broken
quote is marked *broken* and is itself a finding (the line moved out from under the number).

## 3. DISAGREES — which value wins, and why

### `harness_pin_digest` — harness pin digest (--expect-harness)

Competing values: `fa6fd8cc519f5a2794b54fe5f215c808f781b136de657bdece7f5eb4bf37e8ac` vs `2b4d4808cf906582a378c47c340113022588284fc2b58640e83a95fc6bc23871`

| occurrence | value | role |
|---|---|---|
| `experiments/ptr-engine/measure/HARNESS-PIN.json:-` | `fa6fd8cc519f5a2794b54fe5f215c808f781b136de657bdece7f5eb4bf37e8ac` | load-bearing |
| `experiments/ptr-engine/tools/run_a_star.py:51` | `fa6fd8cc519f5a2794b54fe5f215c808f781b136de657bdece7f5eb4bf37e8ac` | load-bearing |
| `<computed:pin digest over recorded per-file hashes>:-` | `fa6fd8cc519f5a2794b54fe5f215c808f781b136de657bdece7f5eb4bf37e8ac` | load-bearing |
| `<computed:pin digest over bytes on disk now>:-` | `fa6fd8cc519f5a2794b54fe5f215c808f781b136de657bdece7f5eb4bf37e8ac` | load-bearing |
| `docs/GRID-RUNBOOK.md:68` | `fa6fd8cc519f5a2794b54fe5f215c808f781b136de657bdece7f5eb4bf37e8ac` | load-bearing |
| `docs/GRID-RUNBOOK.md:119` | `fa6fd8cc519f5a2794b54fe5f215c808f781b136de657bdece7f5eb4bf37e8ac` | load-bearing |
| `docs/GRID-RUNBOOK.md:86` | `2b4d4808cf906582a378c47c340113022588284fc2b58640e83a95fc6bc23871` | stale-by-design |
| `experiments/ptr-engine/measure/GRID-PARAMS.json:-` | `2b4d4808cf906582a378c47c340113022588284fc2b58640e83a95fc6bc23871` | load-bearing |

**Authoritative:** HARNESS-PIN.json:9 (generation 4) + run_a_star.py:51 (the digest the launcher passes) + recomputation over bytes

**Resolution:** fa6fd8cc519f5a2794b54fe5f215c808f781b136de657bdece7f5eb4bf37e8ac. run_a_star.py:64 refuses any pin record whose generation is not 4 or whose digest differs, so the launcher cannot pass 2b4d4808; cell.py aborts at stage 2/7 with Abort(2, '2/7 harness'). GRID-PARAMS.json:158-164 is 18 minutes older and its own supersedes block does not name the newer pin.

**Owner of the stale copy (not edited by this card):** experiments/ptr-engine/measure/GRID-PARAMS.json (regenerate, never hand-edit): needs a card owning the pin bump

### `per_cell_budget` — per-cell --budget

Competing values: `108` vs `67`

| occurrence | value | role |
|---|---|---|
| `experiments/ptr-engine/measure/GRID-PARAMS.json:-` | `108` | load-bearing |
| `experiments/ptr-engine/tools/run_a_star.py:241` | `108` | load-bearing |
| `experiments/ptr-engine/tools/run_a_star.py:366` | `108` | load-bearing |
| `experiments/ptr-engine/tools/run_a_star.py:367` | `67` | load-bearing |
| `docs/GRID-PARAMS.md:125` | `108` | load-bearing |
| `experiments/ptr-engine/measure/GRID-SHAPE.json:-` | `67` | stale-by-design |

**Authoritative:** run_a_star.py:241 (the argv the launcher actually execs) and GRID-PARAMS.json:188

**Resolution:** 108. The launcher hard-codes '--budget 108' into every cell argv; the help string at run_a_star.py:367 still says '(default 67)' with no supersedes pointer, and GRID-SHAPE.json's 67 is superseded by GRID-PARAMS.json:274-277. Measured gate: ceil(48 x 1.10) = 53 <= both, so 67 would not refuse either — the value is not load-bearing for refusal, only for the record.

**Owner of the stale copy (not edited by this card):** experiments/ptr-engine/tools/run_a_star.py (help string) — needs a card owning the launcher

### `per_arm_round_cap` — per-arm fetch-round cap

Competing values: `48` vs `24`

| occurrence | value | role |
|---|---|---|
| `experiments/ptr-engine/longrun/run_longrun.py:230` | `48` | load-bearing |
| `experiments/ptr-engine/longrun/run_longrun.py:2857` | `ap.add_argument("--fetch-rounds-per-arm", type=int, default=TOOL_FETCH_ROUNDS_PER_ARM` | evidence |
| `experiments/ptr-engine/measure/GRID-PARAMS.json:-` | `48` | load-bearing |
| `experiments/ptr-engine/measure/GRID-SHAPE.json:-` | `24` | stale-by-design |
| `docs/GRID-SHAPE.md:86` | `24` | stale-by-design |
| `docs/GRID-PARAMS.md:90` | `24` | load-bearing |

**Authoritative:** run_longrun.py TOOL_FETCH_ROUNDS_PER_ARM = 48 (line located by grep) with --fetch-rounds-per-arm

**Resolution:** 48, overridable. GRID-PARAMS.json:174-181 records the RUNNER-ROUNDS-48 move; docs/GRID-PARAMS.md:90 still asserts 'a module constant with no override' and cites the pre-move line 226 — an undated stale claim in the human doc.

**Owner of the stale copy (not edited by this card):** docs/GRID-PARAMS.md §4 (stale) + docs/GRID-SHAPE.md — needs a doc-sync card

## 4. STALE-BY-DESIGN — an old value kept on purpose

These are not defects: the superseding artefact names the old value, so the pair is
readable and a launcher must use the **live** value in column 3 above.

- **`price_tranche`** — live `964`; preserved old: `724` at `experiments/ptr-engine/measure/GRID-SHAPE.json:-`. Pointer: “price.components.tranche = 964”
- **`price_remaining_after`** — live `2176`; preserved old: `2468` at `experiments/ptr-engine/measure/GRID-SHAPE.json:-`, `2228` at `docs/GRID-PARAMS.md:46`. Pointer: “price.remaining_after = 2,176”; “superseded as the launch remainder by”
- **`fetch_allowance`** — live `48`; preserved old: `24` at `experiments/ptr-engine/measure/GRID-SHAPE.json:-`, `24` at `experiments/ptr-engine/measure/GRID-SHAPE.json:-`. Pointer: “fetch_followup_allowance.value = 48”
- **`ledger_spent`** — live `1128`; preserved old: `1101` at `experiments/ptr-engine/measure/LEDGER-GRID-BASELINE-2.json:-`. Pointer: “v1 (LEDGER-GRID-BASELINE.json) is a dated record”

## 5. ABSENT — a source that should carry the number and does not

- **`fixture_sha256`** (`0804b51575cce3454a1c628a9a2447a01856321e67ac3fd1ff8c9baa48467641`): experiments/ptr-engine/measure/GRID-SHAPE.json:15-16 (names cell.py as the checker, carries no value)
- **`canary_arms`** (`4`): GRID-PARAMS.json :: canary (carries N only, no arm count)
- **`canary_requests`** (`48`): GRID-PARAMS.json :: canary (the priced component lives under price.canary, not canary)
- **`canary_max_wall`** (`900`): GRID-PARAMS.json :: canary (no wall); docs/GRID-RUNBOOK.md §1b (argues 720/600 but never names 900)
- **`canary_hypothesis`** (`smoke`): GRID-PARAMS.json :: canary.verdict_rule (names the gate, not the claim)

## 6. The guard, proved in both directions

A `/tmp` copy of the tree (all 17 sources, so the pin is recomputed from real bytes) is
mutated and re-checked. Quoted from the run:

```
$ python3 tools/launch_contract_diff.py --check --root /tmp/lcd-proof/tree   # shipped values
exit 1        # the three recorded disagreements

$ # reconcile GRID-PARAMS' pin, the launcher help string, and the doc's 24 -> 48
$ python3 tools/launch_contract_diff.py --check --root /tmp/lcd-proof/tree
exit 0        # 22 numbers: AGREES=15, STALE-BY-DESIGN=7

$ # now mutate ONE number back: GRID-PARAMS harness_pin.harness_sha256 := 2b4d4808...
$ python3 tools/launch_contract_diff.py --check --root /tmp/lcd-proof/tree
exit 1        # DISAGREES       harness_pin_digest fa6fd8cc519f5a2794b54fe5f215c808f781b136de657bdece7f5eb4bf37e8ac | 2b4d4808cf906582a378c47c340113022588284fc2b58640e83a95fc6bc23871
```

The same two directions are pinned as tests (`tests/test_launch_contract_diff.py`):
`test_check_mode_zero_on_single_valued_tree` and `test_check_mode_one_on_disagreement`.

## 7. The contract in one block

```
--expect-harness  fa6fd8cc519f5a2794b54fe5f215c808f781b136de657bdece7f5eb4bf37e8ac   (HARNESS-PIN.json generation 4; what run_a_star passes)
--turns           48 grid / 12 canary
--max-wall        2880 grid / 900 canary
--hypothesis      H2 grid / smoke canary
--budget          108 per cell (launcher hard-codes it; the flag is inert)
--fetch-followup-allowance 48 (tools-on only, from FETCH_ALLOWANCE=48)
fetch rounds      48 per arm (code constant, override --fetch-rounds-per-arm) / 3 per turn
price             1016 = 964 tranche + 48 canary + 4 warm-ups
headroom          3192 remaining of cap 4320
p95 floor         n >= 60 (H1 unreachable at 48 turns; the grid declares H2)
```

## 8. The most dangerous number

The **harness digest**. A launcher that trusts `GRID-PARAMS.json` passes
`2b4d4808…` and every one of the ten cells dies at `cell.py` stage 2/7
(`Abort(2, '2/7 harness')`) **before request 1** — the grid costs nothing and looks
broken, so the natural next move is to drop `--expect-harness`, which spends all
**1,016 requests against bytes nobody pinned**; the numbers the grid then produces are
void and a re-run costs another 1,016. Wrong by one generation, it is either a dead
launch or an unverifiable one.

## 9. What this card did not do

- No source was edited: `run_a_star.py`, `cell.py`, `run_longrun.py`, `analyze_stats.py`,
  `HARNESS-PIN.json`, `GRID-PARAMS.json`, `GRID-SHAPE.json`, the ledger, the fixture, and
  every published page are untouched. Each DISAGREES names the card that owns the fix.
- No live cell, no request, no socket.
