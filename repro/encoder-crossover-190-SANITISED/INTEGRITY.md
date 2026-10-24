# INTEGRITY.md — hashes, provenance, and what is unmodified

**Unit:** UREDACT1 · **Written:** 2026-10-15 (UTC) · **Subject:** `repro/encoder-crossover-190-SANITISED/`

This file does two things: it records the sha256 of every file in the sanitised subset so a reader can
tell a modified copy from this one, and it records the evidence that **nothing else was changed** —
neither the as-audited subset it was built from, nor the read-only target repository.

---

## 1. Hashes of the sanitised subset

The files this unit authored (`redact.py`, `README.md`, `REDACTION_REPORT.md`, and — added by the UFIX10 amendment —
`RESIDUALS.md`) are listed at the end. **Re-hashed by UFIX10 after the `strategy/VERIFICATION_REPORT_8.md`
corrections (`README.md`, `REDACTION_REPORT.md`, `MANIFEST.json`, this file, `verify/integrity-table.md`; the
instrument and result files keep the hashes below unchanged).** Everything else is a copy of the as-audited tree with the redactions of
[`REDACTION_REPORT.md`](REDACTION_REPORT.md) §3 applied. **Re-hashed after the UVER5/UVER6 amendment of §10**, so
this table describes the tree as it now stands, not the tree as it was mid-build.

