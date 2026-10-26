# JOB2 — US Governmental Research Organisations & FFRDCs — findings

**Date observed: 2026-10-15** (all entries). Sweep window ≈ 18:26–19:05 UTC (~39 min wall clock,
≈26 tool calls). Search engines were NOT used (per unit brief: broken); everything below was
fetched directly (curl / web_fetch / ATS JSON APIs).

## 1. Ranked shortlist (only openings actually fetched)

| # | Org | Role | Location | URL | PhD? | Citizenship/clearance | FIT |
|---|-----|------|----------|-----|------|------------------------|-----|
| 1 | ORNL | Research Associate, Agentic Workflows | Oak Ridge, TN | https://jobs.ornl.gov/job/Oak-Ridge-Research-Associate%2C-Agentic-Workflows-TN-37830/1438081700/ | **PhD required** (Basic Qualifications, fetched) | not stated in fetched posting text | 5 |
| 2 | ORNL | Postdoc Research Associate – AI for Science | Oak Ridge, TN | https://jobs.ornl.gov/job/Oak-Ridge-Postdoctoral-Research-Associate-AI-for-Science-TN-37830/1435902700/ | **PhD required** (must not pre-date the postdoc window) | not stated in fetched text | 5 |
| 3 | CMU SEI (FFRDC) | Senior ML Research Scientist – Frontier Lab | Pittsburgh PA (2 locs) | https://cmu.wd115.myworkdayjobs.com/SEI/job/Pittsburgh-PA/Senior-Machine-Learning-Research-Scientist---Frontier-Lab_2024076-1 | not fetched | **not fetched — DoD FFRDC roles commonly US-citizenship-gated; VERIFY** | 5 |
| 4 | CMU SEI (FFRDC) | Senior ML Research Scientist – Secure AI Lab (SAIL) | Pittsburgh PA (2 locs) | https://cmu.wd115.myworkdayjobs.com/SEI/job/Pittsburgh-PA/Senior-Machine-Learning-Research-Scientist---SAIL_2024055-1 | not fetched | as above — VERIFY | 5 |
| 5 | CMU SEI (FFRDC) | AI Red Team Engineer / Senior AI Red Team Engineer | Pittsburgh PA (2 locs) | .../job/Pittsburgh-PA/AI-Red-Team-Engineer_2025000-1 · .../Senior-AI-Red-Team-Engineer_2025001-1 | not fetched | as above — VERIFY | 5 |
| 6 | LLNL (FFRDC) | Explainable AI – Postdoctoral Researcher | Livermore CA (hybrid) | https://jobs.smartrecruiters.com/LLNL/3743990014567496-explainable-ai-postdoctoral-researcher | **PhD required at hire** (fetched) | No clearance required; NDAA-2025 §3112 bars PRC/Russia/Iran/DPRK citizens on long assignments | 4 |
| 7 | LLNL (FFRDC) | Sidney Fernbach Postdoctoral Fellow | Livermore CA | https://jobs.smartrecruiters.com/LLNL/3743990015752688-sidney-fernbach-postdoctoral-fellow | **PhD required** (fetched) | No clearance required (same NDAA note) | 4 |
| 8 | ORNL | Senior Research Scientist, HPC and AI | Oak Ridge TN | https://jobs.ornl.gov/job/Oak-Ridge-Senior-Research-Scientist%2C-HPC-and-AI-TN-37830/1389423700/ | **PhD + 6 yrs post-PhD research** (fetched) | not stated in fetched text | 4 |
| 9 | RAND (FFRDC) | Research Lead – AI Cyber Testing & Evaluation | Washington DC | https://rand.wd5.myworkdayjobs.com/External_Career_Site/job/Washington-DC-DC-Metro-Area/Research-Lead----AI-Cyber-Testing---Evaluation_R3122 | PhD language present on sampled pages (title-level observed) | not fetched | 4 |
| 10 | JPL (FFRDC) | JPL Postdoc: Edge Vision Language Models and Foundation Models | JPL Campus, Pasadena | https://citjpl.wd5.myworkdayjobs.com/en-US/Jobs/job/JPL-Campus/JPL-Postdoctoral--Edge-Vision-Language-Models-and-Foundation-Models_R6045 | not fetched | not fetched | 4 |
| 11 | JPL (FFRDC) | Postdoc: Advanced Command and Control AI Systems | JPL Campus | .../job/JPL-Campus/Postdoc--Advanced-Command-and-Control-AI-Systems_R6075 | not fetched | not fetched | 4 |
| 12 | SEI (FFRDC) | AI Security Researcher / Senior AI Security Researcher | Pittsburgh PA | .../job/Pittsburgh-PA/AI-Security-Researcher_2024808-1 etc. | not fetched | VERIFY | 4 |
| 13 | ORNL (title-only) | AI Cyber Engineer · Postdoc Atomistic ML · Postdoc AI+CFD · HPC-for-Neuromorphic staff · Programming Systems postdoc | Oak Ridge TN | see JOBS.jsonl (each URL observed) | not fetched | not fetched | 3 |
| 14 | RAND (FFRDC) | Lead for Counter-AI (Geopolitics of AGI); Senior Research Lead AI Security; AI Security Resident; AI & Biosecurity Resident; Information Scientist (Applied Tech Policy) | DC / SF / Remote | see JOBS.jsonl | not fetched | not fetched | 3 |
| 15 | LLNL | Senior Cyber AI Engineer | Livermore CA | https://jobs.smartrecruiters.com/LLNL/3743990015543656-senior-cyber-ai-engineer | BS required, **MS/PhD preferred** | **BLOCKED: DOE Q clearance ⇒ U.S. citizenship required** | 3 |
| 16 | JPL | Data Scientist II/IV TS/SCI; Robotics Technologist II (Learning-Based State Estimation); ML radar postdoc; Data Scientist IV | JPL Campus | see JOBS.jsonl | not fetched | TS/SCI variants ⇒ clearance-gated | 2–3 |

