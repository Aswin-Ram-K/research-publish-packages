# STRUCTURE.md — the filesystem map of this workspace

**Last verified:** 2026-10-28 · **Workspace root:** `/home/zer0null/research extractor`
**Read with:** [`AGENTS.md`](AGENTS.md) — how work happens (owner mode, documentation contract, hard
constraints) · [`docs/STATE.md`](docs/STATE.md) — the current state of every program ·
[`docs/INDEX.md`](docs/INDEX.md) — the document map.

**This page is a map, not a status page.** Where a directory's *state* matters it points at
`docs/STATE.md` instead of repeating it, because a status duplicated here goes stale silently.

**How the numbers below were obtained.** Measured from the real root on 2026-10-28 with
`os.listdir` / `os.walk` (`__pycache__` and `.git` excluded unless stated) plus
`git --no-optional-locks status --porcelain | wc -l`. They are anchors, not invariants: `scratch/`,
`orchestration/handoffs/` and `orchestration/units/` grow while sessions run, and `state/` churns
hard enough that its file count changed on every measurement in this pass (`state/logs/` alone read
1,609 and 2,429 files within the same verification session). Re-measure before quoting.

**Path spelling.** The root is `research extractor`. A former misspelling (`reserach extarctor`)
survives in documents dated 2026-10-08 … 2026-10-28 as a *record of what was run*; it does not exist
on disk today and must never be copied into a live instruction (AGENTS.md §3, §9).

---

## 0. Before you trust anything here

If `pwd` is inside `~/.omp/wt/…`, you are in a **linked worktree**: it holds tracked files only and
lacks the ~1,300 untracked evidence files that *are* the current state (AGENTS.md §9). Read and write
absolute paths under `/home/zer0null/research extractor`. Guard tests compute `ROOT` from
`__file__`, so a test run inside a worktree tests the worktree, not this workspace.

---

## 1. Top level

`kind` is **source** (hand-written, depended upon) · **derived** (regenerable output) ·
**evidence** (records of what was done) · **runtime** (local state, not part of the product).

### 1.1 Contract, source and guards

