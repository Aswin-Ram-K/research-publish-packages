# U-GATEDTIDY — retire stale unpacked trees, fix one false METADATA row

**Bound:** 12 tool calls. **Write paths only:** `papers/gated-read-batching/released/**`,
`papers/gated-read-batching/submission/METADATA.md`, `scratch/ugatedtidy/**`,
`orchestration/units/UGATEDTIDY.md`, `orchestration/handoffs/UGATEDTIDY.json`.

## Job 1 — measurements BEFORE any move (2026-10-19)

Live archive `papers/gated-read-batching/released/gated-read-batching-released.tar.gz`:
128,902 B, md5 `a7e81bf7c8ebe49da83e869a002be1b2` — matches the card.

| tree | files | bytes (du -sb) | CITATION.cff sha256 | MANIFEST.json sha256 |
|---|---|---|---|---|
| `gated-read-batching-released` | 12 | 2,383,439 | `9a70d43b…a456e02f` | `c04cab24…de8fb44` |
| `gated-read-batching-released (2)` | 12 | 2,383,883 | `7d55667c…b520a13` | `77651419…6a8626` |

## Job 2 — METADATA.md line 29, pre-edit md5 `838557647a1b7a04750c3607ddc02dba`
Old row claims "No DOI was minted or guessed" — false in the plain sense (data-deposit concept DOI
10.5281/zenodo.23483314 exists). Reword to distinguish venue DOI (absent) from deposit concept DOI.

## Status
in progress (card persisted first, per contract)

## Outcome (done)

- Both trees moved to `scratch/ugatedtidy/superseded-unpacked/` (`…-released`, `…-released-2` — space normalised);
  sha256 manifests beside each, `sha256sum -c` 12/12 OK each.
- **Recorded disagreement:** tree 1 was byte-identical to the archive (`diff -rq` empty) — a redundant copy,
  not a stale one; tree 2 differed in 3 files and still denied a DOI. Both moved per the card.
- `released/SUPERSEDED-UNPACKED.md` written (dated 2026-10-19) with the authoritative archive's size + md5 + sha256.
- `released/README.md`: one dated SUPERSEDED annotation inserted (1655 → 1787 B, +132, no deletion).
- `submission/METADATA.md` line 29 reworded: venue DOI absent / deposit concept DOI 10.5281/zenodo.23483314 is
  named; old wording kept as a dated note. Containment proof: reverting that row reproduces the pre-edit
  md5 `838557647a1b7a04750c3607ddc02dba`; 176 lines before and after.
- Archive untouched: 128,902 B, md5 `a7e81bf7c8ebe49da83e869a002be1b2` before and after.
- Tool calls used: 11 of 12.
