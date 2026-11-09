# FAILED-TRIAGE

**Purpose.** Turn the board's failed column into a work list, offline, from artefacts on disk — not from the
sweep's verdict line.

**Why.** The sweep closed four consecutive cards FAIL `no-verdict no-sha` that had all delivered
(`PROJECTION-MODE` 5bb51dde, `STOP-REASON-HOLES` 63912f2b, `OPERATOR-BRIEF-2` f0351ac0,
`REQUEST-LEDGER-2` 21ddabf8). The failed column stood at 104, and no reader could tell "do not retry" from
"retry, it worked".

**Method (read-only).**
1. Failed = `status: failed` and not archived in the task-board ledger (revision 4443) → 104 units, 5 workspaces.
2. For each: unit key from the card title → `orchestration/handoffs/<UNIT>.json` (994 handoffs indexed; none
   needed sampling) → handoff status, `artifacts`, `evidence`, `blocker`.
3. Every named artefact `stat`-ed from the workspace root; size and existence recorded.
4. Verdict row looked up in `~/.dsh/storages/orchestration/verdict.jsonl` by execution id.
5. Class: `delivered-unverdicted` (claim + artefacts present + evidence recorded), `superseded` (named
   done successor or done handoff on the same path), `retriable` (nothing landed, or blocker still true),
   `abandoned` (objective moved).

**Result.** 104 classified — delivered-unverdicted 27, superseded 11,
retriable 66, abandoned 0. All 27 delivered candidates had
their artefacts on disk (full set, no sampling). `failed` becomes 77 if those are accepted.

**Hard rules honoured.** No handoff, unit card, row file or grade file edited. No acceptance command run, no
live request, no dashboard. Writes: `docs/FAILED-TRIAGE.md`,
`experiments/ptr-engine/measure/FAILED-TRIAGE.json`, this card, the handoff, the journal.

**Bound.** 28 tool calls; used 21.
