# REGEN_ASSESSMENT — what applying the substitution actually does

Unit **UREGEN1**. Question answered: *if `redact.py` is run against the live sanitised tree, what does
the release gate see, and what has to be re-declared?*

**Nothing was released, decided, or written outside `scratch/uregen1/**` + this file + the UREGEN1
card/handoff.** `repro/encoder-crossover-190-SANITISED/`, `repro/encoder-crossover-190/`,
`.ucurate1/pre/research-publish-packages/` were read-only inputs (grep/read only; no `git`, no writes).

---

## 0. Commands and method

```bash
cp -r repro/encoder-crossover-190-SANITISED            scratch/uregen1/tree   # the tree to regenerate
cp -r repro/encoder-crossover-190                      scratch/uregen1/encoder-crossover-190  # as-audited sibling
cd scratch/uregen1/tree && python3 redact.py > ../redact-run.log 2>&1
grep -rn -I -i -F -f scratch/uregen1/patterns/hard.txt   <dir> | wc -l   # the gate, verbatim
grep -rn -I -i -F -f scratch/uregen1/patterns/review.txt <dir> | wc -l
cd scratch/uregen1/tree && python3 verify/recompute-claims.py
```

The pattern lists the denylist-era gate hard-coded — the `PATTERNS_HARD`/`PATTERNS_REVIEW` heredocs that then
occupied `orchestration/units/UBUILD1.build.sh` (since deleted by ULICENCE3; the gate today is the positive vocabulary checker written by the heredoc beginning `cat > "$DEST/gate.sh" <<'GATE_EOF'`, currently `:771`–`:896`, `chmod +x` at `:897`) — were extracted byte-for-byte into `scratch/uregen1/patterns/{hard,review}.txt` (24 hard patterns). The
"ship set" numbers come from driving `orchestration/units/UBUILD1.build.sh` with `SAN_SRC` pointed at
the regenerated tree — same script, same destination shape, only the sanitised input swapped.

---

## 1. Did it run clean? Yes — EXIT=0 on the first attempt

```
$ cd scratch/uregen1/tree && python3 redact.py
EXIT=0
```

No sibling patch was needed: the as-audited tree is only *read* by the provenance step, and it was
supplied at `scratch/uregen1/encoder-crossover-190`. Stage-D footer:

```
entries_changed=17  identity_flags_flipped_true_to_false=17
files=42  bytes_total=5268950  hashes_verified_identical=25  derived_excerpts=2
```

17 files rewritten, nothing added or removed (42 `MANIFEST.json` entries before and after).
`redact.py` is self-idempotent (regen₁ vs regen₂ 44/44 identical), so a second run is a no-op.

---

## 2. THE MONEY NUMBER — gate on the regenerated **ship set**: **62 hard / 2124 review**

| | hard-fail lines | review lines |
|---|---|---|
| UCURATE1's unmodified 58-file ship set | **152** | — |
| same 58 files, regenerated | **62** | **2124** |

**The build still does not exit 0.** Substitution removes 90 hard-fail lines (the `StateClass` /
`grantPolicy` occurrences inside `question` values) and leaves 62 that stage C is forbidden to touch.

### Per-pattern (regenerated ship set)

| pattern | lines |
|---|---|
| `expanded[` | 26 |
| `admit(` | 20 |
| `REDACTION_REPORT` | 10 |
| `EXCLUDED.md` | 2 |
| `StateClass` | 2 |
| `grantPolicy` | 2 |
| `VERIFICATION_REPORT` | 1 |
| **distinct lines** | **62** |

(Pattern counts sum to 63 because `second-labeller/disagreements.jsonl:2` carries both `StateClass`
and `grantPolicy`.)

### Every residual line, by file and pattern

