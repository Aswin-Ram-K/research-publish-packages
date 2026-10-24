# UFIXTEST2 — update superseded byline test (paper #2)

Goal: `tests/test_md2tex.py` line ~248 asserted paper #2 had no `\author`. The no-byline
decision was superseded by solo authorship (name only, no affiliation), so paper #2 now
emits the same slot as the other two papers:

    \author{AUTHOR SLOT: REAL NAME --- TO BE SUPPLIED}   (main.tex:10, all three papers)

What the old test protected: (a) no author block, (b) no citation apparatus. Only (a)
was superseded, so (b) is preserved verbatim (same three tokens) and still scoped to the
zero-citation paper.

Change: replaced `test_replay_ships_no_author_and_no_citation_apparatus` with
`test_ships_author_slot_placeholder_and_no_citation_apparatus` + two helpers:
`assert_author_slot` (exact placeholder line, exactly once, no other `\author` line —
so a real name can never ship beside or instead of the slot) over all three papers, and
`assert_no_citation_apparatus` (the unchanged `\cite{`/`\bibitem{`/`thebibliography`
guard) for `replay-record-not-decision` only.

Evidence: pytest 6 passed; red demo (scratch/ufixtest2/red_green.py) perturb→FAIL,
restore→PASS on both guards; md2tex.py sha256 unchanged d924c949…1982d2.
Bound: 10 tool calls. Status: done.
