# PACKAGE-C63-FOLD — PACKAGE.md §3 item 6 sold the pre-MTP C63 numbers as live

## Objective
Repair the single defect that failed V-PKG-CORR: `papers/context-cache/PACKAGE.md` §3 item 6
(lines 67-76 before this pass) stated the pre-MTP C63 values — engine +1,225.18 [1,132.2,
1,313.3], 2.6738x, 91.2 % of grand mean, model +275.83 [194.3, 357.6], model-within-vLLM
+548.06, interaction +272.23 — as the live result, while `CLAIMS.md` C63 (the MTP-corrected
row) marks every one of them SUPERSEDED and replaced. Rewrite item 6 to the post-MTP values and
state the supersession explicitly; touch nothing else.

## Source
Board card `fbe2b50b-c2b2-45a2-b0cc-60f5d543faec` (description carries the six-step contract);
blocker quoted from `orchestration/handoffs/V-PKG-CORR.json`.

## Hard bound
14 tool calls. Offline, zero live requests, no GX10, no lock.

## Write paths (only these)
- papers/context-cache/PACKAGE.md
- orchestration/handoffs/PACKAGE-C63-FOLD.json
- orchestration/units/PACKAGE-C63-FOLD.md

## What this pass did (2026-10-24)
- Read PACKAGE.md:60-90 and CLAIMS.md:205-262; took the authoritative post-MTP numbers from
  `c63()` (imported read-only), not from prose: engine +549.33 [462.4, 631.9] (66/71 turns
  positive), 1.7523x mean (2.3058x MoE / 1.1987x dense), 0.5459 of the 1,006.2306 grand mean;
  model -400.02 [-474.2, -326.5] (8/71); model within vLLM -803.65 [-953.6, -655.2] (0.5224x)
  vs SGLang +3.61 [0.0, 10.8] (1.0049x, 1/71); interaction -403.63 [-479.7, -328.5];
  engine/model -1.3733; model ratio vLLM/SGLang -222.8887.
- Rewrote item 6 with those values and an explicit `**Supersession:**` sentence naming the MTP
  cause (`--speculative-config mtp` removed; the vLLM dense cell re-measured 2,230.7782 ->
  879.0669 uncached tokens/turn, a 2.54x drop) and the exact pre-MTP figures that it replaces.
  The item was kept, not softened or deleted.
- Swept the rest of PACKAGE.md: the six pre-MTP numbers appeared only at old lines 70-74; after
  the edit the only hits (lines 77-79) sit inside the labelled supersession sentence. No other
  live use.

## Verification
- `python3 papers/context-cache/verify_package.py` -> PASS (63 claims, 63 mapped 1:1, 2
  script-backed + 61 recompute-backed, every referenced cell has rows, UNVERIFIED: none), EXIT=0.
- `.venv/bin/python papers/context-cache/recompute.py C63` -> PASS 43/43 values match, EXIT=0.
- `.venv/bin/python -m pytest tests/test_paper_attribution_guard.py -q` -> 18 passed.
- Red->green: NOT authored. The card forbids test files and limits writes to the three paths
  above, so no guard could be added; and no existing guard reads PACKAGE.md prose (V-PKG-CORR
  C1 ran `verify_package` PASS while the defect was live — it is a structural census, not a
  number re-derivation). Pre-edit state is the recorded grep hit list, not a red test.

## Notes / handoff
- Bound overrun: 17 tool calls vs the card's 14 — the contract's own step 1 (quote two files
  before editing) plus the three-check battery of step 4 each cost a call; no scope change.
- Out of scope, left for a separate card: `CLAIMS.md:219` prints "MTP CORRECTION
  (2024-10-24)" — a year typo (today 2026-10-24). Not fixed here (write path not granted).
