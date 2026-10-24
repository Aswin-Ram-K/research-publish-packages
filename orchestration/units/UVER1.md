# UVER1 — independent verification of VISA_INDIA_EUROPE.md and PUBLICATION_STRATEGY.md

**Purpose (one):** falsify the load-bearing claims of two delivered strategy documents. Not the author
of either. Produces a verdict, not a rewrite.

**Bound:** ≤55 tool calls. **Used: 23.** Stop condition: report `partial` on approach to the bound.

**Write paths (only these):**
- `strategy/VERIFICATION_REPORT.md`
- `orchestration/units/UVER1.md`
- `orchestration/handoffs/UVER1.json`

**Target:** `/home/zer0null/Duval` — read-only. Operations used: `git rev-list`, `git log`, `git tag`,
`ls`, `wc`, `grep`, `cat`. No write, no git state change, no hook installed.

## Method

Direct primary-source re-fetch of every load-bearing URL (curl with browser UA + HTML→text, and
`web_fetch`), because local SearXNG returns zero results and DuckDuckGo is CAPTCHA-walled. Verbatim
excerpts captured for each. Repo facts re-measured locally. Author's claimed coverage limits
(udi.no, migri.fi) re-tested on my own client.

## Result

| Document | Verdict |
|---|---|
| `strategy/VISA_INDIA_EUROPE.md` | **pass** |
| `strategy/PUBLICATION_STRATEGY.md` | **pass-with-corrections** |

- **contradicted: 0.** No claim falsified. Denmark Pay Limit (the rank-1 recommendation), the Sweden
  researcher/Blue Card/PR rules, §18g(2), the MSCA/ERC PhD gates, the P1–P9 precedent URLs, arXiv's
  free DOI, the three $0 venues, the ICLR/NeurIPS/Distill dates, the O-1 mapping and all measured repo
  facts reproduced exactly.
- **overstated: 1** — `PUB` L185's JOSS unblock date is stated flatly from commit history while `PUB`
  §11.10 concedes public visibility is `UNVERIFIED`; sound as a lower bound, one day optimistic, and
  the caveat belongs inline. No decision changes.
- **not_reproduced: 6** — ERC-2027-STG call dates, MLSys 2027 dates (already self-flagged §11.5),
  Software Heritage ISO date, Preprints.org footer, make-it-in-germany block (200 for me), two
  cosmetic metadata stamps. All coverage limits, none load-bearing.
- **unverified: 2** — the cosmetic metadata stamps.
- Coverage limits reproduced independently: `udi.no` HTTP 403, `migri.fi` HTTP 403.

## Artifact

`strategy/VERIFICATION_REPORT.md` — verdicts, 45-row claim table with URL + date + verbatim excerpt,
the separated not_reproduced / overstated / unverified lists, minor observations, and a "what would
change my verdict" section.
