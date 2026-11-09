# UNIT WIRE-GATES — one entry point, one refusal surface

**Status:** done. **Zero inference requests, zero network, no live cell, no `git`.**
Upstream cards `a2c4508e` (REQUEST-LEDGER), `c0c7d1c8` (PROJECTION-CALIBRATION) and
`97788db8` (PREREG-ARM-RUN) all settled `done` with usable artefacts; nothing was left
partial.

## Problem

Three offline cards each proved, in isolation, a condition under which a live cell may
spend a request: the ledger's cap, the calibrated projection, and the frozen prereg
(PARM-1). **Nothing joined them.** `cell.py` would start a 60-turn live cell having
consulted none of the three, so the gating the batch built was documentation rather than
enforcement.

## What changed

`experiments/ptr-engine/longrun/cell.py` — a preflight gate chain (G1, G2, G3) used by
every live path, after the budget stage and before `stage_run`:

- **G1 ledger cap** — `turns × arms × reps` + fetch follow-up allowance
  (`ceil(n × 68/801)`, measured from the ledger's own corpus) must fit the remaining
  quota. The decision comes from `request_ledger.build_report(...)` over the row files the
  artefact lists, with the artefact's `cap`/`reserve`; the refusal reuses the ledger's
  `EXIT_OVER` (**4**). No second accounting.
- **G2 projection** — consumes `PROJECTION.json` (per-turn 60 s default from the artefact,
  `--projected-from` p90 override); refuse past `--max-wall` with **exit 8**, quoting
  projected and allowed seconds. `--turn-wall-cap` untouched.
- **G3 prereg** — `n = turns × reps` must satisfy PARM-1 for the claim the cell will state:
  H1 needs `n ≥ 60` (imported from `analyze_stats.min_n_for(0.95)`), H3 needs ≥ 8 of the 12
  checkpoints, H2 needs `n ≥ 1`. A cell declaring no hypothesis is refused (**exit 2**).
- **One refusal format** — `gate · computed · limit · artefact (sha256) · the exact flag`.
- **`--dry-run`** — prints all three verdicts with their numbers plus what the run would
  cost, then exits 0 having spawned no runner and opened no socket.
- **Manifest** — `cell-<arm>-<stamp>.gates.json` (written *before* the run) plus
  `record["gates"]` and a `## gate chain` markdown section carry every verdict and every
  artefact digest the gates consulted.

## Exit codes (final, distinct)

`0` ok · `2` preflight/harness/G3 · `3` budget · `4` the ledger's cap refusal (G1) ·
`5` runner crash · `6` runaway abort · `7` record · `8` projection (G2) ·
`9` grader/analyser disagreement · `10` grade · `11` analyse.

One renumber, stated: `5` and `6` were grade/analyse; `run_longrun.py` already returns 5
for a crash and 6 for a runaway abort and collapsing them was the defect, so grade and
analyse moved to 10 and 11. The table is in the module docstring and in
[`docs/GATE-CHAIN.md`](../../docs/GATE-CHAIN.md).

## Evidence

- `python3 -m unittest discover -s experiments/ptr-engine/longrun/tests -p 'test_cell_gates.py'`
  → **9/9 OK** (G1 allow+refuse, G2 allow+refuse, G3 H1@60 allow / H1@48 refuse / none
  refuse, dry-run no-network, red→green for all three).
- Neighbours unchanged: `test_cell.py` **7/7 OK**, `test_projection_calibration.py`
  **4/4**, `test_guards.py` **6/6 GREEN**.
- Red→green: `RED G1 … got 10`, `RED G2 … got 10`, `RED G3 … got 10` — exit 10 is the
  grade refusal reached only because the neutered gate let the runner run; `cell.py`
  restored byte-identically (asserted).
- Live-path smoke with a fake runner and a fake ledger: manifest written with 3 verdicts
  and 3 artefact digests before the runner was invoked.

## Assumption recorded

`--hypothesis` defaults to PARM-1's `primary` hypothesis (H2) instead of being mandatory,
because `experiments/ptr-engine/longrun/tests/test_projection_calibration.py` (a, c) and `experiments/ptr-engine/longrun/tests/test_guards.py` (d) drive
live paths without it and assert the runner is reached; those files belong to other cards.
An explicitly declared `none` is still refused, and the manifest records the default as
`default:PARM-1.primary` so the choice is visible rather than implied.

## Not done here

The runner's **per-turn** ledger call (`WIRE-CAP-GATE`) remains open: G1 is a preflight
decision on the cell's projected cost, not a per-request interlock.
