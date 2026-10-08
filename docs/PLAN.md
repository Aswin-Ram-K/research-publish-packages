# Research Extractor — a continuous repo-to-publishable-docket pipeline
### Build model: main session orchestrates only. All actual work is delegated.

**Target (first real run):** `/home/zer0null/Duval` (Consonance, AGPL-3.0, `main` @ `6deaed0`, 436 tracked files, 180 under `docs/`, 36 in `docs/research/`, an existing hand-made monograph + external-evidence review this tool formalizes).
**Home:** `/home/zer0null/reserach extarctor` — standalone app, own venv, web dashboard, dockets on disk.
**Model under test:** Occamy-1.0, live on GX10 at `http://192.168.2.168:8012/v1` (SGLang, 262144 ctx) — verified working, including real tool calls.

---

## 0. The execution contract (your directive, made mechanical)

**Main session does only three things:** compose unit prompts, launch/collect subagents, talk to you. Nothing else.

| Main session MAY | Main session MUST NOT |
|---|---|
| Compose a unit card and pass it as a subagent prompt | Write, edit or create any file on disk (unit cards included — subagents persist their own) |
| Launch subagents (`subagent`, `subagent_fork`), ≤3 concurrent, watching for write-path clashes | Run builds, tests, installs, git, or the pipeline itself |
| Read `orchestration/handoffs/*.json`, `orchestration/STATUS.md`, and ≤20-line command summaries | Read source code, logs, or debug a failure |
| Relay status, verdicts and evidence lines to you; escalate decisions | "Fix" a failed unit — its work is re-delegated to a **fresh** unit with the failure evidence |
| Make the phase-gate call (advance / re-delegate) from a verifier's verdict | Approve its own work — every claim is verified by a **different** subagent |

**Consequence to expect:** each unit returns a bounded summary, so this chat stays small and readable while the real work happens in subagent contexts. The spec of record is a file on disk (`docs/PLAN.md`), written by unit 0 — not by me.

**Routing decision (stated, one word to flip):** build units run on the session's existing route (`keyring/deepseek-v4.1-flash`) because **your own Occamy verdict records it as weak at coding** — *"weak in coding, overengineers, picks wrong solutions to simple problems"*. Occamy is the app's brain, not the app's author. Pinning build units to Occamy would require adding an Occamy provider to the live DSH profile (currently only `keyring` at `127.0.0.1:8790` — Occamy `:8012` is not registered) plus a restart. Say **"register Occamy"** and Phase 0 starts with that as its first unit; otherwise no live DSH change at all.

---

## 1. Goal and success criteria

A standalone local app that, given a repo, **continuously** extracts every research-worthy item, verifies each against the real world via web research, groups the results into **lanes** (one lane = one publishable item), and materializes each lane as a **docket folder** containing the *copied* source material, evidence, prior art, draft and publication checklist — with a **web dashboard** showing the reasoning and findings behind each item.

**Done means, on `/home/zer0null/Duval`:**

1. `resextract doctor` green on Occamy, SearXNG, crawl bridge, graphify — or naming exactly what is missing.
2. `resextract run --target duval` completes unattended; **zero writes inside `/home/zer0null/Duval`** (proved by verifier: `git status` + mtime sweep, before and after).
3. `dockets/duval/` has **≥3 dockets at `status: ready`**, ≥2 distinct publication types chosen by the classifier.
4. Every claim resolves to (a) a `file:line` or graph-node provenance in the repo and (b) a copied artifact in `material/` with matching sha256 — no orphan claims.
5. Every external reference carries URL + page date + verbatim excerpt + verdict, and the search-health table records failures truthfully.
6. `resextract refresh` after a new commit marks the right dockets stale and appends specific rework to `UPDATE_BACKLOG.md`; cited URLs are re-fetched and content-diffed.
7. Dashboard on `http://127.0.0.1:8901` shows run timeline, per-candidate Occamy reasoning (incl. `reasoning_content` and tool calls), findings, docket board with staleness, and refresh suggestions.
8. `pytest` green offline (fixtures only, no network, no GX10).
9. **Process criterion:** the main session performed only delegation and reporting — verifiable from `orchestration/` (unit cards, handoffs, verifier verdicts).

**v1 non-goals:** submitting anywhere, cloud models in the app, any write into a target repo, multi-user access.

