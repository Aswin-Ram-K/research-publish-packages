# GATE-OVERRIDE-FIX

**Purpose.** Close the two remaining ways a live run gets past the gate chain in
`experiments/ptr-engine/longrun/cell.py`, and write down the dry-run exit-code contract
the attack recorded as a gap rather than a bypass.

**Origin.** `orchestration/handoffs/V-GATE-CHAIN-2.json` (independent attack): four
original bypasses CLOSED, one survives — `--projected-turn-wall -1 --max-wall 1 --budget
600` printed `projected_wall~=-12s … source=flag` and then **invoked the runner** (LIVE
spawn observed twice). Root cause: `projected_turn_wall()` did `float(explicit)` with no
positivity check while `eval_gate_projection` refused a non-positive ceiling. The attack
also observed two concurrent cells colliding on one manifest filename (second-resolution
stamp + default out-dir `measure/`), and recorded `--dry-run`'s exit-0-with-WOULD-REFUSE
as contract divergence R2.

**Fixes in `cell.py`.**

- F1 — `projected_turn_wall()`: a `--projected-turn-wall` that is not finite and `> 0`
  now raises G2's refusal with exit **8** and the five-fact message (`_projection_refusal`):
  computed `--projected-turn-wall=<v> s`, limit `a positive per-turn ceiling (> 0 s)`,
  artefact + sha256, flag `--projected-turn-wall`, consequence "G2 projection cannot price
  a turn and must not be switched off by an override". The `--projected-from` row-file path
  gets the same rule: a file whose wall rows all price at `<= 0` (p90 `<= 0`) refuses 8
  instead of falling back; a file with *no* wall row at all stays a bad argument (exit 2,
  unchanged — `test_projection_calibration` pins that). A positive value equal to the
  projection still passes (boundary allow).
- F2 — `gate_manifest_path()` + `write_gate_manifest()`: the manifest name now carries the
  pid and a per-process serial (`cell-<arm>-<stamp>-p<pid>-<serial>.gates.json`) and the
  file is created with `O_EXCL`, advancing the serial on collision. Two runs in one second
  can no longer share a path, so no run overwrites another run's gate verdicts. The
  payload is still built from the same `gates` list the runner is gated on.
- F3 — dry-run contract, documented in `docs/GATE-CHAIN.md` §7: `--dry-run` **keeps**
  exit 0 even when a gate would refuse (it authorises nothing; a non-zero code would
  collide with the live refusal codes), so **callers MUST parse** the `WOULD-REFUSE`
  verdict lines or the final `N of 3 gate(s) would refuse` count and never read exit 0 as
  "the gates allow". The final printed line says exactly that, and
  `test_d_dry_run_contract_matches_the_document` asserts both the code and the document
  sentence.

**Bound.** 40 tool calls; offline; zero inference requests; no network; no writes outside
the declared paths; guards only strengthened, never relaxed to make a test pass.

**Write paths.** `experiments/ptr-engine/longrun/cell.py`,
`experiments/ptr-engine/longrun/tests/test_gate_override.py`, `docs/GATE-CHAIN.md`,
`orchestration/units/GATE-OVERRIDE-FIX.md`,
`orchestration/handoffs/GATE-OVERRIDE-FIX.json`.
(`experiments/ptr-engine/longrun/tests/test_cell_gates.py` was left untouched: the new
guards live in a new suite so the existing 15/15 keeps its exact contract.)

**Deliverable.** `orchestration/handoffs/GATE-OVERRIDE-FIX.json`.
