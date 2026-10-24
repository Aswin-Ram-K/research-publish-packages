# UDOCREFRESH2 — refresh the live stale deposit values in the runbook, the Zenodo guide, and the upload text

**Purpose.** The author is uploading to Zenodo now, following `strategy/SUBMISSION_RUNBOOK.md`. That
runbook (`:21`, `:47`, `:48`) and two sibling documents still name the superseded archive
(158,956 B / `bcdbf75e…`). UREADMEFIX1 rebuilt the archive minutes ago (README dead paths fixed), so the
author is holding the correct file while the runbook would call it wrong.

**Bound.** 15 tool calls. **Write paths.** `strategy/SUBMISSION_RUNBOOK.md`, `strategy/ZENODO_DEPOSIT.md`,
`scratch/urelease9/zenodo/ZENODO_UPLOAD.txt`, `scratch/udocrefresh2/**`, this card, own handoff.
**Read-only.** `papers/**` (uploading as we work), `scratch/uneutral10/package/**`, `/home/zer0null/Duval`.
No `git` state change. No published number moved.

**Measured (literal).** `papers/encoder-crossover-190/released/encoder-crossover-190-released.tar.gz`:
159,014 B; sha256 `478941c0259b9309145aea17413c3795d0078c2994d32739a01ff09fc51e89d7`; md5
`4066c3428c1e4836d200909c6a2db6b0`; 37 members. Extracted manifest: `files[]` 30, `counts.files` 31,
`counts.bytes_total` 844,708, `manifest_self` `a4d6767c…`. Front page `README_DEPOSIT.md` 10,585 B /
sha256 `71f76e605644d6db0c45b7db6ec0c39273e4edb8e325e2a3acbf5f977468fe6d`. **Card agreed on every figure.**

**Corrected (new value primary, old value kept verbatim as dated history; line counts unchanged).**
- `strategy/SUBMISSION_RUNBOOK.md` `:21` (digest+size → 478941c0 / 159,014), `:29-30` (PDF → 188,364 B /
  `752747f8…`), `:47-48` (159,014 B / `478941c0…c51e89d7`).
- `strategy/ZENODO_DEPOSIT.md` `:398` (README 10,477 → 10,585 B), `:433-434` (live values → 159,014 /
  `478941c0…`).
- `scratch/urelease9/zenodo/ZENODO_UPLOAD.txt` `:57-58` and `:78-79` (digest/bytes → 478941c0 / 159,014),
  plus the `:80` superseded chain.

**Classification.** All other sweep hits are dated history and were left: RUNBOOK none else;
ZENODO_DEPOSIT `:394-397` (158,762 / `956d6363…` / 844,089 — the UFIXDEP1 section's own dated table);
ZENODO_UPLOAD `:12-14`, `:19` (zip 8e2f603e, correct), `:36`, `:59-62`, `:83`. `77a75700` (old md5) and
`844,600`/`844600`: **0 hits** in all three files.

**Also corrected (unrelated live disagreement).** RUNBOOK `:28-30` said the PDF was 184,933 B while
`strategy/DEPOSIT_METADATA.md:210` said 188,364 B. Measured on disk:
`papers/encoder-crossover-190/rendered/encoder-crossover-190.pdf` = **188,364 B**, sha256 `752747f887…`,
25 pages A4. RUNBOOK was the stale one; `DEPOSIT_METADATA.md` is correct and was not touched.

**Checkers (literal).** `python3 tools/package/check_manifest.py --package
/home/zer0null/reserach\ extarctor/scratch/udocrefresh2/extract/encoder-crossover-190-released` →
`missing=0 hash_mismatch=0 size_mismatch=0 unlisted=0 listed_but_absent=0` /
`manifest_self_recomputes=True` / `VERDICT PASS`, exit 0. `verify/recompute-claims.py` inside the
extraction → `ALL PUBLISHED NUMBERS REPRODUCED: True`, `VERDICT: PASS`, exit 0.

**Status.** done 2026-10-18.
