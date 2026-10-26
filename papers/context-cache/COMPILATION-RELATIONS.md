# COMPILATION-RELATIONS — how the findings in `COMPILATION.md` stand to one another

**Purpose.** Which finding rests on which, which contradict, and which are the same measurement read
two ways. One relation per line: `A -> B` = B depends on A (B is unsound if A is withdrawn);
`A contradicts B` = both cannot be printed as stated; `A == B` = the same measurement, two readings.
Sources are `file:line` or a claim id in `papers/context-cache/COMPILATION.md`. Rebuildable by
reading the index; nothing here is new measurement.

## 1. The append-cost law and the residual partition (C8)

- `RECORD.md:36` SGLang law `uncached = (P1 mod 64) + L` -> `C77` (warm cells bill `residue + L`); source `RECORD.md:36-38`, `FOLD-PROPOSAL.md:58`.
- `RECORD.md:37` vLLM law `uncached = (P1 mod 1056) + 1056 + L` -> `C63` (the engine axis is a block-geometry axis); source `RECORD.md:37`, `CLAIMS.md:229`.
- `C76` (`L = n_payload + 12`, 387/387) -> `RECORD.md:36-37` both laws, because both carry the residue **plus** `L`; source `RECORD.md:38`.
- `C8` residual partition -> `C37` (repeats: 44/44 residual 0) and `C38` (appends: 372/372 nonzero); the partition is the mechanism behind both; source `RECORD.md:128-130`, `CLAIMS.md:143-144`.
- `C37` == `C76` on the append's own framing: the 12 framing tokens are why the append's residual is `residue + L` and not `residue`; source `RECORD.md:38`, `FOLD-PROPOSAL.md:57`.
- `C8` residual detail contradicts `C8` closure narrative — the "303 exact" count recomputed to 160 strictly-zero, 60 whole-block shortfalls unmentioned; source `RECORD.md:138`. Both rows kept; the closure sentence is the withdrawn half (`W11`).
- `W11` (321 partition) -> unrecoverable: no on-disk predicate yields 321, so any relation that routes through it is dead; source `RECORD.md:138`, `GAPS-INVENTORY.md:53`.
- `C8` -> `C40`/`C41`/`C42` (boundary miss at `L mod 64 == 0`): the residue term is what predicts a miss at residue 0; source `RECORD.md:57`, `CLAIMS.md:146-148`.
- `C62` contradicts `C38` **as worded** — 372/372 deviation was measured on 931-12,393-token histories while `C77`'s 322-386-token appends follow the grid exactly; source `FOLD-PROPOSAL.md:76`, `GAPS-INVENTORY.md:47`.

## 2. Discrimination and the refuted billing identity (RECORD's C3/C10)

- `C78` discrimination control (D 0/3, 0 bodies resolved, digest echoed off the index) -> `C78`'s other three arms (A/C 3/3, B 0/3), because without D the other arms measure nothing; source `RECORD.md:87`, `FOLD-PROPOSAL.md:60`.
- `C78` -> capability only: it licenses no token figure; source `RECORD.md:108-110`.
- the billing identity `sum(prompt_tokens) + 12(R-1)` contradicts the stored 32,401 (claimed 34,201, residual +17,193) — `W03`; source `RECORD.md:134`.
- `W03` -> `W05` (quality-arm token columns void): the identity is the arm's own cost model, so its refutation voids every figure built on it; source `RECORD.md:118`, `RECORD.md:134`.
- `W04` (49,594 is the modelled avalanche bill, not a measurement) -> `W03`, same `per_turn` field that contradicts the identity; source `RECORD.md:134`.
- `C78` == capability survives `W05`: task success and the 33 named refusals are read from `RESOLUTION-CODES`, not from the void cost column; source `RECORD.md:108`.
- `W06` (57.6x understatement) -> `W05`: same root cause (`L = prompt_tokens + FRAMING`), never independently re-derived; source `RECORD.md:118`.

## 3. The 8.5x TTFT pair and the law's residue term

