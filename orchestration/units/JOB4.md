# JOB4 — Evals/Safety orgs + Open-source Foundations sweep

**Status:** done (within 30-min wall clock; search engines unused by design — direct fetch only)
**Date observed:** 2026-10-15
**Scope:** (a) paid roles at AI evaluation/safety orgs, (b) grants/fellowships/fiscal-sponsorship a
funding an individual can apply for without PhD/institutional affiliation.

## Write paths (declared)
- jobs/evals-safety-foundations/JOBS.jsonl (53 rows, appended incrementally in 3 batches)
- jobs/evals-safety-foundations/FINDINGS.md (2 ranked shortlists + failed-URL table + coverage)
- jobs/evals-safety-foundations/raw/** (fetched HTML/JSON evidence, re-verifiable)
- orchestration/units/JOB4.md, orchestration/handoffs/JOB4.json

## Method
1. Burst-swept target list with parallel `curl -L -A Mozilla` (batches of ~10), persisted rows
   after every burst (3 write batches: 13 + 19 + 21 rows).
2. Parsed ATS JSON APIs directly: Lever (`api.lever.co/v0/postings/{metr,epoch-ai}`),
   Greenhouse (`boards-api.greenhouse.io/v1/boards/{goodfire}`), Ashby posting-api.
3. Re-swept every 000/404 at least twice (up to 4 attempts each) and used JS-rendering crawl for
   bot-blocked hosts; correct-path re-pointing for 8 wrong-path 404s.
4. Verified before recording: a Greenhouse board slug `cais` was rejected after title-checking
   (unrelated investment firm) — no fabricated CAIS board recorded.

## Results (evidence)
- orgs_attempted 36 · orgs_reached 24 · unreachable rows 12 (all with HTTP status recorded)
- roles recorded 30 · individual-funding no-PhD/no-affiliation 8 · closed programmes 3
- top finds: Foresight AI-for-Science-&-Safety RFP ($30–100k, individuals, deadline 2026-10-31,
  open-source mandate); EA Funds/LTFF (individuals, any country); MATS Residency (2027 cohorts
  open, $1,250/wk + housing); Emergent Ventures (13+, direct apply); METR 9-posting Lever board
  incl. 2 evals MTS roles; Redwood MTS with $350k–850k band; UK AISI grants all closed.

## Hard failures (never retried past policy, recorded as coverage gaps)
apollo-research.org, palisaderesearch.com, caisafety.org, astera.institute, navigationfund.org,
openresearchfunders.org (all 000 after ≥3 attempts ± crawl); sloan.org 403; fastgrants.org 404;
alignmentresearch.org/careers 404; eleuther.ai/careers 404.
