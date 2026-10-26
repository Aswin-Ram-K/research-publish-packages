# Scandinavian / Northern-European AI & research-engineering openings — JOB3b (final)

Observed: **2026-10-15**. Every row in `JOBS.jsonl` was confirmed by fetching the posting or its official vacancy board (search snippets alone were never recorded). 10 rows total: 5 carried over from the failed previous run (already verified by it) + 5 added this run.

## ⭐ Roles that explicitly do NOT require a PhD (the priority list)

| # | Org | Role | Proof | URL |
|---|-----|------|-------|-----|
| 1 | **Simula (Oslo, NO)** | Research Engineer – AI Safety: revisjon og red teaming (2 yr) | Verbatim: *"Mastergrad i informatikk, maskinlæring … eller tilsvarende erfaring. Doktorgrad er velkommen, men ikke et krav."* | https://www.simula.no/careers/job-openings/research-engineer-ai-safety-revisjon-og-red-teaming-2-rig-stilling |
| 2 | **SINTEF Digital (NO)** | Analytics & AI — Junior Researcher (**MSc** track) and Researcher (PhD track) | Advert states MSc applies for junior-research-scientist lane; agentic AI + industrial ML; deadline 04/11/2026 | https://www.sintef.no/en/sintef-group/career/vacant-positions/position/145811/ |
| 3 | **KTH (SE)** | Research Engineer in Robotics, Perception and Learning | No doctoral-degree requirement anywhere in the ad (sibling KTH ads say PhD explicitly — this one does not) | https://www.kth.se/lediga-jobb/976498?l=en |
| 4 | **TNO (NL)** | Research Software Engineer Geoscience Utrecht (#1430) | Verbatim: *"An MSc or PhD in Earth Sciences…"* — MSc sufficient; degree level "Master" | https://www.tno.nl/en/careers/vacancies/2026/10/research-software-engineer-geoscience/ |
| 5 | **TNO (NL)** | Internship — Cross-lingual transfer for Dutch LLM pretraining | Internship lane (student-level, no PhD); LLM-pretraining research | https://www.tno.nl/en/careers/vacancies/2026/10/internship-cross-lingual-transfer-dutch |
| 6 | **TNO (NL)** | Internship — Data-driven corpus mixtures for data-efficient LLM pretraining | Internship lane; LLM data-efficiency research | https://www.tno.nl/en/careers/vacancies/2026/10/internship-data-driven-corpus-mixtures |

**"Doktorgrad er velkommen, men ikke et krav" chase result:** the exact Simula phrase family was re-searched; the AI-safety research-engineer ad (#1) is the only live Simula posting with it today. Simula's full board (fetched 200) now shows only that role + a PhD position (InnoGuard MSCA) + an open-application page. SINTEF's MSc-junior lane (#2) is the other confirmed "PhD optional" pattern in Norway.

## Open but PhD-gated (recorded for completeness, lower priority)
- KTH Postdoc in LLM inferencing — https://www.kth.se/lediga-jobb/972326?l=en
- KTH Postdoc sustainable GenAI for media — https://www.kth.se/lediga-jobb/974287?l=en
- KU Copenhagen Computational & Data Staff Scientist, NNF Center for Protein Design (deadline 08-11-2026; "A PhD in bioinformatics, data science or a related domain" is essential) — https://jobportal.ku.dk/alle-opslag/?show=169121
- UiO PhD Research Fellow, Knowledge-Grounded LLM Agents for Defensive Cyber Operations (#309937, doctoral-training post) — https://www.jobbnorge.no/en/available-jobs/job/309937/…

## Sponsorship / residence-permit evidence
- **No posting in this sweep explicitly mentions visa sponsorship** — normal for Scandinavia (employer posts the job; the work-permit / EU Blue Card / researcher-residence decision happens afterwards via migration agencies: Migrationsverket SE, UDI NO, SIRI DK, Migri FI).
- Practical signals: KTH, SINTEF and Simula ads are English-working-language and at institutions that hire internationally; SINTEF flags possible **Security Act clearance**, which can disadvantage non-Norwegian (non-EU) candidates — treat SINTEF as EU-friendly first.
- The three Nordic no-PhD roles (#1–3) are all at research-performing organisations where a researcher residence permit / EU Blue Card is a routine route.

## Failed URLs / coverage gaps (status recorded, nothing guessed)
| URL | Status |
|---|---|
| https://www.ri.se/en/lediga-jobb , https://www.ri.se/lediga-jobb , https://jobb.ri.se/ (RISE, SE) | **HTTP 403 "Sidan har blockerats"** — WAF-blocks this network (curl + scraper) — NOT searched from here |
| https://ut.ee/en/job-offer/junior-lecturer-artificial-and-natural-intelligence (Tartu, EE) | **HTTP 403 Access denied** — posting exists (search-engine index) but content unverifiable here |
| https://www.aalto.fi/en/careers → wd3.myworkday.com/aalto (Aalto, FI) | Workday login-gated (cxs API 404 / redirect) |
| https://jobbanken.dtu.dk/ (DTU, DK) | DNS/connection failure (000) from this network; DTU landing page 200 but listings not inline |
| https://www.norce.no/... (NORCE, NO) | now redirects to heydi.no → 404 (org transition?) |
| https://www.ntnu.no/ledige-stillinger (NTNU, NO) | 200 but listings JS-rendered — no server-side titles extractable |
| https://www.jobbnorge.no/ search UI | 200 but SPA (no server-rendered results); individual job pages verify OK |
| https://jobs.50skills.com/ru (Reykjavik U, IS) | 200 but SPA shell; no server-rendered listings — RU ML/cyber postdocs seen only via search index |
| https://www.hi.is/en/vacancies (U. of Iceland) | 200 but no AI-relevant titles in server HTML |
| https://www.chalmers.se/lediga-tjanster , /en/work-at-chalmers/lediga-tjanster/ | 404 |
| https://www.uio.no/english/about/employment/ , /vacancies/ (old paths) | 404 — correct path found: /english/about/vacancies/academic/ (200) |
| https://www.dtu.dk/english/about-dtu/job , /about-dtu/job-at-dtu | 404 — correct: /english/about/job-and-career/vacant-positions (200, but list is external/JS) |
| DFKI careers dfki.de/en/jobs, dfki.de/en/service/job-offers | Cloudflare challenge / error page (stealthy scrape reaches nav only) |
| jobs.dfki.de/ausschreibungen.html (DFKI offer list) | 200 but the actual offer table is **login-gated** — no listings visible anonymously |
| https://www.iais.fraunhofer.de/de/karriere/stellenangebote.html (Fraunhofer IAIS) | 200; page renders only nav/theme links server-side — live offers not extractable anonymously (JS) |
| https://www.iais.fraunhofer.de/en/jobs.html, https://nora.ai/jobs | 404 |
| INRIA careers (FR) | Anubis bot-check ("Making sure you're not a bot!") |
| ETH careers (CH) | challenge shell only, no listings extractable |
| AI Sweden careers.ai.se | 200 — but **only MSc thesis-project slots** live today (LLM agents, LLM-as-judge, RLVR tool-calling…); no staff research-engineer vacancy. Closed precedent: "Senior ML Research Engineer" (deadline 2026-02-20) accepted "PhD … OR at least 4+ years of industry experience in ML development and research engineering" — evidence AI Sweden hires without a PhD. |

## Coverage statement
Swept this run (direct board fetches): Simula ✔(complete), SINTEF EN+NO ✔(complete), KTH ✔(previous run, rows kept), VTT ✔(complete — no AI role live), KU Copenhagen ✔(all-opslag), UiO ✔(academic vacancies via jobbnorge), TNO ✔(3 pages of vacancies), CWI ✔(vacancies — only quantum/bio PhD-gated roles live), NTNU/UiB/AI Sweden/AAU/AU/Iceland/RU/Taltech/Tartu/Chalmers/RISE/Aalto/DTU/DFFKI/INRIA/ETH — probed, outcomes and failures as tabled above. Boards whose listings are JS-only (NTNU, jobbnorge search, RU 50skills, Aalto Workday, DTU jobbank, RISE WAF, Tartu 403) are the honest limits of this run; RISE and Tartu are the two most promising to re-check from a different network.
