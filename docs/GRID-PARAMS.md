# GRID-PARAMS — the launch parameters the fetch-budget measurement requires

**Carrier:** [`experiments/ptr-engine/measure/GRID-PARAMS.json`](../experiments/ptr-engine/measure/GRID-PARAMS.json)
**Supersedes (parameters only, never bytes):** `GRID-SHAPE.json` field
`grid.requests_incl_digests` and the 24-round allowance. **Dated 2026-10-26.**
**Offline:** 0 requests, 0 network events, 0 live cells. Every figure below is a count over rows
already on disk.

**The one-sentence answer to this unit's question:** no — on the pre-RUNNER-ROUNDS-48 wiring a
48-turn tools-on cell kept its channel open only to **24** billed rounds, because
`--fetch-followup-allowance` is an accounting reserve in `cell.py` that never reaches the runner.
**Superseded 2026-10-26 (generation 1 → 48):** the pool is 48 and `--fetch-rounds-per-arm` sets it (§4).

---

## 1. Two demand regimes, one measurement

| regime | billed rounds | closes? | last billed turn | refusals |
|---|---|---|---|---|
| **v6** (modern, carries `billed_round`) | **20 of 24** | **never** | T16 | 0 `fetch_budget_exhausted` in 371 tool calls |
| **v4** (no `billed_round`; rounds billed on `path_not_found`) | 20 of 24 | never | T30 | not a modern demand measure |
| **v5** (direct observation of the failure chain) | **24 of 24 by T3** | **at T3** | T3 (21 rounds in one turn) | **226** across 45 post-closure turns |

v5 after closure, counted: **45** turns, **41** with tool calls, **1** cap-length completion at T29
(`completion_tokens 4096 / max_tokens 4096`, `finish_reason length`, `truncated true`) carrying
**130** refused calls. **43 of the 45** post-closure turns still invite a read; the model acted in
**41 of 45**.

This is a count of two cells, not a probability. The claim it supports is narrow and sufficient:
**v6's 20-of-24 is a demand observation, not a guarantee.** A shape whose channel can close at T3 and
whose remaining 45 turns keep asking for a read is not the shape we decided to run.

## 2. Why the conservative choice is 48

