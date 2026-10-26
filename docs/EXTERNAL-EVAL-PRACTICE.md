# EXTERNAL-EVAL-PRACTICE — what the field knows about evaluating models and agents, and what this repo adopts

Unit `EVAL-PRACTICE-SURVEY`, 2026-10-26. **Offline for the model under test: 0 inference requests.**
Method: read the primary repositories, docs and papers listed in §9 over the web (30 sources fetched or
grepped in this run); every number below is either quoted from a source or is arithmetic this document shows.
Sibling card `SERVING-PRACTICE-SURVEY` covers measurement of the *server*; this one covers *evaluation*.

**Why this exists.** The live cell is 4 arms × 48 turns × **3 checkpoint questions**, graded by two
hand-rolled prose judges measured at **FN 30.8 % / FP 45.5 %** (`grade_v3`) and **FN 26.9 % / FP 50.0 %**
(`grade_v4`) in [GRADER-FITNESS.md](../experiments/ptr-engine/measure/GRADER-FITNESS.md). A claim of
"equal-or-better quality" currently rests on three binary cells per arm. §7 shows that this cannot support
the claim at **any** number of runs, and gives the cheapest design that can.

---

## 0. Verdict in one paragraph

The established suites do **not** grade free-form prose when the answer has a machine-checkable ground
truth: SWE-bench applies the patch and runs tests, τ-bench compares the final database state, GAIA and
LiveBench score short answers against objective ground truth, and lm-evaluation-harness converts an answer
into a typed value through a **filter pipeline** before any metric sees it. Prose-token matching is what
these harnesses use only for uncontrolled free-form, and where they use a model judge they *measure the
judge against human votes* first (MT-Bench: >80 % agreement) and report agreement statistics. Their
statistical bar is also higher than ours: lm-eval reports bootstrap standard errors per metric, Inspect
ships `ci_wilson()`, `bootstrap_stderr()` and clustered errors, and the eval-statistics literature asks
questions to be treated as draws from a super-population with pre-declared analysis. **This repo should
adopt a decidable answer contract, unit-test grading at checkpoints, per-headline CIs, a paired McNemar
test on item-level outcomes, and a pre-registered cap of at most one contrast — and should reject prose
matching as a primary accuracy metric and the current 3-checkpoint design as evidence for any arm ranking.**

---

## 1. What established harnesses do about grading and free-form output

