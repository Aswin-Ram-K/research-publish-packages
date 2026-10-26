# V-QUALITY-ARM — independent re-derivation of the QUALITY-ARM handoff

Verifier, not author. Offline only: `quality/runner.py` was never executed (no live endpoint consumed).
All work on `/tmp` copies. Write paths: this file + `orchestration/handoffs/V-QUALITY-ARM.json`.

## 1. rows.jsonl — reconciled exactly

`115` rows parsed by `json.loads` (no partial lines). Per-kind: `request 48`, `prediction 48`,
`rep 12`, `corpus 4`, `compaction 3` → `48+48+12+4+3=115`. Arms A–D × reps 3 = 12 rep rows;
4 request rows and 4 prediction rows per arm/rep; 4 corpus rows (one per arm) with an identical
`index_text` (distinct set size 1). **`fsync` per row is not verifiable from `rows.jsonl`** —
`runner.py:151 os.fsync(handle.fileno())` exists, but the file carries no durability evidence.

## 2. Discrimination — CONFIRMED

From `rep` rows only: A 3/3, B 0/3, C 3/3, **D 0/3**; `resolved_total` D = `[0,0,0]`,
`withheld_total` D = `[5,5,5]`, `final_answer` D = `'756741be'` in all three reps.
Cross-check on the 12 D `request` rows: `answer_has_fact` 0, `resolved_count` sum 0,
`withheld_count` sum 15. B also fails (0/3, 33 × `PTR_STORE_MISS`), which PREREG calls a finding,
not a failure. The index's k12 digest `756741be` is the only thing D can echo → the index does not
carry the fact.

## 3. Index — hash and bytes CONFIRMED, leak property CONFIRMED (with one caveat)

`len(index_text.encode()) = 458`; `sha256 = e81ba025cfb484a8460022dedffa8cb8e7ffe09a53b365f9b84227eb105531d5`
— both match the handoff. The text contains no `AUD-`, no `AUD-4417`, no `lumen`. Every corpus row's
`leak_check` says `items_naming_the_vendor ['k01']`, `items_carrying_the_fact_code ['k01']`,
`fact_unique_to_k01 true`, and `corpus.py` re-derived the same 12 bodies/458-byte index on a `/tmp`
copy. **Caveat: the index artefact file does not exist** — all four `run_root` values
(`/tmp/ptr-quality-{A,B,C,D}-r0-*`) are gone (`os.path.isdir` False), so the hash is over the in-row
copy of `index_text`, not over a file on disk.

## 4. PREREG vs RESULTS vs rows

Arms A/B/C/D ✓; `reps_per_arm 3` → 3 rep rows/arm ✓; `turns_per_rep 4` → 4 request rows/arm/rep ✓;
`judgement_rule` (exact case-sensitive `AUD-4417` in the final answer) → `answer_has_fact` is true in
exactly the T4 row of each A and C rep ✓; `discrimination_gate` (D answering → rebuild) never fires ✓.

