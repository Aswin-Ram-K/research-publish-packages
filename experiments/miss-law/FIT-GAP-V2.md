# C8 — Contradiction re-derivation (FIT-GAP-V2)

Self-sourced from `experiments/miss-law/rows.jsonl` alone (774 JSON rows). No verdict, handoff or
`C8-FIT-GAP.md` was read before deriving. Grid: 64 for `server` starting `sglang`, 1056 for `vllm`.
`floor = prompt_tokens // grid * grid`; `residual = cached_tokens - floor`.

## 1. Fit set

- 387 rows carry a non-null `L_app`. Predicate: `[r for r in rows if r.get('L_app') is not None]`.
  Note `L_app` is **absent** (not null) on the other 387 rows, so `Counter` counts 387 keys of 774.
- `role` composition: `{'measure': 387}` — 100 %, no mixing. Predicate: `Counter(r['role'] for r in fit)`.
- Of those 387, **304** carry `cached_tokens`, **83** do not. Predicates:
  `sum(1 for r in fit if r['cached_tokens'] is not None)` → 304; the complement → 83.
- The fit set is *exactly* the `meas()` selection: `sum(1 for r in fit if not (r['role']=='measure' and not r['error']))` → **0**.
- Server split: `sglang` 301, `vllm` 86 (`Counter(r['server'] for r in fit)`).

## 2. Residual distribution (fit rows with a cached value, n=304)

| residual | all | sglang | vllm |
|---|---|---|---|
| 0 | 160 | 159 | 1 |
| −64 | 51 | 51 | 0 |
| −128 | 6 | 6 | 0 |
| −192 | 2 | 2 | 0 |
| −1056 | 69 | 0 | 69 |
| −2112 | 16 | 0 | 16 |

Command: `Counter(r['cached_tokens'] - (r['prompt_tokens']//grid(r['server'])*grid(r['server'])) for r in fit if r['cached_tokens'] is not None)`,
split by `if r['server']=='sglang'` / `=='vllm'`. **No positive residual exists** (n = 0).

## 3. The 144 non-zero residuals

`sum(1 for r in fit_cached if residual(r) != 0)` → **144**, in exactly three groups:

- `vllm` / phase `residue` — **78**. Cells `res-7000|7050|8055|8056-n{1,64,512,1056}`, `n_payload` 1 (n1), 64, 512, 1056; residual −1056 (n1, n64) and −2112 (n512, n1056). 3 reps for n1, 2 for the rest.
- `sglang` / phase `residue` — **59**. Cells `res-8005|8037|8051..8063|--n{1,16,32,64,128}` around prompt 8064–8203, where `prompt > 8000`; residual −64/−128/−192 = one, two, three 64-blocks.
- `vllm` / phase `B` — **7**. Cells `Bprobe-1300..6700`, `n_payload` 2, rep 0; residual −1056 each (cached 0/1056/…, the discovery probes).

Whole-multiple question, computed not assumed:
`{residual(r) % grid(r['server']) for r in fit_cached if residual(r) != 0}` → **{0}**. Every deviation is
a whole number of block sizes (1–3 on sglang, 1–2 on vllm). Sign is always negative: `cached_tokens` never
exceeds `floor(prompt)`; the server under-reports, it never over-reports.

## 4. Fit rows with null `cached_tokens` (n = 83)

- Phase: `grid` 50, `residue` 22, `position` 11 (`Counter(r['phase'] for r in fit if r['cached_tokens'] is None)`).
- Cell naming: `grid-h0-n*` (h0 = zero history, 3 reps per n), plus `res-*` / `pos-*` h0 cells. Server: **sglang only**, all with `cached_reported == False`.
- Their `uncached_tokens` equals **`prompt_tokens` exactly**: `sum(1 for r in N if r['uncached_tokens']==r['prompt_tokens'])` → **83 / 83**.
- Plain law `uncached == residue + L_app`: `sum(1 for r in F if r['uncached_tokens'] == r['prompt_tokens'] % grid(r['server']) + r['L_app'])` → **0 holds, 387 violations** over the whole fit set (83/83 among the null rows). Structural, not random: with no reusable prefix at all, nothing is cached, so `uncached` is the full prompt — the law has no `h0`/no-hit term. The only identity that holds is `uncached == prompt − cached` (304/304 on rows with a value, 83/83 with `cached = 0`).

