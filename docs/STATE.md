# STATE — the current state of this workspace

**Last updated:** 2026-11-11 · **By:** the crash-recovery close-out of `U-SPCC-69`…`U-SPCC-73` (manifests committed, derived artefacts regenerated, `--preview-root` added; corpus re-measured at **103 files / 10,167 rows**, so the ledger headroom is **1,927**, not 4,125), then the compaction/cache design and E7's pre-registration (§1a, 0 requests)
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
verdict stays **`not_adjudicable`**, and the ledger stands at **10,167 spent / 1,927 remaining of 12,094**
(re-measured 2026-11-11 over **103** `rows-*.jsonl` files; the 4,320 default cap in the ledger tool is
exceeded by **5,847** and that is a decision, §6).
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

**Ledger, re-derived 2026-11-11:** **`spent 10,167`** of cap **12,094** (`PROJECT_QUOTA`,
`experiments/ptr-engine/longrun/cell.py:141`) ⇒ **1,927 remaining**. The count is a **row count over the
103 `rows-*.jsonl` files** in `experiments/ptr-engine/measure/`, which is the count of record because every
request writes a row; a later reader can re-derive it the same way (`wc -l`). The 2026-11-09
reconciliation recorded 7,869 / 4,225, `U-SPCC-LIVE.json` `store_after` records 7,969 / 4,125 after its
100 turns, and the 2026-11-10 units `U-SPCC-62`/`64`/`68` added the E2 and E3 cells that take the store to
10,167 / 1,927 (Δ **+2,198** over ten new rows files).
**The 4,320 default cap is exceeded by 5,847**, which is why `test_request_ledger::test_g` is red: a true
fact, not a test bug. (An intermediate `request_ledger.py` snapshot read 7,953 while the proof's rows were
still landing; it is not the count of record.)

**`REQUEST-LEDGER.json` is stale and cannot be rebuilt as things stand.** The file records `requests_raw
2591` over `files_deduped 38 + files_not_applicable 3 = 41` rows files; the corpus is **103** files.
`tools/request_ledger.py --write --cap 4320` refuses with exit **4**,
`OVER BUDGET: spent=10167 + would_spend=0 = 10167 > cap=4320 - reserve=0 = 4320 (over by 5847)`, so the
derived artefact cannot be regenerated without a cap decision (§6 item 10). Its 2,591 is the tool's own
*billed-request* rule (kinds `turn`, `tool-followup`, `turn-initial`, `digest`), not a row count, and the
test's 10,167 is the raw row count: the two numbers are different measures of the same corpus, and the
disagreement is an instrument question for the operator, not a defect either side can fix alone.

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

