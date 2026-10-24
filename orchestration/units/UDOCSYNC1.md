# UDOCSYNC1 — sync stale bundle/member digests in live docs

**Unit:** UDOCSYNC1 (bounded ≤30 tool calls; used 24) · **Status: done**
**Workspace:** `/home/zer0null/reserach extarctor` · 2026-10-19 America/Chicago
Card + handoff were persisted before any work; no `git` run against any target; nothing written under
`papers/*/released/**`.

## JOB 1 — live truth (re-derived from disk, not trusted from the card)

All six bundles and all three `main.tex` re-measured. **Every number on the card matched my re-derivation.**

| artifact | size (B) | sha256 | md5 |
|---|---|---|---|
| encoder `submission/main.tex` | 84,967 | `2b5d049ed7b5368657c227f9efab42a64d1a70304b34813401bf128297ad33cc` | — |
| gated `submission/main.tex` | 39,351 | `9235ec53e581edf0884e7ca9d85e6be696a148d9599f0465af02f7927f635277` | — |
| replay `submission/main.tex` | 32,350 | `ac74384c73d476e89e84e7b5c35a82160a96a6a518adac57bd79929ce339d934` | — |
| encoder `submission/encoder-crossover-190.tar.gz` | 28,638 | `5bc51590bbf9eb4daf0dfc3828eb1bb38f963ca8a06b5cc951e1fa0855982750` | `3c8d38a38cebd15c04d66e32cfdafe72` |
| encoder `preprints/encoder-crossover-190-preprints.zip` | 28,712 | `705bc498c7c7eb7cf1e53cae8f49fb8656787694c39dbc7c5f4064f9aa7caf7f` | `5c483d8cd71bfbfa12596725a2c58f69` |
| gated `submission/gated-read-batching.tar.gz` | 14,011 | `cdce3f010e8779a2f291dc4abe654cbc3517c905dc77b2a3a94f60e14e4ed010` | `30c4c8d331dba03de4a7edd051b4dc11` |
| gated `preprints/gated-read-batching-preprints.zip` | 14,094 | `feecb7f7879766bf9ecedaa03bbae3b8817eaab47513d092e42052a4127b74f5` | `09f535a4d84c439cc801f5097994c9c4` |
| replay `submission/replay-record-not-decision.tar.gz` | 11,425 | `e0973596e6237f7c1ea3ab6cedef21c0485800b69488f433ca0b324ea8e90797` | `720164891c8996a8bf7437ba81588602` |
| replay `preprints/replay-record-not-decision-preprints.zip` | 11,379 | `63044528d554ac5f2a6507e3d06708f3be44aba7e0fba7a3e43be4953260173d` | `b79732d135650ca176f30bb62a64f764` |

`submission/ABSTRACT*.txt` (sha256 / B): encoder `ABSTRACT.txt` `eac59f0e…` 3,462 · `ABSTRACT_METADATA.txt`
`fe678624…` 1,195 · gated `ABSTRACT.txt` `59ef6d55…` 2,120 · `ABSTRACT_METADATA.txt` `05ce7038…` 1,884 ·
replay `ABSTRACT.txt` `5c58912f…` 1,967 · `ABSTRACT_METADATA.txt` `9765d28e…` 1,594.

`MANUSCRIPT.md` (sha256 / B): encoder `53db535c…` 71,485 · gated `2125bee7…` 34,871 · replay `b2d3ce12…` 25,965.

## JOB 2 — stale quotations found (own sweep)

Swept `strategy/*.md`, `papers/*/submission/*.md`, `papers/*/CLAIMS.md`, `papers/*/GAPS.md` for the six
superseded prefixes **and** for every hex run ≥16 chars whose first 8 chars match no live file. (First sweep
used `\b[0-9a-f]{8}\b`, which cannot see a prefix of a 64-char hash — corrected before any edit.)

Sites whose stale value was **presented as current** (all corrected):
`strategy/PREPRINTS_SUBMISSION.md` §5 table `:249-251` (3 zip digests/sizes + 3 member digests/sizes),
`:267`, `:306`; `strategy/SUBMISSION_READINESS.md:85` + `:219`; encoder `BUILD_NOTES.md:10,212,241,331,346`
and `METADATA.md:142`; gated `BUILD_NOTES.md:33,186` and `METADATA.md:156`; replay `BUILD_NOTES.md:21,135-137,171,180`
and `METADATA.md:20,113,122`; replay `CLAIMS.md:192`; replay `GAPS.md:147-151`.