- the law's residue term (`RECORD.md:36`) -> the 8.5x penalty: at residue 0 the warm prefix is re-billed whole, which is the residue term evaluated at its worst point; source `RECORD.md:145`.
- 8.5x pair (`P1 7392` residue 0, TTFT 1.790/1.792 s vs `P1 7394` residue 2, 0.2108/0.2114 s, cell G6) -> `L02`; it is the entire evidence for the vLLM avalanche magnitude; source `RECORD.md:145`, `GAPS-INVENTORY.md:23`.
- `W08` (7.4x cold-prime vs warm-measure) contradicts the 8.5x pair **as evidence**, not as value: the 7.4x is a role mismatch across different lengths; source `RECORD.md:145`.
- 8.5x -> `W01` is unaffected: SGLang's residue-0 case is still undecided (`L01`), and the vLLM measurement cannot be transplanted because the block sizes differ (1,056 vs 64); source `RECORD.md:114`, `RECORD.md:57`.
- `L02` -> `C63`: a second residue would harden the vLLM block-geometry reading but is not required for the 2x2, which is measured over 71 turns; source `CLAIMS.md:229`, `GAPS-INVENTORY.md:23`.

## 4. Fan-out, effect sizes and their supersessions

- `C04` -> `C05`: the 3.3133 is computed from U4b's arm totals; source `CLAIMS.md:86-87`.
- `C53` supersedes `C05` as the effect size (6.744 vs 3.3133); `C05` stays as that cell's measured value; source `CLAIMS.md:87`, `CLAIMS.md:185`.
- `C06` -> `C53`: the counterfactual 5.3922 is only interpretable as a floor against G5's 6.744; source `CLAIMS.md:88`.
- `C21`'s causal reading is superseded by `C44` (E/F = 1.038 per-break, not 1.700x); the arithmetic stands, the mechanism moves to post-compaction window truncation; source `CLAIMS.md:281`, `CLAIMS.md:150`.
- `C22` == `C44`: the 92.2% steady-state share and the 1.038 per-break ratio are the same decomposition read two ways; source `CLAIMS.md:290-291`.
- `C24` -> `C22`: the break-only counterfactual is the 7.8% half expressed as a multiple; both superseded for break cost by `C44`; source `CLAIMS.md:292`.
- `C25` -> `C21`: the unbounded window is why A still wins despite never shrinking; source `CLAIMS.md:117`, `CLAIMS.md:121`.
- `C26` -> `C44`: break events at turns 18 and 35 are the six events G1 decomposes; source `CLAIMS.md:122`, `CLAIMS.md:150`.

## 5. Grid, cross-stack and the engine axis

- `C37` -> `C55`: the per-stack unit (gcd of hot `cached_tokens`) is the same grid statement at a different scope; source `CLAIMS.md:143`, `CLAIMS.md:196`.
- `C55` == `C49`: both read grid units from the same WIN-VLLM rows, once per config and once per stack; source `CLAIMS.md:181`, `CLAIMS.md:196`.
- `C56` -> `C55`: identification (1,056 does not divide V1) is what makes the unit measured rather than fitted; source `CLAIMS.md:197`.
- `C61` -> every grid claim: the guard is what keeps `C45`-`C60` from resting on an empty config; source `CLAIMS.md:202`.
- `C63` == `C65`: the same 2x2, once through `recompute.py` and once through `recompute_r2.py` without it; agreement is the point; source `CLAIMS.md:229`, `CLAIMS.md:265`.
- `C63` contradicts its own superseded block (engine 1,225.18, model +275.83) — the MTP correction replaces it; the superseded values are printed for traceability only; source `CLAIMS.md:239`.
- `C67` -> `C69`: O4's measured cost of the P1 form is the ceiling the version round tests against; source `CLAIMS.md:267`, `CLAIMS.md:269`.
- `C64` -> `C67`: the withdrawn padding win and the prompt-layout round are the same question (does alignment pay), answered twice; source `CLAIMS.md:264`, `CLAIMS.md:267`.
- `C68` -> `C67`: four distinct configurations is what licenses reading the layout round as four setups rather than one repeated; source `CLAIMS.md:268`.

## 6. The fold's five drafted claims and C80/C81

- `C75` -> `V-ENGINE-P0.json` checks[3] (determinism) and checks[4] (r recomputed); `X01` carries the digest half that `C75` prints as a byte count; source `FOLD-PROPOSAL.md:64`.
- `C76` -> `experiments/miss-law/rows.jsonl` (387/387, `L_app == n_payload + 12`); source `FOLD-PROPOSAL.md:65`.
- `C77` -> `experiments/ptr-engine/measure/rows.jsonl` (warm cells A/B/D 18/15/15 at residues 5/2/2); source `FOLD-PROPOSAL.md:66`.
- `C78` -> `experiments/ptr-engine/quality/rows.jsonl`, re-derived by `V-QUALITY-ARM.json` checks[1]; `C78` is the only fold claim that is `VERIFIED-OFFLINE`; source `FOLD-PROPOSAL.md:67`.
- `C79` -> `experiments/ptr-engine/tests/` (190 passed); `C80` -> `tests/test_negative_controls.py:104-114`; `C81` -> `V-ENGINE-P0.json` checks[7] (`PTR_WARMPOOL_INSIDE_REPO`); source `FOLD-PROPOSAL.md:68-70`.
- `C75` contradicts the universal reading of `r`: it is one corpus at the crossover, so `C75` does not imply a curve (`W07` is the discarded second point); source `FOLD-PROPOSAL.md:26`, `GAPS-INVENTORY.md:17`.
- `C77` -> `C76`: the warm-cell identity `uncached = residue + L` needs `L = n_payload + 12` to be a number; source `RECORD.md:38`, `FOLD-PROPOSAL.md:57-58`.
- `C80`/`C81` -> `O01`: both are drafted in `FOLD-PROPOSAL.md` only, so they cannot enter `CLAIMS.md` without the operator's ratification; source `GAPS-INVENTORY.md:19`, `GAPS-INVENTORY.md:48`.

