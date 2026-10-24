# UFIXPKG10 — fix two stale package values (published digest + test expectation)

**Purpose (one):** Correct two stale values left by the package clean-up: (1) the live published
digest/byte-count for the shipped instrument `fixture/reflex-decisions.ts` under
`papers/encoder-crossover-190/`, leaving frozen dated records intact; (2) the stale census
expectation in `tests/test_package_tools.py`, after independently re-deriving the totals.

**Hard bound:** 20 tool calls. If the new census totals cannot be independently reproduced within the
bound, STOP and report `partial` with the disagreement rather than editing the test.

**Declared write paths (exactly these):**
- `papers/encoder-crossover-190/**` (incl. `submission/`)
- `tests/test_package_tools.py`
- `tools/package/README.md`
- `orchestration/units/UFIXPKG10.md`
- `orchestration/handoffs/UFIXPKG10.json`
- `scratch/ufixpkg10/**`

**Rule constraints:** `/home/zer0null/Duval` read-only, no git against it; no installs/fetches; no
builds into a real release destination (scratch only); no guard weakened; no new number invented.

**Three objects, never to be conflated:**
- as-audited source: `repro/encoder-crossover-190/fixture/reflex-decisions.ts` — 145,031 B, `076164ac…b4796`
- shipped instrument: `fixture/reflex-decisions.ts` — now `89e77a8e…e169`, 81,439 B (was 81,284 B)
- shipped fixture: `fixture/fixture-190.json` — 76,897 B, `a15224ba…3852e`

**Plan:** read MANIFEST.json for current values → grep all digest/byte sites → read each site → edit
live sites only, date-note frozen records → regenerate `submission/main.tex` via `scratch/uprep1/md2tex.py`
(run twice, byte-identical) → rebuild tarball → independently count census totals over the shipped tree
→ update test + `tools/package/README.md` → run pytest + three package tools → handoff JSON.

**Status:** in progress.
