# AGENTS.md — how work happens in this workspace

**Workspace root:** `/home/zer0null/research extractor`
**Read first:** this file, then [`docs/STATE.md`](docs/STATE.md). Everything else is on demand via
[`docs/INDEX.md`](docs/INDEX.md).
**Product of this workspace:** evidence and write-ups. It is a research and documentation workspace:
models/experiments are probed, measured, priced, and written down so the result can be carried into
other work. Code exists to make a measurement possible. A measurement that is not documented did not
happen.

> This contract replaces the earlier "main session orchestrates only" regime (2026-10-08 … 2026-10-28).
> That regime is preserved as history in `orchestration/CLOSING.md` and `orchestration/VERDICT-RITUAL.md`.
> The hard constraints in §5 and the evidence rules in §4 were not relaxed by the change.

---

## 0. Session pickup — do this before anything else

1. **Confirm where you are.** `pwd` must be this workspace root (or a path inside it). An omp session
   may start in a linked worktree under `~/.omp/wt/…`; a worktree checkout **lacks the untracked
   files** that are the current state. If `pwd` is not the root, use absolute paths rooted at
   `/home/zer0null/research extractor` for every read and write.
2. **Read `docs/STATE.md`.** It is the single current-state page: what is live, what was last
   measured, what is blocked, what the next actions are. It supersedes older status pages as *current
   state*; those remain valid as dated records.
3. **Read only what the task names.** `docs/STATE.md` points at the authoritative document per
   program; `docs/INDEX.md` maps the rest. Do not scan 176 documents to orient.
4. **Run `python3 tools/session_start.py`.** It prints the git checkpoint, the dirty/untracked counts,
   the newest journal entry and handoffs, the live request ledger, and the documentation check —
   cheap, read-only, no network.
5. If the task is a measurement, read the runbook it names (`docs/GRID-RUNBOOK.md` for ptr-engine)
   before the first command. The runbook's first command is often a 0-request reconcile, not a run.

---

## 1. What lives here

| Program | State | Entry point |
|---|---|---|
| **ptr-engine serving/cache/cost experiment** — 4-arm context grid against live Occamy/SGLang | **LIVE**; gen-6 grid measured 2026-10-28, verdict `not_adjudicable`, gen-7 decision pending | `experiments/ptr-engine/`, `docs/GRID-RUNBOOK.md`, `docs/STATE.md` §1 |
| **Paper track** — 3 papers filed (Zenodo + TMLR), 4th (`context-cache`) in progress | filed/waiting; 4th live | `papers/`, `strategy/SUBMISSION_RECORD.md`, `docs/STATE.md` §2 |
| **Research Extractor app** (`resextract`) — repo→docket pipeline | dormant, still contract-load-bearing (tests/config pin it) | `src/resextract/`, `docs/PLAN.md` (build plan, historical), `docs/OPERATIONS.md` |
| **Supporting workstreams** — jobs, release, repro, submission kit, external-practice surveys | parked/done | `docs/STATE.md` §4 |

The detailed filesystem map, including paths that must never move, is [`STRUCTURE.md`](STRUCTURE.md).

---

## 2. Operating model

**Owner mode is the default.** The session that owns the task may read source, run commands, write
files, and debug failures. It also owns the write-up. Delegation is a tool for throughput, not a
constitutional barrier.

- **Delegate fan-out, not the top-level plan.** The owning session settles scope, decomposition and
  cross-slice contracts; independent slices go to subagents in parallel with disjoint declared write
  paths. ≤5 concurrent subagents (operator instruction).
- **Give every subagent a self-contained slice.** It has no access to this conversation: state the
  target files, the change, the acceptance check, the write paths, and the bound (max attempts or a
  stop condition). Shared prerequisites go in the shared context, not repeated per slice.
- **Verification independence for claims.** A *measurement* or a *guard* is verified by a different
  agent than the one that produced it, or by re-running the recorded command in a fresh process. The
  author's own summary is never the evidence.
- **Partial is a result.** Report `partial` with the remainder named. Never fabricate a green.
- **Never extend a unit; supersede it.** A failed unit is replaced by a new one carrying the failure
  evidence, not resumed with a different brief.

