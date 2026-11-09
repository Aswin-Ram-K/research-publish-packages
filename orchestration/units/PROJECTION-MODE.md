# PROJECTION-MODE — refuse in the unsafe direction, per thinking mode

**Card:** 7864d1d7-8ae8-4750-86c5-9c02b24c3105 · execution 5bb51dde-8bd6-4443-9b2b-0c564f2f7333
**Bound:** <=26 tool calls, 0 inference requests. OFFLINE: no network, no git, no live cell.

## Why
`V-INSTRUMENTS` recomputed PROJECTION-CALIBRATION at delta 0 (4 dp): the calibration is
right, the consumption is wrong. `--projected-from` defaults to `None` and no non-test
caller passes it, so pooled 60 s/turn priced every cell:
thinking off/absent -> 60 turns projected 3,600 s vs measured p50 2.9 s/turn (~174 s,
~20x over, SAFE); thinking auto/on -> 60 turns projected 3,600 s, ADMITTED at
`--max-wall 3600`, against measured p50 13,092 s (3.6x) / p90 40,962 s (11.4x) — and
PROJECTION.json already marks 60 turns at 25,662 s `admitted_under_3600=false`.
`--projected-turn-wall 180` reproduced `projected=10800` silently: the repair was a
default change, not an invariant.

## What changed
1. **Per-mode defaults** consumed from the artefact: `defaults.projected_turn_wall_s_by_mode`
   and `defaults.projected_turn_wall_s_p90_by_mode`; `--projected-from p90` selects the
   tail. Legacy `defaults.projected_turn_wall_s` stays readable and is NOT read.
   `cell.py --thinking` (absent|off|auto|on) now drives BOTH the projection and the
   runner payload (`--thinking` is passed to run_longrun.py; absent = off, the runner's
   own default).
2. **Refuse in the unsafe direction:** unknown spelling and any mode missing from the
   artefact table -> exit 8, naming the mode and the allowed spellings; no pooled fallback.
3. **180 s regression is loud:** `--projected-turn-wall` differing from the mode's
   calibrated p50 prints `OVERRIDE …` and writes gate-manifest field
   `projection_override = {value, mode, calibrated_s, direction, reason_required, warning}`.
   Chosen over a hard p50 floor (see docs/PROJECTION.md): a conservative measured override
   stays expressible, and the manifest makes an optimistic one auditable.
4. **Boundary unchanged:** `projected == max_wall` admitted, `> max_wall` refused (exit 8),
   five-field refusal surface intact.

## Assumption (recorded)
`off`/`absent` keeps 60 s/turn rather than its measured 2.9 s p50: 60 s is the calibration's
deliberate conservative figure (above the measured off p90 of 38.1 s), it is the SAFE
direction, and moving it would break the frozen boundary `48 x 60 = 2880` pinned by
`test_projection_calibration.py` (a file this card may not edit). The unsafe regime is
auto/on and that is where the mode-specific figure bites.

## Evidence
- new: `experiments/ptr-engine/longrun/tests/test_projection_modes.py` 8/8 passed.
- red: neutering `_mode_wall` to `return 60.0` -> thinking-auto 60-turn test FAILED
  (`projected_wall~=3600s`, `assert 10 == 8`); restored (sha256 identical) -> 8/8 passed.
- neighbours all exit 0: test_cell_gates 9 passed + 3 subtests; test_projection_calibration
  1 passed; test_cell 7 passed + 6 subtests; test_guards 1 passed.