---

## 2. Verified environment (all checked this session)

| Fact | Evidence |
|---|---|
| Occamy live; **tool calls work** | `POST /v1/chat/completions` (`:8012`) returned `finish_reason: tool_calls` with valid JSON args; `/v1/models` → `occamy-1.0`, `max_model_len 262144` |
| ⭐ **Thinking can be turned off** | `chat_template_kwargs.enable_thinking=false` → **0.25 s / 2 tokens**; same question with thinking on → **10.5 s / 397 reasoning tokens**. A ~40× lever — the pipeline must switch it per stage |
| Repo-KG engine already exists, never promoted | `graphify` (PyPI `graphifyy`, **0.9.80** available; 0.9.65 working in `~/Desktop/deepseek agent harness testing/scratch-graphify`): tree-sitter AST free/local, Leiden/Louvain, `query/explain/path/affected/god-nodes`, docs/PDF/docx semantic pass, incremental `update`, `watch`, git hooks, `add <url>`, `save-result`/`reflect`, `export wiki|callflow-html|obsidian|graphml`. Its `openai` backend honors `OPENAI_BASE_URL` → points at Occamy |
| Prior art in your sandbox | `scratch-graphify/` — working venv, a real 30 MB graph (26,555 nodes / 39,331 edges / 1,511 communities), `SPEC-per-repo.md`, `@local/dsh-plugin-graphify` (9/9 tests, never promoted), and your own bounded-unit `ORCHESTRATION-CONTRACT.md` — the protocol §9 adopts |
| Web legs live | SearXNG `http://127.0.0.1:8080` (JSON API returns arXiv results); bridge `http://127.0.0.1:8891` (`POST /crawl {url,maxLength}`, `POST /scrape {url,mode,maxLength}`, `/health` ok) |
| Docling bridge `:8893` stopped (cold start ~30 s) | curl refused → optional high-fidelity PDF path, not a dependency |
| No LaTeX/pandoc/tectonic | `which pdflatex pandoc tectonic` empty → paper dockets emit `.tex` + markdown; PDF only if a renderer exists, else the missing toolchain is recorded in `CHECKLIST.md` |
| Ports | `8901`/`8902` free; occupied: 3080, 8080, 8790, 8891 |
| Manual pipeline to automate | `Duval/.lane-j-scratch/` — `web/` raw HTML, `webcache/`, `research/lane-j-evidence.md`, `staging/`, and `consonance-external-evidence-2026-10-07.md.txt` (1907 lines: URL + page date + verbatim excerpt + CONFIRMS/EXTENDS/CONTRADICTS, plus a "Tooling reality" honesty table) |
| Failure to design around | That file records `local_web_search` "worked for the first ~6 queries, then returned **no results**"; arXiv API 429; `web_fetch` does not follow cross-origin redirects (needs scrape) |
| Build subagents currently route only to `keyring` | `~/.dsh/profiles/web/cordis.yml` shows `keyring` @ `127.0.0.1:8790/v1`, default model `deepseek-v4.1-flash`; no Occamy/`:8012`, no `sglang` provider |

---

## 3. Architecture

```
target repo (READ-ONLY) ──► KG layer (graphify: AST + docs/PDF/docx semantic pass on Occamy)
                                   │
                     ┌─────────────┴──────────────┐
                     ▼                            ▼
            MINER (Occamy agent loop)      WEB RESEARCH (SearXNG + crawl/scrape, cached)
            candidates → claims                   │ prior art, quotes, hashes
                     └─────────────┬──────────────┘
                                   ▼
              ASSESS (novelty + real-world value) → LANES (cluster) → CLASSIFY (type) → SPLIT
                                   ▼
              DOCKET MATERIALIZER (copies material in, drafts the one item, checklists)
                                   ▼
              CONTINUITY ENGINE (watch/refresh, staleness, rework backlog)
                                   ▼
              DASHBOARD (FastAPI + SSE, zero-framework static UI, 127.0.0.1:8901)
```

**Runtime:** Python 3.14 venv in the workspace — `graphifyy[openai,pdf,office,leiden,watch]`, `fastapi`, `uvicorn`, `sse-starlette`, `httpx`, `jinja2`, `pydantic`, `pytest`. No Node dependency.

### 3.1 Layout

