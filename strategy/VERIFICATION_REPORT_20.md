# VERIFICATION REPORT 20 — UBIJ3 rename-out release tree

**Verifier:** UVER20 (independent; did not write the work). **Bound:** 30 tool calls.
**Card:** `orchestration/units/UVER20.md`  **Parent:** session-c3d61727-8af8-4c19-b1b9-5922c347a11a
**Record of failed unit UVER19 left untouched** (`strategy/VERIFICATION_REPORT_19.md`); nothing in
`scratch/uver19/` was relied upon.

**Invariant under test:** the text the model actually reads must not change.

## VERDICT: `partial`

Substantively the invariant **holds and is fail-closed**. Every headline number reproduces exactly,
and — the strongest single result — a **verifier-owned fork of the builder regenerates the shipped
tree byte-for-byte**. Verdict is `partial` only because 3 of 12 checks did not reproduce
(stimulus-only digest, packaging-surface figures, and `measure.sh` which crashes), and because the
shipped `MANIFEST.json` and `measure.sh` are defective.

## Reproduced as claimed (independent re-run)

| Claim | Claimed | UVER20 measured | OK |
|---|---|---|---|
| tree-three-r2 | 45 files / 3,006,637 B | 45 / 3,006,637 | yes |
| tree-one-r2 | 44 / 3,057,815 | 44 / 3,057,815 | yes |
| tree-two-r2 | 44 / 3,038,324 | 44 / 3,038,324 | yes |
| census three (frozen scanner) | 3,348 = 2,171/1,099/78 | identical | yes |
| census one | 5,364 = 2,171/2,024/1,169 | identical | yes |
| census two | 3,118 = 1,617/1,381/120 | identical | yes |
| inside-stimulus delta | 0 | +0, distinct 30 vs 30 | yes |
| per-class data-jsonl | 1221/0/0 (base 1221/164/1000) | identical | yes |
| K01..K10 layer | 3,676 all three, 0 inside | 3,676 / 0 inside ×3 | yes |
| `imajev` non-census leak | 42 occ / 10 files | 42 / 10 | yes |

Census was produced with the **same frozen scanner** the author used, `scratch/ubij1/census_one.py`
(same 184-identifier list from `scratch/uagnostic1/census.tsv`) — I **audited and re-ran** the author's
scanner rather than authoring my own; that is an audit, and I say so explicitly. Every count above is
one I produced by running it myself. Its matcher is case-insensitive **substring** counting and
attributes each string to the *first* identifier hit only.

### Guard / idempotence / rebuild (verifier-owned fork)
`on scratch/ubij3/**` is forbidden to write, and `bij_three.py:311-312` refuses any output outside
`scratch/ubij3/` with `_stage`/`_tmp` hardcoded there — so the shipped builder **cannot be run
in place without violating the read-only rule**. I forked it to `scratch/uver20/bij20.py`, changing
only `ALLOWED_ROOT` (line 49). Results:

- Green build: 45 files, 3,006,637 bytes, `GUARD inside-stimulus delta = +0`, **exit 0**.
- Two consecutive builds **byte-identical** (`diff -r` exit 0).
- Manifest digest `995299b123335bf4c9414f3cb84ab834eec33b7721b1b3b82607783ceb9d466f` — matches `995299b1…`.
- My rebuild `diff -r` vs shipped `scratch/ubij3/tree-three-r2` → **exit 0, byte-for-byte identical**.
- **RED→GREEN (last, expensive):** red copy disables the rendered-prose needles
  (`PROSE_KEYS = set()`). Run: **exit 3**, `GUARD FAILED (closed): inside-stimulus moved -2132 (distinct 9 vs 30)`,
  *"No output tree was written."* No output tree existed afterwards; no `_tmp`/`_stage` leftovers.
  **The guard is a real guard, not an assertion.**

### Tools re-run in a verifier sandbox copy (`scratch/uver20/tree-run`)
`compileall` **0**, stderr 0 bytes, **0 SyntaxWarning**; `train.jsonl` **800**, `dev.jsonl` **200**,
`disagreements.jsonl` **18**, all **0 bad**; `parse_fixture.py` **0** (**190 records / 721 options**,
0 parse failures); `compare.py` **0**; `recompute-claims.py` **0** printing
`ALL CLAIM NUMBERS PRESERVED: True`, sha256 `3e67a39eadc9a4f65d32462ec7093c167d01089089a7a88b131415ef65275dc5`.
`harness/prepare.py` **exit 2** with literal text:
`REFUSED: corpus digest mismatch — expected c78681d6cf35bf23245bd24963c5fbdd6b3ea03e1bf74d1b3ddc5a49ca63fd66, got f1359a72d0826dd6c44cf2672ddaa665cdeb35aad56f0f15f4ba52867bb5ddf3`
— i.e. only the pre-existing corpus-digest pin, as claimed.

### Metrics re-derived from stored labels — all exact
routeA kappa `0.32520740993294694`; routeB kappa `0.9013584840356494`, exact index **172**, **18**
disagreements; AB `0.3526315789473684`; closed-vocabulary kappa `0.8837023738280471` (n=106); roster
kappa `0.9139973672663448` (n=84); arms `0.347368 / 0.347368 / 0.263158 / 0.452632 / 0.231579 / 0.678947`;
2×2 `39/27/90/34` (sum 190).

