# UDOIBACK1 — install the published Zenodo DOI (`10.5281/zenodo.23463945`)

**Purpose.** The author published the deposit (`10.5281/zenodo.23463945`, concept `10.5281/zenodo.23463944`,
`https://zenodo.org/records/23463945`, `encoder-crossover-190-released.tar.gz`, 159,014 B, md5
`4066c3428c1e4836d200909c6a2db6b0`, PolyForm-Noncommercial-1.0.0). The paper/package still said the
identifier was *pending*. This unit enumerates every such site, installs the real DOI at the live ones,
keeps dated history, updates `CITATION.cff`, and regenerates the four derived artifacts with project
tooling only.

**Hard bound.** 30 tool calls. **Used: 27.**
**No publish/upload/contact. No `git` state change. `/home/zer0null/Duval` untouched (never referenced).**
**Write paths:** `papers/encoder-crossover-190/**`, `scratch/udoiback1/**`, `orchestration/units/UDOIBACK1.md`,
`orchestration/handoffs/UDOIBACK1.json`.

## 1. Site enumeration (search ran on content, not on line numbers)

`grep -rniE 'zenodo|\bdoi\b|persistent identifier|deposit identifier' papers/encoder-crossover-190`
(114 matches) then a pending-specific alternation. Classification:

| site | text | class |
|---|---|---|
| `papers/encoder-crossover-190/MANUSCRIPT.md:743` | `(Zenodo DOI pending — see Data and code availability)` | **(a)** -> updated |
| `papers/encoder-crossover-190/MANUSCRIPT.md:793-794` | `Zenodo\nDOI pending — see the persistent-identifier paragraph below` | **(a)** -> updated |
| `papers/encoder-crossover-190/MANUSCRIPT.md:858-860` | `**Persistent identifier: none yet.** … has **no persistent identifier**. No DOI has been minted or guessed here, so the released artifacts carry a licence statement and no persistent identifier.` | **(a)** -> rewritten true |
| `papers/encoder-crossover-190/submission/METADATA.md:26` | `**The released package still needs its Zenodo DOI** — pending, …` | **(a)** -> updated |
| `papers/encoder-crossover-190/submission/main.tex:375,407,427` | same three statements, LaTeX | **(a)**, derived -> fixed by regeneration, never hand-patched |
| `papers/encoder-crossover-190/released/encoder-crossover-190-released (2)/CITATION.cff:29-31` | `# DOI: deliberately absent. No DOI exists for this deposit yet.` | **(a)** -> updated (a `doi:` field, see §3) |
| `papers/encoder-crossover-190/rendered/encoder-crossover-190.html:988-991` | `**DOI: AUTHOR TO CONFIRM — Zenodo DOI to be inserted on deposit.** … no persistent identifier yet` | **(a) but derived & already stale-differently** — see §5 gap (c) |
| `papers/encoder-crossover-190/submission/METADATA.md:85-95` | `## Statements added for R39–R43, and the DOI slot for R36`, header marked `**SUPERSEDED (2026-10-16, UFIXBODY3)**`, table row `:91` `DOI: AUTHOR TO CONFIRM — Zenodo DOI to be inserted on deposit` | **(b)** dated history — left alone |
| `papers/encoder-crossover-190/submission/BUILD_NOTES.md:113` | `*identifier* (Zenodo DOI slot, pending)`, inside the dated block `## Update 2026-10-16 (UFIXFMT1) — …` (heading at `:94`) | **(b)** dated history — left alone |
| `papers/encoder-crossover-190/CHECKLIST.md:22-23`, `OPEN_QUESTIONS.md:13`, `:84-86`, `LICENSE_ANALYSIS.md:446-447` | `[PENDING AUTHOR SIGN-OFF]` (not the deposit id); `grep, 2026-10-15` observations that `zenodo` did not occur in `MANUSCRIPT.md` | **(b)** dated/unrelated — left alone |
| everything else in the 114 matches | third-party citation DOIs / `no DOI` for the Simmering blog post | **(b)** unrelated — left alone |

`papers/encoder-crossover-190/released/README_DEPOSIT.md` contains **no** DOI/identifier/pending sentence
(0 matches), so the archive front page did not need an edit.

## 2. Installed text

- `MANUSCRIPT.md:743`: `(Zenodo DOI \`10.5281/zenodo.23463945\` — see Data and code availability)`
- `MANUSCRIPT.md:793-794`: `**no evaluation harness**; Zenodo\nDOI \`10.5281/zenodo.23463945\` — see the persistent-identifier paragraph below`
- `MANUSCRIPT.md:856-861` (new paragraph):
  `**Persistent identifier: DOI \`10.5281/zenodo.23463945\`.** The released reproducibility package (29 files;
  no evaluation harness — see Data and code availability) is published on Zenodo under that DOI (concept DOI
  \`10.5281/zenodo.23463944\`), so the released artifacts carry a persistent identifier as well as a licence statement.`
