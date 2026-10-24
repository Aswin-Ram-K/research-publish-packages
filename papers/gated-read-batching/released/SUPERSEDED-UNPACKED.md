# SUPERSEDED — unpacked release trees moved out of this directory

Dated 2026-10-19.

## What moved (moved, not deleted)

| was | now |
|---|---|
| `released/gated-read-batching-released/` | `scratch/ugatedtidy/superseded-unpacked/gated-read-batching-released/` |
| `released/gated-read-batching-released (2)/` | `scratch/ugatedtidy/superseded-unpacked/gated-read-batching-released-2/` (space in the name normalised) |

## Why

Both unpacked trees sat beside the live archive under the **same filename stem** — the exact
arrangement that has previously led a unit to mistake a stale unpacked tree for the current
deposit. The unpacked copies are not authoritative; the archive is.

Measured **before** the move (this unit, 2026-10-19):

| tree | files | bytes (`du -sb`) | `CITATION.cff` sha256 | `MANIFEST.json` sha256 |
|---|---|---|---|---|
| `gated-read-batching-released/` | 12 | 2,383,439 | `9a70d43b0104a7bd4c2bc30993b105efdf7dae9055dbbd217f6c8d07a456e02f` | `c04cab2496cdc141ecfdc711c04fe7b07d1a4b5ff04c1170b646b893ede8fb44` |
| `gated-read-batching-released (2)/` | 12 | 2,383,883 | `7d55667c8ed58f351eb24e2a4c9e89fd773b67bef622865d3bcb726895b20a13` | `776514190a43c1c20f57272f036c93aa8e4f565be7d8e25011bb00a85d6a8626` |

Honest correction to the record, not smoothed over: the two trees were **not equally stale**.

- `gated-read-batching-released/` measured **byte-identical to the archive's tree** (`diff -rq`
  against a fresh extraction reported no differences). It was a redundant second copy, not a
  content-stale one; it was moved anyway because a second copy under the same stem is precisely
  what gets mistaken for the current artifact.
- `gated-read-batching-released (2)/` **is content-stale**: it differs from the archive in 3 files —
  `CITATION.cff`, `MANIFEST.json`, `README_DEPOSIT.md` — and its `CITATION.cff` still asserts
  "No DOI has been minted for this deposit yet", which contradicts the shipped deposit's concept
  DOI `10.5281/zenodo.23483314`.

## Authoritative artifact

`papers/gated-read-batching/released/gated-read-batching-released.tar.gz` — **128,902 bytes**,
md5 `a7e81bf7c8ebe49da83e869a002be1b2`, sha256
`e2ceb554f319cb898221c655f1b64ba0e8a022e4e0ad9ffc3fda5fbecd464b24`. 16 members (1 dir + 3 subdirs
+ 12 files), built by `scratch/upkginstall7/build_archive.sh`; do not hand-zip in its place.

## Integrity of the moved trees

Each moved tree has a sha256 manifest beside it in `scratch/ugatedtidy/superseded-unpacked/`
(`gated-read-batching-released.sha256`, `gated-read-batching-released-2.sha256`); `sha256sum -c`
verified **12/12 OK** for each after the move.
