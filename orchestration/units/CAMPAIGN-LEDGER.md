# Unit CAMPAIGN-LEDGER

## A. Reconciliation
- Wrote `$CAMPAIGN/ledger/RECONCILIATION.md` and `reconciliation.json`.
- CCS: 209 intents vs 189 row-bearing sends; 20 orphan intents by send_id (cal2 12, cal3 5, intents.jsonl 3); 0 rows without intent. No assistant-content-hash dedup.
- ptr ledger: 2591 spent, 1729 remaining, cap 4320; 30 unsound duplicate_excess not deducted.
- HL-PILOT: stated 765, table sum 767, row files 749 (+14 no-row +4 probes).
- Historical 756 figure conditional; CCS reservation 1500 does not fund campaign.
- Historical files: 19 inputs, sha256 before/after: 0 mismatches.

## B. Campaign ledger
- `$CAMPAIGN/ledger/campaign.json`: total 1500, phases preflight 48/context 384/prompt_format 192/serving 288/holdout 384/contingency 204.
- `$CAMPAIGN/ledger/ledger.py`: flock on absolute lock, fail-closed reads, reserve/record/status, --dry-run, index consistency check.
- Lock file created; fresh status: 1500 remaining, 0 spent.

## Tests
- `$CAMPAIGN/tests/test_campaign_ledger.py`: 6 tests, all pass.
- Red proof: removed phase-cap check in /tmp copy; 2 tests failed (phase cap exceeded, 4th reserve succeeded). Restored original; 6 passed.
