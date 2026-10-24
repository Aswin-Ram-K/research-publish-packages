# UFIXFMT1 — skeleton card (written before any work; skeleton_written_first=yes)

**Purpose (one):** Apply formatting requirement fixes R17, R18, R6/R7, R36, R39–R43, internal-unit-ID removal,
stale release path correction, and tarball hygiene to the GENERATED submission — every fix in the SOURCE
(`papers/encoder-crossover-190/MANUSCRIPT.md` and/or `scratch/uprep1/md2tex.py`), then regenerate
`papers/encoder-crossover-190/submission/main.tex` and prove fixed point by regenerating twice + `cmp`.

**Hard bound:** 35 tool calls maximum. Report `partial` with remainder named rather than overrunning.

**Declared write paths:**
- `papers/encoder-crossover-190/MANUSCRIPT.md`
- `papers/encoder-crossover-190/submission/*`
- `scratch/uprep1/md2tex.py`
- `scratch/ufixfmt1/**`
- `orchestration/units/UFIXFMT1.md`, `orchestration/handoffs/UFIXFMT1.json`

**Forbidden:** hand-patching `main.tex`; touching numeric claims, abstention thresholds, κ values; building a
PDF; writing outside the workspace.

**Status:** DONE. All eight fixes landed in source; `main.tex` regenerated twice with `cmp` byte-identical
(sha256 `30e162b4cc6d7b3ae97d03141f3a35e808222be8b6d5a90d439878ba9ce85646`, 83,774 bytes); 13 `\bibitem` /
23 `\cite` over 13 distinct keys; 0 non-ASCII; `\begin`/`\end` 32/32; one-member tarball (28,631 bytes);
6 `AUTHOR TO CONFIRM` markers left and tabulated in `submission/METADATA.md`. Not hand-patched; no PDF built.