- `METADATA.md:26`: `**The released package is deposited on Zenodo under DOI \`10.5281/zenodo.23463945\`** (superseded 2026-10-18 UDOIBACK1: *still needs its Zenodo DOI — pending*)`
- Both on-disk `CITATION.cff` copies under `papers/encoder-crossover-190/released/` are byte-identical after
  the edit (`56300d7c…`, 2,006 B).

## 3. `CITATION.cff`

Field used = **`doi`** (CFF 1.2.0 top-level DOI field). Location/line: inserted at
`papers/encoder-crossover-190/released/encoder-crossover-190-released (2)/CITATION.cff:25`, immediately after
`date-released`.

before:
```
date-released: "2026-10-17"
# DOI: deliberately absent. No DOI exists for this deposit yet. Zenodo assigns one on
# publication; add it here afterwards as  doi: "10.5281/zenodo.XXXXXXX"  (and, for a
# concept DOI that survives versions, use the "Concept DOI" shown on the record).
```
after:
```
date-released: "2026-10-17"
doi: "10.5281/zenodo.23463945"
…
# DOI installed 2026-10-18 (UDOIBACK1) after the author published the deposit on Zenodo.
# The doi field above is the version DOI; the concept DOI that survives versions is
# 10.5281/zenodo.23463944. Superseded wording, retained: 'DOI: deliberately absent. …'
```
2,006 B, sha256 `56300d7c43a4cc9d65912130922a5505f07403adebaa73e13da28d4ac792b2a3` (was 1,837 B / `1c1d25ba…`).

`version` / `date-released` — **found, left unchanged, no value invented:** `version` is absent, and the file
says why (`:33` "No version number is declared: no version has been assigned by the author").
`date-released: "2026-10-17"` is the package build date from `MANIFEST.json`
(`generated_utc 2026-10-17T03:26:03Z`), with its own comment telling the author to set the real deposit date
on upload. The Zenodo record's publication date was **not fetched** (`unverified`), so that field is left for
the author.

## 4. Regeneration (project tooling only)