## JOB 3 — corrections (minimal; history kept as dated notes)

Edited **10 files**; no document restructured, no measured result changed, no paper prose touched:
- `strategy/PREPRINTS_SUBMISSION.md` — §5 rows + `:267`/`:306` updated in place; new dated section
  `## Update 2026-10-19 (UDOCSYNC1)` appends the live table + md5s and names every superseded figure
  (incl. the UPREPRINT3 replay row `10,372`/`251af28e…`).
- `strategy/SUBMISSION_READINESS.md` — new dated **Z5** superseding `:85` and Z1.
- encoder `BUILD_NOTES.md` / `METADATA.md` — inline `**[2026-10-19 (UDOCSYNC1): SUPERSEDED — …]**` on each
  `main.tex` "current" claim + a dated update section.
- gated/replay `BUILD_NOTES.md` / `METADATA.md`, replay `CLAIMS.md` / `GAPS.md` — same dated-note treatment.
- Edits applied by `scratch/udocsync1/sync_digests.py`, in which every replacement asserts its expected
  occurrence count and aborts the whole run on a mismatch (two genuine mismatches were caught and fixed this way).

## JOB 4 — proof

- Stale values **presented as current**: before > 20 (the §5 table, `:267`, `:306`, READINESS `:85`/Z1, and the
  `main.tex` "current" rows in the three paper records); **after: 0**. Retained superseded values now appear
  only inside dated notes/sections (Z1, UPREPRINT3, UREFRESH1, UDOCSYNC1, or the files' own `Superseded …` lines).
- Full-sha256 / size-literal counts **before → after**, no file lost a number:
  PREPRINTS 9/7→15/13 · READINESS 2/15→4/19 · enc BUILD_NOTES 64/88→71/99 · enc METADATA 15/23→17/26 ·
  gated BUILD_NOTES 33/33→34/35 · gated METADATA 14/22→15/23 · replay BUILD_NOTES 25/32→28/36 ·
  replay METADATA 25/29→27/32 · replay CLAIMS 6/12→8/14 · replay GAPS 2/4→4/6.

## JOB 5 — upload target check (read-only)

All six containers exist; each holds **exactly one** member `main.tex` whose sha256 **equals** the live
`submission/main.tex` (tar_ok=YES, zip_ok=YES for encode / gated / replay). Every upload path named by the
documents exists with the digest now quoted beside it in `PREPRINTS_SUBMISSION.md` §5.

## Disagreements with the card (reported, not smoothed over)

1. `strategy/ARXIV_SUBMISSION_PREP.md:5,:30` — the file contains **no** digest literal at all (zero hex runs
   ≥16). Nothing stale to correct; **not edited**.
2. `strategy/VERIFICATION_REPORT_PAPERS.md:28,:124` — its hashes are package-tree/source aggregates
   (`4efa5754…`, `a5d32dd7…`, `653d05db…`, `fd9bafd6…`, `2a4cc287…`), not bundle/member digests; `:28`/`:124`
   are prose. No stale bundle quotation; **not edited**.
3. The card's "gated and replay equivalents were updated by the previous unit" holds only for the **tarball**
   rows; their `main.tex` "current" rows were still stale (39,133/`d321f8c3…`, 28,604/`2059e12b…`) and are
   corrected here.
4. `strategy/VERIFICATION_REPORT_DEPOSIT_4.md:104-105` quotes `d321f8c3…` / `2059e12b…` — **outside my write
   paths**, reported only; it reads as that verifier's dated historical record.
5. `strategy/PREPRINTS_SUBMISSION.md` UPREPRINT3 table (`:424-425`) swaps labels `#7 gated-read-batching` /
   `#2 replay-record-not-decision` (§5 has #2 gated, #7 replay). A label defect, not a digest one; left
   unchanged (no restructuring) and reported.

## Write paths honoured
Only the declared paths were written. No `papers/*/released/**` was touched.
