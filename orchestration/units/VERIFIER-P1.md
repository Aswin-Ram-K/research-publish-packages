# VERIFIER-P1 — independent recheck of phase 1

Adversarial verification of preservation manifest, reconciliation, and campaign ledger. No historical cells modified. Full verdict: `experiments/context-cache/cells/CONTEXT-SERVING-CAMPAIGN/notes/VERDICT-P1.md`.

## Results
- Preservation: 713 files (663+50) reproduced; 22 externals all hash-match; HEAD f17663d reproduced; lock pid 723294 dead (honest); checker clean (exit 0); drift detection red→green reproduced.
- Reconciliation: 209 intents / 189 rows / 20 orphans (cal2 12, cal3 5, intents 3); 0 rows without intent; no content-hash dedup; ptr 2591/1729/4320; CCS 1500 granted/208 spent; HL 765 stated vs 767 table vs 749 row files. Plan premise 19 corrected to 20.
- Ledger: 1500 + phase caps reproduced; flock fail-closed; durable uuid intents; corruption fail-closed; cap enforcement red→green (mutant allowed over-cap, original rejected); tests 6/6 pass.

## Red→green
- Preservation checker: /tmp mirror unchanged OK → modified/added/tampered fail → restored OK.
- Ledger cap: mutant (`>=`→`>`) allowed 4th reserve vs cap 3 → original rejected.

## Blocker
none (minor porcelain count off-by-one: manifest 74, claim 73; 10 new untracked campaign artifacts).
