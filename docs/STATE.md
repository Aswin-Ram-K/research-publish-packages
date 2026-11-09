# STATE — the current state of this workspace

**Last updated:** 2026-11-06 · **By:** SEED-CONCEPTS-2026-11-06 (closing writer)
**Read this first.** It is the single *current-state* page. Older status pages remain valid as dated
records but are superseded here as current state — chiefly [`orchestration/STATUS.md`](orchestration/STATUS.md)
(the docket-era batch record, 2026-10-21) and [`orchestration/CLOSING.md`](orchestration/CLOSING.md).
Document map: [`docs/INDEX.md`](INDEX.md) · filesystem map: [`STRUCTURE.md`](../STRUCTURE.md) ·
narrative: [`journal/INDEX.md`](../journal/INDEX.md) · build spec (historical): [`docs/PLAN.md`](PLAN.md).

---

## 0. One line

The live work is the **ptr-engine serving/cache/cost experiment**: the gen-6 16-cell grid is measured
and its verdict is **`not_adjudicable`** (2026-10-28); the instrument itself, not the budget, is the
binding constraint, and the next step is a **gen-7 instrument decision that belongs to the user**.
The request ledger is reconciled (**2,591 spent / 1,729 remaining of 4,320**). The app and the paper
track are dormant-but-intact, not abandoned. Separately, the **Consonance bounded-context research is
filed** (2026-11-03): a report and a prospective protocol, both independently rechecked **PASS**, with **0
live calls** — and the comparative experiment they specify is **UNFUNDED** (7,560 requests against 1,729
remaining) until the user decides (§2a).

---

## 1. LIVE — ptr-engine: serving, cache and cost

**Question.** On the live Occamy/SGLang endpoint (`http://192.168.2.168:8012/v1`, model `occamy-1.0`,
tools on), does a pointer/index-based context design (`pointer-stable`, arm C) serve a 48-turn
workload with lower tail latency and less prompt work than full-transcript history
(`transcript-grow`, arm A), at no worse answer quality — and at what request/cache cost?
Arms: A `transcript-grow` · B `transcript-compact` · C `pointer-stable` · D `lease-reopen`
(B/D descriptive only). Frozen rules: [`docs/PREREG-ARM-RUN.md`](PREREG-ARM-RUN.md) (PARM-1),
[`docs/TVS.md`](TVS.md).

**Last measured verdict — 2026-10-28, owner `orchestration/handoffs/GRID-2-FINAL.json`:**

| Hypothesis | Verdict | The number that decides it |
|---|---|---|
| H1 tail latency (C p95 TTFT < A) | **`not_adjudicable_floor`** | binding arm C: p50 156.151 ms [146.306, 291.926], n=48, lag-1 r=+0.2949 ⇒ **n_eff 26.14 < 60**; p95 **refused at n=48**; arm A has 0 usable cells |
| H2 prompt work per turn (both limbs) | **`not_adjudicable`** | frozen rule is C-vs-A; A has 0 usable cells. Within-arm only: C cached 5,395.09 vs uncached 355.62 tok/turn (n=364); D 1,497.85 vs 332.28 (n=184) |
| H3 checkpoint quality (no worse than 2/12) | **`not_adjudicable`** | the grid's `x/12`, `x/9`, `answered_ratio` are **placeholder zeros**, not measurements; no admissible emitter exists for the gate |
| TVS (tokens to verified success) | **`UNDEFINED`** | `n_verified_success = 0` arm-level and 0 at first checkpoint — denominator undefined, no token count substituted |

Overall: **`not_adjudicable`**. These reproduce the grid's handoff to the digit; the report recomputes
them from rows (`experiments/ptr-engine/tools/grid2_final_report.py`, 21 tests).

**Why it could not adjudicate — the instrument, four defects:**

1. **Treatments never fired** (fixture layer): 8 transcript cells carry `usable_for: []`; `evicted_turns=0`,
   `digest_rows=0` over 48 turns. `tasks-v6/LR-01.v8.json` prices its wall from *declared* padding
   (10,616) while live base is 5,628–6,139 tokens and growth 41–98 tok/turn ⇒ turns-to-wall 73–113 > 48.
