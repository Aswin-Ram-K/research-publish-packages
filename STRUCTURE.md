# STRUCTURE.md — the map of this workspace

**Workspace:** `/home/zer0null/reserach extarctor` (the misspelling is intentional — do not "fix" the path)
**Written by:** unit **USTRUCT**, whose single purpose was to give the workspace a documented top-level
organisation **without breaking anything that already works**.
**Read this with:** [`AGENTS.md`](AGENTS.md) (how work happens) and [`docs/PLAN.md`](docs/PLAN.md) (what is built — the spec of record).

If you have just arrived cold, read this page first, then `AGENTS.md`, then `docs/PLAN.md`.

---

## 1. Top-level entries at a glance

`kind` is one of **source** (hand-written, tracked, depended upon), **derived** (generated
output that can be regenerated), **evidence** (records of what was done/observed), **runtime**
(local state, caches, environments — not part of the product).

| Entry | Kind | What it is | Do other things depend on its path? |
|---|---|---|---|
| [`src/`](src) | source | The `resextract` Python package. The product. | **Yes — heavily.** Tests import it; the CLI entry point is here. **Never move.** |
| [`tests/`](tests) | source | Pytest suite, 44 top-level items, including the orchestration-contract guard `test_orchestration_handoffs.py` and the gitignore guard `test_repo_hygiene.py`. Also holds fixtures and a nested `tests/state/` (deliberately *not* gitignored — a nested `state` is not the root runtime dir). | **Yes.** Tests hard-code relative paths to `orchestration/handoffs`, fixtures and `src`. **Never move.** |
| [`config/`](config) | source | Runtime configuration: `resextract.toml`, `targets.toml`, `graph_pin.toml`. | **Yes.** Loaded by path at startup; `graph_pin.toml`'s tracked-ness is pinned by a verifier check. **Never move.** |
| [`docs/`](docs) | source | The written record and the spec: `PLAN.md` (spec of record), `ACCEPTANCE_PROTOCOL.md`, `OPERATIONS.md`, `LESSONS.md`, `TARGET_POLICY.md`, `SECRET_SCAN_POLICY.md`, `LIVE_TARGET_NOTES.md`, `PLAN_CORRECTIONS*.md`. | Referenced by `AGENTS.md` and by units. Treat as source; editing it changes the contract. |
| [`orchestration/`](orchestration) | mixed | Where the multi-unit build records itself. See §2. | **Yes — and its two subdirectories are contract-locked.** |
| [`pyproject.toml`](pyproject.toml) | source | Package metadata + tool configuration (pytest, etc.). | **Yes.** Test/CLI behaviour depends on it. **Never move.** |
| [`AGENTS.md`](AGENTS.md) | source | Governance: the unit contract, the ≤5-subagent concurrency cap, hard constraints. | Yes — it is the contract every unit reads. |
| [`.gitignore`](.gitignore) | source | Ignore rules whose **semantics** (not text) are pinned by `tests/test_repo_hygiene.py`: root-anchored `/dockets/` and `/state/`, deliberately global `*.sqlite-wal/-shm/-journal` and `**/*.tmp`. | **Yes.** A careless edit fails the hygiene guard. Do not "tidy" these rules. |
| [`state/`](state) | runtime | Gitignored local runtime state: 58 items — SQLite DBs and sidecars, scratch dirs (`U5.*`, `U6.*`, `U8.*`), backups, `logs/` (frozen baselines used by the handoff-shape guard). | **Yes.** Units read/write it and the frozen baselines live here. **Never move**; also never commit it. |
| [`dockets/`](dockets) | derived | Produced dockets (`duval/`, `_smoke/`). Root-anchored-gitignored, so whether it should be versioned is a **known open question for the user** — deliberately left as-is. | **Yes, by convention.** Docket paths are stored workspace-relative in the store. **Never move.** |
| [`journal/`](journal) | evidence | 16 items: dated entries `2026-09-28.md` … `2026-10-13.md` plus `INDEX.md`. Untracked. | No code depends on it. It is the running narrative record. |
| [`strategy/`](strategy) | evidence | 9 items: paper candidates, publication strategy, social presence, visa routes, verification reports. Untracked. | No code depends on it. Human-facing analysis. |
| [`archive/`](archive) | evidence | **NEW (USTRUCT).** Loose root artifacts preserved, not deleted, with an explanatory [`README.md`](archive/README.md). | Nothing depends on it. Purely preserved evidence. |
| [`jobs/`](jobs/README.md) | derived | **NEW (USTRUCT).** Job-search workstream root: five subdomain trees, each with `FINDINGS.md` + `JOBS.jsonl`. Parent + README created by USTRUCT; the child contents belong to sibling units. | Owned by the job-search units. USTRUCT must not touch `jobs/<slug>/`. |
| [`experiments/`](experiments/README.md) | evidence | **NEW (USTRUCT).** Sandboxed experiments, each with `EVIDENCE.md` + `RUN.json`; rule: work on a **sandbox copy**, never on `/home/zer0null/Duval`. | Owned by the experiment unit (`experiments/second-labeller-190/` is the first expected). |
| [`.git/`](.git) | runtime | Git metadata. HEAD at the time of writing: `41ad35b`. | Yes, but it is VCS internals — never hand-edit. |
| `.pytest_cache/` | runtime | Pytest's own cache. Disposable. | No. |
| `.venv/` | runtime | Local virtualenv. Gitignored via root-anchored `/.venv/`; a *nested* `.venv` belongs to another project. | Yes at run time (`.venv/bin/python -m pytest`), but it is environment, not source. |

