# PDF route for paper #3 (encoder-crossover-190)

**Unit:** UPDF1. **Verdict: a usable PDF exists on this host, produced without any TeX toolchain.**
Two independent routes work and are byte-stable in their visible content.

Artifacts in `papers/encoder-crossover-190/rendered/`:

| file | bytes | route | pages |
|---|---|---|---|
| `encoder-crossover-190.pdf` | 728,748 | Chrome headless print-to-PDF (the deliverable) | 20, A4 |
| `encoder-crossover-190-libreoffice.pdf` | 495,677 | LibreOffice HTML import -> PDF (fallback / comparison) | 24, A4 |
| `encoder-crossover-190.docx` | 42,326 | LibreOffice HTML -> ODT -> DOCX (Preprints.org fallback) | n/a |
| `encoder-crossover-190.html` | 85,658 | generated intermediate | n/a |
| `convert.py` | 5,568 | the converter (reproducible, no network, no installs) | n/a |

## 1. The working route (Chrome headless print-to-PDF)

```
cd "papers/encoder-crossover-190/rendered"
python3 convert.py        # MANUSCRIPT.md -> encoder-crossover-190.html (markdown 3.10.2, +tables)

google-chrome --headless=new --disable-gpu --no-sandbox --no-pdf-header-footer \
  --run-all-compositor-stages-before-draw --virtual-time-budget=15000 \
  --user-data-dir="/abs/path/scratch/updf1/chrome" \
  --print-to-pdf="/abs/path/papers/encoder-crossover-190/rendered/encoder-crossover-190.pdf" \
  "file:///abs/path/papers/encoder-crossover-190/rendered/encoder-crossover-190.html"
```

Observed: exit 0, `728748 bytes written to file ...`, 0.8 s wall clock, `Pages: 20`,
`Page size: 594.96 x 841.92 pts (A4)`, `Tagged: yes`, `PDF version: 1.4`, Producer `Skia/PDF m150`.

**The workspace path contains a space, and that is the only trap.** Unquoted, the same command dies
immediately with `ERROR:chrome/app/chrome_main.cc:201] Multiple targets are not supported in headless mode.`
(exit 13) — the path was split into extra targets, not a render failure. Quote every path.

`/snap/bin/chromium` is **not** usable on this host:
`internal error, please report: running "chromium" failed: cannot create transient scope: DBus error
"org.freedesktop.DBus.Error.InvalidArgs": [Process 27 is a kernel thread, refusing.]`
Use `/usr/bin/google-chrome` (150.0.7871.128). Harmless noise on stderr either way:
`dconf-CRITICAL ... /run/user/1000/dconf/user: Read-only file system`, `NSS error code: -8126`,
`radv is not a conformant Vulkan implementation`. None of it affects the output.

## 2. The LibreOffice routes

**2a. HTML -> PDF: works.**
```
export HOME="$PWD/scratch/updf1/lohome" XDG_CONFIG_HOME=... XDG_CACHE_HOME=... XDG_RUNTIME_DIR=... SAL_USE_VCLPLUGIN=svp
soffice -env:UserInstallation="file://<URL-PERCENT-ENCODED profile dir>" --headless --norestore \
  --convert-to pdf --outdir <out> <in>.html
```
`using filter : writer_web_pdf_Export`, exit 0, 495,677 bytes, 24 pages A4, `Tagged: yes`, PDF 1.7,
Producer `LibreOffice 26.2.6.3`.

Two traps, both hit and fixed:
- A `-env:UserInstallation` URL containing **literal spaces** kills the process with
  `terminate called after throwing an instance of 'com::sun::star::uno::RuntimeException'` (no output
  file, no useful message). Percent-encode the path (`%20`) — then it works.
- LibreOffice needs writable `HOME`/`XDG_*`; `/run/user/1000` is read-only here and produces the
  `dconf-CRITICAL` lines unless you redirect those variables.

