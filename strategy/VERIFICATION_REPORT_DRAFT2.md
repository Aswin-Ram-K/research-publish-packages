# VERIFICATION REPORT — DRAFT2 (UVERDRAFT2, independent verifier)

Paper under test: `papers/replay-record-not-decision/` (MANUSCRIPT.md, CLAIMS.md, GAPS.md, AVAILABILITY.md).
Verifier is not the author. No network. No `git` command was run. `/home/zer0null/Duval` untouched.
Raw records (pinned path; digest verified, 15 byte-identical copies of each digest exist under `state/`):
- `state/refresh-verify/duval/scnB/state/kg-refresh/duval/repo/.worktrees/engine-a/docs/research/decision-variants.jsonl`
- `…/docs/research/l1-head-to-head.jsonl`

My re-derivation is my own script, `scratch/uverdraft2/verify_draft2.py` (reads only the two `.jsonl`).
The author's `scratch/udraft2/recompute_per_variant.py` was read, not trusted.
**Definition used throughout:** a *binding comparison* is one **unordered model pair × one case `id`**, both
rows read at the **same variant**; divergence = `picked_index` differs. Outcome divergence =
`(picked_index == correct)` differs. Correctness is derived, never the raw `correct` field.

**Verdict: `partial`.** The headline arithmetic reproduces exactly, check for check. Two statements are
contradicted, three are overstated, one username-disclosing path is present.

---

## 1. File identity — CONFIRMED

```
sha256sum "$R/decision-variants.jsonl" "$R/l1-head-to-head.jsonl"
c5ec44a799ddeb963f862fc5c054ddad6ef2fce6ad90edfafd7c1755ac4370e7  …/decision-variants.jsonl
6af0e0d8294cf4d7a20e2d8cb9bfe0c11ff70cc4c4b2792fcdedaf9246b2a1e7  …/l1-head-to-head.jsonl
stat -c '%s'  -> 1197797 / 63238      wc -l -> 3040 / 380
find state \( -name decision-variants.jsonl -o -name l1-head-to-head.jsonl \) -print0 | xargs -0 sha256sum | awk '{print $1}' | sort | uniq -c
     15 6af0e0d8294cf4d7a20e2d8cb9bfe0c11ff70cc4c4b2792fcdedaf9246b2a1e7
     15 c5ec44a799ddeb963f862fc5c054ddad6ef2fce6ad90edfafd7c1755ac4370e7
```
Both digests, both byte sizes and both line counts match the other unit's report exactly. Every mirror copy
is byte-identical to the pinned digest.

## 2. The schema trap — CONFIRMED

```
[correct] DV value set: [0, 1, 2, 3, 4] | L1 value set: [0, 1, 2, 3, 4]
[line1] DV: {'correct': 1, 'picked_index': 1, 'model': 'laya', 'variant': 'V0', 'id': 'acquisition-001'}
[line1] L1: {'correct': 0, 'picked_index': 1, 'model': 'laya', 'id': 'worker.class-001'}
```
`correct` is an option **index**, not a boolean, in both files, observed range `{0,1,2,3,4}`. Both line-1
examples in MANUSCRIPT §2.1 are exact. Field counts (CLAIMS C12) also hold: DV **21** keys
(`calls conf correct decomposable error error_stage id kind level1_group level1_ok level2_skipped
level2_unreached model ms ms1 ms2 p1 p2 p_chosen picked_index variant`), L1 **8** keys
(`correct error id kind model ms p_chosen picked_index`).

