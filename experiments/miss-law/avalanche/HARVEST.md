# HARVEST — avalanche rows (C9)

**Ruling (a): HARVEST.** 378 rows are measurements from one completed run; the units failed to report,
not to measure (`AVALANCHE-INSERT`: `"measurement in progress"`; `AVALANCHE-2`: Q1–Q5 all `"unknown"`).

**Source:** `experiments/miss-law/avalanche/rows.jsonl` — 378 rows, sha256
`8147d195e2de495e1b8cbf59231e00f58c5cd8cec0b587923f5723c6ba7b8ba2`, written by `probe.py` (`all 3`);
`run.out` `done stage=all reps=3`; 1:1 with `log.txt` (378 lines, 0 `LENGTH-MISMATCH`); ts
00:29:51–00:37:24 -0500; 0 rows with `error`; 0 exact duplicates; 123 complete per-rep pairs, none partial.

**Profile (file scope — no row carries it):** vLLM :8014, `qwen3.5-9b`, block size 1056, metric label
`engine="0",model_name="qwen3.5-9b"` (`probe.py:1,17,24-25`; `LAW.md:28`).

**Method (rows only):** drop `prime` (108 rows, all `cached=0`); avalanche = `cached>0`, none = `cached==0`;
`residue = P1 % 1056` is a stored field; the 3 reps are pooled.

| arm | residue | probes | avalanche | none |
|---|---|---|---|---|
| CEIL | 0 | 36 | 12 | 24 |
| CEIL | 2 | 36 | 30 | 6 |
| MINIMAL | 0 | 6 | 0 | 6 |
| MINIMAL | 1, 2 | 6 each | 3 | 3 |
| PP | 776–780 | 6 each | 3 | 3 |
| RECOVER | 0 | 54 | 30 | 24 |
| RECOVER-CTRL | 2 | 12 | 12 | 0 |
| WINDOW | 0 | 12 | 3 | 9 |
| WINDOW | 1 | 12 | 3 | 9 |
| WINDOW | 2–4 | 12 each | 6 | 6 |
| WINDOW | 1054, 1055 | 12 each | 6 | 6 |
| **total** | | **270** | **141** | **129** |

**Reading.** `r=0` → identical resend `cached=0` in every arm; `r∈{1..4}` → the cell `P1=6336+r` gives
`cached=5280` in 3/3 reps but the cell `P1=1056+r` gives 0: residue and P1 are not separable here.

**Limits.** (1) No per-row profile/engine field: single-profile harvest, no cross-profile use. (2) `cached`
is attributable only as sole-writer, strictly serialized deltas (`probe.py:3`; `LAW.md:36-42`), and
`prompt_tokens_details` is null on this build, so no token-level second instrument. (3) One run, 3 reps,
7.5 min, no flush/restart; residues sampled = {0,1,2,3,4,776–780,1054,1055}. (4) vLLM B=1056 ≠ SGLang B=64 law.
