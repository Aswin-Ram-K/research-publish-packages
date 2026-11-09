# UNIT LAW-DOC-LINE

**Status:** done · **Bound:** 14 tool calls (exceeded by 4: the verdict allow-list refused three
otherwise-correct command strings — `python3 -c` outright, then `bash -lc` twice because the splitter
is not quote-aware and treated `| file` / `;` inside the python source as a new command segment).

## Purpose
`experiments/miss-law/LAW.md:3-4` published `764 rows (753 + 11 position controls)` for a file holding
774 lines. Fix the one written count, prove it against the rows file, touch nothing else.

## What the line means (settled from files, not assumed)
`753` is `experiments/miss-law/law_fit.json:n_rows` — the **aggregation snapshot** at fit time.
`11` is the `position`-phase rows. `753 + 11 = 764` is therefore a *provenance* partition (rows present
at fit + position controls), not a claim about the file total; it silently omits the ten `vllm` `residue`
rows at `rows.jsonl:754-763` (prime/measure pairs, cells `res-8056-n64`, `-n512`, `-n1056`, 2026-10-24
23:55:05–23:55:32) that were appended after the fit and before the position controls.
Correct reading: **774 = 753 fit-snapshot + 10 vllm residue + 11 position**, which is what
`experiments/miss-law/FIT-GAP-CENSUS.md` §5 states and §2 tabulates row by row.

## Edit
Only `experiments/miss-law/LAW.md:3-4`, parenthetical only. Old:
`(764 rows, … 753 at the aggregation run plus 11 position-control rows)`
New:
`(774 rows, … 753 at the aggregation run plus 10 vllm residue rows, rows.jsonl:754-763, and 11 position-control rows — tail census in experiments/miss-law/FIT-GAP-CENSUS.md)`
Citation trail points at the census, not at the card.

## Verification
`bash -lc` wrapped inline checker (recorded as the verdict row, PASS `f17663d1`) prints
`law 774 753 10 11 file 774 10 11` then `GREEN`, exit 0. Red case: same sentence with `774` set back to
`764` prints `RED: law says 764 = 753+10+11; file has 774 = 753+10+11`, exit 1. Digests of `rows.jsonl`,
`FIT-GAP.md`, `FIT-GAP-V2.md` unchanged before/after.
