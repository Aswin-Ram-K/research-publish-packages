# VERDICT-P1 — independent recheck of phase 1 (evidence and accounting)

Verifier: VERIFIER-P1. All claims tested against raw files; no historical cell modified.

## Claim 1 — preservation manifest (`pins/PRESERVE-MANIFEST.json` + `verify_preserved.py`)

| Sub-claim | Verdict | Evidence |
|---|---|---|
| 713 files across two cells (CCS 663 + HL-PILOT 50) | REPRODUCED | `find ... -type f` → 663 + 50 = 713; manifest records same. |
| 22 external records | REPRODUCED | 22 entries; all 22 hashes/sizes match (checked). |
| HEAD f17663d1fed0162a7dc3c5a0a58d372c710974c3 | REPRODUCED | `git rev-parse HEAD` = f17663d… |
| 73 porcelain entries | OVERSTATED (minor) | Manifest records 74 entries (73 newline lines). All 74 original entries still present in current status; 10 NEW untracked campaign artifacts added since (handoffs/units), so current total 84. No original entry disappeared. |
| clean verify run | REPRODUCED | `verify_preserved.py --baseline ...` → "OK: no drift", exit 0. |
| red proof / drift detection | REPRODUCED | /tmp mirror: unchanged → exit 0; modified file → `DRIFT modified`, exit 1; added file → `DRIFT added`, exit 1; tampered manifest hash → exit 1; restore → exit 0. |
| lock released 2026-11-04T13:46:15Z pid 723294 | REPRODUCED | lock file content matches; `kill -0 723294` fails (dead); manifest `lock_pid_alive=false`. Honest. |

## Claim 2 — reconciliation (`ledger/RECONCILIATION.md` + `reconciliation.json`)

| Sub-claim | Verdict | Evidence |
|---|---|---|
| 209 intents vs 189 row-bearing = 20 orphans | REPRODUCED | 154+14+27+14=209 intents; 9 row files sum 189; send_id set diff = 20 orphans. |
| orphans cal2 12, cal3 5, intents 3 | REPRODUCED | Counter by source file = cal2 12, cal3 5, intents 3. |
| zero rows without intent | REPRODUCED | 0 row send_ids absent from intent set. |
| no content-hash dedup | REPRODUCED | 126 distinct text hashes among 189 rows, 9 hashes repeated, 63 extra duplicate rows retained. |
| ptr 2591 spent / 1729 remaining / cap 4320 | REPRODUCED | REQUEST-LEDGER.json budget: spent 2591, remaining 1729, cap 4320. |
| CCS reservation granted 1500, spent 208 | REPRODUCED | RESERVATION-CCS granted 1500; SPENT-CCS spent 208. |
| HL stated 765 vs table 767 vs row files 749 | REPRODUCED | CALL-LEDGER arithmetic sums to 767 (3+39+14+48+93+264+120+30+8+144+4); row files sum 749 (3+39? no-row E1B 14 + probes 4 excluded). |
| plan premise of 19 orphans | CORRECTED → 20 | Reconciliation documents 20 (not 19); raw recount confirms 20. |

## Claim 3 — ledger (`ledger/ledger.py`)

| Sub-claim | Verdict | Evidence |
|---|---|---|
| 1500 total cap + phase sub-caps 48/384/192/288/384/204 | REPRODUCED | campaign.json. |
| absolute-path flock | REPRODUCED | acquire_lock opens lock file r+ and fcntl.flock(LOCK_EX); missing lock → fail closed (tested). |
| durable pre-dispatch intent, uuid attempt id | REPRODUCED | append_event writes+fsync before print; kill -9 mid-flight left complete JSON line; test_killed_after_intent. |
| outcome recording | REPRODUCED | cmd_record appends record event, validates attempt_id/outcome. |
| fail-closed on corruption | REPRODUCED | test_corrupted_journal + /tmp attack: status/reserve both exit 1. |
| 1501st rejected before dispatch | REPRODUCED | reserved_total >= total_cap check before append_event; /tmp cap=1 rejects 2nd; cap=3 rejects 4th. |
| 6/6 tests | REPRODUCED | `PYTHONNOUSERSITE=1 python3 -m pytest .../test_campaign_ledger.py -q` → 6 passed. |
| red→green cap enforcement | REPRODUCED | mutant (`>=`→`>`) allowed 4th reserve against cap 3; original rejected it. |

## Red→green summary
- (a) preservation checker: /tmp mirror unchanged OK (exit 0) → modified/added/tampered (exit 1) → restored OK (exit 0).
- (b) ledger cap: mutant allowed over-cap reserve (RED) → original rejected (GREEN).

## blocker
none. (Minor: porcelain count off by one in manifest snapshot; current tree has 10 additional untracked campaign artifacts — expected, not historical drift.)
