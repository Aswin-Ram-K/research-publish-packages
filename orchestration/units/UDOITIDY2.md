# Unit UDOITIDY2 — close the three loose ends left by UDOIBACK2

- **Bound:** 15 tool calls; used 10. Date: 2026-10-19 (America/Chicago).
- **Status: done.**

## Declared write paths (only these were written)
`papers/replay-record-not-decision/**`, `scratch/udoitidy2/**`,
`orchestration/units/UDOITIDY2.md`, `orchestration/handoffs/UDOITIDY2.json`.
No `git` command was run against any target repo or this workspace.

## JOB 1 — email (DONE)
`TMLR_ANONYMITY_NOTE.md`: the wrong form `aswin.k.1603@…` → `aswinram.k.1603@…`, matching the frozen
byline (`submission/main.tex:12`, mtime unchanged 2026-10-19 14:19:40). Added dated line at `:58`:
"Correction 2026-10-19 (UDOITIDY2): … dropped the `ram` … transcription error in this note, not in
the paper …". The correction line deliberately does **not** reproduce the wrong address.

| form | before | after |
| --- | --- | --- |
| `aswin.k.1603` (wrong) | 1 occurrence, 1 file | **0** |
| `aswinram.k.1603` (right) | 1 occurrence, 1 file | 3 occurrences, 2 files |

First attempt reintroduced the wrong string inside the correction sentence (count stayed 1); caught on
the same sweep and rewritten to describe the error instead of quoting it.

## JOB 2 — rendered PDF (DONE)
Recompiled with the three mandatory env vars, exit **0**, `Undefined control sequence` **0**, `!` **0**,
never `-Z continue-on-errors`. New PDF **101,593 B / 10 pages**, sha256
`a2f10c7da83663e61bae71e05ab9fbfc617613cf8726c8096e5eff047e554c31`. Installed as
`rendered/replay-record-not-decision.pdf`; its own `pdftotext` shows **1 ×** `10.5281/zenodo.23482511`
and **0 ×** `10.5281/zenodo.23482512`. Old file (94,683 B, sha256 `4ac73a51…`) → `rendered/_superseded/
replay-record-not-decision-prior-doi-backfill-4ac73a51.pdf`, with a dated section appended to the
existing `_superseded/README.md`.

## JOB 3 — stale unpacked trees (DONE)
`released/` held **two** unpacked trees, both byte-stale versus the rebuilt archive: each carried a
pre-DOI `CITATION.cff` (sha256 `da586565…`, no `doi:` field) and a `MANIFEST.json` (`2f9fd121…`) that
no longer matched the archive's `c2fada5d…` / `49cf42f1…`. Both moved (never deleted) to
`scratch/udoitidy2/superseded-unpacked/`, each beside a `.sha256` manifest of all 10 files
(`sha256sum -c` → OK for both). Marker: `released/SUPERSEDED-UNPACKED.md`. The loose
`released/CITATION.cff` and `README_DEPOSIT.md` **match the archive's bytes** and were kept.

## JOB 4 — archive (DONE, clean extraction)
- `check_manifest.py`: `missing=0 hash_mismatch=0 size_mismatch=0 unlisted=0 listed_but_absent=0`,
  `manifest_self_recomputes=True`, `VERDICT PASS`, exit **0**.
- `recompute-claims.py` (cwd = extracted package root): `CHECKS: 30/30 passed`,
  `ALL PUBLISHED NUMBERS REPRODUCED: True`, `VERDICT: PASS`, exit **0**.
- `CITATION.cff`: `doi: "10.5281/zenodo.23482511"` once, `23482512` **0** times.
- Archive: **107,764 bytes**, sha256 `e6f920c432e0dc180ca72336e0bb60b2155462b8365f8800359a24beec3bbe63`,
  md5 `41afa2831ff2f43af91d9c4416d8f658`. `MANIFEST.json` never hand-edited.

## JOB 5 — the upload the author still owes
Published record **23482512** still holds the **old** archive (107,641 B, md5
`a279e399382792952205b0738f958e38`). The local archive differs only because `CITATION.cff` gained the
concept DOI (+123 B). The author must **publish a NEW VERSION of record 23482512** and upload:

- path: `papers/replay-record-not-decision/released/replay-record-not-decision-released.tar.gz`
- size: **107,764 bytes**
- sha256: `e6f920c432e0dc180ca72336e0bb60b2155462b8365f8800359a24beec3bbe63`
- md5: `41afa2831ff2f43af91d9c4416d8f658`

Publishing a new version does **not** change the concept DOI `10.5281/zenodo.23482511` — it always
resolves to the latest version. The version DOI `10.5281/zenodo.23482512` stays with the old version.

## Disagreements with the card (reported, not smoothed)
1. Wrong email is at `TMLR_ANONYMITY_NOTE.md:55`, **not `:44`**; `:44` is prose about the DOI.
2. `rendered/replay-record-not-decision.pdf` was **94,683 B** (sha256 `4ac73a51…`), not 91,551 B. The
   91,552 B file is already in `_superseded/` (`…tectonic-prior-main-85f13e8c.pdf`, Oct 17). **No
   91,551-byte PDF exists** in the tree; the card's figure matches no live file.
3. `verify/recompute-claims.py` does not exist at workspace root — only inside the package, so it must
   run with cwd = extracted package root.
4. `released/` held **two** stale unpacked trees, not "tree(s)" implied as one.
5. The fresh compile's **101,593 B / 10 pages** confirmed exactly.
6. The email fix is not in the archive payload (`MANIFEST.json` lists no paper-root note). If a later
   repack starts including paper-root documents, that becomes a payload change.
