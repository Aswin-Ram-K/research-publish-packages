# UTMLRPOL1 — TMLR policy check for the planned publication order

**Unit id:** UTMLRPOL1
**Workspace:** `/home/zer0null/reserach extarctor`
**Parent agent:** session-c3d61727-8af8-4c19-b1b9-5922c347a11a

## One purpose
Establish, from TMLR's own published rules (jmlr.org/tmlr/ and subpages, OpenReview TMLR venue
instructions), what the author's planned publication order does to a TMLR submission.

## The author's plan (the input this unit must judge)
Deposit data on Zenodo → post the paper as a public Preprints.org preprint under the author's real
name → later submit the same work to TMLR. A public GitHub repository and a Zenodo DOI for released
artifacts will also exist.

## Questions to answer (each with verbatim quote + fetched URL)
1. Public identified preprint already posted — allowed? under what conditions?
2. Must the TMLR submission avoid citing/linking that preprint / its DOI?
3. Is an arXiv preprint required at all? (author is not arXiv-endorsed and won't use arXiv)
4. Anonymity rules at submission, and what happens to anonymity after acceptance?
5. AI-use disclosure requirement (a previous unit found TMLR silent — re-check and quote).
6. Required LaTeX style file (`tmlr.sty`?), where obtained, what the portal accepts (PDF only? source?)
7. Review timeline and decision options (accept / reject / major revision).
8. Code and data availability requirement, and in what form.
9. Rule about the work being under review elsewhere simultaneously.

## Method
- Local web search `http://127.0.0.1:8080/search?q=<query>&format=json`; `local_web_crawl` for full pages.
- Primary sources only (jmlr.org/tmlr/*, OpenReview venue instructions). No blog summaries.
- Ambiguous rule → quote the whole paragraph, not a convenient fragment.
- Unreachable page → mark NOT VERIFIED; never invent a quote.

## Hard bound
18 tool calls. If a specific rule cannot be found from a primary source within budget, STOP and report
which one is unresolved.

## Write paths (nothing else)
`scratch/utmlrpol1/**`, `strategy/TMLR_POLICY.md`, `orchestration/units/UTMLRPOL1.md`,
`orchestration/handoffs/UTMLRPOL1.json`

## Prohibitions
No account creation, no submission, no contact with anyone. No credential/token/ORCID in any file.
No writes outside the listed paths.
