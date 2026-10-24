# HOST-SCOUT-3 — read-only scout for paper-ready work across six host projects

Status: done
Mode: READ-ONLY. No writes outside this workspace, no builds, no servers, no model requests,
no git writes (no git command was run at all).
Bound: 40 tool calls / 20 minutes. Used 31 tool calls; finished inside the time bound.
Started 2026-10-23T23:01:58-05:00.

## Objective

Find work in the six named projects that is ALREADY paper-ready, or one small batch from
paper-ready — a complete experiment/analysis with real numbers and ideally a write-up, not an
idea. Per candidate: exact paths, what is established (numbers), what is missing, readiness,
venue fit, risk.

## Method

Cheap `ls`/`find` orientation per project, then selective reads of the documents that could
carry measurements: README/BENCHMARK, `docs/`, `.agents/notes/`, `benchmarks/*/README.md`,
research reports, session close-outs, dated sweep reports. Numbers below were read out of the
files, not inferred. Nothing was executed except two read-only `node -e` aggregations over
JSON data files that the project itself ships as data (no project code was run).

## Candidates

### 1. deepseek-harness — performance-budget corpus + incident post-mortem series (PARTIAL, one batch)

Paths:
- `/home/zer0null/deepseek-harness/benchmarks/session-corpus/README.md` (39 lines)
- `/home/zer0null/deepseek-harness/benchmarks/agent-continuation/README.md` (33 lines)
- `/home/zer0null/deepseek-harness/.agents/notes/implemented/testing/2026-09-28-session-corpus-performance.md` (80 lines)
- `/home/zer0null/deepseek-harness/docs/postmortem/0001…0004*.md` (4 post-mortems, 47–113 lines each)
- `/home/zer0null/deepseek-harness/docs/subsystems/` (60+ subsystem design docs)
- `/home/zer0null/deepseek-harness/.agents/notes/implemented/` — 293 English design notes
  (architecture 177, feature 40, process 34, testing 18, simplification 13, bug-fix 11)
- `/home/zer0null/deepseek-harness/BENCHMARK.md` is 3 lines and only points at the Python SDK guide —
  it is NOT a results document.

Already measured (real numbers, quoted from `…/2026-09-28-session-corpus-performance.md:54-66`):
- List 3,000 sessions: boot 2,317.8 / 2,204.5 ms; first 3,228.7 / 2,633.6 ms; repeat 2,636.4 / 2,235.1 ms
  (two runner models: AMD EPYC 7763 / EPYC 9V74)
- Content search 1,000 sessions: first 144,359 / 135,065 ms (index build); repeat 3,426.3 / 2,704 ms
- Fork: strata median 95.5 / 73.5 ms; p99 (rank 988, 7,229 events) 1,066.2 ms; longest 19,162.1 / 20,326.7 ms
- Peak RSS list/search/fork 742.7 / 1,197.8 / 745.1 MB
- Whole file 294.5 s (EPYC 7763) vs 266.6 s (9V74); seeding 85 s; ~1.5 GB of Zstandard logs
- Apple M5 Pro: list 1,000 311–358 ms; list 5,000 1,364–1,603 ms; list 10,000 3.2–5.4 s @ 1.9 GB RSS
- Budgets derived as higher median × 1.25 headroom; hosted-to-reference ratio 2.4–3.4×

Incident corpus (`docs/postmortem/`): 4 resolved post-mortems, each with a named root cause, a
timeline tied to persisted event-log sequence numbers, and the guardrail that closed it —
0001 ACP default-export drops inject; 0002 JS expression disabled filesystem tools;
0003 web agent validated a replacement server instead of its current GUI (evidence: session
`session-3eb796c2-…`, sequences 6, 30939, 31865, 34309, 34441, 34681); 0004 Landlock
partial-enforcement notice misclassified child failures (`landlock-run: partial enforcement`
notice vs exit-125 fatal line; `SANDBOX_UNAVAILABLE` misattribution).

Missing for a paper:
- No consolidated results table: the numbers are spread across per-benchmark notes; no single
  experiments section, no cross-benchmark summary, no figure.
- No before/after baseline for any optimisation (the perf notes give budgets and calibration,
  not "we improved X by Y%").
- No evaluation of the *agent* (task success, tool-use accuracy) — only harness
  latency/memory. `SAFETY.md` states plainly "It has not undergone a security audit", so a
  sandboxing-security paper would need an actual security evaluation, which does not exist.
- No related-work section, no claims framed against prior harness work.

Readiness: one batch — a synthesis unit that lifts the measured medians from the 8 benchmark
READMEs/notes into one results table, plus the 4 post-mortems as case studies. Zero new
experiments strictly required for a *systems experience report*.

