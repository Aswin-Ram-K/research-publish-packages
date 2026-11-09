# Unit `WITHDRAWN-SCREEN` — screen the publication surface, correct the flagged pages

**Card:** `22052dfc-86d1-405f-9139-c6e137f62e75` · execution `1e5e7e68` · 2026-10-26 · OFFLINE, 0 requests.

## Purpose
`WITHDRAWN-INDEX` (`4cddec07`) built the 15-entry withdrawal register
(`experiments/ptr-engine/measure/WITHDRAWN.json`) and its guard
(`experiments/ptr-engine/tools/withdrawn_index.py --check <file>`, exit 1 on an uncorrected withdrawn
quote). It proved the guard bites and deliberately did not correct the pages it fired on. This unit
closes that loop: screen every published markdown file, correct the two documents the register
flagged, and prove the guard goes green on them and still red on a re-pasted figure.

## Bound
≤26 tool calls, ≤20 min, 0 network requests. Additive only. No deletion, no reflow, no edit of the
register (`WITHDRAWN.json`), `docs/WITHDRAWN.md`, or any measurement/rows/grade file.

## Write paths (declared)
- `docs/LATENCY-REPORT.md`, `experiments/ptr-engine/measure/ARM-RECONCILE.md` (the two flagged)
- `docs/WITHDRAWN-SCREEN.md`
- `experiments/ptr-engine/measure/WITHDRAWN-SCREEN.json`
- `experiments/ptr-engine/tools/withdrawn_screen.py`
- `experiments/ptr-engine/longrun/tests/test_withdrawn_screen.py`
- `orchestration/units/WITHDRAWN-SCREEN.md`, `orchestration/handoffs/WITHDRAWN-SCREEN.json`,
  `orchestration/journals/WITHDRAWN-SCREEN.jsonl`, `/tmp/ws/**`

## Result
- **130** markdown files scanned (102→103 `docs/**`, 25 `measure/*.md`, 2 root).
- **7** files with hits: **2** quote a withdrawn figure (the two corrected), **4** are `98.7`
  substring artifacts of the citable p50 `198.72`/`198.7`, **1** real reported-only offender
  (`docs/REQUEST-LEDGER.md:145`, `WI-002`).
- Corrections: `docs/LATENCY-REPORT.md:45` (`WI-004`, p95 318.14 "stands" → withdrawn) and
  `experiments/ptr-engine/measure/ARM-RECONCILE.md:9` + `:104` (`WI-009` 1,867 → 967; `WI-011`
  cached share 0.871157). No sentence deleted; dated `Correction (2026-10-26)` blocks appended.
- `no_correction_needed` recorded for the four substring-artifact documents rather than inventing
  corrections (same rule, different number).
- Loudest finding: the *register* is over-broad — `WI-011`'s quote is the bare 3-character string
  `98.7`, so the guard fires on any page printing a p50 in the 198.7 ms range. Reported for the
  register owner; not edited here.
- Closure: `withdrawn_index.py --check` exits **0** on both corrected documents; exits **1**
  (`WITHDRAWN WI-004 line 120`) on `/tmp/ws/paste-back.md`, a copy of ARM-RECONCILE with the figure
  pasted back. `withdrawn_screen.py --check` exits 0 over 130 files; 8 tests pass.
