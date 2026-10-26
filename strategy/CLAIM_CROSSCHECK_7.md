# CLAIM_CROSSCHECK_7 — are the 143 cut3 expectations anchored to published claims?

Unit UCLAIM7. Question: `scratch/urelease7/cut3/verify_claims.py` prints
`RESULT pass exit=0 claims=143 failed=0 []`. Do those 143 expectations check the **published claims**,
or do they compare shipped numbers to hard-coded copies of themselves?

**Verdict in one line.** Not circular in the main: **140/143 expectations compare a published constant to
a value carried in a second, separate artifact** (`record.json`), and **~55 of those re-derive the value by
arithmetic over lower-level shipped cells** rather than reading it precomputed. **3/143 are constants
checked against copies of themselves** in `sealed.json` — the release's own NOTEs and the release-cut doc
declare exactly those, so `143 claims reproduce` should be read as **141 row-anchored expectations / 140
recomputable** and **2 published figures that provably do not reproduce from rows** (carried by 3
expectations). What the run corroborates is *paper-vs-reduction agreement*, not re-measurement from raw
data: the raw record is withheld and the only link to it, `PROV-*`, is a self-declared digest pin no reader
can recompute.

Evidence command (re-run, captured in full to `scratch/uclaim7/expectations.txt`):

```
python3 scratch/urelease7/cut3/verify_claims.py scratch/urelease7/cut3   # -> RESULT pass exit=0 claims=143 failed=0 []
```

Counts below are of the **PASS/FAIL lines**, not of the four `NOTE` lines (NOTEs are diagnostics, not
claims): `grep -c '^PASS\|^FAIL' scratch/uclaim7/expectations.txt` → **143**. I confirmed the count from my
own run; it is 143.

---

## 1. Inventory of the 143 expectations

Exactly as `verify_claims.py:117-286` emits them. Grouped; the last column is how the *checked* (`got`)
value is obtained.

