# Superseded unpacked trees — moved 2026-10-19 (unit UDOITIDY2)

The released archive beside this file is **`replay-record-not-decision-released.tar.gz`**,
107,764 bytes, sha256 `e6f920c432e0dc180ca72336e0bb60b2155462b8365f8800359a24beec3bbe63`,
md5 `41afa2831ff2f43af91d9c4416d8f658`. Its `CITATION.cff` carries the concept DOI
`10.5281/zenodo.23482511`.

Two unpacked trees sat here and no longer matched that archive byte-for-byte:
- `replay-record-not-decision-released/` — carried a pre-DOI CITATION.cff with no doi: field; its `MANIFEST.json` likewise no longer matched. Per-file SHA-256: `scratch/udoitidy2/superseded-unpacked/replay-record-not-decision-released.sha256`.
- `replay-record-not-decision-released (2)/` — carried a pre-DOI CITATION.cff with no doi: field; its `MANIFEST.json` likewise no longer matched. Per-file SHA-256: `scratch/udoitidy2/superseded-unpacked/replay-record-not-decision-released (2).sha256`.

They were **moved, not deleted**, to `scratch/udoitidy2/superseded-unpacked/`, each beside a
`.sha256` manifest recording every file's digest. Reason: a stale unpacked tree beside a live
archive under the same stem is the exact ambiguity this workspace has been bitten by twice before.
The loose `CITATION.cff` and `README_DEPOSIT.md` at this level still match the archive's bytes and
are kept.

---

## 2026-10-19 — a further unpacked tree moved (unit UTREES1)

One unpacked copy had reappeared in this directory: `replay-record-not-decision-released/`. It was
**byte-identical to the archive's tree at the time of moving** — `diff -rq` against a fresh `tar -xzf`
of `replay-record-not-decision-released.tar.gz` produced no output; 10 files, 1,313,443 bytes on both
sides. Unlike the two trees described above, it was **not stale**; it was retired because nothing here
keeps an unpacked copy in sync, and an identical-looking copy beside the archive is the ambiguity this
file exists to prevent.

Moved (not deleted) to:
`scratch/utrees1/superseded-unpacked/replay-record-not-decision/replay-record-not-decision-released/`

The tree is unchanged at the destination; a per-file manifest sits beside it at
`scratch/utrees1/superseded-unpacked/replay-record-not-decision/replay-record-not-decision-released.sha256`
(10 entries, verified with `sha256sum -c`: 10/10 OK).

### Authoritative artifact (measured 2026-10-19, this workspace)

| field | value |
|---|---|
| path | `papers/replay-record-not-decision/released/replay-record-not-decision-released.tar.gz` |
| bytes | 107,764 |
| md5 | `41afa2831ff2f43af91d9c4416d8f658` |
| sha256 | `e6f920c432e0dc180ca72336e0bb60b2155462b8365f8800359a24beec3bbe63` |

Unchanged in size and md5 across this unit's work (measured before and after the move). This directory
now contains only that archive plus `CITATION.cff`, `README_DEPOSIT.md` and this file.
