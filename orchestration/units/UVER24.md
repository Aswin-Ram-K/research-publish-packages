# UVER24 — independent verification of unit UDTAG1 (replacement for UVER23)

**Purpose.** Independently re-derive every material claim of UDTAG1's neutralisation of five internal
decision ids in the release artifact copy. This unit replaces UVER23, which died leaving only a
12-line placeholder; `strategy/VERIFICATION_REPORT_23.md` was read and overwritten, as instructed.

**Hard bound.** 25 tool calls. **Used 17.** Stop condition: any failure of the inside-stimulus census
delta to be 0 halts and reports immediately.

**Declared write paths** (nothing else written):
`strategy/VERIFICATION_REPORT_23.md`, `orchestration/units/UVER24.md`,
`orchestration/handoffs/UVER24.json`, `scratch/uver24/**`.

## Method
Never read whole trees; per-file checks in loops printing counts, `grep -rl` file lists, `head`/`tail`,
`diff -rq` line counts. The report file was written early and grown after each step. Tool runs that
would write (`compileall`, `parse_fixture.py`, `compare.py`) were executed on copies under
`scratch/uver24/`, never inside a verified tree.

## What was checked, and how
1. Rename completeness/injectivity in contents and in file/dir names; replacement file-count
   correspondence against the base; `diff -rq` for added/removed paths; the "17 of 45 files" count.
2. Census invariance with the workspace's own `scratch/ubij1/census_one.py`, both trees, `PYTHONHASHSEED=0`.
3. `verify/recompute-claims.py` exit code, literal output, and byte-identity against the base; the
   published constants read out of `papers/encoder-crossover-190/CLAIMS.md`.
4. Exit codes: `compileall`, three JSONL parses with malformed counts, both `second-labeller` tools —
   run in **both** trees to settle pre-existing vs rename-induced.
5. **Own** manifest checker (`scratch/uver24/check_manifest_uver24.py`); the author's `check_emitted.py`
   was deliberately not run.
6. `diff -rq` idempotence between the two builds.
7. Red→green: perturb a copy by one byte, show the checker fails and names the file, restore.
8. Scope: recorded manifest digest still matching disk + newest-mtime ordering vs the unit's handoff.

## Result
`pass-with-corrections`. All material claims reproduced (see
`strategy/VERIFICATION_REPORT_23.md` for the full table of numbers). Two record defects:
`counts.bytes_total` is recorded as 3,009,198 but is 3,008,830 on disk (delta 368) — the artifact is
self-consistent and the record is wrong; and the listed artifact
`scratch/udtag1/udtag1_facts.json` does not exist.

## Deliberately not done
No git command was run anywhere. `/home/zer0null/Duval` and
`/home/zer0null/research-publish-packages` were never written. No file outside the four declared
paths was created or modified.
