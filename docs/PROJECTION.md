# PROJECTION.json — which key the gate now reads

**Amendment:** `PROJECTION-MODE` (card 7864d1d7 / execution 5bb51dde). This file records
what `experiments/ptr-engine/longrun/cell.py` consumes; the derivation of the numbers is
still `docs/PROJECTION-CALIBRATION.md` (unchanged).

## The defect this closes

`V-INSTRUMENTS` recomputed the calibration and got **delta 0 at 4 dp** on every figure: the
calibration was right. The gate consumed it wrongly. `--projected-from` defaulted to
`None` and no non-test caller passed it, so one **pooled 60 s/turn** priced every cell
regardless of thinking mode:

| thinking mode | measured p50 | measured p90 | old projection, 60 turns | real wall at p50 |
|---|---|---|---|---|
| off / absent | 2.9 s | 38.1 s | 3,600 s | ≈174 s (over-projected ≈20×, safe) |
| auto / on | 218.2 s | 682.7 s | 3,600 s (**admitted** at `--max-wall 3600`) | **13,092 s** (3.6× under), p90 40,962 s (11.4×) |

Over-projecting a thinking-off cell wastes nothing. **Under**-projecting a thinking-auto
cell admits an experiment whose own calibration says it will overrun — that is the unsafe
direction, and it is what this changes.

## Keys

- `defaults.projected_turn_wall_s_by_mode` — **read by the code** for the expected turn
  (`p50` column): `{absent: 60.0, off: 60.0, auto: 218.2, on: 218.2}`.
- `defaults.projected_turn_wall_s_p90_by_mode` — **read by the code** when
  `--projected-from p90` selects the tail: `{absent: 38.1, off: 38.1, auto: 682.7,
  on: 682.7}`.
- `defaults.measured_p50_s_by_mode` / `measured_p90_s_by_mode` — the raw measurements,
  carried for audit only; the gate never multiplies them directly.
- **`defaults.projected_turn_wall_s` (60.0) is LEGACY**: kept readable for one release and
  **no longer read by `cell.py`**. Its `projected_turn_wall_s_status` key says so in-file.

### Why `off` is 60 s and not its 2.9 s p50

Deliberate, and it is the *safe* direction. `docs/PROJECTION-CALIBRATION.md` §3 chose 60 s
as "deliberately conservative — above the p50 of every regime except thinking-on", which
is above the measured off p90 (38.1 s). Lowering off to 2.9 s would *tighten* the guard
but is not this card's defect, and it would break the calibration's own pinned boundary
`48 × 60 = 2880` in `experiments/ptr-engine/longrun/tests/test_projection_calibration.py` — a file this card may not
edit. So `off`/`absent` keeps 60 s and stays over-projected ≈20×: no off cell is refused
that would have been admitted, and no off cell is admitted (at 60 s) that overruns.

## Mode selection (`--thinking`)

`cell.py --thinking` accepts `absent`, `off`, `auto`, `on`. The flag drives **both** the
runner payload (it is now passed straight to `run_longrun.py`, whose own default is `off`
— so `absent` is spelled `off` there) **and** the projection figure. An **unknown spelling
refuses with exit 8**, naming the mode and the allowed spellings; a mode **missing from the
artefact's table** also refuses (exit 8) rather than guessing. There is no silent fallback
to the pooled scalar.

## `--projected-turn-wall` is loud, never silent

An explicit per-turn override no longer reproduces the pre-repair 180 s worst case in
silence. When the flag's value differs from the mode's calibrated p50, the gate prints
`3b/7 projection OVERRIDE …` and writes **`projection_override`** into the gate manifest
(`cell-<arm>-<stamp>.gates.json`):

```json
"projection_override": {"value": 180.0, "mode": "auto", "calibrated_s": 218.2,
                        "direction": "optimistic", "reason_required": true,
                        "warning": "--projected-turn-wall 180.0s overrides …"}
```

**Chosen over** refusing any value below the mode p50 because: (a) an override can be a
*measurement* (a specific prior arm's p90) that the artefact's pooled p50 cannot express,
and a hard p50 floor would forbid it; (b) the unsafe direction is already refused by
`--max-wall` (a 180 s auto cell at 60 turns projects 10,800 s → exit 8) and by the mode
refusals; and (c) `direction` distinguishes `conservative` (above p50, safe) from
`optimistic` (below p50, loud and `reason_required`), so an auditor sees which happened
without the gate silently rewriting the operator's number.

## Boundary

Unchanged and exact: `projected == --max-wall` is **admitted**, `projected > --max-wall`
is **refused** with exit `8`, and the refusal keeps its five fields — gate id, computed
value, limit, artefact (+ sha256), and the flag that would change it.