| file | sha256 | bytes |
|---|---|---|
| `EXCLUDED.md` | `5688fe6af1326e080291768208c0229e1ace51d5539e0f12fcd301cf65bb27cf` | 6011 |
| `LICENCE_TODO.md` | `5cea8dc27454602cb41dd7be554e3f93cd7d4343fd439b81c4f49ada1938222c` | 2657 |
| `MANIFEST.json` | `1c24ac8285f466c01cff388fe84bc6ebf22277170980186b2fe934fb2909a281` | 20033 |
| `fixture/DECISION_CASE_SCHEMA.ts` | `6dafaf46ba6b011c419d9ea796484dc794a9e020d5322824702b4cc27080dcdd` | 1159 |
| `fixture/reflex-decisions.ts` | `751dc007ba115dccc5815fdf97c9ce7b34b0dc990a6e57802d762e9b35ad9cae` | 90738 |
| `harness/LEAD-WIRING.md` | `f8a79cde868678d7e51dcceabbc894e6236bbade9731057778a17f9683f60c56` | 2253 |
| `harness/README.md` | `dff8f90d47ef6cbfdeb004d8816d352ea4382bc6fdde984d07c9a39b2d28d169` | 5862 |
| `harness/analyze.py` | `5377f634148b4dabd6f210bb1c7ee440b3686ab7f3441bee55d17ca30d3b5acc` | 25277 |
| `harness/collect.py` | `5a56927b4d4d313c1fc8458906c3c05785b81528e75da1910fa41ae8bdd28838` | 25436 |
| `harness/defect-probe.py` | `0a82c9573cf2a0fc79e92f4914ca1bd93388995289aea21571710be2b5e4e810` | 5317 |
| `harness/evaluate.py` | `3782a748c6b32a8cb3f6172da45a2985286989d90a0a119f6b3bd1beb12f89d0` | 21943 |
| `harness/export-fixture.ts` | `ceb43a52f32ea184edddc2bc13560a0e82190a7115d7d910bf6e4b67d7bb79bf` | 4830 |
| `harness/lint.ts` | `dbb691ba9e402b8450ebeb15e904c1a8cf3509153add803c6d76b6158789d4ad` | 22793 |
| `harness/prepare.py` | `32fac632b06dd6c14e07f1332ec58d7f798b1f086a9b3673d15f037dddeaac90` | 9432 |
| `harness/tccommon.py` | `e9e6368a9d6a1792adf6b022130effdf2b38ebea45c4d124d8c07d19e93f4e1d` | 10982 |
| `harness/tcmodel.py` | `f0f83498d1802916e9de954f11f84fcdaa3dc99f913ac236c74d520982590075` | 9994 |
| `harness/train.py` | `6bb136c2cb495c4b95bf424d18b552b443bdac889e2ebc2d0e28a1ea10a44714` | 21507 |
| `harness/data/corpus.json` | `c78681d6cf35bf23245bd24963c5fbdd6b3ea03e1bf74d1b3ddc5a49ca63fd66` | 1567643 |
| `harness/data/dev.jsonl` | `d311a99f0d5b2bd8bcff03e9913b3857ec4c98ffd3714ce9a7afa42514eaa976` | 484922 |
| `harness/data/fixture-190.json` | `3c64af010783f82c9af6066b4ac5525ac86e3775bb6e65ad9107258e0b82a032` | 84550 |
| `harness/data/lint-report.json` | `dde62c90976e795ffa92bc5c747efa02cd4578e3082418b0bef227b22931a290` | 6738 |
| `harness/data/manifest.json` | `ad5850822ebf208b91b982c570ca6544ea610f6d4d38859bc38789205564857b` | 2672 |
| `harness/data/train.jsonl` | `24c39afa8606942ac2f4fb3e6f1ce5c2b0c9ee581b67d1aed38260d4aa020c09` | 2205127 |
| `preregistration/EXP12-typed-channel-comparison-prereg.md` | `2edca2f94cfc856441c61a8a04921e10efd0c922365ca5d393eaf02c9bb09ec9` | 9140 |
| `second-labeller/EVIDENCE.md` | `59647790314904b902a502cd25c07da147c20495960de34aaa1a1d11888f5581` | 23803 |
| `second-labeller/OWED_CORRECTIONS.md` | `d9a0df25590d1c52febd3d61c409fa0b28651d04a775e8d5ed57fd25f6607a1f` | 10032 |
| `second-labeller/PREREGISTRATION.md` | `341d3e4ce3fa5592a23d786ec10b6f25ce1744f85b6ad73c198801859b5099b3` | 9759 |
| `second-labeller/RUN.json` | `5080c32907f83666c792dafc812009bca40c7fc8652941482e5881e566d00885` | 12612 |
| `second-labeller/compare.py` | `a214da90383b35d115790289f052da6aeb3bb39e338ec6dc8fc1116556563d52` | 8743 |
| `second-labeller/disagreements.jsonl` | `a5d1a7c7190ed838d2c153dd61d3024fab5f7c620b8169aacceed2f6e3f021d8` | 15838 |
| `second-labeller/labelsB.json` | `7f1606b9cffc8ad71cc06ca58ab6c7f12cba8eeff674ed36db860288620d10fd` | 5339 |
| `second-labeller/metrics.json` | `13fed8c60d701918c11f523d655278af32e67f75b58e00b7963aaad519aace70` | 7688 |
| `second-labeller/parse_fixture.py` | `cc0b5216fd977a79103c861a4a67a3f5e41f54395e4e92c5c85707353d768967` | 6551 |
| `results/DEFECT-EVIDENCE.json` | `096dec1500693b6e854e3feb7c5fab858b97e7d92cabdb1e23c9455ed940ef35` | 3724 |
| `results/REPORT.md` | `cc0b8c5ac16af61a4c1ecd5a1252bfd316a353ded81efb7355aec54bdf3bbc8d` | 28231 |
| `results/baselines.json` | `2bf65e22dc3274fa7559f14e74269f27609094c740aee42aa83b354b89f3726b` | 80853 |
| `results/eval-deberta-v3-base.json` | `a74252daece9a3200d8baca158f605741c0ad3ab5096bf80bcdf33e00db2eb8a` | 81140 |
| `results/eval-majority-class.json` | `fbca6e2cb9b0e3814fde918ec03208a6b0ec563e543833df76edee23e8f1d736` | 80082 |
| `results/eval-modernbert-base.json` | `65255bdab08e752c6c222f29a7d2ff36421a3c6af4b6b3107c996bce66da0263` | 81268 |
| `results/eval-setfit-mpnet.json` | `8c8197987b65954d624be84c3156f4242e26b508a07967aab5798957d01ab8b7` | 81476 |
| `results/eval-shuffled-label.json` | `8d93d735a2b9e788af477cb983e1bbf3a6d1aeb0a68a636b0bf6b4db412e9dbd` | 81453 |

**This unit's own artefacts.**

| file | sha256 | bytes |
|---|---|---|
| `redact.py` | `db5c82720e4b1bc018acae8747aa41e773b681519a30dd21d52e27428b6aad1e` | 50022 |
| `README.md` | `042da60c6e82a90a4c2e177771c4fa84a3cb0a8ceb2700344203e5653274950e` | 13065 |
| `REDACTION_REPORT.md` | `bd0ccb1388395a960d0f3759bf1bed3e5ce1b833b381d5a2f0774e997a332fbf` | 49128 |
| `RESIDUALS.md` | `a1ae55605d2c93489bb65df3dc7e2970e61182eb52fb816fe792e374d33d6f57` | 8177 |
| `SCRUB_REPORT.md` | `42b40b0ddf9b555bd46103649fb58a577f43f7c4fd68e87587e5114ffdc465a6` | 28137 |