Full per-opening records (36 `open` rows) are in `JOBS.jsonl`.

**Why these fit the profile** (independent empirical research on agent state kernels, LLM-agent
harness evaluation, pre-registered experiments, AGPL-3.0 codebase): the closest genuine match in
the whole sweep is **ORNL "Research Associate, Agentic Workflows"** (agent workflows, PhD-level,
research staff). **SEI's AI Red Team / AI Security Researcher** roles are evaluation-centric
(attacking/evaluating LLM systems = closest industry analogue to harness evaluation), and
**ORNL AI-for-Science + LLNL Explainable AI** are scientific-ML / trustworthy-AI research posts
with independent research ownership. Nothing in this subdomain mentions pre-registration or
open-source licensing; that is not stated in US lab postings as a rule.

## 2. Cap-exempt reasoning (governmental research organisations, 8 CFR 214.2(h)(8)(iii)(F))

- **National labs (LBNL, ORNL, PNNL, ANL, LANL, Sandia, LLNL, BNL, Fermilab, SLAC, NREL, INL)**
  are federally funded research and development centres (FFRDCs) operated *for the US Government*
  — DOE/NNSA/NSF contracts run through a university (UC, Battelle/UT-Battelle, Fermi Research
  Alliance, Stanford/SLAC) or a nonprofit. Two cap-exempt routes apply to an employee of the
  *operator*: (a) the operator is a **nonprofit research organisation** and (b) where the operator
  is a university or affiliated nonprofit, the **governmental-research-organisation / university**
  route. Practically: a hire made *by the operator entity* (not by a staffing supplier) is
  cap-exempt, so H-1B cap numbers are not the obstacle.
- **Agencies (NIST, NIH, NSF, NASA, DARPA, IARPA, DOE, NOAA, USGS, ARL, AFRL)** are themselves
  **US Government entities** — direct federal employment needs no H-1B at all (except
  contractor-staffed support roles, which are *not* cap-exempt through the agency).
- **Nonprofit FFRDC operators on the list** — MITRE, Aerospace Corporation, MIT Lincoln Laboratory
  (MIT affiliate), CMU SEI (CMU affiliate), Battelle, Riverside Research, IDA, RAND, SRI — are
  501(c)(3)/university-affiliated **nonprofit research organisations**; their direct hires are
  cap-exempt. Joint university–lab appointments inherit the **university's** cap-exempt status.
- Caveat: cap-exempt *employer* ≠ *work authorised*. See next section — that is the real filter.