`48 = 2 × 24`. It is chosen to be larger than the largest single-turn burst observed (v5's 21) so
that no one turn can close the pool, and it covers v6's observed 20 with 28 rounds of margin.
The cost of that margin is **+240 requests** — see §3. It is **not** presented as a guarantee: §5
says exactly what it fails to bound.

## 3. The price

```
480 turns  + 480 rounds  + 4 digests = 964
previous price                        = 724   (480 + 240 + 4)
delta                                 = +240
remaining: 3,192 − 964                = 2,228
```

**Revision 2 (2026-10-26, `LAUNCH-PACKAGE-RECONCILE`) — the launch price is 1,016, not 964.** The
block above is preserved verbatim as the *tranches-only* price. What a launch actually pays is:

```
 964 tranche      (480 turns + 480 rounds + 4 digests)
+ 48 canary       (12 turns x 4 arms, N=12 per docs/TRANCHE-CANARY.md:23)
+  4 warm-ups     (one per arm)
= 1,016

remaining: 3,192 − 1,016 = 2,176
```

`2,228` above is the remainder of the tranches alone and is superseded as the launch remainder by
**2,176**. Artefact: `experiments/ptr-engine/measure/GRID-PARAMS.json` (revision 2) `price`, which
carries the components and a `supersedes` block naming this card.

**The budget figure is now measured, not assumed.** On the current `cell.py`, stage `3/7 budget`
(`cell.py:353-395`) asks the runner's own `--dry-run` for `would_send_total` and compares
`ceil(would_send_total × 1.10)` against `--budget`. Measured `would_send_total` = **48** (turns
only — the 48 fetch rounds are *not* added), so `required` = **53**, and **both `--budget 67` and
`--budget 108` are ALLOWED** at stage 3/7 (each exits 5 only because the probe shim refused the
live launch at stage 4/7). The earlier claim that `67` refuses at exit 3 before any request is
**false today**; see the dated correction in `docs/FETCH-BUDGET-48.md`. `108` is retained because
the launch command and `run_a_star.py:181`/`:280` carry it — not because `67` refuses.

**964 is not approved spend.** It is a price payable only *if* the grid runs, and it must always be
quoted beside the remaining headroom **and** the ledger caveat:

> the frozen artefact says **1,101 spent / 3,219 remaining**; the fresh scan says **1,128 / 3,192**.
> The **27**-request gap is unresolved and is settled by `LEDGER-REBUILD-27`. This document uses
> **3,192** because it is the conservative of the two.

## 4. The consistency check that changed the deliverable

The card asked me to verify two things against the runner. Both failed on re-reading the code.

**Paths first.** `experiments/ptr-engine/measure/run_longrun.py` does not exist. The runner is
[`experiments/ptr-engine/longrun/run_longrun.py`](../experiments/ptr-engine/longrun/run_longrun.py).

| premise | verdict | code |
|---|---|---|
| `--fetch-followup-allowance` sets the per-arm rounds | **false** | `run_longrun.py:230` is `TOOL_FETCH_ROUNDS_PER_ARM = 48`, overridable by `--fetch-rounds-per-arm` (`:2857`, default `:2856`); `:961` tests `rounds_used + fresh >= fetch_rounds_per_arm(cfg)`. **Generation 1 was 24 with no override — superseded 2026-10-26, because v5 spent all 24 inside turn 3 (21 in one recon burst) and starved the T46 checkpoint** |
| `--budget` is the per-cell request budget | **true, with a different mechanism than implied** | `cell.py:1859` → `stage_budget` (`cell.py:354-393`): runner `--dry-run` → `would_send_total` × `1.10` (`cell.py:140`) → `Abort(3, "3/7 budget")` when `required > --budget` |

- The runner has **two** fetch flags: `--fetch-rounds-per-turn` (`run_longrun.py:2852`, default
  `TOOL_FETCH_ROUNDS_PER_TURN = 3` at `:232`) caps rounds per **turn**; `--fetch-rounds-per-arm` (`:2857`) sets the per-**arm** pool.
- `--fetch-followup-allowance` is **`cell.py`'s G1 accounting reserve** (`cell.py:1882-1887`,
  consumed at `cell.py:1160-1165`, priced at `:1167-1175`). It never reaches the runner:
  `stage_run`'s argv (`cell.py:1550`) emits no such flag, and `run_a_star.py:201` appends it to the
  **cell** argv, not the runner's.

**Superseded 2026-10-26 (generation 1 → 48):** raising the flag to 48 rescues the price accounting
(G1 reserves 96 instead of 72) **and** it now reaches the runner — `TOOL_FETCH_ROUNDS_PER_ARM = 48`
at `run_longrun.py:230`, overridable by `--fetch-rounds-per-arm` (`:2857`). Nothing is blocked.

### `--budget 67` does abort the cell — but not as `BudgetExhausted`

With the 48-round pool the runner's projection is `48 turns + 48 rounds = 96`
(`projected_requests`, `run_longrun.py:436-443`, the pool added at `:463`; `transcript-compact` adds 2 digests → 98). The cell
gate requires `ceil(96 × 1.10) = 106` and `--budget 67` refuses at **exit 3, stage 3/7, before any
request is sent** (`cell.py:388-392`).

`BudgetExhausted` is a *different, runtime* error: raised at `run_longrun.py:984` against the
runner's internally computed budget, caught at `:2469`. `--budget` never reaches it. Both look like a
runner failure in a log; neither is one.

## 5. The per-cell budget, derived

| term | non-compact (cells 1-6, 9-10) | transcript-compact (cells 7, 8) |
|---|---|---|
| turn requests | 48 | 48 |
| fetch rounds | 48 | 48 |
| derived digests | 0 | 2 |
| **raw projection** | **96** | **98** |
| cell gate (+10%) | `ceil(96 × 1.1) = 106` | `ceil(98 × 1.1) = 108` |

**Recommended `--budget 108`** — one uniform value covering all ten cells; 106 would pass eight and
refuse the two compact cells. Digests need to be added **only** on cells 7 and 8; that is why the
number is 98 there and 96 elsewhere.

## 6. What 48 does not fix

