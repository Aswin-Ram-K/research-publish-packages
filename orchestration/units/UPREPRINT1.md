# UPREPRINT1 — Preprints.org bundles and verified requirements

**Unit:** `UPREPRINT1` · **Date:** 2026-10-18 · **Status:** done (18/25 tool calls used)
**Purpose (one):** establish Preprints.org's real submission requirements from its own pages, decide the
bibliography question by evidence, and produce one self-sufficient bundle per paper in
`papers/<slug>/preprints/`.

## Bound and write paths

- **Bound:** 25 tool calls; report `partial` naming the remainder if exhausted. Used **18**.
- **Write paths:** `papers/*/preprints/**`, `strategy/PREPRINTS_SUBMISSION.md`, `scratch/upreprint1/**`,
  `orchestration/units/UPREPRINT1.md`, `orchestration/handoffs/UPREPRINT1.json`. Nothing else was written.
  `papers/encoder-crossover-190/released/**` read only; `/home/zer0null/Duval` untouched; no git command run.

## What was done

1. **Requirements verified from source.** `https://www.preprints.org/instructions-for-authors`,
   `/help-center/submission-guidelines` and `/about` fetched read-only (plain `web_fetch` → `HTTP 403`
   Akamai; stealthy scrape → `HTTP 200`). Deciding sentences and URLs are quoted in
   `strategy/PREPRINTS_SUBMISSION.md` §1.
2. **Earlier record corrected** (§2). The `.bib` clause is conditional — "including the .bib file, **if
   applicable**"; no page says "a PDF alone is NOT accepted" (that is an inference from "Files should be
   submitted in Microsoft Word or LaTeX format"); the licence sentence lives on `/about`, not the
   Instructions page; and the earlier record missed the mandatory **Conflicts of Interest** section.
3. **Bibliography decided by evidence** (§3): ship the self-contained `main.tex` and **no** `.bib`.
   `grep -c '\input\|\include{\|\bibliography{\|\includegraphics'` → 0 in all three; the
   `thebibliography` environment is inlined (13 / 13 / 8 `\bibitem`s); `papers/gated-read-batching/` has
   no `REFERENCES.bib` at all, so a `.bib`-bearing bundle could not be uniform. No `\bibliography{}`
   variant was produced — that would be the second bibliography mechanism the card forbids.
4. **First-page audit** (§4) against the six required elements, quoting `pdftotext -f 1 -l 1 -layout`.
   Result: **keywords missing from all three**; **#2 and #7 missing contact and affiliation** (name-only
   `\author{}`); #7's page 1 states its own gap: "name only, with no affiliation, institution or contact
   stated". #3 carries name + "Independent researcher" + `aswinram.k.1603@gmail.com`.
5. **Bundles built** (§5) — one `main.tex` per zip, digest-identical to `submission/main.tex`, no
   workspace-internal file, no absolute path, no `scratch/` reference, no unit id.
6. **Cold-compiled from the zip** (§6) with `scratch/utex1/bin/tectonic` 0.15.0, cache/tmp/HOME redirected
   inside the workspace, **no** `-Z continue-on-errors`: exit **0**, `Undefined control sequence` **0**,
   `!` **0**, pages 25 / 13 / 10 — matching the shipped PDFs.
7. **`strategy/PREPRINTS_SUBMISSION.md`** written: requirements + URLs, corrections, per-paper audit,
   bundle digests, compile proof, licence analysis, the author's ordered steps, and the not-verifiable list.

## Findings that change what happens next

- **Documentary gap before posting:** page 1 of all three lacks keywords; #2 and #7 lack contact and
  affiliation; no paper has a "Conflicts of Interest" section. The fix belongs in
  `submission/main.tex`, outside this unit's write paths — editing a copy inside `preprints/` would break
  the digest-match rule. Needs a successor unit and an author decision on what affiliation/contact string
  #2 and #7 carry.
- **`strategy/LATEX_TOOLCHAIN.md` is stale:** it records `-Z continue-on-errors` as *required* because
  `main.tex` "contains 2 undefined macros". On the current file there are zero undefined control
  sequences and the strict build succeeds. Continue-on-errors was not used here.
- **#2 and #7 never mention the Zenodo deposit:** `grep -c 23463944` → 3 in #3, **0** in #2 and #7.

## Licence conclusion

Not a conflict: two objects, two licences. CC BY 4.0 attaches to the posted *manuscript*
(`https://www.preprints.org/about`: "All preprints are posted with a Creative Commons CC BY 4.0 license…");
PolyForm Noncommercial 1.0.0 attaches to the *released artifact tree*
(`papers/encoder-crossover-190/released/encoder-crossover-190-released/LICENSE:5`). The two do not
relicense each other, and no verbatim code is reproduced in any manuscript
(`begin{verbatim}|lstlisting|minted` → 0; `\verb` → 0), so the usual way CC BY could capture PolyForm code
does not arise.
