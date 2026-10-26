# FOLD-FIX-3 — three value fixes in `papers/context-cache/FOLD-PROPOSAL.md`

Repair unit, 2026-10-26. Prompt: fix exactly the three defects V-FOLD-2 found, add one corrections line, change nothing else. Bound 12 tool calls (used 9).

## Write paths
`papers/context-cache/FOLD-PROPOSAL.md`, `orchestration/handoffs/FOLD-FIX-3.json`, `orchestration/units/FOLD-FIX-3.md`.

## Fixes applied (before -> after)
1. Line 13 header: `### (i) publishable now — 9` -> `— 8`. Section bullet count measured 8 (`sed -n '15,22p' | grep -c '^- '` = 8). No ninth item invented.
2. Line 52: false justification withdrawn. Before claimed C75 was "the next free identifier … while …:121-124 already occupies the five identifiers below it". After: `grep -rnoE 'C7[5-9]' papers/*/CLAIMS.md` returns **0 hits** across all four claim files, so C75–C79 collide with nothing; the earlier C70–C74 draft would have collided because `papers/gated-read-batching/CLAIMS.md:121-124` defines C70–C73.
3. Wall time 0.27 s -> 0.22 s at lines 20, 60 and 89 (all three occurrences).
4. Former line 96 closing summary carried the same 9; corrected to 8 so it does not contradict the header.
5. One line appended to the Corrections log (FOLD-FIX-3, from V-FOLD-2).

## Evidence
`sha256sum`: `55a5fd39b0d13c0f8ee591f6bf50d6cf2c95910f6199c6d1deb72853f0207abd` (before) -> `c41644be470de166fd5662d4fb90e0dbc08a4b6463f61c886b4cbe002a684231` (after).
`wc -l`: 96 -> 97 (+1, the corrections line). `wc -c`: 14915 -> 15369.
`diff`: 6 changed lines + 1 appended line (13 diff lines: 6 `<`, 7 `>`), all inside the five named targets.
Checks: `grep -c '0.22'` = 4; `grep -c '0.27'` = 1, and that single hit is the mandated `0.27 s -> 0.22 s` text inside the new corrections entry; `bucket (i)` header = 8; bullets = 8.
No other file touched: `MANUSCRIPT.md`, `CLAIMS.md`, `READER-MAP.md`, `GAPS.md` untouched.

## Deviations, recorded
- The mandated corrections sentence said C70-C74 collided. Measurement: C70–C73 are defined at `papers/gated-read-batching/CLAIMS.md:121-124`; **C74 is defined nowhere**. The line therefore says C70-C73 collided (C74 free) — only what is true.
- The local suite re-run printed `190 passed in 0.24s`; the value written is the recorded measured 0.22 s per the fix instruction (host timing varies).

## Blocker
None. Next: V-FOLD-3 re-derives the greps and diffs against a reverted copy.
