# RUN-A* — tranche 1 grid, stopped at cell 1 by stop rule 7 (exit 6)

**Outcome: 0 of 10 cells completed. 1 cell attempted (pointer-stable r1), 27 of 48 turns,
28 requests billed (27 cell + 1 warm-up), remaining 3,192 of the 3,219 headroom. The grid
HARD STOPPED under stop rule 7 and no second cell was launched.**

## Why it stopped (measured, not inferred)

`cell: 4/7 run REFUSED(6) run_longrun.py exited 6 (one or more runaway turns ended the cell)
— rows kept at experiments/ptr-engine/measure/rows-cell-pointer-stable-20261026T182535Z.jsonl`

Two turns consumed the whole 4096 completion ceiling and tripped the frozen `--runaway-turns 2`:

| turn | wall_ms | finish | truncated | content |
|---|---|---|---|---|
| T3 | 114,838.8 | length | true | loops `read_file`/`fetch` tool syntax (`\`\`\`read_file @knowledge:test_scope.py@1 ec36ff3a`) |
| T27 | 115,331.2 | length | true | degenerates into repeated `<tool_call>` tags |

`--tools` is off in the frozen launch shape, so the model cannot satisfy the tool calls the v8
questions invite and repeats them to the ceiling. This is model/fixture behaviour, not a gate.

Three things this exit is **not**:

- **not a cap-gate trip** — no `CAP GATE` line in the cell log or in the refusal document; the
  runaway path returns before `_gate_finish`, so no reconcile ran (documented defect (b)).
- **not the `cell.py:1568` mislabel** — the runner code 6 is in `_RUNNER_CODES`, so it was
  propagated verbatim with its own text; nothing was relabelled to 5.
- **not a wall-cap overrun** — 0 turns exceeded `--turn-wall-cap 180`; the cell used 349.5 s of
  its 2,880 s projection (advisory; source `measure/PROJECTION.json`, artefact-mode, thinking off).

## Preconditions, as checked at launch

| # | precondition | evidence |
|---|---|---|
| 1 | TRANCH1-DRYRUN-2 pass | re-ran `tools/tranch1_dryrun.py --check` → PASS 10/10, 0 spawns, 0 network events |
| 2 | SPAWN-RECORD-BIND pass | execution `0b644a75` succeeded; 18 tests, red→green recorded |
| 3 | SPAWN-TREE-BIND pass | execution `e998a682` succeeded; D5/D6 closed, 23 tests |
| 4 | V-CAPGATE-REFUSE | `partial` — the narrow waiver applied: believe the exit code, not the label; exit 5/6 = hard stop with diagnosis (that is what fired here) |
| 5 | refusal record binds the tree | `cell-pointer-stable-20261026T182535Z.refusal.json`: `cell_sha256 e24e867b…` = cell.py on disk, `spawn_record_sha256 eba15471…`, `tree_sha f17663d1…` = git HEAD |
| 6 | 12 checkpoints loadable | NUM 5 · CALL 4 · NONE 3 |
| 7 | wall-cap source | `wall_tokens_by_arm` **10616** on all four arms in the manifest; the top-level **3838** was never used (`wall_for_arm` is authoritative, `fixture_for_arm` is applied per arm at `run_longrun.py:2053,2158`) |

