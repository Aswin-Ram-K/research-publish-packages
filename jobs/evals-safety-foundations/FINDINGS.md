# JOB4 FINDINGS — AI Evaluation / Safety orgs + Open-source Foundations

**Observed:** 2026-10-15 (all dates in this file are the fetch date; postings expire)
**Method:** direct URL fetch only (`curl -L`, `web_fetch`-class crawls). Search engines were not used
(per unit card: they return zero results). Every entry below was fetched; nothing is inferred.
**Raw HTML preserved under** `jobs/evals-safety-foundations/raw/` for re-verification.
**Machine-readable data:** `JOBS.jsonl` — 53 rows, 36 organisations, 29 `open`, 3 `closed`,
9 `none_found`, 12 `unreachable`.

---

## Shortlist A — Paid roles (ranked by FIT)

| # | Org | Title | URL | PhD/affil? | FIT | Note |
|---|-----|-------|-----|-----------|-----|------|
| 1 | METR | Member of Technical Staff, Embedded Assessments | https://jobs.lever.co/metr/69792e29-e72c-44a2-8305-82cb40ab17c5 | **no** (no degree requirement stated) | 5 | AI capability/risk assessment; closest paid analogue to independent agent-eval research. Berkeley, full-time. |
| 2 | METR | Member of Technical Staff, Evaluation Execution | https://jobs.lever.co/metr/93baec4d-1e47-40f7-9990-6d7fef12da00 | **no** (not stated) | 5 | Hands-on evaluation execution. Berkeley. |
| 3 | Redwood Research | Member of Technical Staff | https://redwoodresearch.org/careers (apply → airtable form) | **no** (not stated) | 4 | Pay band stated on page: **$350,000–$850,000/yr**. Also links Constellation Astra Fellowship + MATS. |
| 4 | Epoch AI | Researcher / Senior Researcher | https://jobs.lever.co/epoch-ai/de7b4c71-ece2-454a-be70-e7b75c5f3b23 | unclear | 4 | AI measurement/benchmarking org, **remote** full-time. |
| 5 | Goodfire | Research Fellow | https://job-boards.greenhouse.io/goodfire/jobs/4499053008 | unclear | 4 | Interpretability lab; **all Goodfire roles are SF in-person 5 days/wk**. |
| 6 | Goodfire | Research Scientist | https://job-boards.greenhouse.io/goodfire/jobs/4746990008 | **yes** (PhD + publications in posting text) | 4 | Interpretability; degree gate + in-person SF. |
| 7 | METR | General Expression of Interest | https://jobs.lever.co/metr/f3a6db11-7fd1-48e4-af42-20aad1ded72d | **no** | 4 | Open channel: "anyone … any capacity", explicitly alignment researchers/contractors. |
| 8 | METR | MTS, Offensive Security Research | https://jobs.lever.co/metr/b1a2f73f-f927-4f8b-b1b3-b2e57604b5fd | unclear | 3 | AI security research at evals org. |
| 9 | Open Philanthropy → Coefficient Giving | Expression of Interest (Future Openings) | https://jobs.ashbyhq.com/coefficientgiving/2cc48fa8-97aa-47d8-b367-bf3b66cdba3f | unclear | 3 | **Note: openphilanthropy.org/careers now redirects to coefficientgiving.org.** Remote-global, only 1 live posting. |
| 10 | Epoch AI | Expression of Interest (+ Special Projects Associate EOI) | https://jobs.lever.co/epoch-ai/137cb0dc-03a6-4747-b9dc-8255194daee2 | unclear | 3 | Open applications, remote. |

Also live (lower fit): METR CISO / Head of People / IT Systems Engineer / Platform Eng-AppSec /
Member of Policy Staff (all Lever, 200); Goodfire MLE, Forward Deployed Research Scientist (PhD
mentioned), General Interest; Goodfire Research Scientist (London). Full list in `JOBS.jsonl`.

## Shortlist B — Funding an INDIVIDUAL can apply for WITHOUT a PhD or institutional affiliation