## 7. Non-relations worth stating

- `C34`'s 51.67x latency ratio is **not** the pointer engine's `r`; the two numbers are neighbours in
  `CLAIMS.md:135` and `RECORD.md:136` and must never be cited as one; source `RECORD.md:136`.
- `C01`/`C16` are recomputed by the verifier's own scripts, not by `recompute.py`; they are
  `VERIFIED-OFFLINE` where the other claims are `RE-DERIVED` — same file, different instrument; source `CLAIMS.md:18-19`.
- `C40`'s n = 5 per length (`L03`-adjacent) means the 64-grid boundary rule has no power, while `C41`'s
  Fisher test is on the pooled pool; the two rows are consistent but the second is the stronger
  statement; source `GAPS-INVENTORY.md:27`, `CLAIMS.md:147`.

<!-- rows-relations:begin -->
## 8. The 2026-10-26 row files, and what they make citable
Generated by `build_compilation.py` from the same rows that fill section P of `COMPILATION.md`; every figure below is recomputed on each run, so a stale relation cannot outlive the rows it reads. `A -> B` keeps its meaning: B depends on A. Every group is printed whole — no row is selected as representative — so a reader can redo each arithmetic step from the group it names.
### 8.1 LIVE-CELLS-2 — C1, C2, C5 and the null semantics
| cell | role | rows | residue | prompt | cached | uncached | source |
|---|---|---:|---|---|---|---|---|
| `A` | `measure` | 7 | 13 | 0–397 | 320 (+1 null→0) | 0–77 | `rows-live-2026-10-26.jsonl`: `prompt_tokens`, `cached_tokens`, `residue` |
| `A` | `prime` | 7 | 0–1 | 365–385 | — (+7 null→0) | 365–385 | `rows-live-2026-10-26.jsonl`: `prompt_tokens`, `cached_tokens`, `residue` |
| `A` | `same` | 3 | 0 | 384 | — (+3 null→0) | 384 | `rows-live-2026-10-26.jsonl`: `prompt_tokens`, `cached_tokens`, `residue` |
| `B` | `measure` | 4 | 4 | 0–260 | 256 (+2 null→0) | 0–260 | `rows-live-2026-10-26.jsonl`: `prompt_tokens`, `cached_tokens`, `residue` |
| `C` | `append` | 2 | 14 | 7,406 | 0 | 7,406 | `rows-live-2026-10-26.jsonl`: `prompt_tokens`, `cached_tokens`, `residue` |
| `C` | `prime` | 2 | 1 | 7,393 | 0 | 7,393 | `rows-live-2026-10-26.jsonl`: `prompt_tokens`, `cached_tokens`, `residue` |
| `C` | `same` | 2 | 1 | 7,393 | 6,336 | 1,057 | `rows-live-2026-10-26.jsonl`: `prompt_tokens`, `cached_tokens`, `residue` |