**Compaction/cache design, written 2026-11-11 (0 requests).** `docs/COMPACTION-CACHE-DESIGN.md` reframes
the fold: its cost is **not** the prefix re-prefill (measured **86 layer units over 100 turns = 0.05 %**
of 156,390 prompt units) and **not** the token saving (drop-journal saves **6.38 %** at L0 = 1,515,
**1.73 %** at 6,060, **0.88 %** at 12,120 — the absolute saving is constant, so its share collapses as
the fixed prefix grows). The cost is the **re-fetch** that lost information causes: one extra request at
~5,448 prompt tokens + ~179 output (`rows-longrun-v5-tools.jsonl`, 24 `tool-followup` rows of 72).
**A cached token is billed at zero here** — `billed_of` (`score_longrun.py:144-190`) computes
`billed_tokens = prompt_tokens − cached_tokens`, and over 300 rows of
`rows-e2-turnover-2026-11-10.jsonl` the sums are prompt 476,697 / cached 431,680 (90.6 %) / billed
44,426 — so a pin in the cached prefix costs **0 marginal units** on this endpoint and 480 at the
Anthropic/OpenAI 0.1× read price, against a re-fetch's ~1,627. The design's conclusion is therefore
**invariant across the whole plausible cache-price range**. The design adds a `PINS` layer between L0
and L1, makes the fold record a **pin in PINS** (`P<n>|fold|T24|24 turns dropped at epoch 1`) so it
persists on every later turn and extends the cached prefix instead of rewriting it, makes PINS and L1
append-only with tombstones, and forbids summarising (a summary is a full prompt read + output + a
prefix rewrite, is lossy, and 27 measured summaries carried self-injected instructions). Prior art
folded in 2026-11-11 **confirms the design with numbers**: CONPACT (arXiv:2608.11242) measures
compactors retaining **17 %** of side constraints with a forbidden delete in **30/100 sessions after
compaction vs 0 before**, while a separate constraint store reaches **>90 %**; The Missing Boundary
(arXiv:2609.11024) measures **0 %** vs **87 %** loss of control depending on whether control constraints
survive; `openai/codex#25792` records progress **97 % → 42 %** after compaction. It also added four
rules now in §5.2: cap the pin block and **refuse** on overflow (never truncate), stamp every pin with
its turn, supersede rather than overwrite, and sanitise pins written from tool output (the Pillar
"Rules File Backdoor" / CVE-2025-54135 injection surface). E7's pre-registration is
`experiments/ptr-engine/research-seed-concepts/PREREG-COMPACTION.md`: four arms
(`spcc` / `pinned-compact` / `pinned-summary` / `no-compact`), five predictions, four falsifiers, a
two-stage 1,000-request budget. **It cannot run yet** — the cap decision (§6 item 1) gates it, and the
live-cell preview hazard (§6 item 13) must be closed first. Two instrument facts it recorded:
`cell.py:130-136` `HARNESS_FILES` does **not** include `arm_cd.py` or `ptr_engine/layers.py`, so an edit
to the arm or compiler mid-run would not change the harness digest; and `test_gate_arm_count.py` stops a
cell at **500 real requests**, so the 600-request stage 2 was split into 200 + 400.

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
   answers, all the user's (§2a). *Arithmetic refreshed 2026-11-11:* §2a's 4.37× was computed against the
   2,591 / 1,729 snapshot; against today's **1,927 remaining** the comparative is **7,560 / 1,927 = 3.923×**
   — still unfunded, and by more than the 1.833× recorded on 2026-11-10, because the E2/E3 cells spent
   2,198 requests in between.
8. **Authorise a remote root for the GX10 (Nemotron weights)** — remote writes are blocked until the
   operator names **one** root; plan verification item 8 cannot start before that (§1a,
   `experiments/ptr-engine/serving/REMOTE-ROOT.md`).
9. **Authorise the SGLang relaunch with `--enable-hierarchical-cache`** — a container change; without it
   plan verification item 7 is unproven and E1's cache boundary cannot be read on the serving side
   (`experiments/ptr-engine/serving/launch-sglang-spcc.sh`, `U-SPCC-4.json`).
10. **The 4,320 default budget cap** — **10,167 already spent** (a row count over the 103 `rows-*.jsonl`
    files), i.e. **5,847** over that default, while the live project quota (`PROJECT_QUOTA`,
    `experiments/ptr-engine/longrun/cell.py:141`) is 12,094 with **1,927** headroom. Either the default
    moves (and to what) or the ledger tool keeps reporting an over-budget fact — and while it reports it,
    `tools/request_ledger.py --write` exits 4, so **`REQUEST-LEDGER.json` cannot be regenerated at all**
    and stays at its 41-file / 2,591-request snapshot (§1a). Every further measured cell is gated behind
    this: the launcher's `RUN-A RECONCILE` reads the same ledger. `test_request_ledger::test_g` is red on
    exactly this and must not be "fixed" by editing the constant (§1a).
11. **The journal-lint baseline** — the live census reports `new_misses=360` against a frozen baseline
    that exempts 1,017 (`state/logs/U8.15/baseline_gaps.json`). Backfilling 360 journal entries would
    fabricate history; the alternatives are (a) accept a re-frozen baseline that records the 360 by name
    as known history debt, or (b) backfill only those with a real source document. This is an operator
    call because it changes what "the record is complete" means.