`code/fixture/reflex-decisions.ts` — 10 lines
- `REDACTION_REPORT` — :21, :25, :79, :80, :420, :735, :1929 (pointers to `../REDACTION_REPORT.md`, and seven `[withheld: … see REDACTION_REPORT.md §3]` notes)
- `EXCLUDED.md` — :28 (`See ../EXCLUDED.md.`)
- `admit(` — :146 (`options: ["reasoner (propose only)", "editor (attached, writes)", "none -- admit() mints the state", …]`)
- `expanded[` — :572 (`options: ["the expanded[] ref list", …]`)

`code/harness/data/fixture-190.json` — 2 lines
- `admit(` — :72 (`"none -- admit() mints the state"`)
- `expanded[` — :573 (`"the expanded[] ref list"`)

`code/verify/recompute-claims.py` — 1 line
- `EXCLUDED.md` — :14 (docstring reference to `EXCLUDED.md` E12)

`code/harness/LEAD-WIRING.md` — 2 lines
- `REDACTION_REPORT` — :8, :42 (`../REDACTION_REPORT.md` sections 7 and 4)

`code/harness/export-fixture.ts` — 1 line
- `REDACTION_REPORT` — :36

`code/eval/second-labeller/parse_fixture.py` — 1 line
- `expanded[` — :50 (the docstring that explains the `]`-truncation defect)

`code/eval/second-labeller/RUN.json` — 1 line
- `expanded[` — :112

`code/eval/second-labeller/metrics.json` — 1 line
- `VERIFICATION_REPORT` — :5 (`strategy/VERIFICATION_REPORT_…` in the UFIX4 correction note)

`code/eval/second-labeller/disagreements.jsonl` — 3 lines
- `StateClass` — :1, :2
- `grantPolicy` — :2, :5

`code/eval/results/*.json` — 40 lines (label echoes; every hit is an option string)

| file | lines |
|---|---|
| `eval-shuffled-label.json` | 8 — `admit(` :243, :519, :522, :524 · `expanded[` :343, :1096, :1102, :1104 |
| `eval-deberta-v3-base.json` | 7 — `admit(` :243, :519, :522 · `expanded[` :343, :1096, :1102, :1104 |
| `eval-majority-class.json` | 7 — `admit(` :243, :519, :522 · `expanded[` :343, :1096, :1102, :1104 |
| `baselines.json` | 6 — `admit(` :83, :1457 · `expanded[` :348, :349, :1722, :1723 |
| `eval-setfit-mpnet.json` | 6 — `admit(` :243, :519, :522 · `expanded[` :343, :1096, :1102 |
| `eval-modernbert-base.json` | 6 — `admit(` :243, :519, :522 · `expanded[` :343, :1096, :1102 |

**What is irreducible and why:** the only vocabulary the substitution actually rewrites is text sitting
under a `question` key (`redact.py:689-760`, `CASE_FIELDS = ("question",)`, `redact.py:208`). Every one
of the 62 residual lines is *not* a question: they are option labels (`"none -- admit() mints the
state"`, `"the expanded[] ref list"`), the label-keyed histograms/gold/pred fields the shipped eval
results are made of, and filename pointers (`REDACTION_REPORT.md`, `EXCLUDED.md`) that no token rule
covers. `redact.py:206-207` states the reason labels are excluded: substituting one option label moved
`second-labeller` `routeA.ties` 120 → 119 in REPORT2 §5. **62 is a floor given that constraint.**

---

## 3. Gate on the regenerated **whole tree** — UREDACT3's 98 does *not* reproduce as stated

| tree | hard-fail lines (verbatim 24-pattern scan) |
|---|---|
| live shipped `repro/encoder-crossover-190-SANITISED/` | **494** |
| regenerated `scratch/uregen1/tree/` | **360** |

UREDACT3's "394 present bytes / 98 regenerated" reproduce only under a narrower base. I found the exact
base for 98: regenerating minus these nine process/audit files —

```
REDACT3_REPORT.md  REDACTION_REPORT.md  redact.py  README.md  RESIDUALS.md
INTEGRITY.md  SCRUB_REPORT.md  verify/VERIFICATION.txt  verify/redaction-log.json
```