2. **Replicate collapse** (selector layer): `tools/run_grid_report.py:235` dedupes on
   `(arm, rep, turn_index)` and every gen-6 cell wrote `rep=1`; **288 turn rows → 96 analysed**
   (`dropped_duplicate=192`). That merge is also why p95 is refused.
3. **Absent stamp admitted**: `longrun/analyze_stats.py:749` keeps a manifest-less cell (prints it
   `unstamped`) — the two `exit-4` cells are excluded **by name** in the census instead.
4. **Cap-gate projection under-counts** (pinned runner): `projected_requests` prices 96, but a tools-on
   turn bills k+1 requests; the gate refused the 97th → 2 cells `exit 4` at T47/T48 with no manifest.
   (The 5th fault, nested `rows_path`, was repaired writer-side in `cell.py` — not a generation, since
   `cell.py` is outside `HARNESS_FILES`.)

**Request ledger (the budget is not binding):**

| Field | Value |
|---|---|
| Cap / reserve | **4,320** / 0 |
| Frozen baseline | `experiments/ptr-engine/measure/LEDGER-GRID-BASELINE-4.json` — 1,321 requests / 2,999 remaining, `as_of` 2026-10-27T20:53:48Z, sha `3f879fa4…` (source ledger) |
| Spend after the grid | **2,591 / 4,320 ⇒ 1,729 remaining** (delta +1,270, gap 0) |
| Live ledger | `experiments/ptr-engine/measure/REQUEST-LEDGER.json` **rebuilt 2026-10-28** to 2,591/1,729 (`tools/request_ledger.py`; sha now `8ebf4ed5…`) |
| Marginal cost of the grid | **1,270 / 16 = 79.375** (≈79.4) requests/cell; highest single cell **96**; 16 cells at the observed max = 1,536 < 1,729 |
| The "162/cell" claim | **declined**: `2591/16` charges the grid for its 1,321-request baseline. Recomputed, the grid is affordable |
| Launcher state | `run_a_star.py --dry-run` → `RUN-A RECONCILE … gap=0`, `DRY END cells=16 refused=0 requests=0` (verified 2026-10-28 after the rebuild) |

**Next actions, in order** (detail: `docs/GRID-2-FINAL.md` §5-6, `docs/GRID-GAP-DIAGNOSIS.md`,
`orchestration/handoffs/GRID-2-FINAL.json` `next_unit_hint`):

1. **Gen-7 decision — user approval.** A usable grid needs a **new fixture (v9) whose wall is priced
   from measured growth**, the projected-request fix in the pinned runner, and rep identity (cell id
   in `rep`, or a cell-qualified selector key). Any fixture/`run_longrun.py` change **mints generation
   7**: gen-6 rows become non-poolable and the re-run is all-or-nothing per arm. **Do not launch gen-6
   cells expecting a new verdict** — a funded re-run keeping either instrument defect returns this same
   verdict.
2. **Re-run ≥6 cells/arm** (measured cost 79.4–96/cell, inside the 1,729 remaining), then rebuild the
   ledger after the batch. A cap increase above 4,320 is *not* required by the measured numbers and
   would be a user decision.
3. **If a gen-6 census is needed before gen 7**, build it from the 16 manifests by nested
   `run.rows_path` (the pinned reader cannot link them) and keep the 2 `exit-4` cells excluded by name.
4. **Do not** re-analyse existing rows under a new estimator (instrument change), re-run a 48-turn cell,
   edit a grade (exit 10/11 = re-run grader/analyser), or lower the n-floor (`min_n_for(0.95)=60`).

