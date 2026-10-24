# UFIXCITE5

**Purpose.** Two content defects in paper #3 (`encoder-crossover-190`), then regenerate + prove.

1. `papers/encoder-crossover-190/MANUSCRIPT.md:854` cites an internal workspace path
   `strategy/licence-templates/RELEASED-PIECE/`. Rewrite so it points at the released package's own
   shipped files (`LICENSE`, `COMMERCIAL.md`, `CONTRIBUTING.md` at the root of the deposit archive's
   `encoder-crossover-190-released/`). Meaning + licence statements unchanged. Generated form lives at
   `main.tex:423`.
2. `papers/encoder-crossover-190/submission/BUILD_NOTES.md` carries a stale tarball figure
   (28,556 B / sha256 dc4da66c…) at lines 88, 211, 239, 251. Measure the real current value from disk,
   correct all four, keep the superseded value as dated history following the existing
   `[UFIXNOTE1 2026-10-16: SUPERSEDED — …]` convention at `:88`.

**Hard bound.** 12 tool calls. If a before-string does not occur exactly once, STOP and report.

**Write paths (nothing else).**
`papers/encoder-crossover-190/MANUSCRIPT.md`, `papers/encoder-crossover-190/submission/**`,
`scratch/ufixcite5/**`, `orchestration/units/UFIXCITE5.md`,
`orchestration/handoffs/UFIXCITE5.json`

**Do NOT.** Edit papers #1/#2, `tools/package/**`, `scratch/uneutral10/package/**`, the released archive;
change any number/claim/table/figure (only permitted numeric change is the corrected tarball size in
BUILD_NOTES.md); call any network API; write outside the listed paths.

**Definition of truth.**
- `git`-free: pre-edit copies saved to `scratch/ufixcite5/pre/`, then `diff` must show only intended hunks.
- Regenerate: `python3 tools/package/md2tex.py --package encoder-crossover-190` (never hand-edit main.tex).
- Tarball: `tar --mtime=@0 --sort=name -cf - -C <submission> main.tex | gzip -n -9`, built twice, byte-identical.
- Report new byte sizes + sha256 of `main.tex` and the tarball.
- Numeric-literal multiset delta: before total / after total / exact per-token diff for
  `0.6789 0.3474 0.4526 0.6684 4.167 0.33 0.32 152,000`.
- Bibliography integrity: 13 `\bibitem` / 23 `\cite` / 13 distinct / 0 uncited / 0 unresolved.
- Compile: `scratch/utex1/bin/tectonic`, `TECTONIC_CACHE_DIR`/`TMPDIR`/`HOME` exported, no
  `-Z continue-on-errors`; report exit code, `Undefined control sequence` count, `!` count, page count.
- `PYTHONPATH=src pytest tests/test_md2tex.py -q` literal result line.
- 0 occurrences of `strategy/licence-templates` in `MANUSCRIPT.md` and in `main.tex`.