## 3. Citizenship / clearance constraint — stated plainly

**This is the dominant disqualifier in this subdomain, and it disqualifies much of the list.**

- **Confirmed in fetched text:** LLNL *Senior Cyber AI Engineer* — "DOE Q-level security clearance
  which requires U.S. citizenship". **1 role explicitly blocked.**
- **Clearance-gated (implied US citizenship by clearance sponsorship):** JPL *Data Scientist II
  TS/SCI* and *Data Scientist IV TS/SCI* — **2 roles**; any ORNL "Classified Environment" HPC roles
  seen in the same category (titles observed) would be Q-clearance gated too.
- **Country-based statutory bar (not a US-citizenship bar):** LLNL postdocs carry **NDAA-2025
  §3112** — citizens of China, Russia, Iran, DPRK generally barred on assignments >179 days.
- **Not stated in the postings we fetched:** the three ORNL detail pages contained **zero**
  occurrences of "citizen"/"clearance" — but ORNL routinely screens for US citizenship in
  practice for DOE work, so treat "not stated" as *unverified*, not as free.
- **Unverified but likely:** SEI, RAND, JPL-non-TS, and all other FFRDC roles — my budget ran out
  before detail pages were fetched; **do not assume clearance-free.**
- **Bottom line:** an applicant who is not a US citizen should treat LLNL, JPL, SEI, RAND and
  (probably) ORNL/BNL/SLAC classified-adjacent roles as unavailable, which removes the majority
  of high-FIT rows above. Non-citizen-friendly residual: ORNL postings that state no clearance
  (verify per posting), LLNL postdocs (NDAA country bars only), and any purely unclassified
  software/research roles.

## 4. Coverage — what was actually reached

- **Orgs attempted: 37 distinct** (12 national labs · 11 agencies · 9 FFRDC operators · plus
  entries for NIST/NIH/NSF/NOAA/USGS/ARL/AFRL as separate rows).
- **Orgs with real job data extracted: 6** — ORNL (category search + 3 detail pages),
  LLNL (SmartRecruiters API: 26 ML matches, 15 LLM, 21 sci-ML, 3 HPC; 4 detail posts),
  JPL (Workday API: 4/9/5/2 hits per term), RAND (Workday API: 8 AI hits), CMU SEI (Workday API:
  21/22/6/30 hits), Fermilab (Workday API reached, **no relevant roles**).
- **Orgs attempted but not extractable: 31 gap entries** — all listed with URL + HTTP status in
  `JOBS.jsonl` (`status:"unreachable"`). Highlights: ANL 403 (×2), INL 403 (×2), NREL 000 (×2),
  Aerospace 403, Battelle 403, AFRL 403, IARPA 403, ARL 000, NSF 202/0 bytes, DARPA 404,
  NOAA 404, USGS 404, SEI old-path 404, IDA job-openings 404, Sandia 404, LANL 404/244-byte stub.
- **HTTP 200 but JavaScript-only (SPA) — a coverage gap, never guessed:** LBNL `jobs.lbl.gov`
  (identical homepage bytes for every query), PNNL iCIMS, MITRE Phenom, SLAC Oracle Recruiting,
  BNL jobs, Riverside iCIMS, SRI iCIMS, Lincoln Lab careers, **and USAJOBS itself** (200, JS
  shell) — meaning **all USAJOBS-only agencies (NIST vacancies, NIH/CIT/NLM, NSF, NOAA, USGS,
  ARL, AFRL civilian, DOE Office of Science) produced ZERO recorded openings.**
- **Partial discovery left on the table:** Workday tenants `nrel.wd1` and `inl.wd5` exist
  (HTTP 406/422 = host up, wrong site slug) — a follow-up unit that resolves the site slug from
  the Workday SPA can unlock NREL and INL quickly.

## 5. Honest limits

- 36 openings recorded; **only 4 have fetched degree/citizenship text** (3 ORNL + 3 LLNL; RAND
  pages fetched but text not parsed). Everything else is title+URL observed — requirements
  marked "not fetched", never invented.
- Re-sweep: failures were retried at least twice (ANL, INL, NREL, LANL, plus Workday slug
  guesses); all failures above are on the second attempt.
