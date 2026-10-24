# FIX-EVID-DOC — unit card

**Date:** 2026-10-23 (execution session of board card `7701a109-de54-4c71-952a-a2c38c354d77`)
**Contract:** board card prompt `FIX-EVID-DOC — EVIDENCE.md still calls CX-V3 pending and cites a
stale recompute.py digest` plus the card description (read via `task_board_get`/`task_board_list`
in-session — the board sends the prompt only, so the full contract was recovered from the card).

## Objective
Bring `papers/context-cache/EVIDENCE.md` in line with `orchestration/VERDICTS.md:12`
(CX-V3 **PASS**, 2026-10-21 05:22) and correct the stale `recompute.py` digest it cites.

## Declared write paths (checked against concurrent cards)
- `papers/context-cache/EVIDENCE.md` (owned by this card; sibling `FIX-GAPS-RUN` owns
  `GAPS.md`/`RUN.json` and was told not to touch `EVIDENCE.md` — no clash)
- `orchestration/handoffs/FIX-EVID-DOC.json`
- `orchestration/units/FIX-EVID-DOC.md` (this file)

## What was done
Five lines rewritten in `EVIDENCE.md` (card's line numbers had drifted by ≤2; real ones used):
1. `:251` U15 row: "not yet (see §5)" → "CX-V3 (PASS, 2026-10-21; see §5)".
2. `:265-269` "What U7 recomputed" paragraph: dropped "independent verification has **not**
   happened" and the "pending CX-V3 entry" sentence; now records the PASS with the verdict's
   own evidence (recompute 41/41, u5_recon 760/760, 13/13 digests, red→green 1/1 reproduced).
3. `:272` digest `63a4f0e6644ba788e6c38d102ed39687e78d0b4d9a8ba5ba808a5556a4a0623d` →
   `85917e480d1aea24d0d5b85ab75ab0464cd2b950ff6d7622ed093be09716abcc`, measured by
   `sha256sum papers/context-cache/recompute.py` in this pass.
4. `:293-295` §5 bullet 1: "No independent verification of U15 yet" → on-record PASS bullet.
5. `:298` §5 bullet 2 tail: "CX-V3 remains the gate for those" → "has since ruled PASS".

Not touched (out of scope, deliberate): `:311-313` G3-LIMIT-V2 "no independent verifier yet"
bullet (a different fact, no PASS verdict exists for it), and everything in `GAPS.md`/`RUN.json`
(sibling card's files).

## Verification (run in this pass, all green)
- `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python papers/context-cache/recompute.py all`
  → `GRID GUARD PASS  7/7 configs`; `59 claims checked, all match`; rc=0.
- `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest tests/test_paper_attribution_guard.py
  tests/test_claims_decompose.py -q` → `31 passed in 0.12s`; rc=0.
- `sha256sum papers/context-cache/recompute.py` →
  `85917e480d1aea24d0d5b85ab75ab0464cd2b950ff6d7622ed093be09716abcc` (matches the card's
  EVID-FRESH measurement and `RUN.json`'s current pin).

## Hard rules honoured
No edit to `RUN.json`, `GAPS.md`, `CLAIMS.md`, `MANUSCRIPT.md`, any test, `recompute.py`, or
`verify_package.py`; `verify_package.py` not run (sibling owns `RUN.json`); zero live requests.
Bound 20 tool calls — used ~12.
