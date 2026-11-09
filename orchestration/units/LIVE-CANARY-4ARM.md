# UNIT LIVE-CANARY-4ARM

**Purpose.** Prove the launch shape on four arms with 48 real requests, and stop the grid if any
arm degenerates. This is a LIVE card: it spends requests. Hard cap **52 requests** (48 canary turns
+ up to 4 warm-ups); **one invocation** of the canary path; no retries.

**Why now.** `LAUNCH-CANARY-WALL` (2c1c…) → done, next hint: *"The canary now prices its own
projection and a WOULD-REFUSE gate line blocks the launcher (rc 1). Re-run the live canary … to
confirm G2 allow end-to-end; the grid argv is byte-identical so the grid launch needs no re-price."*

**Settled state (verify, do not re-derive).** gen 4 pin
`fa6fd8cc519f5a2794b54fe5f215c808f781b136de657bdece7f5eb4bf37e8ac`; canary = cells 1, 4, 7, 9 →
pointer-stable, transcript-grow, transcript-compact, lease-reopen, 12 turns each; canary wall
**900 s**; `--hypothesis smoke`; per-cell `--budget 108`; ledger **1,128 / 3,192** at baseline v2
`3b79f476…`.

## Tasks
1. Preflight (offline): launcher dry run; quote the gate lines; every gate `allow`, `refused=0`,
   `canary_arms=4 canary_requests=48`, `max_wall=900`. Any `WOULD-REFUSE` → STOP (rc 1), report.
2. Live canary, once, through the launcher's own canary path (no `--dry-run`).
3. Spend from the ledger, not the launcher's claim: `request_ledger.py` before/after; report
   `spent_before`, `spent_after`, `delta`, `delta ≤ 52`. `delta > 52` is a STOP and a finding.
4. Classify each arm with the settled `CANARY-ERA-B-FIX` rules (`tranche_canary.py`, not a
   re-implementation): `shape_ok` needs `answer_verified ≥ 1` and
   `stop_signal_source=finish_reason`; a cap-length completion inside the 12-turn window is
   `shape_degenerate`; anything unresolvable is `shape_unknown` and is never rounded to ok.
5. Decide in writing: all four `shape_ok` → grid may be unblocked; any `shape_degenerate` → grid
   stays held, name the arm/turn/evidence; any `shape_unknown` → held, name the measurement that
   would resolve it.
6. Era-B shape findings era A never had: cached-token share per arm
   (`prompt_tokens_details.cached_tokens`), stop-reason census, and whether any turn hit
   `turn_call_cap` / `fetch_budget_exhausted`.
7. Do not edit `cell.py`, `run_longrun.py`, `run_a_star.py`, `analyze_stats.py`, `grade_v5.py`, any
   fixture, `HARNESS-PIN.json`, `GRID-PARAMS.json`, thresholds, `PARM-1*`, or any published page.
   Rows land where the runner writes them; no row may be deleted, rewritten or re-graded.

## Hard rules
- Never `ask_user_question`. Report failures; do not retry.
- Hard cap 52 requests, one live invocation. A dead invocation is reported with its exit code and
  ledger delta; a second attempt needs its own card.
- Journal first; handoff within 8 calls; verdict row before the handoff write.

## Write paths — exactly
`orchestration/units/LIVE-CANARY-4ARM.md` · `orchestration/handoffs/LIVE-CANARY-4ARM.json` ·
`orchestration/journals/LIVE-CANARY-4ARM.jsonl` · `measure/CANARY-ERA-B.json` ·
`docs/CANARY-ERA-B.md`
