# UTRIMM1 — smallest publishable file set (data + verification tools only; harness withheld)

**Status: done.** Bound: 25 tool calls (used ~19). Source: `scratch/uoutside1/tree-seven` (45 files,
MANIFEST.json sha256 `fecd31574bad62cef328d7d95b851ac338aad552c420d1b08a1126cb48cd97ef`, recomputed on the copy).
All work on copies under `scratch/utrimm1/`; nothing deleted anywhere.

## Purpose
Compute **and experimentally prove** the smallest file set on which the published numbers still verify once the
harness is withheld. No argument-only closure.

## Result
* Minimal machine-closure: **13 files, 588,891 bytes** (`scratch/utrimm1/cut-min`) — recompute-claims.py,
  parse_fixture.py, compare.py, `fixture/reflex-decisions.ts`, `harness/data/fixture-190.json`,
  `results/baselines.json`, the five `results/eval-*.json`, `second-labeller/labelsB.json`,
  `second-labeller/metrics.json`. All three steps EXIT=0 with numbers identical to the full tree.
* 14-file variant (+ `fixture/DECISION_CASE_SCHEMA.ts`, 961 B) if §7's "fixture and its schema" must stay true.
* Harness code (12 files) is removable at zero cost — cut (ii) is fully green. The **first break is cut (iii)**,
  removing `harness/data/*`: `FileNotFoundError: .../harness/data/fixture-190.json` from
  `verify/recompute-claims.py`, EXIT=1. One data file inside `harness/` is load-bearing.
* Standard-library-only claim confirmed by import grep and by strace of all tree files the path opens.
* Census 45→13 files: inside-stimulus 2,171→884, outside 1,094→325, total 3,343→1,224.

## Deliverable
`strategy/PUBLIC_SCOPE_REDUCTION.md` — classification of all 45 files into DATA (21) / VERIFICATION TOOL (3) /
HARNESS (12 code+prose; harness/data/* classed DATA) / PROCESS-OTHER (9), cut-by-cut evidence with literal
exit codes and errors, the minimal file list with per-file reasons, the droppable list with reasons, census and
per-token counts, and the paper sentences that become untrue (reported, paper not edited).

## Not done (named remainder)
Did not edit `repro/encoder-crossover-190/` (43 files, still contains `harness/analyze.py` and
`harness/data/lint-report.json`) nor the paper; a follow-up unit must regenerate the subset and reword
MANUSCRIPT.md §7 / Data-and-code-availability (:738–741, :747, :749, :754, :795–796, :809–817, :819–823, :832–833).