```
/home/zer0null/reserach extarctor/
├── pyproject.toml                 # package resextract; console script `resextract`
├── .venv/
├── config/resextract.toml         # endpoints, model routes, budgets, TTLs, copy caps, excludes
├── config/targets.toml            # {slug, path, include/exclude globs}
├── src/resextract/
│   ├── cli.py  config.py  store.py  journal.py  doctor.py
│   ├── llm/occamy.py              # thinking flag per call, tool calls, retries, budgets, metering
│   ├── kg/graphify.py             # subprocess wrapper + typed results; never throws untyped
│   ├── kg/queries.py              # canned research-directed graph queries
│   ├── web/search.py              # SearXNG: pacing, retry, engine rotation, negative cache
│   ├── web/fetch.py               # crawl → scrape fallback, content-hash cache, HTML→text
│   ├── mine/{candidates,claims,provenance}.py
│   ├── assess/{novelty,value,evidence}.py
│   ├── lanes/{build,classify,split}.py
│   ├── docket/{materialize,copy,draft,checklist,manifest}.py
│   ├── refresh/{review,staleness,backlog}.py
│   └── web/app.py + static/       # dashboard
├── templates/                     # Jinja2: paper, report, blog, benchmark_card, memo, checklists
├── tests/ + tests/fixtures/fixture-repo/
├── dockets/<repo-slug>/<lane-slug>/        # OUTPUT
├── state/{state.sqlite, journal/, webcache/, logs/}
├── orchestration/{units/,handoffs/,STATUS.md,VERDICTS.md}   # the process record
└── docs/{PLAN.md,DESIGN.md,OPERATIONS.md,DOCKET_FORMAT.md}
```

Package/CLI `resextract`, product "Research Extractor" — a one-line rename if you'd rather a Norse name (Huginn/Muninn/Bragi).

### 3.2 CLI

```
resextract doctor [--json]                     # probe Occamy, SearXNG, bridge, graphify, renderers, ports
resextract target add <path> [--slug S] [--include G ...] [--exclude G ...]
resextract run --target S [--max-lanes N] [--budget-tokens N] [--budget-fetches N] [--dry-run]
resextract mine|assess|lanes|materialize --target S [--run-id ID]   # resumable stage entry points
resextract refresh --target S [--docket SLUG|--all] [--prior-art-ttl-days N] [--check-links]
resextract status --target S [--json]
resextract open --target S [--docket SLUG]     # prints the folder path; never writes into the repo
resextract export --target S [--docket SLUG] [--format md|tex|pdf|docx]   # pdf/docx only if renderer present
resextract serve [--host 127.0.0.1] [--port 8901] [--token auto]
resextract watch --target S [--interval 300]
```

Exit codes: `0` ok · `1` completed with recorded degradations · `2` hard dependency down · `3` budget exhausted with work remaining. Every command idempotent and resumable by content hash.

### 3.3 Stage-to-model policy (the throughput contract)

| Stage | Thinking | Max tokens | Notes |
|---|---|---|---|
| Classification, JSON shaping, slugging, query generation | **off** | 256 | 0.25 s class; temp 0 |
| Candidate mining (graph + file reads, tool loop) | **on**, capped | 8k | max 12 steps |
| Novelty assessment / contradiction reasoning | **on**, capped | 6k | the only place long reasoning is bought |
| Drafting (report/paper/blog/card/memo) | **on** | 16k | template-bound; cites only verified evidence ids |
| graphify docs/PDF semantic pass + community labelling | off | — | `--max-concurrency 1` (single GPU) |

All model output parsed through pydantic schemas; unparseable output retried once with the schema echoed, then recorded as a degradation. Every call metered (`tokens`, `reasoning_tokens`, `wall_ms`) into the journal and a per-run budget ledger.

### 3.4 SQLite schema (`state/state.sqlite`)