| Entry | Kind | What it is | Depended on? |
|---|---|---|---|
| [`src/`](src) | source | `src/resextract/` — the `resextract` package (23 entries, 113 files, newest 2026-10-23): repo→docket pipeline, CLI `resextract`. | **Yes.** `tests/` imports it and `pyproject.toml` packages it. **Never move.** |
| [`tests/`](tests) | source | 97 top-level `*.py` tests, plus `fixtures/` (11 fixture trees: `claims-store`, `copy-src`, `dashboard-store`, `docket-store`, `ingest-repo`, `kg-mini`, `lanes-store`, `mine-mini`, `policy-repo`, `refresh-repo`, `staging-repo`) and a nested `tests/state/` (deliberately *not* gitignored — a nested `state` is not the root runtime dir). 197 files excluding `__pycache__` (225 with them). | **Yes.** Tests locate fixtures, `src/` and `orchestration/` by relative path. **Never move.** |
| [`config/`](config) | source | Exactly 3 files: `resextract.toml`, `targets.toml`, `graph_pin.toml` (newest 2026-10-23). | **Yes.** Loaded by path at startup; `graph_pin.toml`'s tracked status is checked. **Never move.** |
| [`tools/`](tools) | source | 11 entries, 20 files excluding `__pycache__`: six flat scripts — `best_config_build.py`, `check_research_notes.py`, `ci_backfill.py`, `release_serving_check.py`, plus the two documentation guards `doc_check.py` and `session_start.py` (both created 2026-10-28) — and four subdirs (`audit/` 2 files, `board/` 1, `integrity/` 1, `package/` 10). Newest 2026-10-28. | Run by `AGENTS.md` §0.4, §3.3, §10 and by package/release checks. |
| [`AGENTS.md`](AGENTS.md) | source | The session contract: owner mode, documentation contract, hard constraints, delegation, traps. | **Yes** — every session reads it first. |
| [`pyproject.toml`](pyproject.toml) | source | Package metadata + pytest/tool configuration. | **Yes.** **Never move.** |
| [`.gitignore`](.gitignore) | source | Ignore rules whose **semantics** (not text) are pinned by `tests/test_repo_hygiene.py`: root-anchored `/dockets/`, `/state/`, `/.venv/`, `/.pytest_cache/`; global `*.sqlite-wal/-shm/-journal`, `**/*.tmp`, `__pycache__/`. | **Yes.** A careless edit fails the hygiene guard. Do not "tidy" them. |
| [`orchestration/`](orchestration) | mixed | Where the unit-era build recorded itself — see §2. | **Yes**, and two of its subdirectories are contract-locked. |
| [`docs/`](docs) | source | 177 entries: **157 top-level** (156 docs + `INDEX.md`) + `research/` (3), `serving-options/` (12), `prompt-system/` (5: 4 `.md` + `RELEASE-v1.json`) = **176 `.md` files**. Newest: `docs/STATE.md` and `docs/INDEX.md` (2026-10-28). `docs/STATE.md` is the current-state page; `docs/PLAN.md` is the historical build spec; `docs/INDEX.md` is the map. | Referenced by `AGENTS.md` and by every unit. Editing it changes the contract. |
| [`journal/`](journal) | evidence | 19 files: **18 dated entries** — `2026-09-28.md` … `2026-10-13.md` (15), `2026-10-26.md`, `2026-10-27.md`, `2026-10-28.md` — plus `INDEX.md`. There is **no daily entry between 2026-10-13 and 2026-10-26**; that window's records are the `orchestration/` documents (`STATUS.md`, `DRIVER_LOG.md`, `VERDICTS.md`) and dated `docs/` pages [INFERENCE — no exhaustive coverage check]. | The narrative half of the documentation contract (`AGENTS.md` §3.1, §3.5). No code depends on the paths. |
| [`archive/`](archive) | evidence | 3 files: `README.md` + `U5.3_red1.txt` / `U5.3_red2.txt` (unique pre-fix module snapshots, 1,043/1,058 lines, kept instead of deleted). | Nothing. Preserved evidence only. |

### 1.2 Evidence and workstreams

