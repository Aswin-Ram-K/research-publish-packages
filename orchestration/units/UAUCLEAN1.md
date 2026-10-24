# UAUCLEAN1 — clean internal-id leak, rebuild+re-prove, build Zenodo archive, write deposit record

## Purpose
Make the release payload clean (no internal unit ids) and produce the exact single archive a Zenodo
deposit takes, with the package's own verification re-proved after the edit.

## Hard bound
25 tool calls. If something cannot be verified in 3 tries, STOP and report.

## Declared write paths
- `scratch/uneutral10/package/**` (release payload; authoritative tree the build promotes)
- `strategy/ZENODO_DEPOSIT.md`
- `orchestration/units/UAUCLEAN1.md`, `orchestration/handoffs/UAUCLEAN1.json`
- `scratch/uauclean1/**`

NOT touched: `orchestration/units/UBUILD1.build.sh`, `tools/package/**`, `papers/**`,
`/home/zer0null/Duval` (read-only, no git).

## Jobs
1. Genericise the internal-unit signature at `scratch/uneutral10/package/second-labeller/RUN.json:13`
   (`_sha256_labels_note`, "SUPERSEDED 2026-10-16 (UFIXPKG13)") and
   `scratch/uneutral10/package/results/REPORT.md:5` ("[corrected 2026-10-16 by UFIXPKG13: ...]"),
   keeping meaning: what changed, when, current values; 369159b0…(81284 B) -> 89e77a8e…(81439 B);
   as-audited source 076164ac…(145031 B) unaffected. Re-sweep payload for `\bU[A-Z][A-Z0-9]{2,}[0-9]*\b`
   and the listed unit-name prefixes.
2. Regenerate `MANIFEST.json` via `scratch/ufixpkg3/rebuild_manifest.py` (no hand-editing).
   Prove: the 3 scripts exit 0 + `VERDICT: PASS`; fixture-correctness digest
   `c7696edc0e71d83faafc2e489925788e0f36c6af94913674f8953718352c9a55`; `tools/package/check_manifest.py`
   zero mismatches with `counts.files == 29`; second regeneration idempotent apart from `generated_utc`;
   no published number moved (before/after).
3. Build `scratch/uauclean1/zenodo/research-publish-packages-encoder-crossover-190-v1.zip`
   (29 files at archive root, `zip -r -X`), `.sha256`, `ZENODO_UPLOAD.txt` (title, creators, description
   from `papers/encoder-crossover-190/submission/ABSTRACT_METADATA.txt`, resource type, keywords,
   licence read from payload `LICENSE`/`COMMERCIAL.md`, version v1). Prove: member list, count == 29,
   extract + `diff -r` vs payload identical.
4. `strategy/ZENODO_DEPOSIT.md` — deposit record, digest, extraction result, reader gets, licence terms,
   honest limits (harness withheld; numbers verified but not re-measurable).

## Status
in progress
