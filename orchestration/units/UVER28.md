# UVER28 — verification of UOUTSIDE1
in progress

## Purpose (UVER28, verifier - replacement for UVER27)
Independently re-check the five outstanding UOUTSIDE1 claims; append each literal result to
strategy/VERIFICATION_REPORT_27.md as it is measured. Hard bound: 20 tool calls (used 14).

## Result: overall PARTIAL
1. tools reproduce in both trees (exit 0; identical kappa/agreement/exact/ties/zero/disagreements) - PASS
2. exactly 4 hand-added keys confirmed in both trees; disagreements.jsonl NOT reproducible (18/18 rows stale, unredacted vocabulary leaked) - PARTIAL
3. counts.files 45, counts.bytes_total 3009245, MANIFEST sha256 fecd3157...cd97ef - PASS
4. build-twice digest 63d015...52ef6 confirmed on two fresh rebuilds; sole inter-tree diff = MANIFEST.json/generated_utc - PASS
5. RED->GREEN on scratch/uver28/redgreen - PASS

## Write paths
strategy/VERIFICATION_REPORT_27.md, orchestration/units/UVER28.md,
orchestration/handoffs/UVER28.json, scratch/uver28/**
