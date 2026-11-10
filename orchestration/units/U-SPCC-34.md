# U-SPCC-34 — the SPCC claim namespace: an E1 cell can declare its own claim

## Defect

The runner's claim vocabulary was PARM-1's alone. `longrun/claim_mode.py:97` had
`CLAIM_IDS = ("H1", "H2", "H3")`, and `longrun/cell.py:1550 eval_gate_prereg`
validated every claim against `measure/PREREG-ARM-RUN.json` with PARM-1's
thresholds (H1 p95 TTFT needs n ≥ 60; H2 is a ratio needing n ≥ 1; H3 needs ≥ 8 of
12 checkpoints).

An E1 cell therefore had no legal declaration:

- `--hypothesis smoke` / `plumbing` marks its rows `comparison_eligible: False`, so
  the rows cannot support the preregistered test;
- `--hypothesis H1|H2|H3` would mislabel an SPCC cell as a PARM-1 claim and be
  adjudicated against thresholds that are not E1's.

E1 was blocked on the namespace, not on the model or the budget.

## Fix

- `claim_mode.py`: new `SPCC_CLAIM_IDS = ("E1".."E6")` and
  `ALL_CLAIM_IDS = CLAIM_IDS + SPCC_CLAIM_IDS`. `resolve_claim` accepts the union,
  so `resolve_claim("E1")` returns
  `{"mode": "hypothesis", "claim": "E1", "comparison_eligible": True}` — the same
  shape `resolve_claim("H2")` returns. `CLAIM_IDS` itself is unchanged, so the
  PARM-1 ids keep their exact records. `assert_comparable` accepts E ids as
  comparable claims (an E1 row is not `unknown_claim`). `refusal_message` keeps the
  phrase "three accepted forms" and now names the E ids inside form (3).
- `cell.py`: new `SPCC_PREREG_ARTEFACT` (env `CELL_SPCC_PREREG_ARTEFACT`, default
  `research-seed-concepts/PREREG-SPCC.json`). `eval_gate_prereg` selects the
  artefact by the claim's namespace: `H*` → `PREREG-ARM-RUN.json` (unchanged),
  `E*` → `PREREG-SPCC.json`. `validate_g3` gained an `spcc=` branch that adjudicates
  against the document's own terms: the cell's request allocation `n = turns × reps`
  must lie inside the entry's `request_ceiling` and the fixture must carry at least
  `checkpoints_required` checkpoints. E1 is 200–500 requests over 48 checkpoints.
  `_check_spcc_doc_pin` refuses (exit 2) if `PREREG-SPCC.md` no longer matches the
  companion's `doc_sha256`, so the prose stays the authority.
- `research-seed-concepts/PREREG-SPCC.json`: machine-readable companion transcribed
  from `PREREG-SPCC.md` (E1–E6: claim, design, falsifier, request ceiling,
  checkpoints required, unit of account). E6's ceiling is GPU hours, not requests,
  so its `request_ceiling` is `null` and G3 refuses an E6 request allocation rather
  than inventing a ceiling for it.

No existing gate was weakened: the H path loads the same artefact with the same
thresholds, and an E1 cell is still refused when its allocation or its fixture
cannot support the claim.

## Proof

Red (pre-change `claim_mode.py` + `cell.py` from HEAD, test file copied in):

```
FAILED test_e1_resolves_to_a_comparable_hypothesis_record - claim_mode.ClaimRefusal:
  claim REFUSED: --hypothesis='E1' is not a declaration this run may make. ...
FAILED test_e1_within_ceiling_and_checkpoints_is_accepted - assert False is True
FAILED test_e1_over_its_request_ceiling_is_refused - assert 0 == 600
FAILED test_e1_fixture_below_48_checkpoints_is_refused - KeyError: 'checkpoints_in_fixture'
FAILED test_unknown_e9_is_refused_naming_the_accepted_spellings - assert 'E1' in "..."
9 failed, 3 passed
```

Green:

```
12 passed in 0.05s
```

Acceptance set (`test_spcc_claim.py`, `test_claim_rows.py`, `test_cap_gate.py`,
`test_capgate_label.py`): `35 passed in 1.81s`.

Neighbouring claim/gate tests (`test_claim_mode.py`, `test_claim_wiring.py`,
`test_cell_gates.py`, `test_gate_messages.py`, `test_verdict_payload.py`,
`test_gate_operand_validation.py`): `60 passed, 7 subtests passed`.

`python3 tools/doc_check.py` → `exit=0`.

Full `longrun/tests` run: `850 passed, 7 failed`. All 7 are pre-existing corpus/state
drift in the shared checkout (untracked `measure/rows-*-spcc-*.jsonl`, new
`orchestration/handoffs/*.json`, a stale `measure/STOP-REASON.json`, and
`test_layers_compiler::test_compaction` on untouched `ptr_engine/layers.py`); none of
those files import `claim_mode` or `cell`.

## What this does not do

It does not run E1. The live server is at 4,113 requests remaining against a 12,094
cap and this unit spent none.
