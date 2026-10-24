# UH2 — India & Europe/Scandinavia research routes independent of student status

**Status:** done (with a required `UNVERIFIED` list) · **Date:** 2026-10-15 · **Bound:** max 60 tool calls; used 58.
**Declared write paths:** `strategy/VISA_INDIA_EUROPE.md`, `orchestration/units/UH2.md`, `orchestration/handoffs/UH2.json` — nothing else touched.

## One purpose
Map the India and Europe/Scandinavia research routes that do **not** depend on student status, and
find real precedents, for a researcher in AI/agent-runtime systems ("Consonance" corpus, working
paper, findings register, AGPL-3.0 codebase) whose school stopped issuing OPT/CPT.

## Deliverable
[`strategy/VISA_INDIA_EUROPE.md`](../../strategy/VISA_INDIA_EUROPE.md) — country × route table (28 rows),
fellowship table (20 funds), India section, precedent-matching table (P1–P10), `UNVERIFIED` list (23
items), ranked top-3 recommendation with a concrete first step each, and a not-legal-advice disclaimer.

## Method and its limits (the honest part)
- Official sources only for load-bearing claims: Migrationsverket (SE), Ny i Danmark/SIRI (DK),
  EURAXESS Norway & Finland national portals (official EU network) where the national authority was
  unreachable, `gesetze-im-internet.de` (DE federal law), IND (NL), European Commission (MSCA), ERC,
  Research Council of Norway, ANRF/Startup India/IndiaAI (IN).
- **No search backend existed in this session:** `local_web_search` returned "no results" for every
  query; the harness `web_search` errored ("no API key for DEEPSEEK_API_KEY").
- **`udi.no` (NO) and `migri.fi` (FI) blocked every fetch path** — curl with browser UA, Crawl4AI,
  Scrapling `stealthy`, an extraction proxy, two public CORS proxies — with HTTP 403 (Azure WAF /
  Cloudflare). `archive.org` returned **HTTP 429** for the whole session, killing the archived-copy
  fallback. Those countries therefore lean on the official EURAXESS national portals, and their
  authority-specific values went to `UNVERIFIED` rather than being asserted.
- `make-it-in-germany.com` (Radware bot check) and `regjeringen.no` (403) also blocked.

## Verified load-bearing facts (with sources)
- **SE researcher permit:** doctorate **or** eligibility to start a doctoral programme; a **business**
  can be the approved research principal; hosting agreement + ≥50% research hours + SEK 9,700/month.
- **SE EU Blue Card:** 180 credits **or five years' relevant professional experience**;
  threshold **SEK 53,625/month** since 15 July 2026.
- **SE ordinary work permit:** salary floor **SEK 34,470/month** (90% of median SEK 38,300).
- **SE PR:** from 11 June 2026, **three years** of continuous research/doctoral/EU Blue Card permits.
- **DK Pay Limit:** **DKK 552,000/year**, explicitly **no educational requirement**; 1 month; DKK 6,810.
- **DE §18g(2) AufenthG:** EU Blue Card **without** the academic qualification for ISCO-08 groups
  133/25 with ≥3 years' experience in the last 7 years.
- **MSCA PF** and **ERC StG** both **require a PhD** + a host organisation — aspirational, not near-term.

## Precedents
Rule-level precedents P1–P9 are verified with verbatim excerpts and official URLs. **No named
individual precedent could be sourced** (no search backend, archive.org 429) — recorded explicitly as
P10 and in the `UNVERIFIED` list. Nothing was invented; no deadline, amount, program name or URL is
stated without a source behind it.

## Blocker
Not a blocker to the deliverable, but a hard limit on its completeness: **no web search, and the
Norwegian and Finnish immigration authorities plus archive.org were unreachable for the entire
session.** Norway/Finland-specific thresholds, fees, processing times and PR paths are `UNVERIFIED`.

## Next unit hint
A follow-up unit (with working search, e.g. a SearXNG instance that returns results) should: (1) open
`udi.no` and `migri.fi` through a search-engine cache or a fresh egress and fill the NO/FI cells;
(2) read the ANRF Ramanujan Fellowship and N-PDF eligibility text in a JS-capable browser;
(3) resolve the nationality branch (Indian citizen vs OCI vs foreign national); (4) source named,
checkable individual precedents for researchers entering Scandinavia on a foundation fellowship.
