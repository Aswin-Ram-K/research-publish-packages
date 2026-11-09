# V-LEDGER-BASELINE

**Purpose.** Independently re-derive the ledger baseline the grid's brake spends against, before 1,056
requests are committed to it. Offline: recompute from rows, never read back; zero requests; no live cell.

**Hard bound.** ≤10 analysis calls, ≤48 tool calls total; stop and report if the count could not be
reproduced in 3 attempts. No rebuild, no re-pin, no edit of `REQUEST-LEDGER.json`, either baseline, any
`rows-*` file, `request_ledger.py`, `cell.py`, `run_longrun.py`, `analyze_stats.py`, `run_a_star.py`, the
pin, the params or any threshold.

**Write paths (exactly).** `experiments/ptr-engine/measure/V-LEDGER-BASELINE.json` ·
`docs/V-LEDGER-BASELINE.md` · `orchestration/units/V-LEDGER-BASELINE.md` ·
`orchestration/handoffs/V-LEDGER-BASELINE.json` · `orchestration/journals/V-LEDGER-BASELINE.jsonl`

**What was verified.**
1. Own row count over `request_ledger.py:784`'s own glob, using the ledger's documented costing rule →
   **1,128 requests over 15 files**, identical to `requests` and `requests_raw`; zero per-file differences.
2. The 27: `1,101 + 27 = 1,128`; file `rows-cell-pointer-stable-20261026T182535Z.jsonl` lines 1-27, sha256
   `46afc892…ca3b1`, ts `18:25:56.773Z` → `18:31:25.300Z`.
3. Dedup: `1098 / excess 30 / rule unsound / deducted false`; **the cap gate spends 1,128**.
4. Baseline-2: pinned ledger sha matches, frozen numbers equal the builder now, v1 byte-unchanged.
5. Headroom `4,320 − 1,128 = 3,192`; 16-cell price 1,056 (PAIR-6+CTX-2) → 2,136; wired 10-cell 1,016 → 2,176;
   refusal strings quoted from `run_longrun.py:407-413` and `cell.py:1283-1291`.
6. Zero-spend: newest rows file is the 27-row cell; mtime trails last row ts by 2 ms; nothing newer.

**Verdict.** `baseline_sound`.
