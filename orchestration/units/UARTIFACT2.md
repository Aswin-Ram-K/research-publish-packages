# UARTIFACT2 — close post-DOI artifact gaps

**Bound:** 25 tool calls (used ~24). **Write grant:** `scratch/ufixman1/build_archive.sh`,
`scratch/uzenodo2/run2/CITATION.cff`, `strategy/DEPOSIT_ARCHIVE.md`,
`papers/encoder-crossover-190/rendered/**`, `papers/encoder-crossover-190/released/**` (stray trees +
markers only), `scratch/uartifact2/**`, `scratch/_superseded-unpacked/**`, own card/handoff.

## Measured (all card-quoted values verified)

- Archaved shipped tarball: 159,085 B, sha256 `add182e7…`, md5 `479f3525…`, 37 members.
- Archive `CITATION.cff` 2,006 B / `56300d7c…`; `README_DEPOSIT.md` 10,585 B / `71f76e60…`;
  `MANIFEST.json` 11,761 B / `14c19015…`, `bytes_total` 844,877, `manifest_self` `5afab382…`.

## Done

1. Reproduced the guard failure (`README_DEPOSIT.md drifted: 71f76e60…`, exit 1); repaired the
   CITATION source and three pins/recipe divergences; proved `BYTE-IDENTICAL` (cmp exit 0).
2. Refreshed `strategy/DEPOSIT_ARCHIVE.md` (new primary, old as dated history) + classified every sweep hit.
3. Regenerated the stale HTML via `convert.py` (86,041 B, DOI present, `AUTHOR SLOT` 0); kept old copy in `_superseded/`.
4. Moved both stray trees to `scratch/_superseded-unpacked/` with README + digests; shipped tarball unchanged.
