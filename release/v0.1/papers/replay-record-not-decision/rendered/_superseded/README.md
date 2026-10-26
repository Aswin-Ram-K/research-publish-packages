# Superseded builds — `replay-record-not-decision`

These files are **not** deliverables; they are kept so the
history of this paper's rendering stays auditable. The current authoritative PDF is one directory up:
[`../replay-record-not-decision.pdf`](../replay-record-not-decision.pdf).

---

## URENDER4 update 2026-10-18 — prior canonical PDF superseded

`replay-record-not-decision-tectonic-prior-main-85f13e8c.pdf` — **91,552 B**, 10 pp, A4 (595.28 x 841.89 pt), sha256
`85f13e8c450579a73a852194dfdc151d104db3afa9459495ae994b59697fc17a`.

It was the authoritative `../replay-record-not-decision.pdf` installed by UINSTALL3 on 2026-10-16 ~22:45 and rebuilt
2026-10-17 16:28, compiled by `tectonic -r 1 --keep-logs` from the **same** `submission/main.tex`
as its replacement.

**Not stale in content.** `pdftotext` of this file and of its replacement differ in **0** lines; the
two builds differ only in the embedded PDF creation date/ID (`pdftotext` normalises neither). It is
quarantined because URENDER4 recompiled every paper and installed the fresh build at the canonical
name (91,551 B, sha256 `4c5acbec547c04797026ae997fa68569966c05fb1070b0fa33ab7f174ea5e345`; exit 0, 0 `Undefined control sequence`, 0 LaTeX `!`). The
mtime ordering agrees: current `submission/main.tex` is 2026-10-17 16:27:59, this PDF 2026-10-17
16:28:03. Prior bytes preserved — not deleted.


---

## UFIXNOTE5 note 2026-10-18 — nothing to quarantine

This paper's `rendered/` contains only the LaTeX-built `replay-record-not-decision.pdf` (the shipping
artifact) and this `_superseded/` directory. On 2026-10-18 (UFIXNOTE5) **no** HTML, DOCX or
LibreOffice-PDF derivative was present on disk for this paper, so none was moved. The unit card's
premise that such derivatives existed here is contradicted by disk.
## Superseded 2026-10-19 (unit UDOITIDY2) — PDF that predates the DOI back-fill

- `replay-record-not-decision-prior-doi-backfill-4ac73a51.pdf` — 94,683 bytes, sha256
  `4ac73a5177f2c60409d375fc3c832d06c859eac647f1bd59b15527db8f4f3537`, 10 pages. **Replaced because its extracted text contains neither DOI**: the paper's
  own concept DOI `10.5281/zenodo.23482511` (added to §7 by UDOIBACK2) is absent, so the rendered PDF
  was stale with respect to `submission/main.tex`.
- Replacement: `rendered/replay-record-not-decision.pdf`, 101,593 bytes, 10 pages, recompiled from
  `submission/main.tex` on 2026-10-19 with Tectonic (exit 0, 0 `Undefined control sequence`,
  0 `!`). Its extracted text contains `10.5281/zenodo.23482511` once and `10.5281/zenodo.23482512`
  zero times. The size difference from earlier compiles is the font bundle fetched into an empty
  Tectonic cache, not a content change — page count is identical (10).
