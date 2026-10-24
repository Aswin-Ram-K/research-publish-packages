# UVERPKG10 — independent verifier for UFIXPKG10

**Role:** independent verification of unit `UFIXPKG10`'s two claimed corrections (stale published
digest; stale test census expectation). I did not author any artifact under review; every number below
is re-derived from disk by a method written here.

**Hard bound:** 20 tool calls. **Write paths:** `strategy/VERIFICATION_REPORT_PKG10.md`,
`orchestration/units/UVERPKG10.md`, `orchestration/handoffs/UVERPKG10.json`, `scratch/uverpkg10/**`.
Nothing else is written; nothing is fixed, weakened, or installed.

**Concurrency note:** `tools/package/README.md` is being edited by `UFIXPKG11` concurrently. I snapshot
it at the start and judge that snapshot, not a later state.

## Checks planned
1. Shipped instrument digest/size by own `sha256sum`/`stat`; compare to `MANIFEST.json`.
2. Published digest at `papers/encoder-crossover-190/CLAIMS.md:46,47`, `MANUSCRIPT.md:802`,
   `submission/main.tex:408`; sweep for live occurrences of the old digest vs dated history.
3. Near-miss: `AVAILABILITY.md:22` `076164ac…` — different file (as-audited source, 145,031 B).
4. Re-run `scratch/uprep1/md2tex.py` on a copy; two runs byte-identical; diff == claimed line only.
5. Tarball: member count, extracted bytes vs on-disk source.
6. Independent census of the payload for the test expectation (own walk, not UFIXPKG10's script).
7. Run tests via `--noconftest`; record the conftest collection failure plainly.
8. Re-run the three payload tools; literal exit codes + published-value verdicts.
9. Red→green: revert a fix in a scratch copy and show a check fails.
10. Write-path containment: content + mtimes outside declared paths, attributed to the concurrent session.

*(Card persisted first per the unit contract; verdict written to
`orchestration/handoffs/UVERPKG10.json`.)*