`runs(id, target, started_at, finished_at, status, budget, tokens_used, notes)` ·
`targets(slug, path, head_sha, graph_path, graph_hash, last_seen_at, exclude_json)` ·
`candidates(id, run_id, kind, title, summary, provenance_json, graph_nodes_json, score, state)` ·
`claims(id, candidate_id, text, kind, provenance_json, verification_state, confidence)` ·
`evidence(id, claim_id, source_kind[local|web], source_ref, sha256, quote, context, retrieved_at, copy_path)` ·
`verdicts(id, claim_id, verdict[CONFIRMS|EXTENDS|CONTRADICTS|UNVERIFIED], rationale, evidence_ids_json, checked_at)` ·
`lanes(id, target, slug, title, thesis, audience, type, parent_lane_id, maturity, status[draft|ready|stale|needs_rework|superseded])` ·
`dockets(id, lane_id, dir, manifest_json, source_head, graph_hash, freshness, verified_at, last_refresh_at)` ·
`web_sources(url, sha256, title, page_date, fetched_at, http_status, extracted_text_path, failure_reason)` ·
`search_health(ts, engine, query, result_count, ok, error)` ·
`rework(id, docket_id, reason, required_work, opened_at, closed_at)`.

Append-only **journal** (`state/journal/<run-id>.jsonl`): every LLM request/response summary, tool call with args + result digest, fetch, copy and verdict change — the substrate for the dashboard's reasoning view.

### 3.5 Docket contract — **one lane = one publishable item**

```
dockets/<repo-slug>/<lane-slug>/
├── README.md          entry point: what this is, status, index, one-paragraph pitch
├── ITEM.md            THE publishable artifact (type-specific; + ITEM.tex for paper)
├── MANIFEST.json      machine-readable (schema below)
├── CLAIMS.md          claim sheet → provenance → verification state
├── EVIDENCE.md        verbatim code/doc excerpts, path + line + sha256
├── PRIOR_ART.md       URL + page date + verbatim excerpt + verdict, + search-health table
├── REFERENCES.md/.bib citations from actually-fetched sources
├── RESULTS.md         measured numbers + the exact command that produced each
├── METHOD.md          rebuilt from the graph, not copied prose
├── material/code|docs|figures|data/   ← **COPIED** from the repo (never link-only)
├── web/               ← COPIED external pages + extracted text + sha256
├── repro/             commands, env pins, run script
├── CHECKLIST.md       type-specific publication checklist incl. a licence gate
├── OPEN_QUESTIONS.md  what remains unproven
├── UPDATE_BACKLOG.md  the specific work that would bring this item up to date
└── HISTORY.md         append-only runs, refreshes, verdict changes
```

`MANIFEST.json` — `{schema: "resextract/docket/1", lane{slug,type,thesis,audience}, target{slug,head_sha,graph_hash}, status, freshness{verified_at,prior_art_checked_at,age_days,state}, claims[{id,text,provenance[],verdict,evidence[]}], material[{src,dest,sha256,bytes,excerpt}], web_sources[{url,sha256,page_date,http_status}], open_questions, rework_open, generated_by{app,version,model}}` — validated on write and re-validated by `resextract status`.

**Copy rule (your explicit requirement):** every file, figure, data file or doc section a claim depends on is **byte-copied** into `material/` with sha256 recorded; excerpts are marked by line span and the full file comes across so a reader can verify context without the repo. Caps **2 MiB/file, 200 MiB/docket**; over-cap items become `material/LINKS.md` stubs (absolute path + sha256 + copy command). Two hard safety rules: **never follow symlinks out of the repo**, **never write inside the target repo** (graphify `--out` + `.graphifyignore` keep `graphify-out/` outside it too).

### 3.6 Publication-type classifier and split rule

Types: `paper | report | blog | benchmark_card | memo`. Deterministic guards — no `paper` without ≥1 `CONFIRMS`/`EXTENDS` anchor **and** ≥1 measured result; no `benchmark_card` without recomputable numbers; anything unverifiable defaults to `memo`, never `paper`. **Split rule:** ≥2 independent primary claims with different audiences or maturity → sibling dockets sharing the parent lane id (your "separate it as 2 items — each folder is one separate publishable item"). Every classification records its rationale in `MANIFEST.json` and `HISTORY.md`.

---

## 4. Pipeline stages

