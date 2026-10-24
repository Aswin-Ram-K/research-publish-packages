# UDOIBACK2 — install the Zenodo DOI into paper #4 (payload + deposit rebuild)

**Parent:** session-c3d61727-8af8-4c19-b1b9-5922c347a11a · **Status:** DONE (2026-10-19) · **Tool calls used:** 29/30

## Purpose
Paper #4 must cite **concept DOI `10.5281/zenodo.23482511`** (never version DOI `10.5281/zenodo.23482512`,
which dies at the next version), then the downstream chain must be proven unmoved.

## JOB 1 — DOI site sweep (reported before editing)
| # | Site | Text before edit | Decision |
|---|---|---|---|
| H1 | `MANUSCRIPT.md:298-303` (§7 Data availability, "**Released.**" para) | "…Total released size of the two records: **1,261,035 bytes**." — a release with no identifier | **live claim to correct** → added a "Persistent identifier: concept DOI `10.5281/zenodo.23482511`" paragraph immediately after it |
| H2 | `released/CITATION.cff:32-37` | "# DOI: deliberately absent. No DOI exists for this deposit yet. Zenodo assigns one on publication; add it here afterwards as doi: \"10.5281/zenodo.XXXXXXX\"…" | **live claim now FALSE** → replaced by `doi: "10.5281/zenodo.23482511"` + a dated SUPERSEDED comment retaining the old wording |
| H3 | `AVAILABILITY.md:3-9` (release-boundary update block) | names the release but no identifier for **this** deposit | **live claim to correct** → added a dated "Update 2026-10-19" block (concept/version record ids, cite-the-concept rule, licence + boundary unchanged) |
| H4 | `TMLR_ANONYMITY_NOTE.md:22-24,28-29` | rule enumerates fragments the anonymous PDF must not print | **live rule to extend** → new dated section: this deposit's DOI is equally identifying, so `10.5281/zenodo.23482511` **and** `23482512` must be stripped from the anonymous variant too |
| — | `submission/METADATA.md`, `CLAIMS.md` | no DOI site (grep: no placeholder, no pending wording) | **no hit** |
| — | companion-only DOI mentions, left alone as correct: `MANUSCRIPT.md:34` (abstract) & `:307-308`, `AVAILABILITY.md:5`, `GAPS.md:5-6`, `submission/main.tex:23,205` (generated), `released/README_DEPOSIT.md:103`, `released/*/README.md:6-7,37,80-81`, `released/CITATION.cff:13-14`, `TMLR_ANONYMITY_NOTE.md:1-24` | `10.5281/zenodo.23463944` = paper #3's deposit, a **different** record | **dated/other-deposit record — leave alone** |

No measured number, claim value or byline was changed. No `MANIFEST.json` was hand-edited.

## JOB 2 — install at source + regenerate
`python3 tools/package/md2tex.py --package replay-record-not-decision` → exit 0, **no dename rule fired**
(no rule was stale, `tools/package/md2tex.py` was **not** modified). Output `main.tex` 32,766 B,
sha256 `a62e377e9c32d8fba98f84f1d17b8e3bb5ff7edb01362d450d8c9a7fd1231a15`.

## JOB 3 — payload rebuild, proved unmoved
- numeric-literal multiset (bibliography-stripped, regex `\d+(?:\.\d+)?` on the body before `\begin{thebibliography}`):
  before 123 distinct / 417 total → after 124 / 419. **ADDED: `10.5281` ×1, `23482511` ×1. REMOVED: none.**
  No year literal was added (the card listed one as expected; the edit needed none).
- `\bibitem` 8, `\cite` 8, distinct cited keys 8, uncited 0, unresolved 0 — unchanged; byline line byte-identical.
- tarball rebuilt with `tar --mtime=@0 --sort=name -cf - main.tex | gzip -n -9`, twice, `cmp` exit 0 → **11,533 B**, sha256
  `dc0b3bbeaef428a7ad8c86a6645f17817b9f44477c59c0c17eac7095f8ba8e39`, md5 `5fb2afc415d855737975a59beb50ae8d`, 1 member `main.tex`, byte-identical to on-disk `main.tex` after extraction.
- PDF: `tectonic -r 1 --keep-logs -o scratch/udoback2/pdf` → **exit 0**, `Undefined control sequence` **0**, `^!` **0**, 10 pages,
  101,593 B. (Needed `TECTONIC_CACHE_DIR` inside the workspace: the first attempt died on a read-only filesystem writing its cache.)

## JOB 4 — deposit archive rebuilt
Ran a copy of `scratch/upkg2c/build_archive.sh` at `scratch/udoback2/build_archive.sh` (scratch/upkg2c is outside the
declared write paths, so its `inputs.sha256` could not be re-pinned in place; the package tree was `cp -a`'d and the pin file
re-generated for the copy — the LEAK GATE, the 8-file check and the deterministic-tar step are unchanged).
`INSTALL=1` → **LEAK GATE PASS**, `DETERMINISTIC: build1 == build2`, 107,764 B, sha256
`e6f920c432e0dc180ca72336e0bb60b2155462b8365f8800359a24beec3bbe63`, md5 `41afa2831ff2f43af91d9c4416d8f658`, 13 members.
Clean extraction: `check_manifest.py` → `missing=0 hash_mismatch=0 size_mismatch=0 unlisted=0 listed_but_absent=0`,
`manifest_self_recomputes=True`, **VERDICT PASS**, exit 0. `verify/recompute-claims.py` → **30/30 passed**,
`ALL PUBLISHED NUMBERS REPRODUCED: True`, **VERDICT PASS**, exit 0.

## JOB 5 — the record the paper now cites
`https://zenodo.org/api/records/23482511` → **302** to `/api/records/23482512` (a concept record resolves to the latest
version; that is the expected behaviour). API values: `conceptrecid=23482511`, `conceptdoi=10.5281/zenodo.23482511`,
`doi=10.5281/zenodo.23482512`, title "Replay-Record-Not-Decision — recorded data and verification tooling",
`resource_type=dataset`, `license.id=polyform-noncommercial-1.0.0`,
file `replay-record-not-decision-released.tar.gz` size **107,641** checksum **`md5:a279e399382792952205b0738f958e38`**.

**The published record no longer matches the local archive.** It matches the *pre-DOI* archive (107,641 B, md5
`a279e399…`); the installed rebuild is 107,764 B / md5 `41afa283…`, because `CITATION.cff` gained the `doi` field. The
author must publish a new version of the deposit (or replace the file) so the record carries the DOI it is cited by.

## Caveats (not fixed here, deliberately)
- `papers/replay-record-not-decision/rendered/replay-record-not-decision.pdf` was **not** overwritten: the workspace
  tectonic cache was empty, so the public bundle was fetched and the new PDF (101,593 B) differs from the installed
  91,551 B for font/bundle reasons, not text. Page count is still 10.
- `released/replay-record-not-decision-released/` and `…-released (2)/` are now stale extractions (pre-DOI `CITATION.cff`
  and `MANIFEST.json`); neither is an input to the build.
- Pre-existing, untouched: `TMLR_ANONYMITY_NOTE.md:44` quotes the author email as `aswin.k.1603@gmail.com`; the shipped
  `main.tex` byline says `aswinram.k.1603@gmail.com`. Byline must not change under this card.
