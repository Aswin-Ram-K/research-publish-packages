# RUNNER-WALL-KEY — which wall key the runner reads

**Verdict: PASS.** The runner reads the **per-arm** wall for every arm, on every path it
runs. Two provenance defects did read the top-level key and were fixed
(`run_longrun.py`), with a red→green that fails on the wrong wall. Offline, 0 requests.

## Resolution order (traced, not assumed)

| # | source | `file:line` | expression |
|---|---|---|---|
| 1 | per-arm | `experiments/ptr-engine/longrun/run_longrun.py:1186-1195` | `by_arm = fixture.get("wall_tokens_by_arm") or {}` → `return int(by_arm[arm])` |
| 2 | top-level (legacy only) | `run_longrun.py:1197` | `return int(fixture["wall_tokens"])` — reached **only** when no non-empty `wall_tokens_by_arm` is declared |
| 3 | schema default | **none** on this path | `adaptation.wall_tokens_default=65536` is read only by `adapt_v2.py:139-143`, `adapt_v3.py:156-160`, `adapt_fixture.py:190-194` for old `long_run.wall_tokens` fixtures; `run_longrun.py` never consults it |
| 4 | hard-coded constant | **none** for tokens | `DEFAULT_WALL_TOKENS` lives only in those legacy adapters |

Before the fix, step 1 fell through to step 2 **silently** for any arm missing from a
declared `wall_tokens_by_arm` block — that was the F3 trap.

## Per-path reads

* `run_longrun.py:1006` `self.wall_tokens = int(fixture["wall_tokens"])` — the `fixture`
  handed to `Planner` is already arm-substituted (`:1217` dry run, `:2176` live via
  `:2126`), so the planner reads the **per-arm** value.
* `run_longrun.py:1077` grow/FIFO: `while len(parts) > 1 and est_tokens("\n\n".join(parts + [current]), self.bpt) > self.wall_tokens:`
* `run_longrun.py:1094` compact: `if t > 1 and est_tokens(window, self.bpt) > self.wall_tokens:`
* `run_longrun.py:1237` `"wall_tokens": int(fx["wall_tokens"])` in `treatment_fire_turns`
  (the launch precondition, per-arm `fx`).
* `run_longrun.py:1319-1332` `expected_digests` → `fixture_for_arm(fixture, "transcript-compact")`.
* `run_longrun.py:1377/1389` `build_manifest` records `design_cap_tokens` / `fixture.wall_tokens`
  from whatever fixture it is handed — correct live, **wrong on the dry-run path** before the fix.
* `cell.py` reads **none** of `wall_tokens` / `wall_tokens_by_arm` / `wall_tokens_basis`; it
  only handles the wall **clock** and passes `--fixture` straight through (`cell.py:318`
  dry run, `cell.py:1460` live).

Residual top-level reads **outside** the runner's wall (reported, not changed):
`score_longrun.py:337` (`fixture.get("wall_tokens")`, grader provenance),
`project_wallclock.py:164` (projection input), and the three legacy adapters.

## Proof — discriminating fixture (top 3838 vs per-arm 38380, 10×)

```
arm,key_read,wall_used,first_fire_turn
transcript-grow,wall_tokens_by_arm[transcript-grow],38380,None (no fire in 48)
transcript-compact,wall_tokens_by_arm[transcript-compact],38380,None (no fire in 48)
lease-reopen,wall_tokens_by_arm[lease-reopen],38380,None (lease step T23)
pointer-stable,wall_tokens_by_arm[pointer-stable],38380,None (prefix change T2)
```

## Proof — v8 as shipped (top 3838, per-arm 10616)

```
arm,key_read,wall_used,first_fire_turn
transcript-grow,wall_tokens_by_arm[transcript-grow],10616,21
transcript-compact,wall_tokens_by_arm[transcript-compact],10616,21
lease-reopen,wall_tokens_by_arm[lease-reopen],10616,None (lease step T23)
pointer-stable,wall_tokens_by_arm[pointer-stable],10616,None (prefix change T2)
```

Matches `FIXTURE-TREATMENTS`' dry run: grow T21, compact T21, lease T23.

Counterfactual with the top-level key alone: grow **T2**, compact **T2** — the trap.

## Fix (all inside `run_longrun.py`)

1. `wall_for_arm` — a declared `wall_tokens_by_arm` is **authoritative**; an arm missing
   from it raises `FixtureError` instead of returning 3838. Legacy fixtures with no per-arm
   block still read the top-level key.
2. Dry-run `build_manifest` now gets `fixture_for_arm(fixture, arm)`. Before,
   `manifests/dryrun-LR-01-lease-reopen-r1.json` froze `design_cap_tokens=3838` and
   `fixture.wall_tokens=3838` for a cell the dry run built at 10616.
3. `load_fixture` accepts a fixture that declares **only** `wall_tokens_by_arm`.
4. `main` preflights every requested arm's wall before freezing a manifest (exit 2,
   `FIXTURE ERROR:`) instead of running an arm at the wrong wall.

## Red → green

Red (before the fix):
```
AssertionError: wall_for_arm silently fell back to the top-level 3838 for transcript-grow;
the arm would fire the wall at T2 instead of T21
('/tmp/.../dryrun-LR-01-transcript-compact-r1.json', {'design_cap_tokens': 3838, ...})
FixtureError: fixture .../byarm-only.json missing required key 'wall_tokens'
```
Green (after): `6/6 PASS`; with `test_treatments_fire.py` + `test_arm_treatments.py`
`22 passed`.

## Regression test that catches a future fallback

`experiments/ptr-engine/longrun/tests/test_wall_key.py`:
`test_arm_missing_from_a_declared_by_arm_block_does_not_fall_back_to_3838` (a future
fallback quotes 3838 in the failure), plus the 10× discriminator and the
dry-run-manifest provenance test (`design_cap_tokens=3838` fails it).

## Recommendation for the top-level `wall_tokens: 3838`

**Keep it in `LR-01.v8.json`** — the fixture is the audited artefact and must not be
edited — as an explicit "below-first-prompt, do not use" legacy marker, enforced by
**refusal** rather than by documentation: a declared `wall_tokens_by_arm` is authoritative
and an arm missing from it now refuses. Future fixtures (v9+) should omit the top-level key
entirely, which the loader now accepts.

**Would the grid have measured the treatments as designed, or the wall at turn 2?**
As designed — every arm runs at 10616, so grow/compact diverge at T21 and the lease at T23;
the turn-2 collapse would only have happened if the per-arm block were absent or silently
bypassed, which is exactly what is now refused.
