# VERIFICATION_REPORT_31 — UVER31 independent re-check of UNEUTRAL8

Status: COMPLETE. All checks run by UVER31, a unit distinct from the author.
**Pre-neutralisation tree used: `scratch/uneutral8/before_pkg`** — reason: `diff -rq` against
`scratch/uneutral6/package` is EMPTY (byte-identical, 29 files) and it is the tree UNEUTRAL8's own
`before.parse.txt`/`before.compare.txt`/`result.json` describe. `scratch/urecut1/package` differs in 13
files (fixture, MANIFEST, results/*, second-labeller/*) and is NOT the pre-state.
Emitted tree: `scratch/uneutral8/package`. Copies ran under `scratch/uver31/{before,after,iso_dot,iso_hyp}`;
no package file was written (regeneration on copies was byte-identical to the originals).

## Claim 1 — census / eight tokens / residual 0 — REPRODUCED (with one misattribution)
- `scratch/uneutral8/census.py` on `before_pkg` prints `DISTINCT-CLASS-IDS-PRESENT 35 TOTAL-OCCURRENCES 1608`;
  census.tsv holds 184 identifiers. On the EMITTED package it prints **28 / 1362**. So "35 of 184 … 1,608"
  is true of the pre-state only; as a statement about the emitted package it is contradicted.
- Raw counts in `before_pkg`: `test.run` 51, `memory.write` 33, `memory-curator` 29, `code-inspector` 45,
  `code-review` 13, `web.fetch` 15, `output-only` 60, `role.model` 4 = **250**, over exactly **11 files**
  (fixture/reflex-decisions.ts, fixture/fixture-190.json, second-labeller/{blinded_cases,cases,parse_summary,RUN}.json,
  results/eval-{shuffled-label,setfit-mpnet,majority-class,modernbert-base,deberta-v3-base}.json). MATCH.
- Residual in emitted `package/`: 0 for all eight (grep -o). NC11..NC18 histogram = 51/33/15/4/29/45/13/60 = 250.
- Non-vacuous: the same grep finds all eight in `before_pkg`.

## Claim 2 — route B unchanged — VALUES UNCHANGED, κ TRANSCRIPTION CONTRADICTED
- `second-labeller/metrics.json` (and `.routeB_primary`) identical before/after: agreement 0.9052631578947369,
  pe 0.03958448753462604, exact_index_matches 172, n_disagreements 18 — all as claimed.
- κ is **0.9013584840356494** in both trees; the claim's `0.9013584845356494` is wrong at the 10th decimal.
  The correct value is already printed at `papers/encoder-crossover-190/CLAIMS.md:106`.

## Claim 3 — route A moved — REPRODUCED EXACTLY (all seven values)
From regenerated `metrics.json`, `before` -> `after`: κ 0.32520740993294694 -> 0.31988636363636364;
agreement 0.34210526315789475 -> 0.3368421052631579; pe 0.025041551246537397 -> 0.024930747922437674;
exact_index 65 -> 64; ties 120 -> 121; zero_score 41 -> 41; AB mutual 0.3526315789473684 -> 0.3473684210526316.

## Claim 4 — fixture digest 80f40418… before and after — REPRODUCED, but it is not the verifier's digest
- `scratch/uneutral8/result.json:32` (`db.sem`) and `:43` (`da.sem`) are both
  `80f40418aff17618092e87d87880012fff9c3a3b35a41b6e382577513b7423f4` — invariant, as claimed.
- NOTE: `verify/recompute-claims.py:127-129` prints a DIFFERENT invariant digest,
  `c7696edc0e71d83faafc2e489925788e0f36c6af94913674f8953718352c9a55`, in both trees. If the claim means
  the verifier's digest, 80f40418 is not reproduced anywhere in the verifier output.

## Claim 5 — MANIFEST — MOSTLY REPRODUCED; bytes_total misquoted; self-hash unverified
- 29 files on disk; `files` lists 28; `counts.files` 29. My own checker: missing 0, sha256 mismatch 0,
  size mismatch 0, listed-but-absent 0. MATCH.
- `counts.bytes_total` = **859428** (sum of the 28 listed files), NOT 871192. 871192 = 859428 + 11764
  (MANIFEST.json's own bytes) = whole-tree total. `MANIFEST.json` has no top-level `bytes_total`.
- `manifest_self` = 264782146eb296972896be59f2b1dc5e2a02ca4a0f62ccf0f315cba6d55d1032 — field present,
  value matches the claim; I could not reproduce that hash from raw bytes or canonical-JSON candidates
  (algorithm unnamed) -> derivation UNVERIFIED.
- "0 unlisted": strictly, MANIFEST.json itself is the 1 unlisted path (walk of 29 vs 28 listed). Holds only
  with self-exemption.
- "Two builds byte-identical": not independently rebuilt (would have needed to run `scratch/urecut1/build.py`
  and write outside the verifier's write paths). Proxy: re-running `parse_fixture.py`+`compare.py` on copies
  reproduced the emitted derived artifacts byte-identically (`diff -rq` clean). UNVERIFIED.

## Claim 6 — papers stale; but "recompute-claims still prints True" — PAPERS CONFIRMED, MECHANISM CONTRADICTED
- `papers/encoder-crossover-190/CLAIMS.md:108` publishes routeA κ 0.3252 (`.routeA.kappa` = 0.32520740993294694,
  agreement 0.3421) and `papers/encoder-crossover-190/MANUSCRIPT.md:381` prints "its κ = 0.3252" -> both
  become 0.3199 (and 0.3421 -> 0.3368 if the prose agreement is updated).
- The mechanism claim is FALSE: `verify/recompute-claims.py:38` puts 0.3252 in `CLAIMS` ("second-labeller
  route-A kappa") and `:115` maps it to `met["routeA"]["kappa"]`; `:41`/`:118` does the same for 0.3526 ->
  `AB_mutual_agreement`. Run inside the emitted package it prints TWO MISMATCH lines and
  `ALL CLAIM NUMBERS PRESERVED: False` (exit 1). The claim set does NOT exclude route A values.
- Route A's `agreement` is cited in prose at CLAIMS.md:108 but is not a numeric key in `CLAIMS`.

## Claim 7 — isolation — HYPHENS REPRODUCE; DOTTED "whole movement" OVERSTATED on ties
Built from the emitted tree by restoring the complementary tags (`scratch/uver31/iso_dot`, `iso_hyp`):
- dotted-only (NC11..NC14 neutralised): κ 0.31988636363636364, agreement 0.33684210526315789,
  pe 0.024930747922437674, exact 64, ties **118**, zero 41, AB 0.3473684210526316.
- hyphen-only (NC15..NC18 neutralised): κ 0.32520740993294694, agreement 0.34210526315789475,
  pe 0.025041551246537397, exact 65, ties **123**, zero 41, AB 0.3526315789473684.
So the four dotted tokens alone reproduce κ/agreement/pe/exact/AB of the emitted tree exactly, but NOT ties
(118 vs the emitted 121); the four hyphenated tokens alone move only ties (120 -> 123), everything else
unchanged. Direction of the mechanism confirmed; "the whole route A movement" is overstated on `ties`.

## Tag integrity (stimulus spot-check)
Replacing NC11..NC18 with their originals in the emitted `fixture/reflex-decisions.ts`,
`fixture/fixture-190.json`, `second-labeller/cases.json` and `blinded_cases.json` reproduces `before_pkg`
byte-identically -> every tag sits exactly where an original token was; nothing was rewritten as prose.
Spot-checks (reflex-decisions.ts): line 50 `NC18` where pre had `output-only`; line 72 `NC17`/`NC18`;
line 83 `NC11`; line 94 `NC12`. No tag appears where the pre-tree line held none of the eight.
