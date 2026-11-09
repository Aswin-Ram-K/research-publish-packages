# GRID-SHAPE — the launch-shape question, answered from the fixture text

**Unit:** `GRID-SHAPE-TOOLS` · **Cost:** 0 inference requests, 0 network events, 0 live cells.
**Recommendation: (a) tools-on** — launch the v8 grid with `--tools read_file`, carried to the
frozen runner through `cell.py`'s `CELL_RUNNER_PATH` hook. **It is a new era: never pool it with
the 27 rows of the tools-off attempt.**

Machine-readable twin: [`GRID-SHAPE.json`](../experiments/ptr-engine/measure/GRID-SHAPE.json).
(The card's `measure/` resolves to `experiments/ptr-engine/measure/`, where every sibling
`GRID-*.json` lives; no duplicate copy was written.)

## 0. The premise, checked against the fixture instead of the hint

The handoff's diagnosis named *"`@knowledge:` source inspections"* as the v8 shape. **Three
corrections, all measured on the bytes:**

1. **No turn in any generation contains `@knowledge:`** — 0/48 in v5, v6, v7, v8.
2. **No turn contains the literal `read_file`** — 0/48 in all four. The string appears exactly
   once in the v8 *system prompt*, in the sentence that says checkpoint turns have no tools.
3. **The read invitation predates v8 by three generations.** v5 already carried it on 46/48
   turns. So this is **new model behaviour on an old question shape**, not a v8 fixture defect —
   which is exactly the case the card said would change the recommendation.

The invitation is a **path reference**, e.g. `Read ptr_engine/resolve.py#L66-L110 and list every
raise site`. 46 of 48 turn blocks carry one; the two that do not are **T30** (`repair`) and
**T48** (`verify`).

## 1. Fixture census — v8, 48 turn blocks

`invites-read` = the question names a source path (`*.py`, `*.py#L…`, `*.md`, `*.json`, `*.txt`).
Checkpoint ids are the v8 ids.

```
T   kind        read  cp id        T   kind        read  cp id
1   work        yes   -            25  work        yes   -
2   plant       yes   -            26  checkpoint  yes   cp.7.t26
3   work        yes   -            27  work        yes   -
4   work        yes   -            28  work        yes   -
5   work        yes   -            29  work        yes   -
6   checkpoint  yes   cp.0.t06     30  repair      no    -
7   work        yes   -            31  work        yes   -
8   checkpoint  yes   cp.1.t08     32  checkpoint  yes   cp.8.t32
9   work        yes   -            33  work        yes   -
10  work        yes   -            34  work        yes   -
11  work        yes   -            35  work        yes   -
12  checkpoint  yes   cp.2.t12     36  checkpoint  yes   cp.9.t36
13  work        yes   -            37  work        yes   -
14  checkpoint  yes   cp.3.t14     38  work        yes   (errors.py)
15  work        yes   -            39  work        yes   -
16  work        yes   -            40  work        yes   -
17  work        yes   -            41  work        yes   -
18  checkpoint  yes   cp.4.t18     42  checkpoint  yes   cp.10.t42
19  work        yes   -            43  work        yes   -
20  checkpoint  yes   cp.5.t20     44  work        yes   (errors.py)
21  work        yes   -            45  work        yes   -
22  work        yes   -            46  checkpoint  yes   cp.11.t46
23  work        yes   -            47  work        yes   -
24  checkpoint  yes   cp.6.t24     48  verify      no    -
```

**Counts.** 46/48 turns invite a read. **All 12 checkpoint turns invite a read**
(`cp.0.t06`, `cp.1.t08`, `cp.2.t12`, `cp.3.t14`, `cp.4.t18`, `cp.5.t20`, `cp.6.t24`,
`cp.7.t26`, `cp.8.t32`, `cp.9.t36`, `cp.10.t42`, `cp.11.t46`) — i.e. **12/12 checkpoint ids sit
on a tool-inviting turn**; 0/12 sit on a turn that does not.

### Generation comparison — the invitation is not new

| generation | `@knowledge:` | literal `read_file` | path ref | turns without a path ref | checkpoints | checkpoint ids on an inviting turn |
|---|---|---|---|---|---|---|
| v5 (runtime-v5) | 0/48 | 0/48 | **46/48** | T30, T48 | 3 | 3/3 |
| v6 (runtime-v5) | 0/48 | 0/48 | **46/48** | T30, T48 | 12 | 12/12 |
| v7 | 0/48 | 0/48 | **46/48** | T30, T48 | 12 | 12/12 |
| v8 | 0/48 | 0/48 | **46/48** | T30, T48 | 12 | 12/12 |

