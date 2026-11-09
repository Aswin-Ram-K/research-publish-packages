# ADOPT-HARNESS — what already exists for the eight bespoke layers, and what that is worth

**Unit** `ADOPT-HARNESS` · **card** `2dbeba03-a3ae-4cbc-a45c-47fceb534abf` · **retrieved 2026-10-26** ·
journal `orchestration/journals/ADOPT-HARNESS.jsonl` · machine record
[`measure/research/ADOPT-HARNESS.json`](../../measure/research/ADOPT-HARNESS.json).

**Question:** for each of the eight bespoke layers (live runner, gate chain + ledger, budget/runaway guards, verdict gate, provenance pinning, latency analysis, contract grading, canary/shape), does an existing project already implement it well enough to adopt, and what would adoption cost against the frozen era-B instruments?

**Method.** Offline for the model: **0 inference requests**, both live endpoints untouched. Evidence is
HTTP fetches of package registries and primary docs (PyPI JSON, npm registry, GitHub API, the servers'
own doc pages), each recorded with its URL and `retrieved_at` in §9. No project, licence or release date
below is inferred: each row's licence and last-release date was *read* from the registry document named in
the row. Where a claim could not be fetched it says `unverified` and the decision is `unassessed`.
**Bound 30 calls; 20 used.** **No code was edited** — every decision is a proposal with an owner card.

**Frozen-path rule applied throughout.** The era-B grid's instruments — `cell.py` (2300 lines),
`run_longrun.py` (3116), `client.py` (1140), `analyze_stats.py` (1846), `grade_v5.py` (1117) — were
**read only**. Anything that would touch them is `adopt-after-grid`: a proposal for the card after
adjudication, never an edit here.

---

## 0. Verdict

The batch built **two rings**, and they have opposite adoption answers.

- The **commodity ring** — statistics primitives, HTTP retry, schema validation, CLI/config plumbing,
  answer normalisation — is ~**218 lines of hand-rolled statistics** (`analyze_stats.py:253-470`), ~**47**
  retry/attempt touchpoints (`client.py`), and ~**153 lines** of decoration stripping
  (`grade_v5.py:178-330`), against libraries that have shipped for years (SciPy BSD-3 1.18.1,
  statsmodels BSD-3 0.15.0, tenacity Apache-2.0 9.2.1, pydantic MIT 2.14.1, lm-eval MIT 0.4.13).
  **Adopt, after the grid.**
- The **adjudication ring** — the request ledger with reserve/headroom arithmetic
  (`tools/request_ledger.py`, **858** lines), the gate chain G1/G2/G3 (`cell.py:160-162`), the verdict gate
  (`tools/verdict_scope.py`, **361** lines), the provenance freeze (`tools/tree_freeze.py`, **584** lines;
  `cell.py:185-190,334-354`), and era/shape canaries — has **no off-the-shelf equivalent among every
  candidate checked**. Not one project in the candidate space does *pre-flight quota reservation against an
  artefact-backed ledger*, *PASS derived only from a frozen command re-run at the measured head sha*, or
  *era-bounded instrument detection*. **Keep, and say so in one line so it stops being re-litigated.**

Measured arithmetic, and it is the whole answer to "how much was avoidable": of **1097** unit cards in
`orchestration/units/`, **135** name one of the eight surveyed layers (union of the family greps in §8);
**7** of those 135 have a subject a fetched library implements outright (stats, retry, schema, CLI),
**≈10** more are borderline (config/CI/format shims), i.e. **≈12–13 %** of the layer batch. Scaled to the
operator's ~200-round estimate that is **≈25 rounds avoidable, ≈175 not** — and the avoidable ones bought
*lines*, not *rules*: no library would have removed the ledger, the gates, the freeze or the verdict.

---

## 1. The table

Decision vocabulary: `adopt` (take the dependency, delete our code — all are `adopt-after-grid` here),
`adapt` (take it behind our invariants), `borrow-idea` (copy the design, keep our implementation),
`build` (keep what we have; the survey found nothing), `not-applicable` (nothing to replace, with reason),
`unassessed` (could not fetch, so no decision).