| Entry | Kind | What it is | Depended on? |
|---|---|---|---|
| [`experiments/`](experiments/README.md) | evidence | **6 experiment dirs** + `README.md`, 2,098 files excluding `__pycache__` (2,458 with them): `ptr-engine/` (**live**, 941 files, newest 2026-10-28), `miss-law/` (2026-10-26), `agentic-lazy/`, `context-cache/` (2026-10-24), `second-labeller-190/`, `token-substitution-test/` (2026-10-15). Rule: each experiment is sandboxed, never run against `/home/zer0null/Duval`. | `ptr-engine` is the live program (§4); its tests live inside it. |
| [`papers/`](papers) | evidence | 4 paper trees, 136 files, newest 2026-10-26: `encoder-crossover-190/`, `replay-record-not-decision/`, `gated-read-batching/`, `context-cache/`. Each holds `MANUSCRIPT.md`, claims/evidence/gaps docs, `tmlr/`, `submission/`, `rendered/`, `released/`. | The paper track (§4). `submission-kit/` is the upload source of truth, not these trees. |
| [`submission-kit/`](submission-kit) | evidence | 10 files: `README.md` + `abstracts/` (3), `preprints/` (3), `tmlr/` (3). Newest 2026-10-19. | **Yes for uploads** — `docs/STATE.md` §2 names it the source of truth. |
| [`strategy/`](strategy) | evidence | 152 entries (151 `.md`), 158 files, newest 2026-10-23: paper candidates, publication strategy, `SUBMISSION_RECORD.md`, social presence, visa routes, verification reports. | No code. Human-facing analysis. |
| [`measure/`](measure) | derived | Root-level machine twins of **pre-2026-10-27** write-ups only: 6 JSON + `research/` (3 files), 9 files, newest 2026-10-26. The live ptr-engine twins (`REQUEST-LEDGER.json`, `GRID-2-FINAL.json`, 491 entries) live in `experiments/ptr-engine/measure/`. | Cited by dated docs. Do not hand-edit a ledger or baseline (`AGENTS.md` §5 rule 7). |
| [`release/`](release) | derived | `REPORT.md`, `REPRO.md`, and `v0.1/` — a sanitised, self-contained snapshot (16 entries, 946 files): `src/`, `tests/`, `config/`, `docs/`, `experiments/`, `papers/`, `repro/`, `state/`, `MANIFEST.json`, licence files. **Tracked in git.** Newest 2026-10-26. | No live code depends on it. It is a release artefact, not a build input — never "fix" it in place. |
| [`repro/`](repro) | evidence | 2 dirs, 102 files: `encoder-crossover-190/` and `encoder-crossover-190-SANITISED/` (harness, fixture, preregistration, results, verify scripts). Newest 2026-10-15. | The paper's reproducibility claim. `release/v0.1/repro/` is a copy. |
| [`research/`](research) | evidence | 2 dirs, 29 files, newest 2026-10-23: `next-candidates/` (R2 serving design scouting, prospective/unapproved) and `tooling/` (incl. `tooling/handoffs/`). | No. |
| [`jobs/`](jobs/README.md) | evidence | **7 subdomain dirs** (`agent-runtime-global`, `coverage-repair`, `evals-safety-foundations`, `india-ai`, `scandinavia-europe`, `us-national-labs`, `us-nonprofit-research`) + `README.md`, `MASTER_SHORTLIST.md`, `MASTER_SHORTLIST.jsonl`. 514 files, newest 2026-10-15. | Owned by the job-search workstream; not part of the research program. |
| [`dockets/`](dockets) | derived | 2 roots, 90 files, newest 2026-10-08: `duval/` (`duval-replay-material`, `duval-u55-pinned`) and `_smoke/` (frozen backward-compatibility witness). Root-anchored-gitignored. | **Yes, by convention** — docket paths are stored workspace-relative. Whether to version it is an open user decision. |
| `handoff from consonance/` | evidence | 6 files, staged 2026-10-25, **not executed**: `handoff.json`, `README.md`, `DO_NOT_REDO.md`, `EXPERIMENTS.md`, `INTERFACE_CONTRACT.md`, `MEASURED_FACTS.md`. | No. Read-only input to a future session. |

### 1.3 Runtime, scratch and caches

