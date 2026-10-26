# GRADE-RESCORE-V2 — second pre-registered grader beside the original

- **Purpose:** re-grade the existing 192 config-C rows under a deterministic, pre-registered
  rule, without touching `score_longrun.py`; separate the real behaviour failure (D1) from the
  grader false negative (D2).
- **Bound:** max 22 tool calls; zero inference requests; no `curl`.
- **Write paths:** `longrun/GRADE-V2.md`, `longrun/grade_v2.py`,
  `measure/rows-longrun-c-2026-10-26.grade-v2.json`, `/tmp/**`, this card, the handoff.
- **Kill condition:** any checkpoint not decidable from the fixture under R1–R3 is recorded
  `unverifiable` with `n` reduced, never passed.
- **Method:** rule text written first (`GRADE-V2.md`), then the module imports the untouched
  scorer read-only to print original verdicts beside v2 verdicts; red/green synthetic check in
  `/tmp` (10 correct all pass, 10 wrong all fail) plus a must-still-fail check on the real
  turn-12/24 rows.
- **Deliverable:** `orchestration/handoffs/GRADE-RESCORE-V2.json`.
- **Result:** see handoff — D2 repaired (0/10 → 2/10 for `pointer-stable`, `transcript-grow`),
  D1 confirmed (no arm answers turn 12/24; no arm runs the acceptance suite at turn 48).
