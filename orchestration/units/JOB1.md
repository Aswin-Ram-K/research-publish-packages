# Unit card — JOB1

**Purpose:** Sweep US cap-exempt nonprofit research orgs + AI research institutes for open roles matching an
AI/LLM-agent-evals research profile; persist verified openings only.

**Scope:** named target list (24 orgs) + university-affiliated research foundations discovered during the run.
Search engines known broken — direct URL fetch only (curl / web_fetch).

**Hard bound:** 30 minutes wall clock OR 80 tool calls, whichever first. Retries: every failed URL re-tried ≥2×.

**Declared write paths:**
- `jobs/us-nonprofit-research/**` (JOBS.jsonl, FINDINGS.md, .cache/)
- `orchestration/units/JOB1.md`
- `orchestration/handoffs/JOB1.json`
- one appended dated line in `jobs/README.md` (file did not exist at start; created by another unit mid-run,
  then appended to — not created or overwritten by JOB1)

**Result:** partial→done. 30 orgs attempted, 26 reached (some partial), 58 open openings recorded,
53 URLs still failing at last attempt (full list in FINDINGS.md §3).

**Failure modes observed:** NXDOMAIN (astera.institute, palisaderesearch.com, machineintelligenceinstitute.org),
403 Cloudflare (Gusto board, mitre.org, openphilanthropy root), 404 wrong slugs (corrected via site links),
JS-only boards (iCIMS, Apollo webflow, SFI), Open Phil careers 301→coefficientgiving.org (unexplained redirect).

**Handoff:** `orchestration/handoffs/JOB1.json`.