| Group (claim ids) | n | `got` read from | Published counterpart used as `exp` |
|---|---|---|---|
| `PROV-BYTES`, `PROV-LINES`, `PROV-MD5` | 3 | `provenance.json` fields | `papers/gated-read-batching/CLAIMS.md:13` |
| `INV-ROWS`, `INV-ERR`, `INV-PRED-BOOL`, `INV-UNITS`, `INV-PAIRS`, `INV-GOLD`, `INV-GATE-ROWS`, `INV-MODE-[MODE-1..8]` | 16 | `record.json` `inventory` (stored) | `CLAIMS.md:30,35,36,37,38,60,61`; `MANUSCRIPT.md:9,105,137` |
| `INV-ITEMS` | 1 | **recomputed** `len(per_task["[ARM-1]"]["hit"])` | `MANUSCRIPT.md:9` (20 tasks) |
| `INV-BASERATE` | 1 | **recomputed** `gold_pairs/pairs` | `CLAIMS.md:38` (`120/1800 = 0.0667`) |
| `R1-TP-[MODE-1..5]`, `R1-FP-[MODE-1..5]` | 10 | `record.json` `configs.*.tp/fp` (stored) | `CLAIMS.md:118,119,120,123,124` (C67–C69, C72, C73) |
| `R1-F1-[MODE-1..5]` | 5 | **recomputed** harmonic mean of the stored cells | `CLAIMS.md:56,57,58,67,78`; `MANUSCRIPT.md:134,135,137,156-159` |
| `R1-ACC-[MODE-1..5]` | 5 | **recomputed** `(tp+tn)/n` | `MANUSCRIPT.md:156-159` (3 dp only) |
| `R1-F1-SPREAD`, `R1-BEST-F1`, `R1-BEST-PREC`, `R1-BEST-PREC-RECALL`, `R1-BASELINE-PREC`, `R1-RECALL-LOW`, `R1-RECALL-DOUBLED` | 7 | **recomputed** from stored cells | `CLAIMS.md:59,68,74,78,79,80`; `MANUSCRIPT.md:11,31,137,165` |
| `R1-F1-BATCH-DELTA16`, `R1-F1-BATCH-DELTA90` | 2 | **recomputed** (F1 differences) | **no printed counterpart** → DERIVED |
| `R1-ADMITTED-[MODE-1,3,4]` | 3 | **recomputed** `tp+fp` | `CLAIMS.md:121` (C70 `73 / 268 / 146`) |
| `R2-PTOK-SINGLE/B16/B90` | 3 | `record.json` `configs.*.tok_in` (stored) | `CLAIMS.md:52,53,54`; `MANUSCRIPT.md:137` |
| `R2-PTOK-RATIO-B16/B90` | 2 | **recomputed** ratio of stored sums | `CLAIMS.md:55` (`2.341`, `2.418`) |
| `R2-CALLS-SHORT`, `R2-CALLS-ROUTED` | 2 | **recomputed** `configs.n / selection.n` | `CLAIMS.md:50,51` (C16, C17) |
| `R1-TOTAL-SINGLE/MINIMAL/B90MIN` | 3 | **recomputed** `tok_in+tok_out` | `CLAIMS.md:63,65,74`; `MANUSCRIPT.md:147` |
| `R1-TOTAL-UPLIFT-PCT`, `R1-CTOK-RATIO`, `R1-TOK-DEC-SINGLE/MINIMAL/B90MIN` | 5 | **recomputed** | `CLAIMS.md:64,65,68,83`; `MANUSCRIPT.md:147` |
| `R1-CTOK-MINIMAL`, `R1-CTOK-B90MIN` | 2 | `record.json` `configs.*.tok_out` (stored) | `CLAIMS.md:62,65` |
| `R3-N`, `R3-HIT-TOTAL`, `R3-ITEMS-WITH-GOLD` | 3 | `record.json` `selection["[MODE-6]"]` (stored) | `CLAIMS.md:88` (C49); `strategy/GATED_READ_RELEASE_CUT.md:41` |
| `R3-RECALL5` | 1 | **recomputed** `hit_total/gold_total` | `CLAIMS.md:88` (`recall_at_5 = 0.2917`) |
| `R4-N`, `R4-PICKED-TERMSEARCH` | 2 | `record.json` `selection["[MODE-7]"]` (stored) | `CLAIMS.md:88` (`method_dist = {grep: 120}`) |
| `R4-CHOSEN-OK`, `R4-COST-RATIO` | 2 | **recomputed** | `strategy/GATED_READ_RELEASE_CUT.md:46` (`0.700 (84/120)`, ratio 13.6) |
| `R4-COST-PICKED`, `R4-COST-FULL` | 2 | stored means | `strategy/GATED_READ_RELEASE_CUT.md:46` (`656 / 8931`) |
| `R4-ROUTER-GREP-ROWS` | 1 | **recomputed** `picked_dist/n` | no printed counterpart → DERIVED |
| `R4-CHEAPEST-OK-REC`, `R4-ROUTER-207-REC`, `R4-ROUTER-GREP-207-REC` | 3 | **`sealed.json` literals** | release doc marks `sealed` → **ORPHAN (circular)** |
| `R5-N-[ARM-1..6]` | 6 | `record.json` `end_to_end.*.n` (stored) | `MANUSCRIPT.md:195` (six arms × 20); release doc §1 |
| `R5-HITS/UNITS/CTX/PTOK-[ARM-1..6]` | 24 | `end_to_end.*` stored means/counts | release doc §1 (`:36-39`) |
| `R5-HITS-MULTISET` | 1 | **recomputed** multiset distance | no printed counterpart → DERIVED |
| `Q-COST-RATIO-15.3X` | 1 | **recomputed** ratio of two stored means | release doc §1 (`:43`) |
| `Q-EXPOSURE-0-20-A/B` | 2 | `end_to_end` stored `ctx_p1/ctx_p2` | release doc §1 (`:44`) |
| `R5-UNION-[ARM-1..6]`, `R5-DRAFT-[ARM-1..6]` | 12 | stored per-arm counts | release doc §1 (`:41`, `:42`) |
| `R5-UNION-MATRIX-[ARM-1..6]` | 6 | **recomputed** `sum(per_task[a]["payload_in_ctx"])` | release doc §1 (`:41`) |
| `R6-HIJACKED` | 1 | `end_to_end["[ARM-6]"]` stored `inj_p2` | release doc §1 (`:45`); `MANUSCRIPT.md:195` |
| `R6-CLEAN-N/HITS/ACC` | 3 | **recomputed** from `per_task` vectors | release doc §1 (`:45`) |
| `R5-SIGN-1/2/3`, `R5-P-FLOOR` | 4 | **recomputed** (`sign_p`, `strategies/sign_p` in-file) | `CLAIMS.md:87` (C48 `p ≥ 0.219`); `MANUSCRIPT.md:195`; release doc §1 (`:46`) |