---

## 2. `orchestration/` in detail — the contract-locked directory

| Path | Kind | What it is | Must never be moved? |
|---|---|---|---|
| [`orchestration/handoffs/`](orchestration/handoffs) | evidence | **231 files.** Every unit's forced report-back: `orchestration/handoffs/<UNIT>.json`, machine-read by the main session. | **YES — contract-locked.** |
| [`orchestration/units/`](orchestration/units) | evidence | **218 files.** Every unit's persisted card: `orchestration/units/<UNIT>.md`. | **YES — contract-locked.** |
| [`orchestration/STATUS.md`](orchestration/STATUS.md) | source | The batch/unit table and live status. | Not path-locked, but it is the status surface. |
| [`orchestration/VERDICTS.md`](orchestration/VERDICTS.md) | evidence | Verifier verdicts (325 KB of the build's independent checks). | Historically referenced; treat as append-only record. |
| [`orchestration/CLOSING.md`](orchestration/CLOSING.md) | evidence | Closing record of the build. | Append-only record. |

**Why `handoffs/` and `units/` must never be moved, renamed or deleted.** These are not just
files: they are a **contract**. `tests/test_orchestration_handoffs.py` parses *every*
`orchestration/handoffs/*.json` (skipping only a file whose bytes change between two immediate
reads, i.e. mid-write) and fails on any stable file that is not valid JSON or that has lost a
required key of the unit or verifier shape. The unit contract in `AGENTS.md` names these paths
as where each unit persists its own card and report. Move one file and the guard's glob no
longer sees it, the build's provenance record develops a hole, and the tests break. Archiving
or "tidying" them is exactly the kind of full reorganisation this workspace must **not** get.

---

## 3. Paths that must never be moved — and why, in one list

| Path | Why it is frozen |
|---|---|
| `orchestration/handoffs/` | Globbed and parsed by `tests/test_orchestration_handoffs.py`; it is the machine-read report-back contract. |
| `orchestration/units/` | The unit-card half of the same contract, named by `AGENTS.md`. |
| `src/` | Imported by the test suite and the CLI; the product itself. |
| `tests/` | Tests locate fixtures, `src/` and `orchestration/` by relative path from their own location. |
| `config/` | Loaded by path at startup; `graph_pin.toml`'s tracked status is independently checked. |
| `state/` | Gitignored runtime state that live units are actively writing; frozen baselines under `state/logs/` are read by the handoff-shape guard. Do not move, and do not commit. |
| `dockets/` | Docket roots are recorded workspace-relative in the store; moving the root creates new rows by design. Whether to version it is an open user decision — leave it alone. |

Additionally: **nothing may be written outside this workspace**, and the acceptance target
`/home/zer0null/Duval` is **strictly read-only** — never opened, never written, no `git` state
changes, no hooks.

---

## 4. What USTRUCT deliberately did **not** restructure (honest scope statement)

The obvious reading of "give the workspace a clean top-level organisation" is "reorganise the
repo". **That was not done, on purpose.** A full reorganisation would have broken the
orchestration contract and the test suite, so the work here is deliberately confined to the
top level. Concretely, USTRUCT did **not**:

1. **Touch `orchestration/handoffs/` or `orchestration/units/`** (231 + 218 files). Their paths
   are parsed by a guard test and named by `AGENTS.md`'s unit contract; grouping them by unit
   family or by batch would break both. Left byte-for-byte alone.
2. **Touch `src/`, `tests/`, `config/`, `dockets/`, `docs/`, `state/`, `pyproject.toml` or
   `AGENTS.md`.** These are source, fixtures, or live runtime state; other units are reading and
   writing them right now.
3. **Touch `jobs/<slug>/` or `experiments/<name>/` child contents.** Sibling units created their
   own directories concurrently; USTRUCT creates the parent + README only, and this is a hard
   constraint, not a convenience.
4. **Stage, commit or `git rm` anything.** `state/state.sqlite`, the `dockets/` versioning
   question and `*.tmp` handling are explicit **open user decisions** recorded in
   `orchestration/VERDICTS.md`. Moving the two stray root files into `archive/` leaves git
   *status* cleaner, but that is a side effect, not a commit: nothing was staged.
5. **Rewrite the historical records.** `orchestration/handoffs/U5.3.json`, `units/U5.3.md`,
   `units/U0.15.md`, several `U8.*` handoffs and `VERDICTS.md` still refer to
   `U5.3_red1.txt` / `U5.3_red2.txt` at their **old root paths**. Those are frozen evidence of
   what was true at the time and were deliberately left unedited; `archive/README.md` records
   the move so the reference is traceable.
6. **Run the test suite.** Other processes may be mid-write under `state/`; only read-only
   commands were used. (The move's test-neutrality is an argument, not a measured green run —
   see §5.)

**Net effect:** the root went from "source dirs + two stray dumps + a `file:` accident" to
"source dirs + `archive/` + two documented workstream roots". Everything that carries a
contract was left alone.

---

## 5. Why the moves here are safe (the argument, stated plainly)

- `archive/U5.3_red{1,2}.txt` are **untracked** files that **no test and no code reads** —
  verified by searching the whole repo for their names: every hit is a *historical record*
  (handoffs, unit cards, `VERDICTS.md`) or a docstring that names the different
  `state/logs/U5.3_red{1,2}.txt` pytest logs. `tests/test_repo_hygiene.py` asserts `.gitignore`
  *semantics* via `git check-ignore` and names neither the files nor `archive/`, so a new
  directory cannot trip it.
- They were **not deleted**, because they are **unique**: the root copies are full module
  snapshots (1,043 / 1,058 lines) while the same-named files under `state/logs/` are short
  pytest logs (1,295 / 1,304 B) with different hashes. The only copy of that pre-fix revision
  is now in `archive/`, with its sha256 recorded.
- The `file:` tree held **zero regular files**, so removing it destroyed nothing; `rmdir` was
  used so that the command could only ever succeed on an empty directory.
- `jobs/` and `experiments/` are brand-new directories; creating them cannot collide with the
  sibling units, which expect exactly these parents.

---

## 6. Where to put new things

| You have… | Put it in… |
|---|---|
| Product code | `src/resextract/` |
| A guard or behaviour test | `tests/` (see `test_repo_hygiene.py` for the "pin semantics, name the rule" style) |
| A unit's own card / report | `orchestration/units/<UNIT>.md` / `orchestration/handoffs/<UNIT>.json` — **valid JSON**, contracted shape |
| Job-search results | `jobs/<slug>/FINDINGS.md` + `jobs/<slug>/JOBS.jsonl` |
| An experiment | `experiments/<name>/EVIDENCE.md` + `experiments/<name>/RUN.json`, on a **sandbox copy** |
| Scratch, DBs, one-off outputs | `state/` (gitignored, never committed) |
| An obsolete root artifact worth keeping | `archive/` + a line in `archive/README.md` |
| A produced docket | `dockets/` (versioning still an open user decision) |