| # | Org | Type | Title | URL | Amount/Duration | Deadline | Eligibility (as stated) | FIT |
|---|-----|------|-------|-----|-----------------|----------|--------------------------|-----|
| 1 | Foresight Institute | grant | **AI for Science & Safety Grants RFP (CISAI)** | https://foresight.org/grants/grants-ai-for-science-safety/ | **$30,000–$100,000** typical | **2026-10-31 23:59 PDT** | "We accept applications from **individuals**, teams, and organizations"; no PhD/affiliation mentioned; **work product must be open-sourced** (matches an AGPL-3.0 codebase) | 5 |
| 2 | EA Funds / Long-Term Future Fund | grant | LTFF application via EA Funds portal | https://funds.effectivealtruism.org/funds/ltff (apply: /apply-for-funding) | varies per fund (not stated) | rolling | "EA Funds can make grants to **individuals** … **We accept applications from any country**" | 5 |
| 3 | Emergent Ventures (Mercatus) | fellowship | EV fellowship & grant program | https://www.emergentventures.org/ (apply: https://mercatus.tfaforms.net/5099527) | per proposal (not stated) | rolling | "Applicants must be **at least 13 years old**" — nothing else; **AI-written applications rejected on sight** (AI ok for proofreading only) | 4 |
| 4 | MATS | fellowship | MATS Residency — Winter & Summer 2027 cohorts **open** | https://www.matsprogram.org/residency | **$1,250/week stipend + housing (Berkeley/London) + visa support + up to $25,000 relocation** | cohorts open; exact date not stated | "researchers of **varying backgrounds** … if you are unsure whether you fit, we would rather you apply"; **no PhD requirement stated** | 4 |
| 5 | Algoverse AI Research | fellowship | AI Safety Fellowship (Nov 1 cohort) | https://algoverseairesearch.org/ai-safety-fellowship | stipend not stated; 60 seats/cohort | "Early deadline for the **November 1** cohort" | "open to **university students and industry professionals worldwide** … at least **undergraduate-level education**"; prior research experience ideal, not required | 4 |
| 6 | Constellation | fellowship | Astra Fellowship (advanced-AI-risk org incubator) | https://www.constellation.org/programs/astra-fellowship | funding + ops support (amount not stated) | not stated | "**Prior AI safety experience is not required** … we'd still encourage you to apply" | 3 |
| 7 | Constellation | fellowship | Generator Residency | https://generatorresidency.org/ | "**fully-funded**, three-month residency" | not extracted | generalists "pitch, build, and ship projects" for the AI safety ecosystem | 3 |
| 8 | Foresight Institute | fellowship | Foresight Fellowship — 2028 cohort | https://foresight.org/engage/fellowship/ | year-long; amount not stated | "Apply for the 2028 cohort" live | "early-career scientists, engineers, and innovators"; apply or nomination; no PhD mentioned | 3 |
| 9 | NumFOCUS | grant→fiscal route | Small Development Grants | https://numfocus.org/programs/small-development-grants | amount not stated | cycles **Oct 17** / Jun 6 (notify Nov 21 / Jul 11) | **individuals may NOT apply directly** — only "NumFOCUS Fiscally Sponsored or Affiliated projects"; route = sponsor your project first (https://numfocus.org/information-fiscal-sponsorship) | 3 |

**Closed but worth watching (institution-gated, so excluded from the "no affiliation" shortlist):**
UK AISI **Challenge Fund** (up to **£200,000**/project) and **Alignment Project** (up to
**£1,000,000**/project) — both "Applications are now closed" on https://www.aisi.gov.uk/grants, and
eligibility is "researchers based at eligible UK and international academic institutions and
non-profit organisations". Systemic AI Safety Grants also closed.

