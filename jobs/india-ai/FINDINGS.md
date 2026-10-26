# JOB5 — India: research institutes, national AI initiatives, industry AI labs

**Observed (all dates):** 2026-10-15 · **Data file:** [`JOBS.jsonl`](JOBS.jsonl) (24 entries, 17 org labels)
**Method:** local SearXNG discovery → every claim below re-verified by direct fetch (`web_fetch` / `curl -sL -A "Mozilla/5.0 …"`). Search snippets alone were never recorded.

---

## Shortlist A — Roles (ranked)

| # | org | title | location | PhD? | fit | status |
|---|-----|-------|----------|------|-----|--------|
| 1 | Sarvam AI | Data Scientist – Evaluations, Chanakya (eval harnesses, red-teaming, RAGAS/Eval Harness/LangSmith) | Bengaluru, on-site | not_mentioned (3–6 yr exp) | 5 | open (200) |
| 2 | Google | Post-Doctoral Researcher, PhD, 2026 Start (Fixed-Term) — *postdoc research employment; JSONL entry_type=fellowship* | Bengaluru | **yes** | 5 | open (200) |
| 3 | Microsoft (MSR India network) | Bangalore facet = 10 live roles incl. Research Software Development Engineer‑MSRI and Principal Applied Scientist – Foundation Models, **Agents** & Decision Intelligence | Bangalore | preferred for scientist roles | 4 | open (200) |
| 4 | Sarvam AI | Agent Engineer + 42 open positions (ML Ops Chanakya, Staff Eng API Platform, model roles) | Bengaluru/Delhi | not_mentioned | 4 | open (200) |
| 5 | Google Research | Global research careers hub; India results page live (team=Research, location=India) | global + India | preferred | 4 | open (200) |
| 6 | Google | Software Engineer, PhD, Early Career 2026 + Software Engineer, PhD, Static Program Analysis | Bengaluru | **yes** | 3 | open (200) |
| 7 | IBM Research | Artificial Intelligence Researcher (+ Cloud/Quantum research roles) | not stated on page — confirm India per job | preferred (typical) | 3 | open (200) |
| 8 | IIIT‑Hyderabad | Careers portal: project-staff channel (hiring.projectstaff@iiit.ac.in), recruitment portal, BaSIL Lab openings PDF (2024, stale) | Hyderabad | not_mentioned | 3 | none_found (200) |
| 9 | AI4Bharat (IIT Madras) | Careers page "Available Roles" **empty**; contact enquiry@ai4bharat.org | Chennai | not_mentioned | 3 | none_found (200) |
| 10 | Wadhwani AI | Careers index lists ML Scientist (LLM), Associate ML Scientist, ML Intern, Impact Analytics Fellow — **all 3 ATS postings tested return "no longer available"** (expired 2026-10-15) | Mumbai | not_mentioned | 4 (fit if a posting reopens) | none_found (200) |
| 11 | Fractal Analytics | Careers page live; AI roles not itemised | India | not_mentioned | 2 | none_found (200) |