Treatment-fire turns on v8 (runner preflight, printed in cell 1's log): prefix **T2** ·
grow eviction **T21** · compact wall **T21** · lease step **T23** — all ≤ 48. Cell 1's own arm
(pointer-stable) shows `first prefix change at turn T2`; the other three markers are other arms' and
were never exercised.

## H1 / H2 / H3 / TVS — all not adjudicable, with the refusal text

- **H1 (p95 TTFT): `undecidable`.** PARM-1 needs n ≥ 60 completed turns per arm and a
  `quantile_ci` interval. 0 cells completed: one arm reached 27 turns and no interval was computed
  (the cell aborted at 4/7, before stages 5–6); the other three arms produced zero rows. **No bare
  p95 is published** — the 651 ms figure seen in the driver stream is an unquantiled descriptive
  number over 27 turns and is not H1.
- **H2 (prompt work): `undecidable`.** A cross-arm per-turn ratio needs two arms. Single-arm
  observation only: pointer-stable turns 6–27 carried ~4,852–5,020 prompt tokens of which
  **4,736 were cached** (cached share 0.978), i.e. ~85–116 uncached tokens per turn. Direction of
  the uncached limb is not computable from one arm, and neither limb is picked.
- **H3 (quality): `not adjudicable as a mechanism comparison` — and not graded at all.** The cell
  aborted before stage 5, so there is no `x/12`. Raw checkpoint outcome over the 8 reached turns:
  3 verified (T8, T12, T20), 5 wrong (T6, T14, T18, T24, T26), 4 never reached (T32, T36, T42, T46).
  The three NONE ids are `cp.3.t14`, `cp.5.t20`, `cp.10.t42` — 2 reached, 1 verified (T20), 1 wrong
  (T14 answered `CALL _refuse(...)`), 1 never reached. Over the 9 substantive ids: 6 reached,
  2 verified. `answered_ratio` and `contract_adherence` are undefined without a grade document.
  McNemar b/c and p: **not computed** — a paired test needs two graded arms.
- **TVS: `not_produced`.** 3 verified successes of 12 planned checkpoint turns, 4 never attempted,
  5 answered wrong; with 0 completed cells the per-arm denominator over completed turns is
  undefined, so the figure is **censored, not estimated**.
- **Answer length / completion tokens:** not comparable across arms (one arm, 27 turns).
  pointer-stable completion tokens ranged 5–718 on non-runaway turns plus the two 4,096-token
  runaway turns; reported here so that no cost claim is made from latency alone.

## Spend

| | |
|---|---|
| ledger before | spent 1,101 raw (1,071 dedup), remaining 3,219, cap 4,320, reserve 0 |
| this cell | 27 requests + 1 warm-up (pointer-stable, 260.4 ms, 8 completion tokens) |
| billed vs 660 | **28 of 660** |
| ledger after (rows on disk) | 1,128 rows, remaining **3,192** |
| dedup note | 1,101 **raw** is the budget figure; 1,071 is a diagnostic, never the budget |

## Stop rules that fired

- **Rule 7** — cell 1 exited **6**. HARD STOP, diagnosis above, no retry, no threshold changed,
  no second cell launched. (`--runaway-turns` and `--max-tokens` were left exactly as frozen.)
- Rule 3 — the refusal document itself notes `runner_launch=1 on a refusing invocation (must be 0)`.
  For a *pre-launch* gate refusal that is the right invariant; here the runner had to launch for the
  cell to run at all, so the observation is recorded rather than treated as an unconsulted gate.
- Rules 1, 2, 4, 5, 6 never became reachable: rule 1 (remaining < 264) needs six more cells;
  rule 2 has 0 turns over 180 s; rule 4 needs both pair arms; rules 5/6 need graded rows.

## v8-era caveat

Everything here is one grid on fixture `LR-01.v8.json` (sha 0804b515…), one model
(`occamy-1.0` at `http://192.168.2.168:8012/v1`), thinking off, tools off. The 27 turns are
**not** poolable with any earlier era: v8's walls are per-arm (10616) and its questions
(`@knowledge:` source inspection) are new. Nothing in this run may be compared to v3/v4/G4 rows.

## Promotion verdict for tranche 2

**Not offered.** Tranche 2 was conditional on pooled p95 intervals from 144 completed turns per arm;
0 cells completed, so the promotion test never ran and no extra reps can be justified.

## The operator's thesis

**`not adjudicable`** — and the one missing measurement is precise: **a cell that completes 48
turns at the frozen flags.** At `--max-tokens 4096`, `--tools off`, `--runaway-turns 2`, the v8
fixture drives this model into tool-call syntax degeneration that consumes the 4096 ceiling twice
by T27, and the runner correctly ends the cell at exit 6. Until either the fixture's questions stop
inviting tool calls at tools-off, or the launch shape explicitly enables the tool channel, no cell
of this grid can reach the horizon, so no pointer-vs-transcript comparison can be adjudicated.
This is a **launch-shape/fixture incompatibility**, not a latency result and not a treatment effect.
