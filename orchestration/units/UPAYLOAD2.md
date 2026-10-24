# UPAYLOAD2 --- submission payload for `replay-record-not-decision`

Status: done.  Bound: 25 tool calls.  Write paths honoured (no writes to the other two papers).

## Approach
Read all four documents; concluded the paper cites nothing external, ships no author block, and
carries internal record names in its prose.  Added a third `PACKAGES` entry to the existing converter
and extended the registry minimally (per-package `author_line`, `bib_source="none"`, `expect_zero_bib`,
and `dename_rules`) so that the zero-citation case is handled positively instead of by disabling the
guard.  Generated the payload, rebuilt the one-member tarball by hand, added two tests (one red->green).

## Evidence
- `main.tex` 20,631 B / sha256 `0520d2059734f8381227fdf0bff51fd006bb88b46635419b7dbc07ddd5bdd0d5`; two runs `cmp` byte-identical.
- tarball 7,215 B / sha256 `7294cad8a3d8cbb0c4e933643767ba9e454cceadb391c1137f9b4454bc62270c`; exactly one member; extracted == source.
- `4efa5754...` (encoder) and `a5d32dd7...` (gated) both reproduced byte-identically after the converter changes.
- `pytest tests/test_md2tex.py --noconftest` -> 6 passed.
Full detail: `papers/replay-record-not-decision/submission/{METADATA,BUILD_NOTES}.md`.
