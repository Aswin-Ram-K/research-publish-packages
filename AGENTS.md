# AGENTS.md — Research Extractor workspace

**Spec of record:** [`docs/PLAN.md`](docs/PLAN.md). Read it before any work. This file governs *how*
work happens; the plan governs *what* is built.

## The main session does three things, and nothing else

| Main session MAY | Main session MUST NOT |
|---|---|
| Compose a unit card and pass it as a subagent prompt | Write, edit or create any file on disk (unit cards included — subagents persist their own) |
| Launch subagents (`subagent`, `subagent_fork`), ≤5 concurrent, watching for write-path clashes | Run builds, tests, installs, `git`, or the pipeline itself |
| Read `orchestration/handoffs/*.json`, `orchestration/STATUS.md`, and ≤15–20-line command summaries | Read source code, logs, or debug a failure |
| Relay status, verdicts and evidence lines to the user; escalate decisions | "Fix" a failed unit — re-delegate to a **fresh** unit carrying the failure evidence |
| Make the phase-gate call (advance / re-delegate) from a verifier's verdict | Approve its own work — every claim is verified by a **different** subagent |

**Concurrency cap: ≤5 concurrent subagents.** Raised from ≤3 by explicit **user instruction** during this
build ("use upto 5 subagents in cincurrency") — an operator instruction, not a build convenience.

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

   **A handoff MUST be valid JSON** — it is machine-read by the main session, and that requirement is
   enforced rather than aspirational by `tests/test_orchestration_handoffs.py`, which parses every
   `orchestration/handoffs/*.json`, skips a file only when its bytes change between two immediate reads
   (mid-write), and fails on a stable unparseable file.

   **Two handoff shapes are contracted** — both valid JSON. The seven keys above define the
   **unit handoff** (a unit's report of its own work). A **verifier verdict** — a verifier unit's
   judgement — is a *different* shape with a different job: it reports whether an author's claims
   survived re-checking, so it carries a verdict, not a unit's self-report. Measured across the 43 `V*`
   handoffs present when this was written (U8.18), its core keys — those carried by ≥90% of them — are
   `unit`, `overall`, `checks`, `blocker`, `next_unit_hint`, `write_paths`:

   ```json
   {"unit":"V0.1","overall":"pass|fail|partial","checks":["..."],
    "blocker":"","next_unit_hint":"...","write_paths":["..."],
    "not_reproduced":[],"overstated":[],"unverified":[],"tool_calls":0,"bound":0}
   ```

   Commonly carried but **not** required (count over the same 43): `not_reproduced` 37, `overstated` 37,
   `unverified` 37, `tool_calls` 36, `containment` 36, `bound` 35, `scope` 34, `red_green` 32,
   `corrections` 31. Neither shape is "the wrong one": a verdict-shaped handoff is not a defective unit
   report and is **not** to be rewritten into the unit shape — that would mean inventing values nobody
   wrote. Known shape gaps stay **recorded gaps** in the frozen baselines under `state/logs/` (frozen by
   U8.15 for the unit shape, by U8.18 for the verifier shape); the guard fails on any *new* missing
   required key.
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
  other registered target: no writes, no `git` state changes, no hooks installed inside them. Proven by a
  **lock-free** `git status` (`--no-optional-locks`) plus an mtime sweep, before and after.
- **Never run a bare `git status` against a target.** Any git command run against a read-only target must
  pass `--no-optional-locks` (or set `GIT_OPTIONAL_LOCKS=0`): `git status` refreshes `.git/index`, so it
  writes. Prefer reading files over invoking git at all. Measured over the `commands` arrays in
  `orchestration/handoffs/*.json`: of **136** handoffs carrying **194** target-referencing command strings,
  **62** ran a plain `git -C /home/zer0null/Duval … status` and **0** ran a target-mutating verb.
- **Trace-dependent claims cite a pinned copy, not a live path.** If a claim depends on a file that can
  change under us, it must name the pinned copy's path and digest. The pinned trace is
  `dockets/duval/duval-u55-pinned/material/data/2026-09-28-duval-m0.jsonl` — **866,816 bytes, 573 records,
  573 gated lines / 712 gate occurrences** (pattern set `strategy/LEAD_PACKAGE.md` §1 "Gate-hit measurement",
  `:41-46`), sha256 `431605e624ca90596ec8c5890fc40da08715ae1ffa6759b689255f1670af4ecb`. **Dated observation:**
  the live path grew 866816 → 1570243 bytes mid-batch and measured **1,624,082 bytes / 1087 lines / sha256
  `35687221…` at 2026-10-15 21:02:05** — never cite that path or size as the current size.
- **Nothing is written outside this workspace** (`/home/zer0null/reserach extarctor`).
- No systemd unit is enabled, no DSH plugin mounted, no DSH service restarted — without explicit user approval.
- Long-lived processes (the dashboard) are started as **managed background jobs by the owning unit**,
  which verifies and reports the exact URL. The main session never starts a server.
- Secrets are never written into dockets; secret-shaped paths are refused from `material/`.
- **Every session that does work in this workspace has board ancestry.** A subagent inherits its parent card; an interactive session that works here must have either a card or a dated waiver in `state/logs/session-recon-waivers.json`. A card must not settle `done` while a descendant session is still live — if the child outlives the card, the residual work is re-carded, not silently orphaned.
- **(a) The user's main session lives outside the board by design.** It may drive the board (compose cards, launch subagents, relay verdicts) but it does not itself do work; any work it performs is a card. A non-board session is not automatically an offender — only when it acts as a work session without ancestry.
- **(b) No board unit spawns its own subagents.** A card unit must not delegate to subagents; further work is a new card, not a child of the running unit. `session_recon.py` reports any `card-subagent` (a subagent whose root ancestor is a board execution) as `delegated-from-card`.
  - The guard grades historical (closed) descendants as recorded violations, not offenders: a closed card-subagent is listed under `historicalDescendants` with its parent card and last-write time and does not fail the run; only a live card-subagent (or `--strict`) fails it.
- **(c) A card whose execution has ended must be settled in the same pass.** Never leave a card in `todo`/`running` once its latest execution has ended — settle it to `done`/`failed`. `session_recon.py` reports such cards as `settled-lag`.

## Current state

See [`orchestration/STATUS.md`](orchestration/STATUS.md) for the batch/unit table and live status.

## Automated sessions never ask the user

A session started by the task board, a schedule, a cron reminder, or any other non-human trigger has **no
answerer**. `ask_user_question` in such a session blocks until something external resolves it — and the unit
produces nothing. Observed on 2026-10-21: three task-board execution sessions stalled for hours this way.
`session-7e3c8cc9-6347-4419-b4b4-5b03729810cd` (unit `U3`) called `ask_user_question` at step 3, asking for
its own unit objective because the board card's `prompt` was a single thin line — "Live measurement unit.
Hold the `.occamy.lock` for the whole cell batch." — while the full unit contract lived only in the card's
`description`, which the board does not send. That session sat **8h31m** and produced no artefact. The `U6`
session called `ask_user_question` **9** times and also produced nothing.

- **Rule: in an automated session, never call `ask_user_question`.** Never wait for input. Never ask for
  confirmation.
- **Missing value → conservative default, recorded.** When a required value is genuinely missing, choose the
  most conservative defensible default, record it in the handoff (`orchestration/handoffs/<UNIT>.json`) under
  an `assumptions` key with the reason, and continue to a deliverable. "Partial" is an acceptable result;
  stalling is not.
- **Rule for whoever creates the cards: the `prompt` IS the contract.** A card's `prompt` must be the WHOLE
  unit contract — objective, hard bound, write paths, kill condition, deliverable shape. The board sends
  `prompt` (prefixed by any tag `promptPrefix`); it does **not** send `description`. A one-line prompt
  guarantees a confused unit.
- **Rule: every executable card carries an `automated` tag** whose `promptPrefix` repeats the no-questions
  instruction, so the rule survives even when a card's own prompt forgets it.
- **Rule: a card that must persist a handoff is `workspace-write`, never `read-only`.** Under `read-only`
  with approvals disabled the handoff write is denied, so the unit can complete its whole analysis and ship
  nothing — and the failure is invisible to every test, because the artefact it would have written is
  simply absent. This cost three wasted units: `V-G3FOLD2` re-derived C62, found the two understated bands,
  and its verdict could not be persisted at all. If a card's job is to *report*, it needs a writable path
  for that report; only cards that write nothing anywhere may be `read-only`.