| Entry | Kind | What it is | Depended on? |
|---|---|---|---|
| [`state/`](state) | runtime | 69 entries, ~18k files — **moves while sessions run** (the recursive file count changed on every measurement this pass): SQLite DBs + sidecars, per-unit scratch trees (`U2.5*`, `U5.*`, `U6.*`, `U8.*`), `backups/`, `logs/` (773 entries; frozen baselines), `config/`, `claims/`, `kg/`, `ingest/`, `journal/`, `debris/`, `harness-baselines/`, `gap-ledger.json`, `gap-triage.json`. | **Yes.** Gitignored, never committed, never moved. See §3 for the sha-pinned baselines inside it. |
| [`scratch/`](scratch) | runtime | 289 entries, ~29.7k files including byte-compiled caches, newest 2026-10-26. **Not authoritative by policy**, but a few are cited deliverables (`scratch/utmlr1`, `scratch/urecord1`) — do not blanket-delete. Ignored via `.git/info/exclude` (`/scratch/`), not `.gitignore`. | Referenced by some dated docs. |
| [`extarctor/`](extarctor) | runtime | 1 entry (`extarctor/scratch/`), **0 files** — empty legacy tree. | **Nothing depends on it.** Do not add to it; do not read it as source. |
| [`.dsh-progress/`](.dsh-progress) | runtime | 769 entries but only 104 files (mostly empty session dirs), newest 2026-10-27 (`session-*/run-a-star-grid-16.jsonl`). Board/agent-run progress records. Ignored via `.git/info/exclude`. | No. AGENTS.md §8 calls board mode dormant. |
| [`.orchestration/`](.orchestration) | runtime | Only `incidents/` (29 files), newest 2026-10-28T2050. The external watchdog's incident log; lives outside the product. | No. Not a prerequisite for work. |
| `.scratch/` | runtime | 13 files, newest 2026-10-28 (`grid2/VERDICT-REC-F.json`) — per-session scratch. Ignored. | No. |
| `.verify-scratch/` | runtime | 14 entries, 1,033 files, newest 2026-10-24 — verifier working copies (`engine/ptr_engine/…`). Ignored. | No. |
| `.ucurate1/` | runtime | 6 entries, 121 files, 2026-10-15 — curation unit's workspace. `pre/research-publish-packages/` is ignored; the rest is tracked/untracked history. | No. |
| `.uredact3/` | runtime | 20 entries, 483 files, 2026-10-15, **479 tracked in HEAD** — redaction unit's working notes. | No. Leave alone; it is audit history. |
| `.venv/` | runtime | Local virtualenv (root-anchored `/.venv/`). `.venv/bin/python -m pytest` is how tests run. A *nested* `.venv` belongs to another project. | Yes at run time; it is environment, not source. |
| `.pytest_cache/` | runtime | Pytest's own cache. Disposable, root-anchored-ignored. | No. |
| [`.git/`](.git) | runtime | Git metadata. Branch `research/next-candidates-2026-10-24`, HEAD `f17663d` (2026-10-25), 1,351 `--porcelain` entries. | VCS internals — never hand-edit (§5). |

### 1.4 Loose files at the root

All nine are **tracked in HEAD**; they are history, not a pattern to copy. `pristine.json` (0 bytes)
is the only untracked one.

| File | Size | What it is |
|---|---|---|
| `.arg_utils.py` | 122,054 B | Vendored vLLM source (Apache-2.0 header), kept as the reference for a config argument. |
| `.api_server.py` | 29,939 B | Vendored vLLM `api_server.py`, same purpose. |
| `.vllm_cache.py` | 14,663 B | Vendored vLLM cache implementation, same purpose. |
| `.sgl_sa.html` | 1,603,505 B | Saved SGLang page (server-args reference). |
| `.vllm_engine_args.html` | 706,529 B | Saved vLLM engine-args page. |
| `.issue_comments.json` | 16,577 B | 6-item list of GitHub issue comments kept as a citation. |
| `.protocol.py` | 14 B | Contains exactly `404: Not Found` — an accidental curl capture, not code. |
| `_stage_out.txt` | 1,509 B | `scratch/r2-opt-sim` staging output (latency-fit constants). |
| `.occamy.lock` | 73 B | Released lock record (`{"unit":"U6-R","pid":11,"released_utc":…}`). Live cells serialise on this file (`AGENTS.md` §9); a dead lock is released by its owner record, never by killing a runner. |
| `pristine.json` | 0 B | Untracked empty file. |

---

## 2. `orchestration/` in detail — the contract-locked directory

15 entries, 2,577 files.