Venue fit: ICSE/FSE industry or experience track; HotOS/HotInfra workshop short paper;
"agent harness engineering" experience report. Best framing available today is
**"performance regression gates for a multi-package agent harness: budgets, calibration and
flaky-CI economics"**, with the post-mortems as the reliability companion.
Risk: medium-high. Reviewers will ask for an agent-level evaluation the repo does not have; the
M5 Pro and EPYC numbers come from the project's own CI and cannot be independently reproduced
without running the suite (explicitly out of scope for this scout).

### 2. dsh-plugins — NOTHING paper-ready

Path: `/home/zer0null/dsh-plugins/@local/dsh-plugin-openui/` — the entire tree is a single
OpenUI renderer plugin (`package.json`, `SKILL.md`, `README.md`, `lib/index.js`, `lib/client.js`,
`cordis.patch.yml`, vendored `node_modules`). No data, no experiment, no measurement, no eval.
Readiness: more than one batch (there is no question being asked). Not a candidate.

### 3. agentnet + agentnet-sandbox — NOTHING paper-ready (implementation only)

Paths: `/home/zer0null/agentnet/{PLAN.md,agentnet.js,src/{a2a,board,server,jsonsafe}.js,test/}`,
`/home/zer0null/agentnet-sandbox/{a2a,dashboard,pi-ext}/`.
Established: a working hybrid agent mesh — JSON-RPC 2.0 A2A endpoint, Agent Card at
`/a2a/agent-card.json` and `/.well-known/agent-card.json`, SSE streaming, push-notification CRUD,
durable JSONL board, `fs.watch` wake-on-message. Code totals 1,205 lines; tests are 8 cases
(4 in `test/a2a.test.js`, 4 in `test/board.test.js`). `PLAN.md` states one validation:
"real pi subagent registers + receives an inbox message; dashboard shows the interaction".
`data/` contains only empty `inboxes/`.
Missing: any measurement. No latency, no delivery/reconnect numbers, no multi-machine run log,
no comparison against an existing A2A implementation. Nothing beyond a demo is recorded.
Readiness: more than one batch (a network experiment has to be designed and run first). Not a
candidate under the "already measured" rule.

### 4. background agent ("Orbit") — identity/dedup case study (STRONGEST measured artifact)

Paths:
- `/home/zer0null/background agent/research/identity-duplication.md` (185 lines)
- `/home/zer0null/background agent/docs/EVALS.md` (87 lines)
- `/home/zer0null/background agent/docs/SESSION-FINDINGS.md` (322 lines)
- `/home/zer0null/background agent/research/storage-audit.md` (88 lines), `stream-redundancy.md` (210), `transport-choice.md` (185)

Already measured (`research/identity-duplication.md`, read-only DB investigation):
- 230,395 rows in `fact`; **100 duplicate pairs = 131,500 rows = 57.1 % of the table**
- every pair is `relation_kind='stream'`, `k2:K2-806C/job:*` (25 jobs × 4 relations), 1,315 rows
  per pair, `COUNT(DISTINCT observed_at) = 1` — same observation stored 1,315 times
- the design claim "duplicates differ ONLY in `provenance.fetchedAt`" is **FALSE**: two hashed
  fields vary, `epoch` and `provenance.fetchedAt`; dropping `fetchedAt` alone deduplicates
  nothing; dropping both collapses each pair 13,150 → 10 rows
- `epoch` is a global per-run sequence counter, equal to `run.id` for **99.7 %** of rows, i.e. a
  sequencing field leaking into a content-identity hash
- independent corroboration in `docs/EVALS.md`: `SCHEMA_VERSION` 1.0 → 1.1, and the eval detector
  `dedup.inserted.per.run` (an unchanged re-observation must not insert)
- suite sizes: 142 pass / 0 fail at one point, 261 tests total; 7,600+ facts, 250+ collection runs

