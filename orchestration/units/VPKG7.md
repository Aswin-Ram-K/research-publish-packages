# VPKG7 — independent verification of UPKGINSTALL7 (paper #7 release package)

Status: IN PROGRESS (skeleton written before any work)

## Purpose
Re-derive, from the files, every number UPKGINSTALL7 claimed about the paper #7 release
package and its deposit archive; then check what it did NOT claim (single top-level dir,
extraction vs payload identity, payload internal consistency, licence template identity,
internal-path/unit-id leakage, clean-state rebuild reproducibility, README accuracy).

## Bound
20 tool calls. If a claim cannot be checked in 3 attempts -> `unverified`, not guessed.

## Declared write paths
`scratch/vpkg7/**`, `orchestration/units/VPKG7.md`, `orchestration/handoffs/VPKG7.json`,
`strategy/VERIFICATION_REPORT_PKG7.md`.

## Frozen artifacts (never modified; copies only)
- payload dir `papers/gated-read-batching/released/gated-read-batching-released/`
- archive `papers/gated-read-batching/released/gated-read-batching-released.tar.gz`

## Claims under test (verbatim from UPKGINSTALL7 handoff)
1. payload = 12 files; archive named `gated-read-batching-released.tar.gz`
2. archive 126,032 B, sha256 8eedf2e2..., md5 af513024..., 16 members = 1 top dir + 3 subdirs + 12 files, exactly one top-level dir
3. built twice -> byte-identical (cmp 0)
4. check_manifest.py on payload and on clean extraction -> all counters 0, VERDICT PASS, exit 0
5. verify/recompute-claims.py in extraction -> exit 0, 49/49 passed, VERDICT PASS
6. red->green: flip byte at offset 1,000,000 of data/gated-read-rows.jsonl -> hash_mismatch=1, VERDICT FAIL, exit 1; restore -> exit 0, md5 3aad1ae2...
7. payload MANIFEST.json counts.files=12, counts.bytes_total=2372774, 11 entries
8. CITATION.cff: parses as YAML, no `doi` field, licence PolyForm-Noncommercial-1.0.0, author Aswin Ram Kalugasala Moorthy

## Findings (verdict: partial)

All 8 quoted claims reproduced exactly from the files: 126,032 B / sha256 8eedf2e2… /
md5 af513024…; 16 members (4 dirs + 12 files); one top-level dir; extraction byte-identical to
payload for all 12 files; check_manifest PASS both trees; recompute-claims 49/49 PASS; red→green
exact (hash_mismatch=1, FAIL/exit 1, restore md5 3aad1ae2…); MANIFEST counts 12 / 2372774 / 11
entries; CITATION parses, no doi, PolyForm-Noncommercial-1.0.0, author correct.

Clean-state rebuild passes: two fresh stages, cmp 0, shipped sha256/md5 reproduced, rebuilt payload
tree diff-identical (script reads no prior archive; inputs sha256-pinned).

Fails the checks the report did not make:
- **Leak (FAIL).** `UPKG7B` in `MANIFEST.json:3,5`; `scratch/` paths in `README.md:72,73,125` and
  `GATED_READ_PROVENANCE.md:276`; `tools/package` in `MANIFEST.json:5`, `README_DEPOSIT.md:140`,
  `README.md:129`; `papers/gated-read-batching/…` in `README.md:3,29` and `verify/recompute-claims.py:20`;
  `state/refresh-verify/duval/…` in `README.md:107`; target name `duval` in 4 e2e rows of
  `data/gated-read-rows.jsonl` (`"answer": "2026-09-28-duval-m0"`). 6 of 12 files affected.
- **LICENSE scope wrong.** Appended scope section says `fixture/` and `second-labeller/` ship;
  neither exists in this package. PolyForm body itself verbatim (offset 115, 4,563 B, ffcca388…).
- **Templates:** COMMERCIAL.md identical; LICENSE/CONTRIBUTING.md intentionally edited, not identical.
- Release `README.md` is accurate about the deposit artifact (tar.gz), byte-identity claim true;
  does not warn about extracting in place colliding with the same-named payload dir.

Frozen artifacts untouched (sha256/md5 unchanged; mtime 2026-10-19 01:10:54). Report:
`strategy/VERIFICATION_REPORT_PKG7.md`.