360 − 262 = **98** exactly. The same exclusion on the live tree gives **237**, not 394 — so the two told
numbers do not come from one consistent base, and 394 is not reproduced by anything I tried. My
whole-tree figures are: **494 before, 360 after**. Ship-set figures (section 2) are the ones the release
decision turns on.

---

## 4. Numbers did not move — re-proved on the regenerated tree

`python3 verify/recompute-claims.py` (in `scratch/uregen1/tree`) → **EXIT=0**, and verbatim:

```
  arm modernbert-base  n=190 accuracy=0.347368 (recomputed 0.347368)
  arm deberta-v3-base  n=190 accuracy=0.347368 (recomputed 0.347368)
  arm setfit-mpnet     n=190 accuracy=0.263158 (recomputed 0.263158)
  arm majority-class   n=190 accuracy=0.452632 (recomputed 0.452632)
  arm shuffled-label   n=190 accuracy=0.231579 (recomputed 0.231579)
  arm decider-4b-repro n=190 accuracy=0.678947
  PAIRED McNEMAR ... 2x2: both=39 headOnly=27 deciderOnly=90 neither=34 sum=190
    psi=0.615789 delta=-0.331579 exact p=4.166818e-09 paired MDE=0.159494
  CLAIMS CHECK (tolerance 5e-4)
    0.3474 modernbert-base sealed-190 accuracy   recomputed=0.3473684210526316 OK
    0.4526 majority-class control accuracy       recomputed=0.45263157894736844 OK
    0.2911 chance floor (mean 1/k)               recomputed=0.29105263157894734 OK
    0.6684 decider-4b published baseline         QUOTED CONSTANT (results/REPORT.md 2) OK
    0.6789 decider-4b same-run reproduction      recomputed=0.6789473684210526 OK
    counts 39+27+90+34 = 190 (OK)
  SECOND-LABELLER NUMBERS (from the shipped sanitised metrics.json)
    0.3252 route-A kappa   OK     0.8837 closed-vocab kappa  OK
    0.914  roster+bespoke kappa OK 0.3526 A/B mutual agreement OK
  ALL CLAIM NUMBERS PRESERVED: True
  fixture correctness digest: 8dd05ce6fe31f6bef484e97bed9ec8c96fb5f2c0b17ebb20ff57afb8716c106a
```

- Every CLAIMS value the script carries (9 numeric rows + the 190 count) recomputes within 5e-4; the
  script's own verdict line is `ALL CLAIM NUMBERS PRESERVED: True`. The script never prints a token
  named `numbers_changed`; that verdict line is its equivalent, so **`numbers_changed = 0`**.
- Independent digests, regenerated tree: `train.jsonl` = `24c39afa8606942ac2f4fb3e6f1ce5c2b0c9ee581b67d1aed38260d4aa020c09`,
  `dev.jsonl` = `d311a99f0d5b2bd8bcff03e9913b3857ec4c98ffd3714ce9a7afa42514eaa976` — **byte-identical to the live tree**.
- `harness/data/fixture-190.json` and `train`/`dev` are untouched by stage C; the *fixture source* does
  change as a file (`fixture/reflex-decisions.ts` `751dc007…` → `23515654ea48873e88572b1a63916fbaa44d65b4f81c1970e38086b3fdff030c`), which is expected — question text is inside it.

---

## 5. Projection-digest delta, and the re-declaration cost

Measured with the tree's own method (`verify/run-verification.sh:57-62`: `parse_fixture.py` → `cases.json`,
projection = `id,kind,question,options,correct`, canonical JSON, sha256):

| | scoring-projection digest |
|---|---|
| before (shipped / as-audited, `INTEGRITY.md` §2 row 1) | `57a29b4e78bff60f84309e2e95b56f49663884a13b801345eecd93813ecbf300` |
| after (regenerated tree) | `b85e4585d8c7f0beec02620356b8fcb2b53bb27b0c9e5544bf51e8368bec7a26` |

