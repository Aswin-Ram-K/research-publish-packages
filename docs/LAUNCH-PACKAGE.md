# LAUNCH-PACKAGE — go/no-go for RUN-A-STAR-2

Audit: `LAUNCH-PACKAGE-AUDIT` (offline, read-only, 0 requests). Read at 2026-10-26T19:05Z; the tree was moving — `run_longrun.py` changed at 19:04:32Z during this batch, so the runner sha quoted here is the one *this audit read*, not a settled one.

## Verdict

**`ready_to_launch: false`** — 4 blocking gates (pin moved, price 1,016 absent from artefacts, canary N discordant in two docs, stale allowance/budget in GRID-SHAPE).

## Gates

| gate | artefact path | value | verdict | what a launcher must do |
|---|---|---|---|---|
| G1 pool | measure/GRID-PARAMS.json :: fetch_followup_allowance.value | 48 = run_longrun.py:230 TOOL_FETCH_ROUNDS_PER_ARM (was 24 at :226); override flag now exists, run_longrun.py:2857 --fetch-rounds-per-arm | **agree** | launch as-is; do not trust the 'no override' sentence in GRID-PARAMS.json:75 — it predates the 19:04:32Z edit |
| G2 budget | measure/GRID-PARAMS.json :: per_cell_budget.value | 108 = run_a_star.py:181 argv '--budget','108' and run_a_star.py:280 default 108; driver grid == 108 | **agree** | pass 108; ignore GRID-SHAPE.json cells[*].cell_py_flags[6] '--budget 67' |
| G3 price | measure/GRID-PARAMS.json :: price.total | 964 = 480 turns + 480 rounds + 4 digests; the loaded 1,016 (964 + 48 canary + 4 warm-ups) is quoted by NO measure artefact | **disagree** | do not launch until 1,016 arrives in a measure artefact with its own arithmetic; card prompt says 964/2,228 while card description says 1,016/2,176 |
| G4 remaining | measure/REQUEST-LEDGER.json :: budget.remaining_raw | 3,192 (requests 1128) = LEDGER-GRID-BASELINE-2.json :: remaining 3192 (source_ledger_sha256 matches the current ledger) | **agree** | quote 3,192; 2,228 is only the 964-price remainder and 2,176 exists in no artefact |
| G5 canary | measure/CANARY-ERA-B-FIX.json :: gate_recommendation | N=12, shape_ok, answer_verified>=1, stop_signal_source=finish_reason | **disagree** | docs/TRANCHE-CANARY.md:23 still defaults N=5 and docs/FETCH-BUDGET-48.md:166 still asserts N=5; gate text must be fixed to N=12 before launch |
| G6 pin | measure/HARNESS-PIN.json :: harness_sha256 | recorded 1f7c6791… but the tree now hashes to 2b4d4808… (one file moved: run_longrun.py 0d581d1f… -> b2003038…, mtime 2026-10-26T19:04:32Z) | **moved** | RE-PIN FIRST: the launch must re-pin and pass --expect-harness 2b4d4808… (or later) or it dies at cell.py stage 2/7 |
| G7 baseline | measure/LEDGER-GRID-BASELINE-2.json | label pre_grid_era_b, frozen_at 2026-10-26T19:04:18Z, requests 1128 / remaining 3192, source_ledger_sha256 6da0c1f19b7c… == current REQUEST-LEDGER.json | **agree** | quote spend against LEDGER-GRID-BASELINE-2.json; LEDGER-GRID-BASELINE.json (1101/3219) is frozen-but-superseded and must not be the delta base |
| G8 command | experiments/ptr-engine/tools/run_a_star.py:177-205 cell_argv + run_cell | per-cell argv assembled below; two tokens differ between documents (allowance 24 vs 48, budget 67 vs 108) | **disagree** | run the assembled argv only; the GRID-SHAPE flag list is stale in positions 6 and 8 |

### Assembled per-cell command

```
python3 <CELL=experiments/ptr-engine/longrun/cell.py> --arm <pointer-stable|transcript-grow|transcript-compact|lease-reopen> --fixture experiments/ptr-engine/longrun/tasks-v6/LR-01.v8.json --turns 48 --reps 1 --thinking off --max-wall 2880 --turn-wall-cap 180 --runaway-turns 2 --budget 108 --hypothesis H2 --no-cell-handoff --out-dir experiments/ptr-engine/measure --endpoint <ENDPOINT> [--dry-run] --fetch-followup-allowance 48   # tools-on only; env CELL_RUNNER_PATH=<shim appending --tools read_file>
```

Tokens that differ between documents: `--budget` (**108** GRID-PARAMS/run_a_star vs **67** GRID-SHAPE flags) and `--fetch-followup-allowance` (**48** vs **24**). `--turns 48`, `--reps 1`, `--thinking off`, `--max-wall 2880`, `--turn-wall-cap 180`, `--runaway-turns 2`, `--hypothesis H2`, `--no-cell-handoff` agree everywhere; `--reps`/`--max-wall`/`--out-dir`/`--endpoint` are carried by `run_a_star.py` but are absent from `GRID-SHAPE.json`'s flag list.

## Contradictions

