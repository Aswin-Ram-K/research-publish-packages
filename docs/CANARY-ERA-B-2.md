# CANARY-ERA-B-2 — the four-arm era-B canary, run attempt 2

**Unit** `LIVE-CANARY-4ARM-2` · card `e07e2764-ff52-41bb-a663-272335d45154` · execution `f4578fcf-e8ca-482b-b553-9d78e9e5e2e4`
**Date** 2026-10-26 · **Live requests sent** 0 · **Decision** `GRID HELD`

## Outcome in one line

The canary was **not** run: the launcher that is the only permitted argv builder refuses to
start, and a second precondition command no longer runs. Nothing was spent — the ledger is
`spent 1128 / remaining 3192` before and after.

This is a precondition STOP, not a measurement. A hold is the card's successful result; a
fabricated arm table would have been the failure.

## The seven preconditions, quoted

| # | Check | Status | Evidence |
|---|---|---|---|
| 1 | `RUN-DRY-TURN-SCOPE.json` pass | **pass** | `status=done`; `--max-turns 12` → `turn_requests=12 … cell_total=12 / would_send_total=12`; no-flag → `cell_total=48 / would_send_total=48` |
| 2 | own 12-turn projection, re-run here | **pass** | `pointer-stable turn_requests=12 (N=48 --max-turns=12 x reps=1) digest_requests=0 cell_total=12` / `would_send_total=12`; no-flag re-run still `would_send_total=48` |
| 3 | pin generation ≥ 5, digest recomputed now | **pass** | generation **5**, pinned `35ff41b7bbf37f0df28b4307da8d514fea7d324ef22f719b61ee036b73cb5adb`, recomputed by this unit from `cell.py:128-135` + fixture → same |
| 4 | `cell.py` unmoved since the pin | **pass (recorded gap)** | `cf512f5f3bd075c46a2c7c508ce9b803a32d9ba1ceb44edf3c729ded6ce3ce18`, 114184 B, mtime `2026-10-26T19:52:55Z`, i.e. before `frozen_at 20:05:00Z`; the pin carries **no** `cell.py` sha field (recorded beside it by `V-PIN-GEN5-ATTRIBUTION`) |
| 5 | `launch_contract_diff --check` exit 0 / 13 | **FAIL** | `KeyError: 'components'` at `experiments/ptr-engine/tools/launch_contract_diff.py:653` → `params["price"]["components"]["tranche"]`, exit 1. Unscoped mode (no `--pin-generation`). |
| 6 | launcher dry run prices cells 1,4,7,9 | **FAIL** | exit 1: `HARNESS-PIN record disagrees with the launcher: record generation=5 digest='35ff41b7…', launcher gen 4 digest='fa6fd8cc…'` — no G1/G2/G3 lines, no `canary_arms=4 canary_requests=48` tail |
| 7 | ledger before | **pass** | `measure/REQUEST-LEDGER.json` (built `2026-10-26T18:56:31Z`): `spent 1128`, `remaining 3192`, cap 4320 |

## Spend

`spent_before 1128 · spent_after 1128 · delta 0` — measured from `measure/REQUEST-LEDGER.json`,
not from the launcher. Cap 52 was never approached. The 48-request canary price is unchanged and
remains unspent.

## Two defects, both external to this card's write scope

1. **`LAUNCHER-GEN5-UNWIRED`** — `experiments/ptr-engine/tools/run_a_star.py:51` still holds
   generation 4's digest and `:64` refuses any pin record whose generation is not 4.
   `HARNESS-PIN.json` already records the owner: `wiring.status = "PENDING ADVANCE"`,
   `advance_owner = HARNESS-PIN-WIRING successor`. Effect: *every* launcher cell — grid and
   canary — is refused before spawn. Fail-closed, and cheap to detect.
2. **`LAUNCH-CONTRACT-DIFF-BROKEN`** — `GRID-PARAMS.json` was rewritten at `20:20:00Z` by
   `GRID-PARAMS-16CELL` (schema `consonance.grid-params/3`) and no longer carries
   `price.components`, so `launch_contract_diff.py` cannot execute `--check` at all. The tool and
   the 16-cell record are now mutually incompatible at that line.

## Arms

None. No arm ran, no turn executed, no completion returned. An unmeasured arm is `shape_unknown`
and is never rounded to `shape_ok`; therefore **the 1,056-request / 16-cell grid may not launch**.

## Era-B shape facts

Not measurable — the canary produced zero completions: stop-reason census empty, no
`turn_cap` / `turn_call_cap` / `fetch_budget_exhausted` hits, no arm with zero `ANSWER:` lines
because no arm produced any line.

## What 48 requests proved that 0 requests could not

Nothing yet — and that is the finding: the launch path is shut at **zero** cost, so the next
paid 48 requests should be spent only after `run_a_star.py` is advanced to generation 5 and
`launch_contract_diff --check` runs again.
