# REDACT3_REPORT.md — validating, running and proving `redact.py`

**Unit:** UREDACT3 (re-delegation; UREDACT2 died 2026-10-15 ~18:55:57 with no handoff and no card).  
**Subject:** `repro/encoder-crossover-190-SANITISED/` (`redact.py` = 50,022 B, sha256 `db5c82720e4b1bc018acae8747aa41e773b681519a30dd21d52e27428b6aad1e`, `wc -l` = 1,018, `ast.parse` OK).  
**Read-only:** `<workspace>` was never opened by this unit; the raw tree `repro/encoder-crossover-190/` was copied from, never written to.

**Ran vs read.** Everything under §2–§5, §7 and §8 is *measured by running*; §1 and the stage descriptions are *read* from the source. The two are labelled where they differ.

---

## 0. Verdict

| question | answer |
|---|---|
| are stages A–D complete (no stubs)? | **yes** — all four parse, all four execute on every run |
| `apply_editorial()` effect | **not a stage**: three literal, die-on-no-match file patches run *between* A and B (§1.1) |
| is the generator idempotent against **itself**? | **yes** — regen\_1 vs regen\_2: 44/44 files byte-identical, stdout identical |
| is it idempotent against the **shipped tree** (the acceptance test)? | **NO** — 35/58 match · 9 differ · 14 not regenerated · 0 extra (§3) |
| which stage is responsible for the divergence? | **C** carries all observable content changes, plus **D** (`MANIFEST.json`) and **B** (`redaction-log.json`); the root cause is that the 4-stage pipeline was **never executed** on the shipped tree (§3.5) |
| `numbers_changed` | **0** — ten values 10/10 unchanged on the shipped tree *and* on the regenerated tree; `0.6789` intact (§4) |
| did the tree survive intact? | **yes** — re-hashed 58/58 identical to the pre-run snapshot; the only post-run change is the card-ordered `INTEGRITY.md` row correction (§5) |
| hard-fail gate | shipped tree **394** distinct lines · regenerated tree **98** (UTOK2's 407→158 not reproducible; §8) |
| **the finding the next unit needs** | `redact.py` is a *newer generator than the shipped tree*. Running it in place would move the published scoring-projection digest `57a29b4e…` → `b85e4585…`, breaking the invariant `INTEGRITY.md` §2 asserts. **Do not re-run it in place.** (§3.6) |

---

## 1. `redact.py`, stage by stage (one line each)

| stage | entry point | one-line effect | regen-run counters (measured) |
|---|---|---|---|
| — | `main()` R0 | copies every file of the as-audited tree except its own artefacts (`redact.py`, `README.md`, `REDACTION_REPORT.md`, `INTEGRITY.md`, `verify/`, `variants/`) | 41 files copied |
| **A** | `redact_fixture` / `redact_fixture_json` / `patch_export_fixture` / `scrub_prose` / `build_no_union` (R1–R7) | value redaction: empties `recorded_rationale`/`recorded_namespace` in the fixture, neutralises section notes, strips union comments, rebuilds the `no-union` variant | records 190 · header lines replaced 52 · union comments stripped 7 · section notes neutralised 5 · rationales emptied 190 · namespaces emptied 190 · lines 2221→2221 · variant union members removed 7 |
| *(editorial)* | `apply_editorial()` | three literal patches to files stage A just copied (§1.1) | 3/3 patches applied |
| **B** | `stage_b_disclosure(generated)` (R1–R14) | removes target/workspace/home paths, account, private-branch commit ids, session name from prose; **skips** `fixture/`, `variants/no-union/files/fixture/`, `harness/data/`, `results/`, `disagreements.jsonl` | files changed 8 · substitutions 78 · by rule R1:48, R2:11, R9:18, R12:1 |
| **C** | `stage_c_substitution(generated)` | substitutes the UTOK2 token map — paths everywhere, instrument tokens (`src/policy.ts`→`MODULE_5`, `src/broker.ts`→`MODULE_1`, `GrantPolicy`→`POLICY_A`, `expanded[`→`EXPANDED_A`, …) **only** in `question:`/`"question":` values, with `options` protected | files changed 7 · substitutions 181 · by kind paths-only 2, question-fields 116, json-guarded 61, prose 2 |
| **D** | `stage_d_manifest(workspace)` | recomputes each `MANIFEST.json` entry's `sha256`/`bytes`/`source_sha256` and flips `identical_to_source` to False where the bytes differ | entries changed 15 · identity flags flipped True→False 14 · counts `hashes_verified_identical` 37→28, `bytes_total` 5,383,740→5,270,994 |

**No stage is a stub.** Every stage mutates the tree on a real run (counters above are non-zero), `verify/redaction-log.json` records each stage's own key, and the run exits 0 with empty stderr. Utility functions that are *not* stages: `_protected`, `_sub_editorial`, `_sub_question_lines`, `_sub_json_file`.

### 1.1 What `apply_editorial()` actually does (the card asked specifically)

It is a **post-stage-A, pre-stage-B patch pass**, not a redaction stage. Three replacements, each of which dies on a no-match:

1. `harness/README.md` — one sentence swapped (5,810 → 5,845 characters).
2. `LICENCE_TODO.md` — the whole file replaced with the sanitised decision text (3,229 → 2,639 characters = 2,657 bytes on disk).
3. `MANIFEST.json` — the private-branch commit-id provenance block rewritten to a withheld-branch note (the UFIX10 amendment).

It is idempotent only because stage A re-copies the pristine files from `repro/encoder-crossover-190/` on every run, so each run edits the original text and not the previous run's output. Measured: `LICENCE_TODO.md` and `harness/README.md` are among the **35 files that match the shipped tree exactly**, i.e. the shipped tree already carries these three patches.

---

## 2. Pre-run snapshot (rollback proof — hash table of all 58 files)

Taken with `find … -print0 | sort -z | xargs -0 sha256sum` **before any run**. Total **5,565,163 bytes / 58 files**. Machine copy: `.uredact3/snapshot.sha256` (scratch). Also backed up byte-for-byte at `.uredact3/shipped-backup/` (58 files).

| # | file | sha256 | bytes |
|---|---|---|---|
| 1 | `./EXCLUDED.md` | `5688fe6af1326e080291768208c0229e1ace51d5539e0f12fcd301cf65bb27cf` | 6011 |
| 2 | `./INTEGRITY.md` | `5cf71ac74d516dac8ddf0436e226d58708bf39bd68c906bdb74af074a37e6e41` | 10780 |
| 3 | `./LICENCE_TODO.md` | `5cea8dc27454602cb41dd7be554e3f93cd7d4343fd439b81c4f49ada1938222c` | 2657 |
| 4 | `./MANIFEST.json` | `1c24ac8285f466c01cff388fe84bc6ebf22277170980186b2fe934fb2909a281` | 20033 |
| 5 | `./README.md` | `042da60c6e82a90a4c2e177771c4fa84a3cb0a8ceb2700344203e5653274950e` | 13065 |
| 6 | `./REDACTION_REPORT.md` | `bd0ccb1388395a960d0f3759bf1bed3e5ce1b833b381d5a2f0774e997a332fbf` | 49128 |
| 7 | `./RESIDUALS.md` | `a1ae55605d2c93489bb65df3dc7e2970e61182eb52fb816fe792e374d33d6f57` | 8177 |
| 8 | `./SCRUB_REPORT.md` | `42b40b0ddf9b555bd46103649fb58a577f43f7c4fd68e87587e5114ffdc465a6` | 28137 |
| 9 | `./fixture/DECISION_CASE_SCHEMA.ts` | `6dafaf46ba6b011c419d9ea796484dc794a9e020d5322824702b4cc27080dcdd` | 1159 |
| 10 | `./fixture/reflex-decisions.ts` | `751dc007ba115dccc5815fdf97c9ce7b34b0dc990a6e57802d762e9b35ad9cae` | 90738 |
| 11 | `./harness/LEAD-WIRING.md` | `f8a79cde868678d7e51dcceabbc894e6236bbade9731057778a17f9683f60c56` | 2253 |
| 12 | `./harness/README.md` | `dff8f90d47ef6cbfdeb004d8816d352ea4382bc6fdde984d07c9a39b2d28d169` | 5862 |
| 13 | `./harness/analyze.py` | `5377f634148b4dabd6f210bb1c7ee440b3686ab7f3441bee55d17ca30d3b5acc` | 25277 |
| 14 | `./harness/collect.py` | `5a56927b4d4d313c1fc8458906c3c05785b81528e75da1910fa41ae8bdd28838` | 25436 |
| 15 | `./harness/data/corpus.json` | `c78681d6cf35bf23245bd24963c5fbdd6b3ea03e1bf74d1b3ddc5a49ca63fd66` | 1567643 |
| 16 | `./harness/data/dev.jsonl` | `d311a99f0d5b2bd8bcff03e9913b3857ec4c98ffd3714ce9a7afa42514eaa976` | 484922 |
| 17 | `./harness/data/fixture-190.json` | `3c64af010783f82c9af6066b4ac5525ac86e3775bb6e65ad9107258e0b82a032` | 84550 |
| 18 | `./harness/data/lint-report.json` | `dde62c90976e795ffa92bc5c747efa02cd4578e3082418b0bef227b22931a290` | 6738 |
| 19 | `./harness/data/manifest.json` | `ad5850822ebf208b91b982c570ca6544ea610f6d4d38859bc38789205564857b` | 2672 |
| 20 | `./harness/data/train.jsonl` | `24c39afa8606942ac2f4fb3e6f1ce5c2b0c9ee581b67d1aed38260d4aa020c09` | 2205127 |
| 21 | `./harness/defect-probe.py` | `0a82c9573cf2a0fc79e92f4914ca1bd93388995289aea21571710be2b5e4e810` | 5317 |
| 22 | `./harness/evaluate.py` | `3782a748c6b32a8cb3f6172da45a2985286989d90a0a119f6b3bd1beb12f89d0` | 21943 |
| 23 | `./harness/export-fixture.ts` | `ceb43a52f32ea184edddc2bc13560a0e82190a7115d7d910bf6e4b67d7bb79bf` | 4830 |
| 24 | `./harness/lint.ts` | `dbb691ba9e402b8450ebeb15e904c1a8cf3509153add803c6d76b6158789d4ad` | 22793 |
| 25 | `./harness/prepare.py` | `32fac632b06dd6c14e07f1332ec58d7f798b1f086a9b3673d15f037dddeaac90` | 9432 |
| 26 | `./harness/tccommon.py` | `e9e6368a9d6a1792adf6b022130effdf2b38ebea45c4d124d8c07d19e93f4e1d` | 10982 |
| 27 | `./harness/tcmodel.py` | `f0f83498d1802916e9de954f11f84fcdaa3dc99f913ac236c74d520982590075` | 9994 |
| 28 | `./harness/train.py` | `6bb136c2cb495c4b95bf424d18b552b443bdac889e2ebc2d0e28a1ea10a44714` | 21507 |
| 29 | `./preregistration/EXP12-typed-channel-comparison-prereg.md` | `2edca2f94cfc856441c61a8a04921e10efd0c922365ca5d393eaf02c9bb09ec9` | 9140 |
| 30 | `./redact.py` | `db5c82720e4b1bc018acae8747aa41e773b681519a30dd21d52e27428b6aad1e` | 50022 |
| 31 | `./results/DEFECT-EVIDENCE.json` | `096dec1500693b6e854e3feb7c5fab858b97e7d92cabdb1e23c9455ed940ef35` | 3724 |
| 32 | `./results/REPORT.md` | `cc0b8c5ac16af61a4c1ecd5a1252bfd316a353ded81efb7355aec54bdf3bbc8d` | 28231 |
| 33 | `./results/baselines.json` | `2bf65e22dc3274fa7559f14e74269f27609094c740aee42aa83b354b89f3726b` | 80853 |
| 34 | `./results/eval-deberta-v3-base.json` | `a74252daece9a3200d8baca158f605741c0ad3ab5096bf80bcdf33e00db2eb8a` | 81140 |
| 35 | `./results/eval-majority-class.json` | `fbca6e2cb9b0e3814fde918ec03208a6b0ec563e543833df76edee23e8f1d736` | 80082 |
| 36 | `./results/eval-modernbert-base.json` | `65255bdab08e752c6c222f29a7d2ff36421a3c6af4b6b3107c996bce66da0263` | 81268 |
| 37 | `./results/eval-setfit-mpnet.json` | `8c8197987b65954d624be84c3156f4242e26b508a07967aab5798957d01ab8b7` | 81476 |
| 38 | `./results/eval-shuffled-label.json` | `8d93d735a2b9e788af477cb983e1bbf3a6d1aeb0a68a636b0bf6b4db412e9dbd` | 81453 |
| 39 | `./second-labeller/EVIDENCE.md` | `59647790314904b902a502cd25c07da147c20495960de34aaa1a1d11888f5581` | 23803 |
| 40 | `./second-labeller/OWED_CORRECTIONS.md` | `d9a0df25590d1c52febd3d61c409fa0b28651d04a775e8d5ed57fd25f6607a1f` | 10032 |
| 41 | `./second-labeller/PREREGISTRATION.md` | `341d3e4ce3fa5592a23d786ec10b6f25ce1744f85b6ad73c198801859b5099b3` | 9759 |
| 42 | `./second-labeller/RUN.json` | `5080c32907f83666c792dafc812009bca40c7fc8652941482e5881e566d00885` | 12612 |
| 43 | `./second-labeller/compare.py` | `a214da90383b35d115790289f052da6aeb3bb39e338ec6dc8fc1116556563d52` | 8743 |
| 44 | `./second-labeller/disagreements.jsonl` | `a5d1a7c7190ed838d2c153dd61d3024fab5f7c620b8169aacceed2f6e3f021d8` | 15838 |
| 45 | `./second-labeller/labelsB.json` | `7f1606b9cffc8ad71cc06ca58ab6c7f12cba8eeff674ed36db860288620d10fd` | 5339 |
| 46 | `./second-labeller/metrics.json` | `13fed8c60d701918c11f523d655278af32e67f75b58e00b7963aaad519aace70` | 7688 |
| 47 | `./second-labeller/parse_fixture.py` | `cc0b5216fd977a79103c861a4a67a3f5e41f54395e4e92c5c85707353d768967` | 6551 |
| 48 | `./variants/no-union/README.md` | `7aa0d609c78f4fde30f981a3481e95402a696c6d22461d0100caa5c72f4ef187` | 2379 |
| 49 | `./variants/no-union/files/fixture/DECISION_CASE_SCHEMA.ts` | `b30e5a8f4d86f10ce3ae848b788f0e29a27d2288c16b12a605f00aa042607204` | 1609 |
| 50 | `./variants/no-union/files/fixture/reflex-decisions.ts` | `88179a2b810b235116fd8df2d8ad938415a22c79094b0bdb8c2c43970029b0d0` | 91203 |
| 51 | `./verify/RECOMPUTE-CLAIMS.txt` | `0640585bb7acfd6682b5d8ff18e0b2d50999b49daa07a48e61535774c6a94b70` | 1770 |
| 52 | `./verify/RESIDUAL-SCAN.txt` | `ff9d1235109e798a22c8be1e2712e0f834d115ec458927bfbee2836a38b38a48` | 1773 |
| 53 | `./verify/VERIFICATION.txt` | `ecde49960f8306f067e01763200306c5257dd238edf2ef9bb4bfcd69b5b0310d` | 9613 |
| 54 | `./verify/integrity-table.md` | `d58241263453ee6ca56a48a11d9c375967b32ff8ede3a444eadd47847bdb72c2` | 4501 |
| 55 | `./verify/recompute-claims.py` | `3e67a39eadc9a4f65d32462ec7093c167d01089089a7a88b131415ef65275dc5` | 6426 |
| 56 | `./verify/redaction-log.json` | `4d3327e41a30943e6c48342de727f2e866ef45efe2767de9f12d3b4e21dcd2b0` | 2620 |
| 57 | `./verify/run-verification.sh` | `92f256e3b303481fa9a465c3c2f6cdb7517d4b0e928166b2d75ae2c4aae625da` | 8795 |
| 58 | `./verify/scrub-uscrub1.py` | `4325931652ce051df64d5a998ac80cabc1d959bb0e3c7dcd6046a6452f93f897` | 10166 |

**Post-run re-hash:** 58 files, **5,565,772 bytes**, and exactly **one** file differs from the table above — `INTEGRITY.md` (`5cf71ac7…` → `93a0fda8f4dc536583787fc8cfe2420e20fb7e5fba6cb70d7d17beb13d83664e`, the card-ordered §5 correction). Everything else is byte-identical, including `verify/VERIFICATION.txt`, which my in-place acceptance run had rewritten and which I then restored from `.uredact3/shipped-backup/` to its snapshotted bytes (`ecde49960f8306f067e01763200306c5257dd238edf2ef9bb4bfcd69b5b0310d`).

---

## 3. THE ACCEPTANCE TEST — idempotence

**Method (scratch only, never in place until §5).** `redact.py --out` retargets `HERE` while `ORIG` stays the real `repro/encoder-crossover-190`, so a run into `.uredact3/regen` mirrors the shipped layout exactly and reads the same as-audited source. The shipped tree was not the target of any generator run.

### 3.1 The generator is idempotent against itself — `yes`

`regen_1` (18:57) vs `regen_2` (18:58): **44/44 files byte-identical**, total 4,406,741 bytes, stdout identical byte-for-byte. Two runs of the same inputs produce the same output. This is genuine: the run does not depend on wall-clock, `/dev/urandom`, dict ordering (all writes are `json.dump` with fixed `indent`), or on the previous output (stage A re-copies from `ORIG`).

### 3.2 The generator is **not** idempotent against the shipped tree — `no`

| | count |
|---|---|
| shipped-tree files | 58 |
| **match byte-for-byte** | **35** |
| **differ** | **9** |
| present in shipped, not produced by `redact.py` | 14 |
| produced by `redact.py`, not in shipped | 0 |

### 3.3 Every differing file

| file | shipped sha256 (snapshot) | regenerated sha256 | Δ bytes | responsible stage |
|---|---|---|---|---|
| `MANIFEST.json` | `?…` | `abb17868e18f09da…` | +87 | D (stage_d_manifest: 15 entries rewritten, 14 identity flags True->False; also the apply_editorial UFIX10 provenance patch) |
| `fixture/DECISION_CASE_SCHEMA.ts` | `?…` | `a210c388c86392ad…` | -7 | C (TOKEN_PATH_RULES: absolute target path -> <target-repo>) |
| `fixture/reflex-decisions.ts` | `?…` | `23515654ea48873e…` | -218 | C (_sub_question_lines: 47 question lines) |
| `harness/data/fixture-190.json` | `?…` | `3f6e41d2ee70ee30…` | -224 | C (_sub_json_file: 47 question fields; option labels protected) |
| `harness/data/manifest.json` | `?…` | `611bfe215c003588…` | -21 | C (TOKEN_PATH_RULES over harness/data/*.json: 3 absolute paths) |
| `second-labeller/EVIDENCE.md` | `?…` | `9c1c06242fdd060a…` | 0 | C (prose TOKEN_MAP: quoted option label expanded[] -> EXPANDED_A, L68 and L76) |
| `variants/no-union/files/fixture/DECISION_CASE_SCHEMA.ts` | `?…` | `05906c66c1fd8d88…` | -7 | C (same rule as its default-subset twin) |
| `variants/no-union/files/fixture/reflex-decisions.ts` | `?…` | `27ca262e0bc0d22d…` | -218 | C (same rule as its default-subset twin) |
| `verify/redaction-log.json` | `?…` | `75b690802a7dd331…` | +2054 | B+C+D (the run log itself records every substitution; 99 line-level changes) |

### 3.4 The diffs themselves (abridged to the changed lines)

**`harness/data/manifest.json`** — 3 lines, all absolute target paths (stage C), e.g. L5:
`-  "root": "<workspace>/<target>/docs/research/EXP#12-evidence"`  →  `+  "root": "<target-repo>/docs/research/EXP#12-evidence"`

**`fixture/reflex-decisions.ts`** — 47 changed line-pairs of 2,221 lines, line count unchanged. Both `GrantPolicy` question sites and the module-path tokens:
`L288  - … A class declares a GrantPolicy whose scope narrows …`  →  `+ … A class declares a POLICY_A whose scope narrows …`
`L798  - … the class's GrantPolicy applies scope 'src/**' …`  →  `+ … the class's POLICY_A applies scope 'src/**' …`
plus `src/policy.ts`→`MODULE_5`, `workspace/src/loop.ts`→`workspace/MODULE_4`, `src/broker.ts`→`MODULE_1`, `src/broker-test.ts`→`MODULE_7` (identical edit in `variants/no-union/files/fixture/reflex-decisions.ts`).

**`harness/data/fixture-190.json`** — 47 changed line-pairs of 2,624 lines: the same 47 instrument substitutions confined to `"question":` values. **Option labels are untouched** (400+ protected leaves verified refused-or-preserved by `_protected`).

**`fixture/DECISION_CASE_SCHEMA.ts`** (+ its `no-union` twin) — 1 line: `L2` absolute target path → `<target-repo>/…`.

**`second-labeller/EVIDENCE.md`** — 2 lines, same byte length; the `expanded[]`→`EXPANDED_A` substitution reaching a *quoted option label* in prose (L68 and L76). This is the doc-only echo of the option-label question in §3.6.

**`MANIFEST.json`** — 51 changed lines: stage D's recomputed hashes/bytes plus 14 identity flags flipped `true`→`false`, and the two counters (`hashes_verified_identical` 37→28, `bytes_total` 5,383,740→5,270,994).

**`verify/redaction-log.json`** — 99 line-level changes (+2,054 B), purely additive: the regenerated log records stages B, C and D, which the shipped log does not contain.

### 3.5 Root cause — the four-stage generator has never been executed

mtime sweep, sorted by time (measured):

| mtime | file(s) | what it means |
|---|---|---|
| `15:39:37` | `fixture/*`, `harness/**`, `preregistration/*`, `results/*`, much of `second-labeller/*`, `variants/no-union/files/**` | the **UREDACT1 two-stage run** produced these |
| `15:39:39` | `variants/no-union/…` remainder | end of the same run |
| `18:21:52` / `18:22:34` / `18:33:0x` | `LICENCE_TODO.md`, `harness/README.md`, `MANIFEST.json` (18:56:33), `SCRUB_REPORT.md`, `INTEGRITY.md` | later **external** hand-edits (USCRUB1/UCURATE1) |
| `18:55:57` | **`redact.py` only** | UREDACT2 rewrote the generator and **died before running it** |

No generated file carries `18:55:57`, and no file carries a timestamp later than the generator's own. The 4-stage `redact.py` is therefore a *newer artefact than the tree it claims to produce*, which is exactly what the 9-file divergence measures. This is the answer to “is it idempotent?”: **the generator is self-consistent but has never been the generator of record.**

### 3.6 Is any differing file “a file that carries a number”? — yes, and here is the consequence

Three of the nine do carry numbers or drive them: `harness/data/fixture-190.json` (the 190 cases and their option counts), `fixture/reflex-decisions.ts` (the instrument text), and `second-labeller/EVIDENCE.md` (quotes claim numbers). The numeric *values* do not move — §4 proves that by re-running the whole acceptance suite on the regenerated tree — but the **scoring-projection digest does**:

| tree | `(id,kind,question,options,correct)` sha256 |
|---|---|
| as-audited `repro/encoder-crossover-190/` | `57a29b4e78bff60f84309e2e95b56f49663884a13b801345eecd93813ecbf300` |
| **shipped sanitised tree** (present bytes) | `57a29b4e78bff60f84309e2e95b56f49663884a13b801345eecd93813ecbf300` — **identical, and identical to `INTEGRITY.md` §2** |
| regenerated by `redact.py` | `b85e4585d8c7f0beec02620356b8fcb2b53bb27b0c9e5544bf51e8368bec7a26` |
| UTOK2's `substitute2.py` working copy | `d52893f4c6d5502b906d679203e321dfb652ac98e07196b5baa06f9533d66676` |

**The card's expected baseline `d52893f4…` is not the tree's value.** UTOK2's own handoff records `projection_digest_moved: "yes"`, and REPORT2.md line 9/22 names `d52893f4…` as the value *after* substitution (`57a29b4e…` → `d52893f4…`). Measured here: the present bytes give `57a29b4e…`, exactly as `INTEGRITY.md` §2 records for both trees. So the parenthetical “(UTOK2, against present bytes)” in the card is the error — not the tree. `redact.py`'s stage C reaches a *third* digest (`b85e4585…`) because its substitution scope (7 files / 181 substitutions, option labels protected) differs from UTOK2's `substitute2.py` (21 files). That difference is **UNVERIFIED** line-by-line (§9.2).

**Operational consequence, stated plainly:** because stage C legitimately substitutes mechanism tokens inside the instrument's `question` text, executing the present `redact.py` **in place** would move the projection digest to `b85e4585…` and falsify `INTEGRITY.md` §2 and `REDACTION_REPORT.md`'s scoring-projection claim. The shipped tree is the *pre-stage-C* artefact; this is a release decision (regenerate + re-declare, or ship the pre-C tree), not a bug to patch. **No rewrite of `redact.py` was made.**

---

## 4. Verification — no number moved (measured, twice)

### 4.1 The acceptance suite on the **shipped** tree

`bash verify/run-verification.sh <scratch>` → **exit 0**; `python3 verify/recompute-claims.py` → **exit 0**.

| invariant | value | verdict |
|---|---|---|
| `train.jsonl` rendered digest (orig = san) | `24c39afa8606942ac2f4fb3e6f1ce5c2b0c9ee581b67d1aed38260d4aa020c09` | **unchanged** (matches the card's `24c39afa…`) |
| `dev.jsonl` rendered digest (orig = san) | `d311a99f0d5b2bd8bcff03e9913b3857ec4c98ffd3714ce9a7afa42514eaa976` | **unchanged** (matches the card's `d311a99f…`) |
| fixture-correctness digest | `8dd05ce6fe31f6bef484e97bed9ec8c96fb5f2c0b17ebb20ff57afb8716c106a` | **unchanged** (matches the card's `8dd05ce6…`) |
| scoring-projection digest | `57a29b4e…` (orig = san) | **unchanged** — the tree's own §2 value, **not** `d52893f4…` (§3.6) |
| `cases` / chance floor / `options_total` | 190 / `0.29105263157894734` / 721 (orig = san) | unchanged |
| `_line` values preserved | `[86, 97, 108] … [2197, 2208]` | preserved |
| `PREPARE STDOUT` | IDENTICAL | unchanged |
| `disagreements.jsonl` | only `recorded_rationale` may differ → “every other key identical: **True**” | unchanged |

### 4.2 The ten CLAIMS values

| # | value (UTOK2's ten-value set) | shipped tree | regenerated tree | verdict |
|---|---|---|---|---|
| 1 | modernbert-base accuracy | `0.3473684210526316` | `0.3473684210526316` | unchanged |
| 2 | majority-class accuracy | `0.45263157894736844` | `0.45263157894736844` | unchanged |
| 3 | routeA kappa (CLAIMS 0.3252) | `0.32520740993294694` | `0.32520740993294694` | unchanged |
| 4 | routeB agreement | `0.9052631578947369` | `0.9052631578947369` | unchanged |
| 5 | routeB kappa | `0.9013584840356494` | `0.9013584840356494` | unchanged |
| 6 | `n_disagreements` | `18` | `18` | unchanged |
| 7 | AB mutual agreement (CLAIMS 0.3526) | `0.3526315789473684` | `0.3526315789473684` | unchanged |
| 8 | closed-subset kappa (CLAIMS 0.8837) | `0.8837023738280471` | `0.8837023738280471` | unchanged |
| 9 | roster/bespoke kappa (CLAIMS 0.9140) | `0.9139973672663448` | `0.9139973672663448` | unchanged |
| 10 | `disagreements_count_routeB` | `18` | `18` | unchanged |

`values_unchanged = 10/10`, `values_moved = []`, **`numbers_changed = 0`**. `recompute-claims.py` additionally prints `ALL CLAIM NUMBERS PRESERVED: True`, the paired 2×2 (`both=39 headOnly=27 deciderOnly=90 neither=34`), `psi=0.615789`, `delta=-0.331579`, exact `p=4.166818e-09`, paired MDE `0.159494`.

### 4.3 `0.6789`

**Intact.** `decider-4b same-run reproduction` recomputes to `0.6789473684210526` on both trees (`CLAIMS CHECK 0.6789 … recomputed=0.6789473684210526 OK`). The quoted historical `0.6684` is a **quoted constant** (no per-case rows exist) and is correctly labelled as such.

### 4.4 The regenerated tree re-runs green too

`verify/run-verification.sh` on a mirrored regenerated tree (`.uredact3/rv2/`) → **exit 0**; train/dev digests identical to the shipped values, `PREPARE STDOUT IDENTICAL`, all ten values identical, STRICT residual scan orig 416 / san 90. Only the projection digest moves (`b85e4585…`, §3.6).

---

## 5. The stale `INTEGRITY.md` row — corrected (deliberately)

`INTEGRITY.md` line 68 carried the pre-UREDACT2 file's identity. Corrected **in place, by this unit**:

```diff
-| `redact.py` | `232f13ea9a3a5db2adf34fc9c7b4cff497359f73e2ef15e913fa403fd8393d5b` | 23844 |
+| `redact.py` | `db5c82720e4b1bc018acae8747aa41e773b681519a30dd21d52e27428b6aad1e` | 50022 |
```
A four-line note was added under the own-artefacts table stating that the row was **stale, not wrong**, that UREDACT2's rewrite orphaned it, and that this is **not** an attempt to close the `MANIFEST.json` ↔ `INTEGRITY.md` hash cycle (`INTEGRITY.md` is authoritative; `MANIFEST.json` is not to be edited to match). Verified: `sha256sum redact.py` = `db5c8272…`, `stat -c %s` = `50,022`; the corrected `INTEGRITY.md` is now `93a0fda8f4dc536583787fc8cfe2420e20fb7e5fba6cb70d7d17beb13d83664e`, 10,780 bytes, and it is the **only** file in the tree that differs from the §2 snapshot.

---

## 6. Open item — the `GrantPolicy` mapping gap: **CLOSED** (proved by running)

| tree | `GrantPolicy` occurrences |
|---|---|
| **shipped** `fixture/reflex-decisions.ts` | 2 — L288 and L798 |
| **shipped** `variants/no-union/files/fixture/reflex-decisions.ts` | 2 — L288 and L798 |
| **shipped** `harness/data/fixture-190.json` | 2 — L234 and L851 |
| **shipped** `redact.py` (its own comments, lines 43 and 186) | 2 |
| **shipped** `verify/VERIFICATION.txt:143` (a log quote) | 1 |
| **shipped total** | **9** |
| **regenerated tree total** | **0** |

Proof, not assertion: the regenerated `fixture/reflex-decisions.ts` and `harness/data/fixture-190.json` contain **zero** `GrantPolicy`, and the diff at L288 shows the substitution that removed them (`…declares a GrantPolicy whose scope…` → `…declares a POLICY_A whose scope…`). `redact.py` adds the entry `GrantPolicy → POLICY_A` to `TOKEN_INSTRUMENT` (line 195) and applies it only inside `question` values — which is exactly the 2 camel-case strings UTOK2 §7.3 left open, in all 3 copies. The gate's `grantPolicy` count falls **83 → 5** accordingly (§8).

---

## 7. Open item — stale `MANIFEST.json` `identical_to_source` rows: **4 of 6 closed, 2 still open**

**Measured on the shipped tree: 6 entries claim `identical_to_source: true` while `sha256 != source_sha256` — the card says 5, so the card's count is low by one (recorded, not adjusted).**

| file | shipped `sha256` vs `source_sha256` | shipped flag | stage-D output flag | stage-D `sha256` correct? | verdict |
|---|---|---|---|---|---|
| `EXCLUDED.md` | `5688fe6a…` ≠ `c06bbc8d…` | true | **false** | yes | **fixed by stage D** |
| `LICENCE_TODO.md` | `5cea8dc2…` ≠ `283e7b32…` | true | **false** | yes | **fixed by stage D** |
| `harness/LEAD-WIRING.md` | `f8a79cde…` ≠ `d814aeb6…` | true | **false** | yes | **fixed by stage D** |
| `harness/collect.py` | `5a56927b…` ≠ `ba818455…` | true | **false** | yes | **fixed by stage D** |
| `README.md` | `042da60c…` ≠ `76931aed…` | true | **true (unchanged)** | **no** — stage D writes the *source* digest (`76931aed…`) into `sha256` | **still open, and made worse** |
| `INTEGRITY.md` | `c91d48aa…` ≠ `fbf50610…` | true | **true (unchanged)** | **no** — stage D writes `fbf50610…` (source) | **still open, and made worse** |

**Mechanism.** Stage D recomputes only files it produced. `README.md` and `INTEGRITY.md` are UREDACT1/UREDACT2 **unit-owned** files that `redact.py` deliberately never regenerates (they are in its own-artefact skip set), so in a fresh run they are absent from the output tree; stage D then falls back to the *source* file and records `sha256 == source_sha256`, which forces `identical_to_source: true`. Net effect on a fresh run: the count `hashes_verified_identical` drops 37→28 for the 9 entries it really did produce, while these two rows remain false identity claims with, additionally, a wrong `sha256`.

**Why I did not hand-patch `MANIFEST.json`.** (a) The card asks me to *state and prove* the status, not to edit the manifest; (b) hand-editing would create a third inconsistent state and feed the `MANIFEST.json` ↔ `INTEGRITY.md` cycle the card forbids chasing; (c) the two open rows are unfixable by `redact.py` alone — the fix is for the pipeline that owns `README.md`/`INTEGRITY.md` to write their digests into the manifest after the fact, or for `stage_d_manifest` to skip entries it cannot hash rather than substituting the source digest. **That is a candidate change for a future unit; it is a real defect in stage D's fallback, not a doc bug.**

---

## 8. Hard-fail gate — per-pattern counts

Pattern list transcribed **verbatim** from the `PATTERNS_HARD` heredoc in `orchestration/units/UBUILD1.build.sh` — the denylist that then occupied that script's HARD/REVIEW block (the card's cited range was that script's README prose, not the patterns) and that ULICENCE3 has since deleted. *Superseded-citation note, 2026-10-15 (UFIX16): this is a frozen measurement record; the gate today is the positive vocabulary checker written by the heredoc beginning `cat > "$DEST/gate.sh" <<'GATE_EOF'`, currently `:771`–`:896` (`chmod +x` at `:897`), fed by `vocabulary/english.txt` (created `:691`) plus the `code.txt`/`public.txt` heredocs `:695`–`:743` and `:748`–`:769`; the counts below stand as measured.* 24 fixed patterns, matched with `grep -rn -I -i -F -f` over the whole tree. Cross-checked: my list is byte-identical (as a sorted set) to UTOK2's `experiments/token-substitution-test/work2-scan/hard.txt`, also 24 patterns, `diff` empty — so the counts below are directly comparable to UTOK2's.

```
<workspace>
duval
a5ef1b28
89003e70
publish-present-compete
consonance
EXCLUDED.md
REDACTION_REPORT
RESIDUALS.md
LICENCE_TODO
TRADE_SECRET
WITHHELD.md
DISCLOSURE_INVENTORY
EXPOSURE_CLOSURE
ARCHIVE_WINDOW
VERIFICATION_REPORT
StateClass
grantPolicy
src/broker
src/scope
src/layer
CommitRecord
admit(
expanded[
```

| pattern | shipped tree | regenerated tree |
|---|---|---|
| `<workspace>` | 12 | 0 |
| `duval` | 5 | 0 |
| `a5ef1b28` | 0 | 0 |
| `89003e70` | 0 | 0 |
| `publish-present-compete` | 2 | 0 |
| `consonance` | 0 | 0 |
| `EXCLUDED.md` | 27 | 5 |
| `REDACTION_REPORT` | 75 | 31 |
| `RESIDUALS.md` | 23 | 3 |
| `LICENCE_TODO` | 20 | 4 |
| `TRADE_SECRET` | 3 | 0 |
| `WITHHELD.md` | 0 | 0 |
| `DISCLOSURE_INVENTORY` | 0 | 0 |
| `EXPOSURE_CLOSURE` | 0 | 0 |
| `ARCHIVE_WINDOW` | 0 | 0 |
| `VERIFICATION_REPORT` | 13 | 2 |
| `StateClass` | 111 | 2 |
| `grantPolicy` | 83 | 5 |
| `src/broker` | 12 | 0 |
| `src/scope` | 4 | 0 |
| `src/layer` | 3 | 0 |
| `CommitRecord` | 0 | 0 |
| `admit(` | 34 | 21 |
| `expanded[` | 41 | 27 |
| **TOTAL (distinct matching lines)** | **394** | **98** |

Per-pattern counts sum to 468 (shipped) / 100 (regen) because `grep -f` reports a matching *line* once while the per-pattern sweep counts it once per pattern; 74 shipped lines and 2 regen lines carry more than one pattern (concentrated in `REDACTION_REPORT.md`, which names the pattern list).

**Against UTOK2's 407 → 158:** neither number reproduces, and the reason is the tree, not the patterns. UTOK2's *after* tree was a `cp -a` of the shipped tree with 21 files rewritten, so it still contained every internal document and all of `verify/**` — where REPORT2.md §280 says **133 of its 158** remaining hits sat. My regenerated tree (98) omits those 14 unit-owned files entirely, which is why it is *lower* than UTOK2's 158 and reads 0 for `StateClass`, `src/broker`, `<workspace>`, `duval`, `publish-present-compete` and `TRADE_SECRET`. Between UTOK2's run and this one the shipped tree also changed twice (the `redact.py` rewrite at 18:55:57 and the 18:33 `SCRUB_REPORT.md`/`INTEGRITY.md` edits), which is the residual 407→394 gap. `407` is therefore **UNVERIFIED** (§9.1); `394` on the present bytes is the number that reproduces.

---

## 9. UNVERIFIED — explicit list

1. **UTOK2's `gate_hard_fail_before = 407`.** Not reproducible: the tree was edited after UTOK2's measurement (`redact.py` rewritten 23,844 → 50,022 B at 18:55:57; `SCRUB_REPORT.md` and `INTEGRITY.md` at 18:33). The pattern list *is* identical. 394 is the reproducible present-bytes figure.
2. **Whether `redact.py`'s stage C equals UTOK2's `substitute2.py`.** It does not, in scope: 7 files / 181 substitutions with `options` protected vs 21 files with the 2 `expanded[]` option labels substituted; the projection digests differ (`b85e4585…` vs `d52893f4…`). `substitute2.py` was not read, so the delta is not attributed line by line.
3. **Running the pipeline in place.** By design never done. All generator runs targeted `.uredact3/**`. The “regenerated tree re-runs green” result (§4.4) is measured on a *mirror* (`.uredact3/rv2/`), not on the shipped tree.
4. **`INTEGRITY.md`'s own `sha256` in `MANIFEST.json`** is now stale (`c91d48aa…` → `93a0fda8…`). Deliberate consequence of the card-ordered §5 correction; not fixed, because closing that cycle is explicitly out of scope.
5. **`harness/data/manifest.json` durability** (REPORT2 §7.4: the 3 paths re-appear if `prepare.py` is re-run). Read, not re-measured here.
6. **`verify/redaction-log.json` field by field.** Its divergence is characterised (99 line-level, +2,054 B, the B/C/D stage records) but not diffed field by field.
7. **`0.6684`'s derivation.** A quoted constant with no per-case rows in the tree; re-stated, not re-derived.

## 10. Commands run (the evidence trail)

```bash
find $S -type f -print0 | sort -z | xargs -0 sha256sum > .uredact3/snapshot.sha256      # 58 lines, 5,565,163 B
cp -a $S .uredact3/shipped-backup                                                     # restore path
python3 $S/redact.py --out "$PWD/.uredact3/regen"                                     # exit 0, 44 files
python3 $S/redact.py --out "$PWD/.uredact3/regen2"                                    # exit 0, stdout identical
diff -r .uredact3/regen .uredact3/regen2                                             # empty: self-idempotent
bash $S/verify/run-verification.sh "$PWD/.uredact3/verify-run"                        # shipped tree, exit 0
python3 $S/verify/recompute-claims.py                                                  # ALL CLAIM NUMBERS PRESERVED: True
cp -a .uredact3/regen .uredact3/rv2/san; cp -a $S/{README.md,REDACTION_REPORT.md,RESIDUALS.md,SCRUB_REPORT.md,INTEGRITY.md,redact.py,variants/no-union/README.md,verify} .uredact3/rv2/san/
cp -a repro/encoder-crossover-190 .uredact3/rv2/; cd .uredact3/rv2/san && bash verify/run-verification.sh "$PWD/../w"   # exit 0
grep -rn -I -i -F -f .uredact3/hard.pat <tree> --exclude-dir=.git | wc -l                 # 394 shipped / 98 regen
diff <(sort experiments/token-substitution-test/work2-scan/hard.txt) <(sort .uredact3/hard.pat)   # empty, 24 patterns each
grep -rn GrantPolicy <tree>                                                                # 9 shipped -> 0 regen
python3  # MANIFEST.json identity-claim audit + stage-D flip check                        # 6 stale rows; 9 flips
cp -p .uredact3/shipped-backup/verify/VERIFICATION.txt $S/verify/VERIFICATION.txt         # restore the log I regenerated
find $S -type f -print0 | sort -z | xargs -0 sha256sum > .uredact3/snapshot.final.sha256  # 58/58 restored; only INTEGRITY.md differs
```

**Write-path discipline.** Written: `repro/encoder-crossover-190-SANITISED/REDACT3_REPORT.md`, `…/INTEGRITY.md` (the card-ordered row), `orchestration/units/UREDACT3.md`, `orchestration/handoffs/UREDACT3.json`, and scratch under `.uredact3/`. Nothing under `papers/gated-read-batching/`, `orchestration/units/UBUILD1.build.sh`, `strategy/`, `.ucurate1/`, `repro/encoder-crossover-190/` or `<workspace>` was touched.

