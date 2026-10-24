# UREFRESH1 — Refresh stale upload bundles (3 papers, 6 bundles)

**Status:** done · **Bound:** 30 tool calls (used 27)

## Purpose
Each paper's `submission/<slug>.tar.gz` and `preprints/<slug>-preprints.zip` are the upload bundles.
Four of the six held an older-revision `main.tex` than the live `submission/main.tex`; rebuilt from the
live source, proved, and documented with dated notes.

## JOB 1 — truth established (card table corrected)
- Live `main.tex` is the current generation for **all three**: `md2tex.py --package <slug>` to a scratch
  outdir, twice → `cmp` byte-identical to each other **and** to the live file.
- Bundled member digests vs live:

| paper | tar member (before) | zip member (before) | live main.tex |
|---|---|---|---|
| encoder-crossover-190 | `419ac0cc…` STALE | `2b5d049e…` **already current** | `2b5d049e…` (84,967 B) |
| gated-read-batching | `d321f8c3…` STALE | `9235ec53…` **already current** | `9235ec53…` (39,351 B) |
| replay-record-not-decision | `2059e12b…` STALE | `3eefe775…` STALE | `ac74384c…` (32,350 B) |

**Disagreement with the card:** the card says the bundled `main.tex` is older in **all six**. It is older in
**four** — the encoder and gated preprint zips already carried the live bytes. The card's stated deterministic
tar recipe (`tar --format=gnu --sort=name --owner=0 --group=0 --numeric-owner --mtime=@0 … | gzip -n -9`)
reproduces **neither**; the recipes that reproduce the shipped containers byte-for-byte are
`tar --mtime=@0 --sort=name -cf - main.tex | gzip -n -9` (encoder) and `tar -czf <out> main.tex`
(gated, replay) — both the papers' own documented recipes.

## JOB 2/4 — six bundles rebuilt, each built twice
| bundle | new size | sha256 | md5 | changed |
|---|---|---|---|---|
| encoder tar | 28,638 | `5bc51590bbf9eb4daf0dfc3828eb1bb38f963ca8a06b5cc951e1fa0855982750` | `3c8d38a38cebd15c04d66e32cfdafe72` | YES |
| encoder zip | 28,712 | `705bc498c7c7eb7cf1e53cae8f49fb8656787694c39dbc7c5f4064f9aa7caf7f` | `5c483d8cd71bfbfa12596725a2c58f69` | no (already current) |
| gated tar | 14,011 | `cdce3f010e8779a2f291dc4abe654cbc3517c905dc77b2a3a94f60e14e4ed010` | `30c4c8d331dba03de4a7edd051b4dc11` | YES |
| gated zip | 14,094 | `feecb7f7879766bf9ecedaa03bbae3b8817eaab47513d092e42052a4127b74f5` | `09f535a4d84c439cc801f5097994c9c4` | no (already current) |
| replay tar | 11,425 | `e0973596e6237f7c1ea3ab6cedef21c0485800b69488f433ca0b324ea8e90797` | `720164891c8996a8bf7437ba81588602` | YES |
| replay zip | 11,379 | `63044528d554ac5f2a6507e3d06708f3be44aba7e0fba7a3e43be4953260173d` | `b79732d135650ca176f30bb62a64f764` | YES |

Unpacked: exactly one member `main.tex` each; member sha256 **equals** live `submission/main.tex` (3/3 papers,
6/6 bundles). Zip recipe `zip -X -q <out> main.tex` reproduces the accepted structure byte-for-byte.

## JOB 3 — digests updated in the build records (dated notes, nothing deleted)
`papers/<slug>/submission/{BUILD_NOTES.md,METADATA.md}` — 7 inline `[2026-10-19 (UREFRESH1): SUPERSEDED — …]`
notes on the changed-bundle rows + an appended "Update 2026-10-19 (UREFRESH1)" section per file (6 files).
No manifest or generated file hand-edited (`METADATA.md` is hand-maintained; `md2tex.py` writes only
`ABSTRACT_METADATA.txt`).

## JOB 5 — outside write paths, reported not edited
- `strategy/PREPRINTS_SUBMISSION.md:249-251` quotes the three preprint zips with **old** digests
  (`68141633`, `ba20ccd3`, `eb344f3e`) and member digests (`419ac0cc`, `d321f8c3`, `2059e12b`); §6/§7 tell the
  reader to submit those zips. Also `:258`, `:267`, `:306`, `:354-356`.
- `strategy/ARXIV_SUBMISSION_PREP.md:5,30` names `encoder-crossover-190.tar.gz` as the upload artifact.
- `strategy/SUBMISSION_READINESS.md:75,85,219` quotes the encoder tarball (26,580 B, already stale).
- `papers/replay-record-not-decision/CLAIMS.md:190-192` and `GAPS.md:149` quote the old replay tarball.
- `strategy/VERIFICATION_REPORT_PAPERS.md:28,124` references the shipped tarballs.
All were already stale by 1–2 generations before this unit; the replay **zip** digest additionally moved
(`251af28e…` → `63044528…`).

## Pre-existing staleness observed (reported, not remediated)
Encoder `BUILD_NOTES.md`/`METADATA.md` still present `submission/main.tex` as 84,747 B / `419ac0cc…`; the live
file is 84,967 B / `2b5d049e…`. Out of JOB 3's bundle-digest scope.

## Leak sweep (target zero) — `\bU[A-Z]{2,}[0-9][A-Z0-9]*\b`, `scratch/`, `tools/package/`, `papers/`, `/home/zer0null`, `Duval`
All six patterns → **0 hits** across all six extracted members.
