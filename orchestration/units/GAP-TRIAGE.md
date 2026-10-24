# GAP-TRIAGE — ten open gaps vs `UNVERIFIED: none`

**Status:** done. **Bound:** 75 tool calls (69 used). **Writes:** `papers/context-cache/GAPS.md`,
`papers/context-cache/PACKAGE.md`, `state/gap-triage.json`, `state/gap-ledger.json` (stated-status
strings only), `tests/test_gap_triage.py`, this card, the handoff JSON.

## Objective

`state/gap-ledger.json` derives **ten** sections of `GAPS.md` as `open`, while
`papers/context-cache/verify_package.py` exits 0 printing **`UNVERIFIED: none`**. Decide, per gap,
whether it is a **stated limitation** (the missing measurement is a boundary of scope, no claim
depends on it) or **stale prose** (a later cell had already outdated the sentence), then make the
reader-facing text say what is actually true.

## Method

1. Re-ran the gate and the value check: `verify_package.py` → PASS / `UNVERIFIED: none` (exit 0);
   `recompute.py all` → `59 claims checked, all match` + `COVERAGE GUARD PASS 62 claims`.
2. Re-derived the ledger statuses with `tests/test_gap_closure_ledger.py`'s own `derive()`:
   **closed 2 · narrowed 3 · open 10 · unverifiable 1**, zero stated-vs-derived disagreements.
3. Checked each of the ten against rows/claims on disk (not against its own prose), then:
   - marked each open heading `STATUS: OPEN (stated limitation …)`;
   - rewrote the two stale bodies (G12, G14) with a dated correction note and kept both gaps open;
   - added a triage-ledger section to `GAPS.md` and a scope sentence to `PACKAGE.md` §8: the gate is a
     census of claim *values*, not of scope.
4. Updated the ledger's `stated_status` strings to the new heading words (derived_status unchanged).
5. Guarded the result with `tests/test_gap_triage.py` (coverage of exactly the ten derived-open ids,
   a decision + evidence per id, status lines, no closure claims, and the two retired assertions
   cannot return).

## Result — ten decisions

| Gap | Decision | Why (evidence) |
|---|---|---|
| G2 | **stated-limitation** | 438 U4 rows, one renderer (C13); 438 batch + 13 probe = 451 vs the card's 454 (C14). Unusable by construction; re-run only close. |
| G6 | **stated-limitation** | C22 arithmetic (7.8 % / 92.2 %) is exact; C44 names the mechanism class but no per-turn prefix-diff exists (EVIDENCE §5). |
| G7 | **stated-limitation** | C38 372/372 appends deviate; C54 shows the state cache can bind, but the pure-attention control has not run (G4: both engines are Qwen3.5-MoE hybrid). |
| G8 | **stated-limitation** | C36 139/planned-200 requests, six lengths; TTFT only, decode absent by design. |
| G9 | **stated-limitation** | C40 n = 5 per length; C41 35/35 vs 0/15. The n = 20 cells were not run. |
| G10 | **stated-limitation** | C10 174/190 = 91.6 % floor; C08 max delta 2.632 pts; C09 retention 190/190 vs 0/190. |
| **G12** | **stale-prose** | "no eviction pressure was applied" and "1.3 M tokens" were package-wide claims; C54 (1.5017x, 283 docs, **1,620,892** declared capacity) and C59 (TUNED 1.505083x) contradict both. Corrected; the closer (real trace with concurrency) is still unrun. |
| G13 | **stated-limitation** | Row-key audit: no build/version key in any row; RUN.json has one image sha + "no per-cell launch log" (`server_config.json:1312` = one capture). No canary. |
| **G14** | **stale-prose** | "neither half has been tested at the limit" was outdated by G3-LIMIT-V2/C62 (2,780 rows, 18 compactions at 32k/64k). Corrected; the hybrid arm is absent from the cell's arms (B/B-ptr/S/S-ptr/F/F-ptr/S-k800/F-k800) and all 18 triggers are headroom, not overrun — so the gap stays open. |
| G15 | **stated-limitation** | C44 2/6 events within 10 %, E/F = 1.0384615; EVIDENCE:152-153 81/81 turns imbalanced. |

**8 stated limitations · 2 stale-prose fixes.**

## Evidence (commands and actual output)

```
.venv/bin/python papers/context-cache/verify_package.py
  PASS — 62 claims in CLAIMS.md, 62 mapped 1:1, ... UNVERIFIED: none            (exit 0)

.venv/bin/python papers/context-cache/recompute.py all   (tail)
  59 claims checked, all match
  COVERAGE GUARD PASS  62 claims documented, 60 runnable here + 2 script-backed (exit 0)

tests/test_gap_closure_ledger.py derive() re-run over the ledger
  {'closed': 2, 'open': 10, 'narrowed': 3, 'unverifiable': 1}; disagreements: []

PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest <10 guards> -q
  95 passed in 0.29s
```

Red→green (recorded, restored with `cmp` byte-identical): re-planting G12's
"no eviction pressure was applied (the KV pool holds 1.3 M tokens)" and G14's
"Neither has been tested at the limit." fails
`test_g12_stale_capacity_and_pressure_are_corrected` and
`test_g14_limit_regime_is_no_longer_denied` (2 failed, 7 passed); restored → 9 passed.

## Assumptions recorded

- The card's prompt is the only contract supplied; the ten ids come from the ledger's own
  `derived_status == "open"` (the same ten GAP-LEDGER2 reported), not from a re-reading of prose.
- `stated_limitation` means "the gap names a measurement that has not been run and no claim depends
  on it" — it is not a synonym for closed. Neither stale-prose fix closes its gap.
- Editing `state/gap-ledger.json` was limited to `stated_status` strings (to keep the ledger's own
  "the entry's own words" true) plus a `triage` block; `derived_status` and every `evidence_refs`
  entry were left untouched, and the ledger guard still passes.
- `scratch/gap-triage/GAPS.green.bak` is the red-arm backup, not a deliverable.

## Findings left to other owners

- `EVIDENCE.md` §5 still says G3-LIMIT-V2/C62 has no independent verifier; a fresh verifier card
  should re-derive C62 before any of G3's remainder is narrowed further. Not edited here.
- G13's per-row build pin and U2 44-repeat canary remain the two named, unrun closers.
