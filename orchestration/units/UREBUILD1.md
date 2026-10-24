# UREBUILD1 — rebuild stale preprint bundles + TMLR variants (DONE)

**Bound:** 35 tool calls (used ≈21). **Write paths:** papers/{encoder-crossover-190,replay-record-not-decision,gated-read-batching}/{preprints,tmlr}/**, scratch/urebuild1/**, orchestration/units/UREBUILD1.md, orchestration/handoffs/UREBUILD1.json.

## Result
- **JOB 1:** encoder bundle was already current (member sha256 `2b5d049e…`, cmp identical) → left alone. Rebuilt `replay-record-not-decision` and `gated-read-batching` with `zip -X -q … main.tex` from a staging dir; each has exactly 1 member, extracted `cmp` clean, member sha256 == live sha256.
- **JOB 2:** rebuilt #3 from the current live source by re-running the UTMLR5 chain rebased into `scratch/urebuild1/u5work` (not into `scratch/utmlr5` — not a declared write path), then applied 3 count-asserted neutral-wording replacements for DOI sentences that today's source introduced. Created #2/#7 variants from scratch with count-asserted rules (preamble → `\usepackage{tmlr}` + `\setcitestyle{numbers}`; anonymous byline; `\blfootnote` LLM-use footnote; author blocks/contributions de-named; DOI/zenodo → neutral).
- All three compile with tectonic: literal exit 0, `Undefined control sequence` 0, `!` 0, no missing files. Anonymity counts from the compiled PDF's own extracted text are all 0.
- **JOB 3:** three separate TMLR-ready PDFs exist (16 / 7 / 10 pages). Supplementary-material bundles referenced by #2/#3 are not packaged in `tmlr/`; that is the remaining piece before an OpenReview submission.

## Evidence (authoritative: scratch/urebuild1/variants_evidence.json)
- Zip rebuilt #2: 11526 B sha256 `1b520f22ad7ec0d83e0c82a734fd5790724a2dfbb175a2600ac323294953537d`, 1 member, cmp clean.
- Zip rebuilt #7: 14950 B sha256 `d89131ea1843be796419f3593c38ee1144c0aba92341f4423509dc86ce4f2129`, 1 member, cmp clean.
- Zip #3 left: 28712 B sha256 `705bc498c7c7eb7cf1e53cae8f49fb8656787694c39dbc7c5f4064f9aa7caf7f`, member `2b5d049e…`.
- PDFs: #3 177298 B 16 pp `fb95f0ac302a07678eaf5f73ef7038a5d46beeb6807830f065a94ffb38cf1109`; #2 93109 B 7 pp `cefd09a7a161d73bf7ae27303ca8cb00dbab2761485beca30bb90856846aee7a`; #7 106151 B 10 pp `89490afebd0d2b8b8b06696d50a778af11a2af431f12dfb5d789ff13b6e105de`.
- Anonymity (pdftotext of own PDF): name / `Independent researcher` / email / ORCID / github / zenodo / `10.5281` / DOI 23482511 / DOI 23463944 = **0 each** for all three.
- Numeric: body-only (post-`\begin{document}`, bibliography stripped) removals are identifier-only for #2 (`10.5281`×3, `23463944`×2, `23482511`×1) and none for #7; #3 body removed only the 3 DOI fragments. Claim decimals unchanged (all changed decimals are `10.5281`; #3 additionally drops `4.1`/`2.6` = model-version strings in the de-named AI-tools paragraph). Added: none (body).
- Structure unchanged per paper: #3 23 cites/13 bibitems/0 uncited/0 unresolved; #2 8/8/0/0; #7 14 calls/15 keys/13 distinct/13 bibitems/0/0.

## Disagreements / notes
- Card table's "preprint zip holds" column is the **member** sha256, not the zip's own sha256; state re-confirmed as carded.
- #3's pre-existing variant did carry neutral DOI wording, but it predated the current source; the rebuilt chain initially emitted today's 3 new DOI sentences — fixed with count-asserted rules.
- Body "Use of AI tools" sections of #2/#7 still name the harness/model (not author-identifying, not in the required zero-list); only the TMLR footnote was required to be generic.
