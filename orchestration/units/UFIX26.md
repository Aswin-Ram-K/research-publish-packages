# UFIX26 — repair unit (four sites)

**Status:** done. **Bound:** 15 tool calls (used 11). **Date:** 2026-10-16.
Wrote only the four named sites plus `scratch/ufix26/**`, this card, and the handoff. No write inside
`scratch/ubij1|ubij2|ubij3/**`, `scratch/upack1/**`, `scratch/unoncensus1|2/**`, `scratch/uver20|21|22/**`,
`scratch/ufix25/**`, `scratch/uwire1/**`, `repro/**`, or `orchestration/units/UBUILD1.build.sh`.

## Task 1 — dead `measure.sh` pointer (COHERENT_BIJECTION_EXTENSION_2.md:358)
BEFORE (occurred exactly 1×):
`` `scratch/ubij3/build-r2.log`), then `bash scratch/ubij3/measure.sh` (log `scratch/ubij3/measure.log`). ``
AFTER: same line, `measure.sh` replaced by a dated 2026-10-16 pointer that states the step-7 projection
digest is **not reproducible by any shipped script** (input `second-labeller/cases.json` does not ship) and
gives the working replacements `python3 scratch/upack1/packaging_surface.py` and
`python3 scratch/ubij1/census_one.py scratch/ubij3/tree-three-r2` (184-identifier list
`scratch/uagnostic1/census.tsv`), citing `scratch/upack1/MEASURE_SH_REMOVAL.md`. Both commands were executed
read-only and ran clean (packaging_surface: 45 files / 43 basenames / 12 dir entries / 10 dir names).

## Task 2 — frozen UVER19 checklist (VERIFICATION_REPORT_19.md:10)
BEFORE (occurred exactly 1×): `- [ ] measure.sh reproduces UBIJ3 numbers`
AFTER: that line **unchanged**, with the house-style blockquote appended directly beneath it:
`> **Note 2026-10-16:** \`scratch/ubij3/measure.sh\` was removed by UPACK1 — it crashed on a \`KeyError\` (\`m["routeB"]\` where the key is \`routeB_primary\`) and read \`second-labeller/cases.json\`, which is not shipped. See \`scratch/upack1/MEASURE_SH_REMOVAL.md\`.`

## Task 3 — unsourced 78 (orchestration/units/UBIJ3.md)
Existing 2026-10-16 UPACK1 note **not altered**; a second dated note appended after the file's last line.
UFIX26 measured, read-only, against `repro/encoder-crossover-190-SANITISED/harness/tccommon.py`:
26 changed pairs (`diff -y --suppress-common-lines | wc -l`), 52 changed lines (`grep -c '^[<>]'`), 84
default-diff lines (`diff | wc -l`), 129 unified lines (`diff -u | wc -l`), 70 `-U0`, 95 `-U1`, 113 `-U2`,
212 `-c`. `prepare.py`: 44 default-diff lines / 13 pairs (reproduces the "44"). **No single definition yields
78**; the only route is the double-count `52 + 26 = 78`. 78 is in fact the `keys` column value for
`tree-three-r2` in UBIJ3's §Results table — a different metric. All other tccommon baselines in the workspace
are byte-identical (0 diffs); `tree-one-r2` gives 6 pairs / 12 lines.

## Task 4 — before-image pin (strategy/SHIP_SET_INTEGRITY.md)
Appended dated note: path `scratch/ubij3/tree-three-b/MANIFEST.json`, sha256
`0553ea51672cb7f8ffa743300e8ee30470b6880870f397db85e6fe66cc993d8c` (20,132 bytes on disk), exclusive total
2,986,505, inclusive 3,008,378 = 2,986,505 + 21,873. `scratch/ubij3/tree-three-r2/` was never written.

## Evidence / containment
Every replacement asserted `old.count == 1` immediately before writing (all four asserted 1×). Post-edit
grep: dated markers present in both strategy files (1 each), second note present (1), before-image pin
present (1), live dead pointer count 0, frozen checklist line intact. `find scratch/ubij3/tree-three-r2
-newer scratch/ufix26/NOTES.md -type f` returned empty. No git command run. No target repo touched.
