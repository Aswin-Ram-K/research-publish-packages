# STATE — the current state of this workspace

**Last updated:** 2026-11-10 · **By:** U-SPCC-57 (final E1 cell record)
**Read this first.** It is the single *current-state* page. Older status pages remain valid as dated
records but are superseded here as current state — chiefly [`orchestration/STATUS.md`](orchestration/STATUS.md)
(the docket-era batch record, 2026-10-21) and [`orchestration/CLOSING.md`](orchestration/CLOSING.md).
Document map: [`docs/INDEX.md`](INDEX.md) · filesystem map: [`STRUCTURE.md`](../STRUCTURE.md) ·
narrative: [`journal/INDEX.md`](../journal/INDEX.md) · build spec (historical): [`docs/PLAN.md`](PLAN.md).

---

## 0. One line

The live work is the **serving-context programme (SPCC)**: the layer compiler exists and is **wired** as
the `spcc` arm, the memory allowance is a supervisor decision chain whose `VERIFIED` is only reachable as
a last resort, and **E1–E6 are pre-registered** (§1a). The **billed-accounting plumbing proof is live**
(100 turns, 0 failed; prompt 174,047 · cached 159,744 ⇒ **0.917821**), but the arm's answers are **not**:
that run's scorecard exits **1** with **40/50 answer-shape failures**; the bill itself is **bounded, not
settled** — **`billed_tokens_known` 14,007, at most 14,303**, `billed_coverage` **0.99**: the **296** tokens
on turn **5** are unmeasured (`ABSENT ≠ 0`) and turn **1**'s 261 are settled by the cache mechanism (no
prior prefix), not by assumption — against **159,744 discounted**, with a **557**-token residual reported
inside a **1,740** tolerance. The gen-6 grid
verdict stays **`not_adjudicable`**, and the ledger stands at **7,969 spent / 4,125 remaining of 12,094**
(re-measured 2026-11-10; the 4,320 default cap in the ledger tool is exceeded and that is a decision, §6).
Two machine changes block the plan's own verification items and both are user decisions: the SGLang
relaunch with `--enable-hierarchical-cache`, and a single authorised remote root for the GX10. The app and
the paper track are dormant-but-intact; the **Consonance bounded-context research** remains filed with **0
live calls** and its comparative **`UNFUNDED`** (§2a).

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

## 1a. SPCC — the serving-context programme (current at 2026-11-10, nothing yet measured live)

**What exists, per deliverable, with the handoff that owns it:**

