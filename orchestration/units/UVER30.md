# UVER30 — verifier of UGATE3 gate/build claims

Purpose: independently re-derive UGATE3's 7 claims. Author != verifier.
Bound: 20 tool calls. Write paths: strategy/VERIFICATION_REPORT_30.md,
orchestration/units/UVER30.md, orchestration/handoffs/UVER30.json, scratch/uver30/**.
Status: IN PROGRESS (report grown after each check).

## Result (DONE, 13 tool calls / bound 20)
- C1 CONTRADICTED: digest bbf5a52c… and :134 PROMOTED_SAN_SRC verified, but the file's
  mtime 01:15:52 postdates scratch/ugate3/build1.log (01:14:04) and its deterministic
  gate.sh (cccacbe9…) != scratch/ugate3/dest/…/gate.sh (7df3ed72…). "NOT modified"
  (orchestration/units/UGATE3.md:40) does not hold.
- C2 VERIFIED (my rerun: 29/29/0, 39 files, 74959 words, 501/32, anchor in 4,
  15 never-ship absent). C4 VERIFIED (80/38, 1054/296, 276/11, 0; 1410 occ / 321 distinct).
  C5 VERIFIED (11 tokens only in the released stimulus; 276 occ; opened in place).
  C6 VERIFIED (1411 names REPORT.md:305; 1410 after restore). C7 VERIFIED (rc 2 + exact
  FATAL; build exits $GATE_RC, never "PASSED").
- C3 NOT_REPRODUCED: current script gives 1398, not 1410. 1410 only from UGATE3's frozen
  artifact. Old=1689 unverified; analysis records 1740 (GATE_VOCABULARY_ANALYSIS.md:376).
- Vacuity control passes (injected policyHash flagged, injected banana not).