| Path | Kind | What it is |
|---|---|---|
| [`orchestration/handoffs/`](orchestration/handoffs) | evidence | **1,198 entries**: 1,191 `*.json` unit/verifier reports, 6 `*.md`, and `recovered/` (8 files) — 1,205 files in total. Machine-read by the main session and by the guard. **Contract-locked.** |
| [`orchestration/units/`](orchestration/units) | evidence | **1,116 files**: 1,113 `*.md` unit cards plus `LAUNCHER-GEN6-WIRE.json`, `UBUILD1.build.sh`, `X-SYNTH.json`. Includes `units/TEMPLATE.md`, which is contract text (below). **Contract-locked.** |
| [`orchestration/journals/`](orchestration/journals) | evidence | 235 `*.jsonl` per-unit journals, every one written 2026-10-26 … 2026-10-28 (measured by mtime) — the unit era's machine-readable narrative (`RUN-A-STAR`, `GRID-RUN-2`, `LEASE-REOPEN-23`, `GRID-2-FINAL`, …). |
| [`orchestration/VERDICTS.md`](orchestration/VERDICTS.md) | evidence | 443 KB of verifier verdicts, plus the `VERDICTS.jsonl` twin (1.5 KB). Append-only record. |
| [`orchestration/STATUS.md`](orchestration/STATUS.md) | source | 46.8 KB batch/unit table from the docket era (2026-10-21). **Superseded as current state** by `docs/STATE.md`; still valid as a dated record. |
| [`orchestration/VERDICT-RITUAL.md`](orchestration/VERDICT-RITUAL.md) | source | The verdict ritual text. **Do not edit** — see the warning below. |
| [`orchestration/CLOSING.md`](orchestration/CLOSING.md) | evidence | Closing record of the 2026-10-08 … 2026-10-28 "main session orchestrates only" regime (6.8 KB). |
| `orchestration/cursors/` (1), `verdicts/` (1), `packages/` (10 files), `DRIVER_LOG.md`, `GAPS-INVENTORY.md`, `JOURNAL.md`, `RECORD_REPAIR.md` | mixed | Cursors, packaged verdict sets, the driver log, gap inventory, journal and record-repair notes from the same era. |

**Why `handoffs/` and `units/` must never be moved, renamed or deleted.** They are a **contract**, not
just files. `tests/test_orchestration_handoffs.py` parses *every* `orchestration/handoffs/*.json`
(skipping only a file whose bytes change between two immediate reads, i.e. mid-write) and fails on a
stable file that is not valid JSON or has lost a required key of one of the two contracted shapes —
the seven-key unit handoff and the verifier verdict (`AGENTS.md` §7.5). `AGENTS.md` names these same
paths as where each unit persists its card and report. Move one file and the guard's glob no longer
sees it, the provenance record develops a hole, and the test breaks. Grouping them "by unit family" is
exactly the reorganisation this workspace must not get.

**Contract text — do not edit.** `orchestration/VERDICT-RITUAL.md` and
`orchestration/units/TEMPLATE.md` are asserted *literally* (strings and ordering) by
`experiments/ptr-engine/longrun/tests/test_verdict_ritual.py`. Treat both as frozen contract text; a
change there is an instrument change, not a doc tidy.

---

## 3. Paths that must never be moved

| Path | Measured 2026-10-28 | Why it is frozen |
|---|---|---|
| `orchestration/handoffs/` | 1,198 entries / 1,205 files | Globbed and parsed by `tests/test_orchestration_handoffs.py`; it is the machine-read report-back contract. Append-only. |
| `orchestration/units/` | 1,116 files | The unit-card half of the same contract, named by `AGENTS.md` §7.4. Append-only. |
| `src/` | 119 files | Imported by the test suite and packaged by `pyproject.toml`; the product itself. |
| `tests/` | 97 top-level `*.py` | Tests locate `fixtures/`, `src/` and `orchestration/` by relative path from their own location. |
| `config/` | 3 `.toml` | Loaded by path at startup; `graph_pin.toml`'s tracked status is independently checked. |
| `state/` | 69 entries / ~18k files (moving) | Gitignored runtime state that live units are writing. Do not move, do not commit. |
| `state/logs/` — **gitignored but critical** | 773 entries; 9 `*baseline*` entries at top level (8 files + `U6.16-baseline/`) | `state/logs/U8.15/baseline_gaps.json` and `state/logs/U8.18/verifier_shape_baseline.json` are **sha-pinned** by the handoff guard; a fresh clone fails that guard until they are restored. Baselines are superseded, never edited (`AGENTS.md` §5 rule 7). |
| `dockets/` | 2 roots / 90 files | Docket roots are recorded workspace-relative in the store; moving the root creates new rows by design. Whether to version it is an open user decision — leave it alone. |

