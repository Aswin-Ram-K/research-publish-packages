# UFIXMAN1 — archive manifest / deposit-tree consistency

**Parent:** session-c3d61727-8af8-4c19-b1b9-5922c347a11a
**Bound:** 20 tool calls.
**Write paths:** `papers/encoder-crossover-190/released/**`, `strategy/ZENODO_DEPOSIT.md`,
`scratch/ufixman1/**`, `orchestration/units/UFIXMAN1.md`, `orchestration/handoffs/UFIXMAN1.json`.

## Purpose
The deposit archive `papers/encoder-crossover-190/released/encoder-crossover-190-released.tar.gz`
holds 31 files (29 package files + `CITATION.cff` + `README_DEPOSIT.md`), but the manifest copy
shipped inside it lists 28 (package-only, self-exempt). Its `policy` field promises "lists exactly
the files on disk in this package" — true of `scratch/uneutral10/package/`, false of the archive.

## Tasks
1. Verify all stated facts from disk; report any wrong.
2. Fix the assembly step so the archive's manifest describes the archive's own tree (31 files,
   self-exempt → 30 listed / counts.files 31). Use existing tools, read them first.
3. Determine which tree the previous unit's `30 listed / counts.files 31 / bytes_total 840,000`
   regeneration described — that is a finding about authoritative tree.
4. Rebuild archive reproducibly; build twice, prove byte-identity; report size + sha256.
5. Prove end to end: extract, run checker inside extracted tree; also run against package dir.
6. Record package-content vs deposit-metadata distinction in `README_DEPOSIT.md` and
   `strategy/ZENODO_DEPOSIT.md`.
7. Confirm no published number moved; package manifest still 28 listed / counts.files 29.

**If the assembly step cannot be located: STOP and report where the archive is built from — do not
hand-patch the tarball.**

## Do NOT
Edit any `MANUSCRIPT.md`, `submission/main.tex`, `submission/**`, `tools/package/**`,
`scratch/uneutral10/package/**`, papers #1/#2. No number/claim/table/figure changes. No network.

## Progress log
- All 7 stated facts verified correct (package 29; archive 157,650 B / `7389bd87…` / 31 files; shipped
  manifest 28 listed / `counts.files` 29 / `bytes_total` 831,775 / the fail-closed `policy` string).
- **Assembly step located**: there is no build script — the recipe is `strategy/DEPOSIT_ARCHIVE.md:19-22`
  (`tar --format=gnu --sort=name --owner=0 --group=0 --numeric-owner --mtime=@0 -C <stage> … | gzip -n -9`)
  driven by manual staging (`scratch/urelease9/build/stage{1,2}`, `scratch/udeposit2/build/`). Encoded as
  a re-runnable script at `scratch/ufixman1/build_archive.sh`: stage → add extras → **regen manifest in
  stage** → tar. No tarball hand-patching.
- **Previous-unit finding**: the `30 listed / counts.files 31 / bytes_total 840,000 / manifest_self
  89ef383627e2e774` manifest exists *only* at `scratch/udeposit2/superseded-unpacked-tree/MANIFEST.json` —
  the un-git-tracked unpacked-tree variant, retired to scratch by UDEPOSIT2. Right shape, wrong tree; both
  shipped trees kept the package's 28-file manifest.
- **Fixed**: archive rebuilt (158,762 B, sha256 `956d6363db4563ddd3d848790a4026590a38c86ced993ccd76aecdad66a7910a`),
  built twice with `cmp` exit 0; archive manifest `files[]` 30 / `counts.files` 31 / `bytes_total` 844,089.
- **Proved**: `check_manifest.py` at the extracted archive root → all five counts 0, `VERDICT PASS`, exit 0;
  same against the package → PASS, exit 0; `verify/recompute-claims.py` inside the extraction → exit 0,
  `ALL PUBLISHED NUMBERS REPRODUCED: True`; package manifest byte-unchanged (`d41d82cf…`, 28 listed / 29).
- **Exported**: `strategy/DEPOSIT_ARCHIVE.md` and `strategy/DEPOSIT_METADATA.md` were outside the write
  paths, so they still record the old 157,650-byte archive — a superseding unit is needed for them.
