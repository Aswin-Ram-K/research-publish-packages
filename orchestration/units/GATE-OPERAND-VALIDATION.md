# UNIT GATE-OPERAND-VALIDATION

**Status:** done · **Requests:** 0 · **cell.py sha256:** `6b0ca83a209433479e119323bc20a84588196cd002e72ba3639162455aea8b4e` · **HEAD:** `f17663d1fed0162a7dc3c5a0a58d372c710974c3`

## Purpose
`V-GATE-CHAIN-3` closed PASS while its attack asserted six surviving bypasses as pass
conditions and left G3 untouched. This unit makes the three gates refuse the operands
they read, with expectations derived from the REQUIREMENT, not from the code's output.

## Operands, and whether each was validated before
| gate | operand | source | pre-fix decision | validated before? |
|---|---|---|---|---|
| G1 | `--turns`, `--reps`, arm count | flag/default | `int(args.turns or 0)` — 0/negative spent as written | no |
| G1 | `budget.cap` | artefact | `int(budget.get("cap") or 0)` — `cap=0` falsy, bypassed (F8) | no |
| G1 | `budget.reserve` | artefact/default | subtracted raw, never checked against cap | no |
| G1 | `--fetch-followup-allowance` | flag/derived | `max(0, int(x))` — negatives clamped to 0, admitted | no |
| G2 | `--max-wall` | flag | `ok = max_wall > 0 and projected <= max_wall` — `1e308`/`inf` admitted (F1) | no |
| G2 | `--turn-wall-cap` | flag | `float()` only — `0` handed to the runner as an abort threshold (F8) | no |
| G2 | `--projected-turn-wall` / p90 | flag/rows | only `finite > 0` — `1e-9` admitted, projection rounded to 0 (F2) | partly |
| G2 | per-mode figure | artefact | `float(table[mode])`, never checked — `0` admitted (F3) | no |
| G2 | request count | budget/`turns*reps` | `0`/negative projected below the ceiling | no |
| G3 | `--hypothesis` | flag | silence fell into the H3 branch and ran | no |
| G3 | `--turns`, `--reps` | flag | H3 branch `ok = checkpoints >= 8` ignored n (F4/F5) | no |
| G3 | fixture checkpoints | fixture | counted, never type-checked | no |

## What changed (`experiments/ptr-engine/longrun/cell.py`, this card's file alone)
- One pure validator per gate: `validate_g1`, `validate_g2`, `validate_g3`, plus
  `_num_facts` (finiteness / integrality / sign / bound, returning `(ok, fact)` with the
  operand, the limit and the flag that changes the answer) and `_refuse_from_operands`
  (one refusal surface on the existing verdict).
- Every evaluator routes through its validator; exit codes unchanged (2 usage/artefact
  shape, 4 ledger, 8 projection, 12 prereg). `_enforce` now honours a verdict's own exit
  code, so a usage error stays 2.
- The artefact's own per-mode figure, the p90 of a rows file and the
  `--projected-turn-wall` override are all validated (F3 closed). `--max-wall` keeps its
  pinned D1 non-positive branch as the sign refusal (documented wording preserved).
- Bounds: cap <= 1,000,000; turns <= 100,000; reps <= 10,000; max-wall <= 30 days;
  per-turn wall and turn-wall-cap <= 24 h (turn-wall-cap >= 1 s); projection >= 1 s.

## Attack and evidence
`experiments/ptr-engine/tools/gate_attack.py` — a table of
`{gate, operand, via, value, expected}` over `0, -1, -48, 1e-9, 1e308, inf, nan,
"abc", "", None` for every operand, plus permissive-sibling rows and the six F cases
end-to-end through `cell.main()`.

| gate | rows | hostile | admitted/crashed before | admitted after |
|---|---|---|---|---|
| G1 | 65 | 60 | 39 | 0 |
| G2 | 66 | 61 | 33 | 0 |
| G3 | 50 | 46 | 28 | 0 |

Six named bypasses, end-to-end (expected = requirement; live spawns via the counted
`cell._run`):

| case | argv | exit | live spawns |
|---|---|---|---|
| F1 `B2_max_wall_1e308_allows` | `--max-wall 1e308` | 8 | 0 |
| F2 `G_tiny_override_allows` | `--projected-turn-wall 1e-9 --max-wall 1` | 8 | 0 |
| F3 `H_artefact_zero_allows` | artefact per-mode figure 0 | 8 | 0 |
| F4 `D_turns0_H3_runs_full` | `--turns 0 --hypothesis H3` | 4 (G1 first; G3 alone = 12) | 0 |
| F5 `D2_turns_neg_runs_full` | `--turns -1 --hypothesis H3` | 4 (G1 first; G3 alone = 12) | 0 |
| F8 `I2b_cap_zero_passed_to_runner` | `--turn-wall-cap 0` | 8 | 0 |

Red→green is quoted per case in `measure/GATE-OPERAND-VALIDATION.json` (`red_green`),
and the mutation red→green harness in `experiments/ptr-engine/longrun/tests/test_cell_gates.py` still passes on the
G1/G2/G3 anchors. `experiments/ptr-engine/longrun/tests/test_gate_operand_validation.py` (9 tests) fails if any hostile
value is admitted, if a refusing gate spawns, or if a gate code is renumbered.

## Exit table reconciliation
`exit_codes.EXIT_TABLE` declares 0-12; `docs/GATE-CHAIN.md` §2 documents 0, 2-12. The
gate-chain codes {2, 3, 4, 8, 12} agree everywhere (table, doc, docstrings, source
scan). `1 = internal-error` is declared in `exit_codes.py` but is not a gate code and is
absent from the doc table; it is recorded here and deliberately **not** renumbered or
edited (docs/GATE-CHAIN.md is not this card's file).

## Not satisfied / limitations
- The `before` column is a RECONSTRUCTION from the quoted pre-fix source lines:
  `cell.py` is untracked at HEAD (`git show HEAD:...` -> "exists on disk, but not in
  HEAD"), so no committed pre-fix copy exists to re-run. Everything in `after` is
  measured.
- `experiments/ptr-engine/longrun/tests/test_guards.py` (3/6) and `experiments/ptr-engine/longrun/tests/test_projection_calibration.py` (3/4) fail in
  checks that spawn `run_longrun.py`, which a concurrent card edited at 12:02; the
  failures are "no request reached the fake server" and a runaway-turn check, both
  external and untouched here.

**Claim:** every gate operand is validated; no hostile numeric value is admitted; no
refusal spawns a runner.