*Minor wording note (not a claim failure):* MANUSCRIPT §2.1 "summing the field as if it were 0/1 yields,
for example, `202/190` on the second record file" — the whole-file sum is **404/380**; `202/190` is the
**per-model** naive line. AVAILABILITY's phrasing is exactly right: `scratch/urever2/verify_divergence.py:106-107`
does `acc = sum(r["correct"] for r in rows)` inside a per-model loop and prints `202/190` for **each** of
`laya` and `decider-0.8b` (each model's index-sum happens to be 202). Listed under *overstated* below.

## 3. Headline V0 binding divergence — CONFIRMED

```
[V0] binding 476/1140 = 41.7544%   outcome 324/1140 = 28.4211%
   decider-0.8b|decider-2b  decision 51/190=26.84%  outcome 30/190=15.79%
   decider-0.8b|decider-4b  decision 69/190=36.32%  outcome 47/190=24.74%
   decider-0.8b|laya        decision 98/190=51.58%  outcome 61/190=32.11%
   decider-2b|decider-4b    decision 50/190=26.32%  outcome 35/190=18.42%
   decider-2b|laya          decision 100/190=52.63% outcome 67/190=35.26%
   decider-4b|laya          decision 108/190=56.84% outcome 84/190=44.21%
```
Claimed **476 / 1,140 = 41.7544 %** reproduced. "Comparison" in my computation = 6 unordered model pairs ×
190 case ids = 1,140 (I verified DV indexes uniquely, 3,040 rows = 4 models × 190 cases × 4 variants, and
`decomposable` is constant per `id`, 61 ids `false`). Outcome axis 324/1,140 = 28.4211 % also reproduced.

## 4. Per-variant — CONFIRMED

```
[V1] binding 537/1140 = 47.1053%   outcome 371/1140 = 32.5439%
[V2] binding 456/1140 = 40.0000%   outcome 358/1140 = 31.4035%
[V3] binding 494/1140 = 43.3333%   outcome 383/1140 = 33.5965%
[spread] 40.0000..47.1053 = 7.1053 points
```
All six claimed counts (537/371, 456/358, 494/383) reproduce exactly. Spread 7.1053 points, stated as
7.11 in the manuscript and GAPS — correct.

## 5. Controls — CONFIRMED

```
[control V0<->V2] 244 comparisons, 244 identical, 0 divergent
[control V1<->V3] 244 comparisons, 244 identical, 0 divergent
```
Both claimed controls reproduce exactly (244 = 61 non-decomposable ids × 4 models).

## 6. Pooled prompt rate and the hidden split — CONFIRMED

```
decider-0.8b 51/190 = 26.8421% | decider-2b 30/190 = 15.7895%
decider-4b 45/190 = 23.6842%    | laya 119/190 = 62.6316%
[prompt pooled] 245/760 = 32.2368%
```
Pooled 245/760 = 32.2368 %; the split (laya 62.63 %, deciders 15.79–26.84 %) reproduces exactly.

## 7. Stability — CONFIRMED

```
[stability] 60/190 = 31.5789%
```

## 8. Non-independence of `l1-head-to-head.jsonl` — sub-claims CONFIRMED except `conf` CONTRADICTED

```
[l1 models] Counter({'laya': 190, 'decider-0.8b': 190})
[l1 ids == DV ids] L1 n=190  same set: True
[l1 divergence] decider-0.8b vs laya: 98/190 = 51.5789%
[l1 vs DV] disagreement pattern same on 190/190 cases
[l1 vs DV] laya: picked_index identical 190/190
[l1 vs DV] decider-0.8b: picked_index identical 190/190
[l1 vs DV] ms: differs 380/380, identical 0/380
[l1 vs DV] p_chosen: differs 0/380, identical 380/380
[l1 vs DV] conf: KeyError 'conf'
```
- `picked_index` identical 190/190 per model — **CONFIRMED**.
- `ms` differs 380/380 — **CONFIRMED**.
- `p_chosen` identical 380/380 (differs 0/380) — **CONFIRMED**.
- `conf` **does not exist in L1** — the claim that `p_chosen`/`conf` are identical on 380/380 rows is
  **contradicted** for `conf` (see Finding 1). `laya` vs `decider-0.8b` divergence 98/190 = 51.5789 % and
  same-disagreement-pattern 190/190 — **CONFIRMED**.
- `p_chosen` half of the claim survives; only the `conf` half fails.

## 9. Internal consistency of CLAIMS.md — one coverage overstatement; sampled rows supported

I sampled 16 rows across the range and opened the named source for each: C05, C11, C12, C13, C14, C15,
C16, C17, C22, C29, C40, C41, C47, C54, C55, C56, C62.
- C16 → EXP7:148-150 ✓ ("`correct` is the **index of the correct option**, not a right/wrong flag … reported
  **0 % outcome divergence for every pair**"); C40 → EXP7:139-154 ✓ (line 141 "first run reported '51 %
  replication divergence'"); C22 → EXP7:48-55 ✓ (five measurements verbatim); C56 → EXP7:16-17 ✓ (arXiv
  2605.20173, "replay divergence"); C47 → R2:171 ✓ ("The 3.9 % spread across variants (40.0–47.1 %)"), so the
  paper's 7.11-point correction is right; C62 → R2:137-147 ✓ (three framing corrections at R2:139, :142,
  :145); C54 → R2:152 ✓ as a location, though its replacement content is Finding 1; C17 → fixture
  `…/evals/fixtures/reflex-decisions.ts` **145,031 B** and **190** `id:` literals ✓; C55 → L1 accuracy
  `laya` 71/190 = 0.3737 and `decider-0.8b` 100/190 = 0.5263 ✓ (my per-model `picked_index==correct`).
- All arithmetic rows I re-derived hold (C05 = 1,261,035; C21 61 ids; C23–C30; C32–C39; C41; C43–C54).

**Finding 3 (overstated, check 9):** CLAIMS.md:147 "Rows with an explicit file/field source: **all 62**."
At least C05, C19, C20, C21, C31, C37, C42, C47, C58–C61 have `arithmetic`/`derived` in the Source column,
not a file or field. The provenance is complete but the word "file/field" is stronger than the table.

## 10. Byline — no author name/affiliation/contact, BUT one username-disclosing path

