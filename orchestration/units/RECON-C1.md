# RECON-C1 — re-adjudicating C1 from the warm-prefix rows

Read-only unit. Sources: `experiments/ptr-engine/RECORD.md:114`; `experiments/ptr-engine/measure/rows.jsonl`
(49 rows, 12 of them `phase:"measure"` request rows); `experiments/miss-law/rows.jsonl` (774 rows);
`experiments/miss-law/LAW.md:85`. Zero live requests.

## What line 114 claims

1. ENGINE-R1 recorded `cached=null` and billed the whole prefix (`8013 = P1+13`; cell C `397 = P1+13`). **Consistent** — cell C reproduces it exactly ×3 reps: P1 384, L 13, prompt 397, `cached_tokens:null`, `cached_reported:false`, `uncached_tokens:397`. `LAW.md:85` is the same shape (residue 0, 8000, L 13, null, 8013).
2. BILL-AUDIT: residue 0 re-bills `64 + L`, residue 1 `1 + L` — "one block, not the prefix". **Untested here, not contradicted** — no residue-0 row has a warm reading (cell C is null) and there is no residue-1 cell at all. At residues 5/2 the re-bill is `residue + L`, which is not `64 + L`.
3. "Only one unit read a field that reports a number at residue 0." **Consistent** — 9/12 measure rows have `cached_reported:true`; the 3 residue-0 rows report null. Nothing in these rows reports a number at residue 0.
4. "ENGINE-R1's `397` should be ~`77` on that append — a **5.2×** overstatement." **Not supported by the rows** — `77 = 64 + 13` needs `cached = 320` at P1 384; the rows' own rule (`cached = P1 − residue`) gives 384 and a bill of 13. Undecidable from these rows (see §The 5.2x claim).
5. "Its 'avalanche insurance, 26×' claim and any padding justified by it are instrument artifacts." **Padding half not supported** — the rows bill the tail token-for-token (5 + 13 = 18 at residue 5), so padding to alignment can save at most `residue ≤ 63` tokens, never a 64-block. The 26× number is inherited from the null-instrument ENGINE-R1 row and is not re-measured here.
6. C-ADJUDICATE closure: "residue-0 avalanche is one block, not the prefix — `/generate` warm 384 on a **423-token** prompt." **Inconsistent as residue-0 evidence** — 423 = 6·64 + 39, i.e. residue 39; a 384 cached reading there is the ordinary block-aligned case, the same form as cells A/B/D, and says nothing about residue 0.
7. "The 5.2× clause is therefore WITHDRAWN; `397` is the engine's own law value." **Half-consistent** — 397 is genuinely the measured value (`law_uncached_measured_L:397`, `observed_minus_predicted:0`), but a null second instrument at residue 0 cannot withdraw a claim about residue 0; it only removes the confirmation.
8. "The second instrument reports warm values in 9/12 rows — 384×3 cell B, 320×3 cell A, 320×3 cell D — null only at cell C." **Consistent, exact** (verified by count).
9. "`quality/rows.jsonl`'s 48 request rows carry no `cached_tokens` key." **Consistent** — 115 rows, 48 with `row:"request"`, no `cached_tokens` key in any.
10. "`run_cells.py:109` posts `/chat/completions`, not `/generate`." **Consistent** — `experiments/ptr-engine/measure/run_cells.py:109` is `"/chat/completions"`.
11. "C1 reopened: warm `cached_tokens` 320/384/320 at residues 5/2/2 in A/B/D with `cached_reported:true`; a second instrument on `:8012` exists." **Consistent** — all 12 measure rows carry `token_source:"http://192.168.2.168:8012/v1"`.

## Offset

