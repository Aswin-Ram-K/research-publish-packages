# VERIFICATION_REPORT_8 — independent re-verification of UREDACT1 (sanitised paper-#3 release)

**Unit:** UVER8 (independent verifier; not the author) · **Run:** 2026-10-15T20:49Z
**Subject:** `repro/encoder-crossover-190-SANITISED/` (UREDACT1) · **Target:** `/home/zer0null/Duval` @ `907fa39da7ba8ecfbe6e976b7a4cddadea7ac36b` (read-only)
**Method:** fresh copy of the sanitised tree into a workspace scratch area (`.uver8-scratch/`, deleted afterwards); the real tree and `repro/**` were never written.

## VERDICT: `pass-with-corrections`

The carbon claim — **reproduction holds with `0` numbers moved** — is **CONFIRMED** by an independent re-run and by my own recomputation that does not use UREDACT1's script. The fresh-export rule is **CONFIRMED** (blob identity + no `.git`). The leak reduction is **real for the instrument files**. But **four count/scope claims are wrong** (see §7), all in the direction of understating the residual: the published `210 → 154` is measured on an exclusion set the report does not state, the new `README.md` is recorded as clean when it has 8 strict hits, `§7(d)`'s "no residual occurrence outside (a) and (b)" is false for the shipped tree, and the tree still ships the private commit SHA.

---

## 1. Contradicted (with replacement) — at the top

| # | UREDACT1 statement | what I measured | **replacement text** |
|---|---|---|---|
| C1 | `REDACTION_REPORT.md` §2 table, row `README.md`: as-audited `1` → sanitised `–`, footnote *"replaced by this unit's README (which names `DecisionKind` once, on purpose)"* | sanitised `README.md` has **8** strict-regex hits: `DecisionKind` ×5 plus verbatim quotations of `admit()`, `src/scope.ts`, `src/state.ts`, `StateClass`, `grantPolicy`, `expanded[]` | **`README.md` sanitised = 8** (5 `DecisionKind` + 3 lines quoting the withheld vocabulary). The "once, on purpose" parenthetical is wrong. |
| C2 | §7(d): *"After R1–R6 the sanitised tree contains **no** residual occurrence of `src/*.ts`, `StateClass`, `grantPolicy`, `materialiseGrants`, `grantKey`, `content-addressed` or `expanded[]` outside (a) and (b)"* | true for the **instrument** files; false for the shipped tree — `REDACTION_REPORT.md` 32, `redact.py` 18, `README.md` 8 strict lines carry exactly this vocabulary in prose | **"After R1–R6 the sanitised *instrument* files contain no residual occurrence of that vocabulary outside the `question`/option text (a)(b); the unit's own shipped prose and tooling do (REDACTION_REPORT.md 32, redact.py 18, README.md 8)."** |

## 2. Overstated (with the measured number)

