# VERIFIER-P2 — independent recheck of measurement instrument (phase 2)

Adversarial verification of arms, tasks, driver, watcher/analyser, ledger/quarantine, live preflight. Full verdict: `experiments/context-cache/cells/CONTEXT-SERVING-CAMPAIGN/notes/VERDICT-P2.md`.

## Results
- Arms: 20/20 pass; gist content-free across all 8 instances; renderer hashes reproducible (current A cbbdf0b0... B 7b079fcb... C dcae2b6e... D f64683f9...); preamble parity + salt one-line diff confirmed.
- Tasks: 18/18 pass; determinism, two families/split, >=6 early deps, exact-body turns, 6 negatives fail, truncation ok:null, bwrap engages.
- Driver: 13/13 pass only after temporary envelope renderer-hash sync; committed envelope stale → fail-closed. --envelope mandatory, escape rejected, freeze aborts bad hash, first-row audit ok, salt cell equality.
- Watcher/analyser: 8/8 pass; null cache widens range; quality refusal; synthetic excluded.
- Ledger: 6/6 pass; 318 voids single reason; 2 real pre-quarantine vLLM smokes; status outcomes-minus-voids. Predicate over-broad vs current journal (324 matches vs 318 voids).
- Preflight: 6 claimed attempts all null cached_tokens (CACHE_FIELDS_UNRELIABLE supported); server-side "0 device hits" unverified (no snapshot).

## Red→green
- Gist: mutant leaked body into gist → test failed → restored → passed.
- Analyser: mutant disabled null detection → TypeError/crash → restored → passed.
- Driver: mutant disabled renderer-mismatch check → no refusal → restored → passed.

## Blocker
Stale envelope renderer hashes block all driver dispatch (fail-closed) until re-freeze; documented quarantine predicate over-broad for current journal.