---

## 3. Documentation contract — mandatory, and the thing that has failed before

A session that changes anything in this tree **has not finished** until all of the following are true
in the same session:

1. **`journal/YYYY-MM-DD.md`** — append a dated entry: what was done, **why**, the exact commands and
   their results (numbers, not adjectives), and what remains open. If the file exists, append; never
   rewrite an earlier day.
2. **`docs/STATE.md`** — update `Last updated:` and every program block whose state changed. This is
   the page the next session reads first; a stale STATE page is a defect, not a cosmetic issue.
3. **`docs/INDEX.md`** — one line for every document you create. The guard
   (`tools/doc_check.py`) fails on an unindexed doc or an index entry pointing at a missing file.
4. **An experiment gets a home.** A new experiment lands in `experiments/<name>/` with:
   `README.md` (question, status, how to run, where the evidence lives), `EVIDENCE.md` (what was
   measured and with what command), `RUN.json` (machine-readable run record). The machine twin of a
   result then goes in that experiment's `measure/` (`experiments/<name>/measure/<SLUG>.json`) and the
   write-up in `docs/` — the experiment directory is not the final home of a *write-up*, but it is the
   home of the measurement it produced. Cross-experiment outputs may sit in the root `measure/`.
5. **`journal/INDEX.md`** — one row per daily entry (date, headline, anchor). It is the narrative
   index; the guard checks coverage.

**Rules that keep the record honest:**

- **One fact, one home.** `docs/STATE.md` owns *current state*; dated docs under `docs/` own the
  measurement at their date; the machine twin under `experiments/<name>/measure/*.json` owns the raw
  numbers; `journal/` owns the narrative. Link, don't duplicate.
- **Supersede, never overwrite.** A newer document states which older one it supersedes; the older
  file stays on disk. Frozen records (`orchestration/handoffs/`, `orchestration/units/`,
  `orchestration/VERDICTS.md`, `state/logs/` baselines) are append-only.
- **A dated record keeps its spelling.** Historical commands that name the old workspace path
  (`/home/zer0null/reserach extarctor`) are records of what was run; leave them. Fix the path only in
  documents whose job is to instruct a *future* session (runbooks, operations, state).
- **Mark inference.** `[INFERENCE]` for anything not measured in this session; never present a
  plausible number as a measurement.
- **No orphan docs.** A file under `docs/` that no index line mentions is a guard failure.
- **Definition of done:** behaviour verified by a real run **and** the documentation contract satisfied —
  the journal entry, the `docs/STATE.md` update, the `docs/INDEX.md` line, the `journal/INDEX.md` row —
  plus the experiment's own record when the change is an experiment. A change with no journal line did
  not happen.

---

## 4. Evidence discipline (unchanged in force)

- **Measured vs asserted.** Every claim carries either the command that produced it or the marker
  that it is asserted. Numbers copied from prose are not measurements.
- **Red→green for guards.** A guard test must be shown to fail when the fix is reverted, and the
  reverted run recorded in the test docstring (this is the house style — see
  `tests/test_orchestration_handoffs.py`).
- **Frozen verdicts.** Once a verdict row is written it is not re-edited; a correction is a new
  verdict that names the one it supersedes. Swapping an estimator after rows exist is an instrument
  change and mints a generation whose rows may not be pooled with the old one.
- **Pinned, not live.** A trace-dependent claim cites the pinned copy and its digest, never the live
  path or its current size. The canonical example is the Duval m0 trace in
  `dockets/duval/duval-u55-pinned/material/data/2026-09-28-duval-m0.jsonl` (866,816 bytes, sha256
  `431605e624ca90596ec8c5890fc40da08715ae1ffa6759b689255f1670af4ecb`).
- **Never run the same paid measurement twice.** A 48-turn cell is money and evidence; re-run a
  partial as a fresh stamp, never append, never retry a locked cell.

---

## 5. Hard constraints (never relax without explicit user approval)

