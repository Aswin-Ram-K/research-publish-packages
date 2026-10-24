# UPKGINSTALL7 — install paper #7's released area (mirror of paper #3)

Status: done
Bound: 30 tool calls; used ~22.

## Purpose
Paper #7 (`papers/gated-read-batching/`) had a finished package at `scratch/upkg7b/package/`
(10 files). Installed it the way paper #3's release was installed:
- `papers/gated-read-batching/released/` payload dir (12 files) + `CITATION.cff` + `README_DEPOSIT.md`
- deterministic deposit archive `released/gated-read-batching-released.tar.gz`, built twice, byte-identical
- proved with check_manifest.py (payload + extraction), recompute-claims.py, red→green on one byte
- `strategy/CONSOLIDATION_NOTE.md` — author's observation recorded, not actioned

## What was done
1. Read the proven #3 recipe (`scratch/ufixman1/build_archive.sh`) and #3's released tree, CITATION.cff,
   README_DEPOSIT.md. Reused its assembly order; did not edit it.
2. Wrote `scratch/upkginstall7/build_archive.sh`: stages the 10 package files, adds the two deposit
   extras, **regenerates MANIFEST.json inside the stage**, packs
   `tar --format=gnu --sort=name --owner=0 --group=0 --numeric-owner --mtime=@0 | gzip -n -9`,
   twice from two independent fresh stages, `cmp`s them, then installs payload + archive. Guards 6
   inputs by sha256 + file count + rows byte size. Never reads a previous archive.
3. Authored `scratch/upkginstall7/deposit-metadata/{CITATION.cff,README_DEPOSIT.md}` modelled on #3's.
4. Built + installed; verified payload, extraction, recompute, red→green; added
   `papers/gated-read-batching/released/README.md` layout note (which artifact is the deposit).
5. Wrote `strategy/CONSOLIDATION_NOTE.md` (recorded, not actioned).

## Divergence from #3's layout (deliberate, reported)
#3 keeps its two extras' source under `scratch/uzenodo2/run2/` and also a root-level
`released/README_DEPOSIT.md` front matter. Here the extras' source is
`scratch/upkginstall7/deposit-metadata/` and they are installed **only** inside the payload/archive tree;
a second root-level copy would be an independently editable duplicate — exactly the drift #3's
`SUPERSEDED-UNPACKED-TREE.md` records. `released/README.md` names the tarball as the deposit artifact and
tells the author not to hand-zip the unpacked tree (same-stem hazard #3 recorded).

## Write paths
papers/gated-read-batching/**, scratch/upkginstall7/**, strategy/CONSOLIDATION_NOTE.md,
orchestration/units/UPKGINSTALL7.md, orchestration/handoffs/UPKGINSTALL7.json
No git command was run. No write outside these paths.