12. **The handoff-shape baseline** — `tests/test_orchestration_handoffs.py` is red on **49** unit-shape
    gaps that the 2026-10-24 frozen baseline (`state/logs/U8.15/baseline_gaps.json`) never covered;
    the files were committed by the preservation commit `9fadcc9`. Either re-freeze the baseline naming
    the 49 as known history debt, or repair the 49 docket-era handoffs to the seven-key shape. The
    first erases the guard's meaning if done silently; the second rewrites history. Measured
    2026-11-11: `2 failed / 28 passed`, and the handoff written that day (`U-SPCC-74.json`) is not
    among the gaps.
13. **Where a live cell's previews go** — `experiments/ptr-engine/longrun/cell.py:411` builds
    `argv = [sys.executable, RUNNER, "--dry-run", "--fixture", args.fixture, "--arms", args.arm,
    "--reps", str(args.reps)]` with **no** `--preview-root`, and `stage_budget` runs on every **live**
    cell. So every live cell overwrites the tracked
    `experiments/ptr-engine/state/previews/<task>/<arm>/turn-*.json` for its own task and arm — the
    same defect class `U-SPCC-73` closed in the tests, one layer up, on the production path.
    **Recommended default:** a run-scoped directory under the gitignored `state/`
    (`state/previews/<run_id>/`), so a live cell keeps its prompt bodies as scratch and the committed
    previews stay the evidence of the run that produced them. Not changed without this decision,
    because it changes what evidence a live cell leaves behind.
14. **How `spcc` gets the tool channel** — E7's arms B and C are `spcc` variants, and `refetch_count`
    is E7's primary mechanism, but `run_longrun.py:3919` services tool calls only for arms **not in**
    `(arm_cd.ARM_C, arm_cd.ARM_D, arm_cd.ARM_SPCC)`, so **`spcc` does not service tool calls today**.
    The only tool-enabled rows in the corpus are `pointer-stable` (`rows-longrun-v5-tools.jsonl`, 72
    rows). Two routes: **(a)** remove `ARM_SPCC` from that exclusion and add it to
    `arm_requires_tools` (`run_longrun.py:3367-3369`) — one line plus a predicate, keeps the layer
    compiler as the single place a fold is defined; **(b)** build arms B and C on `pointer-stable` and
    port the layer compiler into it — larger, keeps `spcc` as it is. **Recommended: (a).** This is an
    operator call because it changes what `spcc` is, and E7 cannot measure its own hypothesis until it
    is settled.

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

**Late units of the same day — `U-SPCC-69`…`U-SPCC-73` (commits `286e2df`…`de048d6`, journaled
2026-11-11).** These ran after the close-out above and were left unjournaled when the session died; the
record is now in [`journal/2026-11-10.md`](../journal/2026-11-10.md) under their own headings.

- **`U-SPCC-69`** — `experiments/ptr-engine/longrun/manifests/` held **23** untracked files (the ticket
  said 39): 6 dry-run scratch + 17 completed-run manifests. The 17 were committed after every
  `rows_path` resolved and every `run_id` was found in its rows file; the 6 `dryrun-*` were deleted.
- **`U-SPCC-70`** — three handoffs (`U-SPCC-26`, `U-SPCC-45`, `V-SPCC-36`) and two unit cards that
  earlier units wrote but never committed were committed; dry-run previews and refusal scratch cleared.
- **`U-SPCC-72`** — `measure/STOP-REASON.json`, `measure/VERBOSITY.json` and `docs/VERBOSITY.md`
  regenerated by their real generators over the current corpus (`rows 10167, answered 8772, empty 1395`;
  `cells=128 p95_ok=50 refused=75 decomp=36 fits=93`, `VERDICT confound_immaterial`). Four corpus-drift
  tests went green; the directory stands at **2 failed / 929 passed**.
