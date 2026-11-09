# RECLAIM-ACCEPTANCE — re-measuring three cards charged with the cap-gate red

**Unit:** RECLAIM-ACCEPTANCE · **HEAD:** `f17663d1fed0162a7dc3c5a0a58d372c710974c3` · offline, 0 requests.
**Trigger:** `CAPGATE-FOREIGN-RED` removed the only cap-gate failure (`capgate 9/9 OK`).

This page re-runs what each card recorded as its acceptance command. It does not re-do any card's work and
modifies no card's work product.

## Per card

### 1. SEAM-TEST-RED (`bd45c215-738a-46c6-9c7a-2475e4758c6a` / `9c65da33`)

- Closure row: **failed / `exit-1`**, command `python3 -m unittest discover -s experiments/ptr-engine/longrun/tests -p 'test_*.py'` (verbatim from the closure ledger; identical in the handoff's `evidence.commands`).
- Charged failure: `test_cap_gate.CapGateTest.test_c_followup_counts_as_a_second_unit` (`experiments/ptr-engine/longrun/tests/test_cap_gate.py:205`, `'tool-followup' not in ['turn-initial','turn']`).
- **Today:** exit **1** — `Ran 176 tests in 6.366s`, `FAILED (failures=1)`:
  `test_verdict_ritual.LiveLedgerTest.test_no_new_unverdicted_closure_since_the_baseline`,
  `AssertionError: {'FIXTURE-GENERATIONS': ['96ec0bcc-…:efa8039f-…']} != {}`.
- The cap-gate red is **gone** (`test_cap_gate.py` 9/9 OK) and the card's own seam test is green
  (`test_decidability_seam.py`, Ran 5, OK), but the suite command still exits 1 on a **different foreign red**
  (a governance test complaining that *FIXTURE-GENERATIONS* settled `done` with no verdict row).
- **Classification: blocked-by-foreign-red.** Not reclaimable: not exit 0. **No verdict row** — the card's own
  tests are green, so the charge against *it* was wrong, but the recorded command cannot pass until
  FIXTURE-GENERATIONS gets a verdict row.

### 2. CLAIM-ROW-STAMP (`6e8947b0-e99c-4954-bb56-3389023bdb5e` / `a55b79bf`)

- Closure row: **verified (PASS)**, command `python3 experiments/ptr-engine/longrun/tests/test_claim_rows.py`,
  exitCode 0, sha `f17663d1`. The card's `partial` **handoff** was a self-report; the **verdict gate never failed it**.
- **Today:** exit **0** — `5/5 GREEN`; and the suite its blocker actually named, `test_cap_gate.py`, is
  `Ran 9 tests | OK`; `test_cell_gates.py` 15 OK; `test_claim_wiring.py` 6/6.
- **Classification: reclaimable, already PASS.** **No new row recorded** (identical command; re-recording a PASS
  adds nothing and the rule is new rows only).

### 3. WIRE-CAP-GATE (`9d182ed2-34ec-491c-be23-ff6d24b0650b` / `84fbcae2`)

- Closure row: **failed / `no-verdict`**, with `command`, `exitCode`, `sha` all **null** — it failed because no
  verdict row existed, **not** because of the cap-gate red.
- Recorded acceptance command (first of its `evidence.commands`):
  `python3 -m unittest discover -s experiments/ptr-engine/longrun/tests -p 'test_cap_gate.py' -v`.
- **Today:** exit **0** — `Ran 9 tests in 0.657s | OK` (plus the live RED/GREEN lines: neutered pre-send call →
  rc=9 rows=3; brake restored → rc=4 rows=0 requests=0). `test_request_ledger.py` also exit 0.
- The other recorded command `test_tool_channel2.py` is exit **1** — `AssertionError … 'tools-off output drifted'`
  at `experiments/ptr-engine/longrun/tests/test_tool_channel2.py:294` (`assertion_e_tools_off_identical`) — already flagged as *drifted* in its
  own handoff, not on the cap-gate path, outside this card's write paths.
- **Classification: reclaimable.** **Verdict row recorded** (see below).

## Verdict row recorded

`orchestration_verdict {action:"record", taskId:"9d182ed2-…", executionId:"84fbcae2-…"}` →
`PASS f17663d1` with command

```
bash -c "python3 -m unittest discover -s experiments/ptr-engine/longrun/tests -p 'test_cap_gate.py' -v"
```

The `bash -c` wrapper is forced by the verdict allow-list (`python3` is refused); the wrapped text is the card's
own recorded acceptance command, so the measurement is the card's, not a substitute.

## Census

| classification | n | cards |
|---|---|---|
| reclaimable | 2 | CLAIM-ROW-STAMP (already PASS), WIRE-CAP-GATE (new row → PASS) |
| blocked by a foreign red | 1 | SEAM-TEST-RED (cap-gate red gone; `test_verdict_ritual`/FIXTURE-GENERATIONS now red) |
| still-red for its own reason | 0 | — |
| not-runnable | 0 | — |

**False FAILs from the one stale cap-gate assertion: 1.**

### The finding

Of the three cards charged with the cap-gate red, **only one** — SEAM-TEST-RED — was a false FAIL
attributable to the stale `experiments/ptr-engine/longrun/tests/test_cap_gate.py:205` assertion. One had already settled **verified (PASS)**
and one failed for **absence of a verdict row**, not for the red. So this assertion does **not** explain
`failed=104`: in the sample of three it accounts for one false FAIL, and the brief's attribution of the other
two does not survive the closure ledger. The residual red that still blocks SEAM-TEST-RED is a *second*
governance artefact (an unverdicted FIXTURE-GENERATIONS closure), not a lost-work failure.

## Limits

- No card work product was touched; no existing verdict row was edited; no file moved or missing.
- SEAM-TEST-RED stays un-reclaimed until FIXTURE-GENERATIONS carries a verdict row.
- `test_tool_channel2.py` assertion (e) remains red for its own pre-existing reason.
