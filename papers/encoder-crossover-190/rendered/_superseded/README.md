# Superseded builds — `encoder-crossover-190`

These files are **not** deliverables. They are kept so the history of this paper's rendering is
auditable. The current, authoritative PDF is one directory up:
[`../encoder-crossover-190.pdf`](../encoder-crossover-190.pdf) — installed by unit **UINSTALL3** on
**2026-10-16 ~22:45**, compiled by `tectonic` 0.15.0 from
`papers/encoder-crossover-190/submission/main.tex` (sha256
`742dabbcd64cc5de5ab21e771529be090e97fc1597df36b3b28c8ca5fa453404`).

## `encoder-crossover-190-latex.pdf` — 185,377 B, 27 pp, US letter (612 × 792 pt)

A superseded LaTeX build (Producer `xdvipdfmx`, Creator `tectonic`). Wrong in two ways:

1. **Wrong page size** — US letter, while the paper's build is A4 (595.28 × 841.89 pt).
2. **Broken cross-references** — it carried four damaged `§B3` / `§F.3` sites that rendered as the
   corrupted text `internal reference notes 3;`. Measured on its extracted text: `notes 3;` appears
   **1** time, and the intended forms `B3` and `F.3` appear **0** times each.

Replaced **2026-10-16 ~22:45** by UINSTALL3 with the fresh A4 build. Original mtime 2026-10-16 22:33.

## `encoder-crossover-190-CHROME-headless-a4.pdf` — 727,811 B, 20 pp, A4 (594.96 × 841.92 pt)

A superseded headless-Chrome print (Creator `HeadlessChrome/150.0.0.0`, Producer `Skia/PDF m150`),
produced by the workspace's HTML→PDF pipeline. It is a print of the HTML rendering, not of
`submission/main.tex`; LaTeX-generated page numbers and the numbered bibliography are absent
(`[1]` matches: **0**).

**Note on the previously-reported "stale byline":** that characterization was *not* reproduced in
this file. Extracted text contains the correct name `Aswin Ram Kalugasala Moorthy` exactly **1**
time and `AUTHOR SLOT` **0** times. The file is nevertheless superseded, because it is not built from
the shipped LaTeX source.

Replaced **2026-10-16 ~22:45** by UINSTALL3. Original mtime 2026-10-16 22:31.

## Not moved (not named as superseded, left in place)

`encoder-crossover-190-libreoffice.pdf`, `encoder-crossover-190.docx`, `encoder-crossover-190.html`
and `convert.py` remain in `rendered/` unchanged. They are derivative convenience artifacts, not
authoritative PDFs; the authoritative PDF is `../encoder-crossover-190.pdf`.

---

## URENDER4 update 2026-10-18 — prior canonical PDF superseded

`encoder-crossover-190-tectonic-prior-main-58c22c90.pdf` — **184,933 B**, 25 pp, A4
(595.28 x 841.89 pt), sha256 `58c22c906d0220fb707eed538bf13bf33304a4b2751b033e0d4a0c71bce7fd44`.

It was the authoritative `../encoder-crossover-190.pdf` installed by UINSTALL3 on 2026-10-16 ~22:45
(that file's mtime 2026-10-17 15:36), compiled by `tectonic -r 1 --keep-logs` from an **older**
`submission/main.tex`. It is superseded because the source changed after it was built: current
`submission/main.tex` is 84,695 B / sha256
`397713d74920e9e1bc5f5fb8dc6ef09fb5fa9e641583f0ecd16b718d5f9d09ca` (mtime 2026-10-18 02:54), newer
than this PDF. `pdftotext` differs in **764** lines (GNU `diff`; 750 by Python `difflib`, which also splits on form feeds) between this file and its replacement: the
replacement carries the installed affiliation block (`Independent researcher` /
`aswinram.k.1603@gmail.com`) and the cleaned abstract.

Replaced **2026-10-18 (URENDER4)** by a fresh A4 tectonic build of the current source: 188,364 B,
sha256 `752747f87423f1fa87cf365179ed1c93915ad65a1aed00e8d8929979964699a1`, exit 0, 0 `Undefined control sequence`, 0 LaTeX `!`. Prior bytes preserved — not deleted.

- `encoder-crossover-190-html-pre-DOI-refresh-2026-10-16.html` (85,507 B) — the stale HTML retained by UARTIFACT2 before `convert.py` was re-run on 2026-10-18; it still said `DOI: AUTHOR TO CONFIRM`. Superseded by the regenerated `encoder-crossover-190.html` (86,041 B).
