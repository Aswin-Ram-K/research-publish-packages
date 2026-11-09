# CONSONANCE-BC-EVAL — prospective evaluation protocol

**Status:** done (protocol only; no experiment, no model call, no live request, no spend).
**Date:** 2026-11-03. **Bound:** 60 tool calls; used well inside it.
**Objective:** write the prospective, preregisterable evaluation design for the bounded recoverable
context view (BRCV): preserve handoff E1 then E2 with their original falsifiers, controls and budgets;
define five paired arms; a worked unavailable-fact hypothetical; budget arithmetic that shows the
comparative is unfunded; Stage-0 kill conditions; void list; relation to `BOUNDARY-PREREG` and gen-7.

**Declared write paths (only these):**
- `research/next-candidates/consonance-bounded-context-evaluation.md`
- `orchestration/units/CONSONANCE-BC-EVAL.md`
- `orchestration/handoffs/CONSONANCE-BC-EVAL.json`

**Read (absolute paths under `/home/zer0null/research extractor`):**
`handoff from consonance/EXPERIMENTS.md` (all six budgets + E1/E2 method, controls, falsifiers),
`handoff from consonance/INTERFACE_CONTRACT.md` (§1 fingerprints, §2 null rule, §3 run.json, §4 fixture,
§5.3 controls), `handoff from consonance/MEASURED_FACTS.md` (F1/F2 rows), `handoff from consonance/README.md`
order via plan, `experiments/ptr-engine/longrun/QUALITY-POSITIVE-CONTROL.md`,
`docs/CHECKPOINT-COVERAGE.md`, `experiments/ptr-engine/BOUNDARY-PREREG.md` (head + ladder),
`docs/STATE.md` (defects 1–4, ledger, lines 40–60), `orchestration/STATUS.md` §7.1 (`E1` fork-break-cost,
`E2` cache-forensics, `E4`, `E4R`, `LIVE-MEAS`), `papers/context-cache/CLAIMS.md` (C62, C64),
`papers/context-cache/MANUSCRIPT.md` §8a, `experiments/ptr-engine/longrun/run_longrun.py`
(`ARMS`, `projected_requests`, `expected_digests`), `experiments/ptr-engine/longrun/score_longrun.py`
(check kinds; abstention grep), `experiments/ptr-engine/longrun/tasks-v6/LR-01.v7.json` and
`LR-01.v8.json` (N, wall, wall_tokens_by_arm, growth basis), `longrun/fixtures/LR-01..06.json`.

**Verification run (offline):** one python pass over `EXPERIMENTS.md`, the six fixtures and the request
arithmetic. Output recorded in the handoff `evidence` block.

**Findings that shaped the protocol (all from reads, no new run):**
1. `score_longrun.py` has **no** abstention vocabulary (`abstain|retrieval_miss|STALE|REVOKED|NOT_FOUND`
   → 0 matches) and four check kinds; §7's success/abstention distinction needs a scorer extension as a
   Stage-0 prerequisite.
2. `tasks-v6/LR-01.v8.json` prices its wall from **declared** answer padding (`wall_tokens_by_arm 10616`
   for all four arms) while its own basis lists measured growth of 38.532–684.362 tok/turn; `docs/STATE.md`
   records turns-to-wall 73–113 > 48, i.e. treatments never fired. Gen-7 needs a v9 wall from measured growth.
3. The handoff's CON-E2 cap (≤120) cannot also deliver a verdict: 3 arms × 40 turns = 120 turn requests
   before 3 checkpoint requests (123), and 3 reps = 369 (450 with a 12-checkpoint fixture). Recorded as an
   explicit owner decision, not resolved silently.
4. The comparative is unfunded: 420 turns/arm/rep × 4 one-request arms × 3 reps = 5,040 > 1,729 remaining
   (2.92×), 6,300 (3.64×) with D at 2 requests/turn.
5. Padding is measured and loses (C64: P2−P1 +20.8429 [10.014, 31.586], 70 pairs); no padding rule appears
   in the protocol.

**Assumptions (recorded, not resolved):**
- D is priced at 2 requests/turn from `BOUNDARY-PREREG.md`'s `R-pointer` shape; a lower fetch rate only
  strengthens the "unfunded" conclusion, so the conservative shape was used.
- "Checkpoint request" is counted as a separate request from its turn (the runner's `expected_digests`
  treats digests as extra requests); if a design folds the checkpoint into the turn, E2's counts drop by
  3 per rep and the conclusion (120 < 123) still holds at the design's own arms.
- 60-turn horizon on LR-02 (64) and LR-05 (72) means the first 60 turns; LR-01/03/04 are `UNAVAILABLE`.
