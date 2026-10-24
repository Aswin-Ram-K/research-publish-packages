# UGATEDAV — data-availability record for `gated-read-batching`

**Purpose (one):** write `papers/gated-read-batching/AVAILABILITY.md` from the paper's own
contents, align `MANUSCRIPT.md`, rebuild LaTeX + `submission/gated-read-batching.tar.gz`,
and recompile clean.

**Bound:** 25 tool calls. Stop condition: if the tarball cannot be made byte-identical
twice or the compile cannot reach exit 0 without `continue-on-errors`, report `partial`.

**Declared write paths**
- `papers/gated-read-batching/AVAILABILITY.md`
- `papers/gated-read-batching/MANUSCRIPT.md`
- `papers/gated-read-batching/submission/**`
- `scratch/ugatedav/**`
- `orchestration/units/UGATEDAV.md`
- `orchestration/handoffs/UGATEDAV.json`

**Forbidden:** `released/`, any other paper, any `git` command against a target repo.

**Status:** done. Wrote `AVAILABILITY.md` (released/withheld/can-and-cannot/licence/no-DOI, each claim checked against the archive), added `MANUSCRIPT.md` §"Data availability" before References and tightened one "reproducing" → "recomputing", regenerated `submission/main.tex` (41,793 B, sha256 8eff5f8c…), rebuilt the tarball twice byte-identical (14,888 B, sha256 45bd955d…), recompiled exit 0 with 0 undefined / 0 `!` lines, 14 pages, PDF 114,746 B sha256 6541bd22…. Numeric literals 373→395 tokens, 0 removed. A stray `papers/scratch/` subtree was created by a relative-path mkdir slip and removed; nothing outside the declared paths now exists.
