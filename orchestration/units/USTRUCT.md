# USTRUCT — top-level workspace organisation (documented, non-destructive)

**Unit:** USTRUCT · **Parent:** main session (`session-c3d61727-8af8-4c19-b1b9-5922c347a11a`)
**Purpose (one):** give the workspace a clean, documented **top-level** organisation without
breaking anything that already works.

**Hard bound:** maximum 35 tool calls; STOP and report `partial` if that would be exceeded.
**Declared write paths:** `STRUCTURE.md`, `archive/**`, `jobs/README.md`, `experiments/README.md`,
`orchestration/units/USTRUCT.md`, `orchestration/handoffs/USTRUCT.json`. Nothing else was touched.

## Constraints applied

- **Never** move/rename/delete under `orchestration/handoffs/` (231 files) or `orchestration/units/` (218 files)
  — `tests/test_orchestration_handoffs.py` parses every file there.
- **Never** touch `src/`, `tests/`, `config/`, `dockets/`, `docs/`, `state/`, `pyproject.toml`, `AGENTS.md`.
- **Never** move/rename/delete under `jobs/<slug>/` or `experiments/<name>/` — sibling units are writing there now.
- `/home/zer0null/Duval` not opened at all (strictly read-only target).
- Nothing written outside `/home/zer0null/reserach extarctor`.
- The test suite was **not** run (a concurrent process may be mid-write in `state/`); read-only commands only.
- No `git add`, `git commit`, `git rm`, `git mv`.

## What was done

1. **Inspected the strays before acting.**
   - `U5.3_red1.txt` (37,726 B, 1,043 lines): the **pre-fix** full-module revision of
     `src/resextract/docket/materialize.py` — U5.3's red→green evidence pair. Unique content:
     **not** a duplicate of `state/logs/U5.3_red1.txt` (1,295 B, the short pytest log; different sha256).
   - `U5.3_red2.txt` (38,370 B, 1,058 lines): the **post-fix** revision of the same module.
   - `file:`: a 5-directory tree mirroring `file:/home/zer0null/reserach extarctor/state/`,
     holding **0 regular files** — an artifact of a shell redirect that mistook `file:...` for a path.
2. **Created `archive/`** and moved the two dumps in, names preserved, with
   `archive/README.md` describing each file, its origin, its sha256 and why it is preserved
   (never deleted — each is the only copy of that revision). Removed the empty `file:` tree with
   `rmdir` (which can only ever delete empty directories) and recorded its reconstructed path in
   the README.
3. **Created the workstream roots** `jobs/README.md` (five slugs; required `FINDINGS.md` +
   `JOBS.jsonl` per slug) and `experiments/README.md` (sandbox-copy rule; never
   `/home/zer0null/Duval`; `EVIDENCE.md` + `RUN.json`). Parents + READMEs only — no child contents.
4. **Wrote `STRUCTURE.md`**: every one of the 18 top-level entries with kind
   (source/derived/evidence/runtime) and path-dependency, the contract-locked paths and why, a
   "where to put new things" table, and an explicit honest-scope section on what was *not*
   restructured.
5. **No `.gitkeep` added** — `jobs/` and `experiments/` are non-empty (they contain their READMEs),
   so none was needed.

## Evidence

| Check | Result |
|---|---|
| `find "file:" -type f \| head` | empty output → 0 regular files; 5 directories |
| `ls -laR "file:"` | only `.` and `..` at all 5 levels; path below it is `…/reserach extarctor/state/` |
| `sha256sum U5.3_red1.txt state/logs/U5.3_red1.txt` | `f6bfde35…` vs `74859190…` → **different files** (root = module snapshot; state/logs = pytest log) |
| `diff U5.3_red1.txt U5.3_red2.txt` (digits stripped) | red2 adds the `outside_target_root` branch + the `MaterializeRefused` guard → the red/green pair |
| before counts | handoffs 231 · units 218 · state 58 · strategy 9 · journal 16 |
| after counts | handoffs 231 · units 218 (unchanged — nothing moved) |
| `grep -rn "U5\.3_red"` repo-wide | all hits are historical records (U5.3/U0.15/U8.*/VERDICTS) or docstrings naming `state/logs/…`; **no test reads the root files** |
| `ls -A` root after | `.git .gitignore .pytest_cache .venv AGENTS.md archive config dockets docs experiments jobs journal orchestration pyproject.toml src state strategy tests` |
| `rmdir` on `file:` tree | succeeded → every level was empty (would have failed otherwise) |

## Status

`done`. Deliberate non-goal, stated plainly: this is **not** a full reorganisation. Grouping
`orchestration/handoffs` / `orchestration/units`, or moving `src`/`tests`/`config`/`state`, would
break the orchestration handoff contract and the test suite. The changes are confined to the root
plus two new documented parents.