- `rows-live-2026-10-26.jsonl` -> `C1` (the warm cell whose cached prefix ends on a 64-token block boundary): cell `A` has 6 reporting row(s) that cache, each reporting cached 320 and billing 58–77 uncached of a 378–397-token prompt; cached is an exact multiple of the 64-token block unit named in `C55`; `residue` 13 on those rows — those rows reuse the prefix instead of re-billing it. Also, 11 row(s) in this cell carry a null counter (0 under the settled semantics). Source `rows-live-2026-10-26.jsonl`: `cached_tokens`, `prompt_tokens`, `residue`, `cell`, `role`.
- `rows-live-2026-10-26.jsonl` -> `C5` (the compact UNPADDED cell): cell `B` has 2 reporting row(s) that cache, each reporting cached 256 and billing 4 uncached of a 260-token prompt; cached is an exact multiple of the 64-token block unit named in `C55`; `residue` 4 on those rows; `index_form` `compact` with `padding` `none`, `index_bytes` 383, `index_lines` 12; on every reporting row `prompt_tokens − cached_tokens` equals the recorded `residue` — those rows reuse the prefix instead of re-billing it. Also, 2 row(s) in this cell carry a null counter (0 under the settled semantics). Source `rows-live-2026-10-26.jsonl`: `cached_tokens`, `prompt_tokens`, `residue`, `cell`, `role`.
- `rows-live-2026-10-26.jsonl` -> `C2` (the warm re-send at residue 1): cell `C` has 2 reporting row(s) that cache, each reporting cached 6,336 and billing 1,057 uncached of a 7,393-token prompt; cached is an exact multiple of the 1,056-token block unit named in `C55`; `residue` 1 on those rows — those rows reuse the prefix instead of re-billing it. 4 row(s) report cached 0 and bill the whole 7,393–7,406. Source `rows-live-2026-10-26.jsonl`: `cached_tokens`, `prompt_tokens`, `residue`, `cell`, `role`.
- `rows-live-2026-10-26.jsonl` -> `L01`, `L02`, `L03`: the row each queue entry called for now exists in this file (an SGLang residue-0 warm cell, a vLLM residue-1 warm same-row, and a compact UNPADDED cell). Those index rows keep `BLOCKED-LIVE` **on purpose**: a status is derived from `CLAIMS.md` and the row's `[live]` marker, never from a row file, so releasing them is an editorial act on the claim row. Source `rows-live-2026-10-26.jsonl`: `cell`, `role`, `residue`; `COMPILATION.md` section M.
- `rows-live-2026-10-26.jsonl` -> every relation that reads `cached_tokens`: 13 of 27 rows carry a null, and a null is a measured **0** under the settled endpoint rule — those rows stay citable as `cached = 0`, never as "unknown". Source `rows-live-2026-10-26.jsonl`: `cached_tokens`, `cached_reported`, `cached_source`.
- `rows-live-2026-10-26.jsonl` **self-limitation**: 2 of 27 rows carry a non-empty `error`, so any count taken over the file must exclude them rather than treat them as zeros. Source `rows-live-2026-10-26.jsonl`: `error`.

### 8.2 C0-EQUALINFO — the equal-information result
**`occamy-1.0-NVFP4`** on `http://192.168.2.168:8012/v1/chat/completions` — 46 of 48 rows report a cache counter.
- `rows-equalinfo-2026-10-26.jsonl` -> `C67` (the pointer index is null against full history): at 12 item(s) in context `C0F` costs **1,911** uncached per turn-rep while `R` costs **3,524**, so `R` bills 1.844x the plain transcript. Source `rows-equalinfo-2026-10-26.jsonl`: `prompt_tokens`, `cached_tokens`, `arm`, `turn`, `rep`, `items_in_context`.
- `rows-equalinfo-2026-10-26.jsonl` -> `C67` (the pointer index is null against full history): at 12 item(s) in context `C0FT` costs **46** uncached per turn-rep while `R` costs **3,524**, so `R` bills 75.514x the plain transcript. Source `rows-equalinfo-2026-10-26.jsonl`: `prompt_tokens`, `cached_tokens`, `arm`, `turn`, `rep`, `items_in_context`.
- `rows-equalinfo-2026-10-26.jsonl` -> `C75` / `C76`: the pointer protocol pays more on every plain arm (1.844x–75.514x), so this measurement **contradicts** the token-saving reading of `C75`/`C76`: the compact index's win is a byte ratio (`r`), and it does not reach the per-turn bill at this item count. Source `rows-equalinfo-2026-10-26.jsonl`: `prompt_tokens`, `cached_tokens`, `arm`.
- `rows-equalinfo-2026-10-26.jsonl` -> `C08` (no accuracy delta): the plain cell `C0F` answers 3 row(s) correctly against 3 for `R` — the arithmetic above is a cost difference, and this count is the only quality statement the file supports. Source `rows-equalinfo-2026-10-26.jsonl`: `answer_correct`.
**`qwen3.5-9b`** on `http://192.168.2.168:8014/v1/chat/completions` — 0 of 52 rows report a cache counter.
- `rows-equalinfo-2026-10-26.jsonl` -> `C67` (the pointer index is null against full history): at 12 item(s) in context `C0F` costs **28,219** uncached per turn-rep while `R` costs **4,821**, so `R` bills 0.171x the plain transcript. Source `rows-equalinfo-2026-10-26.jsonl`: `prompt_tokens`, `cached_tokens`, `arm`, `turn`, `rep`, `items_in_context`.
- `rows-equalinfo-2026-10-26.jsonl` -> `C67` (the pointer index is null against full history): at 12 item(s) in context `C0FT` costs **22,626** uncached per turn-rep while `R` costs **4,821**, so `R` bills 0.213x the plain transcript. Source `rows-equalinfo-2026-10-26.jsonl`: `prompt_tokens`, `cached_tokens`, `arm`, `turn`, `rep`, `items_in_context`.
- `rows-equalinfo-2026-10-26.jsonl` -> `C75` / `C76`: the pointer protocol pays less on every plain arm (0.171x–0.213x), so this measurement **does not contradict** `C75`/`C76` — but it also cannot confirm them, because the arms are compared on gross prompt tokens only. Source `rows-equalinfo-2026-10-26.jsonl`: `prompt_tokens`, `cached_tokens`, `arm`.
- **Bound on every figure above for `qwen3.5-9b`**: none of this model's 52 rows report a cache counter, so those figures are gross-token readings and each ratio is a bound, not a cache-aware bill. Source `rows-equalinfo-2026-10-26.jsonl`: `cached_tokens`, `cached_reported`.
- `rows-equalinfo-2026-10-26.jsonl` -> `C08` (no accuracy delta): the plain cell `C0F` answers 3 row(s) correctly against 0 for `R` — the arithmetic above is a cost difference, and this count is the only quality statement the file supports. Source `rows-equalinfo-2026-10-26.jsonl`: `answer_correct`.

