# ADOPT-HARNESS — adopt-before-build survey of the eight bespoke layers

**Status:** done · **Card** `2dbeba03-a3ae-4cbc-a45c-47fceb534abf` · **Retrieved** 2026-10-26 ·
**Bound** 30 tool calls (used 20–22) · **Code edited: none.**

## Purpose

The operator's problem, in their words: *"always learn what's already available out there to easily adopt
and reduce our workload."* This batch hand-built ~200 rounds of infrastructure. This unit tells the
difference between the part that was necessary and the part that was not, **with evidence** — not to
defend the build.

## Deliverables (declared write paths)

| path | what |
|---|---|
| [`docs/research/ADOPT-HARNESS.md`](../../docs/research/ADOPT-HARNESS.md) | the memo: 8-row component table, candidate-space rejections, what changed my mind, Top 3, sources |
| [`measure/research/ADOPT-HARNESS.json`](../../measure/research/ADOPT-HARNESS.json) | machine record: 8 `components[]`, 32 `sources[]` (url + retrieved_at), 3 `top3[]`, arithmetic |
| `orchestration/units/ADOPT-HARNESS.md` | this card |
| `orchestration/handoffs/ADOPT-HARNESS.json` | handoff |
| `orchestration/journals/ADOPT-HARNESS.jsonl` | step journal |

Read-only, never edited: `cell.py`, `run_longrun.py`, `client.py`, `analyze_stats.py`, `grade_v5.py`.

## Method

1. Read the five frozen instruments for citations only (`wc -l`, `grep -n`) — no execution of the pipeline,
   no writes, no git state change.
2. Counted the build cost from the record: 1097 unit cards, 135 matching the eight layers (union of ten
   family greps), 7 of them pure commodity subjects.
3. Fetched every candidate's registry document and primary doc page and **read** its licence and last
   release date — PyPI JSON, npm registry, GitHub API, SciPy/statsmodels/vLLM/SGLang/LiteLLM/Inspect docs.
   No project, licence or release date is inferred.
4. Decided per rown with the frozen-path rule: anything touching the five instruments is
   `adopt-after-grid`, a proposal for a later card, never an edit here.

## Results

| layer | decision |
|---|---|
| live runner (SSE, tool rounds, stop reasons) | `adopt-after-grid` (openai client transport; keep our TTFT latch + stop-reason map) |
| gate chain G1/G2/G3 + request ledger | **`build`** — no candidate reserves a pre-flight budget; every option is post-hoc |
| budget/runaway guards | `adapt` (tenacity for retry policy only; guards stay) |
| verdict/acceptance gate | `borrow-idea` (pre-commit's committed-command idea; keep the proof) |
| provenance & pinning | **`build`** — dvc/mlflow/wandb version data or add a server; lakeFS is BUSL-1.1 |
| latency analysis | `adopt-after-grid` (SciPy bootstrap + statsmodels McNemar; keep estimability policy) |
| contract grading | `borrow-idea` (lm-eval filter-before-metric; the contract must become decidable first) |
| canary / shape classification | **`build`** — nothing in the candidate space does era detection |

**Top 3 by workload removed:** stats primitives (≈218 lines), retry policy (~47 sites), row schema.
Each has a named owner card and an offline proof experiment.

## Answer to the operator's question

**≈1 round in 8 was avoidable** — 17 of 135 layer cards are pure reimplementations of library features
(7 outright + 10 borderline) = 12.6 %, ≈25 of ~200 rounds. Those bought *lines*, not *rules*: no fetched
library implements the ledger's pre-flight reservation, the verdict's frozen-command binding, the
harness digest freeze, or era detection — 1803 lines of adjudication machinery with no off-the-shelf
equivalent (`request_ledger.py` 858, `tree_freeze.py` 584, `verdict_scope.py` 361).

## Open / unverified

- litellm/inspect_ai not installed — behaviour claims are vendor-doc level.
- vLLM `bench serve` flag list not verified (sub-page body empty to the fetch); subcommand existence is.
- 0 live requests to `:8012`; nothing here is a measurement of the server.
- Counterfactual of "how many layer cards a library would have made unnecessary" is provable for 7 cards
  only; the rest is stated as judgement.
