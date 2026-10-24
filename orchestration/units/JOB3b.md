# Unit card — JOB3b (Research Extractor)

**Purpose:** Discover and verify AI/LLM/research-engineering openings at Scandinavian & Northern-European research institutes, universities and research-performing companies that a researcher with an independent empirical record could win **without a PhD**, and that can support a researcher residence permit / EU Blue Card.

**Run window:** 2026-10-15, 14:24–14:48 CDT (~24 min wall clock, ~65 tool calls). Continuation of a failed earlier run: its 5 verified JOBS.jsonl rows and raw/ HTML cache were reused; new findings appended, never clobbered.

**Write paths:** jobs/scandinavia-europe/**, orchestration/units/JOB3b.md, orchestration/handoffs/JOB3b.json

**Method:** local_web_search for discovery (noisy engine; results used only as leads) → direct verification by web_fetch / curl (browser UA) / local_web_scrape of the actual posting or its official vacancy board → row appended to JOBS.jsonl only after a fetch. Search snippets were never recorded as evidence.

**Hard result (fit 1–5, PhD optional):**
1. Simula Oslo, Research Engineer AI Safety (2yr) — "Doktorgrad er velkommen, men ikke et krav" — fit 5
2. SINTEF Digital, Junior Researcher (MSc) lane in Analytics & AI — fit 5 — deadline 2026-11-04
3. KTH, Research Engineer in Robotics, Perception and Learning — fit 5
4. TNO NL, Research Software Engineer Geoscience — MSc sufficient — fit 2 (domain transfer only)
5–6. TNO NL, two LLM-pretraining internships (cross-lingual transfer; corpus mixtures) — fit 3

**PhD-gated but recorded:** KTH LLM-inferencing postdoc, KTH sustainable-GenAI postdoc, KU/NNF Protein-Design Computational & Data Staff Scientist (deadline 2026-11-08), UiO PhD Fellow in Knowledge-Grounded LLM Agents for defensive cyber ops.

**Biggest coverage gaps (with status):** ri.se WAF 403; ut.ee job-offer 403; Aalto Workday login-gated; jobbanken.dtu.dk DNS-fail; NTNU & jobbnorge search JS-only; jobs.50skills.com/ru SPA; jobs.dfki.de login-gated; IAIS offers JS-only; norce.no → heydi.no 404; Chalmers lediga-tjanster paths 404.

**Sponsorship:** no posting in the sweep mentions sponsorship explicitly (normal for the region; permit handled by Migrationsverket/UDI/SIRI/Migri after offer). SINTEF flags possible Security Act clearance — EU candidates favoured.

**Status:** done. 10 JOBS.jsonl rows valid JSON; FINDINGS.md ranked by country.