The degeneration is therefore **occamy-1.0 emitting `<tool_call>` syntax that nothing serves**,
on a question shape that has asked for a file read since v5. At tools-off the model's designed
resolution path is absent, so it retries the call until the 4,096-token completion ceiling is
gone (T3 `stop_reason=length`, T27 `runaway_turn`, both `truncated=true`, `completion_tokens=4096`).

## 2. Plumbing — where `--tools` can and cannot go

| hop | `file:line` | what it does |
|---|---|---|
| runner flag | `experiments/ptr-engine/longrun/run_longrun.py:2798-2800` | `--tools LIST`, documented `supported: read_file` |
| runner predicate | `run_longrun.py:255-259` | `tool_names()` split on `,`; `tools_enabled()` = `"read_file" in names` |
| fetch budget | `run_longrun.py:226,231` | `TOOL_FETCH_ROUNDS_PER_ARM = 24`, `TOOL_FETCH_ROUNDS_PER_TURN = 3` |
| checkpoint gate | `run_longrun.py:2409-2411` | `if tools_enabled(cfg) and not is_answer_turn:` — **checkpoint turns never fetch**, even tools-on |
| **cell.py parser** | `experiments/ptr-engine/longrun/cell.py:1807-1867` | **no `--tools` argument exists** |
| **cell.py runner argv** | `cell.py:1501-1521` | `argv = [sys.executable, RUNNER, "--fixture", …]`; **`--tools` is never emitted** |
| cell.py runner path | `cell.py:122` | `RUNNER = os.environ.get("CELL_RUNNER_PATH") or os.path.join(HERE, "run_longrun.py")` |
| cell.py launch | `cell.py:1502` | `argv = [sys.executable, RUNNER, …]` — a python file, run by the same interpreter |
| cell.py harness pin | `cell.py:126-133` | `HARNESS_FILES` digests **`run_longrun.py`'s bytes**, not the path it is launched through |
| cell.py fetch price | `cell.py:153-155`, `:1137`, `:1834` | `FETCH_FOLLOWUP_RATIO = 68/801`; `--fetch-followup-allowance` overrides it |

**Finding, precisely.** `cell.py` has no `--tools` argument and its runner argv never carries one,
so passing `--tools read_file` to `cell.py` is rejected by argparse (exit 2). `cell.py` *can price*
a tools-on cell (`--fetch-followup-allowance`) but **cannot start one**. The runner accepts the
flag directly. `cell.py` is held by another card, so it was not patched.

**Routing used.** `--tools read_file` rides a two-line shim generated by the driver at
`$TMPDIR/grid-shape-shim/runner_read_file.py`, named through `CELL_RUNNER_PATH` (`cell.py:122`).
The shim does `runpy.run_path(run_longrun.py)` with `--tools read_file` appended, so
`run_longrun.py` executes **byte-for-byte unchanged** and `cell.py`'s `HARNESS_FILES` digest still
matches — the dry run prints `2/7 harness ok harness_sha256=c4541802…`. Every cell gate (G1/G2/G3),
the claim sidecar, the grader, the analyser and the p4 gate are unchanged. **No `cell.py` patch,
no `run_longrun.py` patch.**

## 3. The three options, with numbers

### (a) tools on — `--tools read_file`

Tools-on request rate, measured on the three historical tools-on cells in
`experiments/ptr-engine/measure/` (each 48 turns, arm `pointer-stable`):

| rows file | turn rows | tool-followup rows | requests/turn |
|---|---|---|---|
| `rows-longrun-v4-tools-2026-10-26.jsonl` | 48 | 20 | **1.416667** |
| `rows-longrun-v5-tools.jsonl` | 48 | 24 | **1.500000** |
| `rows-longrun-v6-tools.jsonl` | 48 | 24 | **1.500000** |

1.50 is **not a hope, it is the ceiling**: at most `TOOL_FETCH_ROUNDS_PER_ARM = 24`
(`run_longrun.py:226`) follow-up requests per 48-turn arm ⇒ `(48+24)/48 = 1.5` exactly.

Tranche 1 = 10 cells × 48 turns = **480 turn rows**; follow-ups ≤ 10 × 24 = **240**; the two
`transcript-compact` cells add `run_longrun.expected_digests(v8) = 2` derived digest rows each = **4**.

| quantity | value |
|---|---|
| requests charged by G1 | 480 + 240 = **720** (factor 1.5000, not 1.374532) |
| requests including derived digests | **724** |
| share of the 3,192 remaining | **22.6 %** |
| remaining after | **2,472** (2,468 with digests) |
| cell-10 cumulative G1 | 1,101 + 720 = **1,821 / 4,320** |
| wall at 60 s/turn | 48 × 60 = 2,880 s/cell ⇒ **8 h 00 m** sequential |

