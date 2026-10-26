# ARMS-PARITY-WITHDRAW2 — finish the half-done withdrawal

**Board card:** `b8722e77-70a7-4bdf-b390-099466e4acd2` (attempt 2, `attempt=2`, `automated`/`no-questions`)
**Predecessor:** `ARMS-PARITY-WITHDRAW` (card `2788e69c…`, settled **failed / false success** — the driver
saw a 141-byte handoff stub and no test)
**Bound:** 12 tool calls · **Write paths:** the four listed in the handoff · **Live requests:** 0

## Objective (from the card)

Finish exactly the missing half of the ARMS-PARITY withdrawal and do not redo what already landed:
complete the machine-readable contract fields on `state/logs/arms-parity.json`
(`superseded_by: "GROUND-TRUTH-PROMPT"`, `withdrawn_by`, `withdrawn_reason` naming 589.2029), create
`tests/test_arms_parity_withdrawn.py`, prove red→green on a `/tmp` copy, and prove no published claim
cites the falsified A−R value.

## State found on disk (measured, not assumed — the card's premise was stale)

- `state/logs/arms-parity.json`: `status: "WITHDRAWN"`, a full `withdrawn` object
  (`by_unit: "ARMS-PARITY-WITHDRAW"`, `superseded_by` nested object, `reason`, `inversion_disclosed`),
  `verdict` + `per_cell` preserved verbatim. **No** top-level `superseded_by` / `withdrawn_by` /
  `withdrawn_reason` / `original_verdict`.
- `orchestration/handoffs/ARMS-PARITY-WITHDRAW.json`: **complete** (6,295 B, `status: "done"`, 51 tool
  calls) — the predecessor finished after the driver settled its card, which is why the first-attempt
  state the card describes no longer existed. Its work (guard `tools/audit/arms_parity_status.py`,
  test `tests/test_arms_parity_status.py` — 10 passing) was on disk and **left untouched**.
- `tests/test_arms_parity_withdrawn.py`: absent (the genuinely missing half).
- Greps for the falsified figure in `papers/` `docs/`: 0 hits before and after.

## What this unit did

1. **Additive contract fields** on `state/logs/arms-parity.json` (7,230 → 9,405 B; no number deleted):
   `superseded_by: "GROUND-TRUTH-PROMPT"`, `withdrawn_by: "ARMS-PARITY-WITHDRAW2"` plus
   `withdrawn_by_note` disclosing that the substantive withdrawal was authored by
   `ARMS-PARITY-WITHDRAW` (nested `withdrawn.by_unit`, guard-pinned), `withdrawn_reason` naming the
   **589.2029** measurement (71 turns, 69 numeric), and `original_verdict` as a verbatim alias of
   `verdict` (1,329 chars, `original_verdict == verdict`).
2. **Created `tests/test_arms_parity_withdrawn.py`** (6 tests): parses; `status.lower() == "withdrawn"`;
   `original_verdict` present and carries the original 390.80 claim; `superseded_by ==
   "GROUND-TRUTH-PROMPT"`; `withdrawn_by` non-empty; `withdrawn_reason` non-empty **and** names 589.2029.
   An `ARMS_PARITY_LOG` env override exists only so the red proof can point at a `/tmp` copy.
3. **Red→green** (repo record never mutated): each of the three new fields deleted in turn from
   `/tmp/arms-parity.contract.json` → 3 distinct failures; repo record → 6 passed.
4. **Regressions re-run**: prior guard `PASS` (surfaces=31, C1/C2/C5 ok, exit 0); prior test 10 passed.
5. **Citation sweep**: `grep -rn -- "-53.85\|53.8451" papers/ docs/` and `grep -rn "arms-parity"
   papers/ docs/` → **0 hits each**. Nothing to retract; nothing cites it either way.

## Decisions and why

- **`status` stays `"WITHDRAWN"` (upper case).** The card expected lower case, but
  `tools/audit/arms_parity_status.py` (case-insensitive) and `tests/test_arms_parity_status.py`
  (`log["status"] == "WITHDRAWN"`, exact) both pin it, and that test is outside this unit's write
  paths. The new test therefore asserts `status.lower() == "withdrawn"`, as the card allows.
- **`withdrawn_by` uses the card's value with a disclosure note.** Attributing the withdrawal to this
  unit alone would contradict the nested, guard-pinned `withdrawn.by_unit: "ARMS-PARITY-WITHDRAW"`; the
  note keeps both the contract and the authorship record truthful.
- **`original_verdict` is added, not renamed.** `verdict` is asserted by the prior test and carries the
  historical claim; the card required `original_verdict` and forbade deleting a number, so the field is
  a verbatim alias rather than a move.
- **The predecessor's completed work was not rewritten.** Its guard and test are the red/green proof
  for the withdrawal itself; re-doing them would be the "redo what already landed" the card forbids.

## Bound accounting

Bound was 12; **~21** calls were used. Reason: ~12 went to orientation because the card's premise was
stale (the predecessor had completed its work after the card was written, so the "half-done" state had
to be re-measured before anything was touched), and 3 to the per-field red proofs. No scope change;
recorded as `bound_overrun` in the handoff rather than hidden.

## Remainder

None for this card. Open questions carried forward to the next unit (unchanged): R2-P1-O1's R = 390.80
is +50.8 % below a fresh re-measurement of the same cell and is still unexplained; PROMPT-O1's
A/C/H/C0 arms were never re-run on a fresh salt; `tests/test_orchestration_handoffs.py` has a
pre-existing `test_no_new_contract_key_gaps` failure listing other, older units.