1. **Ingest / KG** — `target add`, then graphify `extract --code-only` (free AST) → docs/semantic pass on Occamy (`OPENAI_BASE_URL=http://192.168.2.168:8012/v1`, `OPENAI_MODEL=occamy-1.0`, dummy `OPENAI_API_KEY`, `--max-concurrency 1`, `--no-viz` above 5k nodes) → `label`. Duval excludes: `.worktrees/`, `node_modules/`, `.git/`; includes `docs/`, `src/`, `tests/`, `evals/`, `tools/`, `source-material/`, `.lane-j-scratch/*.md` (where the monograph and evidence review live).
2. **Mining** — canned graph query battery (novel primitives, invariants, measured deltas, negative results, reversed decisions, unreproduced claims) + a bounded Occamy tool loop (`graph_query`/`graph_explain`/`graph_path`/file read/grep). Notebooks (`.ipynb`, unsupported by graphify) are normalized to markdown into `state/notebooks/` and fed to the docs pass.
3. **Claims** — atomic, falsifiable, each with provenance and a "what evidence would settle this" field.
4. **Web research** — query generation → SearXNG with pacing + jitter, engine rotation, backoff, negative cache TTL, index-page fallback; fetch via crawl bridge, scrape on failure, content-hash cached; capture page date, title, verbatim excerpt. Every attempt lands in `search_health` and `PRIOR_ART.md` prints that table **including failures**.
5. **Assess** — per claim: `CONFIRMS`/`EXTENDS`/`CONTRADICTS`/`UNVERIFIED` + real-world value axes (who is affected, what it unblocks, measured delta, reproducibility, cost, licensing). Unverifiable claims are kept and labelled.
6. **Lanes** — cluster (graph communities + dependency-free lexical similarity) with Occamy naming; score publishability; classify + split.
7. **Materialize** — create folder, copy material, render EVIDENCE/RESULTS/METHOD from stored data, draft the single item from its template **constrained to verified evidence ids**; a post-check fails the docket if the draft cites anything outside the ledger.
8. **Continuity** — §5. 9. **Dashboard** — §6.

---

## 5. Continuity, review, staleness prevention (your answer #5)

- **Triggers:** `watch` (default 5 min: git HEAD + mtime sweep), explicit `refresh`, and a **staged** `resextract-refresh.timer` (6-hourly) created but **not enabled** without your approval.
- **On repo change:** `graphify update` → changed files → graph nodes → re-mine only affected candidates (`affected` traversal) → re-assess where claims moved → dockets with moved provenance become `needs_rework` or `stale` with a specific reason.
- **Periodic lookover:** each refresh (a) re-fetches every cited URL and content-diffs it — moved/gone/edited becomes a recorded finding; (b) re-runs novelty probes past TTL (`prior_art_ttl_days = 30`); (c) searches for work published since the last check and appends genuinely new prior art under the same URL+date+quote standard.
- **Work suggestions:** each docket gets `UPDATE_BACKLOG.md` entries — *"claim X is now contradicted by Y (fetched date, quote); to bring this up to date, run experiment Z / re-measure M / add ablation A"* — generated from the diff and marked `model-suggested` so it is never confused with measured fact; aggregated into `dockets/<repo>/WORK_SUGGESTIONS.md`.
- **Freshness vocabulary** everywhere: `current` · `stale (age N d)` · `needs_rework (source moved)` · `superseded (by lane L)`. Nothing silently overwritten: `HISTORY.md` + `MANIFEST.json` hold the timeline; the prior `ITEM.md` is kept as `ITEM.md.r<N>`.

---

## 6. Dashboard (`resextract serve`, `127.0.0.1:8901`, token-gated)

Zero-framework static HTML/CSS/JS (your KeyRing dashboard idiom), vendored assets, no CDN, SSE. Read-only by default; control buttons only with the one-time token; refuses non-loopback binds without explicit `--host`.

1. **Runs** — timeline, stage progress, tokens/wall/fetches vs budget, degradations, resume point.
2. **Reasoning** — per-candidate Occamy trace: prompt digest, `reasoning_content`, each tool call with args and result digest, resulting JSON. Filtered from the journal, never invented.
3. **Findings** — candidates → claims → verdicts with provenance links and evidence excerpts side by side.
4. **Lanes / Dockets** — board with type, status, freshness age, claim count, open questions, material size; each card opens the folder index.
5. **Web research** — sources, verdicts, search-health history (intermittent SearXNG visible, not hidden).
6. **Refresh** — what changed, rework backlog, "re-verify now".

---

## 7. Failure modes