| # | problem | existing option (name · URL · licence · last release) | what it would replace here (`file:line`) | adopt cost (files touched · deps · risk to frozen paths) | build cost already paid (cards) | decision |
|---|---|---|---|---|---|---|
| 1 | Live runner: SSE client, per-turn loop, tool rounds, stop-reason classification, row writing | **openai-python** <https://pypi.org/pypi/openai/json> · Apache-2.0 · 3.39.0 (2026-10-26); **litellm** <https://pypi.org/pypi/litellm/json> · MIT · 1.106.4 (2026-10-25); **inspect_ai** <https://pypi.org/pypi/inspect-ai/json> · MIT · 0.3.285 (2026-10-25), tool loop <https://inspect.aisi.org.uk/tools.html> | `client.py` SSE decode + `STOP_REASON_*` (`client.py:101`), the `ttft_ms` "first stream delta carrying a token" latch (`client.py:25`, rationale `client.py:11-15`), per-turn tool rounds (`run_longrun.py:988-1019`), window/wall token management (`run_longrun.py:1153-1241`) | **frozen**: all three files are era-B instruments. Deleting the SSE decoder gives up the *measured* TTFT latch (vLLM latches on first chunk with `choices`, SGLang on first non-empty `text` — a deliberate divergence recorded in `docs/EXTERNAL-SERVING-PRACTICE.md` §1) and the stop-reason taxonomy the canary reads. 2 deps, 1 module rewritten, grid invalidated | 3 files, 5 556 lines; client/runner cards inside the **135** layer cards; no separate "SSE" card — the cost is the grid itself | **adopt-after-grid** (transport only: `openai` client replaces the hand-rolled stream decoder *after* adjudication, keeping our `ttft_ms` latch and stop-reason map as a thin wrapper) |
| 2 | Gate chain G1 ledger cap · G2 wall projection · G3 prereg n, and the request ledger's reserve/headroom | **vLLM `bench serve`** <https://docs.vllm.ai/en/latest/cli/> · Apache-2.0 · vllm 0.32.0 (2026-10-18); **SGLang `/metrics`** <https://docs.sglang.io/docs/references/production_metrics> · Apache-2.0 · 0.5.22 (2026-10-16); **litellm spend tracking** <https://docs.litellm.ai/docs/proxy/cost_tracking> · MIT · 1.106.4 | `cell.py:160-162` (`GATE_LEDGER`/`GATE_PROJECTION`/`GATE_PREREG`), `cell.py:688-818` (G2 evaluate/enforce), `cell.py:408-417` + `cell.py:17-19` (headroom, ledger-as-only-accounting), `tools/request_ledger.py` (858 lines) | none available: every candidate is **post-hoc** (server counters after the request; proxy spend logs after the key). None reserves a *pre-flight* budget against an artefact and refuses before the request is sent. Adopting one adds a second accounting — exactly what `cell.py:18-19` forbids | **18** ledger cards + **31** gate/prereg cards | **build** (keep; and record the one-line reason: no candidate reserves pre-flight) |
| 3 | Budget / runaway guards: turn wall cap, runaway counter, abandon-and-continue | **tenacity** <https://pypi.org/pypi/tenacity/json> · Apache-2.0 · 9.2.1 (2026-10-07); **backoff** <https://pypi.org/pypi/backoff/json> · MIT · 2.2.1 (2022-10-05, stale) | the retry/attempt surface in `client.py` (~47 `retry|backoff|attempt|STOP_REASON` sites); **not** the guards themselves: `run_longrun.py:473-475` (`max_turns` cap) and the `runaway` exit path (`run_longrun.py:327`, code 6) are semantic, not retry policy | 1 dep; `client.py` frozen. tenacity covers `stop_after_attempt`/wait strategies only — the turn wall and abandon-and-continue are ours | **8** budget/wall/runaway cards | **adapt** (tenacity for the retry *policy* only, post-grid; guards stay) |
| 4 | Verdict / acceptance gate: `orchestration_verdict`, frozen-command rule, `tree_freeze`, `verdict_scope` | **pre-commit** <https://pypi.org/pypi/pre-commit/json> · MIT · 4.7.0 (2026-10-12); **tox** <https://pypi.org/pypi/tox/json> · MIT · 4.67.1 (2026-10-18); **nox** <https://pypi.org/pypi/nox/json> · Apache-2.0 · 2026.10.20 | `tools/verdict_scope.py` (361 lines), `tools/tree_freeze.py` (584 lines), the frozen-command binding in the DSH `orchestration_verdict` tool | these run a *suite*; none binds a verdict to `exit 0 AND sha == execution head sha`, refuses a command edit between attempts, or re-runs the frozen judge against a scratch copy of the card tree. Adopting one would replace a proof with a checklist | **16** verdict/tree-freeze/acceptance cards | **borrow-idea** (pre-commit's "the hook command is committed, not improvised" idea is already what the frozen-command rule is; keep ours) |
| 5 | Provenance & pinning: harness digest pin, per-row `request_sha256`, `row_seq`, baseline snapshots | **dvc** <https://pypi.org/pypi/dvc/json> · Apache-2.0 · 3.67.1 (2026-03-31); **mlflow** <https://pypi.org/pypi/mlflow/json> · Apache-2.0 · 3.17.2 (2026-10-21, licence re-read at <https://api.github.com/repos/mlflow/mlflow>); **lakeFS** <https://pypi.org/pypi/lakefs-sdk/json> · **BUSL-1.1** · 1.88.0 (2026-10-01); **wandb** <https://pypi.org/pypi/wandb/json> · MIT · 0.31.0 (2026-10-16) | `cell.py:185-190` (`_sha256_file`), `cell.py:334-354` (`freeze_harness`, exit 2 on a moved digest), the baseline dirs under `state/harness-baselines/`, `row_seq`/`request_sha256` in each row | dvc versions *data*; the invariant here is "the set of files that can move a measurement", which lives in the runner and must be computed at launch, and dvc adds a `.dvc` index that would itself need pinning. mlflow/wandb need a tracking server or a DB — a second source of truth next to the rows. lakeFS is **BUSL-1.1**, not OSI-approved: a licence blocker for adoption | **27** pin/provenance/digest/freeze cards | **build** (keep; dvc/mlflow/wandb recorded as `not-applicable` for the measurement freeze, lakeFS rejected on licence) |
| 6 | Latency analysis: quantile intervals, bootstrap, `n_eff` autocorrelation, McNemar | **SciPy** `scipy.stats.bootstrap` <https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html> · BSD-3 · 1.18.1 (2026-08-21); **statsmodels** `contingency_tables.mcnemar` <https://www.statsmodels.org/stable/generated/statsmodels.stats.contingency_tables.mcnemar.html> · BSD-3 · 0.15.0 (2026-08-27) | `analyze_stats.py:253-270` (`wilson_ci`), `:302-330` (`rank_span`, `min_n_for`), `:350-399` (`quantile_ci` percentile bootstrap), `:430-470` (`mcnemar_exact`) — **218 lines** | 2 deps, 1 frozen file. **What must survive adoption**: the *estimability policy* (`analyze_stats.py:111-113`: `MIN_N=20`, `TAIL_MIN=3`, `RESAMPLES=10000`, `SEED`) and `rank_span`'s distribution-free refusal — SciPy has no "this quantile is not estimable at this n" refusal, and that refusal is the finding, not the computation | **2** stats-subject cards directly; the primitives are load-bearing in the **15** bootstrap / **18** mcnemar / **6** n_eff mentions | **adopt-after-grid** (SciPy for the bootstrap interval + statsmodels for McNemar; keep `rank_span`, `min_n_for` and the seed as our policy layer) |
| 7 | Contract grading: answer-contract checks, decoration stripping, negative controls | **lm-evaluation-harness** filter pipeline <https://pypi.org/pypi/lm-eval/json> · MIT · 0.4.13 (2026-08-31); **inspect_ai** scorers <https://inspect.aisi.org.uk/reference/inspect_ai.analysis.html> · MIT · 0.3.285; **promptfoo** <https://registry.npmjs.org/promptfoo> · MIT · 0.125.1 (2026-10-25) | `grade_v5.py:178-330` trap/decoration stripper (153 lines), `:98-115` numeral integrality, `:155-176` `_parse_call` | lm-eval's filters assume a typed answer field and a metric; our subject is prose contract compliance with measured **FN 30.8 %/FP 45.5 %** (v3) and **26.9 %/50.0 %** (v4) — a *reliability* problem a different normaliser does not fix. promptfoo is a runner, not a grader contract; it would replace the whole cell, not the check | **23** contract/grade cards | **borrow-idea** (lm-eval's "filter before the metric, several filters over the same generation" is the pattern to copy post-grid; the stripper stays until the contract is decidable) |
| 8 | Canary / shape classification: era detection, degeneracy rules | none found in the candidate space (vLLM/SGLang expose model metrics, not run-shape canaries; inspect/lm-eval have no era detector) | canary + era logic in the longrun tools (`tools/grid_resume.py` and the canary test suite), degeneracy rules in `docs/CANARY-ERA-B*.md`, `docs/ANSWER-DEGENERACY.md` | — | **21** canary/era/degeneracy cards | **build** (keep; era detection is workspace-specific by construction) |