| Piece | State | Path / evidence |
|---|---|---|
| **Layer compiler** | built; five layers **L0 CONTRACT / L1 WORLD INDEX / L2 JOURNAL / L3 WORK / L4 CONTRACT-LINE**, `COMPACT_EVERY = 24`, `PtrPrefixDrift`; 5 tests pass | `experiments/ptr-engine/ptr_engine/layers.py`, spec `experiments/ptr-engine/research-seed-concepts/PROMPT-ENGINE-V1.md` (`U-SPCC-23.json`) |
| **`prefix_sha256` scope** | **`L0+L1`**, not `L0+L1+L2`: L2 is append-only, so hashing it cannot be identical across turns 1–24. L2 is the tail; compaction is the only permitted break | `U-SPCC-2C.json` `prefix_hash_decision` |
| **`spcc` arm** | **wired** — `ARM_SPCC`, `SpccArmState`, dispatch and stamping; an unwired first incarnation was caught and repaired; 26-turn offline stub run: `layer_tokens` on every row, one prefix break at turn 25, `epoch == 1`, `cached_tokens: null` where unreported | `experiments/ptr-engine/longrun/arm_cd.py`, `experiments/ptr-engine/longrun/run_longrun.py` (`U-SPCC-2C.json` `first_three_rows`, `prefix_and_compaction`) |
| **Launch contract** | `launch-sglang-spcc.sh` mirrors the captured invocation, adds `--enable-hierarchical-cache`, `--mem-fraction-static 0.45` (54.45 GB of a 121 GB pool), has a dry run and **refuses to start while a memory window exists** | `experiments/ptr-engine/serving/launch-sglang-spcc.sh` (`U-SPCC-4.json`, `U-SPCC-4B.json`) |
| **Fork decision** | **no fork** — none of the three gap criteria (per-range eviction protection, non-prefix reuse, per-range attribution) demonstrated by a failing run | [`docs/serving-options/FORK-DECISION.md`](serving-options/FORK-DECISION.md) (`U-SPCC-4.json`) |
| **Memory allowance** | a mechanism, not arithmetic: hard cgroup cap **60 GiB (`64424509440`)**, admission reserve **68 GB `MemAvailable`**, 2 s sampling; `VERIFIED` reachable **only** as the last resort of the chain `killed-by-supervisor → aborted → died-by-signal → peak-unknown → peak-exceeded-cap → unaccounted-unknown → mem-available-rose → VERIFIED`; 22 tests | `experiments/ptr-engine/serving/spcc_supervisor.py`, `experiments/ptr-engine/serving/MEM-WINDOW.schema.md` (`U-SPCC-5D.json` `final_chain`, `green_full_suite`) |
| **Pre-registration** | **E1–E6**, fixed order, a prediction written before each run, falsifier and request budget per experiment; **E6 gated on E1** | `experiments/ptr-engine/research-seed-concepts/PREREG-SPCC.md` (`U-SPCC-6.json`) |
| **Instrument** | `billing` block (`prompt_tokens`, `cached_tokens`, `uncached_tokens`, `billed_tokens`, `cached_fraction`, `coverage`, `attribution`), one-answer-per-checkpoint guard that fails loudly naming duplicated ids, `denominator_mismatch`, and `reconcile()` | `experiments/ptr-engine/longrun/score_longrun.py`, `experiments/ptr-engine/tools/request_ledger.py` (`U-SPCC-7.json`) |
| **Findings ledger** | 7 rows, every one traced to a source document; the masking claim corrected in place | `experiments/ptr-engine/research-seed-concepts/FINDINGS-LEDGER.md` (`U-SPCC-1.json`) |
| **Suite** | full directory **86 failed / 723 passed → 5 failed / 806 passed**; the v4-fixture cluster was closed after that count (three suites 28 passed) | `U-SPCC-9A.json` `full_directory`, `U-SPCC-9C.json` `three_suites_after` |

**Ledger, re-derived at close-out 2026-11-10:** **`spent 7,969`** of cap **12,094** (`PROJECT_QUOTA`,
`experiments/ptr-engine/longrun/cell.py:141`) ⇒ **4,125 remaining**. The count is a **row count over the 93
`rows-*.jsonl` files** in `experiments/ptr-engine/measure/`, which is the count of record because every
request writes a row; a later reader can re-derive it the same way. The 2026-11-09 reconciliation recorded
7,869 / 4,225 and `U-SPCC-LIVE.json` `store_after` records 7,969 / 4,125 after its 100 turns (Δ **+100**).
**The 4,320 default cap is exceeded by 3,649**, which is why `test_request_ledger::test_g` is red: a true
fact, not a test bug. (An intermediate `request_ledger.py` snapshot read 7,953 while the proof's rows were
still landing; it is not the count of record.)

