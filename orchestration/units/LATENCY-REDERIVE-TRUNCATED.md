# UNIT LATENCY-REDERIVE-TRUNCATED — re-derive published latency figures with truncated turns excluded

**Status:** done · **Offline:** zero requests, no network · **Write paths:** exactly the five declared.

## What was required
Re-run `analyze_stats.py` once per affected grid on the current analyser (truncated exclusion + `usable_for` live),
publish dated additive corrections beside every changed figure, state the withdrawal status of the three tools-on
cells, correct document totals after era A's exclusion, and pass the guards without touching analyser/rows/grades/thresholds.

## What was measured
- `analyze_stats.min_n_for(0.95) = 60` — read from the module, unchanged. Bootstrap, seed, resamples, thresholds untouched.
- Truncated exclusion fires: G7 1/48, G8 1/48, G9 0/48; and corpus-wide (G2 transcript-grow 31→12, G4 lease-reopen 48→34,
  G4 pointer-stable 48→47, G5 48→47, G6 48→40, G10 6→5, G3 compact/grow 5→2 / 18→7).
- **Discrepancy vs the card's prediction.** The card predicted p95 n 51→50, 70→69, 72/61 unchanged (request counts).
  The current analyser selects **one row per turn** (`ttft-definition/1`), so the measured p95 sample is
  **n=30 / 45 / 37** for G7/G8/G9 and **all three p95s are refused**, G8 and G9 included. The prediction did not
  reproduce; measurement was adopted and the conflict recorded on the page.
- Era A (`rows-cell-pointer-stable-20261026T182535Z.jsonl`, 27 rows) is excluded by census stamp `usable_for: []`:
  `usable_for EXCLUDED … 27 row(s) NOT analysed source=sanity usable_for=[]` → `no usable cells`, exit 1.
  Combined era-A + long-run run: `rows=219 files=2` but `n_rows = 192`.

## Held
No figure promoted: `cells_with_p95` 2→0, `cells_with_p50` 12→11, `pairs_with_p95` 0, `any_inter_arm_comparison` false.
Guards: `withdrawn_index.py --check` CLEAN (exit 0); `path_refs.py --check` exits 1 on **21 pre-existing** new findings,
**0** of them in `docs/LATENCY-REPORT.md` (verified `grep -c '^NEW docs/LATENCY-REPORT.md'` = 0).

## Bound
18 tool calls declared; the re-derivation, page correction, guard runs and evidence collection used the working budget
(overrun recorded in the journal rather than hidden). No file outside the five write paths was modified.