**2b. ODT -> PDF: works** (superfluous for the deliverable, but it is the bridge that makes the DOCX
work). `--convert-to odt` on the HTML yields a **Writer/Web** document (`using filter : writerweb8_writer`,
40,954 bytes); `--convert-to pdf` on that ODT uses `writer_pdf_Export`, exit 0, 495,449 bytes, 24 pages.

**2c. HTML -> DOCX: works only via ODT.**
- Direct: `--convert-to docx` on the HTML **fails** — `Error: no export filter for .../encoder-crossover-190.docx
  found, aborting.` / `Error: no export filter`, exit 1. Cause: the HTML-imported document is a Writer/**Web**
  document and there is no `writerweb8` DOCX filter.
- Via ODT: `--convert-to docx` on the `.odt` uses `filter : Office Open XML Text`, exit 0, 42,326 bytes.
  Verified as a real DOCX: 12 zip entries, `word/document.xml` 243,427 chars, **5 `<w:tbl>` blocks**, byline present.

## 3. Reproducibility

Run twice, same inputs:

```
99b011d019ccbb2d9680d010fa8d6c541cc369129fe35ab33921b149aa102eaa  run1.pdf
df4b8801695f4098db99e479d91be86affb7abf6c043e5cfd54b543670fbc476  run2.pdf
cmp: differ, byte 381, line 7
```

**Not byte-identical, and here is exactly where the 171 differing bytes live** (out of 728,748, i.e. 0.023 %):

1. Offsets 380-382 and 415-417 — the two timestamp fields
   `/CreationDate (D:20261017032557+00'00')` and `/ModDate (...)`. Same second in this pair only because
   the two runs were 0.3 s apart; they are set from the wall clock.
2. ~167 single/double-byte differences at offsets ~338 k-549 k, all inside the tagged-PDF structure tree:
   `/ID (node00000NNN)` entries and the `/Names [(node...) NNN 0 R ...]` array. Skia assigns struct-tree
   object numbers in a non-deterministic order between runs; the node set and count are identical.

**The visible document is identical.** `pdftotext -layout` of the two runs is byte-for-byte equal
(70,727 chars each). So: reproducible in content, not bit-reproducible in container — expected for
any printer that stamps `/CreationDate`. No other divergence exists.

## 4. Honest quality assessment of `encoder-crossover-190.pdf`

**Mechanical:** 20 pages, A4 (594.96 x 841.92 pt), 728,748 bytes, Tagged PDF 1.4.
Text is fully machine-readable: `pdftotext` extracts 70,727 chars with no mojibake
(`Î`, `Â`, `â€`, `Ã`, U+FFFD all absent). All fonts embedded **and** subset with a Unicode map
(`pdffonts`: `yes yes yes` for every row) — DejaVu Serif / Sans / Mono as CID TrueType, Identity-H.

**Completeness:** all 7 numbered sections plus Abstract, Data and code availability, Persistent
identifier, Compute and resources, Author contributions, Funding, Competing interests, Use of AI tools,
and References are present in the extracted text. All 5 tables are present and **none overflowed**:
10,542 word boxes, max `xMax` 547.50 pt against a 594.96 pt page and a 546.77 pt right content edge —
0 words past the margin, 0 clipped. Left edge 48.0 pt, matching the 17 mm CSS margin.

**Unicode is intact, not mangled** — the counts in the PDF equal the counts in the source:
κ 31, ≈ 3, ≥ 10, × 13, ± 4, → 23, Δ 8, ψ 7, § 63, plus ↔ 3 and − 32. `ψ = 0.616`, `Δ = −0.3316`,
`p = 4.167e−09`, `(≥ 2 ... training ↔ fixture pairs)` all extract as the right glyphs.

**Abstract and byline:** yes to both. Page 1 extracts
`AUTHOR SLOT: REAL NAME — TO BE SUPPLIED` immediately under the title, and the abstract's first
sentence and headline sentence both verify under whitespace normalisation. `convert.py` lifts the slot
from `submission/main.tex:10` (`\author{AUTHOR SLOT: REAL NAME --- TO BE SUPPLIED}`) and renders `---`
as an em dash, hence `—` rather than `---`.

**What is worse than a LaTeX build, plainly:**
- **No page numbers and no running heads.** `--no-pdf-header-footer` is required to suppress Chrome's
  ugly URL/date header, which also removes the page number — bad for a 20-page reviewing copy.
- **Maths is Unicode, not typeset.** `Δ`, `ψ`, `≥` are upright text glyphs, not math italic; `e−09` is a
  Unicode minus, not a superscript; there is no display math, no equation numbering, no `\label`/`\ref`
  machinery (the manuscript writes `§2` cross-references by hand, so nothing is lost there, but nothing
  is gained either).
- **Tables are boxed grids**, not booktabs: full 0.6 pt rules on every cell, grey header fill, 7.9 pt sans.
  Legible and complete, but visibly not a LaTeX table. The long "baseline / source / re-scorable?" table
  is dense at 8 pt and carries inline monospace paths.
- **`✅` (U+2705) survives as a colour-emoji glyph** in the Results table — `pdffonts` shows
  `NotoColorEmoji` embedded as **Type 3** (a bitmap) purely for those two characters. Readable, extracts
  correctly, and wrong for a preprint. Replace with plain text before submission.
- **Hyphenation is Chrome's automatic one** (`hyphens: auto`): it splits compounds like `fine-/tuned` and
  `typed-/single-label` at line ends. Cosmetically below LaTeX quality.
- **No journal/site style** — no `tmlr.sty`, no arXiv class, no DOI/line numbering; Title/Author metadata
  is the placeholder slot.

**The LibreOffice PDF is the weaker fallback:** 24 pages for the same text (its HTML importer approximates
the CSS rather than applying it with Chrome's engine — the byline and affiliation run together on page 1:
`AUTHOR SLOT: REAL NAME — TO BE SUPPLIEDAffiliation not supplied ...`), same 5 tables, fonts embedded,
`Tagged: yes`. Use it only if Chrome is unavailable.

## 5. Recommendation

**Preprints.org: yes, submit this.** The gate is `.doc`/`.docx`/`.pdf`, and both a 20-page A4 PDF and a
valid 5-table DOCX now exist. The PDF is complete, selectable, font-embedded, tagged, A4, and free of
Unicode damage — materially better than "no PDF at all", and adequate for a non-typeset preprint server.
Submit the Chrome PDF as primary; keep the DOCX as the fallback the server can re-flow.

**TMLR (and arXiv house style): no — compile the LaTeX elsewhere.** TMLR expects its own style file and
a properly typeset PDF; this render has no page numbers, no TMLR styling, upright-Unicode maths and a
colour-emoji glyph in a results table. The LaTeX in `submission/main.tex` (84,358 bytes) is the source of
record and would compile on any host with TeX Live, or in Overleaf, in minutes. Spend that, not this.

**Before submitting anywhere, three fixes:** fill `AUTHOR SLOT: REAL NAME`; get page numbers back
(CSS `@page` margin-box counters — untested here); replace `✅` with plain text (and optionally kill
`hyphens: auto` to stop `fine-/tuned` splits).

## 6. What I did not test

- **The absence of a TeX toolchain.** I took the card's list as given and never ran `which pdflatex` /
  `tectonic`. If a TeX binary is in fact reachable, this whole route is unnecessary.
- `pandoc`, `wkhtmltopdf`, `weasyprint`, LaTeX-in-container — not probed.
- **No visual inspection of rendered page images.** The overflow claim rests on `pdftotext -bbox`
  geometry plus text extraction, not on looking at pixels; no one has eyeballed the pages.
- Chrome header/footer variants, `@page` margin boxes, a page-numbered build.
- The DOCX **opened in Word/LibreOffice**, or its tables' column widths; only the zip structure,
  `<w:tbl>` count (5) and byline text were checked.
- The PDF in a browser reader, an upload form, or any PDF/A / PDF-UA validator (only `Tagged: yes`).
- Reproducibility on another host, or with fonts other than DejaVu (the CSS names DejaVu first, so a host
  without it silently falls back).
- Whether Preprints.org's `.docx` path preserves the tables.

---

## 2026-10-16 - BYLINE RE-RENDER, unit URENDER2 (papers #3 and #7)

**Trigger.** Both PDFs were rendered before the author's real name replaced the drafting
placeholder, so they still printed `AUTHOR SLOT: REAL NAME --- TO BE SUPPLIED`.
Root cause on #3 is a timestamp ordering: the Chrome PDF was written 22:25:57 while
`papers/encoder-crossover-190/submission/main.tex` (the byline source) was written 22:28:15 -
the fix landed after the render. The stale PDF extracted `AUTHOR SLOT` once (page 1, line 5)
and `Aswin Ram Kalugasala Moorthy` zero times.

**Sources actually read.** The authored markdown `MANUSCRIPT.md` is converted to HTML by the
paper's `rendered/convert.py`, which lifts `\author{...}` out of `submission/main.tex:10`.
So the render derives from BOTH; neither was edited. `tools/package/md2tex.py` (the md->tex
converter) was not touched. `papers/gated-read-batching/rendered/` did not exist and was created.

**Recipe change.** The #3 converter was generalized to auto-detect its paper directory, so one
script serves both papers. It also drops the old hardcoded
`<meta name="author" content="AUTHOR SLOT: REAL NAME --- TO BE SUPPLIED">`
(old `convert.py:114`) - a second, invisible placeholder source that survived in the HTML head
and would have carried into the DOCX doc properties. The converter now REFUSES to write if the
lifted byline contains `AUTHOR SLOT` (exit 2) or if the slot survives into the HTML (exit 3).

**Routes.** Unchanged from section 1 above: `/usr/bin/google-chrome --headless=new --print-to-pdf`
is the deliverable route; DOCX is LibreOffice HTML -> ODT -> DOCX. Every path is quoted - the
workspace path contains a space.

**NEW TRAP (hit here, cost one render).** LibreOffice `--convert-to pdf` writes to the SAME
basename as the input, so running it on `<paper>.html` silently OVERWROTE the Chrome
`<paper>.pdf` deliverable with the weaker 24-page LO output. Render the LO PDF to a scratch
outdir and rename it `<paper>-libreoffice.pdf`, never `--outdir` the paper's own `rendered/`.

### Artifacts re-rendered (Chrome primary; LO comparison; both A4)

| paper | artifact | bytes | sha256 |
|---|---|---|---|
| encoder-crossover-190 | `encoder-crossover-190.html` | 85507 | `a1cfad186219cd1cf19d06cca5827c0189f2621b3df3f8392ded92e853fa2e95` |
| encoder-crossover-190 | `encoder-crossover-190.pdf` | 727811 | `5c7f82a76a0ca5e9dafd8b73d0cbd0d5dd42fde7b760298959410a371895e1e0` |
| encoder-crossover-190 | `encoder-crossover-190.docx` | 42290 | `1fefced69b37fac1fe47857f41b4b82df6a01c127826eac10a4b4418587e2ee5` |
| encoder-crossover-190 | `encoder-crossover-190-libreoffice.pdf` | 503769 | `95d5e0224fc68512e6b1f2b7000a5b86b46a444e2e09a8bfd44725c46e634146` |
| gated-read-batching | `gated-read-batching.html` | 39761 | `d4be5707a96dcf52c56465fc7272047aea024d8d6f60ab8dfa0c398e3643cb3e` |
| gated-read-batching | `gated-read-batching.pdf` | 315333 | `4f3e7aff416e60c8e85be24249d756ab7836340b12b6ed7449e6e6764902852f` |
| gated-read-batching | `gated-read-batching.docx` | 24344 | `a154b52f005ac351188339227c47b39d69277162d978e79ed61370c86d2d24f4` |
| gated-read-batching | `gated-read-batching-libreoffice.pdf` | 280188 | `34c4555ade2375f827f8d6194f9edcfab6f77ed3b3802daec20b8a7fc5deaf55` |

**encoder-crossover-190 - byline proof.** `pdftotext -layout` on the PDF (real text extraction,
not inference from the HTML twin) contains `Aswin Ram Kalugasala Moorthy` exactly once,
on page 1 immediately under the title, and `AUTHOR SLOT` zero times:

```
Aswin Ram Kalugasala Moorthy
Byline carried into this render from submission/main.tex.
```

- page count: 20
- Unicode intact: U+FFFD 0, I-hat 0, A-hat 0, a-euro 0, A-tilde 0 (all zero).

**gated-read-batching - byline proof.** `pdftotext -layout` on the PDF (real text extraction,
not inference from the HTML twin) contains `Aswin Ram Kalugasala Moorthy` exactly once,
on page 1 immediately under the title, and `AUTHOR SLOT` zero times:

```
Aswin Ram Kalugasala Moorthy
Byline carried into this render from submission/main.tex.
```

- page count: 10
- Unicode intact: U+FFFD 0, I-hat 0, A-hat 0, a-euro 0, A-tilde 0 (all zero).

### Quality re-check vs the pre-byline render (regression test)

- **Page count: no regression.** #3 stays at 20 A4 pages (594.96 x 841.92 pt); #7 is a new
  render at 10 A4 pages (it had no PDF before).
- **Fonts: no regression.** All fonts embedded AND subset with a Unicode map (`pdffonts`
  `yes yes yes` on every row; DejaVu Serif/Sans/Mono as CID TrueType, Identity-H). #3 lists 11
  font rows (including NotoColorEmoji Type 3 for the emoji in the source), #7 lists 7.
- **Tables present: no regression.** 5 tables in #3 (as before), 4 in #7; DOCX `word/document.xml`
  carries 5 and 4 `<w:tbl>` blocks respectively, so the tables survived the ODT/DOCX bridge too.
- **Unicode: no regression.** All anti-mojibake markers zero in both extracted texts; #3 keeps
  kappa 31, approx 3, >= 10, times 13, +- 4, arrow 23, Delta 8, psi 7, section 63, - 32 -
  identical to the pre-byline counts recorded in section 4 above.
- **Overflow: unchanged, and here is the honest number.** `pdftotext -bbox` max `xMax` is
  547.50 pt in BOTH papers, and 547.50 pt was also the pre-byline max - identical, so nothing
  regressed. Against the strict 546.77 pt right content edge (A4 594.96 pt minus the 17 mm
  margin), 600 word boxes in #3 and 276 in #7 land in the 546.77-547.50 pt band, i.e. a
  0.73 pt (0.26 mm) sub-millimeter overshoot. The earlier note's '0 words past the margin' used
  the page-width criterion; under this stricter margin criterion the count is 600, not 0.
  Nothing is clipped and nothing crosses the 594.96 pt page edge.
- **Only intended content diff.** The byline block and the stale affiliation sentence changed;
  #3's extracted text is 70,688 chars vs 70,727 pre-byline, 16 h2 / 22 h3 / 5 tables unchanged.

### Font detail (measured after the re-render)

- `encoder-crossover-190`: 11 font rows, 0 with any of emb/sub/uni = no.
- `gated-read-batching`: 7 font rows, 0 with any of emb/sub/uni = no.

**Byline verification summary: PASS.** `Aswin Ram Kalugasala Moorthy` present in all
three artifact kinds per paper (HTML, PDF text, DOCX `word/document.xml`); `AUTHOR SLOT`
count is 0 in every one of them, including the DOCX doc properties.