**Authoritative files:** `docs/GRID-2-FINAL.md` (+ `experiments/ptr-engine/measure/GRID-2-FINAL.json`) · `docs/GRID-GAP-DIAGNOSIS.md`
(+ handoff `GRID-GAP-DIAG.json`) · `docs/GRID-RUN-2.md` + `journal/2026-10-27.md` + handoff
`GRID-RUN-2.json` (the run record) · `docs/GRID-RUNBOOK.md` (commands, exit codes, per-cell ritual;
its §0 state snapshot is historical) · `docs/LEDGER-RECONCILE.md` + `experiments/ptr-engine/measure/LEDGER-GRID-BASELINE-4.json`
· `docs/PREREG-ARM-RUN.md` (frozen) · `docs/TVS.md` · `docs/LEASE-REOPEN-23.md` (D-arm clearance) ·
`docs/CACHE-CREDIT-CHAT.md` (cache credit is measurable: +2,048 cached tokens on a repeated prompt).
**Historical:** `docs/GRID-BUDGET-RECHECK.md`, `docs/LEASE-REOPEN-12.md`, `docs/CANARY-ERA-B*`,
`experiments/ptr-engine/measure/GRID-SHAPE.json`, `experiments/ptr-engine/measure/GRID-PARAMS-16CELL.json`, `docs/GRID-RUNBOOK.md` §0.

---

## 2. Paper track — filed, waiting; fourth paper in progress

- **Filed (2026-10-19):** three papers — `encoder-crossover-190`, `replay-record-not-decision`,
  `gated-read-batching` — published on **Zenodo** (DOIs `10.5281/zenodo.23463944`, `…23482511`,
  `…23483314`); **TMLR** submissions pending under forum ids `L9GcDGb2fr`, `U2WjJMH0EK`, `q72ZB9ZMqy`;
  Preprints: encoder + gated accepted (editor-reported, HTTP 403 on verification), replay not accepted.
  Standing rule: **never claim the work was never published.**
- **Upload source of truth:** `submission-kit/` (9 sha256-verified files). Upload from there, not from
  the paper trees.
- **Fourth paper, live:** `papers/context-cache/` (MANUSCRIPT.md ~91 KB, COMPILATION/FOLD docs) — the
  write-up of the cache/serving mechanism; it consumes ptr-engine results, so its claims inherit §1's
  `not_adjudicable` status until gen 7.
- **Fifth artefact, 2026-11-06:** a documentation-only **research seed package** —
  [`experiments/ptr-engine/research-seed-concepts/README.md`](../experiments/ptr-engine/research-seed-concepts/README.md)
  — recommending **two** papers (flagship = append-cost law + its design consequence; methods = instrument
  validity) instead of the one N1 brief. See §10. No manuscript was modified and no request was sent.
- **Superseded:** `strategy/SUBMISSION_READINESS.md`'s "NO" verdict (2026-10-16) predates the actual
  filings; read `strategy/SUBMISSION_RECORD.md` for what exists. `strategy/TMLR_SUBMISSION.md`
  describes an anonymised variant built but **not** submitted.

---

## 2a. Consonance bounded-context research — filed 2026-11-03

**Question.** Can Consonance's intended bounded recoverable context view (BRCV) — a deterministic stable
instruction/tool prefix, a bounded recent verbatim working set, and authoritative versioned external
records fetched on demand through deterministic pointers, with old tool output masked before any summary
— keep older evidence reachable at bounded prompt cost? **Answered prospectively only**: two documents
specify the design and how to test it. **No experiment has run, no model call was made, and no Rust kernel
or stripped-down omp interface exists.**

**(a) Deliverables and verdicts** — each verdict written by a unit that authored nothing it graded:

| Artifact | Size | Verdict | Owner anchor |
|---|---|---|---|
| `research/next-candidates/consonance-bounded-context-report.md` | 356 lines / 53,979 B | **PASS** after one repair (`V-CONSONANCE-BC-REPORT` partial → `CONSONANCE-BC-REPORT-FIX` → recheck pass) | `orchestration/handoffs/V-CONSONANCE-BC-REPORT-RECHECK.json` |
| `research/next-candidates/consonance-bounded-context-evaluation.md` | 517 lines / 44,691 B | **PASS** after one repair (`V-CONSONANCE-BC-EVAL` partial → `CONSONANCE-BC-EVAL-FIX` → recheck pass) | `orchestration/handoffs/V-CONSONANCE-BC-EVAL-RECHECK.json` |

