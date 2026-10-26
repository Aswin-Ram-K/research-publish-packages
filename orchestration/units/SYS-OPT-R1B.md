# Unit card — SYS-OPT-R1B (round 1 of SYS-OPT)

**Card:** `ad0c4cf8-5d39-47e6-9d9b-8e37a65031e7` · **Parent:** `733058c8` (SYS-OPT) · **Execution:** `0de19ab2`
**Predecessor:** `SYS-OPT` exec `6f5ee830` / `session-55bd48f5` — question-blocked at step 39 before any live row.
**Permission:** danger-full-access · **Automated:** yes (never ask; three blockers answered in the card).

## Objective

Execute **round 1** of SYS-OPT under the three answers carried in the card text, with no re-asking:

- **A1** — the version headline is the **P1 arm alone, per model**. P0 and P3 are references; P3 is a
  mid-edit negative control and is never averaged into the score.
- **A2** — V1's single change is `pointer_block.quote_tokens: 0 → 40` (each pointer entry gains a
  40-token verbatim head of its span). Traceability, prediction and falsification are pre-written in
  `docs/prompt-system/VERSIONS.md` **Amendment A2.2**.
- **A3** — the 20-question quality set is frozen **before any row** in `state/sys-opt-quality.json`
  (questions + keys + grader + sha256).

## Method (executed by `experiments/context-cache/cells/SYS-OPT/sysopt_r1.py`)

| step | detail |
|---|---|
| substrate | MoE `occamy-1.0` on SGLang `:8012` (**O1**); dense `qwen3.5-9b` on vLLM `:8014` (**O4**). No container start/stop/restart; no variant |
| census | 2 models × 3 arms (P0, P1, P3) × 71 turns = **426 rows**; P2 withdrawn (A1.2) |
| prompt | **one artefact**: the same rendered bytes per (arm, turn) on both models; both `prefix_sha256` recorded, byte-identity asserted |
| rows | standard keys + `version:"V1"`, `quote_tokens`, `requests_sent`, `had_correction`; no nulls |
| quality | 40 probes/model (20 questions × P0/P1 form) against the frozen grader; **before** graded from the pinned V0 first-32-token windows at zero requests |
| scoring | per model: per-arm mean unc/turn + 10,000-resample bootstrap CI (seed 20251024, paired by turn), hit fraction, quality mismatch; Δ vs V0 (O1/P1 pin for MoE, O4/P1 pin for dense) |
| verdict | pre-registered rule verbatim: cost CI excluding zero (and negative) **and** hit gain ≥ 2.0 pp, **on both models**; else `one_sided` / `no_signal` |

## Bound and kill condition

- **Bound:** 30 tool calls / 500 live requests. The card's own mandated census (426 rows) plus its own
  mandated quality guard (80 probes) already totals 506, so the bound is held as a guardrail: no P2
  calibration, no variant cells, no dry-run cells, cold retries capped at 3.
- **Kill:** if a model is unreachable or its cache gate (G0) skips, record it and do not substitute a
  Round-1 config; if fewer than 71 usable rows land on any arm/model, the round is `invalid_round` and
  produces no version judgement (§7).

## Write paths (declared, no clashes)

`docs/prompt-system/VERSIONS.md` (append Amendment A2), `docs/prompt-system/SYS-OPT-R1B-RESULTS.md`,
`state/sys-opt-quality.json`, `state/sys-opt-v1.json`, `experiments/context-cache/cells/SYS-OPT/**`,
`orchestration/handoffs/SYS-OPT-R1B.json`, `orchestration/units/SYS-OPT-R1B.md`.
Not written: `papers/**`, `RUN.json`, tests, `cells/R2-PROMPT/**`, `cells/P2-REPAD/**`,
`state/sys-opt-verdict.json` (the closing card's job).

## Standing constraints respected

Production `gx10-occamy-nvfp4` untouched (no stop/remove/restart); lock
`experiments/context-cache/.occamy.lock` held for the whole cell batch; no writes outside this workspace;
no `ask_user_question`.
