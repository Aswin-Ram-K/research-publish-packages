# VERIFICATION_REPORT_DEPOSIT_2.md — VDEPOSIT2, independent re-check of UFIXDEP2

**Verifier:** VDEPOSIT2 (did not author any artifact under check). **Date:** 2026-10-18.
**Subject:** `UFIXDEP2` — `orchestration/units/UFIXDEP2.md`, `orchestration/handoffs/UFIXDEP2.json`.
**Hard bound:** 18 tool calls used 15. **Verdict: PASS**, with two findings recorded (one contradicted
ancillary claim, one overstated wording). Nothing was edited outside
`strategy/VERIFICATION_REPORT_DEPOSIT_2.md`, `orchestration/units/VDEPOSIT2.md`,
`orchestration/handoffs/VDEPOSIT2.json`, `scratch/vdeposit2/**`.

---

## 1. Doc correction — the three sites

All three sites named in the card now assert the **current** policy in the present tense and retain the
reversed policy as **dated history** (not deleted). Actual line numbers on disk: `:54-57`, `:81-86`,
`:98-102` (the card's `:94-95` hint is ~6 lines low; the third site is the UDEPOSIT2 §5 check list).

| site | current-tense assertion | dated superseded text retained |
|---|---|---|
| `strategy/DEPOSIT_ARCHIVE.md:50` | `check_manifest.py --package <extracted archive root>` -> `unlisted=0`, `VERDICT PASS`, exit **0** | — |
| `strategy/DEPOSIT_ARCHIVE.md:54-57` | (invariant 1 base) | `*Superseded 2026-10-17 (retained as history):*` … `unlisted=2` at the tarball root, `which that date *believed* to be by design` … `That belief was **reversed on 2026-10-18**` |
| `strategy/DEPOSIT_ARCHIVE.md:81-86` | `unlisted=0` / `VERDICT PASS` / exit **0** | `unlisted=2` / exit 1 `**was, on 2026-10-17, held to be** by design` + `*Superseded 2026-10-18 (UFIXDEP1):* that policy was reversed` |
| `strategy/DEPOSIT_ARCHIVE.md:98-102` | `as measured on 2026-10-17` header… | `… VERDICT FAIL, exit **1** — the then-current design, **reversed on 2026-10-18**` |
| `strategy/DEPOSIT_ARCHIVE.md:133-135` | `unlisted=0`, `VERDICT PASS`, exit **0** (UFIXDEP1 re-measure) | — |

**Sweep for survivors of the stated class** (`unlisted=2` / `VERDICT FAIL` / exit 1 asserted
present-tense as current, or excused as "by design"):

- `strategy/DEPOSIT_ARCHIVE.md` — 9 matches for the class, **all** either current-policy-correct
  (`:50`, `:85`, `:134`) or explicitly dated/superseded (`:56`, `:81`, `:82`, `:100`, `:101`, `:102`).
  **Zero survivors.**
- `strategy/DEPOSIT_METADATA.md` — **zero hits** for each of `unlisted`, `by design`, `only the 29`,
  `VERDICT FAIL`. UFIXDEP2's "returned no hits" claim reproduced exactly.
- Adjacent files (outside the mandated sweep, checked anyway): `strategy/ZENODO_DEPOSIT.md:377`
  describes the same defect but in past tense under "*The defect that was fixed*" — **not a survivor**.
  `strategy/VERIFICATION_REPORT_DEPOSIT.md:36-46`,`:140-141`,`:174` is the prior verifier's audit
  record that *found* the defect — historical by construction.

**Digests verified by direct measurement:**
`strategy/DEPOSIT_ARCHIVE.md` **10,759 B sha256
`b7e04cd5acf93f76be5e2fb8eaea8b31136a333ae72f52a7b9d55944d8f12a57`** ✔ matches the claim;
`strategy/DEPOSIT_METADATA.md` **29,867 B sha256
`953cbc28bc07fb4ce15b2e90432946d9429ee6db813c7e141549b302be7c1afb`** ✔ unchanged.
The **pre-edit** figure (10,127 B / `91f1843a…`) is **not recomputable** — the file is untracked
(`git status --porcelain` → `??`) and no pre-image exists on disk. It is corroborated as *UFIXDEP1's
handoff output* (`orchestration/handoffs/UFIXDEP1.json:15`: 6,660 B `b6f0c8a9…` → 10,127 B
`91f1843a…`), so the chain is consistent but was not independently re-measured.

## 1b. `contradicted` — a false present-tense claim found by the full-file sweep

`strategy/DEPOSIT_ARCHIVE.md:17`, the `inputs` row, names the third input as
`scratch/uzenodo2/run2/README_DEPOSIT.md`. On disk that file is **6,396 B sha256
`baf134595ecb65bb94fcd42d7587acce7655e1a3ad7cb4eaab92b6cece8673f4`** — the *superseded* README, which
the same file records as "was" at `:95` and as superseded at `:125`. The superseded script
`scratch/ufixman1/build_archive.sh:29` actually reads
`$ROOT/papers/encoder-crossover-190/released/README_DEPOSIT.md` = **10,477 B sha256
`503751f19ad71f6efa4d42217449948178b164521d4acc37ca9ddc4834970085`**, which is also the digest of the
copy inside the shipped archive (verified by `tar xzOf … | sha256sum`). Pointing the build at the
documented path makes its own guard fail (`README_DEPOSIT.md drifted`, exit 1 — see §4). The row is
materially wrong for anyone rebuilding from it. It is **not** one of the three sites UFIXDEP2 reported
fixing (different class), and no unit has claimed to fix it.

## 2. Self-containment, adversarially

The rule "do not touch the originals" and "renamed away" conflict; I satisfied both by building in a
**sandbox root with zero previous tarballs anywhere** — strictly stronger than renaming one file.
`scratch/vdeposit2/root` was assembled with only the declared inputs (package + `CITATION.cff` +
`README_DEPOSIT.md` + a copy of the shipped archive as comparison authority + `tools/`), **42 files
total, `find … -name 'prev-*.tar.gz' | wc -l` = 0**. The script copy
`scratch/vdeposit2/build_archive_sandbox.sh` differs from the original by **one line** (`ROOT=…`,
repointed). `grep -n prev` on the copy returns **comments only (lines 6, 7, 11)** — no code path reads
a tarball. The real `scratch/ufixman1/prev-encoder-crossover-190-released.tar.gz` was never touched
(after: still 157,650 B `7389bd879e970d840a528a9a19bfb9a6623babf3ec10746b18fc616bf2b4dad3`).

**Green:** `sh scratch/vdeposit2/build_archive_sandbox.sh` → `bytes=158762 members=37`,
`BYTE-IDENTICAL: self-contained build == shipped archive (cmp exit 0)`, **exit 0**, with no previous
tarball reachable. The script's earlier launcher therefore no longer depends on a prior artifact: the
UFIXMAN1 defect described at `build_archive.sh:5-8` is genuinely fixed.

## 3. Byte-identity — literal results

- shipped `papers/encoder-crossover-190/released/encoder-crossover-190-released.tar.gz`:
  **158,762 B**; sha256 **`956d6363db4563ddd3d848790a4026590a38c86ced993ccd76aecdad66a7910a`** ✔
- build `out1.tgz`, `out2.tgz`, `encoder-crossover-190-released.tar.gz`: all **158,762 B**, all
  sha256 **`956d6363…`** ✔
- `cmp out1.tgz out2.tgz` → **exit 0**; `cmp out1.tgz <shipped>` → **exit 0**;
  after the red/green perturbation and restore, `cmp out1.tgz <shipped>` → **exit 0**
- members `tar tzf | wc -l` = **37** = 6 `/`-terminated entries (1 top dir + 5 subdirs) + **31** files ✔
- archive `MANIFEST.json` digest **`e9e5e5e07fc63c6887c88127bb2a1c03300c8d6dac692b31ba288757d5457a4d`** ✔
  (matches UFIXDEP2's handoff); `manifest_self` `8daf32ea280059b2…`; `files_on_disk 31`,
  `bytes_total 844089`, `files[] entries 30 (excludes MANIFEST.json)`,
  `added: ['CITATION.cff','README_DEPOSIT.md'] changed: 0` ✔ (doc `:16`)

## 4. Red→green on the input-digest guards — **the required guard result**

Guards are **live, not inert** (literal stderr and exit codes):

```
RED   perturb sandbox scratch/uzenodo2/run2/CITATION.cff (append one newline)
      -> CITATION.cff drifted: b32e9a916ab619efab71d826226576395b9e483ccbae2297e05e0e5bd85b6c8a
      -> exit 1  (re-run while still perturbed -> exit 1)
RED   perturb sandbox papers/.../released/README_DEPOSIT.md (append one newline)
      -> README_DEPOSIT.md drifted: a1481ceee92cf6e36ccbed3dff1a13213757e593477f054258834bdf474038d2
      -> exit 1
GREEN restore both from scratch/vdeposit2/*.good
      -> exit 0; cmp(out1, shipped) == 0
```

Both guards fail with a *distinct* drifted digest pointing at the right input, so the check is not a
tautology. `refused`/`not_run`: none. Red→green: **RED confirmed, GREEN restored**.

## 5. Shipped checks on an extraction of the reproduced archive

`scratch/vdeposit2/verify-extract/encoder-crossover-190-released` (unpacked from the sandbox build):

```
python3 tools/package/check_manifest.py --package <ABS extraction root>      # exit 0
  missing=0 hash_mismatch=0 size_mismatch=0 unlisted=0 listed_but_absent=0
  manifest_self_recomputes=True (blank generated_utc; drop manifest_self; sort_keys indent=2)
  VERDICT PASS
cd <ABS extraction root> && python3 verify/recompute-claims.py              # exit 0
  ALL PUBLISHED NUMBERS REPRODUCED: True
  VERDICT: PASS
  fixture correctness digest: c7696edc0e71d83faafc2e489925788e0f36c6af94913674f8953718352c9a55
```

All five counters zero ✔, `VERDICT PASS` ✔, exit 0 ✔, `ALL PUBLISHED NUMBERS REPRODUCED: True` ✔,
fixture digest exact ✔. The absolute-path requirement was honoured; the extraction root is
**31 files** and the check passes at that root with `unlisted=0` — the reversed policy is dead in
substance, not just in prose.

## 6. Custody — nothing shipped was modified

| artifact | before | after |
|---|---|---|
| `papers/.../encoder-crossover-190-released.tar.gz` | 158,762 B `956d6363…` | **identical** |
| `scratch/uneutral10/package/MANIFEST.json` | `d41d82cf8aa838737a55d300bd77b74c787c44d482a5f964c4c446e40c2aac02` | **identical** |
| `strategy/DEPOSIT_ARCHIVE.md` | `b7e04cd5…` | **identical** |
| `strategy/DEPOSIT_METADATA.md` | `953cbc28…` | **identical** |
| `scratch/ufixman1/prev-…tar.gz` | 157,650 B `7389bd87…` | **identical** |

The rewritten script writes only `$W/build/` and `$W/GENERATED_UTC.txt`; even in the sandbox it never
wrote the shipped path. Package still 29 files; archive still 31 files. No writes outside the declared
write paths.

## 7. The open item — `strategy/DEPOSIT_ARCHIVE.md:42` (reported, not edited)

**It is already marked superseded — it is not a live claim — but its own prose is stale.**

- The row sits inside the section **`## Superseded — retained, never upload`** (`:37`), with header
  `| path | bytes | sha256 | why |` (`:39`).
- The retired path is **ABSENT from disk** (`papers/encoder-crossover-190/released/` now holds only
  `README_DEPOSIT.md`, `SUPERSEDED-UNPACKED-TREE.md`, `encoder-crossover-190-released.tar.gz`).
- The dated marker stands there: `SUPERSEDED-UNPACKED-TREE.md`, 2,404 B sha256
  `72dfdddf810737ec7dfc6a7bd6a54b12ac8294905b300b716c79c75b34ee73b8`, headed
  "**Dated:** 2026-10-17 (UDEPOSIT2)". The moved tree exists at
  `scratch/udeposit2/superseded-unpacked-tree/`.
- UDEPOSIT2 §1 (`:65-72`) records the move explicitly ("was **moved, not deleted**").

**Residual defect (overstated, not contradicted):** the row's own prose is written in the present
tense about a path that no longer exists — "its `COMMERCIAL.md` **is** still the pre-fix 3,512-byte
file", "its `README_DEPOSIT.md` **is** `b10762…`", "Un-git-tracked. **Left unmodified by
URELEASE9**" — and carries **no inline dated supersession sentence**, unlike the two sites UFIXDEP2 did
correct (`:54-57`, `:81-86`). A reader who stops at the row is misled about the tree's existence; a
reader who sees the section heading is not. Fixing it is a **new unit's** job; this verifier edited
nothing.

## 8. Classification

- **contradicted (1):** `strategy/DEPOSIT_ARCHIVE.md:17` `inputs` row names
  `scratch/uzenodo2/run2/README_DEPOSIT.md` (`baf13459…`, the superseded 6,396 B file) where the build
  actually reads `papers/encoder-crossover-190/released/README_DEPOSIT.md` (`503751f1…`, 10,477 B).
  Pointed at the documented path the build fails its own guard.
- **overstated (1):** `strategy/DEPOSIT_ARCHIVE.md:42` present-tense assertions about the retired
  unpacked tree; superseded by section heading only, with no inline date.
- **not_reproduced:** none.
- **unverified (2):** (a) the pre-edit `10,127 B / 91f1843a…` state of `DEPOSIT_ARCHIVE.md` — no
  pre-image preserved and the file is untracked, so only UFIXDEP1's handoff corroborates it;
  (b) `strategy/DEPOSIT_ARCHIVE.md:18` `proof` row ("`diff -r` against the inputs is empty, exit 0"),
  measured by UFIXDEP1, not in this unit's remit and not re-run.
- **red→green:** `CITATION.cff` guard RED (`b32e9a91…`, exit 1) → GREEN (exit 0, `cmp` vs shipped 0);
  `README_DEPOSIT.md` guard RED (`a1481cee…`, exit 1) → GREEN (exit 0). Guards are live.

## 9. Verdict

**PASS.** Both claims under check reproduce exactly: the three reversed-policy assertions are corrected
and the superseded wording is retained and dated (zero survivors of that class in either document), and
`scratch/ufixman1/build_archive.sh` is self-contained — a root with no previous tarball at all rebuilds
**158,762 B / `956d6363…` / 37 members**, byte-identical to the shipped archive, whose extraction passes
both shipped checks. Custody is clean. The one contradicted item (`:17`) and one overstated item
(`:42`) are pre-existing text in the certified document, outside the three sites UFIXDEP2 declared
fixed; they are handed to a new unit because a verifier fixes nothing.
