# UARXIV1 — publication without arXiv endorsement

**Unit:** UARXIV1 · **Date:** 2026-10-15 · **Bound:** ≤45 tool calls (used 44 incl. card/handoff/message).
**Write paths:** `strategy/PUBLISH_WITHOUT_ENDORSEMENT.md`, this card, `orchestration/handoffs/UARXIV1.json`.

## Purpose
Find the concrete path to a **public, dated, citable, peer-reviewable** paper #3 (`papers/encoder-crossover-190/`)
for an **unaffiliated independent researcher**, given that arXiv now requires endorsement (policy of 2026-01-21)
and an institutional email alone is no longer sufficient. Extend — and, where wrong, correct —
`strategy/PUBLICATION_STRATEGY.md` §8 without editing it.

## Method
Primary-source fetch only; no claim from memory. Read §8/§2/§9/§11 of `PUBLICATION_STRATEGY.md` first; fetched
arXiv endorsement + moderation + rate-limit pages and the two governing blog posts, TMLR Home/Submissions/Author
Guidelines/FAQ, Preprints.org About, Research Square preprints page, Zenodo Quickstart/Principles/Policies, OSF
Preprints help, USCIS Policy Manual Vol 2 Part M Ch 4. Failed/unrendered fetches are recorded as gaps, never
worked around from memory (ICLR 2027 workshops HTTP 404; OpenReview docs body did not render; SSRN never fetched).

## Findings (headline)
1. **Direct answer: conditional `yes`.** #3 can be public, dated and DOI-bearing with **no endorsement** —
   Preprints.org or Research Square (stated "free", stated DOI, no endorsement/affiliation requirement); Zenodo
   for the artefact DOI. It cannot be made *peer-reviewed* without a venue — and the peer-reviewed route does not
   need arXiv either.
2. **TMLR does not require an arXiv preprint** (submissions.html: direct OpenReview submission; author-guide.html:
   "Authors are also allowed to upload their submissions to arXiv or other preprint servers at any time" =
   optional; faq.html: preprints accepted). CC BY 4.0 **from time of submission** confirmed verbatim; no fee
   stated on four pages; survey papers excluded since 2026-09-01.
3. **arXiv mechanics confirmed:** endorsement required for a first submission **in all categories**; first path
   needs institutional email **AND** prior accepted arXiv authorship in the domain (both, not either); otherwise
   personal endorsement only, one per endorsement category; six-character code obtained by starting a submission;
   "The endorsement process is not peer review"; "arXiv staff cannot waive endorsement requirements".
4. **Rate limits confirmed verbatim:** 2 new submissions/calendar month, 3 active; **rejections count** ("whether
   they are accepted or rejected, you will have to wait until the next month"); applies across all categories.
5. **8 routes assessed; 4 give a DOI with no endorsement and no affiliation** (Preprints.org, Research Square,
   Zenodo, OSF Preprints).
6. **Honest separation enforced:** preprint ≠ peer-reviewed, in the deliverable and in the O-1 read-out
   (USCIS criterion 6: "The article is normally peer-reviewed"; criterion 5 needs third-party citations).
7. **Corrections recorded for `PUBLICATION_STRATEGY.md`** (named by line, file untouched): line 321 (and §10 item 1)
   — institutional email **cannot** remove the endorser requirement alone; line 61 — arXiv is **not** a TMLR
   prerequisite; line 288 — TMLR "journal DOI" **uncorroborated**; line 348 — "all categories" now answered,
   cs.\* domain granularity still unverified.

## Blocker
None. Two fetches were unreachable (ICLR 2027 workshops page HTTP 404; OpenReview docs body did not render) and
are recorded as `UNVERIFIED` rather than filled in.

## Next unit hint
A verifier should re-fetch S1/S2/S4/S6/S7 and check the four correction lines against
`PUBLICATION_STRATEGY.md`; and separately settle the two live gaps — TMLR's DOI and cs.\* endorsement-domain
granularity — neither of which changes the recommended sequence.