> **`redact.py` row corrected by UREDACT3.** It carried `232f13ea…` / 23844 B — the digest and size of
> the **pre-UREDACT2 two-stage** generator. UREDACT2 rewrote the file into the four-stage A–D generator
> (50022 B) and died before writing any report, leaving this row stale. The row above is the file's
> actual current sha256 and size. This is a **deliberate** correction of a stale record, not an attempt
> to close the `MANIFEST.json` ↔ `INTEGRITY.md` hash cycle: this file is authoritative, and the cycle is
> the known, documented limitation of §5 — do not edit `MANIFEST.json` to match.

`verify/` and `variants/` are excluded from the table above because they are scaffolding and a labelled
alternative, not the published subset. `verify/` holds the runnable acceptance test
(`run-verification.sh`, `recompute-claims.py`) and its verbatim logs; `variants/no-union/` holds the
clearly-labelled alternative to the default subset.

---

## 2. The one hash that had to change, and the hash that did not

| digest | as-audited | sanitised |
|---|---|---|
| `fixture/reflex-decisions.ts` (whole file) | `076164ac53c2c1aac130953345c481f88b51f4d6fb93d465c7430308a99b4796` | `751dc007ba115dccc5815fdf97c9ce7b34b0dc990a6e57802d762e9b35ad9cae` |
| the 190-case **scoring projection** (`id`,`kind`,`question`,`options`,`correct`) | `57a29b4e78bff60f84309e2e95b56f49663884a13b801345eecd93813ecbf300` | `57a29b4e78bff60f84309e2e95b56f49663884a13b801345eecd93813ecbf300` |
| `harness/data/train.jsonl` (rendered, re-run) | `24c39afa8606942ac2f4fb3e6f1ce5c2b0c9ee581b67d1aed38260d4aa020c09` | `24c39afa8606942ac2f4fb3e6f1ce5c2b0c9ee581b67d1aed38260d4aa020c09` |
| `harness/data/dev.jsonl` (rendered, re-run) | `d311a99f0d5b2bd8bcff03e9913b3857ec4c98ffd3714ce9a7afa42514eaa976` | `d311a99f0d5b2bd8bcff03e9913b3857ec4c98ffd3714ce9a7afa42514eaa976` |

The fixture's whole-file digest **must** change: it is the digest of the bytes, and the bytes changed.
That is not a defect to be hidden — it is the reason the pre-registration's identity check can no
longer be run as written, and it is recorded as a reproducibility cost in §5 of the report. What is
asserted instead, and what holds, is the **scoring-projection digest**: the five fields every reported
number depends on are unchanged. The rendered split files re-generate byte-identically to the digests
`LEAD-WIRING.md` recorded before this unit existed.

---

## 3. The as-audited subset is unmodified

`repro/encoder-crossover-190/` was never written to. Proof, not assertion: that subset ships its own
`MANIFEST.json` with a sha256 for each of its 42 entries, and re-verifying all 42 against the files on
disk **after** the redaction build gives:

```
manifest entries: 42
verified unchanged: 42   mismatched: 0   missing: 0
```

The 43rd file on disk is `EXCLUDED.md`/`INTEGRITY.md`-class metadata — the one-file discrepancy the
audit recorded as `UNVERIFIED` U9, still unresolved and still not this unit's to resolve.

## 4. The target repository is unmodified

| | |
|---|---|
| Target | `the read-only target repository` — read-only; no write, no commit, no `git` state change |
| HEAD before | `907fa39da7ba8ecfbe6e976b7a4cddadea7ac36b` |
| HEAD after | `907fa39da7ba8ecfbe6e976b7a4cddadea7ac36b` |
| `git status --porcelain`, before and after | the same four untracked paths: `?? .ci-trunk.txt`, `?? .relay/`, `?? docs/evidence/selfbuild/relay-outbound-2026-10-13.txt`, `?? docs/migration/` |

**Attribution:** not this unit. Those four are the unrelated concurrent session's dirt, matching what
`repro/encoder-crossover-190/EXCLUDED.md` §5 and `strategy/TRADE_SECRET_AUDIT.md` §9 already record at
the same HEAD. This unit read the target (including read-only `git cat-file` against the closed branch
commit id withheld from this release, which changes nothing) and wrote nothing to it.

## 5. What this file does not prove

It does not prove the subset is free of mechanism disclosure. It proves the subset is byte-identifiable
and unmodified, and that the redaction did not move a number. The **irreducible residue** — internal
mechanism named inside the instrument's own `question` and option text, which cannot be edited without
re-running every arm — is measured in [`REDACTION_REPORT.md`](REDACTION_REPORT.md) §7 and is the
finding that bounds how far this redaction can go. Every known residual reference in the shipped tree,
including the ones in this file's own prose, is listed with a fixed/irreducible judgement in
[`RESIDUALS.md`](RESIDUALS.md).
