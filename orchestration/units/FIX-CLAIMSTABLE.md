# FIX-CLAIMSTABLE

**Objective.** Repair the three defects PAPER-FINAL-V2D returned `overall: fail` for, in the
order given: (1) the damaged `CLAIMS.md` source-key table, (2) the two numbers V2C claimed
guarded but which are not, (3) a red→green that is real this time.

**Hard bound.** 20 tool calls. If the dedup could not be made consistent in 6 calls, STOP and
report `partial` naming every ambiguous key.

**Write paths.** `papers/context-cache/CLAIMS.md`, `papers/context-cache/MANUSCRIPT.md`,
`papers/context-cache/recompute_r2.py`, one new `tests/test_claims_value_guard.py`,
`orchestration/handoffs/FIX-CLAIMSTABLE.json`, this card.

**Contract.** No live requests, no GX10, no container. Do not touch `recompute.py`,
`verify_package.py`, `RUN.json`, `EVIDENCE.md`, `GAPS.md`. Never loosen an existing checker;
add.

## What was done

1. **Table.** V2C had added 18 rows, 8 of them duplicate paths and 9 unused `-rows` aliases,
   and introduced two dangling refs (`P2-REPAD-rows` cited by C64 while the table defines
   `REPAD-rows`; `R2-VLLM-CELL-rows` cited by C65 and defined nowhere). Fix: delete all 17
   `-rows` alias rows, keep the 8 new Round-2 keys that are actually cited, re-point C64 and
   C65 at the defined keys. Paths are unique again (37 rows / 37 paths).
2. **Guard.** `tests/test_claims_value_guard.py` links `CLAIMS.md` text to the recompute pins
   for the first time: pinned scalars must be legible in the claim's Value cell, C69's quality
   pairs must be written `19/20 -> 18/20`, and the `MANUSCRIPT.md:901` census must not claim
   more arms than `recompute.EXPECTED["C62"]["arm_kinds"]` measured. `NOT_IN_CELL` waives, with
   reasons, the pinned keys that are only numbers in the raw rows.
3. **Red→green.** Both V2D plants now fail the guard and pass once reverted byte-exact.

## Assumptions (no answerer in an automated session)

- V2C had **deleted** 15 legitimately defined source paths (U2/U4/U9/U5/U4b/U15/G1/G3/
  WIN-SGL/WIN-VLLM/TUNED/G3V2/MOE-VLLM/DENSE-SGL/G5/M4) and had left `REPAD-rows` and
  `TRACK-t256` uncited. "Restore the pre-V2C table and re-add only genuinely new keys" reads
  as: those 17 rows come back too. Without them `verify_package` and `recompute.py all` both
  pass while citing paths the table no longer defines.
- `R2-VLLM-CELL-rows` (the renamed alias, cited by C65) is retired rather than defined: the
  only file it could plausibly name, `SYS-OPT/round-result.json`, is a JSON artefact whose
  "rows" figure is payload, not lines -- adding it broke
  `test_round1_record_pins.py::test_claims_source_table_recomputes` (`row count drifted,
  assert 72 == 71`). C65 cites `R2P-O4` instead.
- `C63` lost its value cell in V2C: the row at `CLAIMS.md:230` has two cells, so its
  "corrected" numbers live in the claim text and a MTP CORRECTION note. Not repaired here --
  `recompute.py C63` still PASSes, and rewriting a superseded claim is out of this unit's
  scope. Recorded as residual.
