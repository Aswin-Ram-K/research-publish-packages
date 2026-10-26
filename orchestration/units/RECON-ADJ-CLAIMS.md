# RECON-ADJ-CLAIMS — adjudication of the 14 V-RECORD items from the data

Rows are authority, not either document. `experiments/ptr-engine/RECORD.md` re-read in place (`14c37e7e…fea9`, 140 lines); `orchestration/units/V-RECORD.md` re-read (§WRONG, §UNSOURCEABLE). Commands are `python3` one-liners over the named file; the selector and its deciding output are quoted.

## Verdicts

| item | line | verdict | deciding command → output line |
|---|---|---|---|
| 1 V-W1 | 134 | VERIFIER-CORRECT | `py` over `quality/rows.jsonl` `[r['residue'] for arm=='C', rep==2]` → `[10, 53, 11, 20]` (turns 1-4); `per_turn` → `[55, 13, 1]` (turns 2-4); 47 is A rep0 turn 4 |
| 2 V-W2 | 114 | BOTH-WRONG | `py` over `measure/rows.jsonl` `len(rows)` → `49`; `'cached_tokens' in r` → `12` rows: A 320×3 (P1 325), B 384×3 (386), D 320×3 (322), C `None`×3 (384) |
| 3 V-W3 | 114 | VERIFIER-CORRECT | `py` keyset of the 48 request rows → no `cached_tokens` key; `sum('cached_tokens' in r)` → `0` |
| 4 V-W4 | 130 | BOTH-WRONG | `py` split on `L_app is not None` → `387/387`; key present outside → `0`; inside `L_res` null → `27`, `hits_delta` null → `290` (+11 absent) |
| 5 V-W5 | 130 | VERIFIER-CORRECT | `py` `Counter((server,cell,rep))` over the 6 `sglang-h*` rows → `3` tuples ×2 (all rep 0, `phase=calib`) |
| 6 V-W6 | 130 | RECORD-CORRECT | `py` `C8-FIT-GAP.json:/evidence/classes` → `{"outlier": 0, "law_gap": 0, "defect": 21}` |
| 7 U1 | 122 | RECORD-CORRECT | `py` `measure/rows.jsonl:pad_tokens`, cell B/C/D measure rows → `[60] [58] [50]`, 3 reps each |
| 8 U2 | 116 | RECORD-CORRECT | `py` `vllm2/rows.jsonl:ttft_server_s` → `1.585238` (P1 6336 `prime`), `0.216728` (P1 8450 `measure`, res 2) |
| 9 U3 | 36 | RECORD-CORRECT | `py` grep of `MISS-LAW.json` → `residual 0 in 186/186 rows over residues 2..63 x 3 reps` (= 62×3) |
| 10 U4 | 57 | RECORD-CORRECT | `py` grep of `MISS-LAW-2.json` → `TTFT 1238/1241, 1790/1790, 2222/2223 ms vs 206/211/216 ms … an 8.5x TTFT jump` |
| 11 U5 | 55 | RECORD-CORRECT | `py` grep of `MISS-LAW-2.json` → `cold-prefill slope of 0.171 ms/token`, `excluded by ~270x` |
| 12 U6 | 105 | RECORD-CORRECT | `py` `quality/rows.jsonl` both fields stored → `templated%64 != prompt%64` in `48` of `48` |
| 13 U7 | 132 | RECORD-CORRECT | `py` `avalanche/rows.jsonl` → `len({pair_id})` `123`; `role=='prime'` `108`, all `cached==0`; `270/3` → `90` cells |
| 14 U8 | 132 | RECORD-CORRECT | `py` `role!='prime'` → `270` rows → `cached>0` `141`, `cached==0` `129`; `HARVEST.md` prints `270 / 141 / 129` |

Tally: RECORD-CORRECT **9** · VERIFIER-CORRECT **3** (1, 3, 5) · BOTH-WRONG **2** (2, 4) · UNDECIDABLE **0**.
Two verifier numbers are imprecise where its verdict is right: item 4's `hits_delta 301` folds 11 absent rows into "null" (strict null 290); item 5's count 3 is right but "each duplicated by its own measure row" is wrong — all six rows are `phase=calib`, two probes per cell.

## Fix clauses

