# AGENTS.md — Research Extractor workspace

**Spec of record:** [`docs/PLAN.md`](docs/PLAN.md). Read it before any work. This file governs *how*
work happens; the plan governs *what* is built.

## The main session does three things, and nothing else

| Main session MAY | Main session MUST NOT |
|---|---|
| Compose a unit card and pass it as a subagent prompt | Write, edit or create any file on disk (unit cards included — subagents persist their own) |
| Launch subagents (`subagent`, `subagent_fork`), ≤3 concurrent, watching for write-path clashes | Run builds, tests, installs, `git`, or the pipeline itself |
| Read `orchestration/handoffs/*.json`, `orchestration/STATUS.md`, and ≤15–20-line command summaries | Read source code, logs, or debug a failure |
| Relay status, verdicts and evidence lines to the user; escalate decisions | "Fix" a failed unit — re-delegate to a **fresh** unit carrying the failure evidence |
| Make the phase-gate call (advance / re-delegate) from a verifier's verdict | Approve its own work — every claim is verified by a **different** subagent |

## Unit contract (every unit, no exceptions)

1. **One purpose per unit.** No multi-step task files.
2. **Hard bound** stated up front: max tool calls / attempts, or a stop condition ("if X cannot be verified in N tries, STOP and report").
3. **Declared write paths**, listed in the unit card and checked against the concurrently running units for clashes.
4. **Persist your own card** to `orchestration/units/<UNIT>.md`.
5. **Forced report-back.** Every unit ends by writing `orchestration/handoffs/<UNIT>.json`:

   ```json
   {"unit":"U0.1","status":"done|failed|partial","artifacts":["..."],
    "evidence":{"command_or_count":"actual output","commands":["..."]},
    "blocker":"","next_unit_hint":"...","write_paths":["..."]}
   ```

   and returns a **≤15-line summary** to the main session: status, artifacts, the evidence lines that
   prove the claim, blocker, next hint. That cap is what keeps the orchestrating session small.
6. **Fresh context per unit.** A unit reads only: its own card, the previous unit's handoff, and the
   current disk state. **No unit is ever extended** — it is superseded by a new unit.
7. **Partial is a result**, not a system failure. Report `partial` with the remainder named.

## Verification independence

Every batch gets a **separate verifier unit that is not the author**. It re-runs the evidence commands,
checks the plan's clause, and includes a **red→green** check on at least one guard (the test must fail
when the fix is reverted). Verdicts are recorded in [`orchestration/VERDICTS.md`](orchestration/VERDICTS.md);
the main session makes the gate call from them.

## Hard constraints

- **Target repos are strictly read-only.** `/home/zer0null/Duval` (the acceptance target) and every
  other registered target: no writes, no `git` state changes, no hooks installed inside them. Proven by
  `git status` plus an mtime sweep, before and after.
- **Nothing is written outside this workspace** (`/home/zer0null/reserach extarctor`).
- No systemd unit is enabled, no DSH plugin mounted, no DSH service restarted — without explicit user approval.
- Long-lived processes (the dashboard) are started as **managed background jobs by the owning unit**,
  which verifies and reports the exact URL. The main session never starts a server.
- Secrets are never written into dockets; secret-shaped paths are refused from `material/`.

## Current state

See [`orchestration/STATUS.md`](orchestration/STATUS.md) for the batch/unit table and live status.