| # | Rule |
|---|---|
| 1 | **Target repos are strictly read-only.** `/home/zer0null/Duval` and every registered target: no writes, no git-state changes, no hooks. Prove with a lock-free `git status` plus an mtime sweep. |
| 2 | **Never run a bare `git status` against a target.** Pass `--no-optional-locks` or set `GIT_OPTIONAL_LOCKS=0`; the index refresh writes. Prefer reading files over invoking git at all. |
| 3 | **Never read or walk a target's `.worktrees/`** — a foreign actor writes there. |
| 4 | **Nothing is written outside this workspace** (`/home/zer0null/research extractor`). The old spelling `reserach extarctor` is not a path; it does not exist. |
| 5 | **No systemd unit enabled, no DSH plugin mounted, no DSH service restarted, no GX10/Occamy service restart** — these are user decisions. A long-lived server is started as a managed background job by the owning session and its exact URL reported. |
| 6 | **Secrets never enter dockets or commits.** Secret-shaped paths are refused from `material/`; the commit scan is value-based; never edit completed evidence to satisfy a scan. |
| 7 | **Do not hand-edit derived or frozen artefacts:** `experiments/ptr-engine/measure/REQUEST-LEDGER.json` and `experiments/ptr-engine/measure/LEDGER-GRID-BASELINE-*.json` are regenerated by `experiments/ptr-engine/tools/request_ledger.py`, baselines are superseded not edited; `state/logs/*baseline*.json` are sha-pinned by guard tests. |
| 8 | **Git safety.** The working tree holds ~1,300 untracked evidence files and HEAD (`f17663d`) is a checkpoint, not the truth. Never run `git clean`, `git reset --hard`, `git checkout -- .`, `git add -A`, or `git commit -a` without explicit approval; never assume an uncommitted file is disposable. |
| 9 | **Automated sessions never ask.** A session started by a schedule, the task board, or a cron reminder has no answerer: never call an interactive question tool, never wait for input. Missing value → the most conservative defensible default, recorded under `assumptions`, then continue to a deliverable. Interactive sessions *may* ask when the decision is genuinely the user's (cost, service change, scope). |

---

## 6. Where new things go

| You have… | Put it in… |
|---|---|
| Product code | `src/resextract/` |
| A guard or behaviour test | `tests/` (house style: pin the semantics, name the rule, record red→green) |
| A current-state change | `docs/STATE.md` (+ its line in `journal/`) |
| A measurement write-up | `docs/<UPPER-SLUG>.md`, machine twin in the experiment's `measure/<SAME-SLUG>.json` |
| A new experiment | `experiments/<name>/` with `README.md`, `EVIDENCE.md`, `RUN.json` |
| A daily narrative | `journal/YYYY-MM-DD.md` (+ `journal/INDEX.md` row) |
| A delegated unit's card / report | `orchestration/units/<UNIT>.md` / `orchestration/handoffs/<UNIT>.json` (valid JSON) |
| Scratch, DBs, one-off outputs | `state/` (gitignored; never commit, never move) |
| A produced docket | `dockets/` (versioning is an open user decision) |
| An obsolete artifact worth keeping | `archive/` + a line in `archive/README.md` |

---

## 7. Delegation contract (a unit card and its report)

1. **One purpose per unit.** No multi-step task files.
2. **Hard bound** stated up front: max tool calls / attempts, or a stop condition.
3. **Declared write paths**, checked against concurrently running units for clashes.
4. **Persist your own card** to `orchestration/units/<UNIT>.md`.
5. **Forced report-back.** Every unit ends by writing `orchestration/handoffs/<UNIT>.json`:

   ```json
   {"unit":"U0.1","status":"done|failed|partial","artifacts":["..."],
    "evidence":{"command_or_count":"actual output","commands":["..."]},
    "blocker":"","next_unit_hint":"...","write_paths":["..."]}
   ```

   and returns a **≤15-line summary**: status, artifacts, the evidence lines that prove the claim,
   blocker, next hint. **A handoff MUST be valid JSON** — `tests/test_orchestration_handoffs.py`
   parses every `orchestration/handoffs/*.json`, skips a file only when its bytes change between two
   immediate reads (mid-write), and fails on a stable unparseable file. Two shapes are contracted:
   the seven-key **unit handoff** above, and the **verifier verdict**
   (`unit, overall, checks, blocker, next_unit_hint, write_paths`, commonly
   `not_reproduced, overstated, unverified, containment, bound, scope, red_green, tool_calls,
   corrections`). A verdict-shaped handoff is not a defective unit report; known historical gaps are
   frozen in the baselines under `state/logs/`. Any *new* missing required key fails the guard.
