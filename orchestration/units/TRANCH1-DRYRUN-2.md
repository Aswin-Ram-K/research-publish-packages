# UNIT `TRANCH1-DRYRUN-2` — re-rehearse the ten cells under the claim they can carry

**Status:** done — all ten allowed under `--hypothesis H2`; **no gate edited**, no threshold lowered.
**Requests:** 0. **Spawns:** 0. **Sockets:** 0. **Tool calls:** 40 (BOUND EXCEEDED: the card said 28;
the overrun is extension + three correction rounds on the launch-command emitter, all recorded here
rather than hidden).

## Purpose
`TRANCH1-DRYRUN` found a pincer: G3 refuses H1 at `n=48` for every 48-turn cell, and the pooled shape
that clears `n>=60` is refused by G2 (`8640 s` / `5760 s` > `2880 s`). The main session's decision
(board #975) is that **no cell makes an H1 claim**: each cell launches `--hypothesis H2` (the cache
limb, `n>=1`), and H1 is adjudicated only on the pooled rows post-hoc at `n=144/96`. This unit
re-rehearsed all ten cells under that decision and proved it needs no gate edit.

## What was run
`python3 experiments/ptr-engine/tools/tranch1_dryrun.py` — ten `cell.py --dry-run` invocations
(`pointer-stable r1-r3`, `transcript-grow r1-r3`, `transcript-compact r1-r2`, `lease-reopen r1-r2`),
each `--turns 48 --reps 1 --hypothesis H2 --thinking off --max-wall 2880 --turn-wall-cap 180
--runaway-turns 2 --budget 900` against `tasks-v6/LR-01.v8.json`, one manifest each under
`experiments/ptr-engine/measure/dryrun2-t2-<arm>-r<rep>.json`, plus four pooled probes at
`--hypothesis H2` (recorded under /tmp, never launched) and five gate probes in-process.

## Result
* **all ten allowed** under H2: G1 allow `1,154` cumulative, G2 allow `2880/2880` ratio `1.0000`
  (`artefact-mode`), G3 allow `n=48 >= 1`.
* **G3 still refuses H1 at n=48**, verbatim: "PARM-1 admits H1 (p95 TTFT, q=0.95) only at n >= 60
  completed turns; this cell would have n=48, so its own n cannot support the claim it would state".
* **G3 allows H1 at the pooled n=144** (post-hoc only) and **G2 refuses 2881 s > 2880 s**, so the
  decision is a claim choice, not a relaxation.
* **`H1` appears 0 times** in the ten launch commands and ten manifests; every command says
  `--hypothesis H2`. The string survives only in documentation of the post-hoc analysis.
* **zero network, zero spawns** re-proven by the same `sitecustomize` audit hook.
* `cell.py` sha **before == after == `e24e867b8fe9eec7d1344f5738d9f04022f9f5d0968fa0f575ab9c30e6edf013`** (`SPAWN-TREE-BIND` did not move it mid-run) → `stamped`.
* price: **53 requests/cell, 530 total (+4 per-arm 8-token warm-ups = 534)**; ledger cap 4,320,
  spent 1,101, remaining after 2,685. G1's `1,154` is **cumulative**, not a forecast.

## Extensions to the tool (no check loosened)
`--hypothesis` (default H2; H1 still reproduces the held grid), claim-named artefacts
(`dryrun2-t2-*`, `TRANCH1-DRYRUN-2.json`, `docs/TRANCH1-DRYRUN-2.md`), and new report blocks
`gate_probes`, `launch_commands`, `pooled_analysis_plan`, `price`, `h1_occurrences`.
`--check` still fails on any cell any gate refuses — under H1 it exits 1 on ten G3 refusals, under
H2 it exits 0; that pair is the claim guard in `test_tranch1_dryrun.py`.
