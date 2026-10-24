# UNEUTRAL3 — build and measure C′ (pinned + strip + selective retag)

Parent: session-c3d61727-8af8-4c19-b1b9-5922c347a11a. Status: IN PROGRESS (skeleton written first).

## Purpose
Build the workable option C′ = pinned tree (A) + strip provably-dead JSONL fields + selective retag of
non-fixture material (keep `PIN_LITERAL_KEYS` and `.py`/`.sh` pins), and MEASURE:
- Stage 1: strip `texts`,`id`,`familyId`,`clanId`,`stratum` — verified read-sites, byte saving.
- Stage 2: number-movement test for the strip (recompute-claims.py, parse_fixture+compare, arms, F1s).
- Stage 3: bijective relabel of `kind` vocabulary and `<kind>-NNN` case ids — measured, not argued.

## Hard bounds
≤45 tool calls. Write paths: `scratch/uneutral3/**`, `strategy/CPRIME_MEASUREMENT.md`,
`orchestration/units/UNEUTRAL3.md`, `orchestration/handoffs/UNEUTRAL3.json`.
Never write live tree except `redact.py`; never touch `papers/**`; `/home/zer0null/Duval` read-only.
Map M never written/logged (`map_shipped: false`).

## Results
(filled at completion)

## Evidence
(filled at completion)