**The live billed proof, exactly.** `orchestration/handoffs/U-SPCC-LIVE.json` (**done**, 2026-11-10T06:29)
ran `run_longrun.py --claim-mode plumbing --arms masking-no-fetch --fixture tasks-v7/TX-03.v1.json`:
**100 rows / 100 requests, 0 failed, 0 truncated, `finish_reason{"stop":100}`**. Its bill re-derives:
**prompt 174,047 · cached 159,744 · uncached 13,746 ⇒ cached/prompt 0.917821**; `cached_tokens` is `null`
on turns **[1, 5]** (`coverage 0.98`), and **557 prompt tokens are accounted as neither** (174,047 −
159,744 − 13,746). **The bill is a BOUND, not a measurement (`ABSENT ≠ 0`), after the stamping fix
(`U-SPCC-18`, no model call):** `billed_tokens_known` **14,007** (the established lower bound),
`billed_upper_bound_tokens` **14,303** (nothing cached on the unknown row), `billed_unknown_rows` **1**,
`billed_unknown_turns` **[5]**, `billed_coverage` **0.99** — **at most 14,303, with at least 14,007
established and 296 tokens on turn 5 unmeasured**. Per row: `prompt − cached` when the counter is
reported (`billed_source "reported"`); the whole prompt on turn 1 only (`"first-turn-no-cache"` — the
first request has no prior prefix, so `cached = 0` follows from the mechanism); and `null`/`"unknown"`
past turn 1, because a missing counter is **not** nothing-cached. `billed_tokens` is **never**
`uncached_tokens` and **never** `0`. The single ambiguous `cached_fraction` was **removed** in favour of
two named fields: `cached_fraction_of_prompt` **0.917821048337518** and `cached_fraction_of_accounted`
**0.920767767594674**. `reconcile_delta_total` **557** against tolerance **1,740** (1 % of prompt) —
**within tolerance true**; the residual is **reported, not asserted away**. **The bill is between 14,007 and
14,303; 159,744 is the discount** — 14,303 is the upper bound, not the charged quantity. **What it does not
prove:** the scorecard exits **1** with **40/50 checks failing on answer
shape (`kind NONE != NUM`)**, so this is a billing proof, not evidence that `masking-no-fetch` works on
`TX-03`. The landed score file `experiments/ptr-engine/measure/score-spcc-billedproof-2026-11-10.json` still
carries the stale `billed_tokens: 0` block; a landing unit refreshes it and it must not be cited.

