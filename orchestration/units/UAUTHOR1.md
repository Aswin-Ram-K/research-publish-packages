# UAUTHOR1 — affiliation + corresponding-author contact for paper #3

**Status:** done
**Hard bound:** 25 tool calls.

## Purpose
Preprints.org requires author list, affiliations and corresponding-author contact on page 1.
Paper #3 currently has a name only. Add affiliation + contact *through the converter's
per-package configuration* so the change is reproducible, then rebuild and prove the payload.

## Author's decisions (final)
- Name: `Aswin Ram Kalugasala Moorthy` (already in place)
- Affiliation: `Independent researcher`
- Corresponding-author contact: `aswinram.k.1603@gmail.com` (deliberately public)
- Scope: **paper #3 only** (`papers/encoder-crossover-190/`). Papers #2 and #7 stay name-only.

## Tasks
1. Add affiliation + contact to paper #3 config in `tools/package/md2tex.py`; keep #2/#7 unchanged;
   keep the author-slot assertion meaningful (pin the new exact lines; still reject invented author/affiliation).
2. Regenerate `submission/main.tex` + tarball; generate twice and `cmp` for byte-identity.
3. Prove no published number moved: bibliography-stripped numeric-literal multiset identical
   before/after; counts 13 bibitem / 23 cite / 13 distinct / 0 uncited / 0 unresolved unchanged.
4. Recompile with Tectonic: literal exit code, `Undefined control sequence` count, `!` count, page count.
   Affiliation + email on page 1 of extracted text; nowhere unexpected.
5. Run `PYTHONPATH=src pytest tests/test_md2tex.py -q`; report literal result line.
6. State whether the anonymised TMLR variant is now stale (do not rebuild it).

## Bound / stop condition
If the converter's registry cannot express a per-package affiliation, STOP and report that as the blocker
rather than special-casing paper #3 outside the converter.

## Write paths
`tools/package/md2tex.py`, `papers/encoder-crossover-190/submission/**`,
`papers/encoder-crossover-190/MANUSCRIPT.md`, `papers/encoder-crossover-190/METADATA.md`,
`tests/test_md2tex.py`, `scratch/uauthor1/**`, `orchestration/units/UAUTHOR1.md`,
`orchestration/handoffs/UAUTHOR1.json`
