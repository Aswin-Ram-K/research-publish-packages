# UNIT `TRANCH1-DRYRUN` — rehearse the 660-request grid offline

**Status:** done (grid HELD by a gate pincer — the finding is the deliverable).
**Requests:** 0. **Spawns:** 0. **Sockets:** 0. **Tool calls:** ≤30.

## Purpose
`RUN-A*` (`ad214412`) prices 10 cells / 480 turns / ≈660 requests and was held only on
`V-SPAWN-ATTACK-2`. Every piece it relies on had been built but never exercised TOGETHER. This
unit drives one `cell.py --dry-run` per (arm, rep) and checks the decisions mechanically.

## What was run
10 invocations, `pointer-stable r1-r3`, `transcript-grow r1-r3`, `transcript-compact r1-r2`,
`lease-reopen r1-r2`, each `--turns 48 --reps 1 --hypothesis H1 --thinking off --max-wall 2880
--turn-wall-cap 180 --runaway-turns 2 --budget 900` against `tasks-v6/LR-01.v8.json`, plus 4
pooled probes (`--reps 3` pair / `--reps 2` context) to price the only shape whose n clears H1.

## Result — the pincer
* G1 **allows** all ten: `1,101 already spent + 48 turns + 5 allowance = 1,154` (cap 4,320,
  headroom 3,219); marginal 53 requests/cell, 530 for the grid, well under the 900 cap.
* G2 **allows** all ten at exactly its ceiling: `48 x 60 s = 2,880 s` vs `--max-wall 2880`,
  ratio 1.0000; the per-turn wall is the mode-aware **60 s** (`artefact-mode`, thinking=off),
  not the 180 s abort cap and not the pooled 218.2 s.
* G3 **refuses** all ten, verbatim: "PARM-1 admits H1 (p95 TTFT, q=0.95) only at n >= 60
  completed turns; this cell would have n=48, so its own n cannot support the claim it would
  state".
* The pooled shape satisfies G3 (n=144 / 96) and is then **refused by G2** at 8,640 s / 5,760 s
  against the same 2,880 s ceiling.

No invocation shape of this grid passes G2 and G3 at the pinned flags. `cell.py` was not edited,
no threshold/cap/horizon/n-floor was lowered, and `--hypothesis H2`/`smoke` was never used.

## Treatments (from `wall_tokens_by_arm` = 10,616, never the 3,838 trap)
grow first FIFO eviction **T21**, compact first wall **T21**, lease first step **T23**, pointer
first prefix change **T2** — all <= 48.

## Deliverables
`measure/TRANCH1-DRYRUN.json`, `measure/dryrun-t1-<arm>-r<rep>.json` (10), `docs/TRANCH1-DRYRUN.md`,
`tools/tranch1_dryrun.py` (+`--check`, exit 1 on refusal/trap/dup/spawn), `experiments/ptr-engine/longrun/tests/test_tranch1_dryrun.py`
(3 passed, red->green on the 3,838 trap).

## Next hint
The launch decision is a card-level one: `--max-wall >= 8640` for pooled 3-rep cells, or launch
per-rep cells that cannot claim H1 (H2 only), or re-scope. Never lower a threshold.
