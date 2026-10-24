# UV1 — Publication strategy (publicly viewable, peer-reviewable, citable at minimum cost)

**Purpose (one):** determine how to get this research publicly viewable, peer-reviewable and citable at minimum cost and friction, in service
of an O-1 (extraordinary ability) petition, and produce a costed, ordered plan.

**Bound:** max 55 tool calls; STOP and report `partial` if exceeded. **Used: 39.**
**Write paths:** `strategy/PUBLICATION_STRATEGY.md`, `orchestration/units/UV1.md`, `orchestration/handoffs/UV1.json` (nothing else).

## Inputs
- `strategy/PAPER_CANDIDATES.md` (710 lines, 2026-10-11) — ranking + recommended sequencing #3 → #1 → #4 (read; not re-argued).
- `/home/zer0null/Duval` (read-only) — repo, `CITATION.cff`, fixture, git history.
- Primary sources only for every load-bearing claim (28 sources in the §12 ledger).

## Method
Version-pinned extraction rather than whole-page reading: eCFR via its XML API (title 8 up to date as of 10/13/2026), USCIS Policy Manual and
the venue pages fetched with `urllib` and reduced to targeted excerpts under a regex, so the tool output stayed bounded. Local measurements on
the target repo for the history/licence/fixture facts. `local_web_search` returned `no results` on three attempts and `web_search` was
unavailable (no `DEEPSEEK_API_KEY`); the venue landscape was therefore built from the venues' own conference pages instead of search.

## Findings (each already evidenced in the deliverable, §12)
1. **The load-bearing discovery: arXiv mints a DataCite DOI for every submission, free.** "All articles submitted to arXiv are automatically
   assigned DOIs … submitted to DataCite **at no cost to the authors**." (info.arxiv.org/help/doi.html, 2026-10-14) → "publicly viewable +
   citable" is a **$0, ~1-week** move, independent of peer review.
2. **All three recommended venues cost $0 in fees** — TMLR (no fee stated on four official pages), JOSS ("no fees for submitting or
   publishing"), JAIR ("no publication fees are charged to authors"), and ICLR 2027 workshops ($0 to submit; papers must be posted publicly on
   OpenReview). The cheapest credible route is therefore not a compromise; it is the free route in the right order.
3. **JOSS is blocked by a measured gate, with a date.** The repo's earliest commit is 2026-09-28 (857 commits, non-shallow), so "public for
   more than six months" cannot clear before **≈2027-03-28**; and JOSS needs *demonstrated research use*, which the corpus's own arXiv postings
   will supply.
4. **The O-1 mapping is 3 of 8, which is exactly the minimum** — (B)(6) authorship (met by Step 0 alone, on USCIS's own words), (B)(5) original
   contributions of major significance (the #4 flagship, needs independent citations), (B)(1) prizes, reachable only if a **best-paper award** is
   deliberately hunted. (B)(4) judging is the stretch fourth. **Publication is not a criterion; authorship is** — quoted verbatim against both
   the regulation and the Policy Manual.
5. **The workshop question is settled by USCIS text, not opinion.** Conference presentations count if they are *published*; the ICLR 2027 rule
   forcing accepted papers onto OpenReview therefore matters more than the workshop/journal distinction.
6. **Endorsement is the only real prerequisite and it is checkable in week 1** — start a submission, pick the category, and you are emailed an
   endorsement code; an institutional email may remove the requirement entirely. Whether cs.AI/cs.SE/cs.PL/cs.LG are separate endorsement
   domains is `UNVERIFIED`.
7. **NeurIPS 2026 workshops are already closed** (proposal deadline 2026-06-06); **Distill has been on hiatus since 2021-03-04**; MLSys 2027's
   window (2026-10-19 → 10-30) is the only imminent deadline.
8. **The second-labeller fix is bounded and cheap in quantity, not yet in price:** 190 measured cases × 2 passes ≈ **12.7 person-hours**,
   unlocking **four** candidates (#3, #4, #5, #10). The hourly rate is `UNVERIFIED` and this document deliberately carries no currency figure.

## Deliverable
`strategy/PUBLICATION_STRATEGY.md` — venue comparison table (22 venues/mechanisms), DOI & archival mechanics, the 8-criterion O-1 mapping with
verbatim quotes, a month-by-month costed timeline (Oct 2026 → Jul 2027), the explicit (a)/(b)/(c) comparison with a recommendation, the
second-labeller cost analysis, a "do this next week" checklist, a 13-item `UNVERIFIED` list, and a 28-row source ledger
(URL · page date · verbatim excerpt).

## Honesty notes carried into the deliverable
- Where a venue page states **no** fee, the document says "no fee is stated on the pages checked" (a verifiable negative) rather than "it is free".
- The **USCIS Policy Manual chapter carries no "last reviewed" stamp in the fetched HTML**, so its page date is `UNVERIFIED`; the eCFR source is
  pinned to "title 8, up to date as of 10/13/2026".
- The task prompt's phrase "lesser nationally or internationally recognized prizes" is the **Policy Manual's** gloss; the **regulation** at
  8 CFR 214.2(o)(3)(iii)(B)(1) reads "nationally or internationally recognized prizes or awards". Both are quoted in place rather than blended.
- The user-facing assumption "publication satisfies a criterion" is corrected explicitly (Policy Manual: published work "will not necessarily
  establish" major significance).

## Containment
Target repo touched read-only (`ls`, `cat`, `head`, `wc`, `grep`, `git log`, `git rev-list`, `git tag`, `ls .git/shallow`); no writes, no git
state change, no hooks. Nothing outside the three declared write paths was written.
