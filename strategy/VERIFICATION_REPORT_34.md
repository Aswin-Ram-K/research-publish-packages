# VERIFICATION REPORT 34 — UVER34 vs UMERGE1 (bibliography merge + sentence rewrite)

Verifier: UVER34 (not the author). Unit under test: `orchestration/units/UMERGE1.md`, handoff
`orchestration/handoffs/UMERGE1.json`, upstream `strategy/ROBERTA_CLAIM_SOURCING.md` (UBEN1),
`strategy/VERIFICATION_REPORT_33.md` (UVER33). Independent re-run, not a re-read of the author's evidence.

## VERDICT: PASS — 9/10 confirmed; 1 contradicted detail (check 9, non-material to the artifact)

| # | claim | verdict |
|---|-------|---------|
| 1 | sentence no longer false | PASS |
| 2 | rewrite faithful, not overstated | PASS |
| 3 | standing policy unviolated | PASS |
| 4 | merge real and complete | PASS |
| 5 | regeneration reproducible | PASS |
| 6 | LaTeX clean | PASS |
| 7 | frozen records annotated not edited | PASS |
| 8 | no other number moved | PASS |
| 9 | meta-claim :80-82 vs :10-12 | PASS on substance, CONTRADICTED detail |
| 10 | red→green | PASS |

---

## C1 — the sentence is no longer false: PASS

**`MANUSCRIPT.md:182-191` (§2.1), current text (verbatim):**

> **One corpus claim is now sourced, and we cite it for its result.** The corpus's assertion that an
> encoder-only RoBERTa outperforms a fine-tuned LLaMA2-7B on 77-class intent classification is supported by
> Benayas, Sicilia & Mora-Cantallops (2024), *A comparative analysis of encoder only and decoder only models
> in intent classification and sentiment analysis*, *Language Resources and Evaluation* **59**(3):2007–2030,
> DOI `10.1007/s10579-024-09796-y` (`benayas2024comparative`). On BANKING77 (77 intents) the paper reports the
> encoder-only arm ahead of the fine-tuned decoder-only arm, and a decoder-only serving penalty of one to two
> orders of magnitude on a single T4 (29–108× at fixed output-token budgets). We cite it for that
> peer-reviewed, same-task encoder-over-decoder result; we do not reuse the corpus's "125M" formulation (the
> paper prints "approximately 110-120 million parameters") or its derived F1 gap, which the paper does not
> print. GLiNER and GLiClass, previously unsourced, now have identifiers and are treated in §2.2.

**`MANUSCRIPT.md:682-685` (§6.4 echo), current text (verbatim)** — note the +1 line shift from the card's
`:681-683`:

> survey. The corpus claim that was carried without an identifier — an encoder-only RoBERTa beating a fine-tuned
> LLaMA2-7B on 77-class intent classification — is now sourced to Benayas, Sicilia & Mora-Cantallops (2024),
> *Language Resources and Evaluation* **59**(3):2007–2030, DOI `10.1007/s10579-024-09796-y`, and cited for that
> result.

**`MANUSCRIPT.md:873-877` (References prose), current text (verbatim):**

> Industry `2025.acl-industry.68`, and arXiv `2507.11412` (ICLR'26). Unit **UMERGE1** then merged the remaining verified addition, and the bibliography now carries it as a 13th
> entry: **`benayas2024comparative`** — Benayas, Sicilia & Mora-Cantallops (2024), *A comparative analysis of
> encoder only and decoder only models in intent classification and sentiment analysis*, *Language Resources
> and Evaluation* **59**(3):2007–2030, DOI `10.1007/s10579-024-09796-y` — the peer-reviewed, same-task
> encoder-over-decoder study that sources the corpus claim; it is cited in §2.1 and §6.4.

None of the three LIVE sites asserts "no locatable identifier" / "unsourced" / "dropped". The same three
sentences are mirrored in `submission/main.tex:79`/`:81`/`:371`-region (regenerated, see C5/C6). The old
false clause survives only in FROZEN records, each behind a dated note (C7) — reported, not fixed, per card.

## C2 — faithful and not overstated: PASS

- "approximately 110-120 million parameters": the manuscript quotes the source's own wording. Cross-checked
  against `strategy/ROBERTA_CLAIM_SOURCING.md:131` — *"line 215: RoBERTa 'comprises approximately **110-120
  million parameters**'"* — the source doc's own primary-source extraction. The paper never prints "125M"
  (`ROBERTA_CLAIM_SOURCING.md:131`), and the manuscript says so.
- Result characterisation: "On BANKING77 (77 intents) the paper reports the encoder-only arm ahead of the
  fine-tuned decoder-only arm". Source-carried: Table 2 Banking column (RoBERTa 94.27/94.28 vs LLaMA2-FT
  70.87/72.17; `ROBERTA_CLAIM_SOURCING.md:121-122`), abstract "encoder-only models in general provide better
  performance than decoder-only models" (`:115`).
