# U-SPCC-31 — correct the corpus-provenance inference

**Status:** done. **Date:** 2026-11-10. **Predecessor:** `U-SPCC-30` (commit `be5e139`).

## Why

`U-SPCC-30` measured fixture-digest matches and then wrote that the unaffected rows files are
"0 missing and fully reproducible". A matching `fixture_sha256` establishes only that the fixture bytes
are present on disk. Replay additionally needs the model artefact, the server build and flags, the
tokenizer, the sampling parameters, the harness code version and the prompt-construction path — none of
which the digest check touches. The inference was wrong; the measurement was not.

## What changed

- `experiments/ptr-engine/research-seed-concepts/FINDINGS-LEDGER.md` — headline sentence now reads
  "have their fixtures available"; added a **Replay is unverified** paragraph; the closing sentence now
  says the remaining 82.3% are unverified too; "Method, reproducible" → "Method, repeatable".
- `docs/STATE.md` §11 — new **Corpus-wide fixture provenance** paragraph with the counts and the
  replay-unverified sentence.
- `journal/2026-11-10.md` — correction item 10.
- `orchestration/STATUS.md` — batch row `U-SPCC-30`, `31`.

## Counts (unchanged)

7,734 pins · 1,368 missing · 1,272 unrecoverable · 96 recoverable · 13 of 93 files affected · 80 of 93
with zero missing pins.

## Acceptance

`grep -rn "fully reproducible\|0 missing and fully reproducible"` over the four files is empty;
`fixture available` and `replay is unverified` appear in each document that carries the finding;
`python3 tools/doc_check.py` exits 0.
