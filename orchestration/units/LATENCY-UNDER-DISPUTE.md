# LATENCY-UNDER-DISPUTE — reconcile the latency report with the failure of rule R

**Automated, offline.** Zero inference requests, zero network. **Bound:** 26 tool calls.

## Why
`LATENCY-REPORT-2` re-derived every interval on rows de-duplicated by rule R, and withdrew exactly one p95 — G7
`V4-TOOLS / pointer-stable` (n 68 → 51). `V-DUPLICATE-RULE` then returned **overall: fail** on R's *justification*:
`content_sha256` is `sha256(assistant content)` — a response hash, 869/869 rows at `run_longrun.py:1493` — so identical
tuples are not proof of one request. Meanwhile the ledger is reverting spend to the raw count for the same reason, so
latency and ledger were treating one rule in opposite ways.

## Task (as carded)
1. One explicit floor policy on every cell: p95 only if `n_raw ≥ 60` **and** `n_dedup ≥ 60`; else refused by name with
   both counts. Written into `docs/LATENCY-REPORT.md` as a one-line rule with its reason.
2. Label the dispute on every affected figure in `measure/LATENCY-REPORT.json` (`dedup_rule_status`, `n_raw`,
   `n_dedup`, `withdrawal_basis`).
3. Recompute nothing unaffected: p50 column and the G4 four-arm table stated with counts.
4. State what the disputed rows can and cannot do, the measurement that would decide it (`DEDUPE-ROOT-CAUSE`), and that
   the withdrawn reading is the one to quote until it lands.
5. One operator number: p95 values after the policy, arms, and whether any is an inter-arm comparison.

## Result
G7 **68 / 51 → withheld**; G8 **72 / 70 → published** `397.41 [273.84, 659.70] n=70`; G9 **72 / 61 → published**
`429.70 [318.80, 477.06] n=61`. 2 p95 values, 2 single-arm grids, 1 arm, **0** inter-arm comparisons. G4 four arms
48 raw = 48 de-duplicated, 0 removed, p50 bit-identical.

## Hard rules honoured
No rows file, grade file, `request_ledger.py`, `measure/REQUEST-LEDGER.json`, `TVS.json`, `analyze_stats.py`,
`client.py`, `run_longrun.py` or `cell.py` was edited. Recompute is from rows via the analyser; publication is into the
two report artefacts and this unit's own files. Floor never lowered; no bare p95; both counts always published.
