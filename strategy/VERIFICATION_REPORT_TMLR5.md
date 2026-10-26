# VERIFICATION REPORT — TMLR5 (independent verifier VUTMLR5)

**Verdict: PARTIAL.** The build, the compile facts, the red→green fix and the anonymity proof all
reproduce exactly. The **B2 baseline-equality justification does not reproduce**: the only cited
quantitative baseline (`scratch/utmlr2/evidence.json`) records `private-doc-name` = **0**, not 2.
No artefact was repaired (report-only), and nothing under `scratch/utmlr1|2|4|5/**`, `papers/**`,
`tools/package/**` or the released archive was written.

Method: re-derived the build in my own `scratch/vutmlr5/` by `sed 's#scratch/utmlr5#scratch/vutmlr5#g'`
on `scratch/utmlr5/build.py` (single path-rebase, no rule change), ran it twice, compiled with the
recipe's own Tectonic invocation, and re-measured every claim independently.

## 1. Build re-derivation — REPRODUCED exactly

| claim | UTMLR5 | mine | verdict |
|---|---|---|---|
| `tmlr/main.tex` bytes | 83,785 | **83,785** | match |
| lines | 476 | **476** | match |
| sha256 | `8d6b036c23e4195e9119f67d2a7493831e836bfd68a9a2d73849eecdfbbf0fd0` | **identical** | match |
| two builds byte-identical | yes | **yes** (`cmp` clean) | match |

`scratch/vutmlr5/build.py` copied verbatim from UTMLR5's with the write root rebased; all 7
`SCRUB3` rules matched `found=1`; the chain ran rc=0 at every stage. No hand-edited `.tex`.

## 2. Red→green on `\setcitestyle{numbers}` — REPRODUCED in both directions

| direction | literal exit | error text / result |
|---|---|---|
| **RED** — `\setcitestyle{numbers}` removed (copy at `scratch/vutmlr5/redgreen/main.tex`) | **1** | `error: main.aux:84: Package natbib Error: Bibliography not compatible with author-year citations.` — **NO PDF** |
| **GREEN** — line restored | **0** | `Bibliography not compatible` count **0**; PDF produced |
| **COUNTER-TEST** — `\PassOptionsToPackage{numbers}{natbib}` **before** `\usepackage{tmlr}` (full style tree) | **1** | same natbib author-year error at `main.aux:84`; **NO PDF** |

The red→green is real, not coincidental, and the counter-test corroborates the *reason* UTMLR5 gives:
a load-time option loses to tmlr's own runtime `\setcitestyle`.
**One factual slip:** the style line is **`tmlr.sty:21`**, not `:20` —
`grep -n`: `15:\RequirePackage{natbib}`, `21:\setcitestyle{authoryear,round,citesep={;},aysep={,},yysep={;}}`
(line 20 is the comment `% modification to natbib citations`). Mechanism conclusion unaffected.

## 3. Compile facts — REPRODUCED

Exit **0**; `Undefined control sequence` **0**; lines starting `!` **0**; lines starting `error` **0**;
pages **16** (`pdfinfo`); PDF **176,971 B**. `-Z continue-on-errors` never used.
Pinned `SOURCE_DATE_EPOCH=1700000000`, two consecutive runs: both
`0c35ed5603253ec5e049639f1637014999d620f94c445670ef5b8932593eac06`, `cmp` byte-identical — **claim met**.
The *default-run* digest `971a96ae…` did **not** reproduce (my fresh run:
`5a41f1fe11682294ba95b613681bfde634bf564a035e8cf866e955cac81622da`); this is the documented
embedded-timestamp effect, and UTMLR5 claims only the pinned digest is reproducible — so **not a
contradiction**, but the literal value is unreproducible by construction.

## 4. Anonymity from PDF text — REPRODUCED, independently commanded

Command: `pdftotext scratch/vutmlr5/pdf_pinned_1.pdf - | grep -o -i -F "<needle>" | wc -l` (and
`grep -o -E '[0-9a-fA-F]{40,64}'` for digests). Extracted text 73,178 B. Counts:

`Aswin` 0 · `Kalugasala` 0 · `Moorthy` 0 · `Independent researcher` 0 · `aswinram` 0 · `gmail.com` 0 ·
`ORCID` 0 · `github` 0 · `GitLab` 0 · `Zenodo` 0 · `analysis.json` 0 · `research-publish-packages` 0 ·
`ad301ae` 0 · `907fa39` 0 · `DOI pending` 0 · 40–64 hex 0 · **`Anonymous authors` 1**. All match.
Also checked the PDF metadata dict (`pdfinfo`: no Author/Title/Subject fields; `CreationDate` =
the pinned epoch) and a raw-binary needle grep — clean.

