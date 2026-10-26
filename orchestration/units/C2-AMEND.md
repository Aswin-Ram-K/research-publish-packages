# C2-AMEND — RECORD.md's C2 "7.4x" layer corrected to 8.5x (2026-10-26)

**Status:** done · **Bound:** 12 tool calls · used 11 · **Append-only** (no existing layer edited).

## Purpose
RECORD.md's C2 layer recorded the vLLM re-bill as "0.216 → 1.59 s = 7.4x" and withdrew 8.5x on that basis.
The driver re-derived it: the two figures are not a matched pair. One correction paragraph was appended.

## Verified
- `1.585238` = `role=prime`, `pair_id G1-P6336-r0`, `P1_target 6336`, `cached_tokens 0` — a COLD first send.
- `0.216020` = warm `role=measure`, cell G1, round 1, `P1 7450`, `cached_tokens 6336`; 1.585238/0.216020 = 7.34,
  arithmetic across two roles and lengths → **7.4x withdrawn**.
- Controlled cell G6, round 1, reps 0/1: `P1 7392` (residue 0) → `cached_tokens [0,0]`, `ttft_server_s`
  `[1.789975, 1.791956]`; `P1 7394` (residue 2) → `[6336,6336]`, `[0.210802, 0.211353]`; 8.491/8.478 →
  **8.5x, warm-vs-warm, measured**.
- Artefact is nine CELLS (`CAL, CAL-T, G1..G7`), 133 rows — not nine arms.
- Deviation from the brief: G6 never swept 7393, but cell G1 carries a real warm residue-1 pair
  (`G1-P7393-r0/r1`, `cached_tokens 0`, `1.788242/1.791721`). Residue 1 is measured outside the controlled
  cell and misses like residue 0; the live gap is a residue-1 warm row *inside* G6.

## Result
Inserted at **line 145**, after the last layer (144), before `## 6.` (now 148). 148 → 150 lines,
38,075 → 40,310 bytes. Additivity: stripping lines 145-146 reproduces sha256 `bc592dec…03aa6`, the
before-state, so every pre-existing byte is untouched; `grep -c` = 1; five sentinels unchanged (5/1/1/1/1).

## Next
A residue-1 warm row inside G6 (`P1 7393`, same round/reps). The withdrawn 7.4x still stands unmarked in
`papers/context-cache/FOLD-PROPOSAL.md:31` and `orchestration/units/C-ADJUDICATE.md:23/:28`.
