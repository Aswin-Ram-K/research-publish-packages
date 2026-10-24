# Unit UGATEDDOI — back-fill the Zenodo concept DOI into `gated-read-batching` and rebuild every artifact

**Status:** done (2026-10-19). **Tool-call bound:** 30 — **exceeded, 34 used** (2 calls lost to shell
mistakes: a relative redirect into a `cd`-ed directory, and `tectonic -o` into a non-existent dir).
Recorded here rather than rounded down.

## API confirmation (not taken on trust)
`curl https://zenodo.org/api/records/23483315` → `doi: 10.5281/zenodo.23483315`,
`conceptdoi: 10.5281/zenodo.23483314`, `conceptrecid: 23483314`, `resource_type: dataset`,
`license: polyform-noncommercial-1.0.0`, `language: None`, `publication_date: 2026-10-19`,
one file `gated-read-batching-released.tar.gz` 128,559 B `md5:5c0db7c9afedf5d47747c70e03e8a136`.
`/api/records/23483314` answers **302** (concept records redirect to the version record) — the concept
DOI is confirmed by `conceptdoi` on the version record, not by a second body.
The **local** pre-edit archive's md5 was `5c0db7c9afedf5d47747c70e03e8a136` — i.e. the workspace held
exactly the file Zenodo serves as version 1.

## Edits (before → after)
1. `MANUSCRIPT.md` §Data availability, "Persistent identifier" paragraph: "**No DOI has been minted for
   this deposit and none is claimed here.** … no identifier is predicted or promised." → "**Persistent
   identifier: concept DOI `10.5281/zenodo.23483314`.** … carries the `doi` field with that concept DOI."
   plus a bracketed *Superseded wording, dated 2026-10-19 and kept as dated history* quotation of the old
   paragraph.
2. `AVAILABILITY.md`: summary line "No DOI has been minted for this deposit yet" → concept-DOI line;
   §Persistent identifier rewritten (concept DOI + version record 23483315 + dataset/polyform/licence
   facts + why the concept DOI, not a version DOI) with the old wording kept as a dated superseded block.
3. `released/README.md`: "No DOI yet. None has been minted…" → concept DOI + dated superseded note.
4. deposit `CITATION.cff`: added `doi: "10.5281/zenodo.23483314"`; the "DOI: deliberately absent" comment
   block replaced by a concept-DOI note + dated superseded record.
5. deposit `README_DEPOSIT.md`: same no-DOI paragraph → concept DOI + dated superseded note.
6. Artifact-description numbers re-derived from the rebuilt archive (not invented): archive 128,559 →
   **128,902** B, sha256 `1e3b5781…` → `e2ceb554…`, md5 added; extracted tree 2,383,883 → **2,384,398**
   B; `CITATION.cff` 1,862 → 2,139, `README_DEPOSIT.md` 9,868 → 10,105, `MANIFEST.json` 4,649 → 4,650,
   `bytes_total` 2,379,234 → 2,379,748. A dated "Rebuilt 2026-10-19 for the concept-DOI back-fill" note
   keeps the superseded 128,559 B / `1e3b5781…` / md5 `5c0db7c9…` as history.

## Not changed
No measurement, count, percentage, table, figure or byline. Byline before == after (asserted).
`\bibitem` 13 / distinct 13 / `\cite` occurrences 14 / distinct keys 13 / uncited 0 / unresolved 0 —
identical before and after. Recompute on a clean extraction: 49/49, `VERDICT PASS`, exit 0.

## Rebuild chain
1. deposit archive rebuilt twice from a **copy** of the build script (`scratch/ugateddoi/build_archive_doi.sh`,
   pins recomputed for the two edited metadata files) → `cmp` byte-identical, then installed.
2. `md2tex.py --package gated-read-batching` — guard did not fire (13 bibitems / 14 cites / 0 uncited /
   0 unresolved, balanced 19/19, no residual non-ASCII; the only sanitiser hit is the pre-existing
   internal id `UFIXGR7` removal, unchanged in strength).
3. payload tarball built twice from `submission/` → `cmp` byte-identical (15,251 B).
4. PDF: tectonic exit **0**, `Undefined control sequence` 0, `!` 0, no `-Z continue-on-errors`; old render
   moved to `rendered/_superseded/` with a dated README.
5. preprint zip: one member, extracted `cmp` clean against `submission/main.tex`.
6. TMLR: rebuilt from the new `main.tex` with a **new** count-asserted rule that redacts the DOI paragraph
   (`scratch/ugateddoi/tmlr_build.py`); compiled; anonymity proved on the PDF's own `pdftotext` output —
   name 0, `Independent researcher` 0, email 0, ORCID 0, github 0, zenodo 0, `10.5281` 0, both DOIs 0.

## Observation, not a fix
`papers/gated-read-batching/released/gated-read-batching-released (2)/CITATION.cff` — a stale duplicate
tree with a space in its name — still carries the old "no DOI" comment. It is outside the rebuilt payload
(`released/gated-read-batching-released/`) and was left untouched; flagging it, not silently editing it.
