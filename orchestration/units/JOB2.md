# Unit card — JOB2

**Purpose:** Sweep US governmental research organisations and FFRDCs for AI/LLM/HPC/scientific-ML
roles and persist openings + coverage gaps to disk.

**Scope:** national labs (LBNL, ORNL, PNNL, ANL, LANL, Sandia, LLNL, BNL, Fermilab, SLAC, NREL,
INL), agencies (NIST, NIH, NSF, NASA/JPL, DARPA, IARPA, DOE Office of Science, NOAA, USGS, ARL,
AFRL), nonprofit FFRDC operators (MITRE, Aerospace, MIT Lincoln, CMU SEI, Battelle, Riverside,
IDA, RAND, SRI). Search engines declared broken → direct URL fetch only (curl / web_fetch / ATS
JSON APIs: Workday CXS, SmartRecruiters).

**Hard bound:** 30 min wall clock or 80 tool calls, whichever first; ~27 tool calls used (~39 min).

**Declared write paths:**
- `jobs/us-national-labs/**` (JOBS.jsonl, FINDINGS.md, scratch/)
- `orchestration/units/JOB2.md`
- `orchestration/handoffs/JOB2.json`

**Forced report-back:** valid-JSON handoff at `orchestration/handoffs/JOB2.json` + ≤15-line summary
sent to parent via `send_message`.

**Method / evidence:** every recorded opening was fetched; nothing inferred. Reachability probed
twice for failures; HTTP status + note recorded per unreachable URL.

**Status:** done (partial coverage — SPA/403-blocked boards documented as coverage gaps).