Narrative: [`journal/2026-11-03.md`](../journal/2026-11-03.md). Batch record:
[`orchestration/VERDICTS.md`](orchestration/VERDICTS.md) `## Batch: Consonance bounded-context research (2026-11-03)`.

**(b) What is established, what is proposed, what is not established.**

- **Established** (traced to originals, offline): `67.1141×` is **body bytes versus index bytes**, not a
  token, cost or latency saving (`experiments/ptr-engine/RECORD.md` §1: 30,000/447); a 3/3 lookup is a
  **narrow capability**, not a quality result; the gen-6 grid verdict stays **`not_adjudicable`** (§1); C54
  is a **server-wide resident working set under one pressure**, not a per-conversation allowance, a pin, or
  a universal 260k-token budget; a **body-store retention pool is not the server's KV/state cache**;
  `cached_tokens: null` is **unknown** except where endpoint- and field-specific semantics are established
  (SGLang `:8012`), never universally zero; an append-only transcript still grows in logical input, since
  cache hits reduce prefill work and not token count; and **G5's `6.744331504` is the mean of eight
  per-fan-out ratios**, not `123,256 / 20,328` (ratio of totals `6.063360882`).
- **Proposed, unmeasured:** BRCV itself; the E1/E2 envelopes; the five-arm comparative. Every number in
  the protocol is *protocol arithmetic*, not a result.
- **Not established:** the three external literature sources (marked **unverified** in the report); the
  Rust kernel and omp integration (user-supplied direction, no API invented).

**(c) Exact next decision.** Run **`E1-CACHE-BOUNDARY-SWEEP` at ≤60 calls**, then **`E2-CHECKPOINT-COST`
at a budget the owner approves**: **123 calls is a one-rep descriptive probe** (not adjudicable), **369** is
the adjudicable 3-rep run and **450** with the 12-checkpoint fixture. The full comparative is **7,560
requests against 1,729 remaining = 4.37× ⇒ `UNFUNDED`**; the funded alternative is the **185-call
instrument pilot**, and funding neither is also an answer. `experiments/ptr-engine/BOUNDARY-PREREG.md`
(696 scheduled, ceiling 810, registered 2026-10-26) remains a **separate** unexecuted candidate and is
never pooled with E1/E2.

**(d) Blockers.** The **quality emitter cannot say yes** — a log that follows the fixture's own `ANSWER:`
contract still grades `verified_success false` (`PATH-CANNOT-SAY-YES`, report E-17), so **every quality arm
including E2's `verified_success` limb is blocked** on a fixture/grader owner decision, not a patch. No
eligible fixture carries **multi-hop** retrieval or a **missing/stale/revoked** source; the protocol records
those classes `UNAVAILABLE` / `NOT_OBSERVED` and refuses to score them as success. The ledger must be
**re-reconciled** before E1 starts.

---

## 3. Research Extractor app (`resextract`) — dormant, still load-bearing

- `src/resextract/` — repo→docket pipeline; Python ≥3.14, console script `resextract`
  (`doctor`, `status`, `materialize`, `serve`, `run`; the unimplemented subcommands exit 3 honestly).
- **State:** dormant since ~2026-10-24. Two Duval dockets were assembled 2026-10-08
  (`dockets/duval/duval-replay-material`, `duval-u55-pinned`, both `status: draft`) and `_smoke/` is the
  frozen backward-compatibility witness (`verify_docket` `ok=False` by design).
- **Acceptance is unmet and was never met:** the store holds **0 claims / 0 verdicts / 0 evidence**, so
  every docket verdict is `UNVERIFIED`; §1.3 of the build plan cannot be satisfied from here.
  See `orchestration/STATUS.md` §§1-3 (dated record).
- **Dependencies that still bind:** `tests/` (~97 files) imports it; `config/` is loaded by path;
  `.gitignore` semantics are guard-tested. Do not move `src/`, `tests/`, `config/`.
