# Unit card — PROSE-VACUITY (self-persisted)

Board card: 172427db-59fb-4aba-92e9-ec18ed40ae22 (running at start).
Objective: sweep the four package prose files (MANUSCRIPT.md, CLAIMS.md, EVIDENCE.md, GAPS.md)
for hedged/vacuous claims; classify each against the data; cross-check every defect against
`orchestration/handoffs/*.json` and `experiments/context-cache/cells/*/analysis.json`.
Mode: measure, not fix. No prose file was edited.

Hard bound: 15 tool calls. Actual: 12 (list, working_directory, bash-verify, 4 reads, 2 compress,
1 grep+read GAPS, 3 bash cross-check). Stop condition met.

Write paths (declared, no clash with concurrent units): orchestration/handoffs/PROSE-VACUITY.json,
orchestration/units/PROSE-VACUITY.md ONLY.

## Marker sweep result

`grep -n` over the 17 markers across all four files: ~150 raw hits. The dominant classes:
MANUSCRIPT §11 (single-seed/one-cell limitations), §3 (C05/C06 supersession), §5 (C13/C16
"untested at n>0"), §9a (C55/C61 grid guard), §12 (CX-V2 provenance); CLAIMS.md (C04/C05/C06/C44/C62
supersession + range-with-exception hedges); EVIDENCE.md §2.2/§2.6.1/§2.6.2 (per-unit derivations);
GAPS.md G1–G12 (gap titles + closures).

## Defect table (only non-SUPPORTED hits)

| file:line | quote (≤15 words) | class | evidence for the class |
|---|---|---|---|
| EVIDENCE.md:251 | "not yet (see §5)" (U15 "Verified independently by" column) | STALE | orchestration/VERDICTS.md:12 records `2026-10-21 05:22 CX-V3 PASS` with `recompute.py all 41/41` and reproduced red→green; CX-V3's ten checks include U15's 1.700x. GAPS.md:327 already flags this line as stale ("the attribution in EVIDENCE.md §5 is now stale in the same way") and was not repaired here. |
| EVIDENCE.md:263-266 | "The independent verification of U15 has not happened yet" | STALE | Same VERDICTS.md:12 entry. U15 was verified by CX-V3 (a different agent from U7). |
| EVIDENCE.md:293-295 | "No independent verification of U15 yet. CX-V3 is the gate; until it rules, the 1.700x figure is author-analysed…" | STALE | CX-V3 has ruled (PASS, red→green 1/1 reproduced). |
| EVIDENCE.md:298-299 | "…CX-V3 remains the gate for those." | STALE | CX-V3 passed; the gate is closed for the total-uncached/accuracy half too. |
| GAPS.md:325 | "CX-V3 is still pending." | STALE | Contradicted 2 lines later by GAPS.md:327 ("CX-V3 is **not** pending"). The stale sentence was left in place below its own correction. |
| GAPS.md:335-336 | "`orchestration/VERDICTS.md` carries a pending CX-V3 entry for exactly that" | STALE | VERDICTS.md:12 is a PASS entry, not pending. |
| GAPS.md:341 | "What would close it: CX-V3's independent pass, a graded correctness measure…" | VACUOUS | CX-V3's pass is already listed as a closure condition after being satisfied; the remaining two (graded correctness, real summariser) are genuine open work. Half-vacuous: the first of the three named closers is done. |

## Counts

- Raw marker hits: ~150 across four files.
- SUPPORTED: ~143 (the overwhelming majority carry a claim id C## or a named cell/row set, and the
  hedge is warranted by the data — C05/C06 supersession, C11 p=1.0, C12 salt rounding, C44
  "within measurement noise" with u15_1_700x_survives_decomposition=False, C53 band, C62
  range-with-exception, §11 single-seed, §9a "regularity observed, not a contract verified").
- VACUOUS: 1 (GAPS.md:341, first closure condition already satisfied).
- STALE: 6 (all CX-V3-pending claims in EVIDENCE.md ×4 + GAPS.md ×2).
- FALSE-ORPHAN: 0. Every asserted result maps to a cell with rows (U2 88, U4 438, U4b 24, U5 760,
  U9 139, U10 120, U15 160, G1 264, G5 192, G3-LIMIT-V2 2780). U13/U14 are offline marker cells
  (u13_fork_marker.json, u14_append_note.json) with no .jsonl by design — not orphans.
  CX-V2 is a verifier unit with scripts, also by design.

## Three most serious findings

1. EVIDENCE.md:293-295 — the headline limitation ("No independent verification of U15 yet") is
   false: CX-V3 passed on 2026-10-21 and the paper still tells the reader its 1.700x figure is
   author-only.
2. GAPS.md:325 — a stale sentence survives directly above its own dated correction (GAPS.md:327);
   a reader stopping at the gap title/first paragraph gets the opposite of the truth.
3. EVIDENCE.md:251 — the provenance table's "Verified independently by" cell for U15 still reads
   "not yet", contradicting VERDICTS.md:12 and the document's own §5.

## Notes / assumptions

- The grep sweep was one pass per file; MANUSCRIPT.md and CLAIMS.md were also read in full, so
  coverage is complete, not sampled. "~150 raw hits" is an estimate because marker tokens overlap
  (e.g. "~" appears inside other markers).
- No cell `analysis.json` contradicts any SUPPORTED claim; no false-orphan candidate surfaced, so
  none was promoted.
