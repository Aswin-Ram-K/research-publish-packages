# Unit RUN-C-PLAN

**Purpose (one):** turn DESIGN-V3 config C into an executable, pre-registered plan. Zero requests.
**Bound:** 18 tool calls, 1 attempt, no re-run of the dry-run beyond twice.
**Write paths:** `experiments/ptr-engine/longrun/RUN-C-PLAN.md`,
`orchestration/handoffs/RUN-C-PLAN.json`, this card. Nothing else; runner/scorer/fixtures/rows untouched.
**Kill:** if `--dry-run` cannot produce `would_send_total`, ship `partial` with the failing command + exit code.

## What was done
1. Stub handoff (`partial`, blocker `in progress`) written first.
2. Read the real flag list from `run_longrun.py --help` (no guessed flag names).
3. Dry-ran config C: `runtime/LR-01.json`, 4 arms, 1 rep, `--thinking off`, `--max-tokens 4096`,
   `--max-turns 48`, `--run-id longrun-c-2026-10-26` → exit 0, `would_send_total=192`, manifest content read.
4. Copied the frozen decision rule and P1–P4 verbatim from `LONGRUN-PREREG.md`.
5. Wrote `RUN-C-PLAN.md`: commands, stop conditions, scoring command + output shape, validity block, budget.

## Constraints found (recorded, not fixed)
- Live budget 204 = 192 + 2 digests + 4 controls + 6 repairs; dry-run models only the 192 arm-turns.
- `--dry-run` ignores `--max-turns`; harmless only because N=48 == the requested 48.
- `checks_structured` = 12 for LR-01 (55 is the sum over LR-01…06), so the C cell's quality leg is 12 checks.
- One rep → no 2-rep p95; rule (i) is a ratio with a wide interval, no significance claim. t60 leg dropped by N=48.
