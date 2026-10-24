# JOB5 — India AI/LLM opportunities sweep (30-min burst unit)

## Purpose (one only)
Sweep India-based opportunities — research institutes, national AI initiatives, industry AI labs, and
fellowships an individual may apply for — for AI/LLM systems, agent runtimes/evaluation, LLM infra,
applied ML; verify every candidate by direct fetch; persist to `jobs/india-ai/`.

## Hard bound
30 minutes wall clock or 90 tool calls, whichever first. Failures retried ≥2×; unverifiable URLs
recorded as coverage gaps with HTTP status. No invented jobs/fellowships/amounts/deadlines.

## Write paths (declared; no clashes with concurrent units)
- `jobs/india-ai/JOBS.jsonl` (incremental append after each burst)
- `jobs/india-ai/FINDINGS.md`
- `orchestration/units/JOB5.md` (this file)
- `orchestration/handoffs/JOB5.json`

## Method
1. `local_web_search` discovery bursts (SearXNG repaired — returns real results, with junk mixed in;
   treat snippets as leads only).
2. Direct verification: `web_fetch` first; government/Akamai sites (PIB, TCS) block fetch → `curl -sL
   -A "Mozilla/5.0 (X11; Linux x86_64) Chrome/124.0"`. ANRF works only on apex host (no `www`).
   `/tmp` is wiped between bash calls — curl+parse must happen in a single command.
3. Scheme facts (amounts, deadlines, eligibility) read verbatim from ANRF FAQ pages; job facts read
   from server-rendered careers pages (Google careers results, MSR open-positions with Bangalore city
   facet, Sarvam job pages).

## Outcome
24 JSONL entries, 17 org labels; FINDINGS.md with ranked role + fellowship shortlists, PhD-required
flags, all failed URLs with status, coverage statement, visa note (Indian citizen needs no visa) and
explicit note that the nationality branch belongs to another unit. Status: partial (CSIR/DBT/DST/MeitY,
Adobe/TCS/Krutrim blocked or unswept — named as gaps).
