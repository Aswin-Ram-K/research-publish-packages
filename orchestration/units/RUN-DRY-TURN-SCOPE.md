# RUN-DRY-TURN-SCOPE

**Card:** `9d7b9aac-6ca8-4b88-9a36-99c3bc15314b` — execution `a8085c15-2e50-4217-8cd5-5b5adf44d1e0`
**Status:** done · **Journal:** `orchestration/journals/RUN-DRY-TURN-SCOPE.jsonl` · **Handoff:** `orchestration/handoffs/RUN-DRY-TURN-SCOPE.json`

## One purpose

Make the runner's **dry run honour `--max-turns`**, so a 12-turn cell projects 12 turns instead
of the fixture's 48 — and a full cell stays byte-identical.

## What was measured (before)

| where | line (pre-edit) | code |
|---|---|---|
| live price | `experiments/ptr-engine/longrun/run_longrun.py:457-460` | `n_turns = int(fixture["N"])` / `max_turns = int(getattr(cfg, "max_turns", 0) or 0)` / `if max_turns > 0:` / `    n_turns = min(n_turns, max_turns)` |
| live loop | `run_longrun.py:2235-2238` | same four lines |
| **dry loop** | `run_longrun.py:2079` | `for t in range(1, int(fixture["N"]) + 1):` |
| **dry count** | `run_longrun.py:2120` / `:2124` | `turns = int(fixture["N"]) * c["reps"]` / `assert turns == int(fixture["N"]) * c["reps"], "turn count must be N x reps"` |

Reproduction on `tasks-v6/LR-01.v8.json`, `--arm pointer-stable --reps 1 --dry-run`:
`would_send_total=48`; adding `--max-turns 12`: **still `48`**.

Why it matters: G2 prices `turns × 60 s`. A 12-turn canary is `720 s` (inside the 900 s canary
wall); the preview priced it at `48 × 60 = 2880 s` and refused it. A dry run that ignores the turn
limit gates a cell that cannot exist.

## Fix — one source of truth

`cell_turns(cfg, fixture)` (`run_longrun.py:455`) is now the **only** definition of the cell's turn
scope; `projected_requests` (`:475`), `run_cell` (`:2259`) and `run_dry` (`:2092`) all call it. No
second `min()` was added to the preview.

| before | after |
|---|---|
| `for t in range(1, int(fixture["N"]) + 1):` (`:2079`) | `for t in range(1, n_turns + 1):` (`:2100`) |
| `turns = int(fixture["N"]) * c["reps"]` (`:2120`) | `turns = n_turns * c["reps"]` (`:2141`) |
| `assert turns == int(fixture["N"]) * c["reps"], …` (`:2124`) | `assert turns == n_turns * c["reps"], …` (`:2145`) |

The `--max-turns=<n>` suffix on the REQUEST-COUNT line is printed **only** when the cell is
genuinely shortened, so a full cell keeps its exact pre-fix bytes.

## Evidence

| case | projected | `turn_requests` | `would_send_total` |
|---|---|---|---|
| `--max-turns 12` | 12 | `turn_requests=12 (N=48 --max-turns=12 x reps=1)` | **12** |
| no flag | 48 | `turn_requests=48 (N=48 x reps=1)` | **48** |
| `--max-turns 96` | 48 | `turn_requests=48 (N=48 x reps=1)` | **48** |
| `--max-turns 24` | 24 | `turn_requests=24 (N=48 --max-turns=24 x reps=1)` | **24** |

(`pointer-stable` declares no digests and tools are off, so the projection is turns only.
`transcript-compact --max-turns 12` also reports `would_send_total=12`, `digest_requests=0`.)

Byte-identical proof (git-free): a `/tmp` copy of the runner with **only** the `run_dry` loop/count
reverted to `fixture["N"]` was diffed against the fixed runner — printed blocks identical for the
48-turn cell and for `--max-turns 96`, and `--max-turns 48` identical to no-flag. The only
whole-output difference is line 1 (manifest sha), which embeds `created_utc`; two identical
invocations differ in exactly `['created_utc']`, and `--max-turns` is not recorded in the manifest.

Live path unchanged: `projected_requests` old formula vs new `cell_turns` identical in **56/56**
cases (`max_turns ∈ {0,1,12,24,48,96,200}` × 4 arms × tools off/on).

## Test

`experiments/ptr-engine/tests/test_dry_turn_scope.py` — 14 cases: the end-to-end dry run must
project `min(48, max_turns)`; the same number must equal the live `projected_requests`; a source
guard forbids `fixture["N"]` as the preview's loop bound or count; full-cell line shape is pinned.
**Green** `14 passed`. **Red** with `RUNNER_UNDER_TEST` pointing at the reverted copy: `7 failed,
7 passed` (only the shortened-cell cases and the source guard fail — correct).

## Pin

`run_longrun.py` is in `HARNESS_FILES` (`cell.py:128-135`). Generation 4 pins it at
`b2003038…`; it is now `30dfa9e9…`, so gen 4's `harness_sha256 fa6fd8cc…` no longer describes this
tree. It was **already** stale (`grade_v5.py` moved earlier) and stays stale until
`HARNESS-PIN-GEN5` runs. **Not re-pinned here.**

## Not touched

`cell.py`, `analyze_stats.py`, `grade_v5.py`, `run_a_star.py`, `HARNESS-PIN.json`,
`GRID-PARAMS.json`, any fixture, any threshold, any published page; `PROJECTION.json` (60 s/turn),
the price 1,016, the ledger 1,128/3,192, the 900 s canary wall, every gate decision rule.
Write scope: `run_longrun.py` (`cell_turns` + the `run_dry` loop/count/print) and the new test.