The delta is **not cosmetic**: `redact.py:336-338` and `fixture/reflex-decisions.ts:553-554` both assert
that the scoring projection is *unchanged* and that "that projection's digest is the invariant a
sanitised checkout should assert". Regeneration **falsifies that assertion**, because `question` is part
of the projection and stage C rewrites question text. `INTEGRITY.md:93` currently prints the same digest
in both the "before" and "after" columns.

### Files recording the old digest (`grep -rl 57a29b4e… . --exclude-dir=.git`) — **89 files**

| class | count | examples |
|---|---|---|
| **ships in the 58-file package** | **0** | — |
| live tree's own docs (`repro/encoder-crossover-190-SANITISED/`) | 7 | `INTEGRITY.md`, `README.md`, `REDACTION_REPORT.md`, `SCRUB_REPORT.md`, `REDACT3_REPORT.md`, `verify/VERIFICATION.txt`, `variants/no-union/README.md` |
| workspace records (scratch, `.uredact3/`, `experiments/token-substitution-test/` 45, `orchestration/handoffs` 5, `orchestration/units/USCRUB1.md`, `strategy/VERIFICATION_REPORT_8.md`, `.ucurate1/pkgroot/pkg/code/verify/VERIFICATION.txt`) | 82 | — |

**Zero of the 58 shipped files record the old digest.** `README.md`, `INTEGRITY.md` and
`variants/no-union/README.md` are not in `SHIP_STAGED` (the `SHIP_STAGED=(` list at `UBUILD1.build.sh:133`, closing `:202`: only
`code/harness/README.md` ships; `variants/` is absent; `code/verify/VERIFICATION.txt` is explicitly
excluded at :174-181). So the **re-declaration cost is entirely outside the package**: it is the live
tree's own `INTEGRITY.md` §2 + `README.md` and the workspace's process records — 89 files, of which the
7 live-tree ones are the ones a rebuild would inherit. Any future rebuild that re-runs the tree's own
verification will fail on `INTEGRITY.md:93` unless that row is re-declared to `b85e4585…`.

---

## 6. UREDACT3's stage-D defect claim — **contradicted**

The claim: "stage D writes the **source** digest into `sha256` while leaving `identical_to_source: true`;
6 stale identity rows, 2 still open (`README.md`, `INTEGRITY.md`)".

Stage D's actual code (`repro/encoder-crossover-190-SANITISED/redact.py:884-889`):

```python
flag = (sh == h) if sh else e.get(key)   # :884-885   identity flag = (source == output)
e["sha256"], e["bytes"] = h, b           # :886       sha256 IS the OUTPUT digest
if sh: e["source_sha256"] = sh           # :888-889   source digest kept separately
```

Measured on the regenerated `MANIFEST.json`: **42 entries, 37 → 25 rows flagged identical, all 25 satisfy
`sha256 == source_sha256`, 0 contradictions.** The implementation is correct.

The contradiction is in the **shipped** `MANIFEST.json`, which stage D repairs:

| | entries | identity flag True | sha256 == source_sha256 | contradictions |
|---|---|---|---|---|
| shipped (live) | 42 | 37 | 31 | **6** |
| regenerated | 42 | 25 | 25 | **0** |

The six defective rows in the shipped MANIFEST: `EXCLUDED.md`, `INTEGRITY.md`, `LICENCE_TODO.md`, `README.md` (all four are tree-level process docs, not in `SHIP_STAGED`), plus `harness/LEAD-WIRING.md` and `harness/collect.py` (which do ship as `code/harness/...`). The *record* carrying the contradiction is the tree-root `MANIFEST.json`, which is absent in `SHIP_STAGED` (52 entries), so no shipped file states it. **Verdict: UREDACT3's claim is backwards — regeneration fixes the defect;
and the row count is 6, not 2.**

---

## 7. Is regeneration a one-command release step? **No.**

What someone would have to run for the live tree to *become* the regenerated tree (not run by me):