- **`U-SPCC-73`** — `--preview-root` added to `experiments/ptr-engine/longrun/run_longrun.py`
  (`:4321-4324`, dispatch `:4700`). The defect it closes: `run_dry(..., root=None)` at `:3199` defaulted
  to `preview_root(fixture["task_id"])` (`:3201`), the **tracked** tree, so a test dry run overwrote six
  committed `experiments/ptr-engine/state/previews/LR-01/*` files with an emptied `INDEX` block. Three
  further `--dry-run` call sites (`test_cell_gates.py:322`, `test_tool_channel2.py:289`,
  `test_wire_client.py:348`) still pass no `--preview-root` and are the next unit.

**Suite state after them (measured 2026-11-11, live checkout):** `test_verdict_ritual.py` **10 passed**
(the six unverdicted closures are settled); `test_journal_lint` **red** at `new_misses=360`
(`exempt_frozen=1017`); `test_request_ledger::TestRealCorpus` **red** at
`spent=10167 > cap=4320 (over by 5847)`; `tests/test_orchestration_handoffs.py` **red** at
**2 failed / 28 passed** — `A2-FIX.json` carries no status/verdict/result/overall key, and **49**
unit-shape gaps sit outside the 2026-10-24 frozen baseline (`state/logs/U8.15/baseline_gaps.json`
contains none of them; the files were committed by the preservation commit `9fadcc9`). All three reds
are operator decisions (§6 items 10–12), not code defects. A fresh worktree reports `new_misses=1377`
for the journal-lint test because `state/logs/U8.15/baseline_gaps.json` is gitignored and absent
there — **the worktree cannot run that guard**, which is why this close-out was done in the live
checkout.

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

## U-SPCC-58 — the masking arm's 10 wrong answers are confabulation, not index leakage

`U-SPCC-58` classified the 10 wrong answers in the `masking-no-fetch` arm of
`experiments/ptr-engine/measure/rows-e1-indexfix-2026-11-10.jsonl` (index fix `b38db8a`):
**9 pure confabulation, 1 cross-fact confusion, 0 index leakage**. The answered values occur
in no index line and no fixture body. The masking arm's **8/48 retention score is unchanged
and fair**; the **0→10 wrong count is a prompt-design artefact** of showing the arm an index
it cannot address, and must not be read as an arm property.

All 100 masking prompts were rebuilt through `Planner.build` + `checkpoint_prompt` with
**100/100 `sha256` match**, so the reconstruction is exact.

| turn | checkpoint | expected | answered | class | source |
|---:|---|---:|---:|---|---|
| 6 | `cp.TX-03.f01.d5` | 3001 | 4000 | pure confabulation | nowhere |
| 7 | `cp.TX-03.f01.d6` | 3002 | 5000 | pure confabulation | nowhere |
| 9 | `cp.TX-03.f01.d8` | 3003 | 3103 | cross-fact confusion | `doc-fact-02` body in L3, delivered T8 |
| 13 | `cp.TX-03.f02.d5` | 3101 | 4100 | pure confabulation | nowhere |
| 14 | `cp.TX-03.f02.d6` | 3102 | 4103 | pure confabulation | nowhere |
| 22 | `cp.TX-03.f03.d5` | 3201 | 4200 | pure confabulation | nowhere |
| 23 | `cp.TX-03.f03.d6` | 3202 | 4203 | pure confabulation | nowhere |
| 25 | `cp.TX-03.f03.d8` | 3203 | 4203 | pure confabulation | self-echo of its own T23 answer |
| 29 | `cp.TX-03.f04.d5` | 3301 | 4300 | pure confabulation | nowhere |
| 30 | `cp.TX-03.f04.d6` | 3302 | 4303 | pure confabulation | nowhere |