- **Environment repair (2026-10-28):** the venv's editable install pointed at the pre-rename path, so
  *every* test failed at `conftest.py` import; the `.pth` was repointed and the launcher's hardcoded
  root fixed. Targeted suites verified: `tests/test_launcher_dryrun_refusal.py` 4 passed,
  `experiments/ptr-engine/tests/test_ledger_kind_rule.py` + `test_grid2_final.py` 28 passed. **The full
  suite was not re-run in this session** — run it before claiming app health.

---

## 4. Supporting workstreams

| Workstream | State | Where |
|---|---|---|
| Job search | done-ish; 7 subdomains (README documents 5), `FINDINGS.md` + `JOBS.jsonl` | `jobs/` |
| Public release v0.1 | done: 943 files / 61 MB, sanitised, 7/7 gates, PolyForm NC 1.0.0 | `release/REPORT.md`, `release/REPRO.md` |
| Reproducibility packages | archived | `repro/encoder-crossover-190/` |
| External-practice surveys | adopted as standards for metrics/eval | `docs/EXTERNAL-SERVING-PRACTICE.md`, `docs/EXTERNAL-EVAL-PRACTICE.md` |
| External-workspace pointers | normative protocol (cite constants, never copy) | `docs/EXTERNAL_WORKSPACE_POINTER_PROTOCOL.md` |
| Consonance handoff package | staged 2026-10-25, **not executed** | `handoff from consonance/` |
| Consonance bounded-context research | filed 2026-11-03: report + prospective protocol, both rechecked **PASS**, **0 live calls**; no run exists and the comparative is `UNFUNDED` | `research/next-candidates/`, §2a |
| R2 serving design scouting | prospective, unapproved | `research/next-candidates/` |
| Scratch (290 dirs) | not authoritative by policy, but some are cited deliverables (`scratch/utmlr1`, `scratch/urecord1`) — do not blanket-delete | `scratch/` |

---

## 5. Repo mechanics and hazards (all verified 2026-10-28 unless marked)

- **The workspace path was renamed.** It is `/home/zer0null/research extractor`. The old spelling
  `reserach extarctor` is not a path and does not exist; `STRUCTURE.md` carried a false claim that the
  misspelling was intentional until 2026-10-28, when it was rewritten to record the old spelling only
  as a dated-record artefact. Dated records keep the old spelling; live instructions were fixed.
- **Git:** branch `research/next-candidates-2026-10-24`, HEAD `f17663d` (2026-10-25), remote
  `Aswin-Ram-K/research-publish-packages`. **Everything after 2026-10-25 is uncommitted**, and ~1,300
  files are untracked — including this page's sources of truth. HEAD is a checkpoint, not the truth.
- **omp worktrees are partial:** a session started under `~/.omp/wt/…` sees tracked files only. Use
  absolute paths under the real root.
- **Session contract:** [`AGENTS.md`](../AGENTS.md) — owner mode, documentation contract, hard
  constraints. **Docs map:** [`docs/INDEX.md`](INDEX.md). **Doc guard:** `tools/doc_check.py` +
  `tests/test_agent_context.py`; orientation: `tools/session_start.py`.
- **Gitignored-but-critical:** `state/logs/U8.15/baseline_gaps.json` and
  `state/logs/U8.18/verifier_shape_baseline.json` are sha-pinned by `tests/test_orchestration_handoffs.py`;
  a fresh clone fails that guard until they are restored. `state/state.sqlite` is live WAL — copy
  before reading.
- **Contract text, do not edit casually:** `orchestration/VERDICT-RITUAL.md` and
  `orchestration/units/TEMPLATE.md` are asserted literally by
  `experiments/ptr-engine/longrun/tests/test_verdict_ritual.py`.
- **Live-cell discipline:** `.occamy.lock` held for the whole batch (one request in flight, serial);
  after a batch, rebuild `experiments/ptr-engine/measure/REQUEST-LEDGER.json`; never hand-edit a ledger or baseline; never
  restart the shared model server.

---

## 6. Open decisions for the user

1. **Gen-7 instrument** — approve the fixture/generation change that makes the treatments reachable
   (the only route to an adjudicable H1/H2/H3). Nothing launches without it.
2. **Budget cap** — 1,729 requests remain; the measured re-run fits. An increase would need explicit
   approval; none is required by the numbers.