Group sizes sum to **143** (17 INV + 3 PROV + 20 R1-confusion + 9 R1-derived + 3 R1-ADMITTED + 7 R2
+ 10 R1-token + 4 R3 + 10 R4 + 6 R5-N + 24 R5-table + 1 multiset + 3 Q + 12 union/draft + 4 R6
+ 6 R5-UNION-MATRIX + 3 sign + 1 floor).

## 2. Three-way classification

### ANCHORED — 136

The `exp` constant appears at the same value in a published document. Because these are 136 rows, the
anchor is given per **group**; every member of a group shares the cited locator(s).

| Group | Anchor |
|---|---|
| `PROV-BYTES/LINES/MD5` | `papers/gated-read-batching/CLAIMS.md:13` — "**2,267,742 bytes, 9,260 lines, md5 `3aad1ae29e472ef9f5f54e179510faf5`**"; restated `strategy/GATED_READ_RELEASE_CUT.md:56` |
| `INV-ROWS/ERR/PRED-BOOL` | `CLAIMS.md:60` (C26 "9,260 rows, 0 call errors, 0 unparsed"); `MANUSCRIPT.md:105` |
| `INV-UNITS/PAIRS/GOLD` | `CLAIMS.md:30` (90 files), `:35` (1,800 pairs), `:37` (120 gold) |
| `INV-GATE-ROWS` | `CLAIMS.md:61` (C27 "9,000"); `MANUSCRIPT.md:137` |
| `INV-MODE-*` (8) | `CLAIMS.md:60` (mode counts 1800×5, 20, 120, 120 → 9,260) |
| `INV-ITEMS`, `INV-BASERATE` | `MANUSCRIPT.md:9`, `:31` (20 tasks, 120-of-1,800); `CLAIMS.md:38` |
| `R1-TP/FP-*` (10) | `CLAIMS.md:118` (C67), `:119` (C68), `:120` (C69), `:123` (C72), `:124` (C73) — the exact tp/fp integers match |
| `R1-F1-*` (5) | `CLAIMS.md:56` (0.218), `:57` (0.227), `:58` (0.211), `:67` (0.320/0.299), `:78`; `MANUSCRIPT.md:137`, `:156-159` |
| `R1-ACC-*` (5) | `MANUSCRIPT.md:156-159` (0.916 / 0.896 / 0.833 / 0.883 / 0.927; **3 dp**) |
| `R1-F1-SPREAD`, `R1-BEST-F1`, `R1-BEST-PREC`, `R1-BEST-PREC-RECALL` | `CLAIMS.md:59` (0.016), `:67` (0.320), `:78` (0.4179 / 0.2333 / 0.2995); `MANUSCRIPT.md:11`, `:165` |
| `R1-BASELINE-PREC`, `R1-RECALL-LOW`, `R1-RECALL-DOUBLED` | `CLAIMS.md:74` (P 0.2877, R 0.1750), `:75`/`:82` (R 0.3667) |
| `R1-ADMITTED-*` | `CLAIMS.md:121` (C70 `73 / 268 / 146`) |
| `R2-PTOK-*` (3) | `CLAIMS.md:52,53,54`; `MANUSCRIPT.md:137` |
| `R2-PTOK-RATIO-*` | `CLAIMS.md:55` (`2.341` / `2.418`) |
| `R2-CALLS-*` | `CLAIMS.md:50,51` (`15×`/`90×`) |
| `R1-TOTAL-*`, `R1-TOK-DEC-*` | `CLAIMS.md:63,64,65` (1,952,010; 1,084.5; 456.6), `:74` (642,010) |
| `R1-TOTAL-UPLIFT-PCT` | `CLAIMS.md:83` (C44 check `= 1.280`); `MANUSCRIPT.md:11` ("roughly 30 %") |
| `R1-CTOK-RATIO` | `CLAIMS.md:68` (`1,690,920 / 190,699 = 8.87×`) |
| `R1-CTOK-*` (2) | `CLAIMS.md:62` (1,690,920), `:65` (190,699) |
| `R3-*` (4) | `CLAIMS.md:88` (C49 `recall_at_5 = 0.2917`, `tasks_with_any_gold = 17`); release doc `:41` |
| `R4-N`, `R4-PICKED-TERMSEARCH` | `CLAIMS.md:88` (`method_dist = {grep: 120}`); release doc `:46` |
| `R4-CHOSEN-OK`, `R4-COST-*`, `R4-COST-RATIO` | `strategy/GATED_READ_RELEASE_CUT.md:46` (`0.700 (84/120)`, `656 / 8931`, ratio 13.6) |
| `R5-N/HITS/UNITS/CTX/PTOK/Q-*` | `strategy/GATED_READ_RELEASE_CUT.md:36-44`; scoping statement `MANUSCRIPT.md:195` |
| `R5-UNION-*`, `R5-DRAFT-*`, `R5-UNION-MATRIX-*` | `strategy/GATED_READ_RELEASE_CUT.md:41-42` |
| `R6-HIJACKED`, `R6-CLEAN-*` | `strategy/GATED_READ_RELEASE_CUT.md:45`; `MANUSCRIPT.md:195` ("injection-exposure measurement" scoped out) |
| `R5-SIGN-*`, `R5-P-FLOOR` | `CLAIMS.md:87` (C48 `p ≥ 0.219`); `MANUSCRIPT.md:195` ("sign tests are p ≥ 0.219") |