Counts: **9 pure confabulation, 1 cross-fact confusion, 0 index leakage**. The 8 correct
turns (3, 10, 19, 26, 47, 54, 63, 70) are identical in both cells and all `d2`; the 10
flipped turns were `NONE` in `rows-e1-parserfix-2026-11-10.jsonl`. No value leaked from the
index — the index carries ref names, a digest and a byte count only; the index leaked only
names the question already states.

## U-SPCC-62 — E2: compaction interval trades cost against accuracy, and the "accuracy flat" prediction is falsified

`PREREG-SPCC.md` §E2 asks whether a larger compaction interval lowers rewrite cost with no
accuracy loss until the interval exceeds the distance at which facts stop being refetched.
`f4de200` (U-SPCC-59) made `COMPACT_EVERY` a cell dimension; this is the first cell that
varies it. One cell, three arm-variants of `spcc`, same fixture, same model, only the
interval varying:

```
--fixture tasks-v7/TX-03.v1.json --arms spcc --compact-every 12,24,48 --reps 1
--temperature 0 --seed 42 --model occamy-1.0 --base-url http://192.168.2.168:8012/v1
--claim-mode E2 --budget-cap 12094 --run-id e2-compact-2026-11-10
--rows experiments/ptr-engine/measure/rows-e2-compact-2026-11-10.jsonl
```

300 rows, 300 requests, 0 truncated, 0 failed turns, wall 120.78 s, cap-gate reconcile
delta 0 (spent 9,367 → 9,667 of 12,094).

| C | value_correct | contract_correct | NONE | wrong | unparsed | graded | total | requests | billed_tokens | compactions |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 12 | 18/48 (37.5%) | 18/48 (37.5%) | 28 | 2 | 0 | 48 | 48 | 100 | 16,655 | 8 |
| 24 | 20/48 (41.7%) | 17/48 (35.4%) | 28 | 0 | 0 | 48 | 48 | 100 | 15,807 | 4 |
| 48 | 36/48 (75.0%) | 34/48 (70.8%) | 12 | 0 | 0 | 48 | 48 | 100 | 15,703 | 2 |

**Cost.** 16,655 → 15,807 → 15,703 billed tokens, monotone falling: −848 (−5.09%) from
C=12→24, −104 (−0.66%) from C=24→48, total −952 (−5.72%). Almost all of the fall is in the
first step; C=24→48 is within noise of flat.

**Accuracy.** Value 37.5% → 41.7% → 75.0%; contract 37.5% → 35.4% → 70.8%. Band ±2/48 =
±4.2 pp. C=48 is +33.3 pp over C=12 on value — far outside the band.

**The falsification.** The hypothesis's "accuracy flat" prediction is **falsified**:
accuracy is not flat, it rises by 33.3 pp from C=12 to C=48. Compaction is not
accuracy-neutral at small C — it is accuracy-destructive. The mechanism is visible in the
NONE column, 28 → 28 → 12: compaction evicts fetched bodies, so more frequent compaction
produces more abstentions, not more wrong answers (wrong is 2, 0, 0). The turnover point the
hypothesis predicts — larger C eventually hurting — was not reached inside {12,24,48}.

**Deepest passing distance** moves with C: 8 → 20 → 32. Per-distance value passes (out of 8
per distance) are C=12 7/4/4/3/0/0, C=24 7/4/4/3/2/0, C=48 8/5/7/6/6/4 at
d2/d5/d6/d8/d20/d32. The refetch horizon is set by the compaction interval, not by a
fixture property.

**Control.** No compaction fired mid-turn; every increment lands on a turn boundary — C=12
at 13,25,37,49,61,73,85,97 (8); C=24 at 25,49,73,97 (4); C=48 at 49,97 (2). First fire at
13/25/49 matches the verified U-SPCC-59 prediction.

**Falsifier.** *Cost does not fall monotonically* — not triggered; *accuracy drops before
the predicted distance* — not triggered (accuracy never drops as C grows, it rises). The
falsifier is not triggered, but the hypothesis's own "accuracy flat" prediction is
falsified.

