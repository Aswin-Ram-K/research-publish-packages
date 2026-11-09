# UNIT `HANDOFF-BASELINE-REGEN` — make the handoff-shape guard green by freezing 13 pre-existing gaps

**Status: BLOCKED** (deliverables written; the last step requires an edit the unit forbids).
Date: 2026-10-26T13:20-05:00 · HEAD `f17663d1fed0162a7dc3c5a0a58d372c710974c3` · offline, zero inference requests.

## Purpose

`VERDICT-ALLOWLIST-WRAP` reported `tests/test_orchestration_handoffs.py::test_no_new_contract_key_gaps`
red at HEAD and named 13 handoffs as new verifier-shape gaps. Task: reproduce it, prove per-file
pre-existence from the filesystem, freeze a dated baseline, prove green and red, never touch the test.

## Hard bound

24 tool calls; journal first; handoff by call 6; verdict row before the handoff write.
Never `ask_user_question`. Offline.

## Declared write paths

`state/logs/handoff-shape-baseline-2026-10-26.json` · `docs/HANDOFF-SHAPE-BASELINE.md` ·
`orchestration/units/HANDOFF-BASELINE-REGEN.md` · `orchestration/handoffs/HANDOFF-BASELINE-REGEN.json` ·
`orchestration/journals/HANDOFF-BASELINE-REGEN.jsonl`. Nothing else in the workspace was written; the
red-direction fixture lived only in a `/tmp` copy of the tree.

## Kill condition (hit)

"If the honest fix requires a change to `tests/test_orchestration_handoffs.py`, STOP and report
`blocked`." It does — see below.

## Measurement

* Reproduced: `1 failed, 12 passed`; `test_no_new_contract_key_gaps` names exactly the 13 files.
* All 13 are **complete under the unit contract (7/7)**. The only key each lacks is `checks`
  (10 also lack `overall`), which only the *verifier* contract requires.
* `classify()` routes all 13 to the verifier contract on the filename prefix `V`; 3 also carry
  `overall`. The test's premise "43/43 V\* files are verifier verdicts" is false today:
  1085 handoffs, 147 `V*`, 14 of them complete unit handoffs without `checks`.
* So the 13 are 13 **false positives of the classifier**, not 13 recorded defects. Freezing them as
  "missing `checks`" would enshrine a gap no unit handoff ever owed.

## Pre-existence

* vs the reporting unit (`VERDICT-ALLOWLIST-WRAP`, 2026-10-26T13:18:18): **12 of 13 predate it**;
  the 13th is that unit's own handoff.
* vs the last shape freeze (`state/logs/U8.18/verifier_shape_baseline.json`, 2026-10-24T08:05:56):
  **0 of 13 predate it** — all were created 2026-10-26, after the freeze, so on the card's own rule
  they are not freeze-eligible as history.
* mtimes cross-checked against each handoff's first/last journal line where a journal exists.

## Proofs

| direction | command | exit | result |
|---|---|---|---|
| green | `/tmp` copy + one loader line for the dated record: `.venv/bin/python -m pytest tests/test_orchestration_handoffs.py -q` | **0** | 13 passed |
| red | same copy + 14th handoff `V9.99-REGRESSION-PROBE.json` (same shape), `/tmp` only | **1** | names exactly `V9.99-REGRESSION-PROBE.json: ['overall','checks']`; the 13 stay exempt |
| workspace test integrity | `sha256sum tests/test_orchestration_handoffs.py` before/after | — | `9071255e…d37adb065`, unchanged |

## Blocker

`frozen_baselines()` reads exactly two hash-pinned paths, caches them in `_BASELINES`, and resolves
no directory, glob or third file. The recorded baseline therefore cannot reach the guard without one
of: (1) 13 entries added to `state/logs/U8.18/verifier_shape_baseline.json` **plus** its
`VERIFIER_BASELINE_SHA256` pin updated in the test, or (2) a one-line loader addition in the test.
Both edit `tests/test_orchestration_handoffs.py`, which this unit may not do. Rejected third route: a
`tests/conftest.py` hook pre-populating `_BASELINES` — same exemption, hidden from the guard's text.

## Handed forward

The dated record carries `applied: false` and the exact loader line, so a unit permitted to change the
guard needs no re-derivation. The durable fix is `classify()`: a `V*` handoff carrying the 7 unit keys
and no verdict keys is a unit handoff. Freezing alone does not hold — every future `V*`/`overall`
handoff becomes the 14th, which the red proof demonstrates.
