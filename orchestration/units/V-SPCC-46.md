# Verification — U-SPCC-4 / U-SPCC-6 (launch script, fork decision, remote root, prereg)

## Launch script

1. Contains required flags: `--enable-hierarchical-cache`, `--page-size 1`, `--kv-cache-dtype fp8_e4m3`, `--enable-cache-report`, `--mamba-radix-cache-strategy extra_buffer`, `--mem-fraction-static 0.45` (MEM_FRAC). Port is `--port 30000` (container-internal; host-mapped to 8012 per FORK-DECISION.md), not `8012` in the script.
2. Captured invocation is real: `model_path` and `served-model-name occamy-1.0` match live `get_server_info` (`model_path .../models--Accio-Lab--occamy-1.0-NVFP4/snapshots/fa865dc...`) and `/v1/models` (`id: occamy-1.0`). Not aspirational.
3. Memory arithmetic: 0.45 × 121 GB = 54.45 GB ≤ 60 GB; safe. Script comment instead uses 0.45 × ~128 = ~57.6 GB (inconsistent pool size) but conclusion holds. Threshold f < 60/121 = 0.496; 0.45 is safe with margin.
4. `bash -n` → exit 0. `--dry-run` → prints full command, exit 0.
5. With `MEM-WINDOW.json` beside script: refuses, exit 1, message "refusing to start: MEM-WINDOW.json present ...". File deleted; `ls` confirms gone.

## Fork decision

6. All three criteria (a) per-range eviction protection, (b) non-prefix reuse, (c) per-range attribution present. Verdict lines: "Current verdict: **no fork.** No failing run has yet been produced for any of the three fork-gate criteria..." and "Until then this file states 'no fork' and cites the flags that made it unnecessary: ..."

## REMOTE-ROOT.md

7. States remote writes BLOCKED by default, names authorisation requirement (verbatim paste), treats `/home/zer0null/gx10-serving-programme/` as proposal only. Authorisation section: "(none recorded)". Does not authorise anything.

## Pre-registration

8. Six experiments E1–E6 each with hypothesis, design, controls, predicted outcome, falsifier, budget ceiling; fixed order E1→…→E6; E6 gated on E1. Blocked inputs section names Nemotron weights (authorisation) and E5 (relaunched server).
9. Ledger re-derive: spent 7869, remaining 4225, cap 12094; 7869+4225=12094 consistent. rows-*.jsonl line count = 7869. PROJECT_QUOTA = 12094 at cell.py:141.
10. Blocked inputs section names real blockers (Nemotron authorisation; E5 relaunched server).

## Defects found

- Launch script comment's pool size (~128 GB) inconsistent with plan's 121 GB pool; arithmetic stated as ~57.6 GB vs actual 54.45 GB. Cosmetic but should be corrected.
- Script port 30000 (not 8012); host mapping documented elsewhere. If operator expects script to bind 8012 directly, mismatch. Minor.
- No other defects. Files verified present and consistent.