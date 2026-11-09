# BUDGET-SCHEDULE — what the 3,219 remaining requests buy

**Unit:** `BUDGET-SCHEDULE`. **Requests spent:** 0 (offline; no network, no inference, no git).
**Consumes:** `experiments/ptr-engine/measure/REQUEST-LEDGER.json` (`REQUEST-LEDGER`, `a2c4508e`),
`experiments/ptr-engine/measure/PROJECTION.json` (`PROJECTION-CALIBRATION`, `c0c7d1c8`), and the frozen
rule `docs/PREREG-ARM-RUN.md` (`PARM-1`). **Edits to any of them: 0.** Machine-readable twin:
[`budget-schedule.json`](budget-schedule.json).

This document prices. It does not measure, does not re-open a threshold, and invents no cost.

## 1. The numbers this card consumes, and where they come from

| quantity | value | source |
|---|---|---|
| quota cap | 4,320 requests | `REQUEST-LEDGER.json` → `budget.cap` |
| spent | 1,101 requests | `REQUEST-LEDGER.json` → `budget.spent` (`total.requests` = 1,101) |
| remaining | **3,219 requests** | `REQUEST-LEDGER.json` → `budget.remaining` |
| corpus rows that are model turns | 801 | `rows-*.jsonl`, field `kind` = `turn` (14 files, 1,101 rows) |
| tool-follow-up rows | 68 | field `kind` = `tool-followup` |
| unmarked rows, counted as billed | 232 | `REQUEST-LEDGER.json` → `total.assumed_billed` |
| per-turn request factor | **1.374532** = 1,101 ÷ 801 | derived here from the two lines above |
| s/turn, thinking off (n=960) | p50 2.9 · p90 38.1 · mean 27.5 | `PROJECTION.json` → `groups[2]` |
| s/turn, thinking on/auto (n=9) | p50 218.2 · p90 682.7 · mean 190.9 | `PROJECTION.json` → `groups[1]` |
| s/completion-token | 0.0338 off · 0.0288 live · 0.0349 on/auto | `PROJECTION.json` → `groups[*].ratio_s_per_completion_token` |
| policy per-turn wall | 60 s | `PROJECTION.json` → `defaults.projected_turn_wall_s` |
| abort cap (**not** a per-turn wall) | 180 s | `PROJECTION.json` → `defaults.turn_wall_cap_s` |

**The factor is not one request per turn.** The ledger's own corpus decomposes as
1.000 `turn` + 0.0849 `tool-followup` + 0.2897 unmarked per turn row. The four *controlled* longrun
grids ran at exactly 1.000 request/turn (`rows-longrun-c-2026-10-26.jsonl`: 192 rows / 192 turns); the
excess comes from agentic rows. Pricing at **1.374532** is the conservative, measured-today number, and
it is the one used below. A scripted cell prices 27 % cheaper — that is an optimistic bound, not the plan.

## 2. Three schedules, priced in requests and wall hours

Wall is stated for the **adjudicating grid's frozen `thinking = off`** policy (PARM-1 line 151). The
60 s column is the harness policy wall; the `on/auto` column is descriptive only — a thinking-on run can
never support H1 whatever it costs.

| # | shape | model turns | **requests** | **wall, off: p50 / mean / p90** | wall @60 s policy | **remaining after** | on/auto mean (descriptive) |
|---|---|---|---|---|---|---|---|
| **A** | 4 arms × **60** turns × 3 reps | 720 | **990** | 0.58 h / 5.50 h / 7.62 h | 12.0 h | 2,229 | 38.2 h |
| **A\*** | 4 arms × **48** turns × 3 reps (frozen grid) | 576 | **792** | 0.46 h / 4.40 h / 6.10 h | 9.6 h | 2,427 | 30.5 h |
| **B** | 4 arms × 60 turns × 1 rep | 240 | **330** | 0.19 h / 1.83 h / 2.54 h | 4.0 h | 2,889 | 12.7 h |
| **C** | 4 arms × 48 turns × 1 rep (config-C shape) | 192 | **264** | 0.16 h / 1.47 h / 2.03 h | 3.2 h | 2,955 | 10.2 h |

Each row's turn count is the arm × turn × rep product; wall is turns × the per-turn percentile, not
requests × wall, because a follow-up row is part of a turn, not a second turn.

**A carries a defect the other rows do not.** PARM-1 line 137 fixes *Turns per arm = 48* — fixture
`LR-01.v6.json`, `N = 48`, with the 12 checkpoints at turns {6, 8, 12, 14, 18, 20, 24, 26, 32, 36, 42, 46}.
A 60-turn cell therefore needs a **new fixture and a re-frozen rule hash**, which this card is forbidden to
produce. The card's "60 turns" and PARM-1's "48 turns" disagree; the arithmetic is done both ways and **A\***
is the frozen-compatible reading. A 60-turn run is *fundable* (990 < 3,219) — it is not *comparable*.

**Config-C corroboration:** `rows-longrun-c-2026-10-26.jsonl` already exists with exactly C's shape
(192 rows = 4 arms × 48 turns, 1 request per turn), which is what makes C a priced repetition rather than
a guess.

## 3. What each schedule can and cannot conclude (PARM-1's terms)