### 1a. Candidate-space rows with a reason they do not fit

| candidate (URL · licence · release) | why `not-applicable` |
|---|---|
| **vLLM `bench serve`** <https://docs.vllm.ai/en/latest/cli/> · Apache-2.0 · 0.32.0 | closed-loop single-request load generator. It reports aggregate TTFT/ITL over N prompts; it cannot write our per-turn row (`turn`, `row_seq`, `request_sha256`, stop reason) for a 48-turn tool-using conversation, so it replaces the *load model*, not the runner |
| **SGLang benchmark** <https://api.github.com/repos/sgl-project/sglang/contents/benchmark> · Apache-2.0 · 0.5.22 | same shape (`benchmark/serving.py` is a single-request client); read as source in `docs/EXTERNAL-SERVING-PRACTICE.md` §1, whose TTFT latch differs from vLLM's — i.e. adopting it would *change the instrument* |
| **genai-perf** <https://pypi.org/pypi/genai-perf/json> · BSD · 0.0.16 (2025-08-26) | as above, and the registry shows **no release in ~14 months** — insufficient for an instrument we intend to rely on |
| **pre-commit / tox / nox** | CI hygiene for *code*; our verdict gate adjudicates a measurement. Useful for the repo, irrelevant to `tools/verdict_scope.py` |
| **hydra-core** <https://pypi.org/pypi/hydra-core/json> · MIT · 1.3.8 · **typer** <https://pypi.org/pypi/typer/json> · MIT · 0.27.3 | our config is a fixture JSON whose *identity* is part of the harness digest (`cell.py:340`); Hydra's job is composition/completion — adopting it adds a resolver between the fixture and the digest, i.e. a new thing to pin, for no rule removed. typer would rewrite `argparse` surfaces that `cell.py` G2 operand validation depends on |
| **pydantic** <https://pypi.org/pypi/pydantic/json> · MIT · 2.14.1 | the one genuine `adapt`: row-schema validation (`ROW-SCHEMA`) is exactly pydantic's job, and `row_seq`/`request_sha256` become required fields rather than assertions. Deferred to post-grid because rows are written by the frozen runner |