Sentences the rows do not support:
- `RESULTS.md:174-176` — "The telescoping identity `sum(prompt_tokens) + 12·(R−1)` holds exactly …
  C rep2: raw **34,201** + 3×12 + completions → 49,594". Measured: C rep2 `sum(prompt_tokens) =
  32,401`, and the identity's residual is `+17,193`, so it does not hold. `34,201` is a transposition
  of `32,401`.
- `RESULTS.md:175-176` — "the difference is the completion of T1 + T2 + T3 carrying into the prefix".
  C rep2 `completion_tokens` = `[2,2,2,7]` → T1+T2+T3 = **6** tokens, against a 17,193 gap.
- `RESULTS.md:150` — "The avalanche column is empty … 0 avalanches, residues 10,11,20,37,53".
  Within the same file, `rep.per_turn` for C rep2 T4 carries `residue 1, avalanche True,
  uncached 34,190` (= 17,089 + 17,101), and `billed_tokens 49,594` is exactly that modelled bill —
  i.e. the avalanche is in the bill, not absent from it.

**Data defect in `rows.jsonl` itself:** the `request` row `residue` field equals
`templated_prompt_tokens % 64` and differs from the measured `prompt_tokens % 64` in **48/48** rows
(e.g. C rep2 T4: residue 20, but 17,089 % 64 = 1; `rep.per_turn` records 1). The per-row avalanche
flag derived from it is therefore not the avalanche of the measured prefix.

## 5. Billed-token telescoping — REFUTED; missing field named

`billed − sum(prompt_tokens)` per rep: A `+151/+110/+106`, B `+117/+150/+127`, C `+159/+111/+17,193`,
D `+100/+100/+100`. The claimed `+12·(R−1) = +36` never occurs.

`17,552 raw prefix` is not reproducible from any field: `prediction.prompt_bytes` is present
(`458 / 9,570 / 18,630`, not null), max `prompt_tokens` = 18,951 (→ ×4×2.6 = 197,090), and the
numbers the file does support are `sum(prompt_tokens)+36 = 34,275` (A rep0) and `32,437` (C rep2).

**Field missing:** server-reported per-turn cache accounting — `usage.prompt_tokens_details.cached_tokens`.
`runner.py:585-596` reads it, but no `cached_tokens` key reaches `rows.jsonl` (request rows and
`per_turn` carry only the law's modelled `uncached`). `billed_tokens_measured == billed_tokens` in
12/12 reps because `runner.py:688` defines it as `sum(t["prompt_tokens"])` — a recomputation, not a
measurement. Corroborating that the arm's own alignment guard is live: `rerun-corrected.log` records
`AssertionError: per_turn['%d'] bills P1=18794 but the row's own tokenizer count was 10902`.

## 6. Containment

No write outside `experiments/ptr-engine/quality/**` and `orchestration/{handoffs,units}/QUALITY-ARM.*`
is attributable to this unit. The 25 outside files in the 00:20–00:45 window belong to concurrent units
(`ENGINE-R1/R2`, `MISS-LAW-2`, `AVALANCHE-INSERT`, `measure/`, `experiments/miss-law/`); attribution is
by unit name, so it is circumstantial, not proof.

**Undisclosed, but in-path:** written after the 00:39 handoff and absent from `artifacts` —
`runner.py` (01:10, 37,533 B), `probe_instrument.py` (01:07), `rerun_corrected.py` (01:10),
`rows-corrected.jsonl` (01:10, 9 rows), `rerun-corrected.log` (01:10). Because `runner.py` post-dates
the rows, no sha256 ties `rows.jsonl` to the code that produced it.

## RED → GREEN — the offline discrimination gate (`quality/corpus.py`)

Guard: `corpus.py:__main__` exit gate —
`0 if report["fact_unique_to_k01"] and not report["index_has_AUD"] and not report["index_has_vendor"] else 1`.
Chosen because the whole corpus-discrimination claim (and therefore the D control) depends on it and it
needs no live request. Copy at `/tmp/vq/quality/corpus.py`, run with `PYTHONPATH` pointed at the engine.

- GREEN, unmodified copy: `GREEN_EXIT=0`, `items_naming_the_vendor ['k01']`, `fact_unique_to_k01 True`,
  `index_bytes 458`, `index_has_AUD False`.
- RED, plant `if position == 1:` → `if position >= 1:` (fact emitted for every item):
  `RED_EXIT=1`, `items_naming_the_vendor ['k01'…'k12']`,
  `items_carrying_the_fact_code ['k01'…'k12']`, `fact_unique_to_k01 False`.
- RESTORE: `RESTORED_SHA == ORIG_SHA == 9bc91d68b4dac170088045e38ae35d539178dc2af0b8c8ff4ee91b4e97fdea64`,
  `POST_RESTORE_EXIT=0`.

Verdict: **bites** (the exit code follows the planted value). No test was edited, re-pinned or deleted;
the live tree is byte-identical to before the check.

## Verdict

`partial`. Checks 1–4 (counts, discrimination, index hash/bytes/leak, prereg match) reproduce.
Check 5 is refuted, and the `residue` column cannot carry the avalanche claim it exists for.
Check 6 finds no leak but an undisclosed post-handoff rewrite of the producing runner.
