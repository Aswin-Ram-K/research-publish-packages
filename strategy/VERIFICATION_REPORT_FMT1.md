# VERIFICATION_REPORT_FMT1 — independent verification of `strategy/FORMATTING_REQUIREMENTS.md`

**Verifier unit:** VUFMT1 (did not author the document under test)
**Author unit:** UFMT1 · **Document date:** 2026-10-16 · **Verified:** re-run against live pages and current disk state
**Bound:** 25 tool calls; used 13. No writes to the author's document.

## Overall verdict: `partial` — core findings reproduce, §6 arithmetic and one unit label do not.

Re-fetched 15 of the 33 cited URLs (11 in one pass + 4 extra) on the verification date; every
quoted requirement tested **HIT** on the live page except one control that belongs on a different
page. Two defects stand: the §6 header arithmetic (40/34/6) is not reproducible from the §6 table
(44/21/2), and `ABSTRACT.txt`'s character count is mislabelled as a byte count. One cross-cutting
staleness the audit never flags: the shipped tarball's `main.tex` is not the `main.tex` the audit
measured.

## Method (not vacuous — red→green)

Quotes were checked through `scratch/vufmt1/match.py` / `match2.py`: HTML stripped, entities
unescaped, whitespace collapsed, then substring test. Literal outputs:

```
GREEN HIT  @12302 prep.html :: abstracts longer than 1920 characters will not be accepted
RED   MISS        prep.html :: abstracts longer than 1921 characters will not be accepted
RED   MISS        prep.html :: The quick brown fox jumped over the lazy dog
RED   MISS        rs_pp.html :: We accept the following file formats: .doc, .docx, .pdf
```

The matcher fails on a knowledge-known-absent variant and on a known-present quote placed on the
wrong page, and passes on the real quote — so a `MISS` is informative rather than vacuous.
Normalisation is **required**: a raw `grep -cF 'abstracts longer than 1920 characters…'` on the
saved HTML returned `0`, exit 1 (markup splits the string); the same test on the normalized text
hits at offset 12302. Saved pages live in `scratch/vufmt1/fetched/` with sha256 printed during
fetch.

## Check 1 — re-fetched URLs and quoted requirements (all HTTP 200)

| Requirement | Live-page result | Literal evidence |
|---|---|---|
| arXiv abstract cap 1920 | **HIT** `prep.html` @12302 | `Keep it short - abstracts longer than 1920 characters will not be accepted; abridge your abstract if necessary.` `"1920"`×1, `"1,920"`×0 — the no-comma claim is true |
| arXiv licence: menu of six | **HIT** `license_index.html` | each token present ×1: `CC BY 4.0`, `CC BY-SA 4.0`, `CC BY-NC-SA 4.0`, `CC BY-NC-ND 4.0`, `perpetual, non-exclusive license 1.0`; `CC Zero`×3 |
| arXiv licence: no default | **HIT (negative)** | word `default` occurs **0** times on `license_index.html` |
| arXiv licence: irrevocable | **HIT** | `The license chosen is irrevocable and cannot be changed`; `the license chosen for each version is irrevocable` |
| perpetual non-exclusive text | **HIT** `arxiv_nonex.html` | `perpetual, non-exclusive license to distribute this article` |
| "limited rights … limits re-use of any type" | **HIT** | `This license gives limited rights to arXiv to distribute the article, and also limits re-use of any type from other entities or individuals` |
| `license/options.html` → 404 | **HIT** | `http=404` |
| **Negative: arXiv states no size quota** | **HIT (negative)** | On `sizes.html`, `tar.html` and three extra reached pages (`submit_tex.html`, `submit/index.html`, `faq/mistakes.html`): `numeric_size_tokens=[]`, `"quota"=False`, `"size limit"=False`. `sizes.html` carries the `34 Megapixel` / `600dpi` sentence the doc quotes. The 10 MB / 5 MB / 50 MB figures appear nowhere I could reach |
| TMLR stylefile | **HIT** `tmlr_ag.html` | `Submissions must be PDF files generated using the TMLR LaTeX stylefile and template` |
| TMLR anonymised | **HIT** `tmlr_ag.html`, `tmlr_ep.html` | `TMLR uses a double blind review process and submissions must be anonymized`; `open-reviewing, double-blind process`; `anonymized form` |
| TMLR CC BY 4.0 from submission | **HIT** | `from the time of submission to final publication` |
| TMLR "no link to an arXiv version" | **HIT** | `not linking to another version that includes the authors' names` |
| TMLR DOI not stated | **HIT (negative)** | `tmlr_faq.html`: `ISSN`×1 (`2835-8856`), `DOI`×0 |
| Research Square `.doc/.docx/.pdf` only | **HIT** `legal/editorial` only | `We accept the following file formats: .doc, .docx, .pdf` — present on `rs_ed.html`, **MISS on `rs_pp.html`** |

Saved-page digests (first 12 hex, sha256 of the fetched artifact) recorded in
`scratch/vufmt1/fetched/`: `prep.html 3734c272d6ec`, `license_index.html 75ef3cef1c13`,
`sizes.html f04eeac6fdde`, `tar.html 385ed783cd1a`, `tmlr_ag.html 117ed02f6791`,
`tmlr_ep.html 4b00d2432e0c`, `tmlr_sub.html 6dbc3f785bbc`, `rs_ed.html fec4f00fc606`.

## Check 2 — the 13/0 measurement (re-measured, not re-read)

`papers/encoder-crossover-190/submission/main.tex`, sha256
`0ee1b11f0692474c174e920b0e534d044937da076fecff41a85796ba14d6f160`, 80,780 bytes, pure ASCII:

```
bibitem_count= 13
cite_word_count= 0      (\cite\b)
cite_prefix_any= 0      (no \cite, \citep, \citet, …)
```

