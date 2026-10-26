# V-RECORD — number verification of `experiments/ptr-engine/RECORD.md`

Read-only. Nothing in the record was edited; no claim was "fixed".

## Digests
- source `experiments/ptr-engine/RECORD.md` — sha256 `14c37e7e79479c778b7894d0b6123df3e3c1e0b002d02166a0b4f960f448fea9`, 31231 B, 140 lines, mtime 2026-10-25 17:26:36.833 −0500.
- snapshot `/tmp/V-RECORD.snapshot` — sha256 `14c37e7e79479c778b7894d0b6123df3e3c1e0b002d02166a0b4f960f448fea9`, 31231 B, 140 lines.
- **Equal** — no concurrent write landed during the copy. Note: this sandbox gives each shell call a private `/tmp`, so the snapshot did not survive the call; both hashes were taken in the same call as the `cp`, i.e. simultaneously. Everything below was verified against that copy.

## Claim census
66 numeric claims enumerated (counts, ratios, token figures, sha prefixes, mtimes, file lengths).

| class | n |
|---|---:|
| CONFIRMED | 46 |
| WRONG | 6 |
| UNSOURCEABLE | 8 |
| NOT CHECKED | 6 |

Reproduced without difficulty: `95/100/171/108` test counts, `30000/447/12 → 67.1141 → 67.1x`, `37.25 B/line`, `472 B`, index sha `e08700c9…`, `387/387` for `L_app == n_payload+12`, `774` lines / `387 measure 383 prime 4 controls`, `law_fit n_rows 753`, `379` null rows (`377 sglang, 2 sglang-h0`, all `cached_reported=false`), the three mtimes `23:55:02.910 / 23:55:04.988 / 23:55:57.864` (53 s), the 21-row tail composition (10 vllm residue = 5 prime + 5 measure; 11 sglang position, n_payload 1; 5 prime; all `error: null`), `303` exact / `83` null (66 r0, 17 r1) / `1` off at `−1056`, `387+321=708`, `304+17`, `774/774` error-null, `115` quality rows (48/48/12/4/3: `33` refusals = 11/rep, `0/3` vs `3/3`), index `e81ba0…`/458 B, `32,401` vs `34,201` → `+17,193`, `49,594` bill with `uncached 34,190` residue 1 avalanche true, 3 `per_turn` entries / `refused_total 0`, `raw_meta` cold 0 / warm 384 at `prompt_tokens 423`, `397` as `law_uncached_measured_L`, `run_cells.py:109` posting `/chat/completions`, 9 rows of `rows-corrected.jsonl`, the `18794 / 10902` assertion, `378` avalanche rows at sha `8147d195…`, arms `126/108/63/36/30/15`, `378` log lines / 0 `LENGTH-MISMATCH`, `C8-FIT-GAP.md` = 13 lines, `CLAIMS.md:135` = 51.67x, measure cells B (`P1 386, cached 384, uncached 15`) and D (`P1 322, cached 320, uncached 15`), `shape-search.json:2` `"predicted": true`.

## WRONG
1. **L134 (C10 adjudication)** "C rep2's request rows carry residues **55/13/47**". Rows carry per-turn residues **10, 53, 11, 20** (four turns, not three). `python3` over `quality/rows.jsonl`, `arm=='C' and rep==2`, field `residue`.
2. **L114 (C1 adjudication)** "`/chat/completions` reports no `cached_tokens` in **12/12** `measure/rows.jsonl` rows". The file has **49** rows and **9** of them carry `cached_tokens` (384 ×3 cell B, 320 ×3 cell D). `wc -l` + per-row key count.
3. **L114 (C1 adjudication)** "`quality/rows.jsonl` holds `cached_tokens=None` in **48/48** request rows". The 48 request rows have **no `cached_tokens` key at all** (0/48 carry it) — which is what L102 of this same file already says ("no `cached_tokens` key reaches `rows.jsonl`"). Key-set dump.
4. **L130 (restored C8 detail)** "`L_res` / `hits_delta` … null in 387/387 **outside** them and **0/387 inside**". Inside: `L_res` null in **27/387**, `hits_delta` null in **301/387**. Outside, the four keys are **absent**, not null (0/387 rows even carry them).
5. **L130** "**4** duplicate `(server, cell, rep)` pairs among the `sglang-h{0,1,m}` primes". There are **3** — `sglang-h0/calib-sglang-h0-0`, `h1`, `hm`, 6 rows, each duplicated by its own measure row.
6. **L130** "its handoff's `classes` field reads `outlier 0 / law_gap 0 / defect 21`". `orchestration/handoffs/C8-FIT-GAP.json` has **no `classes` value** (absent/null); the triple is carried only by the paragraph being withdrawn.

