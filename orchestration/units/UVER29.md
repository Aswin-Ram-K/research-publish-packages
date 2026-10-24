# UVER29 — verify UPAPER8's 18 edits (encoder-crossover-190)
Purpose: verify edits in papers/encoder-crossover-190/{MANUSCRIPT.md,AVAILABILITY.md} match new release scope (data+verification tools only) and settled licence decision.
Hard bound: 20 tool calls. Stop and report if a check cannot be done in <=3 attempts.
Write paths: strategy/VERIFICATION_REPORT_29.md, orchestration/units/UVER29.md, orchestration/handoffs/UVER29.json, scratch/uver29/**
Checks: (1) 18 edits landed vs scratch/upaper8/*.orig (2) no numeric literal changed (3) licence passage vs CODE_LICENSING_STRATEGY.md:9-40 + licence-templates/RELEASED-PIECE (4) three flags + other harness-assuming sentences (5) red->green revert test.
Report: strategy/VERIFICATION_REPORT_29.md (stub first, append per check).