**Not measured — do not read any of the above as a result.** No live `spcc` cell has run; the
memory window cannot currently be admitted (`MemAvailable` ~14 GB against a 68 GB reserve, so the
supervisor's correct answer is *refuse*). The compiler's own `cached_tokens`
are `null` wherever the endpoint did not report them.

**Blocked by a machine change nobody authorised:** plan verification item 7 needs the SGLang container
relaunched with `--enable-hierarchical-cache`; item 8 needs Nemotron weights on the GX10, and remote
writes are **blocked until the operator authorises one root**
(`experiments/ptr-engine/serving/REMOTE-ROOT.md`, `U-SPCC-4.json`).

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
- **Git:** branch `research/next-candidates-2026-10-24`, HEAD `17182ff`, remote
  `Aswin-Ram-K/research-publish-packages`. The pre-2026-11-09 backlog was committed as a preservation
  commit (`9fadcc9`, **2,665 files**: 54 modified, 2,001 untracked) and then merged with
  `research/paper-candidates-2026-11-04` (`afe4d78`); a small dirty/untracked layer remains (89 paths
  before this close-out's seven documentation files). The `origin/main` merge (`ca9d65e`) was **reverted**
  (`1977d30`, leaked tree removed `dfba6aa`, recorded `59c1c60`) after it leaked an unrelated tree;
  history was never rewritten. **Ancestry, measured 2026-11-10:** `origin/main` is at `5554d82` and **is an
  ancestor** of HEAD (`mergebase 5554d82`) — the earlier "shares no common ancestor" claim is false — and
  the branch's backup ref is `origin/backup/screened-dirty-progress-2026-11-10-1348`. **Neither merge
  advanced `origin/main`, so plan deliverable 0 is only half done.** HEAD is still a checkpoint, not the
  truth. `docs/CURRENT-REPO-STATE.md` (dated record) still carries the old `HEAD: dfba6aa` and the false
  ancestry sentence; it is outside this close-out's write paths and is named for its owner in
  `orchestration/handoffs/U-SPCC-CLOSE.json`.
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
   is **`UNFUNDED`**, with a **185-call pilot** as the funded alternative. Three mutually exclusive
   answers, all the user's (§2a). *Arithmetic refreshed 2026-11-10:* §2a's 4.37× was computed against the
   2,591 / 1,729 snapshot; against today's **4,125 remaining** the comparative is **7,560 / 4,125 = 1.833×**
   — still unfunded, but by 1.833, not 4.37.
8. **Authorise a remote root for the GX10 (Nemotron weights)** — remote writes are blocked until the
   operator names **one** root; plan verification item 8 cannot start before that (§1a,
   `experiments/ptr-engine/serving/REMOTE-ROOT.md`).
9. **Authorise the SGLang relaunch with `--enable-hierarchical-cache`** — a container change; without it
   plan verification item 7 is unproven and E1's cache boundary cannot be read on the serving side
   (`experiments/ptr-engine/serving/launch-sglang-spcc.sh`, `U-SPCC-4.json`).
10. **The 4,320 default budget cap** — **7,969 already spent** (a row count over the 93 `rows-*.jsonl`
    files), i.e. **3,649** over that default, while the live project quota (`PROJECT_QUOTA`,
    `experiments/ptr-engine/longrun/cell.py:141`) is 12,094 with **4,125** headroom. Either the default
    moves (and to what) or the ledger tool keeps reporting an over-budget fact.
    `test_request_ledger::test_g` is red on exactly this and must not be "fixed" by
    editing the constant (§1a).

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

---

## 11. What changed on 2026-11-09 … 2026-11-10 — the serving-context programme (SPCC)

**The plan that was executed:** `local://serving-context-programme-plan.md`, steps 0–7 plus suite repair,
by roughly thirty units (cards and handoffs `orchestration/units/U-SPCC-*.md`,
`orchestration/handoffs/U-SPCC-*.json`). Narrative: [`journal/2026-11-10.md`](../journal/2026-11-10.md).

**Landed**

- **Preservation** — one commit over the whole uncommitted backlog (`9fadcc9`, **2,665 files**), merge of
  the paper-candidates branch (`afe4d78`); the row store verified as growth, not corruption (**92 files,
  7,869 rows, 0 exact duplicates, 123 manifests** — `U-SPCC-0B.json` `row_tallies`; the store is now
  **93 files / 7,969 rows** after the live proof's 100 turns).
- **The leaked-tree merge, reversed** — `origin/main` was merged accepting (`ca9d65e`) with
  `--allow-unrelated-histories` and introduced an unrelated tree (a vendored `api_server.py`, removed in
  `dfba6aa`); it was then **reverted** (`1977d30`) and the repair recorded (`59c1c60`). History was not
  rewritten. **Corrected 2026-11-10:** `origin/main` **is** an ancestor (`mergebase 5554d82`) — the
  "unrelated root / different project" claim is false — and neither merge advanced `origin/main`, so
  deliverable 0 is **half done** (§5).
- **Findings ledger** — `experiments/ptr-engine/research-seed-concepts/FINDINGS-LEDGER.md`, seven rows,
  every row checked against a source document (`U-SPCC-1.json`).
- **Compiler** — `experiments/ptr-engine/ptr_engine/layers.py`; `prefix_sha256` over **L0+L1** with L2 as
  the append-only tail (a deliberate correction of the plan's impossible requirement); spec
  `PROMPT-ENGINE-V1.md`.
- **The `spcc` arm, wired** — `experiments/ptr-engine/longrun/arm_cd.py` + `run_longrun.py`; a first
  incarnation that never called `compile_prompt` was caught and repaired; 26-turn offline stub proves
  stamping and exactly one prefix break (turn 25) (`U-SPCC-2C.json`).
- **Serving** — `experiments/ptr-engine/serving/launch-sglang-spcc.sh` (dry run, hierarchical cache flag,
  memory-window refusal), [`docs/serving-options/FORK-DECISION.md`](serving-options/FORK-DECISION.md)
  (**no fork**), and `experiments/ptr-engine/serving/REMOTE-ROOT.md` (remote writes **blocked**).
- **Allowance** — `spcc_supervisor.py` + `MEM-WINDOW.schema.md`: 60 GiB hard cap, 68 GB admission reserve,
  2 s sampling, `VERIFIED` only as the chain's last resort; 22 tests (`U-SPCC-5D.json`).
- **Pre-registration** — `PREREG-SPCC.md`, E1–E6 in fixed order, E6 gated on E1.
- **Instrument** — billing block, one-answer-per-checkpoint guard, `denominator_mismatch`, `reconcile()`;
  the published **42/48** re-scored unchanged and rows reconciled 7,869 = 7,869 (`U-SPCC-7.json`).
- **Suite** — **86 failed / 723 passed → 5 failed / 806 passed**; stale tests were diagnosed, not
  loosened (exit 14 is `EXIT_CAPGATE_UNRECORDED`; the `run_id` builder always appends `-r{rep}`; the
  session-poisoning socket monkeypatch was removed from import and armed in `setup_module`); derived
  artefacts regenerated by their real generators (`STOP-REASON.json`, `VERBOSITY.json`, `FALSE-PASS.json`
  3→19) (`U-SPCC-8/9A/9B/9C`).

**Corpus-wide fixture provenance (`U-SPCC-30`, 2026-11-10).** Hashing every on-disk
`consonance.longrun-fixture` document (**53 distinct digests**) against every `fixture_sha256` pinned in
`experiments/ptr-engine/measure/rows-*.jsonl` (**7,734 pinned rows across 93 files**; 7,969 rows total,
235 unpinned) finds **1,368 rows in 13 files pinning a digest with no on-disk match** — 17.7% of the
pinned corpus, six distinct digests. **80 of 93 files have zero missing pins**; all 13 affected files are
first-generation AGG/HOP/SUP/LR-01 runs, each superseded by a later generation whose digest is on disk.
Of the 1,368 lost rows, **1,272 are unrecoverable** (pinned bytes never committed) and **96 are
recoverable** from git blob `f17663d1fed0`. The correct reading is **fixture available**, not
reproducible: a matching digest proves only that the fixture bytes are present on disk. For every file,
replay is unverified — no run in this corpus has been re-executed from its pinned fixture and compared
row-for-row, so "fixture available" must not be read as "reproducible". Full table and per-file evidence:
`experiments/ptr-engine/research-seed-concepts/FINDINGS-LEDGER.md` §Corpus-wide fixture provenance.

**Corrections recorded** — masking is **12/48 on `:8012` and 8/48 on `:8014`**, all successes in the d=2
bucket (**0/36 beyond distance 2** on the 12/48 arm; **0/40** on the 8/48 arm, from `d5`/`d6`/`d8`/`d20`/
`d32` × 8), not "0/48 on both stacks". **Why: the mask fires at `intro+4`** (`WINDOW_TURNS = 4`), i.e.
before every `d5`/`d6`/`d8`/`d20`/`d32` probe, so those probes ask about a fact the prompt no longer
carries — the cliff is **content absence**, confirmed by re-materialising all 100 turns byte-identically
and finding **0 occurrences** of the expected value in each of the 40 failing prompts
(`experiments/ptr-engine/research-seed-concepts/FINDINGS-LEDGER.md` row 22;
`experiments/ptr-engine/measure/answer-shape-diagnosis-TX03.md`). Position (depth) remains **untested on
this arm**: those prompts do not contain the value at any position, so they cannot show where a present
value sits; E3 (`experiments/ptr-engine/research-seed-concepts/PREREG-SPCC.md`) keeps the body present and
varies distance. The TX-03 scorecard counters are
`answered_correctly 8`, `abstained_after_mask 40`, `answered_wrong 0`, `unparsed 0`, `total 48`;
`abstained_after_mask` is **legitimate arm behaviour** and is **not** counted as correct, so
`checkpoint_accuracy` stays **8/48**; D-086's source is `MEASURED_FACTS.md` F3;
the ledger is **7,969 spent / 4,125 remaining** (row count over 93 `rows-*.jsonl` files; not the 7,869 /
4,225 reconciled earlier, and not the 7,953 of a mid-write snapshot); the 5-failure
suite count is a point-in-time figure (the v4-fixture cluster was closed after it).

**Still red, each for a stated reason** — the ledger over-budget test (a true fact against the 4,320
default), `test_lost_fixture` (rows pin a fixture that is not on disk; row files out of bounds),
`test_journal_lint` (290 new unjournaled handoffs; writing them now would fabricate history),
`test_verdict_ritual::LiveLedgerTest` (six unverdicted closures; a backfill unit owns it).

**Live billed proof — DONE, plumbing only** (`orchestration/handoffs/U-SPCC-LIVE.json`): 100 turns, 0
failed, 0 truncated; prompt **174,047**, cached **159,744**, uncached **13,746**, cached/prompt
**0.917821**, billed **between 14,007 and 14,303**; `null` cached on turns **[1, 5]** only; **557** prompt
tokens accounted as neither. After the stamping fix (`U-SPCC-18`): `billed_tokens_known` **14,007**,
`billed_upper_bound_tokens` **14,303**, `billed_unknown_rows` **1** (turn **5**, 296 tokens — turn 1's 261
follow from the cache mechanism), `billed_coverage` **0.99**,
`cached_fraction_of_prompt` **0.917821048337518**, `cached_fraction_of_accounted` **0.920767767594674**,
`reconcile_delta_total` **557** within tolerance **1,740** — **at most 14,303 charged, 159,744
discounted**, 557 residual reported. **Open on it:** the scorecard exits **1** with 40/50 answer-shape failures, so it
licenses the billing account and nothing about accuracy. The machine blockers (SGLang relaunch, remote
root, 68 GB reserve) are unchanged by this proof.

## Measured noise floor — temperature 0 + seed 42 is not a reproducibility contract (2026-11-10)

`U-SPCC-45` compared two runs of the **same** arm on **byte-identical** prompts:
`experiments/ptr-engine/measure/rows-e1-spcc-2026-11-10.jsonl` (commit `e18a587`) against
the `spcc` rows of `experiments/ptr-engine/measure/rows-e1-final-2026-11-10.jsonl` (commit
`e4692f8`). `prompt_sha256` and `prompt_tokens` are equal at all 100 turns; `fixture_sha256`
is identical (`f0a636fe…`). The answers still differ at **6 of 100 turns** — T5, T41, T52,
T57, T60, T80 — and **2 of those are scored checkpoints**: T57 `cp.TX-03.f06.d5` (A `NONE`,
B `NUM 3501`) and T60 `cp.TX-03.f06.d8` (A `NONE`, B `NUM 3503`). Those two turns are the
**entire** 20/48→22/48 value delta and the entire 19/48→21/48 contract delta.

Mechanism: `cached_tokens` differ at **26 of 100 turns** on identical prompts (79,808 vs
81,024 total; 22 of 26 higher in B), so prefix-cache occupancy and batch composition
differed between the runs. `git log e18a587..e4692f8` touches only `run_longrun.py`, and no
hunk is in `Planner` (`run_longrun.py:1474`) or any prompt-construction code; the `run_cell`
hunks are the `CapRefusal`/`BudgetExhausted` exits and neither fired (`error=None`,
`cap_refused_mid_turn=None` on all 200 rows).

**The measured band:** per-turn flip rate **6/100 (6 %)**; per-scored-checkpoint flip rate
**2/48 (4.2 %)**; run-to-run spread on the headline metric **±2/48 = ±4.2 pp**. A
2-checkpoint gap is **1.41 sd** of a two-run difference (two-sided p ≈ 0.16) — not
significant.

**Power.** At 48 checkpoints and the measured checkpoint flip rate, 80 % power to resolve a
2-checkpoint difference needs **4 reps** (1,200 requests for 3 arms × 100 turns); at the
more conservative turn-level rate it needs **6 reps** (1,800 requests). E1 ran at `reps=1`
(300 requests), so **`reps=1` is underpowered by construction** and every E1 arm-to-arm
difference below ~4 pp is inside the noise band.

**E1's clauses re-read against the band** (the prereg's prediction and falsifier are
unedited; this is a reading, not a revision):

| clause | observed | vs band | verdict |
|---|---|---|---|
| `spcc` ≥ fetch on single-fact | fetch arm degenerate (never fetched) | — | **unadjudicable** (unchanged) |
| `spcc` > masking **everywhere** | `d2` 6/8 vs 8/8 (contract), `d32` 0/8 vs 0/8 | `d2` gap is −2 = exactly the measured flip magnitude | **not adjudicable** — inside the band, not a clean falsification |
| billed ≤ masking | 9,066 vs 9,730 (answer turns only) | 664-token gap vs 1,216-token cache-driven variation on identical prompts | **not adjudicable** — inside the band |
| `spcc` > masking on the aggregate | 22/48 vs 8/48 | 14 checkpoints = 7× the band | **survives** |
| falsifier "not strictly above masking on any class" | `d5` 4>0, `d6` 5>0, `d8` 4>0, `d20` 2>0 | gaps of 4–5, outside the band | **did not fire** (unchanged) |

**Open decision (operator).** Whether E1's 200–500 request ceiling and its `reps=1` shape are
amended to admit a powered design. A powered E1 costs 1,200–1,800 requests against a live
ledger headroom of **3,682** (raw; 3,712 deduplicated), so it fits — but it is 2.4–3.6× the
preregistered ceiling. Not decided here.

## U-SPCC-51 — the corrected three-arm E1 cell: retention, not mechanism

`measure/rows-e1-tools-2026-11-10.jsonl`, commit `08a7908`, 318 requests, 0 failed, 0
truncated, reconciliation delta **0** on all three arms (`spcc` 8,381→8,481/100, `masking`
8,481→8,581/100, fetch 8,581→8,699/118). Programme spend **8,699 of 12,094**. This is the
first E1 cell where the fetch channel was actually on: `tools_mode: on:read_file` and
`tools_schema_sent=true` on all 100 `spcc` and all 118 fetch rows (`masking` `off`/`false`).

| arm | value | contract | NONE | wrong | unparsed | graded | requests |
|---|---:|---:|---:|---:|---:|---:|---:|
| `spcc` | 22 | 21 | 26 | 0 | 0 | 48 | 100 |
| `masking-no-fetch` | 8 | 8 | 40 | 0 | 0 | 48 | 100 |
| `bounded-context-fetch` | 22 | 22 | 11 | 4 | 11 | 48 | 118 |

18 of 48 fetch rounds were used; 18 checkpoints answered on a follow-up carrying a fetched
body, 15 of those 18 correct; `fetch_prompt_serves=0`.

**Gaps against the measured ±2/48 band.** `spcc`−masking **+14 value / +13 contract**
(outside). fetch−masking **+14 / +14** (outside). **fetch−`spcc` 0 value / +1 contract —
inside the band.** The two retention mechanisms are **not separable on this cell**.

**The claim.** The effect is **retention, not mechanism**. Masking destroys the body at turn
4; the stable-prefix journal and fetch-on-demand both keep it reachable, and both land at
22/48. Neither is separable from the other. Both fail at `d32` together (`spcc` 0/8, fetch
1/8, masking 0/8).

**Four caveats that travel with every figure above.**

1. The fetch arm's 22 is a **floor**, not a ceiling. 10 of its 48 checkpoints ended on
   `finish_reason=tool_calls` with `content ''`, `tool_calls []`, `tool_call_ids null` and no
   follow-up — a harness capture bug, not model behaviour. A fix is in flight (`U-SPCC-49`).
2. The rows carry **pre-fix** `fetch_rounds_used` stamps (0 on 52 rows, null on 66) because
   the counter was dead at `run_longrun.py:3359`; the corrected counter (`a9b9b70`) only
   appears on the next cell. The rows must not be rewritten.
3. 16 rows carry `protocol_violation=answer_wrapped_tool_call` on fetch-arm turn-initial
   rows; each has a matching turn row that did fetch, so none stranded. Still open.
4. Temperature 0 plus seed 42 is not reproducible on this endpoint (±2/48 measured); every
   figure above is a single-rep point estimate with that band.

`PREREG-SPCC.md` is **unedited** — the prereg stays as written.

## U-SPCC-57 — the final E1 cell: the fetch arm's 48/48 is a lookup score, not a retention score

`measure/rows-e1-indexfix-2026-11-10.jsonl`, commit `2e22310`, 343 requests, 0 failed, 0
truncated, reconciliation delta **0**. Programme spend **9,367 of 12,094**; headroom **2,727**.

| arm | value | contract | NONE | wrong | unparsed | requests | billed |
|---|---:|---:|---:|---:|---:|---:|---:|
| `spcc` | 20 | 19 | 27 | 1 | 0 | 100 | 17,187 |
| `masking-no-fetch` | 8 | 8 | 30 | **10** | 0 | 100 | 18,724 |
| `bounded-context-fetch` | **48** | **48** | 0 | 0 | 0 | 143 | 51,715 |

Buckets sum to 48 on all three arms.

**The finding, stated exactly.** The fetch arm's 48/48 is a **lookup score, not a retention
score**. 41 of its 48 checkpoints were answered by fetching the fact body **in the same turn
the question was asked** — the initial response carries the question, emits the fetch, and
the follow-up answers from the body. Prefetch (fetching before delivery) is **0**, so the
specific prefetch concern did not trigger; the model simply never retains anything. Only
**7** checkpoints are genuine retention successes (`f01.d2`, `f03.d2`, `f01.d32`, `f03.d20`,
`f05.d2`, `f07.d2`, `f07.d8`).

Therefore **`spcc`-vs-fetch is not a retention comparison** and must not be reported as one.
The correct statement is: when lookup is available on the question turn, retention is
unnecessary; the fetch arm answers everything and costs **3.0× `spcc`'s billed tokens**
(51,715 vs 17,187).

**Five secondary findings that travel with the table.**

1. **`NOT_FOUND` collapsed 12 → 0.** Every fetch attempt used an advertised
   `doc-fact-NN@r1`. The index fix (`b38db8a`) reached the model.
2. **The masking arm's wrong answers went 0 → 10** (turns 6, 7, 9, 13, 14, 22, 23, 25, 29,
   30) while its value score stayed 8. The index now advertises 13 refs where it previously
   advertised 1, so the masking arm sees fact names it cannot fetch and confabulates values
   instead of answering `NONE`. This is a side effect of the index fix on an arm that cannot
   use it, and a finding in its own right: **advertising addressable refs to an arm that
   cannot address them converts abstention into confabulation.**
3. **The multi-round loop is dead code in practice.** `max(fetch_rounds_this_turn) == 1`
   because the model batches all calls into one response. Multi-REF servicing does work
   (`fetch_rows` reaches 3 at turn 21, 2 at turn 28). `cp.TX-03.f04.d8` (turn 32) is now
   serviced and correct (`NUM 3303`).
4. **Billed rose on every arm** because the index is 13 lines instead of 1: `spcc` +15.9 %,
   masking +33.7 %, fetch +26.2 %. All outside the ±2/48 band on value, but the billed
   changes are a prompt-size effect, not a treatment effect.
5. **The index fix changed the prompt bytes for all three arms**, so no cell before
   `b38db8a` is comparable to this one. The `spcc` 21 and fetch 17 from `c73dfc4` are
   superseded, not replicated.

**The verdicts.**

- `spcc` > masking aggregate: **survives** — 20 vs 8, +12, outside the band.
- `billed ≤ masking`: **FALSIFIED** — `spcc` 17,187 vs masking 18,724 is now *below*, but the
  direction flipped between cells (+2,868, +820, −1,537), so the honest statement is that the
  billing comparison is **unstable** and no direction is established.
- `spcc` ≥ fetch: **falsified on the number, void as a retention claim** — fetch 48 vs `spcc`
  20, but by lookup.
- Falsifier: fired in the earlier cells on billing; in this cell `spcc` bills *less* than
  masking, so it does not fire here. Record the instability rather than picking a cell.

`PREREG-SPCC.md` and its companion JSON are **unedited**.
