# US1 — build a credible public research presence that compounds into O-1-grade evidence

**Unit:** US1 · **Status:** done · **Date:** 2026-10-11
**Hard bound:** maximum **55 tool calls**; STOP and report `partial` if it would be exceeded. **Used: 41.**
**Write paths (only these):** `strategy/SOCIAL_PRESENCE.md`, `orchestration/units/US1.md`, `orchestration/handoffs/US1.json`

## Purpose (one)

Produce a concrete, platform-by-platform plan to build a credible public research presence that compounds into
O-1-grade evidence — grounded in the real corpus, not generic advice.

## Inputs read

- `AGENTS.md` (workspace contract; handoff shapes; hard constraints).
- `strategy/PAPER_CANDIDATES.md` in full (710 lines) — the 14 ranked candidates, the 8 publishable-now set, the
  §D non-paper inventory, §E's O-1 leverage pick (#4) and sequencing recommendation (#3 → #1 → #4), and §F's
  corpus-level observations (measurement discipline as the real asset; external validity as every candidate's
  weakness; the shared 190-case fixture; bimodal `n`).
- `orchestration/STATUS.md` (head) — established that **SearXNG is degraded**, which is why the local search tool
  returned nothing all session and why pages were fetched directly by URL.
- One recent handoff (`orchestration/handoffs/U1.4.json`) for the practical shape of the contract.

## Method

1. Read the spec-of-record inputs (`AGENTS.md`, `PAPER_CANDIDATES.md`).
2. Established that search is unavailable in this workspace (local SearXNG "no results"; built-in `web_search`
   unconfigured; DuckDuckGo/Mojeek/Bing blocked or unhelpful; Reddit and a Redlib mirror blocked). Adapted by
   **fetching primary sources directly by URL** — which is a stronger evidence class where a URL can be named, and
   a coverage limitation where it cannot.
3. Fetched 15 primary pages with `web_fetch` and 4 search/scrape attempts with `local_web_scrape`.
4. Wrote the deliverable grounded in named candidates, findings, method learnings (M1–M14) and named gaps from
   `PAPER_CANDIDATES.md`, with every load-bearing external claim carrying a source id and date, and every
   unverifiable claim marked `UNVERIFIED`.

## Deliverable

`strategy/SOCIAL_PRESENCE.md` — sections: 0 the two facts that reframe the plan; 1 positioning (identity sentence;
3 anchor assets and release order; what to stop doing, as a table of never-post items); 2 nine platform plans
(LinkedIn; X/Bluesky; Scholar+ORCID+Semantic Scholar; arXiv+personal site; GitHub; Hugging Face;
ResearchGate/Academia.edu; HN/Reddit/Lobsters; conferences/meetups), each with purpose, exact setup, cadence,
content format, failure mode; 3 the 12-month compounding ladder; 4 the O-1 mapping across all eight criteria plus
the petitioner and peer-group-consultation facts; 5 a 30-day ordered checklist (23 items); 6 honesty section;
plus a 17-entry source table and a record of the failed sources.

## Key load-bearing findings (all with a fetched primary source)

- **arXiv endorsement changed on 2026-01-21**: an institutional email is no longer sufficient for a new submitter;
  it now needs institutional email **and** prior authorship in the endorsement domain, or a **personal
  endorsement** `[S2]`. This is the first hard wall for an unaffiliated researcher and the plan routes around it.
- **arXiv rate limit**: 2 new submissions per calendar month, 3 active `[S4]`; "proposals for future research",
  supplemental material and short works are typically **not accepted**, and articles "should be complete final
  drafts" `[S6]` — so the findings register / programme / pre-registration set belongs on the personal site, not
  arXiv.
- **Google Scholar**: a verified **institutional** email is required for inclusion in Scholar search results;
  non-institutional addresses are "not suitable" `[S14]`. A real structural disadvantage, stated as such.
- **O-1A**: O beneficiaries **may not petition for themselves**; a separate entity they own (LLC/corp) or a U.S.
  agent may file `[S10]`. Criterion 5 explicitly names "contributions to repositories of software, data, … **with
  evidence of significant … impact in the field**" — the load-bearing words are *evidence of impact* `[S9]`.
  Paid association membership explicitly does **not** satisfy criterion 2 `[S9]`.
- **Peer review is now rationed**: ARR (2026-09-11) reports 38 % of ~17 K May 2026 submissions came from authors
  with no publication record, and each submission must supply a qualified service contributor `[S13]` — the
  circular dependency is named, along with ARR's manual-application and mentorship escape hatches.
- **Zenodo/GitHub**: enabling the repo and creating a release yields a DOI-bearing record archived in Software
  Heritage; `.zenodo.json` overrides `CITATION.cff` entirely `[S7][S8]`.
- **Show HN norms**: Show HN is for things people can **run**; reading material is off-topic and must be a regular
  submission; no solicited upvotes `[S12]` — hence "Show HN the harness, submit the paper".

## Honest limitations of this unit

- **`UNVERIFIED`**: 2026-specific LinkedIn reach mechanics and the X-vs-Bluesky researcher split. No citable
  primary source was reachable; the only observed signals (arXiv blog share buttons include Bluesky; ARR lists
  Bluesky first among contacts) are weak. Both are marked `UNVERIFIED` in the deliverable rather than asserted.
- The subreddit rule text is stated as long-standing norm, not a fetched quote (`UNVERIFIED`).
- The plan is downstream of the papers: if #3 and #2 are not written, no platform mechanic substitutes. The
  deliverable says this in §6.
