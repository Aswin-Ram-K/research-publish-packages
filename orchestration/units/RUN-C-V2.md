# RUN-C-V2 — config C on LR-01.v2, executed

**Status:** partial · **Requests:** 192 · **Rows:** 192 · **Hours:** ~1.4
**Fixture:** `tasks-v2/runtime-v2/LR-01.v2.json` sha256 `0a07db1b…b90848` (not RUN-C-PLAN's older
`runtime/LR-01.json` `b7e303a6…a500`; the card names the v2 fixture and its dry-run says 192).

## Bounds and stops — nothing fired
- Dry-run exit **0**, `would_send_total=192` (48/arm). 6 h guard slack: 3837 s measured (1.07 h), 24-row projection 5184 s (1.44 h).
- Max single turn **152.2 s**; no arm had two turns > 600 s. Digest run==score `0a07db1b…`, `tampered: false`.
- `answer_source: none` 0/192; `finish_reason` stop 177 / length 15.

## Per-arm (analyze_longrun.py, 48 turns/arm)
| arm | p50 TTFT | p95 TTFT | TTVS | cp acc | over_budget | verified |
|---|---|---|---|---|---|---|
| transcript-grow | 482.24 | **838.85** | null | 0/3 | 18.8% (9/48) | false |
| transcript-compact | 202.49 | 224.08 | null | 0/3 | 0.0% (0/48) | false |
| pointer-stable | 167.02 | **356.12** | null | 0/3 | 2.1% (1/48) | false |
| lease-reopen | 134.96 | 201.78 | null | 0/3 | 35.4% (17/48) | false |

Scorer per arm: exit **1**, `verified_success false`, identical 12 pass / 11 fail.
## Frozen rule → **undecidable**
(i) 356.12/838.85 = **0.4245 ≤ 0.5 → TRUE** · (ii) TTVS null in both (0 successes) → not establishable ·
(iii) 0/3 vs 0/3 → TRUE, vacuous tie. Evaluated at final checkpoint t46 + verify t48; t60 unreachable at N=48.
## Tier **REJECTED**
over_budget 27/192 = **14.1%** (F2 ≥20/192). The runner emits no `over_budget` column, so it was computed
from `content` word counts — no re-prompt, no truncation.
## Not trustworthy as an arm comparison
All arms 0/3 checkpoints with the same failure set; compact answered ~15 words/turn; grow turn 2 was
byte-identical to turn 1. Only the latency ranking is measured.
