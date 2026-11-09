# GRID-BUDGET-RECHECK — two prices for one grid, reconciled

**Verdict: PASS. Yes — three reps of the frozen 48-turn grid finish inside 3,219 remaining requests (636 spent, 2,583 left).**

Offline: 0 requests. Four dry runs under a `sys.addaudithook` that records `socket.*`, `urllib.` and
`http.client` events: `AUDIT_NETWORK_EVENTS=0 []` each time, and every gate line self-reports
"0 requests sent, no endpoint contacted".

## 1. The two prices, recomputed

| price | figure | arithmetic | source |
|---|---|---|---|
| `V8-DRYRUN-REFREEZE` dry run | **1,154** | 1,101 spent + 48 turns + 5 allowance | `cell.py` G1 line, reproduced |
| same, `--reps 3` | **1,258** | 1,101 + 144 + 13 | reproduced |
| `BUDGET-SCHEDULE` A\* | **792** | 576 turns x (1,101/801 = 1.374532) = 791.7303 -> 792 | `orchestration/handoffs/BUDGET-SCHEDULE.json` |

Per rep the multiplier gives 192 x 1.374532 = 263.91 -> **264**, which is where "264/rep" came from.
The dry run's 1,154 is **not** a per-rep price at all: it is *cumulative* (already-spent included) and it
describes **one arm** (48 turns), because `--arm transcript-grow` is a single treatment. Asking the same
command for 3 reps gives 1,258 — it grows by 104 (144 turns - 48 turns = 96, plus allowance 13 - 5 = 8),
still carrying the 1,101 baseline.

## 2. Decomposition of 1,154

| term | value | code |
|---|---|---|
| already spent | 1,101 | `experiments/ptr-engine/tools/request_ledger.py:599` `projected = requests_published + would_spend`; printed by `experiments/ptr-engine/longrun/cell.py:1179` |
| turns (`turns x arms x reps` = 48 x 1 x 1) | 48 | `experiments/ptr-engine/longrun/cell.py:875` |
| fetch follow-up allowance `ceil(48 x 68/801)` = ceil(4.0749) | 5 | ratio at `cell.py:124`; `cell.py:888`; `cell.py:1100` |
| digests / warm-ups / per-arm fixed cost inside G1 | **0** | G1 adds no such term (`cell.py:895` is `would_spend = turns_total + allowance` only) |

`1,101 + 48 + 5 = 1,154`. Digests and the 24-round tool pool exist, but only in the **runner's own**
allocation: `experiments/ptr-engine/longrun/run_longrun.py:440` adds `expected_digests(fixture)` for
`transcript-compact` (function at `run_longrun.py:1342`) and `TOOL_FETCH_ROUNDS_PER_ARM = 24`
(`run_longrun.py:226`); that is a per-cell cap, not the ledger gate.

**The term the 792 computation omitted: the already-spent 1,101 requests.** The gate prints cumulative
projected spend; the multiplier priced marginal spend only. There is a second, smaller divergence in the
*rate*: the gate charges `1 + 68/801 = 1.084894` requests/turn, the historical factor is
`1,101/801 = 1.374532`; the gap is exactly `232/801 = 0.289638` — the **232 unmarked request rows**
(1,101 = 801 turn + 68 tool-follow-up + 232 unmarked). The allowance carries the 68 follow-ups; the gate
never charges the 232 unmarked rows.

## 3. reps -> requests -> remaining (price the gate will enforce)

The grid is one cell per (arm, rep): `run_longrun.py:2843`
`cells = [(arm, rep) for arm in arms for rep in range(1, int(cfg.reps) + 1)]`.
Each cell is one arm at 48 turns: `48 + ceil(48 x 68/801) = 53`.

| reps | cells | new requests | cumulative printed | remaining after |
|---|---|---|---|---|
| 1 | 4 | 212 | 1,313 | 3,007 |
| 2 | 8 | 424 | 1,525 | 2,795 |
| 3 | 12 | 636 | 1,737 | **2,583** |

**Largest frozen-compatible design that finishes inside 3,219: 3 reps (A\*) — 636 new requests, 2,583 left.**
No turn count is traded away: `PARM-1` keeps 48 turns/arm.

**H3 cost: none.** 3 checkpoint ids per rep x 3 reps = 9 ids -> 36 paired items
(`BUDGET-SCHEDULE` `evaluability.A*`), comfortably over `b+c >= 6`. 2 reps would give 6 ids / 15 pairs;
1 rep gives only 3 ids and is not evaluable (`b+c <= 3 < 6`).

## 4. What the gate enforces at launch

`cell.py` G1 (`eval_gate_ledger`, `cell.py:1127-1192`) passes `would_spend = turns_total + allowance`
into `request_ledger.build_report` (`cell.py:1167-1168`), which returns `projected = spent + would_spend`
(`request_ledger.py:599`), and compares it to `headroom = cap - reserve = 4,320` (`cell.py:1175`).
So the binding condition is `would_spend <= 3,219` — i.e. **the dry-run arithmetic (53 per cell), not the
1.374532 multiplier**. `1.374532` appears nowhere in the gate; only `FETCH_FOLLOWUP_RATIO = 68.0/801.0`
(`cell.py:124`) does. The printed "1,154" is the cumulative display of the same comparison.

## Reproduction

```
python3 experiments/ptr-engine/longrun/cell.py --dry-run \
  --fixture experiments/ptr-engine/longrun/tasks-v6/LR-01.v8.json \
  --turns 48 --reps 1 --hypothesis H2 --arm transcript-grow --out-dir /tmp/gr-man
python3 experiments/ptr-engine/longrun/cell.py --dry-run ... --reps 3 ...
```

Files not edited: `cell.py`, `run_longrun.py`, `PARM-1`, `LR-01.v8.json`, `measure/REQUEST-LEDGER.json`.
