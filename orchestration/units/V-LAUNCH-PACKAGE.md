# UNIT V-LAUNCH-PACKAGE (verifier)

Objective: independently recompute every number `RUN-A-STAR-2` spends against, offline.
Claim under audit: `orchestration/handoffs/LAUNCH-PACKAGE-RECONCILE.json` :: `ready_to_launch: true`,
1,016 requests against 3,192 remaining of a 4,320 cap.
Bound: 26 tool calls. Verdict row recorded before handoff. No edits outside this unit's three files.

## Recomputed numbers

| # | Number | Recomputed | Source |
|---|---|---|---|
| 1 | price 1,016 | **DOES NOT ADD UP** (981 or 1,020 or 1,164 by reading) | GRID-PARAMS.json :: price |
| 2 | tranche 964 | 964 = 480 + 480 + 4 | run_longrun.py:230, cell.py:128-135 |
| 3 | budget 108 | ALLOWED; 108 >= ceil(98 x 1.10)=108; gate sees 53 | cell.py:140, :380-382, :388-392 |
| 4 | pool 48 | 48 | run_longrun.py:230, :2857 |
| 5 | ledger 1,128 / 3,192 / 4,320 | reproduced exactly | request_ledger.build_report over 15 rows files |
| 6 | pin 2b4d4808 | **MOVED** fa6fd8cc | analyze_stats.py changed 19:14Z, pin frozen 19:09Z |
| 7 | canary N=12 / claim none | wiring present; gate-field mismatch recorded | run_a_star.py:186-200, :328-332 |

## Notes
- Factor used: the cap-based additive model (turns + rounds + digests), not 1.374532.
  480 x 1.374532 = 659.8 < 960, so the additive model dominates and is the runner's own
  projected_requests shape.
- The launcher prints a stale `remaining` base: 3219 at run_a_star.py:369/379/437/443/445.
