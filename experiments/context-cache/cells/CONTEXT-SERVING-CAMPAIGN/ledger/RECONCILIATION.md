# Reconciliation — historical accounting vs campaign

## Sources reconciled (read-only)
- `/home/zer0null/research extractor/experiments/ptr-engine/measure/REQUEST-LEDGER.json`: 2591 requests, 1729 remaining, cap 4320. Dedup rule unsound (content_sha256 hashes assistant content); 30 duplicate_excess NOT deducted.
- `/home/zer0null/research extractor/experiments/ptr-engine/measure/RESERVATIONS.json`: 1 reservation (CCS, granted 1500).
- CCS `ledger/RESERVATION-CCS-2026-11-05.json`: requested 1500, granted 1500, ledger_remaining_at_reservation 1729.
- CCS `ledger/SPENT-CCS.json`: spent 208, cap 1500.
- CCS rows: 209 intents (intents.jsonl 154, cal-intents 14, cal2-intents 27, cal3-intents 14) vs 189 row-bearing sends. Orphans by send_id: 20 intents without row (cal2 12, cal3 5, intents.jsonl 3); zero rows without intent. Not deduplicated by assistant-content hash.
- HL-PILOT `CALL-LEDGER.md`: stated 765 model calls; table arithmetic sums to 767; row files sum 749 (+14 E1B no-row +4 probes = 767).

## Arithmetic defended
- ptr: 4320 cap - 2591 spent = 1729 remaining.
- CCS: 209 intents - 189 row-bearing = 20 unrowed sends by id.
- CCS reservation 1500 is historical; SPENT-CCS 208 is CCS's own spending.

## Unknowns
- 20 (not 19) CCS intents carry no row; causes grouped by file only.
- HL-PILOT 2-call discrepancy (765 stated vs 767 table sum).
- E1B 14 calls left no rows; E5 LR-01 30 aborted rows.
- ptr 30 duplicate_excess not deducted (unsound rule).
- Historical "756 remaining" was conditional, not a verified balance.
- CCS reservation does not fund this campaign.

## Statement
The earlier 756-remaining calculation was conditional, not a verified balance. The historical CCS reservation of 1500 calls is historical and does not fund or consume the new 1500-call campaign allowance. This campaign has its own ledger (1500 cap).