## 5. Row-level integrity

- Duplicate `(server, cell, rep)`: 381 keys with >1 row, 381 extra rows — but **all are prime↔measure pairs** (376 keys), plus 3 prime-only, 1 `warm1`/`warm2`, 1 `cold1`/`cold2`. Adding `role` to the key leaves only **3** collisions, so the 3-tuple alone is not a unique key; `(server, cell, rep, role)` almost is.
- `error` non-null: **0** of 774 (`sum(1 for r in rows if r['error'])`).
- `prompt_tokens` below the grid size: **2** rows, both `vllm` `Bprobe-400` (`prime` 453, and `measure` 467 with `L_app = 14`) against grid 1056. The measure row is inside the fit set and makes `floor = 0`, so its residual is −1056 in group 3's `B` bucket.

## 6. VERDICT on the old classification

- `outlier 0` — **REPRODUCED**. Predicate `sum(1 for r in fit_cached if residual(r) > 0)` → 0. A positive residual (cache claiming more than the block floor allows) never occurs.
- `law_gap 387` — **REPRODUCED as a count, but it is not a law gap.** Predicate: complement of `meas()` over all rows, `sum(1 for r in rows if not (r['role']=='measure' and not r['error']))` → **387**. That is simply the prime/warm/cold rows. Applied inside the fit set the same complement is **0**. 387 is also the fit-set size and the `L_app`-absent count — three different sets that happen to be 387 in this file. The number is right, the name is a collision.
- `defect 321` — **NOT REPRODUCIBLE**. Tried, against all 774 and against the 387 fit rows: `role=='measure'` (387), `L_app is None` (387), `prev_prompt_tokens is None` (387), `cached_tokens is None` (379), `not cached_reported` (379), `uncached==prompt` (467), `phase=='residue'` (620), `phase=='residue' and cached` (366), `fit and L_res is not None` (360), `fit and L_res != residue` (299), `fit and cached%grid==0` (304), `fit and residual==0` (160), `fit and residual!=0` (144), `residual>0` (0), all 1- and 2-way AND combinations of {measure, L_app/null, cached/null, prev, 4 phases, server, L_res, residual sign, L_res==residue, uncached==prompt, B_measured, H_res} → none yields 321. Alternate residual bases (`cached − floor(prev_prompt)`, `cached − prompt`) give 85 and 304/395. **No predicate tried produces 321.**

## What this replaces

**Survives:** the fit-set size 387 and its single-role composition; the residual table (§2), including zero positive residuals (`outlier 0`); the count 387 itself as the size of the non-`meas()` population.
**Withdrawn:** `defect 321` — no predicate reproduces it, so it must not be cited; and the reading of `law_gap 387` as rows where a law fails, since the same 387 are simply the non-measure rows (0 law-failures are excluded from the fit set by `meas()`).
**Remains UNREPRODUCIBLE:** `defect 321` in full (count, scope and predicate), and therefore any `outlier 0 · law_gap 387 · defect 321` partition reaching 708 of 774 rows — this file supports no such partition. What is reproducible is a 144-row deviation population (85 vllm, 59 sglang), all negative whole-block multiples, plus an 83-row no-hit population where the plain law's fourth term is missing.

## 7. Disjoint partition of all 774 rows

Every one of the 774 rows in `experiments/miss-law/rows.jsonl` lands in exactly one class below. The residual is
this file's own definition (§2): `residual(r) = r['cached_tokens'] − (r['prompt_tokens'] // grid) * grid`, grid 64
`sglang` / 1056 `vllm`. `L_app` is **absent**, not null, on the non-fit rows, so the fit test is
`r.get('L_app') is not None` — comparing it to `None` with `[]` access raises `KeyError` on those rows.

