# REQUEST-LEDGER-2 — re-publish the spend figure with the duplicate rule applied

**Status:** done · **Bound:** 26 tool calls (used 20) · **Requests:** 0 (offline, zero inference calls, no network)

## Purpose
`TVS-REGRADE` measured 30 defensible duplicate rows out of 1,101 and concluded raw 1,101 →
de-duplicated 1,071, remaining 3,219 → 3,249. It also found the ledger's three exclusion-marker
names (`billed:false`, `followup_suppressed`, `served_from=='prompt'`) do not occur in the corpus,
so the ledger's exclusion logic was unreachable and its headline 30 rows too high. This unit applies
the rule inside the ledger (per file, honouring each file's schema decidability), re-publishes both
figures, reconciles the markers the writer actually emits, and keeps the exit-code contract.

## What changed
1. `experiments/ptr-engine/tools/request_ledger.py` — duplicate rule applied per file, only where
   every row carries a non-empty `content_sha256` and a millisecond `ts`. Legacy files are
   `rule_status: "not_applicable"` with a written reason and the un-applied collisions reported under
   `collisions_not_applied`. Report now carries `requests_raw`, `requests_deduplicated`, `requests`
   (headline), `remaining_raw`, `remaining`, `duplicate_excess`, `dedup_rule`, `files_deduped`,
   `files_not_applicable`, `per_file`, `marker_reconciliation`, `dedup_decision`. `budget.spent` is the
   de-duplicated figure; `budget.spent_raw` keeps the raw one. Exit 4 prints the de-duplicated
   arithmetic and says so.
2. `experiments/ptr-engine/measure/REQUEST-LEDGER.json` — re-published, both figures.
3. `experiments/ptr-engine/tests/test_request_ledger_dedup.py` — 8 offline tests (3 duplicate groups;
   legacy-schema non-application; --would-spend boundary; unreadable rows; red→green on the dedupe
   call; real corpus 1,101/1,071/30).
4. `docs/REQUEST-LEDGER.md` — the published page: two figures side by side, per-file decision status,
   marker table with corpus counts, cap-gate contract, "what a caller should quote".

## Measured outcome
raw **1,101** → de-duplicated **1,071** (excess **30**: v6-tools 11, v4-tools 17, v5-tools 2);
remaining **3,219 → 3,249**; **11 files decided, 3 not_applicable**.

## Count discrepancy, recorded
The card says 9 decidable / 5 legacy files. A direct schema census says 11 / 3 — only `rows-baseline`,
`rows-equalinfo` and `rows-live` lack `content_sha256` and a millisecond `ts`. The published arithmetic
is identical under either split (every one of the 30 excess rows is in a decidable file). The report
carries the measured split plus a `count_discrepancy` note instead of the card's number.

## Never touched
No rows file, no grade file, `TVS.json`, `LATENCY-REPORT.json`, cap (4,320) or reserve. Both test
suites hash every row file before/after.

## Evidence
- `python3 experiments/ptr-engine/tools/request_ledger.py` → `TOTAL 1101 rows, 1101 raw, 1071 dedup, 30 dup, 11 decided/3 n/a`; `budget: spent=1071 ... remaining=3249 (raw: spent=1101 ... remaining=3219)`.
- `python3 -m unittest discover -s experiments/ptr-engine/tests -p 'test_request_ledger_dedup.py'` → 8 tests, OK.
- `python3 -m unittest discover -s experiments/ptr-engine/longrun/tests -p 'test_request_ledger.py'` → 16 tests, OK.
- Red→green: mutant `dedupe_applied = True` → `False` ⇒ `FAIL: test_1_three_duplicate_groups_excess_three` / `AssertionError: 0 != 3 : 3 duplicate groups` (6 failures); restored ⇒ 8/8 OK.