**What this proof cannot establish:** it bounds the *extracted text layer* of *this* PDF only. It cannot
rule out (a) identifying content in images, embedded fonts, annotations, or attachment streams,
(b) identity leakage through strings not on the needle list (rephrased self-citation, an unlisted repo
or dataset URL, a distinctive experiment description), (c) de-anonymisation by stylometry or by
cross-referencing the public preprint, or (d) that the *source* repository history is anonymous.
It is a necessary negative check, not a proof of anonymity.

## 5. Residue vs the approved UTMLR2 baseline — **CONTRADICTED (as written)**

My count on my own rebuilt `scratch/vutmlr5/tmlr/main.tex` with the recipe's own `SWEEP` set:
`private-doc-name` **2** (L120, L346 — both the `internal checklist` literal), `private-repo-word`
**1**, and `private-path`/`commit-sha`/`long-hex`/`analysis-json`/`author-name`/`email`/`orcid`/
`repo-host`/`host-name`/`zenodo`/`dated`/`preprint`/`git-word`/`commit-word` all **0**. So the *counts
themselves* reproduce.

The **baseline comparison does not**. `scratch/utmlr2/evidence.json` —
the file the verdict names as the baseline — records:

* `residue_sweep_after.private-doc-name.hits` = **0** (`lines: []`), `private-repo-word.hits` = 4;
* `residue_sweep_final.private-doc-name.hits` = **0** (`where: []`), `repo-word.hits` = **1**,
  `private-harness.hits` = 2, everything else named 0.

Neither `strategy/TMLR_VERIFICATION.md` nor `strategy/TMLR_VERIFICATION_2.md` mentions
`private-doc-name` or `private-repo-word` at all (grep: no hits), and neither states a residue
baseline. So: **the `private-repo-word` 1 half does equal the recorded baseline; the
`private-doc-name` 2 half equals a standard that the cited sources do not record (they record 0).**
A defensible *mitigation* exists — UTMLR2's `private-doc-name` regex may not have contained the
`internal checklist` literal, and the UTMLR5 hits are exactly that literal — so this may be a
pattern-set mismatch rather than a regressed scrub. But as written ("equals the previously approved
UTMLR2 baseline"), the claim is unsupported by, and in direct tension with, its own cited baseline.
The card's framing of UTMLR4 as "2/3/5" likewise does not reproduce from `scratch/utmlr4/evidence.json`
(that file shows `private-path` 2, `private-repo-word` 2, `internal-doc` 1, and no `private-doc-name` key).

## 6. Citation structure — REPRODUCED

Independent regex over source and variant: `\cite` calls 23, keys 23, distinct 13, `\bibitem` 13,
uncited **[]**, unresolved **[]**, `\bibitem[` (author-year labels) 0, `analysis.json` 0 — identical
for both files. Key-set difference is exactly the documented rename:
`source_decider_stack_2026` (source-only) ↔ `source_corpus_errata_2026` (variant-only), carried in
both the `\cite` and the `\bibitem`.

## 7. Numbers — REPRODUCED

Environment-stripped numeric multiset: **1203 → 1092** total, **347 → 310** distinct,
**added = []** (0). Removed top values (`10`×11, `15`×8, `2026`×7 …) are provenance datums.

## Verdict tables

* **contradicted (1):** "residue `private-doc-name` 2 … equals the previously approved UTMLR2
  baseline" — the cited baseline records 0 for that category (repo-word 1 does match).
* **overstated (2):** (a) "everything else 0" — `private-harness` = 2 and `digest-hex-word` = 3 are
  non-zero under the recipe's own pattern set (`private-harness` 2 also matches UTMLR2's baseline, so
  this is framing, not fabrication; EVIDENCE.md's own table is more careful than the card);
  (b) `tmlr.sty:20` → the runtime call is at **:21**.
* **not_reproduced (1):** the default-run PDF digest `971a96ae…` (fresh run `5a41f1fe…`) — expected
  timestamp effect, self-consistent with the pid-epoch caveat.
* **unverified (2):** that `scratch/utmlr2/**` constitutes an *approved* baseline beyond evidence.json
  (no approval record in `strategy/TMLR_VERIFICATION*.md` was found); the historical UTMLR4 "2/3/5"
  framing.

**Survived:** the derived artefact (bytes/lines/sha256, byte-identical across builds), the B1
red→green plus the load-time counter-test, every compile fact and both pinned-epoch digests, the
PDF-text anonymity sweep, the citation structure, and the numeric multiset guard.