3. **GX10 / Occamy service changes** — restart, `--mem-fraction-static`, or crash-loop repair are user
   decisions. Last verified reachable 2026-10-27 (HTTP 200); not re-probed 2026-10-28.
4. **SearXNG** — held for the user since the docket-era degradation; the app's search-dependent legs
   remain unproven while it is unproven.
5. **Dockets versioning** — `dockets/` is root-gitignored; whether to version it is still open.
6. **Commit policy** — the untracked layer (~1,300 files) is the current state. Committing it, or
   leaving it uncommitted, is a user call; agents must not run `git add -A` / `git clean` unasked.
7. **Consonance E2 budget and comparative funding** (since 2026-11-03) — E2 runs at **123 calls
   (descriptive only)**, at **369–450 (adjudicable, needs approval)**, or not at all; and the comparative
   is **`UNFUNDED` at 7,560 against 1,729 remaining**, with a **185-call pilot** as the funded
   alternative. Three mutually exclusive answers, all the user's (§2a).

---

## 7. What changed on 2026-10-28 (this session)

- Agent contract rewritten (`AGENTS.md`): owner mode + mandatory documentation contract; hard
  constraints preserved; workspace path corrected; board mode marked dormant.
- This page created; `docs/INDEX.md` created; `journal/INDEX.md` brought up to date; dated journal
  entry added.
- `STRUCTURE.md` corrected (path claim, stale counts, missing top-level rows).
- Documentation guard added (`tools/doc_check.py`, `tests/test_agent_context.py`) and orientation
  snapshot (`tools/session_start.py`).
- Test rig repaired: venv editable path repointed; launcher and refusal-test roots fixed
  (`run_a_star.py`, `tests/test_launcher_dryrun_refusal.py`); tools-dir fallback for a copied launcher.
- `experiments/ptr-engine/measure/REQUEST-LEDGER.json` rebuilt from rows: 2,591 spent / 1,729 remaining (backup at
  `state/backups/REQUEST-LEDGER.pre-grid-rebuild.2026-10-28.json`, sha `3f879fa4…`); launcher dry run
  now reconciles with `gap=0`.
- Live instructions naming the old workspace path corrected; dated records left as recorded.
- **Independently verified** by a unit that wrote none of it: all four re-run claims reproduced
  (`doc_check` exit 0, 41 passed, `gap=0` with 1,321+1,270=2,591, baseline sha `3f879fa4…`), and every
  §1 figure reproduced to the digit from `experiments/ptr-engine/measure/GRID-2-FINAL.json` and the 16
  cell deltas (mean 79.375, max 96). The verifier graded the body `partial` for two real defects it
  found, both now fixed: the guard's ghost-entry check ignored **relative** links (a bad
  `[X](X.md)` row passed), and three stale counts/wording survived (155 docs, "four artefacts",
  79.4-as-equation). `tools/doc_check.py` now resolves every `](…md)` target, with 3 new red→green
  tests (12 total in `tests/test_agent_context.py`); `AGENTS.md` and this page were corrected.

---

## 8. What changed on 2026-11-03 (recorded 2026-11-04)

- **Filed the research report** — `research/next-candidates/consonance-bounded-context-report.md` (356
  lines): the BRCV proposal, a 26-row evidence ledger, the ten claim corrections, and the exact next
  E1/E2 decision.
- **Filed the prospective protocol** — `research/next-candidates/consonance-bounded-context-evaluation.md`
  (517 lines): E1 (≤60 calls) then E2, five paired arms, positive **and** negative controls, a worked
  abstention hypothetical, and `cached_tokens: null` kept unknown.
- **Two material defects found by independent verifiers and repaired**: the report's E2 limb (≤120 calls
  was presented as deciding the premise → now **one-rep descriptive at 123**, adjudicable **369/450**
  with owner approval), and the protocol's comparative total (**6,300 → 7,560 = 4.37×**, because arm D
  bills two requests per turn). `UNFUNDED` survived both and strengthened.