1. `cp -r repro/encoder-crossover-190-SANITISED <fresh copy>; cp -r repro/encoder-crossover-190 <sibling>`
2. `cd <fresh copy> && python3 redact.py` — clean, but 17 files change and 62 hard-fail lines remain.
3. **Re-declare** (blocking, not optional): `INTEGRITY.md` §2's scoring-projection row
   `57a29b4e…` → `b85e4585d8c7f0beec02620356b8fcb2b53bb27b0c9e5544bf51e8368bec7a26`, and the
   "projection unchanged" sentence in `redact.py:336-338` / `fixture/reflex-decisions.ts:553-554`, and
   the same digest wherever the workspace's 89 files repeat it.
4. **Rule on the 62 residue**, i.e. decide whether option labels and the shipped eval-result files may
   be substituted. `redact.py:206-207` records that label substitution costs `routeA.ties` 120 → 119, so
   this is a scientific claim, not a formatting choice.
5. Re-run the gate and the package build; the build still will not exit 0 at 62.

---

## 8. The honest counter-argument

*"The manuscript never names the substituted vocabulary"* — true (`papers/encoder-crossover-190/MANUSCRIPT.md`
has zero hits for `StateClass`/`grantPolicy`/`expanded[`/`admit(`/`GrantPolicy`). But other shipped
artifacts do depend on those names:

- **`fixture/reflex-decisions.ts` header/section notes and `harness/LEAD-WIRING.md`/`export-fixture.ts`
  pointers**: they name `REDACTION_REPORT.md` and `EXCLUDED.md` *as files*. Nothing is broken by
  substitution; they are only pattern-list residue (12 lines).
- **`harness/tccommon.py`** (typed-channel description): `.py` is in `TOKEN_SKIP_EXT` (`redact.py:201`),
  so stage C skips every `.py` file — the typed-channel prose is untouched. `tccommon.py:65`
  `INSTRUMENT_190_SHA256` pins `076164ac…`, not the projection digest, so it needs no re-declaration.
- **`variants/no-union/`**: generated but **not shipped** (`variants/` absent from `SHIP_STAGED`).
- **Option labels**: re-checked *because it was asked*. `redact.py` stage C substitutes, line by line:
  path rules (`_TGT`/`_HOME`, `redact.py:188-190`) always; and `TOKEN_MAP` (`:191-200`) =
  `MODULE_7..1`, `MATERIALISE_A` (`_MGRANT`), `TYPE_A` (`_STATE`), `POLICY_A` (`_GPOL`,
  `["Grant","Policy"]`), `EXPANDED_A` (`_EXP + "]"`, `_EXP`), `ADMIT_A` (`_ADMIT + ")"`, `_ADMIT`).
  Application scope: `.md/.markdown/.txt` get the full map; `.ts/.tsx` get **only** the question value
  lines of `reflex-decisions.ts` (`redact.py:646-668`); `.json` gets path rules everywhere but instrument
  tokens **only under `question` keys**, via `_sub_json_file` (`:689`) with `SAFE_KEYS` (`:203`) and an
  `_protected` guard (`:682`) that refuses to move `correct`, `sha256`, `*Index`, or any path component
  starting `option`/`choice`. `CASE_FIELDS = ("question",)` (`:208`). **Option labels are never
  substituted.** Confirmed empirically: `routeA.ties` = **120** in both the shipped and the regenerated
  `second-labeller/metrics.json` — it did **not** move to 119.
- **The eval**: `cases.json`/`metrics.json` are regenerated by re-running the shipped readers and agree;
  only the *result archives* (`eval/results/*.json`, 40 lines) still carry the raw labels, which is the
  irreducible residue of section 2.

**Consequence for the ruling:** substitution alone cannot make the build exit 0. Clearing the last 62
lines requires either (a) substituting option labels — which changes `routeA.ties` and therefore a
shipped number, or (b) declaring the label-residue accepted for `code/fixture/`, `code/harness/data/`,
`code/eval/`, and the `REDACTION_REPORT`/`EXCLUDED` pointers. (b) is the only option that preserves
every measured number.