| Failure | Handling |
|---|---|
| GX10/Occamy down | `doctor` fails loudly; `run` exits 2 before starting; in-flight runs checkpoint and resume. Never fabricate output |
| SearXNG intermittency (your recorded failure) | pacing + jitter, engine rotation, backoff, negative cache, index fallback; every failure in `search_health`; dockets state plainly when evidence is thin |
| Occamy reasoning loops / tool overfitting | step caps, strict schemas, thinking off for mechanical stages, validate-then-retry-once, server's tested `qwen3_coder` parser (already active) |
| Unparseable model JSON | one schema-echoed retry, then a recorded degradation with the raw text journaled |
| Huge repo/graph | excludes, `--no-viz` >5k nodes, per-stage budgets, `--max-lanes`; Duval is small (436 files) |
| Long-context prefill cost (~1.7k tok/s at 261k ctx measured) | 32k chunk budget, thinking off where possible, content-hash caching |
| Missing LaTeX/pandoc | emit `.tex` + markdown, record the missing renderer in `CHECKLIST.md`, `export --format pdf` fails with an actionable message — no silent skip |
| PDF/docx in material (`source-material/*.docx`) | `graphifyy[pdf,office]`; Docling `:8893` as optional higher-fidelity path |
| Symlinks / repo escape | realpath containment check; refuses copies outside the target root |
| You change your mind mid-run | every stage a resumable command; `--dry-run` writes no dockets |

**Security/privacy:** loopback by default, no telemetry, no real credentials (dummy `OPENAI_API_KEY` for the local router), secrets never written into dockets, secret-shaped paths refused from `material/`, AGPL-3.0 awareness with a licence gate in `CHECKLIST.md` and recorded source licences.

---

## 8. Testing and acceptance

- **Unit (offline):** graphify wrapper parsing on captured output; Occamy client thinking-flag/retry/budget/metering; search pacing + health recording; fetch cache; classifier + split guards; manifest schema; copy engine (caps, symlink refusal, sha256, `LINKS.md`); staleness state machine; draft-citation post-check.
- **Fixtures e2e:** `tests/fixtures/fixture-repo/` (small TS project: one novel primitive, one measured JSONL, one figure, one doc, one notebook) → full pipeline offline with recorded model/search fixtures → assertions on the docket tree.
- **Red→green rule:** each guard test must fail when its fix is reverted; the reverted run is recorded in the test docstring.
- **Phase-1 integration gate (the one real unknown):** does `graphify extract --backend openai` against Occamy actually produce the semantic layer and community labels? **Fallback: a ~150-line in-repo semantic pass** over graphify's code-only graph, reusing its chunker. Tested before anything is built on it.
- **Live acceptance:** `doctor`, then `run --target duval --max-lanes 3 --budget-fetches 60`, then the full run; plus the two `git status`/mtime sweeps proving the repo was never written to.

---

## 9. Orchestration model (how the work actually gets done)

Adopts your own `scratch-graphify/ORCHESTRATION-CONTRACT.md`: bounded units, forced report-back, fresh context, partial success is a result.

**Unit card** (composed by main as the subagent prompt; persisted by the subagent to `orchestration/units/<UNIT>.md`):
`OBJECTIVE` (one sentence) · `INPUT STATE` (what exists, which handoffs to read, which docs) · `HARD BOUND` (max attempts / stop condition, budget) · `WRITE PATHS` (for clash detection) · `VERDICT FORMAT` · `DO NOT TOUCH` list.

**Every unit ends by writing `orchestration/handoffs/<UNIT>.json`** —
`{unit, status: done|failed|partial, artifacts[], evidence{command: output_digest, counts, versions}, blocker, next_unit_hint, write_paths[], tokens_used}` — and returns a **≤15-line summary** to main: status, artifacts, the evidence lines that prove the claim, blocker, next hint. That cap is what keeps this session clean.

