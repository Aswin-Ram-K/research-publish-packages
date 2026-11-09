# LEDGER-CONSERVATIVE — withhold the duplicate deduction until the rule is sound

**Card:** `f505519f-b865-451a-8f7f-7f3cee533cfd` · **execution:** `4d03e65b-0660-4427-8543-1088cacf2136`
**Automated, offline:** no human, zero inference requests, nothing spent.

## Purpose
`V-DUPLICATE-RULE` (`f9654fff`) returned `overall: fail`. Two of five attacks survived, but attack 3 is
sound evidence that the rule is unsound as a request-identity test: `content_sha256` is a hash of the
assistant's `content` (`run_longrun.py:1555`; 869/869 rows re-measured offline satisfy
`content_sha256 == sha256(content)`), so two different requests returning the same text collapse into one
row and the 30-request deduction **understates** spend. Deducting on an unsound rule is forbidden here.

## What this unit changed (publish + spend surface, never a measurement)
1. `measure/REQUEST-LEDGER.json` now publishes `requests: 1101`, `remaining: 3219`. The 1,071 figure is
   kept under `diagnostic` (`deducted: false`, per-file excess 11/17/2, all 30 rows named with
   `deducted: false` and the reason).
2. `tools/request_ledger.py`: `build_report` publishes the raw count through the new
   `deduction_permitted()` gate (flag **and** evidence naming a `request_identity_hash`). The dedupe
   *rule* is untouched; only its authority to subtract was revoked. `requests == requests_raw` unless a
   sound rule with evidence is present.
3. The cap gate's input is now conservative. The G1 gate reads `budget.cap` / `budget.reserve` from the
   artefact and **recomputes** `spent` via `request_ledger.build_report` (`cell.py:721-722`, `cell.py:734`).
   That recomputation used `requests_deduplicated` — so the gate **was** fed a de-duplicated key. Fixed at
   the key it reads; the gate's arithmetic and its exit codes (4 / 3 / 5) are unchanged.
4. `docs/REQUEST-LEDGER.md`: a "Reversal 2026-10-26" section (before → now, the one sentence of evidence,
   and that a future sound rule re-publishes the deduction).
5. `experiments/ptr-engine/tests/test_request_ledger_sound.py` (12 tests): `requests == requests_raw` unless the flag **and**
   evidence are present; flag alone raises; no CLI switch exists; published artefact pinned at 1,101 / 3,219
   with 1,071 in `diagnostic`.

## Never touched
No rows file, no grade file, `run_longrun.py`, `client.py`, `cell.py`, the dedupe rule itself, `TVS.json`,
`LATENCY-REPORT.json`. `test_request_ledger_dedup.py` was amended only where it asserted the *withdrawn
publication* (headline/remaining/spent); its rule assertions are unchanged and still pass.

## Consequence for RUN-A\*
Precondition `remaining >= 900`. The gate now sees **3,219** (was 3,249). A\* needs **792** requests, so it
still fits with **2,427** to spare. Feasibility is unchanged; only the headroom claim moves (by 30).

## Bound
26 tool calls. Deliverables persisted; handoff `orchestration/handoffs/LEDGER-CONSERVATIVE.json`.
