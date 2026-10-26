# EVAL-PRACTICE-SURVEY

Card unit, 2026-10-26. Sibling: `SERVING-PRACTICE-SURVEY` (server measurement).
Operator directive (m00372): learn the process of testing models/agents from the internet and incorporate
what is validated.

## Objective

Bring in what the field knows about **evaluating models and agents** and decide what this repo adopts.
**Offline for the model under test: zero inference requests** — web research is the whole job. Write no
existing repo file; only the three declared paths.

## Bound

≤45 tool calls (generous; research is the point). Handoff written `status: partial` within the first 5 calls.
No subagents (board units must not delegate).

## Write paths

- `docs/EXTERNAL-EVAL-PRACTICE.md` (deliverable)
- `orchestration/units/EVAL-PRACTICE-SURVEY.md` (this card)
- `orchestration/handoffs/EVAL-PRACTICE-SURVEY.json`

## Method

1. Read the repo's own evaluation artifacts first, for grounding: `measure/GRADER-FITNESS.md`,
   `measure/det-verify-matrix.json`, `longrun/METRICS.md`, `longrun/SUITE.md`.
2. Read primary web sources: harness repositories and their docs (lm-evaluation-harness task guide + metrics.py,
   Inspect metrics/eval-logs, openai/evals templates, SWE-bench repo + Verified, vLLM structured outputs,
   human-eval pass@k estimator) and papers by abstract or extracted full text (HELM, BIG-bench, SWE-bench,
   SWE-Bench+, GAIA, τ-bench, LiveBench, RULER, LongBench, MT-Bench judge, Fair Evaluators, Adding Error Bars,
   SWE-agent, Codex).
3. Compute the statistics rather than quote them where the arithmetic is the deliverable: exact McNemar
   thresholds and power, two-proportion sample sizes, Wilson intervals, order-statistic CIs for p95.
4. Turn the findings into ADOPT/REJECT/MODIFY rows against named repo artifacts, with costs.

## Findings (summary; full text in the deliverable)

- Established suites grade an **effect** (tests, DB state, objective value), not prose; prose matching appears
  only for uncontrolled free-form, and model judges are validated against human votes before use.
- Our graders' measured FN 30.8 %/FP 45.5 % (v3) and FN 26.9 %/FP 50.0 % (v4) shrink an arm difference by
  **~4.2×** (1 − FN − FP = 0.237 / 0.231) and require ~18× the items to recover the same power.
- **3 checkpoints cannot support an arm ranking at any n**: max 3 discordant pairs → smallest attainable
  two-sided McNemar p = 0.25, and reruns only cluster the same 3 items.
- Cheapest design that can: **12 decidable checkpoints × 3 runs per arm** (108 extra checkpoint requests),
  exact McNemar on the single pre-registered contrast, Wilson CIs, pass^3.
- p95 at n ≤ 48 has a 95 % CI spanning the 8 largest observations; a p95 claim needs n in the hundreds.

## Assumptions (recorded, per workspace rule for automated sessions)

- "Validated findings" = published and reproduced in a paper or in a harness's own code/docs; vendor blog
  claims are labelled as vendor claims.
- No human rater set exists offline, so judge–human agreement cannot be measured here; the survey reports the
  field's agreement numbers instead and does not claim local agreement.
