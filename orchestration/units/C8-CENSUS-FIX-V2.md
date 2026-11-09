# C8-CENSUS-FIX-V2 — recover the top-ranked retriable unit: the 21-row census, isolated, with a verdict

**Purpose (one).** Deliver the corrected 21-row census the failed `C8-CENSUS-FIX` was chartered for, in
isolation, with a citation-resolving checker and a verdict row. Bound: 24 tool calls; offline; zero inference.

**Declared write path:** `experiments/miss-law/FIT-GAP-CENSUS.md` (journal-first, announced before the write).

**Why not `experiments/miss-law/FIT-GAP.md`.** That path no longer holds a census; it holds a tombstone
(`sha256 70bd26aa…`, 52 lines) that withdraws the file, forbids citation below line 6, and names
`experiments/miss-law/FIT-GAP-V2.md` as superseder with "no fourth is attempted"
(`experiments/miss-law/FIT-GAP.md:1-6`). Overwriting it would destroy a later unit's withdrawal ruling.
`FIT-GAP-V2.md` (`sha256 8b0709a0…`) partitions all 774 rows but carries **no 21-row tail census**, so the
census was genuinely absent on disk and the recovery target is a new, non-conflicting path.

**What the census establishes.** The 21 appended rows (lines 754–774) are
10 `vllm` `residue` rows (**5 `prime` + 5 `measure`**, `n_payload` 64×2 · 512×4 · 1056×4) and
11 `sglang` `position` `measure` rows (`n_payload` 1). `role != measure` is **5**, not the 0 the withdrawn
file printed. Class `DEFECT` → **`SNAPSHOT-LAG`**; OUTLIER 0 / LAW GAP 0 retained; C8 **NARROWED**, not closed.
The non-circular test re-runs exactly: `sglang 232 = 232 − 0`, `vllm 73 = 78 − 5`, and the five-row shortfall
*is* the five `vllm` residue `measure` rows of the tail.

**Checker.** `experiments/ptr-engine/tools/c8_census_check.py` parses the document, re-opens each cited line of
`rows.jsonl`, compares every claimed field, re-derives all eight section-1 totals, re-runs the
`onfile − intail == n_residue_rows` prediction for both servers, and resolves all 31 `path:line` citations.
Green `exit 0`; three mutations under `/tmp/c8-census/red{A,B,C}` each `exit 1`.

**Isolation.** One repo write beyond this unit's own artefacts: the census document. No running card declares
`experiments/miss-law/` (board revision 4472: `WIRE-PROVENANCE-INTO-STATS`, `HARNESS-MAP-V3`,
`QUALITY-ERA-TABLE`, none touching this path). Inputs `rows.jsonl`, `law_fit.json`, `agg.py`, `LAW.md`,
`FIT-GAP.md`, `FIT-GAP-V2.md` byte-identical pre/post.

**Not inherited as verified.** Claims about `defect 321`, the `Bprobe-400` row, and duplicate `sglang-h*` pairs
belong to `FIT-GAP-V2.md` and were outside this brief; this census does not assert them.
