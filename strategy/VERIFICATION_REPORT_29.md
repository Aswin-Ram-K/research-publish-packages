# VERIFICATION REPORT 29 — UPAPER8 (encoder-crossover-190 release-scope edits)
STATUS: COMPLETE. All 5 checks appended. Verdict: PASS (UPAPER8 claims survived; residual scope leaks listed for a follow-on unit).
Bound: 20 tool calls. Read-only against papers/.

## CHECK 1 — all 18 edits landed (diff vs scratch/upaper8/*.orig)
`diff -u scratch/upaper8/<f>.orig papers/encoder-crossover-190/<f>` → MANUSCRIPT.md 4 hunks / 71 changed lines (`@@ -735,23 +735,25 @@`, `-786,14 +788,20`, `-806,21 +814,19`, `-829,16 +835,17`); AVAILABILITY.md 3 hunks / 43 changed lines (`@@ -2,15 +2,16 @@`, `-19,12 +20,13`, `-32,26 +34,27`). The 18 claimed edits are sub-hunk/adjacent, hence 7 hunks.
Per-edit presence test of each handoff `after` fragment: 18/18 present in substance; 0 claimed edits absent.
DISCREPANCY: MANUSCRIPT edit 10 (lines 738-742) records the after-string as `is **checkable**` but the file has plain `checkable` (M:737). Cosmetic only — the substantive rewording landed.

## CHECK 2 — no number changed
Literal census (regex `\d+(?:[.,]\d+)*`).
MANUSCRIPT.md: cur=307 lits, orig=306. CUR-not-ORIG = {`1.0.0`} (from "PolyForm Noncommercial 1.0.0"); ORIG-not-CUR = {}.
AVAILABILITY.md: cur=31, orig=31. CUR-not-ORIG = {`1.0.0`}; ORIG-not-CUR = {`5`} — traced to the deleted clause "(`README.md` §5 heading: ...)", a section reference, not a figure.
Nine required values — identical counts cur/orig: 0.3474 28/28, 0.4526 13/13, 0.2911 9/9, 0.6684 22/22, 0.6789 25/25, 0.3252 2/2, 0.8837 1/1, 0.9140 1/1, 0.3526 1/1. "No figure moved" is credible.

## CHECK 3 — licence passage vs recorded decision
Decision `strategy/CODE_LICENSING_STRATEGY.md:9-40` (ERRATA UMEMO1) + `strategy/licence-templates/RELEASED-PIECE/` (LICENSE = PolyForm NC 1.0.0 + Required Notice; COMMERCIAL.md = "Commercial use requires a paid licence").
Passage `papers/encoder-crossover-190/AVAILABILITY.md:3` (CC BY 4.0 paper text), `:12-14` and `:52-60` (released artifacts source-available under PolyForm NC 1.0.0 with author-offered paid commercial licence; main repository fully proprietary and closed, `LICENSE` "not restated") — all three points MATCH. No contradicting sentence in the new passage.
Outside the passage but inside the edited file: `AVAILABILITY.md:45` "frontier-lab norm — publish the eval harness, withhold the model" contradicts the withheld-harness scope. Pre-existing (also `scratch/upaper8/AVAILABILITY.md.orig:42`), NOT flagged or edited by UPAPER8.

## CHECK 4 — the three flags
(a) CONFIRMED. On disk: `repro/encoder-crossover-190/fixture/reflex-decisions.ts` sha256 = 076164ac53c2c1aac130953345c481f88b51f4d6fb93d465c7430308a99b4796 (as-audited); `repro/encoder-crossover-190-SANITISED/fixture/reflex-decisions.ts` = 751dc007ba115dccc5815fdf97c9ce7b34b0dc990a6e57802d762e9b35ad9cae (sanitised). The released-path README (`repro/encoder-crossover-190-SANITISED/README.md:58-65`) confirms 751dc007 is the shipped bytes. The manuscript quotes the as-audited digest at MANUSCRIPT.md:258 AND :799 and AVAILABILITY.md:22 — UPAPER8's flag named only :799; three sites carry it.
(b) CONFIRMED. MANUSCRIPT.md has 4 occurrences of `repro/encoder-crossover-190/`, 0 of `190-SANITISED`; AVAILABILITY.md:18 declares all paths under the non-sanitised name, 0 SANITISED mentions. On disk both trees exist; the sanitised one is the shippable build.
(c) PARTIAL. MANUSCRIPT.md:772 "Instrument integrity checks a replicator should re-run" — CONFIRMED (F4 152,000-pair / seeded-copy checks need the withheld harness). MANUSCRIPT.md:299 and :686 "Training is not bit-reproducible" — REFUTED as promises of a re-runnable harness: they state a limitation, though they presuppose retraining is possible. Additional unflagged sentence assuming a shipped harness: AVAILABILITY.md:45 (above).

## CHECK 5 — red-green
Wrote `scratch/uver29/check_scope.py`: passes only if MANUSCRIPT contains "The evaluation harness — the model, training and evaluation code — is withheld", "Honest limitation: the harness does not ship…", "checkable against the released reproducibility subset" and contains neither "re-derivable from the released reproducibility subset" nor "the evaluation harness with its frozen inputs".
Reverted copy `scratch/uver29/MANUSCRIPT.reverted.md` (edit 10 undone): FAIL rc=1 (missing=1 residual_old=1). Real file: PASS rc=0. Copy deleted; `scratch/uver29/` holds only check_scope.py.

## VERDICT
UPAPER8's claims survive: 18/18 edits landed, no figure moved, licence passage matches the decision, all three flags real (a and b confirmed, c partly). Residual defects for a follow-on unit: as-audited digest at MANUSCRIPT.md:258/:799 and AVAILABILITY.md:22; non-sanitised path name throughout; AVAILABILITY.md:45 "publish the eval harness"; MANUSCRIPT.md:772 re-run promise.
