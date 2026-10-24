# UFIXPKG3 — fix the released payload for paper #3

**Purpose:** One purpose. Fix three measured defects in the released payload
`scratch/uneutral10/package` (29 files) and prove no published number moves.

## Inputs read
- `strategy/RESIDUAL_TRIAGE_3.md` (diagnosis; §A.2 = the 109/37 bucket-(a) list, §C.2 = checker defect).
- `scratch/uneutral10/package/**` (authoritative payload, edited in place).
- `scratch/urecut1/build.py:94-137` (the documented manifest procedure to replicate).
- `scratch/uneutral10/verify/recompute-claims.py`.

## The three fixes
1. **Genericise 109 occurrences / 37 distinct bucket-(a) tokens** (internal unit names + working-dir
   artefacts) to neutral tags. Mapping held in memory, never written into the payload.
   Longest-first replacement so prefixes cannot mis-match.
2. **`verify/recompute-claims.py`**: correct stale expectation `0.3526` → tree value, and fold the
   `PUBLISHED_STALE` reporting loop's `hit` flag into `ok` so a non-reproduced published value
   forces a non-zero exit and an honest summary line. Nothing else made less strict.
3. **Regenerate `MANIFEST.json`** per the package's own documented procedure (replicating
   `scratch/urecut1/build.py:94-137`); prove with an independent check of my own.

## Evidence to produce
- exit codes + stdout of `verify/recompute-claims.py`, `second-labeller/parse_fixture.py`,
  `second-labeller/compare.py` on backup (`scratch/ufixpkg3/before/`) and edited tree — diffed.
- red→green: on a COPY, break one published expectation → non-zero exit + honest summary;
  restore → green.
- idempotence: build `MANIFEST.json` twice; diff; name any timestamp field.
- before/after file count and changed-file list.

## Declared write paths
- `scratch/uneutral10/package/**`
- `strategy/RELEASE_BUILD_3.md` (append)
- `orchestration/units/UFIXPKG3.md`
- `orchestration/handoffs/UFIXPKG3.json`
- `scratch/ufixpkg3/**`

## Bound
25 tool calls. Not edited: `orchestration/units/UBUILD1.build.sh`, `orchestration/packages/**`,
`papers/**`, `tests/**`. No git against `/home/zer0null/Duval`. No installs, no fetches.
