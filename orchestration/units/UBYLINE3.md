# Unit UBYLINE3 — install author byline in three papers

**Purpose**: put the author-supplied name into all three papers, regenerate payloads,
update records and the byline guard test. One purpose, no scope creep.

**Hard bound**: 20 tool calls. Stop-and-report if any pre-read digest mismatches
(concurrent editor) or if paper #2 files change under us (defer paper #2 only).

**Declared write paths**
- tools/package/md2tex.py
- tests/test_md2tex.py
- papers/encoder-crossover-190/**, papers/gated-read-batching/**, papers/replay-record-not-decision/**
- orchestration/units/UBYLINE3.md, orchestration/handoffs/UBYLINE3.json
- scratch/ubyline3/**

**Name**: `Aswin Ram Kalugasala Moorthy` (verbatim; no affiliation — standing author decision).
Shipped line: `\author{Aswin Ram Kalugasala Moorthy}`

**Pre-flight digests (verified 2026-10-16)**: all three matched the card exactly —
main.tex 84,358 B / `4efa5754…885a`; 37,291 B / `a5d32dd7…86b4`; 20,969 B / `61767248…5a23`.

**Invariants to preserve**: 13/13/0 bibitems for papers 1 and 2, 0 by design for paper 3;
0 non-ASCII introduced; `\begin`/`\end` balanced; exactly one `\author` line per paper;
numeric-literal multiset unchanged; citation guard still hard-fails.