Important scoping note: **R1 and R2/R3 alone are claims the paper actually makes.** `MANUSCRIPT.md:195`
states plainly that "**this paper makes no claim about downstream task accuracy, context-cost reduction, or
injection exposure**" and scopes the R3/R4/R5 arms out. So the 60-odd `R5-*`/`Q-*`/`R6-*` expectations
anchor to `strategy/GATED_READ_RELEASE_CUT.md` §1, not to the manuscript — they verify a *strategy* document's
claim register. That is consistent with the release doc's own framing, but a reader who takes "143 claims
reproduce" as "the paper reproduces" is counting claims the paper disowns.

### DERIVED — 4

`exp` is not itself printed; it is arithmetic on published values, and `got` is recomputed from shipped cells.

| Claim id | `exp` | Why DERIVED |
|---|---|---|
| `R1-F1-BATCH-DELTA16` | 0.0092 | `prf(MODE-3).F1 − prf(MODE-1).F1`; the paper prints 0.218→0.227 but not the delta |
| `R1-F1-BATCH-DELTA90` | −0.0071 | `prf(MODE-4).F1 − prf(MODE-1).F1`; not printed |
| `R5-HITS-MULTISET` | 0 | multiset distance of the six per-arm hit counts vs the published column; a self-consistency assertion with no published form |
| `R4-ROUTER-GREP-ROWS` | 1.000 | `picked_dist["[EXTRACT-2]"]/n`; the release doc prints `207/207`, not `120/120` |

### ORPHAN — 3 (the finding)

Each is a constant in `verify_claims.py` compared to the **same number shipped as a literal in
`scratch/urelease7/cut3/sealed.json`**. No arithmetic over any shipped cell produces it, and none of the
three is in `papers/gated-read-batching/`. Circular in the strict sense.

| Claim id | `exp` | `got` (same literal) | Published counterpart | Verifier's own NOTE |
|---|---|---|---|---|
| `R4-CHEAPEST-OK-REC` | `0.575` (`verify_claims.py:172`) | `sealed["router_cheapest_sufficient"]` | `strategy/GATED_READ_RELEASE_CUT.md:47` marks the source column "**nothing** — see §5" and "**sealed**" | `R4-CHEAPEST-OK-RECOMPUTED`: rows give **0.150** (18/120) under "picked is cheapest and sufficient" and **0.225** (27/120) under "some minimum-cost extractor is sufficient"; "neither reproduces the published value" |
| `R4-ROUTER-207-REC` | `207` (`:174`) | `sealed["router_decisions_total"]` | release doc `:48` "120 rows + 87 prose", "**sealed**" | `R4-ROUTER-207-RECOMPUTED`: "120 of the published 207 … the remaining 87 … are not in any record"; the release "reproduces **84/120** from rows alone" |
| `R4-ROUTER-GREP-207-REC` | `207` (`:175`) | `sealed["router_grep_decisions"]` | same figure as the row above | covered by the same NOTE |