| schedule | H1 (p95 TTFT) | H2 (prompt tokens/turn) | H3 (quality, 2/12 margin + McNemar veto) |
|---|---|---|---|
| **A** (60×3) | evaluable (180 raw/arm, 120 spare) — *if* the fixture is re-frozen | evaluable | evaluable; 36 paired items; b+c ≥ 6 reachable |
| **A\*** (48×3) | **evaluable** — 144 raw/arm, 84 exclusions of headroom | **evaluable** | **evaluable**; 36 paired items |
| **B** (60×1) | **knife-edge**: exactly n = 60, so 60·0.05 = 3.0 = `TAIL_MIN` exactly; **one** `ttft_source = unavailable` row → n = 59 → `quantile_ci` raises `InsufficientSamples` and H1 is **refused**, not caveated. At the frozen N=48 this shape is n=48 → refused outright | evaluable | evaluable on the margin only; **no between-rep variance, no standard error on quality**; 12 pairs |
| **C** (48×1) | **not evaluable at this n** — PARM-1 line 37 refuses n=48 by name | evaluable | **not evaluable**: the historical grid carried 3 v2 checkpoint ids, so the 12-item denominator does not exist |

Every no is a refusal, never a caveat: PARM-1 lowers no threshold for a small n, and this card lowers none.

## 4. Discordant-pair arithmetic

Paired items = 12 declared v6 checkpoints × reps; the McNemar veto is **licensed only at b + c ≥ 6**
(PARM-1 line 108).

| schedule | paired checkpoints (A vs C) | is b+c ≥ 6 reachable? |
|---|---|---|
| A | 36 | yes — needs 6 of 36 discordant (16.7 %), or 6 of 12 inside one rep |
| A\* | 36 | yes, same arithmetic |
| B | 12 | arithmetically yes (max 12) but needs **6 of 12 = a 50 % checkpoint flip rate** |
| C | **3** | **no — b+c ≤ 3 < 6, so the veto is unreachable by construction** |

The fixed margin does **not** pool: it is stated on the 12-item denominator, so each rep is its own
12-item read. Pooling 36 pairs widens the McNemar veto; it does not widen the margin.

## 5. Recommendation — A\*, with a stop rule the harness can refuse on

**Run A\*: 4 arms × 48 turns × 3 reps = 576 turns / 792 requests, 2,427 remaining, ~4.4 h expected
(6.1 h at p90, 9.6 h at the 60 s policy), thinking off.**

Predicates, all evaluated before the next cell starts (a ceiling without a stop rule is a wish):

1. `stop if requests_remaining < requests_for_next_cell` — next cell = 4 arms × 48 turns = 192 turns =
   264 requests at factor 1.374532.
2. `stop if any turn wall_ms/1000 > 180` (the `--turn-wall-cap` abort); the aborted turn is excluded, and
   if the arm is then left with < 60 usable timings H1 is reported **refused** with the estimator's own
   message.
3. `stop if ATTACK or V-GATE-CHAIN reports a defect after the run starts` — halt at the next cell boundary.
4. `stop if after rep 1 H3 vetos` (b+c ≥ 6 with exact two-sided p < 0.05 and C worse, or C loses more than
   2 of 12 checkpoints) — abandon reps 2–3, **saving 528 requests**.
5. `stop if either arm's grade_v5 decidable < 8 of 12` (H3 unadjudicable, PARM-1 line 113) — do not buy more
   reps for a quality-blind read.

Cell sizing matters: a 48-turn cell projects **2,880 s** at the 60 s policy (admitted under `--max-wall
3600`) but **20,529.6 s** at the measured live p90 of 427.7 s/turn (exit 8 — refused). Run 12 arm×rep
cells, not one 576-turn cell.

## 6. What the quota cannot fund

- Ceiling: 3,219 ÷ 1.374532 = **2,341 model turns** (3,218 requests, 1 left) — 12.19 reps/arm at N=48, 9.75
  at N=60.
- Whole-shape capacity: **12 reps/arm** at N=48 (2,304 turns, 3,167 requests); **9 reps/arm** at N=60
  (2,160 turns, 2,969 requests).
- **Four** independent 4-arm × 48-turn × 3-rep grids fit exactly (4 × 792 = 3,168, 51 left). A **fifth** does
  not (3,960 needed).
- Never at this quota: a 20-rep/arm power grid at N=48 (5,278 requests, short by 2,059); a fifth grid; and
  — for any budget — a **paired quantile test** for H1, which `analyze_stats.py` does not contain
  (PARM-1 lines 38–40). Requests buy narrower disjoint CIs, never a test that does not exist.
- Never at this quota: **between-rep quality variance** for any 1-rep schedule (B, C) — variance needs
  reps ≥ 2 by definition; and any **thinking-on H1 adjudication** (A\* at on/auto mean is 30.5 h, p90
  109.2 h, and PARM-1 line 151 excludes such grids regardless of spend).

The honest headline: **the quota is not the binding constraint on full PARM-1** — A\* costs 24.6 % of what
remains. Wall time, the frozen 48-turn grid, and the absence of a paired quantile test are the constraints.
A schedule that pretends otherwise would be the defect this card exists to prevent.

## 7. One operator decision

**Q:** run A\* on the frozen 48-turn grid, or extend `LR-01.v6.json` to 60 turns and re-freeze PARM-1?
**Default:** A\* — no re-freeze, keeps comparability with the 48-turn grids already on disk. The
alternative costs +198 requests, +1.6 h at the 60 s policy, and makes the prior grids non-comparable.