- **allowance** — 48 (measure/GRID-PARAMS.json :: fetch_followup_allowance.value; experiments/ptr-engine/tools/run_a_star.py:44 FETCH_ALLOWANCE = 48)  vs  24 (experiments/ptr-engine/measure/GRID-SHAPE.json :: cells[*].cell_py_flags[8] '--fetch-followup-allowance 24'; also cells[*].projection.followup_allowance 24)  → stale: GRID-PARAMS.json :: supersedes declares this exact field superseded
- **per-cell budget** — 108 (measure/GRID-PARAMS.json :: per_cell_budget.value; experiments/ptr-engine/tools/run_a_star.py:181 argv and :280 default)  vs  67 (experiments/ptr-engine/measure/GRID-SHAPE.json :: cells[*].cell_py_flags[6] '--budget 67')  → stale: 67 refuses at exit 3 stage 3/7 before any request (runner projects 72, +10% = 79 > 67)
- **runner pool constant** — 48 at experiments/ptr-engine/longrun/run_longrun.py:230, with --fetch-rounds-per-arm at :2857  vs  24 'at run_longrun.py:226, a module constant with no override' (measure/GRID-PARAMS.json :: per_arm_round_cap.declared_at; docs/DRYRUN-TOOLS-SHAPE.md:70 says :2228)  → disagree: the document is right for the bytes it read and wrong for the tree at 19:04:32Z; line numbers shifted :226 -> :230
- **price** — 964 (measure/GRID-PARAMS.json :: price.total; docs/GRID-PARAMS.md:43; docs/FETCH-BUDGET-48.md:132)  vs  724 (experiments/ptr-engine/measure/GRID-SHAPE.json :: grid.requests_incl_digests; docs/GRID-SHAPE.md:130) and 1,016 (RUN-A-STAR-2 card description dd2b… only)  → 724 is labelled 'previous' where GRID-PARAMS speaks and stale where GRID-SHAPE speaks; 1,016 has NO artefact — 964+48+4 is the card's own arithmetic
- **remaining** — 3,192 (measure/REQUEST-LEDGER.json :: budget.remaining_raw = 3192; measure/LEDGER-GRID-BASELINE-2.json :: remaining = 3192)  vs  2,228 (measure/GRID-PARAMS.json :: price.remaining_after) / 2,468 (measure/GRID-SHAPE.json :: grid.remaining_after_incl_digests) / 2,176 (RUN-A-STAR-2 card description and title only) / 3,219 (measure/LEDGER-GRID-BASELINE.json :: budget.remaining, frozen at 1101)  → 2,228 re-derives (3192-964); 2,468 re-derives only from the retired 724 price; 2,176 re-derives only from the un-artefacted 1,016; 3,219 is the known-stale frozen baseline, superseded by -2 at 19:04:18Z
- **canary N** — N=12 with answer_verified>=1 and stop_signal_source=finish_reason (measure/CANARY-ERA-B-FIX.json :: gate_recommendation; RUN-A-STAR-2 card description)  vs  N=5 (docs/TRANCHE-CANARY.md:23 'default N = 5'; docs/FETCH-BUDGET-48.md:166 'It runs 5 turns per arm (docs/TRANCHE-CANARY.md:24, N=5)')  → stale: docs/TRANCHE-CANARY.md:140-142 says in the same file that era B's gate cannot be N=5 and must be N=12
- **fixture** — LR-01.v8.json sha256 0804b515… (measure/HARNESS-PIN.json :: files[5]; experiments/ptr-engine/tools/run_a_star.py:36 FIX)  vs  LR-01.v6 (LIVE-SMOKE-8 card 0821ef12-a414-4ce3-90c0-9069c0f7618d, title, 8-turn pointer-stable)  → disagree: the smoke card's fixture and its 24-request allocation predate era B and pool 48; do not copy them into a grid cell
- **pin** — 1f7c67914e5b76680616f08c16708635060a81ab3932c20806e597a5343f3285 (measure/HARNESS-PIN.json :: harness_sha256; docs/HARNESS-PIN.md)  vs  2b4d4808cf906582a378c47c340113022588284fc2b58640e83a95fc6bc23871 (recomputed this audit over HARNESS_FILES+fixture in stage_harness order)  → moved: run_longrun.py 0d581d1f… -> b2003038… at 2026-10-26T19:04:32Z, 14 s after LEDGER-GRID-BASELINE-2 froze; every other harness input still matches its pinned sha

## What this audit cannot prove

- It cannot certify **behaviour**: whether a cell actually terminates in 48 turns, whether the fetch channel closes, or whether the canary returns `shape_ok`. `CELL-PY-BEHAVIOUR-CERTIFY` does that; this audit only compares documents to each other and to the bytes on disk.

- It cannot certify the **runner's edited state**. `run_longrun.py` was written at 2026-10-26T19:04:32Z (sha `b2003038…`), after `HARNESS-PIN.json` (18:59:12Z) and 14 s after `LEDGER-GRID-BASELINE-2.json` (19:04:18Z). A launch that reads a different sha than `b2003038…` is reading a tree this audit did not see; the pin verdict must be recomputed at launch.

- It does not prove `--fetch-rounds-per-arm` is *passed* by any launcher — the flag exists in the runner, but no document shows it in an argv, and the grid relies on the module default of 48.

- It cannot resolve whether 4 warm-ups are 4 requests or 8-token free; the 1,016 price assumes 4 billed warm-ups and no artefact states that.