`sealed.json` ships these as declared literals with the note that they are "copied from the withheld
summary artefact" — i.e. the release is *transparent* about the circularity. The defect is not concealment;
it is that the headline count "**143 claims reproduce**" folds three non-recomputable expectations into a
number whose plain reading is "recomputed from the release". The release-cut doc is more careful than the
verifier's own RESULT line: it says "**Two** of the published figures it carries do not reproduce from the
rows and ship **sealed**". Two **figures** (0.575 and 207) but **three expectations**. Honest headline:
**140/143 expectations are recomputable from shipped cells; 2 distinct published figures are not.**

## 3. Arithmetic, stated honestly

- **143/143 expectations PASS**, and I confirmed `claims=143` on my own run.
- **136/143** have their expected value printed in a published document at the same value (rounding
  aside), with a quoted file:line above.
- **4/143** are derived from published values but not themselves printed.
- **3/143** are literal-vs-literal and cannot be recomputed from anything the release ships.
- Of the 140 recomputable expectations, roughly **55 re-derive** their value by arithmetic over
  lower-level shipped cells (confusion cells, per-item vectors, token sums) and roughly **85 compare a
  published constant to a value stored precomputed** in `record.json` (e.g. `configs.*.tok_in`,
  `end_to_end.*.ctx_mean`, `selection["[MODE-7]"].mean_cost_picked`).

This is a **good** result for the release, with one qualification. The comparison is *not*
constant-against-itself: for all 140, the constant lives in `verify_claims.py` and the checked value lives
in `record.json` — two separately authored files. That is a genuine cross-check between the paper and a
reduction of the run, and it does corroborate the paper's numbers.

## 4. What a reader actually learns

Running the shipped verifier shows that **the paper's published numbers agree with the released
reduction**: the confusion cells, token sums, F1/precision/recall/accuracy arithmetic, the R5 arm table
and the sign tests all match constants that are independently present in `MANUSCRIPT.md`/`CLAIMS.md` (for
R1/R2/R3) or in the release-cut claim register (for the arms the manuscript scopes out) — so this is more
than internal self-consistency. But it is **not** a re-measurement: the raw record is withheld, and the
only link from `record.json` back to that record is `PROV-BYTES/LINES/MD5`, a digest of a file the reader
never receives, which therefore *asserts* provenance rather than proving it. And for **2 published
figures (0.575 cheapest-sufficient, 207/207 router degeneracy), carried by 3 of the 143 expectations, the
reader learns nothing at all** — those lines PASS by comparing a constant to a copy of itself, exactly the
circularity this crosscheck was commissioned to look for. Read precisely: **the release corroborates 140
of 143 expectations against a second artifact; 3 are self-referential, and the release says so in its
NOTEs.**

## 5. Other things noticed (recorded, not fixed)

1. **A stale published value is what the verifier checks.** `R1-F1-[MODE-4]` expects **0.210**
   (`verify_claims.py:150`), but `CLAIMS.md:58` (C24) and `MANUSCRIPT.md:135`, `:158` print **0.211** —
   CLAIMS records that "the manuscript's 0.210 was a truncation and now prints 0.211". The exact ratio is
   0.210526, and the expectation passes at `tol 1e-3`, so the corrected manuscript value and the verifier's
   stale constant are not distinguished. The verifier's own `NOTE R1-F1-PRECISION` records this and calls
   it "Recorded, not resolved".
2. **The 4-decimal accuracy constants are not published at 4 decimals.** `R1-ACC-*` expects
   0.9161 / 0.8961 / 0.8333 / 0.8833 / 0.9272; `MANUSCRIPT.md:156-159` prints 0.916 / 0.896 / 0.833 /
   0.883 / 0.927 and `CLAIMS.md` carries no accuracy row at all. The 4-dp digits have no other published
   source than `record.json`'s own `acc` field — the same artifact under test.
3. **A published claim the release doc says cut3 covers, but no expectation reads.** `record.json` ships
   `gold_derivation` (120 stored; **127** re-derived pinned, **130** live) and
   `strategy/GATED_READ_RELEASE_CUT.md:50` lists "Gold labels | 120 stored; re-derivation gives 127 pinned
   / 130 live" with "Hits cut3? **yes**". `grep -c gold_derivation scratch/urelease7/cut3/verify_claims.py`
   → **0**. The claim ships as data but is never checked. `INV-GOLD` covers only the 120.