1. **The burst.** A model that buys 21 rounds in one turn still buys 21 of 48; two such turns close
   it. What bounds the burst is the **per-turn** cap, `--fetch-rounds-per-turn`
   (`TOOL_FETCH_ROUNDS_PER_TURN = 3`, `run_longrun.py:232`) — v5 predates that bound. 48 bounds the
   *pool*, not the *rate*.
2. **Structure.** Only `B = 144` (3 × 48, the per-turn-cap ceiling) makes closure arithmetically
   impossible in a 48-turn cell. It costs 1,924 and leaves 1,268 of 3,192.
3. **Wiring.** 48 rounds cannot be switched on at all through an existing flag (§4).

## 7. Cards that must now read `GRID-PARAMS.json`

| card | why |
|---|---|
| `orchestration/units/RUN-A-STAR.md` | launches the 10 cells; would otherwise launch 24-round cells |
| `orchestration/units/DRYRUN-TOOLS-SHAPE.md` | quotes the tools-on shape/projection |
| `orchestration/units/GRID-SHAPE-TOOLS.md` | authored the 724 price and the `--budget 67` flags |
| `orchestration/units/FETCH-BUDGET-48.md` | authored the 48 recommendation |
| `orchestration/units/ANALYSIS-PATH-DRYRUN.md` | references the shape |
| `orchestration/units/CANARY-FALSE-POSITIVE.md` | references the shape |

`GRID-SHAPE.json` stays on disk unchanged — it is the record of what was decided before this
measurement. It is no longer the parameter source.

## 16-cell power-conformant shape (GRID-PARAMS-16CELL, 2026-10-26)

`measure/GRID-PARAMS.json` revision 3 records the shape `RUN-A-STAR-2` must launch.

| | 10-cell (rev 2, preserved verbatim in `supersedes`) | 16-cell (rev 3, live) |
|---|---|---|
| arms | 3 / 3 / 2 / 2 | 6 / 6 / 2 / 2 |
| cells | 10 | 16 |
| turns per cell | 48 | 48 |
| turns total | 480 | 768 |
| price | 1,016 (964 tranche + 48 canary + 4 warm-ups) | 1,056 (768 x 1.374532) |
| remaining after | 2,176 | 2,136 |

Why 16: `POWER-UNDER-TURN-N` measured `n_eff(144) = 31.36` on the binding arm
(`rows-longrun-c`, r=0.6423) against the floor of 60; six runs per pair arm
(`n_eff(288) = 62.73`) is the smallest conformant shape.

The multiplication and its factor: `768 turns x 1.374532 = 1055.640576 -> 1,056`. The
factor is `measure/GRID-SHAPE.json :: factor.tools_off_historical` --- the tools-OFF
historical factor. The 16 cells are tools-on `read_file` cells, whose measured factor in
the same record is 1.416667 / 1.5 / 1.5 (ceiling 1.5), so 1,056 is the tools-off price of
a tools-on shape. Recorded as a caveat, not smoothed: at the tools-on ceiling the same
768 turns cost 1,152.

Brake arithmetic: 1,128 spent + 1,056 price = 2,184 <= 4,320 cap, leaving 2,136.

`spend_status` stays **"NOT approved spend"**. Launch authority is board #865's recorded
default, not a params file.

### The launcher does not read this file (measured residual)

`tools/run_a_star.py` reads neither `GRID-PARAMS.json` nor `GRID-SHAPE.json`. Its grid is
the module constant `CELLS` (run_a_star.py:99-103), a literal 10-tuple, and it prints no
price line. A dry run therefore reports `cells=10` both before and after this promotion:
additive records cannot move what the launcher prints. Wiring 16 cells into a launch is a
change inside run_a_star.py (a follow-up card), not a params-file edit.

Spent/remaining: the launcher does not consult `request_ledger.build_report` either. It
counts row-file lines in `spend()` (run_a_star.py:167-175) and computes
`remaining = 3219 - (spend() - spent0)` (run_a_star.py:571, repeated at :585, :644, :652)
against a hardcoded 3,219 --- not the 4,320 cap and not the ledger's 3,192 remaining. The
4,320-cap arithmetic above is `cell.py`'s G1 gate (it prints `G1 1,224/4,320`), not the
launcher's own remaining line.