Cost: every follow-up is a real request inside its turn, so a fetch turn's `wall_ms` includes the
follow-up's latency while the row keeps the initial send's own measurement (ROW-ATTRIBUTION). The
turn's p95 is therefore **`attribution_disputed`** — usable, but not identical in meaning to a
tools-off turn's p95, and the following YAML/era note must travel with it.

### (b) drop the tool-inviting fixtures at tools-off

- The v8 directory holds exactly one grid fixture (`LR-01.v8.json`); "drop it" leaves **0 fixtures,
  0 cells, 0 requests** — H2 and H3 are unadjudicable, not merely reduced.
- Dropping the inviting **turns** instead: 46 of 48 go, leaving **T30 (repair)** and **T48
  (verify)** — 2 turns/arm.
- **H3's denominator becomes 0 of 12 checkpoint ids**, because all 12 checkpoints sit on inviting
  turns. Paired McNemar items: 0 (the veto needs `b+c ≥ 6`). H2 has n=2 turns/arm, below its own
  `min_n ≥ 1` but useless for a per-turn ratio.

### (c) raise the cap-length counter (`--runaway-turns`)

Requires a re-frozen PARM-1 amendment (a threshold change ⇒ a new era). At tools-off the observed
truncation rate is **2 / 27 turns = 7.41 %**, so a 48-turn cell expects **3.6** truncated turns —
the counter would have to reach ≥4. **It converts a truncation into a recorded non-answer rather
than a measurement:** the turn's 4,096 completion tokens are still spent and the turn still yields
nothing, so the cell reaches turn 48 carrying ~4 rows that answer nothing, and the checkpoints
those turns feed stay empty. You pay the full 660 requests (tools-off factor 1.374532) for a grid
whose cells contain holes.

## 4. Recommendation — (a), with an era break

**Justification.** (b) destroys the denominator (0/12 checkpoints). (c) buys continuation, not
answers, and needs a threshold re-freeze. (a) is the shape the fixture was written for: 46/48 turns
ask for a file, the runner has served `read_file` since `FETCH-CHANNEL`, and the three tools-on
cells on disk each finished **48 of 48 turns** with 20–24 served follow-ups — 0 runaway aborts.
Tools-on is also the only option that leaves H2's `prompt_tokens` comparison meaningful, because
the pointer arm's designed saving is *fetch on demand instead of pinning the body*.

**Launch-shape sentence a successor can act on:** *run the ten H2 cells with
`run_a_star.py --tools read_file`, which sets `CELL_RUNNER_PATH` to a shim that appends
`--tools read_file` to the frozen runner and passes `--fetch-followup-allowance 24` to `cell.py`;
keep `--max-tokens 4096` and `--runaway-turns 2`; treat the resulting rows as era B and never
pool them with the 27 tools-off rows.*

## 5. The launch command set (`measure/GRID-SHAPE.json`)

One command per cell, ten cells:

```
python3 experiments/ptr-engine/tools/run_a_star.py --cell N --tools read_file --budget 67 \
        --hypothesis H2 --fixture experiments/ptr-engine/longrun/tasks-v6/LR-01.v8.json
```

resolving to the frozen `cell.py` argv
`--arm <arm> --fixture …/LR-01.v8.json --turns 48 --reps 1 --thinking off --max-wall 2880
--turn-wall-cap 180 --runaway-turns 2 --budget 67 --hypothesis H2 --fetch-followup-allowance 24
--no-cell-handoff --out-dir experiments/ptr-engine/measure` with
`CELL_RUNNER_PATH=$TMPDIR/grid-shape-shim/runner_read_file.py`.
Cell order (unchanged): `pointer-stable` r1–3, `transcript-grow` r1–3, `transcript-compact` r1–2,
`lease-reopen` r1–2.

## 6. Offline dry run — all ten commands, `cell.py --dry-run`

Every cell ran through the driver with `--dry-run` (the preflight subprocess is the shim), **0
requests sent, no endpoint contacted**. Identical gate lines on all ten, because the ledger's
`spent` is frozen at 1,101 while nothing is spent:

| cell | arm / rep | G1 | G2 | G3 | rc | design_cap_tokens |
|---|---|---|---|---|---|---|
| 1 | pointer-stable r1 | 1,173/4,320 | 2,880 s of 2,880 s | n=48 ≥ 1 | 0 | 10616 |
| 2 | pointer-stable r2 | 1,173/4,320 | 2,880 / 2,880 s | n=48 ≥ 1 | 0 | 10616 |
| 3 | pointer-stable r3 | 1,173/4,320 | 2,880 / 2,880 s | n=48 ≥ 1 | 0 | 10616 |
| 4 | transcript-grow r1 | 1,173/4,320 | 2,880 / 2,880 s | n=48 ≥ 1 | 0 | 10616 |
| 5 | transcript-grow r2 | 1,173/4,320 | 2,880 / 2,880 s | n=48 ≥ 1 | 0 | 10616 |
| 6 | transcript-grow r3 | 1,173/4,320 | 2,880 / 2,880 s | n=48 ≥ 1 | 0 | 10616 |
| 7 | transcript-compact r1 | 1,173/4,320 | 2,880 / 2,880 s | n=48 ≥ 1 | 0 | 10616 |
| 8 | transcript-compact r2 | 1,173/4,320 | 2,880 / 2,880 s | n=48 ≥ 1 | 0 | 10616 |
| 9 | lease-reopen r1 | 1,173/4,320 | 2,880 / 2,880 s | n=48 ≥ 1 | 0 | 10616 |
| 10 | lease-reopen r2 | 1,173/4,320 | 2,880 / 2,880 s | n=48 ≥ 1 | 0 | 10616 |

G1 arithmetic: `spent 1,101 + turns 48 + follow-up allowance 24 = 1,173`. Across the grid the
ledger's cumulative projection is `1,101 + 72·n` — cell 10 = **1,821 / 4,320**, well inside the cap.
`tranch1_dryrun.py --check`: **PASS, 10/10 cells, design_cap_tokens=[10616] on every arm** (never
3838), all four treatments fire ≤ 48 (`prefix` T2, `grow` T21, `wall` T21, `lease` T23).

## 7. Is `--runaway-turns 2` still safe under tools-on?

**Yes, with one spare truncation per cell — and that is the residual risk, in plain numbers.**

- Historical tools-on cells: **2 truncated turns in 144 turn observations** = **1.39 %/turn**
  (v4 1/48, v5 1/48, v6 0/48), and **all three reached turn 48**. Tools-off v8: **2/27 = 7.41 %/turn**,
  a **5.3× worse** rate.
- The cell aborts on the **2nd** truncated turn. Spare budget = 1.
- Naive independence at 1.39 %/turn: λ = 48 × 0.0139 = **0.667** → P(≥2 in a cell) =
  `1 − e^−λ(1+λ)` = **14.4 %**. So **~1.4 aborts expected across the ten cells**; P(all ten clean)
  = 0.856^10 ≈ **21 %**.
- **Consequence a successor must plan for:** stop rule 7 is *grid-fatal* — the first `rc=6` ends the
  tranche (that is what stopped cell 2 from ever launching). At 14.4 %/cell the grid is expected to
  stop after **≈7 of 10 cells**. Deciding whether an aborted cell is instead recorded as an abandoned
  cell and the grid continues (a 3-abort stop) is a **policy decision for the next card**; this unit
  did not change the rule, and did not touch `--runaway-turns`.

## 8. Era statement

- **Era A** — tools-off v8: the stopped cell
  `rows-cell-pointer-stable-20261026T182535Z.jsonl`, **27 rows**, exit 6, T3+T27 truncated at the
  4,096 ceiling. It is kept **as an abandoned-cell record**. It is never deleted, never rewritten,
  and **never pooled** with anything.
- **Era B** — tools-on v8: the ten cells this card launches. Different follow-up channel, different
  per-turn latency meaning (`attribution_disputed`), different request factor (1.5000 vs 1.374532),
  different token accounting (a `<tool_result>` is in the prompt).
- **A tools-on v8 grid and a tools-off v8 attempt are two eras. Pooling them would compare a cell
  that could not reach turn 28 with cells that can, and would attribute a request-rate difference to
  the treatment.** The `tools` key in the manifest (`run_longrun.py:1437`) is the machine-checkable
  discriminator; `analyze_stats` must never see both in one arm.

## 9. What this unit did not touch

`PARM-1*`, the fixture's questions and thresholds, `cell.py`, `run_longrun.py`, the graders, the
analyser, `REQUEST-LEDGER.json`, every row file, every published number. The only code change is
the driver `experiments/ptr-engine/tools/run_a_star.py` (it now forwards `--tools` through
`CELL_RUNNER_PATH`, prices the 24-round follow-up pool, and takes `--cell/--dry-run/--fixture/
--budget/--hypothesis`; with `--tools` absent the launch is byte-identical to the historical one).
