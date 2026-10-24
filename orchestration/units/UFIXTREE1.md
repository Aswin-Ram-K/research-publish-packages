# UFIXTREE1 — five candidate release trees: which is authoritative

**Purpose:** decide by measurement which candidate tree reproduces the numbers
`papers/encoder-crossover-190/` publishes; report the exact re-pin line for
`orchestration/units/UBUILD1.build.sh:134` WITHOUT applying it; settle the `repro/encoder-crossover-190/`
mirror question.

**Hard bound:** 25 tool calls. **Used:** 19 bash/write calls; **status: done.**

**Declared write paths (no clashes):** `scratch/ufixtree1/**`,
`orchestration/units/UFIXTREE1.md`, `orchestration/handoffs/UFIXTREE1.json`,
`strategy/AUTHORITATIVE_TREE.md`.

**Read-only honored:** `/home/zer0null/Duval` never opened; no candidate tree, build script, or `papers/**`
edited; no mutating git. All tool runs happened in copies under `scratch/ufixtree1/copies/`.

## Result
- **Authoritative tree: `scratch/uneutral10/package`** — the only tree whose shipped tools reproduce
  all four published values with all three tools exiting 0.
- Current pin `scratch/urecut1/package` is **stale**: route A κ `0.32520740993294694` (published
  `0.3248813212427869`) and A/B mutual `0.3526315789473684` (published `0.3684210526315789`).
- `scratch/ufix31/pkg`: `recompute-claims.py` exit **1**, `ALL CLAIM NUMBERS PRESERVED: False`.
- `scratch/utool1/tree-six`: same stale numbers as the pin, all exits 0.
- `scratch/udtag1/tree-five`: `parse_fixture.py` and `compare.py` exit **1** (FileNotFoundError).
- Fixture correctness digest `c7696edc…` identical in all five → non-discriminating; published fixture
  sha256 is `076164ac…` (`CLAIMS.md:46`).

## Pin change (NOT applied)
`orchestration/units/UBUILD1.build.sh:134` →
`PROMOTED_SAN_SRC="$SRC/scratch/uneutral10/package"`

`SHIP_STAGED` needs no re-derivation (identical 29-file path set; its hit-count annotations should be
re-measured). `tests/test_build_wiring.py` stays green: 11 passed baseline and 11 passed with the re-pinned
script copy via `UWIRE3_BUILD_SCRIPT`.

## Mirror
`repro/encoder-crossover-190/` is still referenced (sanitiser input: `redact.py:2`,
`REDACT3_REPORT.md:48`; integrity docs `INTEGRITY.md:108`, `SCRUB_REPORT.md:394`). Corrections measured:
manuscript names `results/DEFECT-EVIDENCE.json` at `CLAIMS.md:82`, `MANUSCRIPT.md:424,751` (saying it is
*not* released) — not 0 occurrences; the file IS present in the raw and sanitised trees; MANIFEST has one
`files[]` entry, not two. Recommendation: keep the mirror, open the manuscript-vs-disk contradiction
separately. Nothing deleted or edited.

## Status log
- [t0] skeleton + handoff written before any measurement. `skeleton_written_first: yes`
- [t1] published values quoted from `CLAIMS.md:46,108,110,111`.
- [t2] 5 trees copied, 15 tool runs recorded with literal exit codes (`scratch/ufixtree1/out/`).
- [t3] re-pin simulated on a script COPY; wiring test 11 passed both ways.
- [t4] findings written to `strategy/AUTHORITATIVE_TREE.md`.

## Evidence
- `scratch/ufixtree1/out/<tree>.<tool>.txt` (15 files), `scratch/ufixtree1/copies/**`,
  `scratch/ufixtree1/UBUILD1.repin.build.sh`.
- Detail: `strategy/AUTHORITATIVE_TREE.md`.