Missing for a paper:
- The fix is described but no **post-fix re-measurement** is recorded (no "after: N pairs, X % of
  table, ratio back to 1.0"). That one number is the whole experiment.
- Single dataset, single deployment, one machine; no second adapter family to show generality.
- No baseline against an off-the-shelf bitemporal store.

Readiness: **one batch** — re-run the same read-only query set against the post-`SCHEMA_VERSION 1.1`
database and add a before/after table. (That run is execution, so it is not done here.)
Venue fit: short paper / workshop on agent memory & personal data systems (e.g. a data-engineering
or "systems for personal AI agents" workshop); could also be a strong practitioner-blog-grade
case study inside a larger harness paper.
Risk: low-medium. The finding is unusually clean and quantified; the risk is scope — n = 1 store,
and the "bug" is a one-field identity mistake that reviewers may call obvious in hindsight.

### 5. auto PR tool ("prtool") — human-gated contribution funnel (measured, small n)

Paths:
- `/home/zer0null/auto PR tool/README.md` (108 lines — the spec: two gates, strong ≥0.30 /
  candidate ≥0.20 thresholds, vitality `log10(stars+1)×0.03` capped 0.10)
- `/home/zer0null/auto PR tool/data/proposals.json` (109,709 bytes — 38 proposals, gate history)
- `/home/zer0null/auto PR tool/.prtool/SESSION-CLOSEOUT-2026-10-05.md`,
  `.prtool/SESSION-CLOSEOUT-2026-09-23.md`, `.prtool/pr663/`, `.prtool/reports/`

Already measured (tallied read-only from `data/proposals.json`):
- **38 proposals**: `submitted` 3, `awaiting-gate2` 2, `gate1-rejected` 20, `awaiting-gate1` 12,
  `failed` 1
- tier mix: strong 14, candidate 24
- human gate-1 acceptance ≈ 5 of 25 decided = **20 %**; 20 explicit rejections
- real external outcomes attached in the close-outs: PR `OpenHands/extensions#663` open,
  head `cf235dd`, review answered, triage issue `#733` filed; PR 8549 line of work likewise
  documented in `.prtool/pr8549-*.md` + `preflight-*.json`/`txt`

Missing for a paper: the outcomes are self-authored close-outs, not an instrumented log; no
precision/recall against a "true transplantable seed" ground truth; no comparison to a baseline
matcher; the 12 `awaiting-gate1` are undecided and must be excluded, leaving n = 25. Merge
outcomes are maintainer-gated (the close-out says so explicitly).
Readiness: one batch — but the batch is *design* (define the ground truth, label the 38) more
than *measurement*.
Venue fit: workshop / experience report on human-in-the-loop automation or OSS contribution
tooling. Risk: medium — small n, single user's repo graph, author-measured outcomes.

### 6. pi-autonomous-test + maintenance — no paper here, but one reusable measurement artifact

- `/home/zer0null/pi-autonomous-test/README.md` is literally `// test project`; the directory is
  a scratchpad of `hello.txt`, `async-a.txt` … `integration-final.txt`. **Nothing.**
- `/home/zer0null/maintenance/fleet-hygiene/` produces one immutable dated snapshot per day
  (4 present: `REPORT-2026-10-19.md`, `-20`, `-21`, `-22`), byte-for-byte the script's stdout, and
  guarantees "`MISSING` rather than estimate" — a genuinely disciplined measurement convention.
  `REPORT-2026-10-22.md` records: `FLEET: repos=55 dirty_repos=24 dirty_files=1755
  repos_with_unpushed=7`, plus per-repo dirty counts (e.g. 890 dirty files in
  `reserach extarctor`, 521 in `memory and knowledge research - MU-PHI`).
  Missing for any paper: 4 days is not a time series, no experimental variable, no hypothesis.
  Useful only as a supporting figure ("a 55-repo agent fleet accumulates 1,755 dirty files in a
  day") inside the harness paper, not as a candidate of its own.

## Answer to the goal question

**Nothing on this host is paper-ready today.** No project carries a complete
experiment + results + write-up. Three have real, already-measured numbers that could reach a
workshop submission after **one** synthesis/measurement batch:

1. deepseek-harness — perf-gate corpus + 4 post-mortems → experience report (numbers exist, table does not).
2. background agent — identity-duplication study → short paper (before-state measured, after-state missing).
3. auto PR tool — gate funnel → workshop note (n = 25 decided, ground truth undefined).

`dsh-plugins`, `agentnet`, `agentnet-sandbox` and `pi-autonomous-test` contain no measurement and
are not candidates. `maintenance` supplies a supporting number, not a paper.

## Evidence commands actually run

- `ls -1` / `find … -maxdepth 2` orientation over all six project roots (read-only)
- `wc -l`, `head`, `sed -n`, `grep -nE` over the specific documents cited above
- `node -e` read-only aggregation over `auto PR tool/data/proposals.json` (38 rows; project data
  file, not project code)
- No git command was executed anywhere; no file outside this workspace was touched.

## Traps recorded for the next unit

- `/home/zer0null/deepseek-harness/BENCHMARK.md` looks authoritative and is 3 lines of setup
  instructions. The measurements live one level down in `.agents/notes/implemented/testing/`.
- `/home/zer0null/deepseek-harness/research/b2-evidence.txt` (2,863 lines) and `runs/m4-b3*.txt`
  are **agent transcripts** (a Forgejo/GitLab evaluation research run), not this project's results.
  Do not cite them as findings.
- `data/proposals.json` is `{"proposals": {id: …}}` — an object, not an array; the state field is
  `status`, not `state`, and `history` entries do not carry an `action` key (all 91 entries read
  as `undefined`). Counting must go through `status`.
- Every document exists in `.md` / `.zh.md` / `.i18n.yaml` triples in deepseek-harness; cite the
  English `.md` only, or counts inflate ~3×.

## Deliverables

- `orchestration/units/HOST-SCOUT-3.md` (this file)
- `orchestration/handoffs/HOST-SCOUT-3.json`
