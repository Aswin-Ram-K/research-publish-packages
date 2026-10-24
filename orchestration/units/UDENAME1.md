# UDENAME1 — de-naming rule drift in tools/package/md2tex.py

**Status:** in_progress (skeleton written first, per card)

## Purpose
`tools/package/md2tex.py` de-naming rule rewrites `the fixture `evals/fixtures/reflex-decisions.ts``
into `the withheld stimulus fixture`, which is now FALSE: Paper #2's availability section (changed
2026-10-19) says the stimulus fixture is released with the companion note. Shipped
`papers/replay-record-not-decision/submission/main.tex` (~line 187) therefore contradicts itself.

Second load-bearing aspect: `md2tex.py:677-680` raises SystemExit when a rule's source phrase is absent,
so editing the manuscript source phrase without the rule hard-fails the build.

## Declared write paths
`tools/package/md2tex.py`, `papers/replay-record-not-decision/MANUSCRIPT.md`,
`papers/replay-record-not-decision/submission/**`, `scratch/udenames1/**`,
`orchestration/units/UDENAME1.md`, `orchestration/handoffs/UDENAME1.json`

## Bound
15 tool calls. 3 attempts per claim, else STOP and report unverified.

## Log
- (pending)