Additionally: **nothing may be written outside this workspace**, and the target repo
`/home/zer0null/Duval` (and every registered target) is **strictly read-only** — no writes, no git
state changes, no hooks, and **never walk a target's `.worktrees/`** (`AGENTS.md` §5 rules 1-4).

---

## 4. What is actually live

Three programs, no status duplicated here — read `docs/STATE.md`:

1. **`experiments/ptr-engine/` — LIVE (serving / cache / cost).** 941 files excluding `__pycache__`;
   entry docs `SPEC.md`, `LONGRUN-PREREG.md`, `BOUNDARY-PREREG.md`, `RECORD.md`, `ADOPTION.md`,
   `CHANGELOG-P0.1.md`; subdirs `longrun/` (with its own `tests/`, 78 files), `ptr_engine/`, `tools/`
   (incl. `request_ledger.py`), `quality/`, `measure/` (491 entries), `orchestration/`, `audit/`,
   `examples/`, `tests/` (37 files). Runbook: `docs/GRID-RUNBOOK.md`. Current state:
   `docs/STATE.md` §1.
2. **`src/resextract/` — dormant but contract-load-bearing.** The app still binds `tests/`,
   `config/` and the `resextract` console script; dormancy is not permission to move it. Current
   state: `docs/STATE.md` §3.
3. **The paper track — `papers/` + `strategy/` + `submission-kit/`.** Four paper trees; the upload
   source of truth is `submission-kit/`, not the paper trees. Current state: `docs/STATE.md` §2.

Everything else (`jobs/`, `release/`, `repro/`, `research/`, `handoff from consonance/`) is a
supporting or parked workstream — `docs/STATE.md` §4.

---

## 5. What git sees

- **HEAD is a checkpoint, not the truth.** Branch `research/next-candidates-2026-10-24`, HEAD
  `f17663d` (2026-10-25); `git --no-optional-locks status --porcelain` reports **1,351** entries.
  `docs/`, `journal/`, `strategy/` and most of `experiments/` are untracked. **Never infer "deleted"
  from "absent in HEAD"**, and never run `git clean`, `git reset --hard`, `git checkout -- .`,
  `git add -A` or `git commit -a` unasked (`AGENTS.md` §5 rule 8).
- **Two ignore layers.** `.gitignore` holds the guard-tested rules (§1.1). `.git/info/exclude` holds
  the ephemeral ones added for the 2026-10-26 push: `/scratch/`, `/.scratch/`, `/.verify-scratch/`,
  `/.dsh-progress/`, `**/__pycache__/`, `*.pyc`, `/node_modules/`, `/venv/`, `/.venv/`, one
  `/.ucurate1/…` path, and eleven cached job-board HTML files under `jobs/`. A path that "is not in
  `.gitignore`" may still be ignored — check both.
- **`.uredact3/`** is tracked (479 of its 483 files are in HEAD) and **`release/`** is tracked; they are
  the two largest non-source trees git knows about, so they dominate any "modified" listing that is
  not untracked-file noise.

---

## 6. Where to put new things

Aligned with `AGENTS.md` §6 and the `docs/STATE.md` / `docs/INDEX.md` / `journal/` documentation
contract. **Nothing new belongs at the root** — the loose files in §1.4 are history, not a precedent.

