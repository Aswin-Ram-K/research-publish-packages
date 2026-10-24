# UVER20 — independent verifier of UBIJ3 (rename-out release tree)

**Parent:** session-c3d61727-8af8-4c19-b1b9-5922c347a11a
**Hard bound:** 30 tool calls.
**Write paths:** strategy/VERIFICATION_REPORT_20.md, orchestration/units/UVER20.md,
orchestration/handoffs/UVER20.json, scratch/uver20/**.
**Read-only:** scratch/ubij1|ubij2|ubij3|uver19/**, repro/encoder-crossover-190-SANITISED/**,
/home/zer0null/Duval (read only, no git).

**Invariant under test:** the text the model actually reads must not change.

**Replacement unit:** UVER19 died after ~3 calls; its `strategy/VERIFICATION_REPORT_19.md`
is left untouched. Nothing in `scratch/uver19/` is relied upon.

## Checklist (status updated as checks land)
1. [ ] basics: counts / bytes / tree digests x3
2. [ ] census re-derivation (own scanner)
3. [ ] guard delta (inside-stimulus + distinct)
4. [ ] stimulus-only sha256 == 26c5ddcb...
5. [ ] tool re-run exit codes
6. [ ] metrics re-derivation
7. [ ] digest moved/unmoved table
8. [ ] packaging surface 309/240/187, 44 files, 11 dirs, imajev
9. [ ] K01..K10 layer 3676 / 0 inside
10. [ ] >=12 model-facing records byte-identical
11. [ ] measure.sh reproduction
12. [ ] RED->GREEN guard abort exit 3 (LAST)

## RESULT (complete)
VERDICT: **partial** — invariant holds and is fail-closed; 9/12 checks reproduce exactly,
3 do not (stimulus digest, packaging surface, measure.sh). See strategy/VERIFICATION_REPORT_20.md.
Rebuild of the shipped tree from `scratch/uver20/bij20.py` is byte-for-byte identical.
RED->GREEN: exit 3, no tree written. Defects: MANIFEST.json stale (D1), measure.sh KeyError (D2).
