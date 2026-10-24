# GUARD-G5B — make the G5 attribution guard bite at every site

**Status:** done. **Bound:** 15 tool calls (stayed within). **Write paths:** only
`tests/test_g5_fanout_attribution.py`, `orchestration/handoffs/GUARD-G5B.json`,
`orchestration/units/GUARD-G5B.md`, plus temporary MANUSCRIPT.md edits restored
byte-identically (proven by `cmp`).

## What was built
`tests/test_g5_fanout_attribution.py` walks every `6.744` occurrence in
`papers/context-cache/*.md` (17 found) and requires, in the SAME site — the
sentence between real periods (digit-aware, so `4.045` never splits a sentence),
or for markdown-table cells the row plus its table's column-header line — a G5
provenance token `pre-G5` cannot satisfy: `PROVENANCE_RE = re.compile(r"(?<!pre-)\bG5\b")`.
This is exactly the V-PAPER3 failure mode: the old bare-`G5` check was satisfied
by the `pre-G5` supersession phrase.

Four sites cannot carry same-sentence provenance without rewriting prose (not
allowed here) and are explicit named exemptions with written reasons in `EXEMPT`:
MANUSCRIPT.md:163 (§3 figure sentence; provenance in the pinned bold lead-in,
guarded by `test_paper_attribution_guard.py::test_g5_fanout_attribution_is_present`),
MANUSCRIPT.md:152, MANUSCRIPT.md:168, GAPS.md:221. `test_exempt_sites_are_live`
fails if an exemption stops matching an unattributed site, so the list cannot rot.

## Red→green (two sites, one abstract)
- Abstract: removed `(cell G5,` from MANUSCRIPT.md:16 → `1 failed` naming
  MANUSCRIPT.md:16 (the `pre-G5` token in the same sentence did NOT satisfy the
  guard — the point of the anchored regex). Restored: `cmp` identical.
- Non-abstract: removed `from cell G5` from MANUSCRIPT.md:157 → `1 failed` naming
  MANUSCRIPT.md:157. Restored: `cmp` identical.

## Results
- `pytest tests/test_g5_fanout_attribution.py -q` → **4 passed**
- `pytest tests/test_paper_attribution_guard.py tests/test_paper_claim_census.py tests/test_claims_decompose.py -q` → **39 passed** (existing §3 assertion kept, not weakened)

## Trap fixed
Baseline first failed on MANUSCRIPT.md:131 (table row): the header lookup only
examined the single line above the row (another data row), so `B/A (live, G5)`
was never seen. `_table_header_line` now walks up through all contiguous
`|`-lines to the separator and takes the line above it.

Zero live requests. No files outside the three write paths persist.
