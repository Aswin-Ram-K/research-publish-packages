# UFIXDEP4 — fix the package CONTRIBUTING.md draft/dead-link banner, rebuild the archive, cascade the digest

**Status:** done. **Bound:** 22 tool calls; used 18.
**Parent:** `session-c3d61727-8af8-4c19-b1b9-5922c347a11a`.

## Purpose

The deposit archive goes to Zenodo for a permanent DOI. `scratch/uneutral10/package/CONTRIBUTING.md:3`
called itself a **DRAFT** and linked to `../PLACEMENT.md`, an internal strategy file that does not ship —
a dead link in a public deposit. Fix it, sweep the class, rebuild the archive, and cascade the new digest
through every live document.

## Job 1 — defect fixed and class swept

`CONTRIBUTING.md:3` old: `> **DRAFT - template for the author to place.** See [`../PLACEMENT.md`](../PLACEMENT.md).`
New banner (ASCII, lines 3-9): released research artefact, not an open-source project; PolyForm
Noncommercial 1.0.0 governs the released files and any commercial use requires a paid licence; ideas and
corrections are welcome but code is not merged — the author integrates by re-implementation because
verbatim-contributed code would carry the contributor's own noncommercial licence and could never enter a
paid tier; contact = the repository issue tracker `<https://github.com/Aswin-Ram-K/research-publish-packages>`.
No email invented. 3,036 B `dd8b8ee4…` -> 3,547 B `3b5e5962…`.

Sweep of `scratch/uneutral10/package` for `DRAFT|PLACEMENT.md|TODO|FIXME|to be supplied|placeholder|XXX|<placeholders>`:
- **defect, fixed:** `CONTRIBUTING.md:3`;
- **deliberate, untouched:** `fixture/reflex-decisions.ts:5`, `COMMERCIAL.md:53`, and
  `second-labeller/PREREGISTRATION.md:98` (`<id>`/`<index>` JSON-schema notation);
- no `TODO`/`FIXME`/`XXX`/`to be supplied` hits.

## Job 2 — the cascade (measured at every step)

1. Package `MANIFEST.json` regenerated: 11,043 B `fecdc1fb…` (`manifest_self e5b5171902709910…`,
   `counts.bytes_total` 832,286); `check_manifest.py` on the package: five counters 0, `VERDICT PASS`, exit 0.
2. Archive rebuilt twice with `scratch/ufixman1/build_archive.sh` (`GENUTC=2026-10-18T08:05:47Z`):
   internal `cmp` clean, cross-build `cmp` clean, second run `BYTE-IDENTICAL` vs the just-installed file.
3. **New archive: 158,956 bytes, sha256 `bcdbf75eff70eec77fc1f4a181947c86dd9c12862871315e1dfeec8578fbb6a2`, 37 members.**
4. Extraction: `check_manifest.py` five counters 0 / `VERDICT PASS` / exit 0;
   `verify/recompute-claims.py` exit 0, `ALL PUBLISHED NUMBERS REPRODUCED: True`, fixture digest
   `c7696edc0e71d83faafc2e489925788e0f36c6af94913674f8953718352c9a55`.
5. Live docs updated, superseded values kept as dated history: `strategy/DEPOSIT_ARCHIVE.md`,
   `strategy/DEPOSIT_METADATA.md` (duplicated AUTHORITY block collapsed 2->1), `strategy/ZENODO_DEPOSIT.md`
   (append-only dated pointer), `strategy/SUBMISSION_RUNBOOK.md` (every occurrence),
   `scratch/urelease9/zenodo/ZENODO_UPLOAD.txt` (digest record only).

## Job 3 — overstatement corrected

`strategy/DEPOSIT_ARCHIVE.md:18` no longer claims an empty `diff -r`. Measured truth: the archive's
`MANIFEST.json` is regenerated (11,761 B `23b7fa94…`) and differs from the package's (11,043 B `fecdc1fb…`);
the other 28 package files are byte-identical and the archive adds `CITATION.cff` + `README_DEPOSIT.md`.

## Files touched (before -> after sha256)

| file | before | after |
|---|---|---|
| `scratch/uneutral10/package/CONTRIBUTING.md` | `dd8b8ee4…` | `3b5e5962…` |
| `scratch/uneutral10/package/MANIFEST.json` | `d41d82cf…` | `fecdc1fb…` |
| `papers/encoder-crossover-190/released/encoder-crossover-190-released.tar.gz` | `956d6363…` | `bcdbf75e…` |
| `strategy/DEPOSIT_ARCHIVE.md` | `3c82ed49…` | `17cd2187…` |
| `strategy/DEPOSIT_METADATA.md` | `953cbc28…` | `0cc82e45…` |
| `strategy/ZENODO_DEPOSIT.md` | `c238156a…` | `074974fc…` |
| `strategy/SUBMISSION_RUNBOOK.md` | `c5543af9…` | `5daa1dd0…` |
| `scratch/urelease9/zenodo/ZENODO_UPLOAD.txt` | `4029f9da…` | `2aed9d2f…` |

## Incident (resolved)

A first write truncated `CONTRIBUTING.md` to 0 bytes: `encoding="ascii"` on a `"w"` handle raised
`UnicodeEncodeError` on the file's two pre-existing em dashes *after* truncation. Recovered byte-exactly
from the earlier read (revert-test reproduced `dd8b8ee4…`); all later writes are UTF-8 with assertions
before writing. Lesson: assert, then write; never open a file with a narrower codec than its content.
