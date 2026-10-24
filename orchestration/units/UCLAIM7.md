# Unit UCLAIM7 — Are the 143 cut3 expectations anchored to published claims?

## Purpose
Close one gap: determine whether `scratch/urelease7/cut3/verify_claims.py` (16,808 B; prints
`RESULT pass exit=0 claims=143 failed=0 []`) checks expectations ANCHORED to published claims,
DERIVED from shipped rows, or ORPHAN constants checked against themselves.

## Hard bound
20 tool calls. Report stub first, append as measured.

## Declared write paths
- strategy/CLAIM_CROSSCHECK_7.md
- orchestration/units/UCLAIM7.md
- orchestration/handoffs/UCLAIM7.json
- scratch/uclaim7/**

## Read-only
/home/zer0null/Duval — no git commands at all. papers/** and strategy/GATED_READ_RELEASE_CUT.md not edited.

## Findings (appended as measured)
(pending)

## Measured result (final)

Verified count from own run: 143 PASS (`RESULT pass exit=0 claims=143 failed=0 []`).
- ANCHORED 136/143 — expected value printed in MANUSCRIPT.md / CLAIMS.md / GAPS.md (R1/R2/R3)
  or strategy/GATED_READ_RELEASE_CUT.md §1 (R3–R6 arms the manuscript scopes out at MANUSCRIPT.md:195).
- DERIVED 4/143 — R1-F1-BATCH-DELTA16 (0.0092), R1-F1-BATCH-DELTA90 (-0.0071), R5-HITS-MULTISET (0),
  R4-ROUTER-GREP-ROWS (1.000); arithmetic on published values, not themselves printed.
- ORPHAN 3/143 — R4-CHEAPEST-OK-REC (0.575), R4-ROUTER-207-REC (207), R4-ROUTER-GREP-207-REC (207):
  each compares a constant in verify_claims.py to the SAME literal shipped in cut3/sealed.json.
  Recomputable count: 140/143. 2 distinct published figures fail to reproduce (2 figures, 3 expectations).
- ~55 of the 140 re-derive by arithmetic over lower-level shipped cells; ~85 compare a published
  constant to a value stored precomputed in record.json. Two different files -> genuine cross-check,
  not constant-vs-itself.
- Scope caveat: the paper disowns R3/R4/R5 (MANUSCRIPT.md:195), so ~60 of the 143 verify a strategy-doc
  claim register, not the manuscript.

## Other findings (recorded, not fixed)
- R1-F1-[MODE-4] expects stale 0.210; CLAIMS.md:58 / MANUSCRIPT.md:135,158 print corrected 0.211.
- R1-ACC-* 4-dp constants (0.9161/0.8961/0.8333/0.8833/0.9272) have no 4-dp published source; MANUSCRIPT:156-159 is 3 dp.
- record.json ships `gold_derivation` (127 pinned / 130 live) listed as covered at release doc :50, but
  verify_claims.py never reads it (grep -c -> 0).
- R5 two-payload ASR published for 6 arms (release doc :42); only [ARM-6] is checked.
- Q-EXPO-ATTRIBUTION: file-exposure flags give 19 vs context-carry 0 for [ARM-5]; unresolved by the release.
- "per-arm files" label vs verifier field `units_mean` — unresolved.

## Artifacts
strategy/CLAIM_CROSSCHECK_7.md (full inventory + classification + UNVERIFIED)
scratch/uclaim7/expectations.txt (full 149-line verifier output)
