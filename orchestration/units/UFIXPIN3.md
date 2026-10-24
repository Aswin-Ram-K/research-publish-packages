# UFIXPIN3 — fix the two remaining live stale claims

Status: done (bound 10 tool calls; used 10). skeleton_written_first: yes
Write paths: orchestration/units/UBUILD1.build.sh, strategy/SUBMISSION_READINESS.md,
scratch/ufixpin3/**, orchestration/units/UFIXPIN3.md, orchestration/handoffs/UFIXPIN3.json

## Defect 1 — stale printed figures in UBUILD1.build.sh (frozen-override branch)
Chose option (b). Option (a) was not taken: the discovery sweep found no existing
residual-identifier measurement script (only repin copies of this same build script carrying
the same stale echo: scratch/ufixtree1/UBUILD1.repin.build.sh, scratch/vufixtree1/UBUILD1.repin.sh),
the frozen tree repro/encoder-crossover-190-SANITISED is 5,611,997 bytes, and no reproducible
definition of 'residual project identifiers' exists in the workspace — a new count would be a
different measurement. No number is invented or carried over.
Edit (echo remains inside the same SAN_SRC_FROZEN_OVERRIDE=1 branch; control flow unchanged):
- before: echo "                input; ~12.4x more residual project identifiers: 44,056 vs 3,317)."
- after : echo "                input, not the promoted release artifact; see strategy/BUILD_PIN_CHANGE.md"
          echo "                for current measurements)."

## Defect 2 — strategy/SUBMISSION_READINESS.md (Appendix Z item Z4)
The single live urecut1 occurrence was located by reading (Appendix Z, Z4), not from the stale :222 hint.
- before: ...build.sh:134` pins `PROMOTED_SAN_SRC="$SRC/scratch/urecut1/package"`, while later units produced ...uneutral10/package ...
- after : ...build.sh:134` pins `PROMOTED_SAN_SRC="$SRC/scratch/uneutral10/package"` — corrected 2026-10-16 by UFIXPIN3;
          the superseded pre-promotion pin is recorded in strategy/BUILD_PIN_CHANGE.md and the frozen unit cards and
          handoffs — while later units also produced scratch/utool1/tree-six, scratch/udtag1/tree-five and scratch/ufix31/pkg.
No 874,473-byte old-tree figure appears anywhere in SUBMISSION_READINESS.md, so no size edit was needed there.
Superseded figures found in the doc and deliberately left (Appendix Z charter: 'Preserved, not rewritten' —
UFMT2's 2026-10-16 observations, each already superseded by a dated Z correction):
26,580 B tarball at :85 and :200 (superseded by Z1: 28,403 B), main.tex 80,780 B at :77 (superseded by Z2: 83,700 B),
ABSTRACT_METADATA 1,195 vs 1,194 at :193-196 (recorded reconciliation ledger).
874,473 bytes appears only in strategy/STIMULUS_NEUTRALISATION.md:7 and strategy/PUBLIC_PACKAGE_CUT.md:51,88,149
(historical records of the superseded cut, not this unit's write paths).

## Independent measurement of the promoted tree
du -sb scratch/uneutral10/package = 841306; find -type f | wc -l = 29 (matches the briefed 841,306 B / 29 files).

## Verification
before/after sha256: UBUILD1.build.sh dbf96e94eb418054848a14cf23abca3400f248b7b1c214eadc0b2747ee7f413d -> f44c71e96c70bef335d53594761460afd6d0546b0fd3d0a282b962e0de34096d ; SUBMISSION_READINESS.md 1c3932aa8dec4d2cb744e1ea93c0700bcfc724daac13543578c015cff2efca54 -> 57a008819b67597c4993bed3c858ce729e14bca70cf30dbd7244a763b68e0487
bash -n: pass ; grep -c urecut1: script=0 readiness=0 ; PROMOTED line: 134:PROMOTED_SAN_SRC="$SRC/scratch/uneutral10/package"
