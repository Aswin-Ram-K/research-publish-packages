# TRANCH1-DRYRUN-2 — the ten cells re-rehearsed under the claim they can carry

**Unit:** `TRANCH1-DRYRUN-2` · **Offline:** zero requests, zero spawns, zero sockets · **Stamp:** `stamped`
**Grid:** `RUN-A*` — 10 cells x 48 turns (pair at 3 reps, context at 2), `tasks-v6/LR-01.v8.json`,
`--thinking off`, `--max-wall 2880`, `--turn-wall-cap 180`, `--runaway-turns 2`, per-cell cap 900,
**`--hypothesis H2`** on every cell. **Decision: GO.**
**Measurement:** [`../experiments/ptr-engine/measure/TRANCH1-DRYRUN-2.json`](../experiments/ptr-engine/measure/TRANCH1-DRYRUN-2.json)
· **check:** `python3 experiments/ptr-engine/tools/tranch1_dryrun.py --check`

## 1. The claim decision this rehearses

The first rehearsal (`TRANCH1-DRYRUN`) found a pincer: H1 needs `n >= 60` and a 48-turn cell is
`n = 48`, so **G3 refused all ten cells**; the pooled shape that satisfies `n` was refused by G2
(`8640 s > 2880 s`, `5760 s > 2880 s`). The decision (board #975) is that **a 48-turn cell cannot
carry an H1 claim by construction, so no cell makes one**:

- each cell launches with **`--hypothesis H2`** — the cache limb, a claim the cell can measure
  (`n >= 1`: prompt tokens per completed turn, `materiality_margin` `C <= 0.95 x A`);
- **H1 is adjudicated only on the pooled rows, after the tranche**, at **n = 144 per pair arm**
  (3 reps) and **n = 96 per context arm** (2 reps), by the analysis path -- never claimed at launch;
- **neither gate is edited**: G3 still refuses an H1 claim at n=48 (§3 below quotes it), G2 still
  caps the per-cell wall at 2,880 s (nobody launches the pooled shape as one process).

## 2. The ten cells

| cell | arm | G1 computed (cumulative) | G1 spent/turns/allowance | G1 | G2 projected s (ratio, source) | G2 | G3 n / min n (source) | G3 | treatments fire |
|---|---|---|---|---|---|---|---|---|---|
| 1 | `pointer-stable` r1 | 1154 | 1101/48/5 | allow | 2880 (1.0000, `artefact-mode`) | allow | 48 / 1 (`flag:--hypothesis (hypothesis)`) | allow | grow=None compact=None lease=None prefix=2 |
| 2 | `pointer-stable` r2 | 1154 | 1101/48/5 | allow | 2880 (1.0000, `artefact-mode`) | allow | 48 / 1 (`flag:--hypothesis (hypothesis)`) | allow | grow=None compact=None lease=None prefix=2 |
| 3 | `pointer-stable` r3 | 1154 | 1101/48/5 | allow | 2880 (1.0000, `artefact-mode`) | allow | 48 / 1 (`flag:--hypothesis (hypothesis)`) | allow | grow=None compact=None lease=None prefix=2 |
| 4 | `transcript-grow` r1 | 1154 | 1101/48/5 | allow | 2880 (1.0000, `artefact-mode`) | allow | 48 / 1 (`flag:--hypothesis (hypothesis)`) | allow | grow=21 compact=None lease=None prefix=None |
| 5 | `transcript-grow` r2 | 1154 | 1101/48/5 | allow | 2880 (1.0000, `artefact-mode`) | allow | 48 / 1 (`flag:--hypothesis (hypothesis)`) | allow | grow=21 compact=None lease=None prefix=None |
| 6 | `transcript-grow` r3 | 1154 | 1101/48/5 | allow | 2880 (1.0000, `artefact-mode`) | allow | 48 / 1 (`flag:--hypothesis (hypothesis)`) | allow | grow=21 compact=None lease=None prefix=None |
| 7 | `transcript-compact` r1 | 1154 | 1101/48/5 | allow | 2880 (1.0000, `artefact-mode`) | allow | 48 / 1 (`flag:--hypothesis (hypothesis)`) | allow | grow=None compact=21 lease=None prefix=None |
| 8 | `transcript-compact` r2 | 1154 | 1101/48/5 | allow | 2880 (1.0000, `artefact-mode`) | allow | 48 / 1 (`flag:--hypothesis (hypothesis)`) | allow | grow=None compact=21 lease=None prefix=None |
| 9 | `lease-reopen` r1 | 1154 | 1101/48/5 | allow | 2880 (1.0000, `artefact-mode`) | allow | 48 / 1 (`flag:--hypothesis (hypothesis)`) | allow | grow=None compact=None lease=23 prefix=None |
| 10 | `lease-reopen` r2 | 1154 | 1101/48/5 | allow | 2880 (1.0000, `artefact-mode`) | allow | 48 / 1 (`flag:--hypothesis (hypothesis)`) | allow | grow=None compact=None lease=23 prefix=None |

Every cell is one `cell.py --dry-run` invocation (`--turns 48 --reps 1 --hypothesis H2`) with its
own manifest (`experiments/ptr-engine/measure/dryrun2-t2-<arm>-r<rep>.json`). `all_ten_allowed = True`.
Total new spend **530 requests** (53 per cell); the sum of G1's cumulative displays is 11540.

## 3. Both gates behave — quoted, not paraphrased

`cell.py`'s own `eval_gate_prereg` / `eval_gate_projection`, over the real prereg and projection
artefacts. The probes change only the operand, never the check.

| probe | operand | verdict |
|---|---|---|
| G3, the claim a cell launches | `--hypothesis H2`, `n = 48` | **allow** (`n = 48`, min n = 1) |
| G3, the claim no cell makes | `--hypothesis H1`, `n = 48` | **refused** — verbatim below |
| G3, the pooled shape (post-hoc only) | `--hypothesis H1`, `n = 144` | **allow** (`n = 144`) |
| G2 at the ceiling | projected `2880 s`, `--max-wall 2880` | **allow**, ratio **1.0000** |
| G2 one second over | projected `2881 s`, `--max-wall 2880` | **refused** — verbatim below |

The `H1` refusal at n=48, verbatim:

> PARM-1 admits H1 (p95 TTFT, q=0.95) only at n >= 60 completed turns; this cell would have n=48, so its own n cannot support the claim it would state

The G2 refusal at 2,881 s, verbatim:

> projected wall 2881s = 48 request(s) x calibrated per-turn wall 60.0s for thinking off (flag) exceeds the allowed 2880s: this cell would spend its whole budget waiting on runaway turns

So the decision costs no gate edit: the claim that would be refused is the claim nobody makes.

## 4. The exact ten launch commands

These are the rehearsed argv with `--dry-run` dropped and `--out-dir` named; nothing else changes.
The per-arm 8-token warm-up is the one request `ENDPOINT-STATE.json -> grid_advice` asks for before
each arm's first cell; it lives in `run_longrun.py`'s own allocation and is **not** in cell.py's G1
arithmetic, so it is declared here rather than silently dropped.

```bash
# per-arm warm-up: 1 throwaway 8-token request before this arm's first cell (inside run_longrun's allocation, not a cell.py flag, not in G1's arithmetic)
python3 experiments/ptr-engine/longrun/cell.py --arm pointer-stable --fixture experiments/ptr-engine/longrun/tasks-v6/LR-01.v8.json --turns 48 --reps 1 --thinking off --max-wall 2880 --turn-wall-cap 180 --runaway-turns 2 --budget 900 --hypothesis H2 --no-cell-handoff --out-dir experiments/ptr-engine/measure
python3 experiments/ptr-engine/longrun/cell.py --arm pointer-stable --fixture experiments/ptr-engine/longrun/tasks-v6/LR-01.v8.json --turns 48 --reps 1 --thinking off --max-wall 2880 --turn-wall-cap 180 --runaway-turns 2 --budget 900 --hypothesis H2 --no-cell-handoff --out-dir experiments/ptr-engine/measure
python3 experiments/ptr-engine/longrun/cell.py --arm pointer-stable --fixture experiments/ptr-engine/longrun/tasks-v6/LR-01.v8.json --turns 48 --reps 1 --thinking off --max-wall 2880 --turn-wall-cap 180 --runaway-turns 2 --budget 900 --hypothesis H2 --no-cell-handoff --out-dir experiments/ptr-engine/measure
# per-arm warm-up: 1 throwaway 8-token request before this arm's first cell (inside run_longrun's allocation, not a cell.py flag, not in G1's arithmetic)
python3 experiments/ptr-engine/longrun/cell.py --arm transcript-grow --fixture experiments/ptr-engine/longrun/tasks-v6/LR-01.v8.json --turns 48 --reps 1 --thinking off --max-wall 2880 --turn-wall-cap 180 --runaway-turns 2 --budget 900 --hypothesis H2 --no-cell-handoff --out-dir experiments/ptr-engine/measure
python3 experiments/ptr-engine/longrun/cell.py --arm transcript-grow --fixture experiments/ptr-engine/longrun/tasks-v6/LR-01.v8.json --turns 48 --reps 1 --thinking off --max-wall 2880 --turn-wall-cap 180 --runaway-turns 2 --budget 900 --hypothesis H2 --no-cell-handoff --out-dir experiments/ptr-engine/measure
python3 experiments/ptr-engine/longrun/cell.py --arm transcript-grow --fixture experiments/ptr-engine/longrun/tasks-v6/LR-01.v8.json --turns 48 --reps 1 --thinking off --max-wall 2880 --turn-wall-cap 180 --runaway-turns 2 --budget 900 --hypothesis H2 --no-cell-handoff --out-dir experiments/ptr-engine/measure
# per-arm warm-up: 1 throwaway 8-token request before this arm's first cell (inside run_longrun's allocation, not a cell.py flag, not in G1's arithmetic)
python3 experiments/ptr-engine/longrun/cell.py --arm transcript-compact --fixture experiments/ptr-engine/longrun/tasks-v6/LR-01.v8.json --turns 48 --reps 1 --thinking off --max-wall 2880 --turn-wall-cap 180 --runaway-turns 2 --budget 900 --hypothesis H2 --no-cell-handoff --out-dir experiments/ptr-engine/measure
python3 experiments/ptr-engine/longrun/cell.py --arm transcript-compact --fixture experiments/ptr-engine/longrun/tasks-v6/LR-01.v8.json --turns 48 --reps 1 --thinking off --max-wall 2880 --turn-wall-cap 180 --runaway-turns 2 --budget 900 --hypothesis H2 --no-cell-handoff --out-dir experiments/ptr-engine/measure
# per-arm warm-up: 1 throwaway 8-token request before this arm's first cell (inside run_longrun's allocation, not a cell.py flag, not in G1's arithmetic)
python3 experiments/ptr-engine/longrun/cell.py --arm lease-reopen --fixture experiments/ptr-engine/longrun/tasks-v6/LR-01.v8.json --turns 48 --reps 1 --thinking off --max-wall 2880 --turn-wall-cap 180 --runaway-turns 2 --budget 900 --hypothesis H2 --no-cell-handoff --out-dir experiments/ptr-engine/measure
python3 experiments/ptr-engine/longrun/cell.py --arm lease-reopen --fixture experiments/ptr-engine/longrun/tasks-v6/LR-01.v8.json --turns 48 --reps 1 --thinking off --max-wall 2880 --turn-wall-cap 180 --runaway-turns 2 --budget 900 --hypothesis H2 --no-cell-handoff --out-dir experiments/ptr-engine/measure
```

Machine-readable twin: `launch_commands[]` in the measurement JSON (argv + shell + warm-up per cell).

## 5. The pooled analysis plan (a plan — there are no rows)

- **rows:** `experiments/ptr-engine/measure/rows-tranch1-*.jsonl`, one per live cell; **no such file exists yet**.
- **grouping:** by arm, pooling every rep; the pair comparison is `pointer-stable` (C) vs
  `transcript-grow` (A).
- **n per arm:** `pointer-stable n=144` · `transcript-grow n=144` · `transcript-compact n=96` · `lease-reopen n=96`. All at or above the frozen H1 floor of 60.
- **selector:** `analyze_stats.turn_latency_rows(rows) -> (selected, meta); one row per TURN, sample = row['ttft_ms'], absent/null/non-finite dropped and counted (never coerced to 0)`
- **call:** `analyze_stats.quantile_ci([r['ttft_ms'] for r in selected[arm]], q=0.95, resamples=10000, seed=20261020)`
- **p50:** `analyze_stats.quantile_ci(values, q=0.50) -- the materiality check, not a claim`
- **ranking:** disjoint 95% bootstrap intervals: C.hi < A.lo (PARM-1 H1 ranking_rule); overlapping intervals mean NO ranking claim
- **stop rule:** p95 intervals overlap OR |p50(C) - p50(A)| < 100 ms => 'not adjudicable at this budget'
- **owner:** V-TRANCHE-1 (9d271c32): H1 per grid WITH its n, and no direction reported when the pooled intervals overlap

## 6. Price, from the artefacts

| quantity | value |
|---|---|
| requests per cell | **53** (48 turns + ceil(48 x 68/801) = 5 follow-up allowance) |
| cells | 10 |
| total new requests (cells) | **530** |
| per-arm 8-token warm-ups | 4 |
| total including warm-ups | **534** |
| ledger cap / spent / remaining before | 4320 / 1101 / 3219 |
| spent after the tranche | 1631 |
| remaining after the tranche | 2685 |

**G1's `1154` per cell is cumulative, not a forecast** — `1,101 already spent + 48 turns + 5 allowance`
— so it must never be quoted as what the tranche costs. The marginal price is 53 requests per cell.

## 7. The pooled claim is not smuggled in at launch

Scanned the ten launch commands and the ten manifests for the string `H1`: **0 occurrence(s)**.
Zero is the requirement, and zero is what the artefacts carry: every launch command says
`--hypothesis H2`, and the only `H1` in this document describes the POST-HOC analysis in §1 and §5.

## 8. Zero network, zero spawn

Every invocation ran under a `sitecustomize.py` `sys.addaudithook` injected on `PYTHONPATH`
(`cell.py` unedited), recording `socket.*`, `urllib.*`, `http.client`, `subprocess.*`, `os.exec*`,
`os.fork*`, `os.posix_spawn*`. Per cell: **0 network events, 0 spawns**, and every run printed
"0 requests sent, no endpoint contacted". `unshare -n` is unavailable here, so the audit hook plus
the runner's own line is the primitive.

## 9. Treatments still fire inside the horizon

`wall_tokens_by_arm` = **10616** (never the dead top-level 3,838, which sits below v8's first prompt
3,848): `transcript-grow` first FIFO eviction **T21**, `transcript-compact` first wall **T21**,
`lease-reopen` first lease step **T23**, `pointer-stable` first prefix change **T2**.

## 10. What still stops the launch

1. **A gate refusal on any cell** — live exits 4 (G1), 8 (G2), 12 (G3). Under H2 all ten allow; a
   refusal in the live path is a finding, never something to route around.
2. **Projected wall > `--max-wall`** — the ceiling is exact: any reps>1 declaration or any larger
   per-turn wall refuses (the pooled shape is refused at 8,640 s / 5,760 s).
3. **A treatment that never fires inside 48 turns** — the arm becomes indistinguishable from control.
4. **`design_cap_tokens` reading 3,838 (or 65,536)** — the runner must read the per-arm wall.
5. **A spawn or a socket during a dry run.**
6. **Any pinned file moving between the first and last invocation** — the rehearsal is then
   `unstamped`, not a pass.

## 11. Pinning

`sha256` recorded before and after the ten runs for `cell.py`, `run_longrun.py`, `client.py`,
`exit_codes.py`, `tasks-v6/LR-01.v8.json`, `analyze_stats.py`: **stamped (no file moved)**.
