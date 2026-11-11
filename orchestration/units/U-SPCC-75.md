# U-SPCC-75 — the remaining `--dry-run` call sites: two fixed, one already safe, one live hazard named

**Status:** DONE for the test call sites. One **live** hazard found outside the slice and recorded as
a decision, not fixed.

## Why

`U-SPCC-73`'s `next_unit_hint` named three `--dry-run` call sites that pass no `--preview-root`:
`test_cell_gates.py:322`, `test_tool_channel2.py:289`, `test_wire_client.py:348`. The question was
whether any of them can write the **tracked** `experiments/ptr-engine/state/previews/<TASK>/` tree.

## Every call site, and the verdict

| Site | Kind | Writes tracked previews? | Action |
|---|---|---|---|
| `test_tool_channel2.py:289` (`assertion_e_tools_off_identical`) | subprocess `run_longrun.py --dry-run` | **yes** | **changed** — `--preview-root <tmp>/previews` on the "after" argv only (the pre-fix baseline script has no such flag and hardcodes `/tmp/longrun-previews`), plus `--temperature 0`, which the current runner requires and the baseline does not accept |
| `test_wire_client.py:348` (`case_e`) | `R.main(["--dry-run", …])` | no (stub) | **changed** — the stub was `lambda cfg, fixture, cells: 0` while `main` dispatches `run_dry(cfg, fixture, cells, root=cfg.preview_root)` (`run_longrun.py:4700`), a latent `TypeError`; the stub now takes `root=None` and the argv names a temp `--preview-root` |
| `test_cell_gates.py:322` (`check_dry_run_touches_no_network`) | `cell.main(["--dry-run", …])` | **no** | **unchanged, already safe** — it drives `cell.py`, which has no preview write (`grep -n preview cell.py` → one comment at `:2358`), and `cell.py --dry-run` skips `stage_budget` (`cell.py:2352`), the only place `cell.py` spawns `run_longrun.py --dry-run` (`cell.py:411`) |
| `test_dry_turn_scope.py:91`, `test_wall_key.py:157` | subprocess / `R.main` | no | unchanged — already pass `--preview-root` (controls) |
| `test_preview_preservation.py:60` | `R.run_dry(..., root=root)` | no | unchanged — already passes `root=` |
| `test_arm_d_requires_tools.py:183,205`, `test_runner_prereg_gate.py:116`, `test_claim_rows.py:93`, `test_cap_gate.py:291`, `test_runaway_policy.py:120`, `test_stop_reason_producers.py:285`, `test_guards.py:240`, `test_projection_calibration.py:65` | live `R.main` / subprocess / `cell.py` | no | unchanged — none passes `--dry-run`, so `run_dry` is never reached; the two that drive `cell.py` live point `CELL_RUNNER_PATH` at a fake runner, so `stage_budget`'s spawn never reaches `run_longrun.py` |

## Two further tracked-tree writes in the same file, fixed

`assertion_e` also wrote its manifests to `experiments/ptr-engine/longrun/manifests/v4tools2-proof-off-{before,after}.json`
— **tracked** evidence listed in `fixtures-spec/LR-01.spec.json`, whose `created_utc` header changed on
every run (`WIRE-CLIENT.json` records the same dirt). The manifest path now points into the test's
tmpdir; nothing reads the file back.

`assertion_c` and `assertion_d` passed `run_id="offline"` with `rep=1`, which the gen-7 guard
`assert_repeat_identity` (`run_longrun.py:2718`) refuses: `repeat-identity: rep=1 not present in
run_id='offline'`. Both now use `offline-r1`. This was **red at HEAD** — proved by restoring the HEAD
copy of the file and re-running it, which failed with the identical message.

## Red → green, measured

The preview claim, measured directly rather than through the test (the test's stdout comparison is red
at HEAD for an unrelated reason, see below):

```
# RED — no --preview-root
run_longrun.py --fixture tasks-v4/runtime-v4/LR-01.v4.json --arms pointer-stable --dry-run \
  --manifest-path /tmp/red-proof.json --temperature 0
git status --porcelain experiments/ptr-engine/state/previews/
 M experiments/ptr-engine/state/previews/LR-01/pointer-stable/turn-01.json
 M experiments/ptr-engine/state/previews/LR-01/pointer-stable/turn-02.json
 M experiments/ptr-engine/state/previews/LR-01/pointer-stable/turn-03.json

# GREEN — with --preview-root /tmp/pv-green
git status --porcelain experiments/ptr-engine/state/previews/
(empty)
```

The three files were restored **forward** from `HEAD` (`git show HEAD:<path> > <path>`); `git checkout --`
is blocked by this workspace's policy.

## Tests

```
TMPDIR=/home/zer0null/tmp-pytest .venv/bin/python -m pytest -q \
  test_cell_gates.py test_wire_client.py test_dry_turn_scope.py test_wall_key.py test_preview_preservation.py
→ 38 passed, 7 subtests passed in 2.70s
```

`test_tool_channel2.py` is a **script**, not a pytest module (`pytest` collects nothing from it). Run
directly it now reaches `assertion_d` and stops there on the cap gate:
`cap-gate: allocation=50 cap=4320 reserve=0 spent_at_start=10215 …` → `rc=4`. That is the over-budget
fact (§6 item 10), not this unit's change: the gate counts the corpus plus the run's own 48 synthetic
rows. `assertion_e`'s stdout comparison is also red at HEAD — the pre-fix baseline
`manifests/v4tools2-baseline-pre.py` predates the `TREATMENT REACHABILITY` block and the current prompt
bodies — which is why the preview claim was measured directly above.

## The live hazard this audit found (not fixed — a decision)

`experiments/ptr-engine/longrun/cell.py:411` builds
`argv = [sys.executable, RUNNER, "--dry-run", "--fixture", args.fixture, "--arms", args.arm, "--reps", str(args.reps)]`
with **no** `--preview-root`. `stage_budget` runs on every **live** cell, so every live cell overwrites
the tracked `state/previews/<task>/<arm>/turn-*.json` for its own task and arm. This is the same defect
class as `U-SPCC-73`, one layer up, and it is not a test: it is the production path.

Where a live cell's previews should go is an evidence-policy question, so it is recorded as §6 item 13
with a recommended default (a run-scoped directory under `state/`, which is gitignored) rather than
changed here.

## Commit

See `orchestration/handoffs/U-SPCC-75.json`.