4. **A published R5 claim with no expectation for 5 of its 6 arms.** The register carries "two-payload ASR
   | 1/0, 1/1, 1/1, 0/0, 2/2, 0/12" (`strategy/GATED_READ_RELEASE_CUT.md:42`); the verifier checks only
   `R6-HIJACKED` = 12 for `[ARM-6]`. The per-arm injection vectors ship in `per_task` but arms 1–5 are
   never asserted.
5. **An unresolved label discrepancy the verifier ships deliberately.** `NOTE Q-EXPO-ATTRIBUTION`: the
   context-carry flags give `20/20/19/0/19/20`, but the file-exposure flags give
   `[20, 20, 19, 19, 19, 20]` — "19 vs 0 for `[ARM-5]`". The release "does not resolve which label the
   manuscript should use". So the `Q-EXPOSURE-0-20` claim (0/20 both channels) and the `R5-UNION` claim
   rest on one of two shipped columns.
6. **Field-name/label mismatch, unresolved.** The register labels the 4.8 / 7.75 / 4.35 / 4.35 / 3.65 /
   4.1 row "**per-arm files**"; the verifier reads `end_to_end.*.units_mean` and calls the claim
   `R5-UNITS`. Whether "files" and `units_mean` are the same quantity is not stated in the release.
7. **Paper claims with no expectation at all** (out of the release's claim set, so not defects, but they
   bound what "the release verifies the paper" can mean): `MANUSCRIPT.md:121` always-`false` accuracy
   0.933; `CLAIMS.md:66` (C32) per-decision cost ratio 2.4×; `MANUSCRIPT.md:9` the literature numbers
   −17.8 / −5.8 / −4 to −18; `CLAIMS.md:31` (C02) corpus size 2.426 / 2.753 MB — which the release doc
   itself records as "**not reproducible**".

---

## UNVERIFIED

1. **The link from `record.json` to the raw run.** I did not attempt to obtain or read the withheld raw
   record, and the pinned trace path in `AGENTS.md` is a different object. The `PROV-*` expectations are
   satisfied by `provenance.json` restating the digest; no shipped command recomputes the digest of
   anything. Whether `record.json`'s cells are faithful is therefore **unverified by this crosscheck** —
   I only verified that they are *consistent with the published numbers*.
2. **The withheld summary artefact** that `sealed.json` says it copies `0.575` and `207` from: not
   readable by me. Whether the displayed 207 is 207/207 term-search or a sum of prose decisions is
   unverifiable here.
3. **The target-repo research doc and its summary JSON** (cited in `CLAIMS.md` as **G** and **S**, at
   withheld paths under the read-only external checkout): I did **not** read them, and I ran no `git`
   command against any target. Every "published counterpart" I cite is from
   `papers/gated-read-batching/MANUSCRIPT.md`, `.../CLAIMS.md`, `.../GAPS.md`, or
   `strategy/GATED_READ_RELEASE_CUT.md`. The G:/S: line locators inside `CLAIMS.md` are the manuscript
   authors' claims, not mine.
4. **`MANUSCRIPT.md:156-159`'s bs1-`none` and bs90-`none` F1/accuracy rows** were read from my grep of
   the file; I did not re-derive the exact form of the withheld run report's tables.
5. Whether the release-cut doc's own "0 claims lost" comparisons between cut1/cut2/cut3 hold — out of
   scope for this unit; I verified only cut3.

## Evidence (commands run)

```
python3 scratch/urelease7/cut3/verify_claims.py scratch/urelease7/cut3
  -> RESULT pass exit=0 claims=143 failed=0 []
grep -c '^PASS\|^FAIL' scratch/uclaim7/expectations.txt
  -> 143
grep -c gold_derivation scratch/urelease7/cut3/verify_claims.py
  -> 0
awk '{print $2}' scratch/uclaim7/expectations.txt | grep -v ^RESULT | sed -E 's/-\[MODE-[0-9]\]$//; s/-\[ARM-[0-9]\]$//' | sort | uniq -c | sort -rn
  -> per-group census, summing to 143
wc -c scratch/urelease7/cut3/*
  -> 5866 METHOD.md | 171 provenance.json | 5008 record.json | 380 sealed.json | 16808 verify_claims.py | 28233 total
grep -rlF <value> papers/gated-read-batching/        -> anchor locations in §2
grep -rnE '<formatted values>' papers/gated-read-batching/MANUSCRIPT.md   -> R1/R2 table rows
```