**13/0 reproduces exactly.** The doc's `main.tex` size (80,780 B) and sha256 prefix
(`0ee1b11f0692474c174e920b`) also reproduce.

## Check 3 — the "not stated" items

Direct §6 status column: exactly **two** rows are marked `NOT STATED` — **R12** (size limits) and
**R15** (`\date{}`). Across the prose the phrase "not stated on the fetch(ed) page(s)" appears 14
times and covers at least nine distinct items: (1) size quotas, (2) PS prohibition in `anc/`,
(3) compile/processing time limit, (4) TMLR DOI, (5) Research Square licence, (6) whether Research
Square builds the PDF, (7) Zenodo "concept DOI" wording/prefix, (8) OSF PDF-build statement /
screening duration / size cap, (9) BibTeX-vs-`thebibliography` for TMLR/ICML/NeurIPS/ICLR. A
separate item (arXiv-generated author list source) is recorded `NOT VERIFIED`.

Adversarial test of the load-bearing negatives: no size quota anywhere I could reach (5 arXiv
pages); no TMLR DOI on the FAQ. Both recorded honestly, appropriately scoped to "the fetched
page(s)". I found **no case where a "not stated" item was actually stated** on a page the audit
names.

## Check 4 — abstract-character arithmetic

Convention: `len()` over the UTF-8-decoded text counts **Unicode code points** (`chars`); `bytes`
is the raw file length; the trailing newline is **included** in the first figure and **excluded**
in the "text characters" figure.

| File | bytes | chars (incl. NL) | chars (no NL) | words | non-ASCII |
|---|---|---|---|---|---|
| `ABSTRACT_METADATA.txt` | 1,195 | 1,195 | 1,194 | 186 | 0 |
| `ABSTRACT.txt` | **3,462** | **3,416** | 3,415 | 524 | 28 |

- `ABSTRACT_METADATA.txt` = **1,195 chars / 186 words, ASCII-only, contains no "Abstract"** — every
  claim in §0.2 ¶11 reproduces. (The 1,195 B value in §6 is also right, since it is pure ASCII.)
- `ABSTRACT.txt` = **3,416 characters**, not bytes. The doc says "3,416 **bytes** including the
  trailing newline" (line 124) and "`ABSTRACT.txt` (3,416 **B**)" (§6, line 547). Real byte count is
  **3,462** (28 non-ASCII characters add 46 bytes). The derived "3,415 text characters / 524 words"
  is correct, because those are character counts.

## Check 5/6 — adversarial pass

**Not reproduced:**
1. **"§6 holds 40 audited requirement rows."** Measured: **44** rows, R1–R44.
2. **"34 of them carry a verbatim quote from a fetched primary source."** Measured inside §6:
   **21** rows carry the `*"…"*` verbatim marker in their cells.
3. **"6 are recorded as not stated on the fetched page."** Measured in §6: **2** (`R12`, `R15`);
   ≥9 by any prose reading. None of the three readings yields 6.
4. **"Distinct primary URLs used: 33."** 52 distinct `http(s)` URLs appear in the file and no
   inclusion rule is stated, so the count is not independently reproducible as written.
5. **Implicit: the tarball's `main.tex` is the measured `main.tex`.** `tar -tzvf` shows one member,
   `main.tex`, **78,405 bytes, mtime 2026-10-16 13:52**; on-disk `main.tex` is **80,780 bytes, mtime
   14:18**. The audit prints both numbers (§0.1 ¶10 and §6) but never notices they disagree, and §7
   recommends submitting the tarball whose member predates the audited file by 2,375 bytes. So the
   PASS verdicts for R1/R2/R14 and the §7 payload line describe a *different* revision than
   R4–R43's audit. Tarball sha256 `0b745948ad00a62ec06818692173ffa7fa1d71a9a6ced17bca28b723169f4901`
   does match the stated prefix `0b745948ad00a62ec0681869`.

**Overstated / narrower than implied:**
- §3.2 presents `We accept the following file formats: .doc, .docx, .pdf` under both Research Square
  sources; it verifies only on `researchsquare.com/legal/editorial`. R32's source cell correctly
  cites "Research Square editorial", so the attribution is imprecise rather than false.
- The abstract-cap quote is rendered with an em dash in the doc (`—`); the page uses a plain hyphen
  (`Keep it short - abstracts…`). Cosmetic; Wording of the quoted sentence otherwise exact.

**Unverified (named, not softened):** I did not re-fetch/verify the remaining 18 URLs of the
inventory (§4 policy pages, Zenodo, OSF, Preprints.org, NeurlPS/Elsevier/Nature/ICLR, `ltbibl.dtx`),
nor the contents of the three delegated note files
(`scratch/ufmt1/arxiv_notes.md` 34,664 B, `preprint_notes.md` 31,249 B, `policy_notes.md` 42,702 B
— all three exist, which corroborates the provenance claim's file backing only).

**Contradictions:** items 1–5 above; the byte-vs-character label in Check 4.

**Blocker:** none. The document's load-bearing external findings (arXiv cap, six-option irrevocable
licence with no default, no size quota, TMLR stylefile/anonymity/CC BY 4.0/no-link, Research Square
format, internal 13/0) all reproduce; the defects are arithmetic/bookkeeping in §6 and one unflagged
stale artifact, not fabricated sources.

**Recommended author follow-up (not performed here — the author's document is not mine to edit):**
fix the 40/34/6 header to match the table (44 rows by direct count), relabel `ABSTRACT.txt`'s 3,416
as characters (bytes 3,462), state the URL-counting rule or drop "33", and either rebuild the
tarball from the 80,780-byte `main.tex` or record the divergence.
