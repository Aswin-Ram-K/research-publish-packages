# UNIT CELL-PY-BEHAVIOUR-CERTIFY

**Purpose.** Certify the current `experiments/ptr-engine/longrun/cell.py` (`c29a9fb3…`) against the eight
claim rows settled cards made about it. Provenance is not recoverable (untracked, no baseline of
`e24e867b`, written 18:54:16Z by no settled card); behaviour is testable.

**Mode.** Automated, offline. Zero requests, zero network, no harness edit, no live cell.
**Bound.** 24 tool calls; journal first; handoff within 7 calls; verdict row before the handoff write.

**Write paths (exactly).**
`experiments/ptr-engine/measure/CELL-PY-CERTIFICATE.json` · `docs/CELL-PY-CERTIFICATE.md` ·
`orchestration/units/CELL-PY-BEHAVIOUR-CERTIFY.md` · `orchestration/handoffs/CELL-PY-BEHAVIOUR-CERTIFY.json` ·
`orchestration/journals/CELL-PY-BEHAVIOUR-CERTIFY.jsonl`

**Method.** For each claim: locate the site, run the probe end-to-end through `cell.main()` where a
fixture permits (`tasks-v5/runtime-v5/LR-01.v5.json`), quote the observed line and exit code. A probe
that could not be run is `not_testable`, never `holds`. Then run the seven named suites from the repo
root and from the longrun directory and quote both counts.

**Result.** 8/8 claims hold, with two corrections recorded (exit 7 *is* raised by cell.py at four sites;
`--request-allocation` is a runner flag, not a cell.py surface). One suite red is a stale test double
(`tools/gate_attack.py:544`), not cell.py behaviour. Certificate written; no file outside the declared
write paths was touched.

**Follow-up (new card, not this unit).** Refresh `gate_attack.run_chain_cases`'s `counted()` stub to
accept `purpose=`, so the six named bypasses can be exercised end-to-end again.
