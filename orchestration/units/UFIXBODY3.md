# UFIXBODY3 — remove editorial instructions from paper bodies, correct false statements

**Purpose.** Three papers (`encoder-crossover-190`, `gated-read-batching`, `replay-record-not-decision`)
carry in-body editorial instructions addressed to the author. At least one is also factually false
(`encoder-crossover-190/MANUSCRIPT.md:874` claims the manuscript names no author; it now names
`Aswin Ram Kalugasala Moorthy`). A submitted paper must not contain notes telling someone to edit it.

**Hard bound.** 22 tool calls. Stop and report `partial` with the remainder named if exceeded.

**Declared write paths.**
- `papers/encoder-crossover-190/MANUSCRIPT.md`, `papers/gated-read-batching/MANUSCRIPT.md`, `papers/replay-record-not-decision/MANUSCRIPT.md`
- `papers/*/submission/main.tex`, `papers/*/submission/*.tar.gz` (regenerated only)
- `papers/*/submission/BUILD_NOTES.md`, `papers/*/submission/METADATA.md`
- `orchestration/units/UFIXBODY3.md`, `orchestration/handoffs/UFIXBODY3.json`
- `scratch/ufixbody3/**`

**Constraints.**
- `/home/zer0null/Duval` strictly read-only; never run git against it.
- `submission/main.tex` is GENERATED — never hand-edit; edit `MANUSCRIPT.md` then
  `python3 tools/package/md2tex.py --package <slug>`.
- No change to any measured number, claim, reference or bibliography entry. Voice and truth only.
- Never invent author facts (contribution statement, affiliation, funding, competing interests).
  Remove the instruction and record it as an open author item instead.
- Same author name applied to all three papers (`Aswin Ram Kalugasala Moorthy`).

**Plan.** (1) sweep hit list from all three `MANUSCRIPT.md` and test each hit for shipment into
`submission/main.tex`; (2) fix by class — delete directorial text, correct false statements, leave
genuine author decisions open; (3) de-stale `METADATA.md` Comments fields; (4) regenerate, rebuild
tarballs, recompile all three with `scratch/utex1/bin/tectonic`, install PDFs, verify from extracted
PDF text; (5) numeric-multiset diff of pre/post `main.tex` with bibliography stripped must be zero
added / zero removed; (6) run `tests/test_md2tex.py` if guards are touched.

**Status.** done (17 tool calls of 22). Six `AUTHOR TO CONFIRM` directives removed from
`papers/encoder-crossover-190/MANUSCRIPT.md` (:856, :869, :874, :880, :886, :892); the false clause
"The manuscript names no author" replaced with the true byline; the other two papers contained no
directive-class text. All six directives were left undecided and recorded as open author items in
`orchestration/handoffs/UFIXBODY3.json`. Regenerated all three via `tools/package/md2tex.py` (two runs
byte-identical), rebuilt tarballs (1 member each, byte-identical to shipped `main.tex`), compiled all
three with `scratch/utex1/bin/tectonic` (exit 0, 0 undefined control sequences, 0 `!` errors), installed
`rendered/*.pdf` (encoder 24 pp, gated 13 pp, replay 9 pp; all A4), and proved 0 added / 0 removed
numeric literals in each body with the bibliography stripped. `tests/test_md2tex.py`: 7 passed.
