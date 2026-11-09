# UNIT V-CAPGATE-DEDUP — verify the cap gate against a de-duplicated spend

**Kind:** verifier (attacker). **Author of the gate:** not this unit. **Bound:** 24 tool calls; handoff `partial` within 5 calls.
**Offline:** zero inference requests. **Mutation:** `/tmp` mirrors only; the repo's gate, ledger, rows and measure artefact are read-only.

## Claim under test

`orchestration/handoffs/REQUEST-LEDGER-2.json`, `assumptions[1]`: *"budget.spent is the de-duplicated count (1,071) … Downstream cap-gate reconcile therefore also runs on the de-duplicated count."* Its `next_unit_hint` predicts a duplicate mirror surfaces as `delta<0` `CAP GATE UNRECORDED` instead of inflating the budget.

Why it matters: deduplicating spend behind a live brake is the one place a correction can spend real money. If the gate counts 1,071 while the engine bills 1,101, the gate believes it has 30 requests of headroom it does not have — a run that overruns the cap.

## Probes and deliverable

1. Reconcile arithmetic from source (`RequestCapGate.__init__`, `acquire`, `_gate_finish` in longrun/run_longrun.py; `build_report`/`deduction_permitted` in tools/request_ledger.py).
2. Reproduce `delta<0` with one unseen duplicate mirror row in a `/tmp` copy; quote message and exit code; decide refuse vs warn.
3. Boundary: `spent + planned == cap` then one over; then the same with a raw (1,101) vs de-duplicated (1,071) ledger to show which count is used.
4. Unsafe direction: ledger 1,071, rows 1,101, cap leaving exactly 30 — refuse or launch, and the headroom believed.
5. Today's agreement: `measure/REQUEST-LEDGER.json` `spent` / `spent_raw` / `remaining` vs the gate's own reconcile print.

## Result

`partial`. The gate refuses every overrun as shipped (exit 4, and exit 9 on `delta>0`), but `delta<0` prints `CAP GATE UNRECORDED` and returns **exit 0** — it warns, it does not refuse. The claimed deduction is not live: `DEDUCTION_RULE_SOUND=False` and `deduction_permitted()` demands a `request_identity_hash` that does not exist, so the gate spends against the conservative raw 1,101. `--dry-run` never constructs the gate at all.

Deliverables: `experiments/ptr-engine/tools/capgate_dedup_attack.py`, `experiments/ptr-engine/measure/CAPGATE-DEDUP-ATTACK.md`, `orchestration/handoffs/V-CAPGATE-DEDUP.json`.

## Hard rules honoured

- No edit to `run_longrun.py`, `request_ledger.py`, any rows file, or `measure/REQUEST-LEDGER.json`.
- Every "run" is the gate object driven in-process, or `run_longrun.py --dry-run`; no socket, no request.
- Every verdict carries the exact printed line and exit code.

## Containment evidence

- Repo writes: only the five declared write paths.
- Mirrors: `/tmp/capgate-dedup-mirror/{today,shipped,dedup,boundary,unsafe}`.
- The "claimed world" is a `/tmp` shim wrapping the real `request_ledger.build_report` with `deduction_rule_sound=True` plus a placeholder evidence key — the only way to reach the `delta<0` branch without editing a repo file.