**Watchlist (fetched, but no fundable open cycle verifiable from static content):** Schmidt Sciences
("do not accept unsolicited proposals"; only visible open call was decarbonization —
https://www.schmidtsciences.org/opportunities), AI2050 (fellows pages only,
https://ai2050.schmidtsciences.org/), Manifund (JS-rendered rounds, https://manifund.org/),
Coefficient Giving GCR opportunities directory (grant cards JS-filtered,
https://coefficientgiving.org/funds/global-catastrophic-risks-opportunities/).

---

## Every failed URL (with status) — coverage gaps, never guesses

| URL | Status | Attempts / methods |
|-----|--------|--------------------|
| https://www.apollo-research.org/careers (+ apex, + root) | **000 / no connection** | 4 curl + 1 crawl (empty) + Greenhouse/Lever slug probes 404 |
| https://www.palisaderesearch.com/careers (+ apex) | **000 / no connection** | 4 curl + 1 crawl (empty) + ATS slug probes 404 |
| https://www.caisafety.org/ (+ /careers, apex) | **000 / no connection** | 4 curl + 1 crawl (empty); Greenhouse board slug `cais` belongs to an **unrelated investment firm** (title check) — not CAIS |
| https://www.astera.institute/ (+ apex) | **000 / no connection** | 4 curl + 1 crawl (empty) |
| https://navigationfund.org/ (+ www) | **000 / timeout** | 3 curl + 1 crawl (timeout) |
| https://openresearchfunders.org/ | **000 / no connection** | 4 curl |
| https://sloan.org/programs | **403** (bot protection) | 2 curl |
| https://fastgrants.org/ (+ www) | **404** | 3 curl — no homepage served; status of program unverifiable here |
| https://alignmentresearch.org/careers | **404** | 2 curl (home 200 but no job links) |
| https://eleuther.ai/careers | **404** | 2 curl (home 200, no hiring links) |
| https://www.aisi.gov.uk/jobs | **404** | 1 curl — correct page is **/careers** (reached, 200) |
| https://www.linuxfoundation.org/jobs | **404** | 1 curl — correct page is **/careers** (200, but positions link JS-only) |
| https://openssf.org/community/jobs-board/ | **404** | 1 curl — correct page is **/job-board/** (200 → gitjobs.dev) |
| https://numfocus.org/programs/numfocus-fiscal-sponsorship | **404** | 1 curl — correct page is **/information-fiscal-sponsorship** (200) |
| https://www.simonsfoundation.org/funding/opportunities | **404** | 1 curl — correct page is **/funding-opportunities/?status=Open** (200) |
| https://www.schmidtsciences.org/apply/ | **404** | 1 curl — correct page is **/opportunities** (200) |
| https://rethinkpriorities.org/careers | **404** | 1 curl — correct page is **https://careers.rethinkpriorities.org/** (200) |
| https://funds.effectivealtruism.org/funds/ltff/apply-for-funding | **404** | 1 curl — correct page is **/apply-for-funding** (200) |
| https://www.cooperativeai.com/post/grants2 | **404** (with/without slash) | 2 curl — CAIF grant-program posts not reachable at linked URL; coop home 200 |
| https://lmarena.ai/jobs | 200 but **JS-only, zero server text** | 1 curl — no listings observable |
| https://far.ai/careers | 200 but **JS-only, zero server text** | 1 curl |
| https://manifund.org/rounds | 200 but **no server-rendered rounds** | 1 curl |
| https://lf.ai/ | **000** | 1 curl |

## Reach / coverage

- **Orgs attempted:** 36 distinct organisations appear in `JOBS.jsonl` (17 from the evals/safety
  half of the target list, 17 from the foundations half, + 5 discovered during the sweep:
  MATS, Algoverse, Constellation/Generator, Coefficient Giving, NumFOCUS job board).
- **Orgs reached (HTTP 200 with usable content):** 24.
- **Unreachable:** 12 rows carry `status: unreachable` (list above).
- **Paid roles recorded:** 30 (`entry_type: role`), of which 29 have `status: open`.
- **Individual funding with no PhD/affiliation stated:** 8 (Shortlist B rows 1–8; row 9 is
  conditional via fiscal sponsorship).
- **Closed programmes recorded:** 3 (UK AISI grants).
- **Sweep pattern used:** org root → `/careers` `/jobs` `/grants` `/fellowships` → ATS APIs
  (`api.lever.co/v0/postings/<org>`, `boards-api.greenhouse.io/v1/boards/<org>`,
  `api.ashbyhq.com/posting-api/job-board/<org>`); wrong-path 404s were re-pointed to the real
  path wherever the site revealed one (marked in the table above).
- **Not exhausted (time-bounded):** Cooperative AI Foundation grant pages (home reachable,
  posts 404), Coefficient Giving GCR grant cards (JS), Apple/Sloan-class blocked hosts, Apollo &
  Palisade & CAIS ATS discovery (domain unreachable), Linux Foundation open-positions enumeration.

## Profile fit note
Best fits for "independent empirical research on agent state kernels, LLM agent harness evaluation,
pre-registered experiments, AGPL-3.0 codebase, no institutional affiliation":
**Foresight AI-for-Science-&-Safety RFP** (open-source mandate, individuals, $30–100k),
**EA Funds/LTFF** (individuals, any country), **MATS Residency** (funded research time),
**METR EOI + MTS evals roles**, **Redwood MTS**, **Epoch Researcher** (remote).