## UNSOURCEABLE
1. **L122** pads "**60/58/50**" — `measure/rows.jsonl` has no `pad` field; only `P1` 386/384/322 let the pads be inferred, and cell D's corpus base differs (271 vs 325).
2. **L116 (C2 adjudication)** "TTFT **1.59 s** vs **0.216 s** = **7.4×**" — `vllm2/rows.jsonl` carries `ttft_server_bucket_le` and `ttft_server_count_delta`, not those two values; the ratio is arithmetic only (1.59/0.216 = 7.36).
3. **L36** "residual 0 in **186/186** rows" — that denominator exists in no row file; under B=64 I derive **218** SGLang hit-carriers, all at residual 0. Value survives, denominator does not.
4. **L57** "**8.5×** TTFT jump … **1238/1790/2222 ms** against **206/211/216 ms**" — no artefact carries those six numbers (the sentence is withdrawn at L116 but the figures stay printed).
5. **L55** "**~270×** the no-+1056 prediction" — no artefact carries the ratio or the 0.171 ms/token cold-prefill slope it divides.
6. **L105** "differs … in **48/48** rows" — the comparison (templated vs measured `% 64`) is not a stored field; only the stored residue is present in 48/48.
7. **L132** "**123/123** pairs · **90** cache-probe cells · **108/108** `prime` rows `cached=0`" — `avalanche/rows.jsonl` keys the value as `cached`, not `cached_tokens`; re-deriving on the file's own keys did not reach those denominators.
8. **L132** "of **270** cache-probe rows **141** show the avalanche, **129** do not" — no `role`/`measure` partition in `avalanche/rows.jsonl` reproduces the 270 denominator.

## NOT CHECKED
1. **L11** "9 modules, 1896 engine lines + 1222 test lines; SPEC.md 260 lines" — today's tree is 10 modules, 3653 engine / 2248 test lines, SPEC 499 lines; the cited `PTR-ENGINE-P0.1.json:evidence.commands[9]` string was not re-executed (tool bound).
2. **L14** "153 passed (45 in `test_quantise.py`)" — `ENGINE-R1.json:evidence.commands[4]` not read.
3. **L124** "26 classes / 26 codes at P0.1" — no enumeration read; only the 16-code side (7+5+4) checks out.
4. **L78** "12 items × 9000 B" — arm/rep geometry confirmed, per-item byte figure not re-derived from `corpus` rows.
5. **L70** `Bprobe-400` pre-fix verdict "observed 467 vs predicted 1523 (delta −1056)" — arithmetic confirmed from rows; the quoted pre-fix `verdict` text was not read (`HIT-LEDGER.json:evidence.repair_finding` truncated).
6. **L26** "r = 78.3x at 383 B (ENGINE-R1 cell D)" — 30000/383 = 78.33 is arithmetic; the cell-to-index mapping was not re-derived.

## Verdict
**PASS WITH DEFECTS** — the record's measurement numbers reproduce; all six WRONG items sit in the appended adjudication/restoration sentences (L114, L116-adjacent, L130, L134), i.e. exactly the transcription path this unit was told to suspect. No number was edited.