**Requires a PhD:** Google Post‑Doctoral Researcher (#2), Google PhD SWE tracks (#6). **Does not:** #1, #3 (scientist roles preferred), #4, #8–#11.

## Shortlist B — Fellowships/grants an individual can apply for (ranked)

| # | scheme | who applies | PhD required? | amount (as stated on official page) | deadline | status |
|---|--------|-------------|---------------|--------------------------------------|----------|--------|
| 1 | **ANRF N‑PDF** (National Post Doctoral Fellowship) | individual, via host institution; portal `anrfonline.in/ANRF/npdf` (200) | **yes** (or thesis submitted) | Rs 80,000/month (Rs 50,000 until degree awarded) | not_mentioned on FAQ; portal live | open (200) |
| 2 | **ANRF PM Early Career Research Grant** (PM ECRG) | individual (age ≤42, relaxations) | not_mentioned | up to Rs 60 lakh / 3 years | call-based, not_mentioned | open (200) |
| 3 | **ANRF TARE** | researcher with own salary, applies with parent+host institutions | not_mentioned | Rs 60,000/year fellowship + Rs 5 lakh/annum research grant (≥90 days/year at host) | call-based | open (200) |
| 4 | **ANRF Ramanujan Fellowship** | scientist abroad (Indian/Indian-origin, <40), host institution in India | preferred (PhD / MTech / MD + track record) | Rs 1,35,000/month incl. HRA + Rs 7 lakh/annum grant + Rs 60,000/annum overhead; 5 yrs | **until 31.12.2026 17:00**, results twice/year | open (200) |
| 5 | **IndiaAI Fellowships** (FutureSkills pillar) | students (UG/PG/PhD) — likely via institutions; `indiaai.gov.in/fellowship` = **404** | **no** | not stated in govt release | not_mentioned (2025 cycle reportedly 30 Apr — secondary source) | open per PIB 29.07.2026 (200) |
| 6 | **IISc Postdoctoral Fellowship** | individual | **yes** | not on page | not_mentioned | open (200) |

**Not individual-applicable (verified on official pages):** ANRF **J.C. Bose** — nominations only by Heads of Institutions (individuals_may_apply=no; Rs 25 lakh/annum observed); ANRF **PAIR** — only a Hub institution may submit; ANRF **PM Professorship** — superannuated faculty only (observed on the same FAQ page, therefore not shortlisted).

**No-PhD fellowships:** IndiaAI (students), TARE (PhD not mentioned), Ramanujan (Masters acceptable). **PhD required:** N‑PDF, IISc Postdoc, Google postdoc.

---

## Failed / blocked URLs (coverage gaps)

| URL | status | note |
|-----|--------|------|
| `https://www.pib.gov.in/PressReleasePage.aspx?PRID=2291062…` | 403 via page fetch | Akamai bot block; **curl with UA → 200** (used) |
| `https://www.tcs.com/careers/india/research-and-innovation` (and TCS AI-careers pages) | **403** both fetch & curl | bot-blocked; TCS Research openings NOT verified — manual browser check needed |
| `https://www.adobe.com/careers.html` | 403 | bot-blocked; Adobe Research India not verified |
| `https://www.krutrim.com/careers` | TLS failure (curl exit 35) | unreachable, retry needed |
| `https://www.imsc.res.in/jobs` | timeout (curl exit 28) | unreachable, retry needed |
| `https://www.anrf.gov.in/` (with `www`) | connection fail | **working mirror: `https://anrf.gov.in/` → 200** |
| `https://anrf.gov.in/schemes` | 404 | real scheme URLs are `/page/english/awards_fellowship` + `/page/english/research_grants` (both 200) |
| `https://www.indiaai.gov.in/fellowship`, `/careers` | 404 | SPA; IndiaAI verified via PIB release instead |
| `https://www.icts.res.in/careers`, `https://www.jncasr.ac.in/careers`, `https://www.iucaa.in/Vacancies/` | 404 | guessed paths; departmental pages not yet swept |
| `https://www.iitb.ac.in/careers`, `…iitd…`, `…iitk…` | 404 | guessed paths; IIT HR pages are elsewhere |
| `https://www.tifr.res.in/people/job_openings.shtml`, `/people/index.shtml`, `/admin/recruitment.html` | 404 | TIFR vacancy page not discoverable from homepage (200) |

## Coverage statement

- **Reached & verified (HTTP 200 content):** IISc (careers ×3 pages), ANRF (fellowship + grants FAQs), PIB/IndiaAI release, Google (hub + India results + postdoc job page), Microsoft (hub + open-positions + Bangalore facet), Sarvam (careers + job page), AI4Bharat, IIIT‑H, Wadhwani AI, IBM Research, Fractal, TIFR homepage, IndiaAI site root.
- **Blocked/unreachable:** TCS (403), Adobe (403), Krutrim (TLS), IMSc (timeout), guessed 404 paths (ICTS, JNCASR, IUCAA, IIT‑B/D/K, IndiaAI subpaths).
- **Not attempted in depth this run (gaps for next unit):** DBT/DST/CSIR/MeitY scheme pages, IndiaAI research hubs, ANRF OVDF/PAIR full text, ISI Kolkata & IIT departmental vacancy pages, Sierra/Postman/Atlassian India AI groups, Krutrim/Ola Krutrim retry, TCS/Adobe retry with alternate mirrors.
- **Visa fact:** an Indian citizen needs **no visa** to work in India (recorded as instructed).
- **Nationality branch:** the subject's nationality is NOT determined here — another unit covers the nationality branch. This unit only records India-based opportunities.

## Reliability rules honoured
Every amount, deadline and eligibility line above was read from the named page on **2026-10-15**; nothing was extrapolated from snippets. Fellowship cycles change yearly — re-verify before acting.