| You have… | Put it in… |
|---|---|
| Product code | `src/resextract/` |
| A guard or behaviour test | `tests/` (house style: pin the semantics, name the rule, record red→green in the docstring) |
| A current-state change | `docs/STATE.md` (+ its `journal/` line) |
| A measurement write-up | `docs/<UPPER-SLUG>.md`, machine twin `measure/<SAME-SLUG>.json` (live ptr-engine twins currently land in `experiments/ptr-engine/measure/`) |
| A new experiment | `experiments/<name>/` with `README.md` (question, status, how to run, where evidence lives), `EVIDENCE.md`, `RUN.json` |
| A daily narrative | `journal/YYYY-MM-DD.md` **and** a row in `journal/INDEX.md` |
| A delegated unit's card / report | `orchestration/units/<UNIT>.md` / `orchestration/handoffs/<UNIT>.json` — **valid JSON**, contracted shape |
| A document index entry | `docs/INDEX.md` — one line per document; `tools/doc_check.py` fails on an unindexed doc or a dead index line (the index file itself is measured absent — §7) |
| A paper or its revision | `papers/<slug>/` |
| Upload-ready paper files | `submission-kit/` (sha256-verified set) |
| Scratch, DBs, one-off outputs | `state/` (gitignored; never commit, never move) |
| A produced docket | `dockets/` (versioning still an open user decision) |
| An obsolete artifact worth keeping | `archive/` + a line in `archive/README.md` |

---

## 7. Contract-named paths: where they actually are

Measured 2026-10-28. Three of the files `AGENTS.md` names appeared on disk **during** this
verification pass (written by a concurrent session at 16:50-16:51), which is why the table records
both the name and the measured location rather than an assumed one.

| Named by | Path | Where it is |
|---|---|---|
| `AGENTS.md` §0.4, §10 | `tools/session_start.py` | **present** (7,807 B, 2026-10-28) — the orientation snapshot. |
| `AGENTS.md` §3.3, §10 | `tools/doc_check.py` | **present** (8,256 B, 2026-10-28) — the doc/journal/STATE coverage guard. |
| `AGENTS.md` §10, `docs/STATE.md` §5 | `tests/test_agent_context.py` | **present** — red→green fixture tests for that guard. |
| `AGENTS.md` §3.3 | `docs/INDEX.md` | **present** (24.3 KB, 2026-10-28) — 177 rows covering 175 docs + itself + this file; `python3 tools/doc_check.py` exits 0. |
| `AGENTS.md` §5 rule 7 | `tools/request_ledger.py` | does not exist at the root — the live tool is `experiments/ptr-engine/tools/request_ledger.py`. |
| `AGENTS.md` §5 rule 7, `docs/STATE.md` §1 | `experiments/ptr-engine/measure/REQUEST-LEDGER.json` | **present** (2026-10-28, rebuilt to 2,591/1,729). Root `measure/` holds only the six pre-2026-10-27 cross-experiment twins; a pre-rebuild copy sits at `state/backups/REQUEST-LEDGER.pre-grid-rebuild.2026-10-28.json`. |

Re-measure this table before quoting it. The three guard files and `docs/INDEX.md` were written by
this session's units on 2026-10-28; re-run `python3 tools/doc_check.py` to confirm they are still in
place.

---

## 8. Layout traps

1. **Worktrees are partial** (§0). Absolute paths, always.
2. **Path spelling** (§header). Dated records keep the misspelling; live instructions must not.
3. **Counts here are anchors.** `state/logs`, `orchestration/handoffs/` and `scratch/` are written by
   running sessions; re-measure rather than quoting this page as current.
4. **`scratch/` is not authoritative but is not garbage.** Some subdirs are cited deliverables
   (`scratch/utmlr1`, `scratch/urecord1`). Never blanket-delete.
5. **`extarctor/` is empty** and `handoff from consonance/` was never executed. Neither is a source of
   truth; do not "restore" them into the live tree.
6. **`release/v0.1/` is a snapshot.** Editing it changes a released artefact. Fix the source tree and
   cut a new release instead.
7. **Do not edit** `orchestration/VERDICT-RITUAL.md` or `orchestration/units/TEMPLATE.md` (§2).
8. **Gitignored-but-critical:** the two sha-pinned baselines under `state/logs/U8.15/` and
   `state/logs/U8.18/` (§3). A fresh clone is not a working checkout without them.
9. **`tests/state/` is not the root `state/`.** It holds test-scoped backups and is *not* ignored,
   because `/state/` in `.gitignore` is root-anchored on purpose (the file's own comments explain why).