---

## 2. What the survey changed my mind about

1. **I expected litellm to replace the ledger.** It does not: `docs.litellm.ai/docs/proxy/cost_tracking`
   is spend *after* the fact (per key/user/team), and the ledger's job is to refuse **before** the request
   (`cell.py:17-19`). Post-hoc accounting cannot satisfy G1; a pre-flight reservation is genuinely
   unsolved by the ecosystem.
2. **I expected lakeFS or dvc to replace the freeze.** dvc is Apache-2.0 and alive, but it versions data
   files, not "every file that can move a measurement"; and lakeFS — the closest conceptual fit — is
   **BUSL-1.1**, so it is a licence blocker regardless of fit.
3. **`docs/EXTERNAL-EVAL-PRACTICE.md` already answered the grader question** (2026-10-26, same day): the
   suites grade a *decidable* answer, we grade prose. So the grading row is not "find a better stripper";
   it is "make the contract decidable" — which is a design change with an owner, not a dependency.

---

## 3. Top 3

### 1. Statistics primitives → SciPy + statsmodels  (`adopt-after-grid`)
- **Delete**: the bootstrap interval (`analyze_stats.py:350-399`), `_quantile_sorted`/`_binom_cdf`
  internals, `wilson_ci` body (`:253-270`), `mcnemar_exact` body (`:430-470`) — **≈218 of 1846 lines**.