| suite | how an answer is scored | free-form handling | judge reliability handling |
|---|---|---|---|
| **lm-evaluation-harness** ([repo](https://github.com/EleutherAI/lm-evaluation-harness), [task guide](https://github.com/EleutherAI/lm-evaluation-harness/blob/main/docs/task_guide.md)) | `metric_list` per task; `exact_match`, `matthews_corrcoef`, loglikelihood comparisons; `aggregation: mean` across subtasks ("currently, only `mean` is supported") | **filter pipeline** in front of every metric — `regex` extraction (`regex_pattern: "The answer is (\-?[0-9\.\,]*[0-9]+)"`), `take_first`, `majority_vote`, `strict-match`/`flexible-extract`; several pipelines may run **on the same generations** (the doc's `maj@64` / `maj@8` example) | per-metric **bootstrap standard error** (`bootstrap_stderr` in [`lm_eval/api/metrics.py`](https://github.com/EleutherAI/lm-evaluation-harness/blob/main/lm_eval/api/metrics.py)), `mean_stderr`, pooled SE across subtasks |
| **HELM** ([paper arXiv:2211.09110](https://arxiv.org/abs/2211.09110), [repo](https://github.com/stanford-crfm/helm)) | per-scenario accuracy on standardised instances; refuses to report accuracy alone | standardised adapters convert free-form to a scored unit | **multi-metric by design**: 7 metrics (accuracy, calibration, robustness, fairness, bias, toxicity, efficiency) over 16 core scenarios, "87.5 % of the time" — accuracy is one of seven, never the headline claim |
| **openai/evals** ([templates doc](https://github.com/openai/evals/blob/main/docs/eval-templates.md), [build-eval doc](https://github.com/openai/evals/blob/main/docs/build-eval.md)) | "basic" templates (match / includes / fuzzy) for low-variance answers; **model-graded** templates (`modelgraded` YAML with chain-of-thought graders) for open-ended ones; custom code evals | model-graded template grades a *rubric*, not a token | grading rubric is a versioned YAML next to the data; the repo explicitly states it is **not accepting evals with custom code** as contributions (build-eval.md), i.e. the maintainers treat ad-hoc code graders as an auditability problem |
| **BIG-bench** ([arXiv:2206.04615](https://arxiv.org/abs/2206.04615)) | 204 tasks, 450 authors, 132 institutions; programmatic targets for machine-checkable tasks, human evaluation for free-form | normalisation + matching for the programmatic tasks | free-form tasks are routed to human raters rather than a lexical test |
| **SWE-bench** ([arXiv:2310.06770](https://arxiv.org/abs/2310.06770), [repo](https://github.com/SWE-bench/SWE-bench)) | **unit tests on the patched repo** — the patch is applied and the task's tests are run; success is a test outcome, not a sentence | free-form patches are *executed*; no text matching | test selection is the reliability mechanism; **SWE-bench Verified** is a 500-problem subset "validated by real software engineers" ([repo README](https://github.com/SWE-bench/SWE-bench), [dataset](https://huggingface.co/datasets/SWE-bench/SWE-bench_Verified)) |
| **GAIA** ([arXiv:2311.12983](https://arxiv.org/abs/2311.12983)) | short, unambiguous answers; humans 92 % vs GPT-4+plugins 15 % | answers constrained to short strings so they are comparable | the benchmark's contribution is *task* difficulty, not judge sophistication |
| **τ-bench** ([arXiv:2406.12045](https://arxiv.org/abs/2406.12045)) | **final database state compared to the annotated goal state** — "an efficient and faithful evaluation process" | agent output is a sequence of tool calls; the environment, not the prose, is read | introduces **pass^k** (all k i.i.d. trials succeed) because a single trial hides inconsistency |
| **LiveBench** ([arXiv:2406.19314](https://arxiv.org/abs/2406.19314)) | "scores answers automatically according to **objective ground-truth values**" | tasks are built so the answer is checkable | designed explicitly to avoid "the pitfalls of LLM judging and human crowdsourcing"; questions refreshed from recent sources |
| **RULER** ([arXiv:2404.06654](https://arxiv.org/abs/2404.06654)) / **LongBench** ([arXiv:2308.14508](https://arxiv.org/abs/2308.14508)) | exact/structured answers over 13 synthetic tasks at configurable lengths; 21 datasets, avg 6,711 words (EN) | retrieval answers are strings, but lie about *capability*: "despite achieving nearly perfect accuracy in the vanilla NIAH test, almost all models exhibit large performance drops as the context length increases" | difficulty laddered by length so a single easy configuration cannot stand in for the capability |
| **Inspect** (UK AISI) ([metrics](https://inspect.aisi.org.uk/metrics.html), [eval logs](https://inspect.aisi.org.uk/eval-logs.html)) | scorer + **reducer over epochs**; `accuracy`, `stderr`, `bootstrap_stderr` ("1000 samples … by default"), `ci()` (Student-t or percentile bootstrap), **`ci_wilson()` "prefer this over `ci()` for binary scores"**, clustered standard errors | scorer is a function over the sample; free-form is handled by `model_graded_qa` | ships a **`krippendorff_alpha()`** metric for "agreement across multiple judges or scorers" and a `multi_scorer()` + `collect` reducer to produce per-judge ratings |

Three patterns are near-universal and this repo has none of them:

1. **A typed extraction step before grading.** lm-eval never compares prose; it runs a filter and compares
   the extracted value. Our `grade_v3`/`grade_v4` compare *token presence in prose* — a strictly weaker
   operation, and GRADER-FITNESS §5 already names exactly what it cannot check.
2. **A ground truth that is executed or read from source** (SWE-bench tests, τ-bench DB state,
   LiveBench objective values). Our `measure/det-verify-matrix.json` already has the right idea —
   `ground_truth: "AST of the cited source file; never the fixture's expected string and never token
   presence"` — but only 8 of the acceptance checks are `decidable`, and 12 decide nothing.
3. **An uncertainty statement on every number.** lm-eval prints bootstrap SE next to each metric; Inspect
   makes Wilson intervals the recommended binary-metric interval. Our `analyze_longrun.py` prints `n` but
   no interval on `checkpoint_accuracy`.

---

## 2. Grading reliability: how brittle each option is, with numbers

### 2.1 Exact match and regex are brittle in both directions — measured on our own corpus

From [GRADER-FITNESS.md](../experiments/ptr-engine/measure/GRADER-FITNESS.md) (28 hand-written probes × 4
fixtures, replayed through the real grader CLIs):

- `grade_v3`: **FN 16/52 = 30.8 %**, **FP 20/44 = 45.5 %**; `grade_v4`: **FN 14/52 = 26.9 %**,
  **FP 22/44 = 50.0 %`.
- The defects are concrete and reproducible: `"ANSWER: 64."` is *rejected* because a full stop follows the
  numeral, while `"ANSWER: 64 is wrong; the default is 32 refs."` is *accepted* because 64 is present.
- The 8/9-token `cp.2.t46` probes with **opposite meaning** are both accepted by R2 — one wording rejection
  traded for one inversion accept (FN −3.8 pp, FP +4.5 pp).

This is not a local curiosity; it is the documented failure mode of lexical grading. The relevant lesson
from the field is that **a grader must be validated on probes whose intent is known**, which is what our
`measure/` corpus does — and then *gated*, which ours does only in `det-verify-matrix.json` (gate:
`FN == 0 AND FP == 0` over the decidable subset) and not in the arm pipeline.

### 2.2 Model-as-judge: real but bounded, and measured against humans

- **Agreement.** MT-Bench/Chatbot Arena report that "strong LLM judges like GPT-4 can match both controlled
  and crowdsourced human preferences well, achieving **over 80 % agreement**, the same level of agreement
  between humans" ([arXiv:2306.05685](https://arxiv.org/abs/2306.05685)).
- **Position bias is large.** "**Only GPT-4 outputs consistent results in more than 60 % of cases**" when
  the two candidate answers are swapped (Table 2 of the same paper). A judge that flips the winner on a
  swap more than a third of the time cannot be a primary metric for a small-N comparison.
- **Order is a hackable lever.** [arXiv:2305.17926](https://arxiv.org/abs/2305.17926): "Vicuna-13B could
  beat ChatGPT on **66 over 80 tested queries** with ChatGPT as an evaluator" purely by altering answer
  order; the proposed fix is balanced-position calibration (aggregate both orders) plus human-in-the-loop.
- **Verbosity and self-enhancement** are the other two named biases in MT-Bench; both bias *toward fluent,
  longer, in-family* answers — exactly the direction our arms differ in. A prose judge would reward the arm
  that writes more prose, not the arm that is right.
- **Validation is a procedure, not a claim.** The pattern in the field is: collect human votes (MT-Bench
  3K expert + 3K crowdsourced), report agreement, report the disagreement cases. We have 28 probes and no
  human votes; our agreement number is *probe-fit*, not human agreement, and it must be reported as such.

### 2.3 Unit-test grading (SWE-bench style) is the alternative that removes the parse

Where the answer is a change to a repo, the field grades the **effect**: apply the patch, run the task's
tests, pass = success ([SWE-bench](https://arxiv.org/abs/2310.06770)). This is what our fixtures already
support (`tests/test_scope.py`, 9 tests; `predict_billed(...)` equalities; `COMPACT_MAGIC`). It costs
**zero inference requests** and has no FN/FP of its own — its failure mode is different and must be stated:
a test can be satisfied by cheating.

### 2.4 Test-based grading is gameable too — and the field measures how much

[SWE-Bench+ (arXiv:2410.06992)](https://arxiv.org/abs/2410.06992) manually screened SWE-Agent+GPT-4
"successes" and found "**32.67 % of the successful patches involve cheating** as the solutions were directly
provided in the issue report or the comments". Consequence for us: checkpoint tests must not be derivable
from text already visible in the run (the fixture's expected string, a docstring, a comment in an earlier
turn). The 32.67 % figure is the size of the leak channel when the task statement contains the answer.

### 2.5 Constrained output / structured answer contract

Every large serving stack can now force a schema:
[vLLM structured outputs](https://github.com/vllm-project/vllm/blob/main/docs/features/structured_outputs.md)
generates under xgrammar/guidance and takes `{"structured_outputs": {"json": ...}}`, `{"regex": ...}`,
`{"choice": ...}`, `{"grammar": ...}` — note the v0.12.0 rename from the old `guided_json`/`guided_regex`
fields, so a caller pinning the old names silently loses enforcement on upgrade. OpenAI's strict
`json_schema` response format is the vendor analogue (vendor claim; see §9 note — not re-fetched in this
run).

The point of a contract is not style. It is that **grading becomes decidable**: a JSON object either parses
against the schema and carries a typed value, or it does not. §8 specifies the contract this repo should
adopt.

---

## 3. The statistics a claim needs

### 3.1 The design questions, in the order the field asks them

1. **What is the unit of analysis?** Items (checkpoints), not runs. Paired comparisons need the *same*
   items in both arms; ours are the same fixture checkpoints, so pairing is available — at n = 3 items.
2. **What test for paired binary outcomes?** **McNemar's exact test** on the discordant pairs (b, c). Its
   null is that a pair is equally likely to favour either arm (b ~ Binomial(b + c, ½)). This is the standard
   recommendation for comparing two classifiers on the same test items (Dietterich, *Neural Computation*
   10(7), 1998 — cited here, not re-fetched this run). It uses only the items where the arms disagree,
   which is why it is far cheaper than an unpaired comparison.
3. **How wide is the interval?** For binary accuracy use **Wilson** rather than normal-approx: Inspect's docs
   say to "prefer this over `ci()` for binary scores … the bounds always stay within [0, 1] and remain well
   calibrated for small samples and proportions near 0 or 1" ([Inspect metrics](https://inspect.aisi.org.uk/metrics.html)).
   lm-eval and Inspect both offer **bootstrap** SEs for non-binary metrics.
4. **What about a tail latency like p95?** A percentile is an **order statistic**; its CI is driven by
   ranks, not by the mean. This is the single most under-appreciated item in our METRICS.md, which already
   says p95 over 48 turns is "estimated from ≤48 samples … a hint, not a bound".
5. **What about repeated trials?** **pass@k** = chance at least one of k trials succeeds, with the unbiased
   estimator `1 − C(n−c, k)/C(n, k)` from [Codex (arXiv:2107.03374)](https://arxiv.org/abs/2107.03374),
   implemented in [`human_eval/evaluation.py`](https://github.com/openai/human-eval/blob/master/human_eval/evaluation.py).
   **pass^k** is its dual: chance *all* k trials succeed, for reliability ([τ-bench](https://arxiv.org/abs/2406.12045)).
   Our arm comparison is a reliability question, so pass^k is the right family, not pass@k.
6. **Multiplicity.** With 4 arms there are 6 pairwise comparisons. Either pre-register **one** contrast
   (this repo already does: `pointer-stable` vs `transcript-grow`, frozen in
   [METRICS.md](../experiments/ptr-engine/longrun/METRICS.md) §0) or apply a correction (Bonferroni:
   α = 0.0083 for 6 tests). Reporting "whichever arm looked best" is the failure mode the correction prevents.
7. **Pre-declaration.** [Adding Error Bars to Evals (arXiv:2411.00640)](https://arxiv.org/abs/2411.00640)
   frames evaluations as experiments whose questions come from "an unseen super-population" and gives
   formulas for "analyzing evaluation data, measuring differences between two models, and **planning an
   evaluation experiment**". Our `ANCHOR-PREREG*.md` / `TASKS-V2-PREREG.md` files are that idea, applied to
   arms but not yet to *analysis*.

### 3.2 Arithmetic this run computed (exact binomial; no simulation)

**Paired McNemar, exact two-sided, all discordant pairs favouring one arm.** Minimum discordant pairs to
reach p < 0.05: `2·0.5^D < 0.05` → **D = 6** (0.03125); D = 5 gives 0.0625, not significant.

**Power at α = 0.05 (two-sided), exact test**, q = share of discordant pairs favouring the better arm:

| q | discordant pairs D needed for 80 % power |
|---|---|
| 0.65 | 90 |
| 0.70 | 49 |
| 0.75 | 30 |
| 0.80 | 20 |

**Unpaired comparison (two independent proportions), 80 % power, α = 0.05, for contrast:**

| comparison | n per arm |
|---|---|
| 0.50 vs 0.60 | 385 |
| 0.50 vs 0.55 | 1,562 |
| 0.70 vs 0.80 | 290 |
| 0.80 vs 0.90 | 196 |

Pairing on the same items is what makes a 30–50-item study possible at all; without it, ~200–1,500 items
per arm are needed for the effects we care about.

**Attenuation by grader error.** With FN = P(reject | correct) and FP = P(accept | incorrect), an arm's
*observed* success rate is `(1−FN)·p + FP·(1−p)`, so a difference between arms is scaled by
`1 − FN − FP`:

| grader | 1 − FN − FP | a true 10 pp gap appears as | a true 20 pp gap appears as |
|---|---|---|---|
| `grade_v3` (FN .308, FP .455) | **0.237** | 2.4 pp | 4.7 pp |
| `grade_v4` (FN .269, FP .500) | **0.231** | 2.3 pp | 4.6 pp |

A noisy grader does not merely widen the interval — it **shrinks the effect by ~4.2×**, and to recover the
same power you need roughly 4.2² ≈ 18× the items. That single line is the strongest argument against fixing
the sample size before fixing the grader.

**Wilson 95 % intervals at our current n = 3:**

| observed | Wilson 95 % CI |
|---|---|
| 0/3 | (0.000, 0.562) |
| 1/3 | (0.061, 0.792) |
| 2/3 | (0.208, 0.939) |
| 3/3 | (0.438, 1.000) |

Two arms that both score 2/3 on the same three items have **identical** intervals; no arrangement of 3
binary cells separates them.

**p95 latency: how many samples before the CI means anything** (order-statistic CI, binomial ranks):

| n timing samples | 95 % CI for p95 spans |
|---|---|
| 3 | everything (min … max) |
| 7 | 4th-largest … max |
| 12 | 4th-largest … max |
| 48 | 8th-largest … max |
| 96 | 11th-largest … max |
| 192 | 18th-largest … 4th-largest |
| 480 | 36th-largest … 15th-largest |

Our live cell gives ≤48 timing samples per arm (and the policy file had **n = 3–7** before that), so a "2×
better p95" decision rule is currently comparing two samples whose intervals both extend to the maximum. A
p95 claim needs **n in the hundreds** — 192 turns is four 48-turn runs per arm; 480 is ten.

---

## 4. Contamination and leakage

- **Public suites rotate and source-late.** LiveBench's three design constraints are "(1) frequently-updated
  questions from recent information sources, (2) scores answers automatically according to objective
  ground-truth values, (3) a wide variety of challenging tasks" ([arXiv:2406.19314](https://arxiv.org/abs/2406.19314)).
  Recency is the contamination control.
- **Human validation is a contamination control too.** SWE-bench Verified exists because a task can be
  under-specified or trivially leaked; 500 engineer-validated problems replaced the raw 2,294 for headline
  claims ([repo](https://github.com/SWE-bench/SWE-bench)).
- **Solution leakage inside the task text is measured, not hypothetical:** 32.67 % of SWE-Agent+GPT-4
  "resolutions" were cheating because the patch was already in the issue report
  ([SWE-Bench+, arXiv:2410.06992](https://arxiv.org/abs/2410.06992)).
- **What applies to a private fixture.** The model cannot have memorised `LR-01.json`; the risks are the
  other two: (a) **the answer is visible in the run** — a docstring, a test, an earlier turn's output (this
  is the 32.67 % channel), and (b) **our own artifacts leak into the model's context** — the fixture's
  `expected` field, a grading transcript, a repair hint. [TASKS-V2-PREREG.md](../experiments/ptr-engine/longrun/TASKS-V2-PREREG.md)
  and `RUN-C-PLAN.md` control arm prompts, but there is no automated check that the expected value is
  absent from the visible workspace at grading time. LiveBench-style rotation is not needed; a **canary +
  visibility check** is.

---

## 5. Reporting conventions for agent runs

- **Success is an end state, not a sentence.** τ-bench compares "the database state at the end of a
  conversation with the annotated goal state"; SWE-bench applies a patch and runs tests. Both make the
  transcript non-load-bearing for grading, which is what lets them report a single comparable number.
- **Report consistency, not just capability.** τ-bench's headline is that gpt-4o reaches pass^1 ≈ 61 % on
  τ-retail and ≈ 35 % on τ-airline but "pass^8 < 25 % in retail" — the drop *is* the finding
  ([arXiv:2406.12045](https://arxiv.org/abs/2406.12045)). Our 4 arms are a consistency question.
- **Separate model capability from harness capability.** SWE-agent attributes a large part of its gain to
  the agent-computer interface and reports pass@1 12.5 % on SWE-bench and 87.7 % on HumanEvalFix "far
  exceeding the previous state-of-the-art achieved with non-interactive …" baselines
  ([arXiv:2405.15793](https://arxiv.org/abs/2405.15793)). A quality comparison between arms whose
  *prompts, retry policy or context assembly* differ is a harness comparison; the field's convention is to
  hold the harness fixed and vary the model, or to state plainly that the comparison is harness-level.
- **Log the run configuration, the errors, the retries and the reduction.** Inspect's log schema records
  `status`, `plan` ("list of solvers and model generation config"), `error` "including traceback",
  `reductions` "for multi-epoch evaluations", and states that "by default, Inspect logs the raw model API
  request and response for the first few calls per model (as well as all error calls)"
  ([eval logs](https://inspect.aisi.org.uk/eval-logs.html)). Our rows carry `answer_source`,
  `truncated`, `latency_s`, and METRICS.md §8's VALIDITY block — the same idea, weaker on retry accounting.
- **Budget accounting.** A turn budget is only meaningful with the request/retry ledger beside it; τ-bench's
  user-simulator turns and SWE-bench's test executions are both charged. Our `tokens_to_verified_success`
  charges repairs to the causing arm (METRICS.md §3), which is the right convention; the missing piece is
  an explicit **tool-call and retry count per turn**, so a harness-level difference (an extra retry that
  rescued a turn) is visible rather than folded into "the model did better".

---

## 6. ADOPT / REJECT / MODIFY, aimed at this repo

Costs are in card rounds (one unit each), requests (inference), and code.

| # | practice | artifacts touched | concrete change | cost | verdict |
|---|---|---|---|---|---|
| 1 | **Decidable JSON answer contract** (§8) | `longrun/run_longrun.py` (checkpoint prompt), `longrun/grade_v3.py`, `longrun/grade_v4.py`, `longrun/fixtures/LR-0N.json` checkpoints | checkpoint answer is a schema-constrained object; grading parses and compares typed values; prose graders demoted to diagnostics | 1 card, 0 requests, ~150 LOC | **ADOPT** |
| 2 | **Unit-test / state grading** (SWE-bench, τ-bench) | `longrun/fixtures/*` (tests already exist: `tests/test_scope.py`, `predict_billed`), `measure/det-verify-matrix.json` handlers | grade the workspace at the checkpoint (run the test, read the symbol) instead of the sentence; extend `CHECK_HANDLERS` to all 12 acceptance checks | 2 cards, 0 requests, ~250 LOC | **ADOPT** |
| 3 | **Prose-token grading as primary accuracy** | `grade_v3.py`, `grade_v4.py`, `analyze_longrun.py` | stop reporting `checkpoint_accuracy` from token presence; keep the graders as a *diagnostic* column labelled "mention behaviour" (already GRADER-FITNESS §"Consequence") | 1 card, 0 requests | **REJECT as primary** (MODIFY to diagnostic) |
| 4 | **Per-headline CI** (Wilson / bootstrap) | `longrun/analyze_longrun.py`, `measure/METRICS.md` | every accuracy and tokens-to-success row prints Wilson 95 % CI (binary) or bootstrap CI (continuous), plus `n` | 1 card, 0 requests | **ADOPT** |
| 5 | **McNemar exact on item-level pairs** | `analyze_longrun.py`, new `measure/analysis` module | compare arms on the same checkpoint ids; report b, c, exact p, and the discordant count; refuse the comparison when D < 6 | 1 card, 0 requests | **ADOPT** (with the n gate of §7) |
| 6 | **pass^k consistency over reruns** | `run_longrun.py` (add `--runs R`), `analyze_longrun.py` | R reruns per arm; report pass^R with the `1 − C(n−c,k)/C(n,k)` family estimator and per-checkpoint stability | 1 card + R× run cost | **ADOPT at R = 3** |
| 7 | **p95 "≥ 2× better" decision rule at n ≤ 48** | `ptr-engine/LONGRUN-PREREG.md`, `longrun/METRICS.md` §1 | p95 CI at n = 48 spans the 8 largest observations; either raise to ≥192 timing samples per arm (4 runs) or replace the 2× rule with a CI-overlap rule | 1 card, run cost only | **REJECT as frozen rule** → MODIFY |
| 8 | **One pre-registered contrast, no correction needed** | `METRICS.md` §0 frozen rule | already correct — keep, and state it in the analysis JSON so an exploratory 6-way scan cannot be passed off as pre-registered | 0 cards | **ADOPT (already)** |
| 9 | **Judge validation probes as a gate** | `measure/det-verify-matrix.json`, `tools/grader_fitness.py` | gate is already `FN == 0 AND FP == 0` over the decidable subset — make it block arm reporting, not just exist as a matrix | 1 card, 0 requests | **ADOPT** |
| 10 | **Multi-judge agreement (Krippendorff α / human votes)** | — | we have two judges that both fail and no human rater set; α over two bad judges measures nothing | — | **REJECT for now** (revisit if a third judge passes the probe gate) |
| 11 | **Contamination canary + answer-visibility check** | fixture loader, `run_longrun.py` pre-flight | assert the fixture's `expected` value and any grading transcript are absent from the visible workspace at checkpoint time; add one canary string per fixture | 1 card, 0 requests | **ADOPT** |
| 12 | **Structured output enforcement at the server** | serving config (sibling card), `run_longrun.py` request builder | pin the post-v0.12 `structured_outputs` field names, not `guided_json`; record whether enforcement was on in the run row | 1 card, 0 requests | **ADOPT** |
| 13 | **Multi-metric reporting (HELM)** | `analyze_longrun.py` output | report accuracy *with* tokens-to-verified-success, elapsed time and false-claim rate side by side; no single headline | 1 card, 0 requests | **ADOPT (partially there)** |
| 14 | **Model-graded rubric templates (openai/evals)** | — | we already have hand-rolled judges; adding a template library does not fix the FN/FP | — | **REJECT** |
| 15 | **Exact match with normalisation** | `grade_*.py` numeric checks | normalise trailing punctuation and whitespace before comparison (fixes the `"ANSWER: 64."` FN) while keeping the inversion FP unresolved — which is why #1 is the real fix | folded into #1 | **MODIFY** |

---

## 7. The direct question: given 3 checkpoints per 48-turn run and 4 arms, how many runs before one arm can be called better on quality?

**Answer: no number of runs. Not 10, not 100.** The reason is not sample size; it is that the analysis unit
is the item and there are only three items. Here is the arithmetic.

**Step 1 — one run cannot reach significance, at any effect size.** A paired McNemar test on 3 paired items
has at most D = 3 discordant pairs, and its smallest attainable two-sided p is `2·0.5³ = 0.25`. Even if arm
A is right on all three checkpoints and arm B wrong on all three, p = 0.25. The minimum is D = 6 (§3.2).

**Step 2 — more runs do not add items.** Rerunning the same 3 checkpoints R times produces 3 clusters of R.
The independent units are still 3, and a cluster-honest test collapses to 3 pairs. The claim you are
entitled to after any R is "on these three checkpoints, arm A differed" — which is what we already say, and
what the operator cannot use for "equal-or-better quality". Pooling across runs while ignoring the clustering
inflates significance by ~√R and is the specific error [Adding Error Bars to Evals](https://arxiv.org/abs/2411.00640)
warns about.

**Step 3 — the grader destroys most of the signal anyway.** With `grade_v3`, observed Δ = 0.237 × true Δ;
with `grade_v4`, × 0.231. A true 20 pp advantage is measured as ~4.6 pp, and the per-checkpoint instrument
error on cp.0/cp.1/cp.2 is 33–50 % in each direction (GRADER-FITNESS §3). The noise floor is larger than the
effect we would be trying to detect.

**Step 4 — what would be needed.** With *decidable* grading (FN = FP = 0 by construction) and a paired
design, D is the binding constraint:

| q (share of discordant pairs favouring the better arm) | D needed | items needed at ~1/3 discordance | items needed at ~1/2 discordance |
|---|---|---|---|
| 0.70 | 49 | ~147 | ~98 |
| 0.75 | 30 | ~90 | ~60 |
| 0.80 | 20 | ~60 | ~40 |

**Step 5 — the cheapest design that can actually make the claim.**

| design | distinct decidable checkpoints / run | runs per arm | paired items per arm pair | max D | can detect | added checkpoint requests |
|---|---|---|---|---|---|---|
| current | 3 (prose) | 1 | 3 | 3 | nothing (p ≥ 0.25) | 0 |
| A | 12 | 3 | 36 | 36 | q ≥ 0.72 | 9 × 4 arms × 3 = **108** |
| B | 16 | 3 | 48 | 48 | q ≥ 0.70 | 13 × 12 = **156** |
| C | 3 | 8 | 24 | 24 | q ≥ 0.78 only | 0 extra checkpoints, but 32 run-cells ≈ 1,536 turns |

**Recommendation: design A.** Twelve decidable checkpoints per 48-turn run (one every four turns), three
runs per arm (which also gives pass^3), graded from workspace state — 36 paired items, 108 extra checkpoint
requests in total for four arms, and no prose judge anywhere in the decision path. Design C is cheaper in
checkpoints but only detects very large effects and multiplies the expensive part (48-turn runs) by 8.

**Test to use, stated exactly:** per checkpoint pair, record (A correct, B correct); count b = A-only,
c = B-only; run the **exact McNemar test** on (b, c), two-sided, α = 0.05, with the single pre-registered
contrast `pointer-stable` vs `transcript-grow` (so no multiplicity correction is owed); report b, c, p and
the observed difference **with Wilson 95 % CIs per arm**; report pass^3 per checkpoint. If D < 6, report
"insufficient evidence" rather than a direction.

---

## 8. Answer-contract specification

The output shape a model must emit at a checkpoint so that grading is *decidable* rather than parsed from
prose. Four claim kinds cover every checkpoint in `fixtures/LR-0N.json`.

```json
{"cp":"cp.0.t12","kind":"value",
 "target":{"path":"ptr_engine/resolve.py","symbol":"DEFAULT_MAX_REFS","line":39},
 "op":"==","value":64,
 "evidence":"DEFAULT_MAX_REFS = 64"}

{"cp":"cp.1.t24","kind":"value",
 "target":{"path":"ptr_engine/errors.py","symbol":"PtrError.__subclasses__()"},
 "op":"count","value":31,
 "evidence":"31 Ptr* classes registered"}

{"cp":"cp.2.t46","kind":"assertion",
 "target":{"path":"ptr_engine/resolve.py","symbol":"_refuse","line":66},
 "op":"property","value":"ledger_row_written_before_raise",
 "evidence":"row commit precedes raise in _refuse"}

{"cp":"acc.n2b","kind":"prohibition",
 "target":{"path":"tests/test_scope.py"},
 "op":"not_modified","value":true,
 "evidence":"file hash unchanged since turn 0"}
```

**Grading rule (deterministic, 0 requests):**

1. `parse` the object against the JSON schema; a parse failure is a **repair turn**, charged to the arm
   (METRICS.md §3 already charges repairs) and counted in the retry ledger.
2. `kind: value` → read `target.path`, locate `symbol` (AST), evaluate the literal with `ast.literal_eval`,
   compare under `op` (`==`, `count`, `<=`). The asserted value, not the presence of a numeral, is what is
   checked — this closes both FN `"ANSWER: 64."` and FP `"64 is wrong, it is 32"`.
3. `kind: assertion` → run the one targeted test that encodes the property (e.g. monkeypatch the ledger and
   assert a row exists before the raise propagates). Test-based, SWE-bench style.
4. `kind: prohibition` → compare the file's hash against the pre-run snapshot; no textual interpretation.
5. `evidence` is capped at 120 characters and is **recorded, never graded** — it exists to make the row
   auditable and to feed the false-claim metric.

**Enforcement.** Server-side guided decoding with the post-v0.12 vLLM field
`{"structured_outputs": {"json": <schema>}}` ([vLLM docs](https://github.com/vllm-project/vllm/blob/main/docs/features/structured_outputs.md)),
or the OpenAI `json_schema` strict response format where that is the route. The run row must record whether
enforcement was on; an unenforced run is a different instrument and must not be pooled with enforced ones.

**Token cost.** Measured on the four shapes above: 38–62 tokens per answer (mean ≈ 48), against ~20–40 tokens
for the current `ANSWER: <value>` sentence. A strict schema also adds a short `tools`/`response_format`
overhead to the request, not to the answer. At 12 checkpoints × 3 runs × 4 arms = 144 answers, the contract
costs ≈ **7 k completion tokens** in total — negligible next to the run cost, and it buys a grader with
FN = FP = 0 on the decidable set.

---

## 9. Sources, and what is not verified

**Fetched and read in this run** (primary: paper abstract/full text, or the repository's own docs):

- lm-evaluation-harness: [task guide](https://github.com/EleutherAI/lm-evaluation-harness/blob/main/docs/task_guide.md),
  [metrics.py](https://github.com/EleutherAI/lm-evaluation-harness/blob/main/lm_eval/api/metrics.py),
  [README](https://github.com/EleutherAI/lm-evaluation-harness)
- [Inspect metrics](https://inspect.aisi.org.uk/metrics.html), [Inspect eval logs](https://inspect.aisi.org.uk/eval-logs.html)
  (raw `docs/metrics.qmd`, `docs/eval-logs.qmd` in [UKGovernmentBEIS/inspect_ai](https://github.com/UKGovernmentBEIS/inspect_ai))
- [openai/evals eval-templates](https://github.com/openai/evals/blob/main/docs/eval-templates.md),
  [build-eval](https://github.com/openai/evals/blob/main/docs/build-eval.md)
- [SWE-bench repo README](https://github.com/SWE-bench/SWE-bench) (Verified: 500 engineer-validated problems),
  [SWE-bench_Verified dataset](https://huggingface.co/datasets/SWE-bench/SWE-bench_Verified)
- [vLLM structured outputs](https://github.com/vllm-project/vllm/blob/main/docs/features/structured_outputs.md)
- [human-eval estimator](https://github.com/openai/human-eval/blob/master/human_eval/evaluation.py)
- arXiv: [2211.09110](https://arxiv.org/abs/2211.09110) HELM · [2206.04615](https://arxiv.org/abs/2206.04615) BIG-bench ·
  [2310.06770](https://arxiv.org/abs/2310.06770) SWE-bench · [2410.06992](https://arxiv.org/abs/2410.06992) SWE-Bench+ ·
  [2311.12983](https://arxiv.org/abs/2311.12983) GAIA · [2406.12045](https://arxiv.org/abs/2406.12045) τ-bench ·
  [2406.19314](https://arxiv.org/abs/2406.19314) LiveBench · [2404.06654](https://arxiv.org/abs/2404.06654) RULER ·
  [2308.14508](https://arxiv.org/abs/2308.14508) LongBench · [2306.05685](https://arxiv.org/abs/2306.05685) MT-Bench judge ·
  [2305.17926](https://arxiv.org/abs/2305.17926) Fair Evaluators · [2411.00640](https://arxiv.org/abs/2411.00640) Error Bars ·
  [2405.15793](https://arxiv.org/abs/2405.15793) SWE-agent · [2107.03374](https://arxiv.org/abs/2107.03374) Codex

**Cited but not re-fetched in this run** (standard references; treat the citation, not a quoted number, as the claim):

- McNemar's exact test as the paired-classifier recommendation: Dietterich, *Approximate Statistical Tests
  for Comparing Supervised Classification Learning Algorithms*, Neural Computation 10(7), 1998,
  [doi:10.1162/089976698300017197](https://doi.org/10.1162/089976698300017197). The arithmetic in §3.2 and §7
  follows directly from the binomial null and was computed here, so it does not depend on that citation.
- OpenAI strict `json_schema` structured outputs as the vendor analogue of vLLM guided decoding —
  [platform docs](https://platform.openai.com/docs/guides/structured-outputs); **vendor claim**, not verified
  in this run (the docs site is JS-rendered and was not fetched).

**Unverified / contested:**

- **GAIA scoring detail.** The abstract gives the 92 % vs 15 % human/agent gap; how the final answers are
  string-matched and how the held-out test answers are administered was **not** verified here — the GAIA repo
  README did not state it in the part read.
- **"GPT-4 achieves >80 % agreement"** is a *pairwise-preference* agreement on MT-Bench/Chatbot Arena
  conversations, not agreement on factual checkpoint answers. Applying it to our checkpoint grading would be
  a category error; it is cited in §2 as the size of the ceiling, not as a licence to use a judge here.
- **The 33–50 % per-checkpoint instrument error** is measured on 5–7 probes per checkpoint in
  GRADER-FITNESS §2; those intervals are themselves wide, so the exact per-checkpoint rate is uncertain even
  though the both-directions failure is proven by the specific probes in §3.
- **BIG-bench free-form scoring** is described here only as "programmatic where machine-checkable, human
  evaluation otherwise"; the exact split was not re-read from the paper's task list.
- **Contamination**: no source read in this run quantifies leakage for a *private* fixture, because the
  literature's problem is memorisation of public data. This document's claim that our risk is
  answer-visibility-in-run is an inference from SWE-Bench+ (32.67 %), not a directly published result.