| # | class | predicate | rows | sglang | vllm |
|---|---|---|---:|---:|---:|
| 1 | no `L_app` — prime/warm/cold | `r.get('L_app') is None` (prime 383, warm1 1, warm2 1, cold1 1, cold2 1) | **387** | 295 | 86 |
| 2 | fit row, cache not reported | `r.get('L_app') is not None and r['cached_tokens'] is None` | **83** | 83 | 0 |
| 3 | fit row, reported, residual 0 | `… and r['cached_tokens'] is not None and residual(r) == 0` | **160** | 159 | 1 |
| 4 | fit row, reported, residual ≠ 0 | `… and residual(r) != 0` | **144** | 59 | 85 |
| | **sum** | | **774** | **596** | **172** |

**Sum proof.** `387 + 83 + 160 + 144 = 774` = `wc -l rows.jsonl`.
Independently over the columns: `sglang 295+83+159+59 = 596`, `vllm 86+0+1+85 = 172`,
and `596 + 172 = 768` (plus 6 rows under other `server` labels). **Disjointness** is structural, not argued: class 1 is the complement of the fit set
inside all rows; class 2 the complement of "cache reported" inside the fit set; classes 3 and 4 are the two signs of
one comparison (`residual(r) == 0` vs `!= 0`) over the same reported set. So `83 + 160 + 144 = 387`
is the fit set (§1) and `160 + 144 = 304` is its reported subset (§2).

**Class 4 in full** — every residual value, all negative whole-grid multiples:
`-2112` ×16, `-1056` ×69, `-192` ×2, `-128` ×6, `-64` ×51. By phase: vllm `residue` 78, sglang `residue` 59, vllm `B` 7 —
the same 144 and the same groups as §3, now located inside a partition that closes.

### Identities per class

`A` = `uncached_tokens == prompt_tokens − cached_tokens` (the plain cache identity, with `cached = 0` when the
report is null); `P` = `uncached_tokens == (prompt_tokens % grid) + L_app` (the plain law, no no-hit term).

| class | rows | `A` holds | `P` holds |
|---|---:|---:|---:|
| 1 no `L_app` | 387 | **387/387** (296 have no cache report → `uncached == prompt` exactly; 91 report one and satisfy `A`) | **0/387** (undefined — no `L_app`) |
| 2 null cache | 83 | **83/83** — `uncached == prompt` in **83/83** | **0/83** |
| 3 residual 0 | 160 | **160/160** | **0/160** |
| 4 residual ≠ 0 | 144 | **144/144** | **0/144** |

**The record's two identity claims, checked against rows.** (i) "**0 of 387** holds the plain form `uncached == residue + L_app`"
— **CONFIRMED**: `sum(1 for r in fit if P(r))` = **0 holds, 387 violations**. The reason is the one §4 gives: on the 83
null-cache rows `uncached == prompt` exactly, so the law is missing a no-hit term, and on the 304 reported rows
`uncached = prompt − cached`, not `prompt mod grid + L_app`. (ii) The only identity that holds is `A` —
**304/304** on reported rows and 83/83 on null rows (`cached = 0`). What the partition adds is that `P` fails on
**all four classes** including the residual-0 one, so the failure is not a property of the deviating rows alone.
**Convention note (so this is not re-derived as a contradiction):** on the uncached side, the law
`uncached == (prev_prompt_tokens mod grid) + L_app` needs one extra whole block on `vllm`; that form holds
**304/304** of the reported rows and misses exactly the 83 no-hit rows. A count of 85/219 belongs to that
uncached-side convention, not to §2/§3's cache-side residual, which is the 144 used here.

**What this closes and what it leaves open.** It closes the **arithmetic** the withdrawn C8 bookkeeping reading left
behind: the old `387 + 321 = 708` cannot be a partition of 774 because it omits 66 rows, whereas
`387 + 83 + 160 + 144 = 774` assigns every row once under a stated predicate, so a reviewer can no
longer ask how the classes reach only 708. It leaves **`defect 321` itself** open — §6 shows no predicate on this
file reproduces 321, so the old class still has no recoverable meaning, and this section does not invent one.

Command for the whole section: `python3 -c` over `rows.jsonl` with `residual(r) = r['cached_tokens'] - (r['prompt_tokens']//grid(r['server']))*grid(r['server'])`,
`grid = 64 if r['server']=='sglang' else 1056`, partitioned on `r.get('L_app') is None` and `r['cached_tokens'] is None`.