`grep -n -i -E "author|affiliation|institution|university|@…|corresponding|contact|byline|/home/…|zer0null|/Users/"` over the four files: every `author`/`affiliation` hit is a **negation** ("No author block is
supplied", "no affiliation and no institution appears") or "hand-authored". No personal name, no email, no
institution, no contact appears. The byline claim holds.

**Occurrence to report (check-10 requirement):** `papers/replay-record-not-decision/CLAIMS.md:8` contains the
literal path `/home/zer0null/reserach extarctor`, which **discloses the username `zer0null`**. MANUSCRIPT.md,
GAPS.md and AVAILABILITY.md use ellipsised paths (`…/engine-a/…`) and disclose no username.

## 11. Red→green (non-vacuous) — PASSED

```
cp <raw DV> scratch/uverdraft2/perturbed.jsonl
perturb target row: {'model':'laya','variant':'V0','id':'acquisition-001','picked_index':1}
V0 binding divergence  original=476/1140  perturbed=477/1140  changed=True
sha256sum -c scratch/uverdraft2/orig.sha   ->   …decision-variants.jsonl: OK
```
Changing one `picked_index` on a copy moves the V0 count 476 → 477, so the check is sensitive to a single
row; the pinned original's digest is unchanged (`OK`). **Why it would catch a false positive:** the count is
recomputed from all 3,040 raw rows, not read from any summary, so a fabricated or transcribed figure cannot
match unless the arithmetic matches an independent pass over the bytes; and because a one-row mutation is
detectable, a "divergence" number that had been rounded, filtered, or back-filled from a target would fail
the same recomputation.

---

# Findings

## contradicted

1. **`conf` is claimed identical across the two files, but `l1-head-to-head.jsonl` has no `conf` field at all.**
   Sentences:
   - MANUSCRIPT.md:216 — "| `p_chosen` / `conf` vs `decision-variants.jsonl` V0 | **identical on 380/380 rows** |"
   - MANUSCRIPT.md:227-229 — "Measured directly, **`p_chosen` and `conf` are identical on all 380 rows**; only the timing field differs."
   - CLAIMS.md:122 (C54) — "`p_chosen` / `conf` **identical** on 380/380 rows".
   Measured L1 key set is exactly `['correct','error','id','kind','model','ms','p_chosen','picked_index']`;
   `any('conf' in r for r in l1)` is `False`. Only the `p_chosen` half is true (identical 380/380); the
   `conf` half cannot be evaluated and is false as stated (the field does not exist on the L1 side).

2. **The complement of the stable set is stated as 69.4 %; it is 68.4211 % (130/190).**
   Sentences:
   - MANUSCRIPT.md:183 — "For the other 69.4 % of cases, at least one binding picks something different from at least one other."
   - CLAIMS.md:100 (C42) — `"69.4 % of cases diverge" | 1 − 0.315789 = 0.684211 | … | stated as 69.4 %`.
   `1 − 60/190 = 0.6842105…` → **68.4 %** at one decimal, not 69.4 %. The CLAIMS row's own arithmetic
   (0.684211) contradicts the number it records; the manuscript repeats the 69.4 % figure.

## overstated

3. CLAIMS.md:147 — "Rows with an explicit file/field source: **all 62**." About a dozen rows cite
   `arithmetic`/`derived from C…` rather than a file or field (C05, C19, C20, C21, C31, C37, C42, C47,
   C58–C61). Every row does have a stated provenance; the "file/field" wording overstates it.

4. MANUSCRIPT.md:88 — "summing the field as if it were 0/1 yields, for example, `202/190` on the second
   record file." Summed over the whole file the value is **404/380**. `202/190` is the **per-model** naive
   line and is exactly what `scratch/urever2/verify_divergence.py:106-107` prints, so the example is real
   but the "second record file" framing is too broad.

5. AVAILABILITY.md:65 — "The `decision-variants.jsonl` rows also carry `decision` (`picked_index`)". No key
   named `decision` exists in DV (21 keys, verified). The decision axis is carried by `picked_index`; the
   literal field name is not present.

## not_reproduced

None. Every arithmetic figure I could test reproduced.

## unverified

- The antecedent citation **arXiv 2605.20173** (MANUSCRIPT §1/§6, CLAIMS C56) — the manuscript declares it
  was quoted from `EXP#7-replay-divergence.md:16-17` and not fetched. I was barred from the network, so it
  is unverified, **as the paper itself states**.
- Whether `tools/replay/exp7.ts` implements the five §3 definitions (GAPS G-04) — the paper declares this
  unverified by design; not tested here.

## checks that survive (recorded, not padded)

1 (file identity, both digests/sizes/lines, 15 mirrors each), 2 (schema trap: `correct` is index 0–4 in both
files), 3 (476/1,140 = 41.7544 %; outcome 324/1,140), 4 (V1 537/371, V2 456/358, V3 494/383; spread 7.1053),
5 (244/244 identical, 0 divergent, both pairs), 6 (245/760 = 32.2368 %; laya 119/190 = 62.63 %; deciders
15.79–26.84 %), 7 (60/190 = 31.5789 %), 8 (same 190 ids, same 2 models, `picked_index` identical 190/190 per
model, `ms` differs 380/380, `p_chosen` identical 380/380, disagreement pattern 190/190, L1 98/190 =
51.5789 %), 11 (red→green: 476→477 on a perturbed copy, original digest unchanged).