**L134 (item 1)**
current: `carry residues 55/13/47`
corrected: `carry residues 10/53/11/20 on turns 1-4`

**L114 (item 2)**
current: `and no second instrument exists in the record — `/chat/completions` reports no `cached_tokens` in 12/12 `measure/rows.jsonl` rows`
corrected: `and the one second instrument on this path reports warm values in 9/12 `measure/rows.jsonl` rows — 384 ×3 cell B, 320 ×3 cell A, 320 ×3 cell D — and null only at cell C (residue 0)`

**L114 (item 3)**
current: `` `quality/rows.jsonl` holds `cached_tokens=None` in 48/48 request rows ``
corrected: `` `quality/rows.jsonl`'s 48 request rows carry no `cached_tokens` key at all ``

**L130 (item 4, opening sentence)**
current: `` `prev_prompt_tokens` / `L_app` / `L_res` / `hits_delta` are null in **387/387** of them and **0/387** inside ``
corrected: `` `prev_prompt_tokens` / `L_app` / `L_res` / `hits_delta` are absent from **387/387** of them (no key, not null) while inside `L_res` is null in **27/387** and `hits_delta` in **290/387** (+11 absent) ``

**L130 (item 4, tail restatement)**
current: `` `prev_prompt_tokens` / `L_app` / `L_res` / `hits_delta` null in exactly the 387 outside the fit ``
corrected: `` `prev_prompt_tokens` / `L_app` / `L_res` / `hits_delta` absent from exactly the 387 outside the fit ``

**L130 (item 5)**
current: `` **4** duplicate `(server, cell, rep)` pairs among the `sglang-h{0,1,m}` primes ``
corrected: `` **3** duplicate `(server, cell, rep)` pairs among the six `sglang-h{0,1,m}` `calib` rows (2 per cell, all rep 0) ``

## C1 premise

`measure/rows.jsonl` = 49 rows; 12 carry `cached_tokens`; `server` and `role` are null in all 12, `phase=measure`, `token_source` `http://192.168.2.168:8012/v1`.

| cell | reps | P1 | residue | cached_tokens | cached_reported | uncached_tokens | pad_tokens |
|---|---:|---:|---:|---:|---|---:|---:|
| A | 0,1,2 | 325 | 5 | 320 | true | 18 | 0 |
| B | 0,1,2 | 386 | 2 | 384 | true | 15 | 60 |
| C | 0,1,2 | 384 | 0 | null | false | 397 | 58 |
| D | 0,1,2 | 322 | 2 | 320 | true | 15 | 50 |

The endpoint **does** report a warm-prefix `cached_tokens` on the path these rows were taken from: 9/12 rows are server numbers with `cached_reported: true`, and in each `cached = P1 − residue`, `uncached = L` (15 or 18) — the prefix was billed as cached, not re-billed.
- **C1's "no second instrument exists" is contradicted**: the sentence it rests on is false as written, in the very rows it cites.
- **C2's "no row shows a warm prefix re-billed" is supported** by these rows: the only full-prompt bill is cell C at residue 0, where `cached_tokens` is null and `cached_reported: false`, so its `397` is the engine's null-read-as-0 law value, not a reported re-bill. No numeric row re-bills a prefix.
- Not chosen, but on disk: `vllm2/rows.jsonl` carries numeric `cached_tokens=0` on `measure` rows at P1 6336/6337/7392/7393 with `unc = P1 + L`; warmth there is a protocol reading (`round` 0 `prime` → `round` 1 `measure`), not a stored flag.

## Duplicate pairs

Definition as L130 uses it: rows sharing one `(server, cell, rep)` value among the `sglang-h{0,1,m}` rows. Measured: 6 such rows, **3** distinct values — `calib-sglang-h0-0`, `calib-sglang-h1-1`, `calib-sglang-hm-32` — each twice, all `rep 0`, all `phase=calib`, differing only in `H_res` (53 vs 0/1/32) and `cached_tokens` (null vs 8000/7360). So the sentence's **4 is wrong and 3 is right**, but they are not "primes" (no `phase=prime` row exists here) and no measure row duplicates them.

## Not decidable

None. All 14 resolved. Two quantities are reached indirectly, not literally: L122's pads (field is `pad_tokens`, not `pad`) and L132's "90 cells" (270 probes ÷ 3 reps; no stored cell key).