| # | claim | measured |
|---|---|---|
| O1 | *"TOTAL 210 → 154 (56 strict-mechanism lines removed)"*, scan described as *"over the shipped artefacts (excluding this unit's `verify/` scaffolding and the `variants/` alternative)"* | Over **exactly that stated exclusion** the sanitised count is **212**, not 154 (i.e. **+2**, not −56). Reaching 154 additionally excludes `redact.py` (**18**), `README.md` (**8**) and `REDACTION_REPORT.md` (**32**) — 58 lines, undisclosed. Whole-tree: as-audited 210 → sanitised 327. Like-for-like **instrument files only** (both sides excluding each unit's own `README.md` + this unit's `redact.py`/`REDACTION_REPORT.md`/`verify/`/`variants/`): **209 → 154, −55**. |
| O2 | §8/README §6: *"the sanitised tree here therefore contains no `.git` directory and no history"* | **No `.git`, no packfile, no `.idx`, no bundle, no `ORIG_HEAD`/`packed-refs` anywhere — 0 hits (confirmed).** But `MANIFEST.json` ships the closed-branch SHA **`a5ef1b28a7baca7dc1094757106b6a6af2c2aaf8` 20×** as `"source": "git:a5ef1b28…:tools/typed-channel/…"` provenance, and `INTEGRITY.md:121`, `README.md:85–93`, `REDACTION_REPORT.md:344–371` name it in prose. **No history objects; a history *reference* and the private path map survive.** The strict regex cannot see `a5ef1b28`, `tools/typed-channel` or `git:`. |
| O3 | §10.4: *"the `src/`-path residue is exactly: **9 path mentions** inside `question`/option text"* | `fixture/reflex-decisions.ts` contains **10** `src/*.ts` occurrences on 7 lines (one line, `:233`, has two). Across instrument files: **22** occurrences — 10 fixture + 10 `harness/data/fixture-190.json` + 2 `second-labeller/disagreements.jsonl`. Distinct basenames present in instrument files: **8** (`loop`, `policy`, `broker`, `broker-test`, `a`, `b`, `x`, `y`). The kernel names `scope`/`layer`/`state`/`dag`/`store` occur **only** in the unit's own prose — so *"the private path map is gone"* is true **for the instrument**. |
| O4 | *"All **ten** values in `papers/encoder-crossover-190/CLAIMS.md` are reproduced"* (and the card's "ten values") | `CLAIMS.md` carries **nine** distinct headline values — `0.2911 0.3252 0.3474 0.3526 0.4526 0.6684 0.6789 0.8837 0.9140` — and `verify/recompute-claims.py` checks exactly nine. `0.159494` (MDE) and the 2×2 are separate. Say **nine**, or name the tenth. |
| O5 | §3 R6 / §9: `LEAD-WIRING.md` *"142 lines"* → *"43-line sanitised note"* | `wc -l` and `awk NR` both give **141 → 42** (both files newline-terminated). Off by one on both sides. |
| O6 | §7 classification: *"(c) `DecisionKind` type-name references — **4 lines**"* | I count **5** surviving prose lines referencing `DecisionKind`: `DECISION_CASE_SCHEMA.ts` ×3, `MANIFEST.json:82`, `second-labeller/PREREGISTRATION.md:29`. Trivial arithmetic slip, not a leak. |

## 3. Not reproduced (coverage limit — not an author failure)

- **`0.6684` is a quoted constant, not a recomputation.** Nothing in the sanitised subset can recompute it: `results/baselines.json` has **no** `publishedBaselines` block and **no** per-case rows for the published D-067 decider-4b (`CLAIMS.md` says so itself: *"the historical baseline has no per-case rows in the tree"*). UREDACT1 **labels it as a quoted constant in the script and in §4.4** — correctly. Verified as *present* in `harness/{tccommon,analyze,collect,evaluate}.py`, `results/baselines.json`, `results/REPORT.md`.
- **`analyze.py` / `evaluate.py` cannot re-run inside the subset** (`harness/out/manifest-{eval,train}.json` are excluded by `EXCLUDED.md` E12). Their outputs ship frozen; `recompute-claims.py` is a **re-implementation**, not a re-run, and says so. I confirm the limitation, not a defect.

## 4. Unverified

- `export-fixture.ts` / `lint.ts` cannot be executed in the subset (need a repo-shaped checkout + TS runner + the pre-registered digest `076164ac…`, which the redaction deliberately invalidates). Declared in `README.md` §5 and §5 cost item 4. I did not attempt to wire them up.
- The sanitised tree's own `INTEGRITY.md` per-file hash table was not re-derived line-by-line by me; I verified the determinative files directly by hash (`fixture/reflex-decisions.ts` = `751dc007…`, `train.jsonl` = `24c39afa…`, `dev.jsonl` = `d311a99f…`).

---

## 5. Priority 1 — the re-run, on a fresh copy

Fresh copy: `.uver8-scratch/encoder-crossover-190{,-SANITISED}` (98 files). Commands run **inside the copy only**:
`bash verify/run-verification.sh <scratch>/scratch-verify` → **exit 0** (9.7 s; no network, no torch); `python3 verify/recompute-claims.py` → **exit 0**.

**My `run-verification.sh` output differs from the shipped `verify/VERIFICATION.txt` only in (i) the three path lines, (ii) the UTC timestamp, and (iii) the order of the first 40 lines listed by the `head -40` sample in step 8** (that step greps `$W/san` in readdir order, which a fresh `cp -r` does not reproduce). Every number, digest, exit code and total is identical. Verbatim (my run):

```
### 1. T1 instrument digest (EXPECTED TO CHANGE — declared, not silent)
076164ac53c2c1aac130953345c481f88b51f4d6fb93d465c7430308a99b4796  <scratch>/orig/fixture/reflex-decisions.ts
751dc007ba115dccc5815fdf97c9ce7b34b0dc990a6e57802d762e9b35ad9cae  <scratch>/san/fixture/reflex-decisions.ts
-- target HEAD (read-only) --
907fa39da7ba8ecfbe6e976b7a4cddadea7ac36b
-- target git status --porcelain --
?? .ci-trunk.txt
?? .relay/
?? docs/evidence/selfbuild/relay-outbound-2026-10-13.txt
?? docs/migration/

### 2. T5 chance floor (mean 1/k over the 190) recomputed from the fixture, both trees
orig  cases 190  chanceFloorMean1overK 0.29105263157894734  options_total 721
san  cases 190  chanceFloorMean1overK 0.29105263157894734  options_total 721

### 3. T4 second-labeller re-run (shipped readers, unmodified) + scoring-projection digest
  parse_fixture.py [orig] exit=0 stderr=[]
  compare.py       [orig] exit=0 stderr=[]
  scoring-projection (id,kind,question,options,correct) sha256 [orig] 57a29b4e78bff60f84309e2e95b56f49663884a13b801345eecd93813ecbf300
  cases [orig] 190  empty_rationales 0  empty_namespaces 0
  _line values preserved [orig] [86, 97, 108] ... [2197, 2208]
  parse_fixture.py [san] exit=0 stderr=[]
  compare.py       [san] exit=0 stderr=[]
  scoring-projection (id,kind,question,options,correct) sha256 [san] 57a29b4e78bff60f84309e2e95b56f49663884a13b801345eecd93813ecbf300
  cases [san] 190  empty_rationales 190  empty_namespaces 190
  _line values preserved [san] [86, 97, 108] ... [2197, 2208]

### 4. T3 prepare.py re-run (steps 3-4; no torch, no network)
  prepare.py [orig] exit=0
  prepare.py [san] exit=0
-- diff of the two stdout logs (paths normalised) --
  PREPARE STDOUT IDENTICAL
-- rendered split digests --
24c39afa8606942ac2f4fb3e6f1ce5c2b0c9ee581b67d1aed38260d4aa020c09  <scratch>/orig/harness/data/train.jsonl
24c39afa8606942ac2f4fb3e6f1ce5c2b0c9ee581b67d1aed38260d4aa020c09  <scratch>/san/harness/data/train.jsonl
d311a99f0d5b2bd8bcff03e9913b3857ec4c98ffd3714ce9a7afa42514eaa976  <scratch>/orig/harness/data/dev.jsonl
d311a99f0d5b2bd8bcff03e9913b3857ec4c98ffd3714ce9a7afa42514eaa976  <scratch>/san/harness/data/dev.jsonl

### 5. T2 metrics.json: sanitised regeneration vs as-audited regeneration
  orig-regenerated == san-regenerated : True
  san-regenerated  == shipped (hand-added keys stripped) : True
  HEADLINE NUMBERS from the sanitised regeneration:
    comparison cases                                     190
    options_total                                        721
    routeA kappa (CLAIMS 0.3252)                         0.32520740993294694
    routeB agreement (0.9052631578947369)                0.9052631578947369
    routeB kappa (0.9013584840356494)                    0.9013584840356494
    n_disagreements (18)                                 18
    AB mutual agreement (CLAIMS 0.3526)                  0.3526315789473684
    closed-subset kappa (CLAIMS 0.8837)                  0.8837023738280471
    roster/bespoke kappa (CLAIMS 0.9140)                 0.9139973672663448
    disagreements_count_routeB                           18

### 6. disagreements.jsonl: only recorded_rationale may differ
  rows 18 18
  keys that differ: ['recorded_rationale']
  every other key identical: True
  sanitised recorded_rationale values all empty: True

### 7. RESIDUAL STRICT-MECHANISM SCAN (sanitised vs as-audited), per file
  [whole *copies*, which the script itself has populated with sandbox/parse artifacts]
  TOTAL LINES: 416 (orig)  /  314 (san)
```

Step 7's 416/314 is an artefact of the script running `parse_fixture.py`/`compare.py` inside `$W` first (it creates `second-labeller/{cases.json,blinded_cases.json,reflex-decisions.sandbox.ts,parse-*.stdout}`), so it is **not** the shipped-tree count. The shipped-tree count is §6 below. The shipped `verify/VERIFICATION.txt` shows the same contamination; the report's 210/154 come from the **pristine** trees (`verify/RESIDUAL-SCAN.txt`), which I reproduce exactly for the as-audited side.

**`python3 verify/recompute-claims.py` — verbatim, my run (byte-identical to shipped `verify/RECOMPUTE-CLAIMS.txt`), exit 0:**

```
  arm modernbert-base  n=190 accuracy=0.347368 (recomputed 0.347368)
  arm deberta-v3-base  n=190 accuracy=0.347368 (recomputed 0.347368)
  arm setfit-mpnet     n=190 accuracy=0.263158 (recomputed 0.263158)
  arm majority-class   n=190 accuracy=0.452632 (recomputed 0.452632)
  arm shuffled-label   n=190 accuracy=0.231579 (recomputed 0.231579)
  arm decider-4b-repro n=190 accuracy=0.678947

  PAIRED McNEMAR, best head vs decider-4b reproduction (aligned by case id)
    2x2: both=39  headOnly=27  deciderOnly=90  neither=34  sum=190
    psi=0.615789  delta=-0.331579  exact p=4.166818e-09  paired MDE=0.159494

  CLAIMS CHECK (tolerance 5e-4)
    0.3474    modernbert-base sealed-190 accuracy          recomputed=0.3473684210526316 OK
    0.4526    majority-class control accuracy              recomputed=0.45263157894736844 OK
    0.2911    chance floor (mean 1/k)                      recomputed=0.29105263157894734 OK
    0.6684    decider-4b published baseline                QUOTED CONSTANT (results/REPORT.md 2; not recomputable in this subset) OK
    0.6789    decider-4b same-run reproduction             recomputed=0.6789473684210526 OK
    counts 39+27+90+34 = 39+27+90+34 = 190 (OK)

  SECOND-LABELLER NUMBERS (from the shipped sanitised metrics.json)
    0.3252    second-labeller route-A kappa                shipped=0.32520740993294694    OK
    0.8837    second-labeller closed-vocabulary kappa      shipped=0.8837023738280471     OK
    0.914     second-labeller roster+bespoke kappa         shipped=0.9139973672663448     OK
    0.3526    second-labeller A/B mutual agreement         shipped=0.3526315789473684     OK

  ALL CLAIM NUMBERS PRESERVED: True
  fixture correctness digest: 8dd05ce6fe31f6bef484e97bed9ec8c96fb5f2c0b17ebb20ff57afb8716c106a
```

### 5.1 Per-value comparison table (my own recomputation, not the author's script)

I recomputed from the sanitised tree with independent code (raw JSON, own McNemar):

| # | CLAIMS.md value | claim | my recomputed value | source inside the sanitised tree | verdict |
|---|---|---|---|---|---|
| 1 | `0.3474` | modernbert-base accuracy | `0.3473684210526316` (66/190) | `results/eval-modernbert-base.json` `perCase` | **match** |
| 2 | `0.4526` | majority-class control | `0.45263157894736844` (86/190) | `results/eval-majority-class.json` | **match** |
| 3 | `0.2911` | chance floor mean 1/K | `0.29105263157894734` (721 options) | `harness/data/fixture-190.json` | **match** |
| 4 | `0.6684` | decider-4b published (D-067) | **not recomputable** — quoted constant | `results/baselines.json`, `harness/tccommon.py` | **quoted, disclosed** |
| 5 | `0.6789` | decider-4b same-run repro | `0.6789473684210526` (129/190) | `results/baselines.json` `.models.decider-4b-exp11-reproduction.perCase` | **match** |
| 6 | `0.3252` | second-labeller route-A kappa | `0.32520740993294694` | `second-labeller/metrics.json` `.routeA.kappa` | **match** |
| 7 | `0.8837` | closed-vocabulary kappa | `0.8837023738280471` | `metrics.json` `.stratification.closed_subset…` | **match** |
| 8 | `0.9140` | roster+bespoke kappa | `0.9139973672663448` | `metrics.json` `.stratification.roster_and_bespoke_subset…` | **match** |
| 9 | `0.3526` | A/B mutual agreement | `0.3526315789473684` | `metrics.json` `.passes["labelsB.json"].AB_mutual_agreement` | **match** |
| — | `39+27+90+34=190` | paired 2×2 | `39 / 27 / 90 / 34`, sum `190` | aligned by case id | **match** |
| — | `p=4.166818e-09` | McNemar exact two-sided | `4.166817880507353e-09` | recomputed (own exact binomial) | **match** |
| — | MDE `0.159494` | paired MDE | `0.15949356562876219` | `(1.959964+0.841621)·√(ψ/n)` | **match** |
| — | projection digest `57a29b4e…` | invariance invariant | `57a29b4e78bff60f84309e2e95b56f49663884a13b801345eecd93813ecbf300` before **and** after | step 3 | **match** |

**Numbers that moved: 0.** Nine of nine recomputable-or-quoted values agree; `0.6684` is a constant and is labelled as one by the author. The following claims of the card are individually confirmed: projection digest identical before/after · `prepare.py` exit 0 with identical stdout (diff empty after path normalisation) · `train.jsonl`/`dev.jsonl` byte-identical (`24c39afa…`, `d311a99f…`) · `metrics.json` orig-regen == san-regen == shipped (with the four hand-added UFIX4 keys stripped, as the script declares).

### 5.2 RED → GREEN (the check can fail)

On the **copy only**: I flipped **one** `perCase.correct` in `results/eval-modernbert-base.json` and added `0.01` to `routeA.kappa` in `second-labeller/metrics.json`, then re-ran `recompute-claims.py`:

```
    0.3474    modernbert-base sealed-190 accuracy          recomputed=0.34210526315789475 MISMATCH
    counts 39+27+90+34 = 38+27+91+34 = 190 (OK)
    0.3252    second-labeller route-A kappa                shipped=0.33520740993294695    MISMATCH
  ALL CLAIM NUMBERS PRESERVED: False
```

→ **RED: two MISMATCH, `ALL CLAIM NUMBERS PRESERVED: False`, exit 1.** After restoring both files, the same command returned `ALL CLAIM NUMBERS PRESERVED: True`, **exit 0**, and the restored files hashed `65255bda…` / `13fed8c6…` — identical to the real tree's copies, proving the restore was exact and the real tree was never touched. **The check is falsifiable.**

## 6. Priority 2 — the leak reduction, re-measured

Strict regex, verbatim from `run-verification.sh`: `StateClass|grantPolicy|materialiseGrants|grantKey|admit\(|src/(broker|scope|layer|loop|policy|state)\.ts|content-addressed|DecisionKind|expanded\[\]|Needle`.

| scope | as-audited | sanitised | delta |
|---|---:|---:|---:|
| whole tree (incl. the unit's own `verify/`, `variants/`, tooling, report) | 210 | **327** | **+117** |
| **exactly the exclusion the report states** (`verify/`, `variants/` removed) | 210 | **212** | **+2** |
| instrument files only (also remove `redact.py`, `README.md`, `REDACTION_REPORT.md` from the after side, `README.md` from the before side) | 209 | **154** | **−55** |
| the figure the report publishes | 210 | 154 | −56 (mixes the two scopes) |

Sanitised per-file counts (`grep -rIlE`/`grep -cE`, pristine tree): `fixture/reflex-decisions.ts` 52 · `harness/data/fixture-190.json` 50 · `REDACTION_REPORT.md` 32 · `redact.py` 18 · 5 `results/eval-*.json` 8/7/7/6/6 · `README.md` 8 · `results/baselines.json` 6 · `second-labeller/disagreements.jsonl` 3 · `fixture/DECISION_CASE_SCHEMA.ts` 3 · `second-labeller/EVIDENCE.md` 2 · `parse_fixture.py` 1 · `RUN.json` 1 · `PREREGISTRATION.md` 1 · `MANIFEST.json` 1. The as-audited 210 and its per-file table reproduce UREDACT1's and UTS1's figures exactly.

**Are the nine (my count: 22) `src/` mentions all inside irreducible question/option text?** Over the **instrument** files, yes — every one of the 22 is inside a `question` field (10 in the fixture on 7 lines, mirrored 10 in `fixture-190.json`, 2 in one `disagreements.jsonl` row). The kernel module names `scope.ts`/`layer.ts`/`state.ts`/`dag.ts`/`store.ts` appear in **no** instrument file; they survive only in the unit's own prose. So the claim is **directionally right and numerically undercounted** (O3).

**What its regex misses** (my own terms: `StateClass`, `grantPolicy`, `manifest`, `expanded`, `admit`, `broker`, `scope`, `layer`, `Dag`, `CommitRecord`):

- `Dag` **0** · `CommitRecord` **0** — clean.
- `layer` 31, `scope` 670, `manifest` 194 — dominated by ordinary English and the pipeline's own `manifest.json`/`num_layers`; no *additional* kernel rule found in prose beyond what the strict terms catch.
- The two option labels (`none -- admit() mints the state`, `the expanded[] ref list`) are already inside the regex and correctly classified as irreducible.
- **The real regex-blind residue is the history reference**: `a5ef1b28a7baca7dc1094757106b6a6af2c2aaf8` ×20 in `MANIFEST.json` (`git:a5ef1b28…:tools/typed-channel/…`), plus prose in `INTEGRITY.md`, `README.md`, `REDACTION_REPORT.md`. The regex contains no term for a commit SHA or the private path `tools/typed-channel/`, so this passes the scan and still tells a reader which private commit and which private directory tree the release came from (see O2).

**`.git` / history:** `find` for `.git*`, `*.pack`, `*.idx`, `ORIG_HEAD`, `packed-refs`, `*.bundle` → **0 hits** across the whole sanitised tree. No VCS objects. **Confirmed** (with the O2 caveat about the SHA citation).

**As-audited subset unmodified:** re-parsing `repro/encoder-crossover-190/MANIFEST.json` (list shape, 42 entries) → **42/42 OK, 0 mismatched, 0 missing**, recomputed by my own sha256 loop. **Confirmed.** (Sample hashes: `fixture/reflex-decisions.ts` `076164ac…`, `train.jsonl` `24c39afa…`, `dev.jsonl` `d311a99f…`.) Target HEAD before = after = `907fa39da7ba8ecfbe6e976b7a4cddadea7ac36b`; `status --porcelain` before = after = the same four untracked paths (`.ci-trunk.txt`, `.relay/`, `docs/evidence/selfbuild/relay-outbound-2026-10-13.txt`, `docs/migration/`) — pre-existing, attributed to the unrelated concurrent session, unchanged by me.

## 7. Fresh-export rule — re-verified

```
$ git -C /home/zer0null/Duval rev-parse a5ef1b28:tools/typed-channel/analyze.py
18966eff5fbd088fa850d0f01d6d32dae6b2d507
$ git -C /home/zer0null/Duval hash-object <sanitised>/harness/analyze.py
18966eff5fbd088fa850d0f01d6d32dae6b2d507        MATCH
   tccommon.py  68c39632efbd81dae37a5332a6c0b716f574cc68  MATCH
   train.py     15858fcd4eb31840758987e1490ebeab56a8981c  MATCH
$ git -C /home/zer0null/Duval merge-base --is-ancestor a5ef1b28a7baca7dc1094757106b6a6af2c2aaf8 HEAD ; echo $?
1     # NOT an ancestor: the branch is closed and unmerged
```

All three released harness files are **byte-identical to the blobs on the closed branch `a5ef1b28`**, and the branch is not reachable from target HEAD. The tree contains **no `.git` and no history objects**. The rule as written is right; what it does not cover is the SHA citation surviving in `MANIFEST.json` (O2).

## 8. Priority 3 — the public-repo claim, settled from the public side

**I computed this hash myself; I did not take UVER6's number on trust.**

| item | value |
|---|---|
| URL fetched | `https://raw.githubusercontent.com/Aswin-Ram-K/publish-present-compete/main/findings/PAPER-DERIVATION.md` |
| HTTP | `200`, `size_download=46636` |
| method | `curl -sSL` → file, then `sha256sum` (raw bytes; no text post-processing) |
| **sha256 I computed** | **`d98c4359d37b987db07707e0b96358de0cd280c979896c6a15858d96bcd14802`** |
| public repo blob sha (GitHub API) | `7842e48c591343dff09cd8cbcf5931382e534493`, size 46636, `findings/PAPER-DERIVATION.md` |
| Duval copy (read-only) | `/home/zer0null/Duval/docs/research/PAPER_DERIVATION.md` → **`d98c4359…`**, 46636 bytes |
| date of fetch | **2026-10-15 (UTC)** |
| cross-check | the `master` branch URL returned the same 200 / 46636 / `d98c4359…`; a probe at repo root (`/PAPER_DERIVATION.md`) returned 404 |

**Result: byte-identical — same sha256, same byte count.** UVER6's published number is **independently confirmed**, and the earlier finding that *"the sha256 appears only inside UVER6's own report/handoff"* is now superseded: it is reproducible from the public internet at the URL above.

**Does UDISC2's 13/13 disclosure confirmation change my conclusion?** It reinforces it but does not carry it. My hash result is the load-bearing item for the narrow claim UREDACT1 flagged (the derivation paper is public, byte-identical). UDISC2's 13/13 (verbatim quotes + URLs, established by a second source) is a **different and wider** claim — that the *mechanisms* are disclosed in that repo, not merely the paper. Both point the same way. My verdict on the reproduction and on the leak accounting does not depend on either: the corrections in §2/§7 stand regardless of prior disclosure, and the `0`-numbers-moved result is independent of the public repo entirely. What the hash *does* settle is that the "defensible by prior disclosure" option (b) no longer rests on an unverified attestation.

## 9. What would change my verdict

- **To `fail`:** any of the ten (nine) values failing to reproduce from inside the sanitised tree; the projection digest differing before/after; `prepare.py` exiting non-zero or rendering a different split; the released harness bytes *not* matching `a5ef1b28`; or a `.git`/packfile found. None occurred. A single strict-mechanism hit inside the **instrument** outside `question`/option/`DecisionKind` would also move me to `fail` on the leak axis — I found none.
- **To plain `pass`:** UREDACT1 restates the leak count with its scope disclosed (**212** over the stated exclusion; **209 → 154, −55** instrument-only), corrects the `README.md` row to **8**, scopes §7(d) to the instrument, records that `MANIFEST.json` ships the `a5ef1b28` SHA and private `tools/typed-channel/` path map, fixes "nine values" and `LEAD-WIRING.md` **141 → 42**. All are edits to prose/counts; no re-run is needed to confirm them.
- **What would not change it:** the `0.6684` quoted-constant caveat (disclosed), the `E12` non-runnability of `analyze.py`/`evaluate.py` (declared), or the irreducible question-text residue (a finding, not a failure — it is the unit's own headline).

## 10. Four lists, separated

- **contradicted (2):** C1 `README.md` sanitised "–"/"once" → **8** hits; C2 §7(d) "no residual occurrence … outside (a) and (b)" → true only for the instrument files, false for the shipped tree (`REDACTION_REPORT.md` 32, `redact.py` 18, `README.md` 8).
- **overstated (6):** O1 `210 → 154 (−56)` scope; O2 "no history is present" (SHA citation survives); O3 "9 `src/` path mentions" (10 in the fixture, 22 in instrument files); O4 "ten values" (nine); O5 `LEAD-WIRING.md` "142 → 43" (141 → 42); O6 `DecisionKind` "4 lines" (5).
- **not_reproduced (2):** `0.6684` recomputation (quoted constant, correctly labelled); `analyze.py`/`evaluate.py` in-subset re-run (E12, declared).
- **unverified (2):** `export-fixture.ts`/`lint.ts` execution (needs TS runner + repo checkout, not in subset); the sanitised `INTEGRITY.md` per-file table in full (I verified the determinative files directly).

**Containment:** writes limited to `strategy/VERIFICATION_REPORT_8.md`, `orchestration/units/UVER8.md`, `orchestration/handoffs/UVER8.json`. Scratch `.uver8-scratch/` created inside the workspace and **removed**. `/home/zer0null/Duval`: read-only reads + read-only `git rev-parse/cat-file/hash-object/merge-base/status`; HEAD and `status --porcelain` unchanged; no `git` state change. Tool calls used: **22 of 50**.