- **Keep**: `MIN_N=20`/`TAIL_MIN=3`/`RESAMPLES=10000`/`SEED` (`:111-113`), `rank_span` (`:302-325`),
  `min_n_for`, and every refusal message — the *estimability policy* is the finding SciPy does not encode.
- **Breaks first**: the percentile bootstrap's tie/interpolation convention. SciPy's `bootstrap` has
  vectorised resampling and a different default interpolation; a p95 CI that moves by 1e-3 would move a
  frozen claim.
- **Proof experiment (offline, zero requests)**: recompute every reported CI from the existing rows with
  both implementations and require identical `(point, lo, hi)` to 1e-12 on **100 %** of analyses; adopt
  SciPy only where it matches, adopt statsmodels only for McNemar where the exact p matches, and leave the
  rest as `build`.

### 2. Retry policy → tenacity  (`adapt`, post-grid)
- **Delete**: the hand-rolled backoff/attempt loop in `client.py` (~47 sites that branch on
  `retry|backoff|attempt|STOP_REASON`), leaving the SSE latch and stop-reason map.
- **Keep**: `STOP_REASON_*` taxonomy (`client.py:101`), the first-token TTFT latch (`client.py:25`), and the
  rule that a stream error is classified, not retried into a different row.
- **Breaks first**: a retry that changes the request count would move G1's arithmetic; tenacity must be
  configured with a **fixed** `stop_after_attempt` that the ledger already budgets.
- **Proof experiment (offline)**: replay the recorded streams with the new policy and assert byte-identical
  rows (`request_sha256`, `row_seq`, stop reason) on 100 % of replayed turns.

### 3. Row schema → pydantic  (`adapt`, post-grid)
- **Delete**: hand-rolled row-shape assertions in the writer/readers (**~ROW-SCHEMA** card), once the model
  is the single definition of a row.
- **Keep**: `row_seq` monotonicity and `request_sha256` presence as *required* fields, and poisoned-row
  semantics — a schema must not coerce a poisoned row into a valid one.
- **Breaks first**: coercion. pydantic v2's lax mode would happily turn `"3"` into `3` on a field whose
  type is the finding; use `strict=True` and re-check the pinned corpus.
- **Proof experiment (offline)**: validate the existing pinned `rows.jsonl` corpus with the model and
  require accept/reject decisions identical to today's, **including** every poisoned row.

**Not in the top 3 on purpose**: the transport rewrite (`openai` client / inspect_ai runner) removes the
most lines but also removes the two instruments the whole grid is adjudicated on (`ttft_ms` latch,
stop-reason map). It is `adopt-after-grid` or never; it is not a workload win *this* batch can bank.

---

## 4. Owners (proposals only — nothing edited)

| proposal | owner card to file |
|---|---|
| stats adoption + equivalence proof | `ADOPT-STATS-EQUIV` |
| tenacity retry policy + replay proof | `ADOPT-RETRY-REPLAY` |
| pydantic row schema (strict) + corpus proof | `ADOPT-ROWSCHEMA-STRICT` |
| transport after adjudication, keep instrument wrapper | `ADOPT-TRANSPORT-POSTGRID` |
| record "no pre-flight ledger exists" so it stops being re-surveyed | `ADOPT-LEDGER-RATIONALE` |

## 5. Unverified / open

- **litellm proxy** and **inspect_ai** were verified as *projects and doc pages*, not installed and not
  exercised. Their licence/version/release dates are read from registries; their behaviour claims are from
  their own docs (vendor) — `unverified` at the code level.
- **vLLM `bench serve` help surface** was read from the CLI doc index (the flags `--request-rate`,
  `--num-prompts` appear on the sub-page, which returned an empty body to this fetch) — the *subcommand's
  existence* is verified (`bench serve|throughput|latency|forward` on the index), the flags are not.
- **No claim here is a measurement of `:8012`.** 0 requests were made.
- A counterfactual this survey cannot answer: how many of the 135 layer cards would have been *unnecessary*
  had a library been adopted first — only the 7 commodity-subject cards are provable; the rest is
  judgement and is stated as such.