6. **Fresh context per unit.** A unit reads only its own card, the previous unit's handoff, and the
   current disk state. No unit is ever extended — it is superseded by a new one.
7. **Partial is a result**, not a system failure. Report it with the remainder named.

Concurrency: ≤5 subagents, and only with disjoint write paths. The owning session keeps the plan, the
phase-gate call, and the final write-up.

---

## 8. Board mode (dormant, optional)

The DSH task board and its watchdog live outside this repo (`~/.dsh/…`, `.orchestration/incidents/`).
They are **not** a prerequisite for work here; an interactive session is recorded by its journal
entry. If the board is used again:

- **A card's `prompt` IS the contract.** The board sends `prompt` (plus any tag prefix), never
  `description`; a one-line prompt produces a confused unit.
- **Every executable card carries an `automated` tag** whose prefix repeats "never call
  `ask_user_question`"; and a card that must persist a handoff is `workspace-write`, never `read-only`
  (under `read-only` with approvals off, the handoff write is denied and the unit ships nothing).
- **No board unit spawns its own subagents.** Further work is a new card. `tools/board/session_recon.py`
  reports a subagent whose root ancestor is a board execution as `delegated-from-card`.
- **A card whose execution has ended is settled in the same pass** (`done`/`failed`), never left
  `todo`/`running`.

---

## 9. Known traps

- **Path spelling.** The workspace was renamed from `reserach extarctor` to `research extractor`.
  Many dated docs and the external watchdog still carry the old spelling. Only live instructions were
  corrected; a record that names the old path is not a bug to "fix".
- **Git HEAD is stale by design.** Everything after 2026-10-25 is uncommitted; `git status` is
  measured in thousands of entries. `docs/`, `journal/`, `strategy/` and most of `experiments/` are
  untracked. Never infer "deleted" from "not in HEAD".
- **Worktrees are partial by construction.** `.omp/wt/…` checkouts contain tracked files only; the
  untracked evidence layer is missing. Guard tests compute `ROOT` from `__file__`, so running them
  inside a worktree tests the worktree, not the live workspace.
- **Gitignored-but-critical:** `state/logs/U8.15/baseline_gaps.json` and
  `state/logs/U8.18/verifier_shape_baseline.json` are read (and sha-pinned) by the handoff guard; a
  fresh clone fails that guard until they are restored.
- **Do not edit** `orchestration/VERDICT-RITUAL.md` or `orchestration/units/TEMPLATE.md` casually:
  `experiments/ptr-engine/longrun/tests/test_verdict_ritual.py` asserts literal strings and ordering
  inside them. Treat both as contract text.
- **Ledger discipline.** After any cell batch, rebuild
  `experiments/ptr-engine/measure/REQUEST-LEDGER.json` with
  `experiments/ptr-engine/tools/request_ledger.py`; the launcher refuses to start when the ledger disagrees with the rows
  (`RUN-A RECONCILE … gap=` must be 0). A baseline is superseded, never edited.
- **`.occamy.lock`** serialises live cells; one request in flight, strictly serial, held for the whole
  batch. A dead lock is released by its owner record, never by killing a live runner.
- **Do not restart the shared model server** (`192.168.2.168:8012`); a crash-looping unit is a user
  decision, and the KV-cache sizing guard makes a bare restart a coin flip.

---

## 10. Closing checklist (run before you yield)

```bash
python3 tools/session_start.py                 # orientation snapshot + doc check
python3 tools/doc_check.py                    # docs/journal index coverage, STATE page
.venv/bin/python -m pytest tests/test_agent_context.py -q   # the documentation guard
# + the specific test/command covering the change, re-run in a fresh process
```

Then: `journal/YYYY-MM-DD.md` written or appended, `docs/STATE.md` updated, `docs/INDEX.md` updated,
`journal/INDEX.md` row added. If any of those is missing, the session is not finished.
