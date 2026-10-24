# Unit UFIXPKG13 — fix stale packaged digest prose, then re-anchor + de-volatilize the README claim

**Status:** in progress
**Parent:** session-c3d61727-8af8-4c19-b1b9-5922c347a11a
**Hard bound:** 20 tool calls.

## Purpose (one, with two ordered jobs)
Job 2 depends on Job 1 because Job 1 edits shipped files, which changes `MANIFEST.json`.

### Job 1 — packaged prose still prints a pre-clean-up digest
A clean-up removed bytes from the shipped instrument, so its digest moved
`369159b03aa67f1571517ea2a9c3c460d218ee832d00e8ddd4928e5e6da0f78d` (81,284 B)
→ `89e77a8e24a907f06345a45485c013799e08c806cc9d8f075db7709fbfd8e169` (81,439 B).
`MANIFEST.json:74-76` is already correct; the package's own prose still prints the old pair at:
- `scratch/uneutral10/package/results/REPORT.md:5`
- `scratch/uneutral10/package/second-labeller/RUN.json:12`

True values must be **read from `MANIFEST.json` and independently confirmed by sha256sum/stat** — never
taken from the unit card. Three confusable objects:
- as-audited source `repro/encoder-crossover-190/fixture/reflex-decisions.ts` (145,031 B, `076164ac…b4796`)
- shipped instrument `fixture/reflex-decisions.ts`
- shipped fixture `fixture/fixture-190.json`

Only correct a site asserting the **shipped instrument's digest as current**. A dated record of an earlier
state (e.g. a run record) gets an **annotation**, not a rewrite.

### Job 2 — regenerate manifest, then re-anchor the documented value
After Job 1, regenerate `MANIFEST.json` using the package's documented procedure
(`tools/package/regen_manifest.py`, pinned `--generated-utc`, `--no-note` — confirm exact invocation from
tool + README). Then update the known-good block in `tools/package/README.md` (currently pinned to
`generated_utc 2026-10-16T22:51:23Z`) to the new measured values **with the previous ones kept as a dated
historical transcript**, and — more importantly — make the documented claim robust:
state that these figures are payload-volatile, must be re-derived before being cited, and make the
re-derivation command prominent rather than the number.

## Declared write paths
- `scratch/uneutral10/package/**`
- `tools/package/README.md`
- `orchestration/units/UFIXPKG13.md`
- `orchestration/handoffs/UFIXPKG13.json`
- `scratch/ufixpkg13/**`

## Constraints
- `/home/zer0null/Duval` strictly read-only; never run git against it.
- No edits under `papers/**`; report stale paper-side values instead.
- Never change a number to make a checker pass; never introduce an unmeasured number.
- No real release destination.

## Required proof
- before/after for every edit, each before-string asserted to occur exactly once pre-write
- literal commands + output for true current values and the regeneration
- `python3 tools/package/check_manifest.py` → PASS with literal counts
- `verify/recompute-claims.py` still prints its PASS verdict and the same published values;
  `second-labeller/parse_fixture.py` and `second-labeller/compare.py` literal exit codes;
  **no published number may move** (route-B pairwise kappa, A/B mutual agreement, fixture-correctness
  projection digest stated explicitly)
- byte-level comparison showing exactly which package files changed
- handoff JSON re-parses