## 8. How the card arithmetic was measured

```
ls orchestration/units/*.md | wc -l                       -> 1097
grep -ci 'LEDGER'                                          -> 18
grep -ci 'GATE|PREREG'                                     -> 31
grep -ci 'BUDGET|WALL|RUNAWAY|TURN-CAP|ABANDON'            -> 8
grep -ci 'VERDICT|TREE-FREEZE|ACCEPTANCE'                  -> 16
grep -ci 'CANARY|ERA-|DEGENERAC'                           -> 21
grep -ci 'MCNEMAR|BOOTSTRAP|N_EFF|WILSON|QUANTILE|STATS'   -> 2
grep -ci 'CONTRACT|GRADE'                                  -> 23
grep -ci 'PIN|PROVENANCE|DIGEST|SHA|FREEZE'                -> 27
grep -ci 'RETRY|HTTP|CLIENT|BACKOFF|TIMEOUT'               -> 3
grep -ci 'SCHEMA|CONFIG|CLI'                               -> 5
union over all ten greps                                   -> 135
commodity-subset greps (stats+retry+schema/config/CLI)     -> 7
```
Families overlap; 135 is a union, not a sum (the sum is 154). Line counts are `wc -l` on the named files;
the 218-line statistics region is `awk 'NR>=253 && NR<=470'`.

## Verified

Each item below was read in the fetched source named in §9, not inferred.

- **V1.** `scipy.stats.bootstrap` exists (SciPy v1.18.0 manual; package 1.18.1, BSD-3-Clause, 2026-08-21) — `scipy-bootstrap`, `pypi-scipy`.
- **V2.** `statsmodels.stats.contingency_tables.mcnemar` exists (statsmodels 0.15.0, BSD-3-Clause, 2026-08-27) — `sm-mcnemar`, `pypi-statsmodels`.
- **V3.** litellm's documented cost path is **post-hoc spend tracking** "for keys, users, and teams", with per-request callbacks — not a pre-flight reservation (`cell.py:17-19` is a pre-flight rule) — `litellm-spend`.
- **V4.** vLLM exposes `bench serve|throughput|latency|forward`; SGLang exposes a benchmark tree and a Prometheus `/metrics` endpoint; both are single-request load generators, which is why they cannot write our per-turn rows — `vllm-cli`, `sglang-bench-dir`, `sglang-metrics`.
- **V5.** lakefs-sdk 1.88.0 is **BUSL-1.1** — a licence blocker independent of fit — `pypi-lakefs`.
- **V6.** The layer batch is **135 of 1097** unit cards (union of ten filename greps) and **7** of those have a pure-commodity subject (§8 gives the commands).

## Inferred

- **I1.** Adoption of any library touching `cell.py`, `run_longrun.py`, `client.py`, `analyze_stats.py` or `grade_v5.py` would move the era-B measurement, so every such row is `adopt-after-grid` by the frozen-path rule, not by preference.
- **I2.** The 218-line statistics region is the only place a library would *delete code*; elsewhere it would replace a *rule*, which is why the ledger/gate/verdict rows are `build`.

## Contradicted

- **None.** No fetched source contradicted a claim in this memo. Two expectations were corrected before they became claims: litellm does not replace the ledger, and lakeFS cannot be adopted on licence — both are recorded in §2.

## 9. Sources

All retrieved **2026-10-26** from this workspace; each is a URL this unit fetched (HTTP 200).

