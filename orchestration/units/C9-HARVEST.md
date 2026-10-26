# C9-HARVEST — adjudicate the 378 abandoned avalanche rows

**Card / bound.** 18 tool calls, offline only (no live request, no container, no `.occamy.lock`), automated
(no questions). **Status: done.** **Write paths:** `experiments/miss-law/avalanche/HARVEST.md`,
the C9 paragraph of `experiments/ptr-engine/RECORD.md`, `orchestration/units/C9-HARVEST.md`,
`orchestration/handoffs/C9-HARVEST.json`.

## Objective
C9 says the 378 `AVALANCHE-INSERT` / `AVALANCHE-2` rows were abandoned and never harvested, so nobody has
established whether they are usable measurements or garbage. Decide on evidence and act (harvest / partial /
abandon).

## Inventory (evidence, offline)
- `experiments/miss-law/avalanche/rows.jsonl` — **378 rows**, 26 keys, sha256 `8147d195…b8ba2`; arms WINDOW
  126, CEIL 108, RECOVER 63, MINIMAL 36, PP 30, RECOVER-CTRL 15. Written by `probe.py` (`all 3`), which also
  wrote `log.txt` (378 lines, **1:1**, 0 `LENGTH-MISMATCH`) and `run.out` (`done stage=all reps=3`).
  0 exact duplicates, 123/123 pairs complete (no partial rows), 0 rows with `error`.
- `experiments/miss-law/avalanche/_filler.json` (prompt filler) and `probe.py` — support files, not rows.
- `experiments/miss-law/vllm2/rows.jsonl` — **133 rows**, 38 keys, written by MISS-LAW-2 `probe2.py`/`probe3.py`
  and already consumed by `experiments/miss-law/vllm2/REPORT.md`; **not** part of the 378 and not re-harvested here.

## Integrity
Present on every row: `residue` (=`P1 % 1056`), `P1`, `P1_measured`, `cached`, `uncached`, `ttft_ms`,
`ttft_server_ms`, `kvcomp_count_delta`, `arm`, `pair_id`, `role`, `rep`, `ts`. Arithmetic closes:
`uncached − (P1 − cached) == L` in **378/378** rows; `cached ≤ P1` in all rows; `kvcomp_count_delta == 1` in all.
Missing per row: **model/engine profile**, **server endpoint**, **B=1056** (profile is file-scope only:
`probe.py:1,17,24-25` vLLM :8014 / `qwen3.5-9b` / label `engine="0",model_name="qwen3.5-9b"`; `LAW.md:28`).

## Honesty check
Both units failed to **report**, not to **measure**. `AVALANCHE-INSERT` handoff (00:31): `"measurement in
progress"`, `status:"partial"` — while its own run continued to 00:37 and finished (`done stage=all reps=3`).
`AVALANCHE-2`: `"not yet measured"`, Q1–Q5 all `"unknown"`, `artifacts: []`, `blocker: "in progress"`, and its
declared `avalanche2/` was never created. Neither handoff contradicts a row. Reproducibility: **90/90**
cache-probe cells give the same `cached` in all 3 reps.

## Ruling — (a) HARVEST
`experiments/miss-law/avalanche/HARVEST.md` (38 lines): of 270 cache-probe rows **141** show the avalanche
(`cached>0`) and **129** do not (`cached==0`); at `r=0` every arm returns `cached=0`; residue and P1 are
**confounded** (`WINDOW P1=6336+r` → 5280 in 3/3 reps, `P1=1056+r` → 0), so the table is measured cells, not a
residue law. RECORD.md C9 now reads **HARVESTED (one profile)** with that source.