## U-SPCC-64 — E3: the cliff is eviction, not position

`PREREG-SPCC.md` §E3 asks whether the observed distance cliff is a property of **position**
or of **eviction**. E1 showed the value is absent from the prompt at the failing
checkpoints, which is consistent with eviction but does not separate the two explanations.
E3 removes the confound: every fact body is delivered at its introduction turn and never
masked and never compacted, so at the d64 probe the body is still in the prompt. If the
cliff persists it is position; if it vanishes it was eviction.

```
--fixture tasks-v7/TX-04.v1.json   sha256 0c836872225fc0d6198aa86b3c72ec3dfada0b23f2541cde49adc53429703885
--arms spcc,masking-no-fetch --window-turns 200 --compact-every 200
--reps 1 --temperature 0 --seed 42 --model occamy-1.0
--claim-mode E3 --budget-cap 12094 --run-id e3-retain-2026-11-10
--rows measure/rows-e3-retain-2026-11-10.jsonl
```

48 checkpoints at d2 10 / d8 10 / d20 10 / d32 9 / d64 9; deepest probe turn 99
(`cp.TX-04.f05.d64`). Window 200 over 100 turns masks nothing; interval 200 compacts
nothing. 200 requests, 0 failed, 0 truncated, programme spend 9,667 → 9,867 of 12,094.

**Control holds.** `masked_rows` 0, `compactions` 0, `evicted` 0, `masked_entry` empty, no
`[MASKED` marker on any row, `expected_present` 96/96 true with `expected_present_source`
`prompt-digit-boundary` on all 96 checkpoint rows — including all nine d64 probes.

| arm | value_correct | contract_correct | NONE | wrong | unparsed | graded | total | requests | billed_tokens |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| spcc | 48 | 48 | 0 | 0 | 0 | 48 | 48 | 100 | 17,129 |
| masking-no-fetch | 42 | 42 | 0 | 6 | 0 | 48 | 48 | 100 | 16,265 |

Per distance — contract_correct / n:

| arm | d2 | d8 | d20 | d32 | d64 |
|---|---|---|---|---|---|
| spcc | 10/10 | 10/10 | 10/10 | 9/9 | **9/9** |
| masking-no-fetch | 9/10 | 8/10 | 8/10 | 8/9 | **9/9** |

**Verdict — the cliff is eviction.** At d64 with the body present both arms score 9/9. All
nine d64 probes are correct in both arms, including the deepest probe at turn 99
(`cp.TX-04.f05.d64`, expected 4054, got 4054, body present). The cliff does not persist. It
vanishes. The distance cliff observed in the earlier cells is a property of **eviction**, not
of position: the model can retrieve a fact it was given at distance 64, and it fails when
the fact has been taken away. The headline is *cannot retrieve what it was taken away*, not
*cannot retrieve what it was given*.

**Second result — the arms are not identical when both retain.** The two arms differ by
6/48 = 12.5 pp (48/48 vs 42/48), outside the ±4.2 pp band, and the difference has **no
distance gradient**: the six failures sit at d2, d8, d20 and d32, and d64 is perfect in
both. This is not a residual cliff — it is a prompt-format attribution effect:

| checkpoint | d | turn | expected | answered | error kind |
|---|---:|---:|---|---|---|
| `cp.TX-04.f09.d2` | 2 | 30 | 4091 | 4011 | cross-document (f01's VAL_A) |
| `cp.TX-04.f02.d8` | 8 | 10 | 4021 | 4061 | cross-document (f06's VAL_A) |
| `cp.TX-04.f07.d8` | 8 | 39 | 4072 | 4102 | cross-document (f10's VAL_B) |
| `cp.TX-04.f08.d20` | 20 | 31 | 4083 | 4073 | cross-document (f07's VAL_C) |
| `cp.TX-04.f12.d20` | 20 | 73 | 4123 | 4124 | within-document (VAL_C → VAL_D) |
| `cp.TX-04.f02.d32` | 32 | 34 | 4023 | 4022 | within-document (VAL_C → VAL_B) |

Every failure is a well-formed `ANSWER: NUM` with a plausible wrong value — four
cross-document confusions and two within-document symbol confusions; none is an abstention,
none is unparsed. The masking arm's `WORKING SET INDEX` prompt format costs attribution
accuracy at *all* distances, which is a different mechanism from the distance cliff and must
not be pooled with it.

**The 6/48 gap is answer-slot binding (U-SPCC-67).** Both arms' prompts were rebuilt
through the runner's own `Planner` (`experiments/ptr-engine/longrun/run_longrun.py:1562`)
with `send_chat` replaced by a recorder; `prompt_sha256` matched **200/200** rows. The
masking arm is a flat transcript replay — `WORKING SET`, then 29 turn blocks each shaped
`QUESTION (Tt) / TOOL OUTPUTS: / TOOL_OUTPUT (doc@rev): body / ANSWER (Tt): value`, then the
current turn block, then the checkpoint contract (T30: 158 lines, 1,611 prompt tokens); the
spcc arm is the layered compiler L0/L1/L2/L3/L4 (T30: 69 lines, 1,465 prompt tokens,
`layer_tokens` L0=80 L1=20 L2=215 L3=21 L4=2). The one difference that matters: **the
masking arm replays an `ANSWER (Tt):` line after every turn's tool-output block; the spcc
journal replays no answers at all.** The transcript teaches a positional rule — the answer
slot takes its value from the block immediately above it — because that is the shape of all
29 prior turn blocks. On a checkpoint turn the fixture delivers a body for a *different*
document, and that body is the block immediately above the answer slot: five checkpoint
turns deliver a body, in all five the delivered document differs from the asked one, and
the masking arm answers with the delivered body's value on **4 of 5**, spcc on **0 of 5**.
Quoted, masking T31 lines 152-158: `QUESTION (T31): What is VAL_C of doc-fact-08?` /
`TOOL OUTPUTS:` / `TOOL_OUTPUT (doc-fact-07@1): # doc-fact-07` / `VAL_A = 4071` /
`VAL_B = 4072` / `VAL_C = 4073` / `VAL_D = 4074` → answered 4073, while the expected 4083
sits at line 62 inside `TOOL_OUTPUT (doc-fact-08@1)` delivered at T11, 90 lines and 428
tokens above the question and the only occurrence of that value. Proximity is refuted (at
T30 both arms have the answered value closer to the question than the expected one —
masking 32 before / 27 after, spcc 21 before / 17 after — and spcc answers correctly);
document anchoring is refuted (the masking arm does print `TOOL_OUTPUT (doc-fact-07@1): #
doc-fact-07` and the model ignores it). The masking arm's one correct delivery-turn answer
(T12) is the turn where the expected value had already been echoed as a prior answer:
masking T12 line 55 reads `ANSWER (T10): ANSWER: NUM 4061`. The two within-document
failures have no delivery: T34 answered 4022 = `ANSWER (T22): ANSWER: NUM 4022`, the
replayed answer for the same document but a different symbol; T73 answered 4124, the line
immediately below `VAL_C = 4123` in the same body.

**Verdict and exclusion rule.** The binding is intrinsic to a transcript replay that
replays answers — not fixable without changing what the arm measures, because the answer
replay is load-bearing (the masking branch masks prior answers on masked turns precisely so
an earlier checkpoint's value cannot be copied without recovering the fact; delete the
`ANSWER` lines and the arm is the spcc journal). **The 6/48 gap is therefore a format
artefact and must be excluded from any retention comparison.** At this cell neither arm
loses information (`masked_rows` 0, `compactions` 0, `evicted` 0 on all 200 rows;
`expected_present` true on 96/96 with `expected_present_source = prompt-digit-boundary`):
the cell is a format control, not a retention measurement, and pooling this 12.5 pp with
the distance cliff would attribute a prompt-format artefact to memory. Recorded in
`experiments/ptr-engine/research-seed-concepts/FINDINGS-LEDGER.md` §The 6/48 gap is
answer-slot binding; unit `orchestration/units/U-SPCC-67.md`, handoff
`orchestration/handoffs/U-SPCC-67.json`, commit `dcc9b65`.

**Scoring note.** `score_longrun.score_answer_contract_rows` returns `denominator_mismatch`
when handed a multi-arm rows file: it sums distinct checkpoint ids across every `(arm, rep)`
key and compares that total to the fixture's checkpoint count (96 vs 48 here). The cell was
graded per arm, which is the only reading that satisfies the function's own denominator
rule.

## U-SPCC-68 — E2 turnover sweep: no accuracy turnover in {48,64,96}; the cost turnover sits at C=48

`PREREG-SPCC.md` §E2 predicts a turnover: past some interval, larger C should start to hurt.
U-SPCC-62 swept {12,24,48} and found accuracy still climbing at the top. This cell extends the
sweep upward to {48,64,96} on the same fixture, model and seed, one arm-variant per interval:

```
--fixture tasks-v7/TX-03.v1.json --arms spcc --compact-every 48,64,96 --reps 1
--temperature 0 --seed 42 --model occamy-1.0 --base-url http://192.168.2.168:8012/v1
--claim-mode E2 --run-id e2-turnover-2026-11-10
--rows experiments/ptr-engine/measure/rows-e2-turnover-2026-11-10.jsonl
```

300 rows, 300 requests, 0 failed, 0 truncated, cap-gate reconcile delta 0.

| C | value_correct | contract_correct | NONE | wrong | billed_tokens | compactions | fire turns | prompt_tokens |
|---:|---:|---:|---:|---:|---:|---:|---|---:|
| 48 | 36/48 (75.0%) | 35/48 | 12 | 0 | 14,679 | 2 | 49, 97 | 133,463 |
| 64 | 39/48 (81.3%) | 38/48 | 9 | 0 | 15,063 | 1 | 65 | 142,295 |
| 96 | **47/48 (97.9%)** | 47/48 | 1 | 0 | 14,684 known / 15,275 upper | 1 | 97 | 200,939 |

**No accuracy turnover.** Accuracy rises monotonically 75.0 → 81.3 → 97.9; both steps are
outside the ±2/48 (±4.2 pp) band (+6.25 pp, +16.7 pp). The residual failures are
**abstentions, not wrong answers**: NONE 12 → 9 → 1, wrong 0 throughout. The predicted
turnover does not appear inside {48,64,96}; accuracy is still climbing at the top of the
sweep.

**A cost turnover does exist, and it sits at C=48.** Prompt tokens 133,463 → 142,295 →
200,939 (+50.6%). The curves cross at C=48: past it you pay more prompt tokens for more
accuracy, and accuracy is still climbing. Billed tokens are non-monotone (14,679 → 15,063 →
14,684) and are not the measure to read here — see the rule below.

**d32 is the fixture ceiling, not a horizon.** Deepest passing distance is 32 for all three
intervals — TX-03's distances are 2/5/6/8/20/32, so the horizon is saturated. The
informative quantity is the fraction passing at d32: **4/8 → 5/8 → 7/8**. The only C=96
failure is one abstention at `cp.TX-03.f08.d32` (turn 100).

**Rule — cross-run billed-token comparisons are confounded even when prompts are
byte-identical.** C=48 bills **14,679** here versus **15,703** in E2 (U-SPCC-62) for
byte-identical prompts (`prompt_tokens` match on every turn). The gap is prefix-cache
warmth, not work. Therefore: **only within-run comparisons are valid, and prompt tokens are
the cache-independent measure.** This qualifies E2's −5.72% cost claim — that comparison was
within a single cell, so it stands — but no billed figure from one cell may be compared to
another.