- **Note on the "macro-F1" framing:** the new sentence does **not** state a metric at all — it never says
  macro-F1, because it prints no F1 number. The corpus's 94.27/70.87 are the MACRO figures
  (`ROBERTA_CLAIM_SOURCING.md:128-129`), so the macro/micro distinction is simply not imported. That is
  metric-silent, not a mischaracterisation, and it is the safe choice under the do-not-cite bar.
- "29–108× at fixed output-token budgets" / "one to two orders of magnitude": Table 7, single T4, 29x/56x/108x
  at 10/25/50 max output tokens (`ROBERTA_CLAIM_SOURCING.md:130`). The inversion (corpus said "RoBERTa 29–108×
  faster"; paper reports a "decoder-only serving penalty") is faithful.
- Nothing the source never printed is attributed to the source: the two barred figures (94.27, 70.87) and the
  corpus's own arithmetic "+23.4" are all absent from the new prose and correctly labelled as the corpus's,
  not the paper's.

## C3 — standing policy unviolated: PASS

Policy line read myself — `orchestration/units/UPAPER9.md:65`, verbatim:

> exclusion. The do-not-cite list forbids the 94.27/70.87 numbers. Two units contradict; merging forces argument edits

It says what the authors claim (the do-not-cite list bars 94.27/70.87). The literal string `+23.4` is **not**
in that policy line (UBEN1 records it at `ROBERTA_CLAIM_SOURCING.md:132` and in UMERGE1's card as a barred
corpus artefact), but it is barred in practice anyway.

Counts (independent `grep -c`, patterns `94\.27`, `70\.87`, `\+23\.4`):

| file | matches |
|---|---|
| `papers/encoder-crossover-190/MANUSCRIPT.md` | **0** |
| `papers/encoder-crossover-190/submission/main.tex` | **0** |

Context: `UPAPER9.md:62-67` is headed "DO NOT MERGE" but `:66` itself refers the sourcing decision *"at
MANUSCRIPT.md:182-190/677-679 → sourcing decision for a dedicated unit"* — UMERGE1 is that dedicated unit,
and the do-not-cite bar (the part that is a *policy*, not a deferral) is honoured. Not a violation.

## C4 — merge real and complete: PASS

`REFERENCES.bib:284` opens `@article{benayas2024comparative,` (block `:284-300`, copied verbatim from
`REFERENCES_ADDITIONS.bib:109-145`) and carries `doi = {10.1007/s10579-024-09796-y}` and the matching `url`.

`submission/main.tex`: **13** `\bibitem` (was 12). New last entry, `main.tex:443`, verbatim:

> \bibitem{benayas2024comparative} Benayas, Alberto, Sicilia, Miguel {\'A}ngel and Mora-Cantallops, Mar{\c c}al, \emph{A Comparative Analysis of Encoder Only and Decoder Only Models in Intent Classification and Sentiment Analysis: Navigating the Trade-Offs in Model Size and Performance}, Language Resources and Evaluation, vol.~59, no.~3, pp.~2007--2030, Springer, 2024, DOI: 10.1007/s10579-024-09796-y, \url{https://doi.org/10.1007/s10579-024-09796-y}.

Well-formed (key, names, `\emph{}`, journal, vol/no, pages, publisher, year, DOI, URL), ASCII-only
(main.tex non-ASCII byte count = 0), and prints the full reference. Its `.bib` `note` (which quotes the barred
figures) is a working note and is not printed — only `\bibitem` text reaches main.tex.

## C5 — regeneration reproducible: PASS

`python3 scratch/uprep1/md2tex.py` run twice by me, live `submission/main.tex` after each:

- run1 sha256 `0ee1b11f0692474c174e920b0e534d044937da076fecff41a85796ba14d6f160`
- run2 sha256 `0ee1b11f0692474c174e920b0e534d044937da076fecff41a85796ba14d6f160`

Identical to each other **and** to UMERGE1's reported `0ee1b11f…`. `scratch/umerge1/main.tex.run2` is also
`cmp`-identical. **Also reported (card item):** the file that was already on disk before my first run had the
same sha256 — `cmp scratch/uver34/main.tex.before submission/main.tex` → IDENTICAL. So the concurrent editor
noted in the card left `main.tex` byte-identical to a fresh `md2tex.py` run; no `.tex`/`.md` drift survives.

## C6 — LaTeX clean: PASS

- non-ASCII bytes in `submission/main.tex`: **0** (python `ord(c)>127` count; generator log also reports
  `residual non-ascii in output: none`).
- placeholders: `[Author and/or title not recorded` **0**; `to be completed before submission` **0**.
- `\begin{` 32 = `\end{` 32. Braces `{` 1043 = `}` 1043.

## C7 — frozen records annotated, not edited: PASS

Before-image `scratch/umerge1/backup/**` vs live, counting deleted vs added content lines:

| file | deleted | added |
|---|---|---|
| `REFERENCES.bib` | **0** | 54 |
| `UNSOURCED_RETAINED.md` | **0** | 5 |
| `submission/BUILD_NOTES.md` | **0** | 5 |
| `submission/main.tex` | 0 | 0 (regenerated via backup/main.tex — see C5) |
| `MANUSCRIPT.md` | 15 | 19 (LIVE rewrite, expected — not a frozen record) |

Every frozen-record change is a pure addition of a dated `Note 2026-10-16 (UMERGE1)`:

- `UNSOURCED_RETAINED.md:12` — U1 table row bytes unchanged; new dated table row at `:18`; the U1 heading
  (old `:21`, now `:22`) bytes unchanged; dated note added at `:24-27`. Original "NOT FOUND / Dropped / not
  cited" text still present.
- `REFERENCES.bib:27-29` "STILL NOT INCLUDED, on purpose (no locatable identifier…)" — original three comment
  lines unchanged; dated note appended `:30-33`. Merge-claim header `:10-12` unchanged; dated note appended
  `:14-18`.
- `submission/BUILD_NOTES.md:54-56` item 8 — original three lines unchanged; dated note appended `:57-61`.

Nothing was rewritten; the only ~deletions in the whole set are the three LIVE argument regions of
`MANUSCRIPT.md`, which the card explicitly lists as corrected-in-place.

## C8 — no other number moved: PASS

`diff -u scratch/umerge1/backup/MANUSCRIPT.md MANUSCRIPT.md` produces exactly **3 hunks** — `@@ -178,15
+179,16 @@` (§2.1), `@@ -678,9 +679,10 @@` (§6.4), `@@ -868,6 +870,8 @@` (References prose). Since the only
changed lines lie inside those hunks, no number outside them can differ.

Number-token multiset delta (regex `\d+(?:\.\d+)?`), independent recomputation:

- REMOVED: `{8:1, 125:2, 94.27:3, 70.87:3, 2410.01627:1}`
- ADDED: `{4:1, 3:3, 1:2, 2:1, 2.1:1, 2024:4, 7:1, 77:2, 59:3, 2007:3, 2030:3, 10.1007:3, 10579:3, 024:3, 09796:3, 110:1, 120:1}`

Every removed token is part of the falsified clause being replaced (`125M`, the barred pair, the corpus's
`+23.4` arithmetic shown as `94.27/70.87`, the `2410.01627` UREFS search-diligence reference, and the `≥ 8
phrasings` count). Every added token is a bibliography field of the new entry (2024, 59, 2007, 2030, DOI
fragments) or the quoted "approximately 110-120 million parameters" and the retained `77`/`29`/`108`.
`29` and `108` are PRESERVED (not in either delta). Matches UMERGE1's handoff delta. `REFERENCES.bib` changes
are additive-only (C7), so no pre-existing number there moved.

## C9 — meta-claim about `REFERENCES.bib:80-82`: PASS on substance, ONE CONTRADICTED DETAIL

Region `:80-82` read: it is the tail of the `note` field of `@misc{pride2309_03882,` (`:71-85`, the Zheng et
al. "PriDe" entry) — *"…2023-09-07, v4 2024-02-22; the arXiv comment field reads ``ICLR 2024 Spotlight''…"*. It
**is not** a merge claim. Region `:10-12` read: *"% MERGED BY UNIT UPAPER1c (2026-10-15) from UREFS's
verified additions (REFERENCES_ADDITIONS.bib, REFS_VERIFIED.md). Every added entry was observed on a page
UREFS fetched on 2026-10-15. The five pre-existing entries above are preserved unchanged."* — that **is** the
merge claim, and "partly true" is the right judgement: it is accurate for the five entries it enumerates
(`:14-19`) but was incomplete, since `benayas2024comparative` was the one addition withheld.

- CONTRADICTED: the UMERGE1 handoff says `:80-82` *"lies inside the gcd2305_13971 entry"*. It does not.
  `gcd2305_13971` starts at `REFERENCES.bib:86`; `:80-82` is inside `pride2309_03882` (`:71-85`). The unit
  named the wrong entry. Its substantive point (no merge claim at `:80-82`; the real claim is `:10-12`) stands,
  and no artifact depends on the wrong entry name.

## C10 — red→green (mandatory): PASS

Method: patched a **copy** of `scratch/uprep1/md2tex.py` (`scratch/uver34/md2tex_red.py`, ROOT redirected to
`scratch/uver34/red/…`), populated it with the live `MANUSCRIPT.md` + `scratch/umerge1/backup/REFERENCES.bib`
(pre-merge). Live files untouched by this test.

- **RED** (`REFERENCES.bib` reverted, copy): generator exit 0; `\bibitem` count **12**;
  `\bibitem{benayas2024comparative}` count **0**; output sha256 `277fd7331646c8f3454e2df9055896d02ab49b76d1692371d2f7f600a38f7c30`. Check FAILS as required.
- **GREEN** (copy of the real `MANUSCRIPT.md` + real `REFERENCES.bib`, same patched script): exit 0;
  `\bibitem` count **13**; sha256 `0ee1b11f0692474c174e920b0e534d044937da076fecff41a85796ba14d6f160` — identical to
  the live `submission/main.tex`.

**Not vacuous, one line:** the red arm feeds the actually-pre-merge bibliography and the measured quantity
genuinely flips (12 vs 13 `\bibitem`, benayas entry 0→1), so the check distinguishes a reverted state from the
shipped one rather than always passing.

## Also reported (not fixed)

- **Surviving "unsourced/uncited" statements under `papers/encoder-crossover-190/`**, all FROZEN records with a
  dated pointer, plus one change-log file:
  - `UNSOURCED_RETAINED.md:12` (U1 row) still reads *"**NOT FOUND** … **not cited**; explicitly named as
    unsourced and dropped"* — frozen, pointer at `:18` and `:24-27`.
  - `UNSOURCED_RETAINED.md` U1 section body (the `**Claim as the corpus carried it:**` block and `:39`-region
    "§2.1 now records it as unsourced and dropped from…") — frozen under the `:24` note.
  - `REFERENCES.bib:27-29` "STILL NOT INCLUDED, on purpose (no locatable identifier…)" — frozen, pointer
    `:30-33`.
  - `submission/BUILD_NOTES.md:54-56` item 8 ("excluded … The merged `REFERENCES.bib` already omits it") —
    frozen, pointer `:57-61`.
  - `MANUSCRIPT_CHANGES.md:81` and `:156` describe the *old* "four works have no locatable identifier" text as
    a historical change-log (`C7`); they are process records, not shipped prose, and were not annotated by
    UMERGE1. This is the only surviving *un-annotated* recital of the stale state I found.
  - LIVE prose is clean: no such statement in `MANUSCRIPT.md` or `submission/main.tex`.
- **`main.tex` freshness:** currently byte-identical to a fresh `md2tex.py` run (C5) — the earlier concurrent
  editing left no residue.

Blocker: none. Bound: 20 tool calls; used 11 (incl. this report's writes).