**Delegation mechanics:**
- `subagent` — fresh context, self-contained prompt, default background. Used for all build units.
- `subagent_fork` — only where a unit needs this session's accumulated decisions (e.g. writing the agreed plan to disk, or a consistency review against the plan).
- `workflow` — for genuine fan-out later: parallel per-docket drafting across many lanes, or a 3-angle adversarial review. Not used in Phase 0-1.
- **Concurrency ≤3**, and only when write paths are disjoint (declared in the unit card). Main tracks agent ids, collects results, `interrupt_agent` on drift.
- **Fresh context per unit; no unit is ever extended.** A failed unit is superseded by a new unit carrying the failure evidence. Partial is a valid outcome.
- **Verification independence:** each phase gets a separate verifier unit (never the author) that re-runs the evidence commands and checks the plan's clause, plus a red→green check on at least one guard. `orchestration/VERDICTS.md` records the verdict; main relays it to you and makes the gate call.
- **Main-session discipline:** main reads only handoff JSONs and ≤20-line summaries; it never opens source, never runs a command, never writes a file.
- Long-lived processes (the dashboard) are started as **managed background jobs by the owning unit**, which verifies the exact URL and reports it; main never starts servers.

---

## 10. Unit batches (each batch ends green and verified before the next)

| Batch | Units (write paths) | Gate |
|---|---|---|
| **0** | `U0.1` write plan to `docs/PLAN.md` + scaffold `pyproject.toml`, config, venv install (`graphifyy[openai,pdf,office,leiden,watch]`, fastapi, uvicorn, sse-starlette, pytest) · `U0.2` Occamy client + tests (`src/resextract/llm/`) · `U0.3` store + journal + `doctor` (`src/resextract/store.py`, `journal.py`, `doctor.py`) | V0 verifier: `resextract doctor --json` green on all four dependencies; client tests pass; thinking on/off both exercised with recorded timings. U0.2/U0.3 run concurrently (disjoint paths) |
| **1** | `U1.1` graphify wrapper + query battery (`src/resextract/kg/`) — **the integration gate, run alone** · `U1.2` notebook normalizer | V1: a real graph built from `/home/zer0null/Duval` (paths/hashes recorded), `query` returns real provenance, semantic pass + labels either proven or the fallback activated |
| **2** | `U2.1` miner · `U2.2` claims + provenance | V2: ≥20 candidates with reproducible provenance; every candidate traceable in the journal |
| **3** | `U3.1` SearXNG client + health · `U3.2` fetch/cache | V3: ≥1 real lane's `PRIOR_ART.md` meets the existing review's standard; search-health table honest about ≥1 induced failure |
| **4** | `U4.1` assessment · `U4.2` lanes + classifier + split | V4: ≥3 lanes, ≥2 types, split rule demonstrated on a real multi-claim lane, guards red→green |
| **5** | `U5.1` copy engine · `U5.2` manifest + templates + draft + export | V5: full docket tree for Duval, manifest valid, sha256 of every copied file matches, repo untouched |
| **6** | `U6.1` dashboard API + SSE · `U6.2` static UI | V6: six screens live on `127.0.0.1:8901` rendering batch-2/3 data; loopback-only enforced |
| **7** | `U7.1` watch/refresh/staleness · `U7.2` rework backlog + staged systemd units | V7: simulated commit marks exactly the right dockets stale with correct rework entries; unit files created but **not enabled** |
| **8** | `U8.1` docs (`DESIGN.md`, `OPERATIONS.md`, `DOCKET_FORMAT.md`, `AGENTS.md` visit-log entry) · `U8.2` full acceptance run · `U8.3` independent adversarial verifier | V8: §1 criteria 1-9 each backed by a command output |

Sequential batch boundary; concurrent units inside a batch only with disjoint write paths. Nothing is promoted outside this workspace: no writes into `~/Duval`, no systemd unit enabled, no DSH plugin mounted, no DSH restart — without your explicit approval.

---

## 11. Assumptions (correct any and I'll re-issue the plan)

1. Occamy-1.0 at `192.168.2.168:8012` is the only model the **app** calls; a knob for a second local route exists, default off.
2. Build subagents use the session's `keyring/deepseek-v4.1-flash` route — because your own verdict records Occamy as weak at coding, and because Occamy is not registered in DSH (no restart needed). "register Occamy" flips this.
3. Dockets live in this workspace (`dockets/<repo>/…`); target repos are strictly read-only.
4. "Continuous" = in-app `watch` plus a **staged** 6-hourly systemd user timer you enable when satisfied.
5. `ITEM.md` is the publishable artifact; PDF/LaTeX rendering is best-effort and honestly reported when a toolchain is missing.
6. `~/Duval` (Consonance) is the acceptance target; the tool is repo-agnostic from day one, so `~/Desktop/human memory AI`, `VALHALLA` or a GitHub clone are one `target add` away.