| artifact | invocation (literal) | result |
|---|---|---|
| `submission/main.tex` | `python3 tools/package/md2tex.py --package encoder-crossover-190 --quiet` (invocation confirmed from `md2tex.py --help`; default `outdir=submission`) | 84,786 B, sha256 `1468b61e5baf1a2dc110e5612b70c9d83adc0a91e3101a9fe5b5cfdac6294c6b`, 467 lines; ran twice, `cmp` exit 0 |
| payload tarball | `tar --mtime=@0 --sort=name --owner=0 --group=0 --numeric-owner -cf - -C . main.tex \| gzip -n -9` (recipe verbatim from `submission/BUILD_NOTES.md:266`; "exactly one member, `main.tex`", `tools/package/README.md:291`) | 28,553 B, sha256 `2612fe61a8b82445dad11e1497e61ea0bbb6b2563a14dcfbd641bfc1dd9f4395`, 1 member; twice, `cmp` exit 0 |
| PDF | `TECTONIC_CACHE_DIR=…/scratch/udoiback1/tc TMPDIR=…/scratch/udoiback1/tmp HOME=…/scratch/udoiback1/home scratch/utex1/bin/tectonic -r 1 --keep-logs -o scratch/udoiback1/pdf papers/encoder-crossover-190/submission/main.tex` (route from `BUILD_NOTES.md:285`; **no** `-Z continue-on-errors`) | **exit 0**; `Undefined control sequence` count **0**; `!` line count **0**; 188,820 B, sha256 `7b98c10941a2f1e07ad6e24aa333de369b85e454bd186a5a9d55b4cdee797c2d`; `pdfinfo` Pages **25**, A4 595.28 x 841.89 pts; prior build preserved as `rendered/_superseded/encoder-crossover-190-tectonic-prior-main-752747f8.pdf` |
| deposit archive | recorded recipe `strategy/DEPOSIT_ARCHIVE.md:20-28` + `tools/package/regen_manifest.py --no-note`: stage `scratch/uneutral10/package` (29 files) + `CITATION.cff` + `papers/encoder-crossover-190/released/README_DEPOSIT.md`, regenerate the archive manifest, then `tar --format=gnu --sort=name --owner=0 --group=0 --numeric-owner --mtime=@0 -C <stage> -cf - encoder-crossover-190-released \| gzip -n -9` | 159,085 B, sha256 `add182e778fcb418fc630ba76e06261575650fa85a289e0d842dfa51ecce1240`, md5 `479f352569bcf406d9e8e86386afc932`, 37 members; twice, `cmp` exit 0. New `generated_utc` = `2026-10-19T04:14:50Z` (unpinned: this is a genuinely new build, per `scratch/ufixman1/build_archive.sh`'s own header) |

Nothing was uploaded. The `(2)` on-disk extraction was refreshed to equal the new archive (`diff -rq` exit 0);
the other on-disk tree `…/released/encoder-crossover-190-released/` was restored byte-for-byte to its
as-found state (`CITATION.cff` back to `1c1d25ba…`) because `strategy/DEPOSIT_ARCHIVE.md:45` already records
it as a superseded extraction.

## 5. Proof that only the DOI moved

- **Reconstruction, not assertion.** The pre-edit tree was rebuilt in `scratch/udoiback1/paper_pre` by
  reverting only the three hunks, and fed back through the converter with `--paper-root`. Its output is
  byte-identical to the recorded pre-edit `main.tex`: sha256 `397713d74920e9e1bc5f5fb8dc6ef09fb5fa9e641583f0ecd16b718d5f9d09ca`.
  So the diff below is authoritative.
- **`main.tex` diff:** exactly **3** changed lines (`375`, `407`, `427`), every one a DOI sentence; no other
  line touched.
- **Numeric-literal multiset** (regex `\d+(?:\.\d+)?`, counts):
  `MANUSCRIPT.md` shared 1187, **added `{10.5281: 4, 23463945: 3, 23463944: 1}`**, removed `{}`;
  `main.tex` shared 1314, same added set, removed `{}`; PDF extracted text shared 1346, same added set,
  removed `{}`. The DOI contributes only those three tokens; **no published measurement moved**.
- **`recompute-claims.py`** in a fresh extraction of the new archive: exit **0**, `ALL PUBLISHED NUMBERS
  REPRODUCED: True`, `VERDICT: PASS`, fixture digest `c7696edc0e71d83faafc2e489925788e0f36c6af94913674f8953718352c9a55`.
- **`check_manifest.py --package <abs new extraction>`**: `missing=0 hash_mismatch=0 size_mismatch=0
  unlisted=0 listed_but_absent=0`, `VERDICT PASS`, exit **0**.
- **Manifest isolation proof.** Re-running `regen_manifest.py` with `GENUTC` **pinned to the shipped
  manifest's own value** (`2026-10-18T08:05:47Z`) makes the regenerated archive manifest differ from the old
  shipped manifest in exactly four fields — `counts.bytes_total` 844,708 -> 844,877, the `CITATION.cff` entry
  (`1c1d25ba…`/1,837 -> `56300d7c…`/2,006) and `manifest_self`/`generated_utc`. No other entry changed.
- **PDF text diff** (prior 752,747,8 vs new) is the same three paragraphs, reflowed; added numeric tokens
  only the DOI.

## 6. Gaps / out-of-scope (recorded, not acted on)

- **(a) Source of record out of grant.** `strategy/DEPOSIT_ARCHIVE.md:20` records the CITATION input as
  `scratch/uzenodo2/run2/CITATION.cff`; it still carries the pre-DOI text (`1c1d25ba…`, 1,837 B) and is
  **outside** this unit's write paths. So does `scratch/ufixman1/build_archive.sh`, whose guard still pins
  `want_cit=1c1d25ba…` and `want_front=503751f1…` (the README moved to `71f76e60…` under UREADMEFIX1), i.e.
  a future run of the documented build script **fails its own guard** rather than regressing silently.
- **(b) `strategy/DEPOSIT_ARCHIVE.md` digest table not refreshed** (out of write paths) — the archive is now
  159,085 B / `add182e7…` / md5 `479f3525…` / manifest `5afab382…` / `bytes_total` 844,877 /
  `generated_utc` 2026-10-19T04:14:50Z, superseding the 159,014 B row.
- **(c) Rendered non-LaTeX derivatives are stale and were not in this unit's regenerate list.**
  `rendered/encoder-crossover-190.html` (85,507 B, mtime 2026-10-16 22:31) still says
  `DOI: AUTHOR TO CONFIRM — Zenodo DOI to be inserted on deposit` / `no persistent identifier yet` at
  `:988-991` — and differs from the even older wording, so it pre-dates a later `MANUSCRIPT.md` edit.
  `rendered/encoder-crossover-190.docx` likewise not regenerated (`rendered/convert.py` route not exercised).
- **(d) TMLR variant is stale — do not reuse.** `scratch/utmlr5/tmlr/main.tex` (83,785 B, mtime
  **2026-10-18 03:04**) and `scratch/utmlr5/tmlr/main.pdf` (176,971 B, 16 pp), plus
  `scratch/utmlr5/anonymous/main.tex` (84,616 B), all pre-date this unit's `MANUSCRIPT.md` edit
  (2026-10-18 23:14). It must be rebuilt from the final source after this lands. Note for that unit:
  `VUTMLR5` measured `DOI pending` count 0 in the variant (the anonymity scrub dropped the pending phrase);
  the scrub/`anonymous` route will now see a **literal DOI** in three added spans and must decide how to keep
  the TMLR variant anonymous.