### 8.3 C0-BASELINE — invalid by design, supports nothing
- `rows-baseline-2026-10-26.jsonl` -> **no claim**: C0 never carries k01 in context (turns carry k12, k10, k08 only), so the plain transcript cannot answer by construction — do not cite any figure from this file (source `orchestration/handoffs/C0-BASELINE.json:101`). Every relation that would route through this file is dead on arrival, and its 105 rows are indexed only so nobody re-derives them. Source `rows-baseline-2026-10-26.jsonl`: `unit`, `answer_correct`, `error`.
- `rows-baseline-2026-10-26.jsonl` cell `C` on `occamy-1.0-NVFP4`: 12 rows, 0 correct of 12 answered, 0 error row(s) — recorded, not citable. Source `rows-baseline-2026-10-26.jsonl`: `answer_correct`, `error`.
- `rows-baseline-2026-10-26.jsonl` cell `C0` on `occamy-1.0-NVFP4`: 12 rows, 0 correct of 12 answered, 0 error row(s) — recorded, not citable. Source `rows-baseline-2026-10-26.jsonl`: `answer_correct`, `error`.
- `rows-baseline-2026-10-26.jsonl` cell `R` on `occamy-1.0-NVFP4`: 24 rows, 3 correct of 24 answered, 0 error row(s) — recorded, not citable. Source `rows-baseline-2026-10-26.jsonl`: `answer_correct`, `error`.
- `rows-baseline-2026-10-26.jsonl` cell `C` on `qwen3.5-9b`: 12 rows, 0 correct of 12 answered, 0 error row(s) — recorded, not citable. Source `rows-baseline-2026-10-26.jsonl`: `answer_correct`, `error`.
- `rows-baseline-2026-10-26.jsonl` cell `C0` on `qwen3.5-9b`: 12 rows, 0 correct of 12 answered, 0 error row(s) — recorded, not citable. Source `rows-baseline-2026-10-26.jsonl`: `answer_correct`, `error`.
- `rows-baseline-2026-10-26.jsonl` cell `R` on `qwen3.5-9b`: 33 rows, 0 correct of 21 answered, 12 error row(s) — recorded, not citable. Source `rows-baseline-2026-10-26.jsonl`: `answer_correct`, `error`.

### 8.4 Non-relations worth stating

- Section P and the claim rows are two different ledgers: a `MEASURED` row file is evidence, and it does not by itself make a claim id resolvable — that still needs an id in `papers/context-cache/CLAIMS.md`. Source: `COMPILATION.md` section P.
- `INVALID-BY-DESIGN` is not `WITHDRAWN`: nothing in the baseline file was refuted by a later measurement, it was never able to answer the question. Source: section 8.3.
- A row file's status never edits a claim row's status. The generator rewrites only the `status` column of 7-column rows, the `build:` stamp, and the two marker regions — so any other change to `COMPILATION.md` is a hand edit and must be reviewed as one.
<!-- rows-relations:end -->
