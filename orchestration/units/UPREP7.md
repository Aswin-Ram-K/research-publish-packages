# UPREP7 — Paper #7 submission payload

**Purpose:** Build `papers/gated-read-batching/submission/` (main.tex, ABSTRACT.txt, ABSTRACT_METADATA.txt, METADATA.md, BUILD_NOTES.md, gated-read-batching.tar.gz) from `papers/gated-read-batching/MANUSCRIPT.md`, following the worked example in `papers/encoder-crossover-190/submission/` and converter `scratch/uprep1/md2tex.py`.

**Write paths:** `papers/gated-read-batching/submission/**`, `scratch/uprep7/**`, `orchestration/units/UPREP7.md`, `orchestration/handoffs/UPREP7.json`.

**Hard bound:** 20 tool calls. Read-only access to `/home/zer0null/Duval` (no git commands against it; none were run).

**Converter:** `scratch/uprep7/md2tex.py` (paper-specific; adapts `scratch/uprep1/md2tex.py`). Two sanitisation rules, both reported: drops the leading `**Status:** draft manuscript ...` banner; strips internal unit ids (UFIXGR7 x2).

**Status:** converter written and patched; main.tex generated, run twice, byte-identical; tarball built and verified against on-disk main.tex; METADATA.md + BUILD_NOTES.md pending.