| cell | rep | P1 | residue | cached | uncached | uncached−residue | P1−cached |
|---|---|---|---|---|---|---|---|
| A | 0 | 325 | 5 | 320 | 18 | 13 | 5 |
| A | 1 | 325 | 5 | 320 | 18 | 13 | 5 |
| A | 2 | 325 | 5 | 320 | 18 | 13 | 5 |
| B | 0 | 386 | 2 | 384 | 15 | 13 | 2 |
| B | 1 | 386 | 2 | 384 | 15 | 13 | 2 |
| B | 2 | 386 | 2 | 384 | 15 | 13 | 2 |
| C | 0 | 384 | 0 | null | 397 | 397 | — |
| C | 1 | 384 | 0 | null | 397 | 397 | — |
| C | 2 | 384 | 0 | null | 397 | 397 | — |
| D | 0 | 322 | 2 | 320 | 15 | 13 | 2 |
| D | 1 | 322 | 2 | 320 | 15 | 13 | 2 |
| D | 2 | 322 | 2 | 320 | 15 | 13 | 2 |

`uncached − residue` = **13** in all 9 warm rows (spread **0**); `P1 − cached` = residue exactly (5, 2, 2), i.e. `cached = 64·floor(P1/64)`. What the constant implies: the endpoint bills `residue + 13` uncached — the prompt tail beyond the last complete 64-block is billed **token-for-token** (5, not 64, not rounded up), and the **whole append** (L = 13) is always billed. There is no block-granular rounding of the tail, and no per-cell variation: the offset is exactly the append length.

## Law constant

`L_app = n_payload + 12` verified over `experiments/miss-law/rows.jsonl`: 387 rows carry both `n_payload` and `L_app`, **0 violations**. The constant is **12**; `n_payload = 1` (509 rows) ⇒ `L_app = 13`.
`n_payload` is not in `measure/rows.jsonl` under that name, but it **is present as `payload_tokens: 1`**, and the length is present as `L: 13` on all 12 rows — nothing had to be derived, and `prompt_tokens = P1 + L` holds in 12/12 (325+13=338, 386+13=399, 384+13=397, 322+13=335).
**The measured warm offset (13) is the same number as L_app, not one more.** So the second instrument agrees with the project's own law at residues ≥ 2: `uncached = residue + n_payload + 12`.

## The 5.2x claim

Arithmetic of the claim: `397 / 77 = 5.155 → "5.2×"`, where `77 = 64 + L = 64 + 13` (one re-billed block plus the append).
Row-consistent alternative: if the rows' rule holds at residue 0, `cached = P1 − residue = 384` and the bill is `0 + 13 = 13`, so the factor is `397 / 13 = 30.5×`.
Neither branch is determinable: `cached = 64·floor(P1/64)` and `cached = 64·floor((P1−1)/64)` fit all 9 warm rows **identically** (they can differ only when P1 is a multiple of 64 — exactly cell C, which reports null). Taken literally, cell C says `cached = 0` and `uncached = 397`, i.e. **no overstatement at all (factor 1)**.
**Verdict: undecidable from these rows.** The 5.2× figure is not refuted — it reproduces the BILL-AUDIT one-block model exactly — but these rows cannot produce it, and the same rows' alignment rule predicts 30.5×. What the rows do establish is that `397` is not a general law of this endpoint: for the identical append at residues 2/5 the true bill is 15/18.

## Missing

1. A **warm `cached_tokens` at residue 0** (P1 = 384, L = 13) on `:8012 /chat/completions` with `cached_reported:true`. This is the one number that decides `cached 320 → 77 → 5.2×` vs `cached 384 → 13 → 30.5×`. Needed field: `cached_tokens` on a cell whose P1 is an exact multiple of 64; cell C is the only such cell and reports null.
2. A **residue-1** cell — `1 + L` is asserted at line 114 and appears in no row here (residues present: 0, 2, 5).
3. A **re-measurement of the 26× avalanche figure** on the same instrument; the rows test only residues 2 and 5.
4. **Semantics of `cached_reported:false`**: these rows cannot distinguish "genuinely no cache hit at residue 0" from "field suppressed/null but cache warm" — no row records the endpoint's null semantics on this path.