- **Two rechecks passed**, each by a unit that wrote none of the artifact: `V-CONSONANCE-BC-REPORT-RECHECK`
  and `V-CONSONANCE-BC-EVAL-RECHECK`; their progressive checkers fail on a mutated number
  (`123→120`, `7,560→6,300`), so the green is falsifiable.
- **Record updated**: `journal/2026-11-03.md` + its index row, `orchestration/STATUS.md` (its 2026-11-03 batch section),
  `orchestration/VERDICTS.md` (batch section), `orchestration/units/SESSION-CLOSE-BC-2026-11-03.md` and
  its handoff.
- **No live call and no build**: 0 endpoint requests, 0 model calls, no target-repo write, no Rust kernel
  or omp build, `BOUNDARY-PREREG` untouched and unexecuted, ledger unchanged at 2,591 / 1,729.
- Close-out gate: `python3 tools/doc_check.py` exit 0; `.venv/bin/python -m pytest
  tests/test_agent_context.py tests/test_orchestration_handoffs.py -q` → **30 passed**.

---

## 9. What changed on 2026-11-04 — paper candidates since the last compile

**Question asked and answered: is there one high-quality paper in the work produced since
`papers/context-cache/MANUSCRIPT.md` was sealed (2026-10-24 21:39)?** Four candidates, one recommendation.

| # | Brief (`research/next-candidates/briefs/`) | Thesis | New requests |
|---|---|---|---|
| **1** | `N1-residue-law.md` | An append costs `(P1 mod B) + L`; at residue 0/1 the cache stops paying; two tokens of padding defuse it | **0** |
| 2 | `N2-instrument-liveness.md` | A harness must prove it can say yes *and* no before its nulls count | **0** |
| 3 | `N4-finish-flagship.md` | The drafted paper is the paper: 1,892 uncited rows fold in free | 0 (≈90 optional) |
| 4 | `N3-the-wall.md` | The wall's cost is a window decision, not a boundary event | ≈**920** |

Index and correction table: [`research/next-candidates/2026-11-04-candidates.md`](../research/next-candidates/2026-11-04-candidates.md).

- **N1 is recommended**, on four grounds: it is a law rather than a measurement (residual **0 in 186/186**
  rows, **6/6** misses at residues 0 and 1, **11/11** positional misses across six block indices, **57/60**
  warm rows); it is reproducible offline; it is actionable in a few lines of client code; and it is **not**
  in the draft — §9 covers immediate repeats, §9a the per-stack grid, and §8a argues the opposite way about
  padding because it prices a 64-token page-recovery pad, not a 2-token cliff-avoidance pad.
- **Its cliff magnitude is instrument-dependent and the record says so.** `/generate`
  `meta_info.cached_tokens` reads `cached = 8,000` and `64 + L` at P1=8064 where `usage.prompt_tokens_details`
  reads `null` and the whole prefix; `RECORD.md:114` records the 5.2× between them as withdrawn then
  **UNDECIDABLE** (`orchestration/units/RECON-C1.md`). The paper must state the law, the class change, the
  instrument dependence, and the padding rule — and may not assert absence as a cross-instrument fact.
- **Six numbers corrected by an independent re-check** (folded into the brief, tabulated in the candidates
  index): six block indices not four; instruments disagree on absence; `L − 64` recovery is a different
  request shape (second byte-identical repeat, E4 rep2 `cached = 960` ×20, E4R 40/40) from `LAW.md`'s cold
  prime; crossover cells are **+44.9 % / −95.6 %** (`crossover/RESULTS.md:52,54`); the padding rule is
  positive under every reading (≈64 tokens on the counter reading, ≈`P1 − r` on the null reading); C9 is
  superseded only as a bar to the residue law and still governs HARVEST's 378-row table.
- **Where the record lives:** branch **`research/paper-candidates-2026-11-04`** of
  `/home/zer0null/research extractor` — `f28e2ef` (index + four briefs) then `c8b7b7e` (corrections), parented
  on `f17663d`, **not** on `research/next-candidates-2026-10-24`. Keep it until the owner resumes work from the
  real repository. The session worktree `wt/20261104-171928` was verified **clean, zero commits beyond
  `f17663d`** and is merged into the record branch as an ancestry-only merge.
