# JOB6 — Agent Runtime / Evals / Memory — GLOBAL discovery findings

**Unit:** JOB6 (discovery unit — first unit to use the repaired local SearXNG search)
**Observed date:** 2026-10-15
**Method:** query sweep with `local_web_search` → **every hit verified by direct fetch** (`curl -sL -A "Mozilla/5.0"` on the posting page, or the platform's official API where the HTML page is bot-blocked) → record.
**Deliverable:** `JOBS.jsonl` — **49 openings, 27 employers, all fetched (HTTP 200 except the one documented gap)**.

---

## 1. Method recap: what actually worked (reusable recipe)

### Phase A — search to discover targets (queries that produced the best yields)

| # | Query | Yield (verified openings from it) |
|---|---|---|
| 1 | `site:jobs.ashbyhq.com "agent runtime"` | **best single query** — Profound, Sierra, Callosum, Matter Intelligence, NinjaTech, DataSnipper ×2, Viktor (8) |
| 2 | `"agent runtime" engineer job hiring` | Taktile, Glean (via syndication), Anthropic (via syndication), Profound/Callosum re-confirm |
| 3 | `site:jobs.lever.co "agent" evals OR evaluation researcher engineer` | Apollo Research ×2, Binance ×3, Level AI, Valarian, Unusual/Helios (7) |
| 4 | `"durable execution" OR "event sourcing" LLM agent engineer job` | Unit (Principal Eng, screened out — fit 2), Trase Systems (not fetchable from original board) |
| 5 | `site:jobs.ashbyhq.com "evals" OR "evaluation" engineer agent 2026` | OpenAI Agent Post-Training Frontier Evals, Nous Research, White Circle, Intrinsic-Safety/Variance, Sable, Decagon, Harvey (7) |
| 6 | `"agent harness" OR "agent runtime" software engineer job 2026 startup careers` | Cohere PM Agent Harness, Viktor re-confirm |
| 7 | `Microsoft OR Meta OR Google "agent platform" OR "agent runtime" engineer job careers` | Decagon, Netskope (via syndication hit) |
| 8 | `Netskope "Platform Engineer" "Agent Runtime" careers job` | Netskope official gh_jid |
| 9 | `Anthropic "Agent Runtime" staff engineer job` | Anthropic Agent Runtime Platform family (then enumerated on Greenhouse) |
| 10 | `Glean "Software Engineer, Agents Runtime" jobs` | Glean (then enumerated `gleanwork` Greenhouse board) |

**Weak queries (low/no job yield — avoid or rephrase):** `site:boards.greenhouse.io "agent" "eval" engineer`, `site:jobs.lever.co "agent runtime" ...`, `"agent memory" ... 2026`, `"LLM routing" ...`, `"observability" LLM agent engineer ...`, `Microsoft/Meta/Google ...` (mixed) — these returned dictionary/wiki noise; the SearXNG Bing backend degrades on `site:` for greenhouse/lever and on rare-phrase OR queries.

### Phase B — board enumeration (the real multiplier; do this for EVERY new company)

- **Ashby:** `https://api.ashbyhq.com/posting-api/job-board/<org>` (add `?includeCompensation=true`) → full job list JSON. Probed: `sierra`, `profound`, `callosum`, `viktor`, `matter-intelligence`, `datasnipper`, `ninjatech.ai`, `taktile`, `cohere`, `langchain`, `openai`. (`anthropic`, `glean` are NOT on Ashby.)
- **Greenhouse:** `https://boards-api.greenhouse.io/v1/boards/<slug>/jobs` and `/jobs/<id>?content=true`. Probed: `anthropic` ✅, `gleanwork` ✅ (NOT `glean` — 404), `netskope` ✅.
- **Lever:** `https://api.lever.co/v0/postings/<org>?mode=json`. Probed: `apolloresearch` ✅; METR's board found by scraping `https://metr.org/careers` → `jobs.lever.co/metr/*` (Lever API not needed).
- **Careers-page scrape as slug oracle:** `curl https://metr.org/careers | grep jobs.lever.co` — fastest way to find an org's real board when the slug is unknown.

Enumeration added 25+ openings that plain search never returned (Callosum Evals/Benchmarking, NinjaTech Core Runtime, Anthropic TLM + Managed Agents, Glean ×3, OpenAI ×5, LangChain ×2, Cohere ×3).

### Phase C — verification
- All Ashby/Lever postings carry JSON-LD `JobPosting` (title, location, datePosted, full description) → parsed mechanically, no guessing.
- Greenhouse HTML pages render fine but have **no JSON-LD** → verified the page (HTTP 200) then took description text from `boards-api.greenhouse.io/.../jobs/<id>?content=true`.
- Look-alike slug caught: **`intrinsic-safety` (Ashby) = "Variance"** — the posting body says "At Variance, we are teaching machines…". Recorded as `org: "Variance (Ashby org slug: intrinsic-safety)"`. Prior-unit warning about `cais` reinforced: always read the posting body for employer identity.

---

## 2. Ranked shortlist (fit 5 only, subject-matter = the field itself)

1. **Callosum — Agent Runtime & Systems, MTS** (London) — runtime from first principles: durable execution, checkpointing & replay, distributed scheduling for weeks-long agents. `jobs.ashbyhq.com/callosum/c342204a-…`
2. **Callosum — Research Engineer, Evals, MTS** (London) — agentic eval science + eval/observability infrastructure. `…/07abc888-…`
3. **Callosum — Research Engineer, Benchmarking, MTS** (London) — reproducible contamination-controlled benchmark harness for agent topologies. `…/71c6dcb8-…`
4. **Profound — MTS, Rust Agent Runtime** (NYC) — workflow engine primitives, replay, idempotency, durable state in Rust. `…/profound/4c29c22e-…`
5. **Sierra — Software Engineer, Agent Runtime** (SF) — Agent SDK orchestration engine + evaluation systems. `…/sierra/b3829801-…`
6. **Anthropic — Staff+ SWE, Claude Managed Agents** (SF/NYC) — hosted agent runtime: sessions, environments, tools, memory, permissions; sandboxed execution + state management. `job-boards.greenhouse.io/anthropic/jobs/5395767008`
7. **Anthropic — Staff Research Engineer, Multi-Agent Scaling** (SF/NYC/Seattle) — platform + evaluations for large agent teams. `…/5442680008`
8. **Anthropic — Tech Lead Manager, Agent Runtime Platform** (SF/NYC) — the compute/runtime platform behind Anthropic's internal agents. `…/5316593008`
9. **OpenAI — Software Engineer, Codex Core Agents** (SF) — sandboxed execution, orchestration, **stateful workflows, state & memory systems**. `…/openai/7ade7a12-…`
10. **OpenAI — Software Engineer, Agent Infrastructure** (SF/NYC/London) — the production platform all OpenAI agents run on. `…/c1316397-…`
11. **OpenAI — RE/RS, Personal AGI, Memory** (SF) — memory architecture, long-horizon tasks for training & evals. `…/29074a51-…`
12. **OpenAI — Agent Post-Training, Frontier Evals and Environments Research** (SF) — RL environments + eval methodology (SWE-bench/GDPval lineage). `…/9d72171e-…`
13. **OpenAI — Research Engineer, Frontier Evals & Environments** (SF) — second distinct posting, same family. `…/bba18df5-…`
14. **Glean — Software Engineer, Agentic Runtime** (Mountain View) — multi-turn orchestration, tool calling, **model routing, memory/state**, streaming. `job-boards.greenhouse.io/gleanwork/jobs/4742953005`
15. **Glean — Software Engineer, Evals** (Bangalore) — large-scale eval pipelines + agent observability. `…/4712438005`
16. **METR — MTS, Evaluation Execution** (Berkeley) — **cap-exempt (nonprofit)**; runs evals on agent scaffolds, Time Horizon 2.0. `jobs.lever.co/metr/93baec4d-…`
17. **Apollo Research — Research Scientist/Engineer (Evaluations)** (London & SF) — **cap-exempt (nonprofit)**; Inspect-based eval pipelines for frontier models. `jobs.lever.co/apolloresearch/4a65c6e1-…`
18. **Matter Intelligence — Agent Infrastructure (IC)** (SF) — runtime + durable execution + memory + model routing + evals. `…/matter-intelligence/433bb3f3-…`
19. **NinjaTech AI — Agent Harness Engineer, Core Runtime** (Sydney) — run loop, orchestrator, stuck-agent monitor, provider abstraction. `…/5fe34e1e-…`
20. **Decagon — Senior SWE, Agent Platform** (SF) — execution frameworks, multi-model orchestration, routing control plane, offline evals. `…/decagon/75f544ae-…`
21. **Viktor — Agent Harness Engineer** (Warsaw/Munich/EU remote) — agent runtime loop, memory, evals/regression catching. `…/viktor/d5d2d0fa-…`
22. **Unusual Ventures / Helios — Staff/SSE, Agent Engineering** (NYC) — execution state, memory layer, model routing, evaluation, recovery. `jobs.lever.co/unusual/9dd5d490-…`
23. **LangChain — Sr Backend SWE, AI Observability & Evals Platform** (SF + Boston, 2 postings) — LangSmith evals/observability core services. `…/langchain/f07c1416-…`, `…/b23ea9af-…`
24. **Profound/Sierra/others** — see `JOBS.jsonl` for the 24 fit-5 and 20 fit-4 records.

---

## 3. Cap-exempt split (mandatory field)

| cap_exempt_likely | count | who |
|---|---|---|
| **yes** | **3** | **METR** ×2 (nonprofit research org, Berkeley) · **Apollo Research** ×1 (nonprofit AI-safety research, London/SF) |
| **no** | 46 | all startups, AI labs (Anthropic PBC, OpenAI, Cohere, Glean, LangChain…), big tech-adjacent (Binance, Netskope), vendors |
| unclear | 0 | — |

No university or governmental-research openings with agent-runtime/evals subject matter surfaced in this sweep; the two clear cap-exempt employers found are nonprofit research orgs. Cap-exempt share of records: **3/49 ≈ 6%**. Highest-value cap-exempt hits: **METR Evaluation Execution ($328K–$578K, Berkeley)** and **METR Embedded Assessments ($402K–$687K)** — both directly assess agent scaffolds/monitoring.

---

## 4. Failed / unreachable URLs (coverage gaps — with status)

| URL | HTTP status | Note |
|---|---|---|
| `https://www.netskope.com/company/careers/open-positions/?gh_jid=8078767` | **403** (Cloudflare) | Official careers URL bot-blocked. |
| `https://job-boards.greenhouse.io/netskope/jobs/8078767` | **403** | Cloudflare-blocked. |
| *resolved via* `https://boards-api.greenhouse.io/v1/boards/netskope/jobs/8078767?content=true` | 200 | Full official content retrieved → Netskope record stands, marked `http_status 403` + note. |
| `https://boards-api.greenhouse.io/v1/boards/glean/jobs` | **404** | wrong slug; correct slug is **`gleanwork`** (200). |
| `https://api.ashbyhq.com/posting-api/job-board/anthropic` | (no JSON) | Anthropic is on **Greenhouse**, not Ashby. |
| `https://api.ashbyhq.com/posting-api/job-board/glean` | (no JSON) | Glean is on Greenhouse (`gleanwork`). |
| `https://api.ashbyhq.com/posting-api/job-board/weightsandbiases` | no JSON | not on Ashby (not chased further). |
| `https://boards-api.greenhouse.io/v1/boards/metr/jobs` (+2 alias slugs) | **404** | METR is on **Lever** (`jobs.lever.co/metr`). |
| Trase Systems "Staff SSE (Platform Architecture & Execution Model)" | **not fetched from an original board** | only found via aggregators (hiringcafe/career.io/jobgether) — **NOT recorded in JOBS.jsonl** (rule: no posting-page fetch, no record). Coverage gap. |
| Anthropic "Staff Engineer – Agent Runtime & Productivity" (seen on jobleads.com) | **not on the live Greenhouse board** | The current Anthropic board carries *Tech Lead Manager, Agent Runtime Platform* but no "Staff Engineer – Agent Runtime & Productivity" title → likely closed/renamed; **not recorded**. Coverage gap. |
| Glean "Software Engineer, Agents Runtime" (syndicated at topaisjobs/thatstartupjob) | live as **`Software Engineer, Agentic Runtime`** on `gleanwork` | recorded under the official title. |

No other recorded URL failed: **48 of 49 records = direct HTTP 200 on the posting page; 1 = 403 with official-API fallback; remaining gaps documented above (never guessed).**

---

## 5. Screened OUT (fetched but not recorded — with reason)

- **Unit (fintech) — Principal Engineer** (`jobs.ashbyhq.com/unit/f2ad8b21-…`, 200): "durable execution frameworks" is one nice-to-have line; subject matter is a fintech platform. fit 2 → excluded.
- **Cohere — MTS, Agentic Environments** (`…/8878b0d0-…`, 200): body is LLM tuning/production ML, not runtime/evals → excluded.
- **OpenAI Training/Runtime Foundations, Model Runtime, AI-accelerator Runtime, Inference Runtime** (board titles): training/inference runtimes, not agent runtimes → not chased.
- Sierra's ~60 "Software Engineer, Agent / Strategist, Agent Development" postings: customer-implementation roles (build agents *with* the platform), not the subject matter → excluded except **Agent Runtime** and **Applied Research**.
- Anthropic "Cyber Evaluations Engineer", "Safeguards Enforcement Analyst", "TPM Safeguards": cyber/GRC or TPM → out of narrow scope.

## 6. Coverage statement

- **Scope:** global (no geographic restriction). Locations found: US (SF, NYC, Seattle, Boston, Mountain View, Berkeley, LA), UK (London), Germany (Berlin), France (Paris), Netherlands (Amsterdam), Poland (Warsaw), Israel (Tel Aviv), Canada (Toronto), Australia (Sydney), India (Bangalore/Bengaluru), Taiwan (Taipei), Hong Kong, Philippines (Taguig), South Korea/Europe-wide (Cohere/Sierra boards).
- **Platform coverage:** Ashby (11 boards enumerated), Greenhouse (3 boards enumerated + content API), Lever (2 boards + METR careers scrape). Time budget: ~25 min of the 30 allotted; ~46 tool calls of 90.
- **Not covered (next unit's leads):** aggregators-only postings (Trase Systems), Meta/Microsoft/Google first-party ATS (their career sites were not enumerated), university/national-lab boards beyond other units' scope, and Ashby boards not yet probed (`decagon`, `harvey`, `whitecircle`, `nousresearch`, `sable`, `meraki-labs`, `intrinsic-safety` full enumerations — only keyword hits were taken).
- **Data integrity:** every record in `JOBS.jsonl` corresponds to HTML stored under `raw/` fetched during this session; `date observed` = 2026-10-15 on all records.