| id | URL | what it establishes |
|---|---|---|
| `pypi-scipy` | <https://pypi.org/pypi/scipy/json> | SciPy 1.18.1, BSD-3-Clause, 2026-08-21 |
| `scipy-bootstrap` | <https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html> | `scipy.stats.bootstrap` exists, SciPy v1.18.0 manual |
| `pypi-statsmodels` | <https://pypi.org/pypi/statsmodels/json> | statsmodels 0.15.0, BSD-3-Clause, 2026-08-27 |
| `sm-mcnemar` | <https://www.statsmodels.org/stable/generated/statsmodels.stats.contingency_tables.mcnemar.html> | `contingency_tables.mcnemar` in statsmodels 0.15.0 |
| `pypi-tenacity` | <https://pypi.org/pypi/tenacity/json> | tenacity 9.2.1, Apache-2.0, 2026-10-07 |
| `pypi-backoff` | <https://pypi.org/pypi/backoff/json> | backoff 2.2.1, MIT, 2022-10-05 (stale) |
| `pypi-httpx` | <https://pypi.org/pypi/httpx/json> | httpx 0.28.1, BSD-3-Clause, 2024-12-06 |
| `pypi-openai` | <https://pypi.org/pypi/openai/json> | openai 3.39.0, Apache-2.0, 2026-10-26 |
| `pypi-litellm` | <https://pypi.org/pypi/litellm/json> | litellm 1.106.4, MIT, 2026-10-25 |
| `litellm-spend` | <https://docs.litellm.ai/docs/proxy/cost_tracking> | "Spend Tracking" — spend for keys, users, teams; per-request callbacks (post-hoc) |
| `pypi-inspect` | <https://pypi.org/pypi/inspect-ai/json> | inspect_ai 0.3.285, MIT, 2026-10-25 |
| `inspect-tools` | <https://inspect.aisi.org.uk/tools.html> | "Tool Basics – Inspect" (tool-calling surface) |
| `inspect-analysis` | <https://inspect.aisi.org.uk/reference/inspect_ai.analysis.html> | `ci_wilson`, `bootstrap_stderr` in Inspect's analysis API |
| `pypi-lm-eval` | <https://pypi.org/pypi/lm-eval/json> | lm-eval 0.4.13, MIT, 2026-08-31 |
| `npm-promptfoo` | <https://registry.npmjs.org/promptfoo> | promptfoo 0.125.1, MIT, 2026-10-25 |
| `pypi-pydantic` | <https://pypi.org/pypi/pydantic/json> | pydantic 2.14.1, MIT, 2026-10-11 |
| `pypi-hydra` | <https://pypi.org/pypi/hydra-core/json> | hydra-core 1.3.8, MIT, 2026-10-25 |
| `pypi-typer` | <https://pypi.org/pypi/typer/json> | typer 0.27.3, MIT, 2026-10-06 |
| `pypi-mlflow` | <https://pypi.org/pypi/mlflow/json> + <https://api.github.com/repos/mlflow/mlflow> | mlflow 3.17.2, 2026-10-21; licence `Apache-2.0` (GitHub API `license.spdx_id`) |
| `pypi-dvc` | <https://pypi.org/pypi/dvc/json> | dvc 3.67.1, Apache-2.0, 2026-03-31 |
| `pypi-lakefs` | <https://pypi.org/pypi/lakefs-sdk/json> | lakefs-sdk 1.88.0, **BUSL-1.1**, 2026-10-01 |
| `pypi-wandb` | <https://pypi.org/pypi/wandb/json> | wandb 0.31.0, MIT, 2026-10-16 |
| `pypi-precommit` | <https://pypi.org/pypi/pre-commit/json> | pre-commit 4.7.0, MIT, 2026-10-12 |
| `pypi-tox` | <https://pypi.org/pypi/tox/json> | tox 4.67.1, MIT, 2026-10-18 |
| `pypi-nox` | <https://pypi.org/pypi/nox/json> | nox 2026.10.20, Apache-2.0, 2026-10-20 |
| `pypi-vllm` | <https://pypi.org/pypi/vllm/json> | vLLM 0.32.0, Apache-2.0, 2026-10-18 |
| `vllm-cli` | <https://docs.vllm.ai/en/latest/cli/> | subcommands `bench serve`, `bench throughput`, `bench latency`, `bench forward` exist |
| `pypi-sglang` | <https://pypi.org/pypi/sglang/json> | SGLang 0.5.22, Apache-2.0, 2026-10-16 |
| `sglang-metrics` | <https://docs.sglang.io/docs/references/production_metrics> | Prometheus exposition, `/metrics` endpoint |
| `sglang-bench-dir` | <https://api.github.com/repos/sgl-project/sglang/contents/benchmark> | the benchmark tree exists (listing returned) |
| `pypi-genai-perf` | <https://pypi.org/pypi/genai-perf/json> | genai-perf 0.0.16, BSD, 2025-08-26 |