- **Not done:** no paper text beyond the briefs' abstract stubs, no cell launched, the 9-request decisive cell
  (prime → identical resend → three appends, read on both instruments) **not** run, the ~90-request
  resting-window arm not approved, N3's ≈920-request package unscheduled, Consonance comparative still
  `UNFUNDED`.
- **No live call and no build:** 0 endpoint requests, 0 model calls, no target-repo write, ledger unchanged at
  2,591 / 1,729.
- Close-out gate: `python3 tools/doc_check.py` exit 0; the two contract suites pass (see the handoff's
  `evidence.pytest`).

---

## 10. What changed on 2026-11-06 — the research seed package (documentation only)

**Question asked and answered: what paper (or papers) does the existing research actually warrant, and
what would each one need before it can claim its result?** Answer: **two**, on different claim types, with
the flagship named first. Full reasoning, evidence map and kill criteria live in the package; this page
records only state.

**Package** — `experiments/ptr-engine/research-seed-concepts/`, a documentation subfolder of the existing
experiment. It creates **no experiment, no `RUN.json`, no `measure/` JSON, no result**: there is nothing
here that could be mistaken for a measurement.

| doc | bytes | answers |
|---|---:|---|
| `README.md` | 15,091 | which papers, why this boundary, what cannot be claimed today, links |
| `EVIDENCE-DOSSIER.md` | 33,892 | one entry per usable contribution → its dataset, claim, status, contradiction, role |
| `RESEARCH-BRIEF.md` | 24,310 | flagship: problem, RQ, contributions C1–C4, arms, prototype, V1–V8, K1–K9 |
| `SECOND-PAPER-BRIEF.md` | 13,143 | methods paper: seven-case instrument-failure series (0 requests) |
| `VALIDATION-ROADMAP.md` | 17,411 | stage 0 offline gates → ≈9-request cell → 36/≈185 pilots → 7,560 comparative |

**Recommendation in one line.** Flagship = *the bill is set by the append, not the window* — the measured
append-cost law (`(P1 mod B) + L` with residual 0; the residue-{0,1} class change; vLLM `+B` on 85/86), the
design consequence, and the index/bodies prototype's measured capability (3/3 fetch, 33/33 refusals, 0/3
no-body control) — with the five-arm comparative named as **unmeasured**. Second = instrument validity
(the quality path that could only say no; two mutually exclusive graders; a treatment that never fired;
replicate collapse 288→96; an admitted stamp; a cap gate two turns short; a bill that was not a bill).

**Corrections this session** (each re-derived from rows, not prose): "1,892 uncited rows" → **5,403**
`*.jsonl` lines across seven cells; "63 claims" → **69** mapped 1:1 (`verify_package.py` **PASS** today; 63
is the stale `RUN.json` synthesis count); `LAW.md` "four block indices" → **six** (11/11 rows); the graded
grid cost **79.375** requests/cell, not the declined 162.

**Zero spend, zero side effects.** 0 endpoint requests, 0 model calls, 0 live-grid cells, ledger unchanged
at **2,591 / 1,729** (snapshot 2026-10-28 — must be re-reconciled before any future run), no target-repo
write, `papers/` untouched, `BOUNDARY-PREREG` still unexecuted, gen-7 still undecided.

**Open for the user, in the order the roadmap needs them:** (i) approve the fixture/grader repair that lets
the quality path say *yes* — without it every quality arm is void before its first call; (ii) approve ≈9
requests for the decisive padding cell (prime 8,000 → identical resend → three appends, read on both
instruments); (iii) decide the comparative: fund 7,560 by raising the 4,320 cap, fund only the pilots
(≈185 or 36), or fund neither. No cap increase is authorised by this session.

**Verified:** `python3 tools/doc_check.py` → `OK docs clean under /home/zer0null/research extractor`
(exit 0); every link in the five package documents resolves (**23 targets, 0 broken**); no file outside the
package was modified (`find . -newermt '2026-11-06 00:00'` → **0** hits outside it).