### Digest moved / unmoved table
Unmoved: `harness/data/fixture-190.json` (`022be4a3…`), `second-labeller/metrics.json`,
`MANIFEST.json`. Moved: `harness/data/train.jsonl` (`e81baca9…`→`95e0ea13…`), `dev.jsonl`
(`41629719…`→`a9cd7e4a…`), `results/baselines.json` (`8d4c584c…`→`90689d57…`). Exactly as claimed.

### Fix 2 — true for the lines, **overstated if read as whole files**
`harness/tccommon.py:118` and `harness/prepare.py:148` are **byte-identical** to baseline at those
lines, and `nCandidate` has exactly **2** occurrences (tccommon.py:118, prepare.py:148), both escape
contexts, preserved. But the **whole files differ**: `tccommon.py` 78 diff lines, `prepare.py` 44.
`F19 option` occurs **0** times. Read as "the files are byte-identical" the claim is false; read as
"those lines/escapes survived Fix 2" it is true. **Overstated (wording only).**

### Model-facing text — byte-identical
Compared base (`tree-one-r2`) vs shipped, decoding JSON and comparing the values of
`question`/`options`/`situation` (canonical JSON, order-insensitive keys):
`train.jsonl` **800 records / 1,600 prose fields / 0 mismatched**, `dev.jsonl` **200 / 400 / 0**,
`fixture-190.json` **380 prose fields / 0 mismatched**. **1,001 records and 2,380 prose fields compared, 0 differences.**

## DEFECTS

### D1 — `MANIFEST.json` is a real defect in the ship set (CONFIRMED, worse than stated)
`scratch/ubij3/tree-three-r2/MANIFEST.json`, sha256 `0553ea51672cb7f8ffa743300e8ee30470b6880870f397db85e6fe66cc993d8c`:
- `counts.files: 42` while the tree has **45** files; `counts.bytes_total: 5,070,428` vs real **3,006,637**.
- Omits the now-shipped `verify/recompute-claims.py` (confirmed), plus `MANIFEST.json` itself and both
  `variants/no-union/files/fixture/*.ts`.
- Lists `INTEGRITY.md` and `README.md`, which **do not exist** in the tree.
- **34 of 42 per-file `sha256` values are stale**; only 6 match.
- Identical sha256 in baseline and emitted tree → **carried over unchanged**, i.e. inherited, not
  newly introduced by UBIJ3. Still shipped, still wrong.

### D2 — `scratch/ubij3/measure.sh` does not run to completion
Step 7 does `m["routeB"]`, but the real key is **`routeB_primary`** → `KeyError: 'routeB'`. The author's
own `scratch/ubij3/measure.log:41` shows that exact traceback, so `measure.sh` never produced its
step-7 numbers. Step 7 also reads `second-labeller/cases.json`, which **does not exist**. `measure.sh`
is therefore **not a working reproduction script**, and it would also write into `scratch/ubij3/**`.

### D3 — no side is taken on UBIJ2's "outside is also stimulus" argument
I confirmed the census's "outside" bucket is large (1,099 in the emitted tree) and that the guard
protects only `question`/`options`/`situation` values. Whether part of "outside" is training stimulus
is **not adjudicated** here.

### D4 — "numbers preserved" ≠ experiment reproduces
No model was re-trained. `recompute-claims.py` recomputes from stored labels. Additionally
`second-labeller/metrics.json` carries a `_correction` key: *"Corrected by UFIX4 on 2026-10-15 per
UVER3 C2 (strategy/D59_3.md): the limitation keys were added by hand … the frozen scripts (D01,
characterise.py, compare.py) were NOT edited and still regenerate the pre-correction bytes."* So the
metric numbers verify as arithmetic over stored labels, not as a re-run of the experiment.

## NOT REPRODUCED / UNVERIFIED
- **Stimulus-only sha256 `26c5ddcb…`** — NOT reproduced. No shipped script computes it; 7 candidate
  definitions I tried (inside-stimulus values and matched needles, several joins/encodings) all miss.
  The invariant is nonetheless established by stronger means (byte-identical rebuild + 2,380
  byte-identical prose fields + census inside delta 0).
- **Packaging surface 309 / 240 / 187, and "44 file names"** — UNVERIFIED. No measuring procedure is
  shipped; `orchestration/units/UBIJ3.md:116-121` is the only source. My closest reading gives
  **45 file basenames** (not 44) and **11 directory entries** (matches "11 directory names"), with
  0 needle hits among directory names. `imajev` 42/10 confirmed independently.
- **Projection digest `620e4a07…`** — UNVERIFIED: its input `cases.json` is not shipped.
  (bytes_total 5,070,428 in MANIFEST is likewise unreproducible against the shipped tree.)

## Recommendation
**Ship `tree-three-r2`.** The invariant is protected and, on my own rebuild, exactly satisfied; the
tree is reproducible byte-for-byte from source. **Do not ship `tree-two-r2`** (inside-stimulus 1,617
against a 2,171 baseline). Before shipping, **fix `MANIFEST.json`** (D1) and either fix or drop
`measure.sh` (D2); re-derive or retract the packaging-surface figures (D3/§NOT REPRODUCED).

## Containment
Wrote only `strategy/VERIFICATION_REPORT_20.md`, `orchestration/units/UVER20.md`,
`orchestration/handoffs/UVER20.json`, `scratch/uver20/**`. No writes to `scratch/ubij1|ubij2|ubij3|uver19/**`
or `repro/encoder-crossover-190-SANITISED/**`; no git command; no rename map written or printed.
