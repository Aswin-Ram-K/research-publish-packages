# V-FOLD-2 — independent re-check of the repaired FOLD-PROPOSAL

Unit: verifier of `papers/context-cache/FOLD-PROPOSAL.md` after FOLD-FIX / FOLD-FIX-2.
Trigger: V-FOLD verdict `fail`; the repairs were never independently re-checked.
Mode: automated, offline, read-only on all audited artefacts. Bound 18 tool calls (used 15).
Write paths: this card + `orchestration/handoffs/V-FOLD-2.json`.

## Overall: partial

The three original defect classes are 2 closed and 1 half-closed, but the repaired text
still cannot be printed as-is: bucket (i) declares 9 items and contains 8, and the
identifier history it states is off by one. Both are one-line edits, not re-analysis.

## Per-item

1. Suite count — PASS on substance: `187` count 0; text says 190; re-ran
   `cd experiments/ptr-engine && python3 -m pytest -q` -> `190 passed in 0.22s`, exit 0.
   The printed `0.27 s` is not reproducible (V-FOLD: 0.24 s) — stale timing, drop it.
2. Claim ids — FAIL on justification, PASS on safety. In use: C75-C79, zero hits in all
   four `papers/*/CLAIMS.md`. But gated-read-batching:121-124 holds C70-C73 (four, not
   "five"), and C74 has 0 occurrences under `papers/`, so C75 is not the next free id.
3. `checks[...]` — PASS, 8/8 MATCH, off-by-one fixed. V-ENGINE-P0 [3] 3 determinism,
   [4] 4 r recomputed, [6] 6 seven negative controls, [7] 7 warmpool isolation;
   V-QUALITY-ARM [1] 2 discrimination, [2] 3 index, [4] 5 billed tokens. Each cited
   element's text begins with its cited label.
4. `rebuild_corpus.py` — PASS. File exists, unmodified; `.venv/bin/python` run exit 0:
   BODIES 12 / BODY_BYTES 30000 / INDEX_BYTES 447 / INDEX_LINES 12 / 37.25 / 472 /
   sha e08700c9…9bd2 (plus RATIO 67.1141). All seven match line 74.
5. 8.5x TTFT — PASS. G6 residue 0: P1 7392, pt 7392, cached 0, ttft 1.789975; residue 2:
   P1 7394, pt 7394, cached 6336, ttft 0.210802; 1.789975/0.210802 = 8.4913 -> 8.5.
   7.4 / nine-arm / 1.585 / 0.216 all grep 0. Two overstatements: the residue-2 row is
   P1 7394 (not 7392), and "no residue-1 warm row" is false — six measure rows at
   residue 1 (G1 7393, G7 6337, G7 8449, x2 reps) all carry cached 0.
6. Bucket counts — FAIL on (i): claims 9, holds 8 (lines 15-22). (ii) 8/8, (iii) 12/12.
   Cause: items 7-8 were made claimless without decrementing the header.
7. Corrections log — 4 VERIFIED, 2 OVERSTATED, 0 MISSING: (a) verified (except 0.27 s),
   (b) overstated (C74 free), (c) verified 8/8, (d) verified (two-root leg inherited),
   (e) verified as text but breaks the count, (f) verified on the number, overstated on
   the residue parenthetical and the residue-1 absence.

## Not reproduced
`0.27 s`; bucket (i) = 9; "five identifiers" at :121-124; "no residue-1 warm row".
`33 PTR_STORE_MISS (11/rep)` was checked and does reproduce: 33 occurrences under
`resolutions[].code`, 11 per rep over 3 arm-B reps — V-FOLD's "3 occurrences" counted a
different field, so that number is not a defect.

## Blocker
None. Nothing repaired (by contract); the four fixes are named in the handoff's
`next_unit_hint` for a fresh repair unit.
