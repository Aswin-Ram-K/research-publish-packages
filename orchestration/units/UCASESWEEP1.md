# UCASESWEEP1 — exhaustive case-insensitive leak sweep across all release surfaces

**Status:** DONE — report at `strategy/CASE_SWEEP_REPORT.md` (card persisted before work, per unit contract)
**Parent:** session-c3d61727-8af8-4c19-b1b9-5922c347a11a
**Bound:** 25 tool calls. If a fact cannot be established in 3 attempts, STOP and report it unverified.
**Reports; does not repair.**

## Purpose

Three prior sweeps each reported these release packages clean and each was wrong: #1 missed internal
unit ids and workspace paths; #2 found those but missed the target repo name in four data rows; #3 found
those but missed `"answer": "DUVAL_HOSTED_LAYER_OK"` at `data/gated-read-rows.jsonl:9235` and `:9239`.
The failure pattern is search-for-what-the-previous-sweep-found. This unit searches **every form at once,
case-insensitively, on every surface, including the already-published package**, and reports counts +
per-hit judgement.

## Declared write paths (only these)

- `scratch/ucasessweep1/**`
- `strategy/CASE_SWEEP_REPORT.md`
- `orchestration/units/UCASESWEEP1.md`
- `orchestration/handoffs/UCASESWEEP1.json`

## Surfaces

1. `papers/encoder-crossover-190/released/**` (payload + fresh extraction; **already public on Zenodo — report only**)
2. `papers/gated-read-batching/released/**` (payload + fresh extraction)
3. `papers/replay-record-not-decision/released/**` (payload + fresh extraction)
4. `scratch/uneutral10/package/**` (canonical tree behind paper #3's published deposit)
5. The three papers' `MANUSCRIPT.md`, `CLAIMS.md`, `AVAILABILITY.md`, `GAPS.md`, `README.md`, `submission/main.tex`
6. Public repo working copy if present in this workspace

## Patterns (all case-insensitive)

- `duval` (all forms)
- trace id `2026-09-28` + suffixes `-m0`, `-duval-m0`, `-trace-m0`; `DUVAL_HOSTED_LAYER_OK` any case
- `zer0null`
- `consonance`
- `resextract` and `reserach extarctor`
- internal unit ids `\bU[A-Z]{2,}[0-9][A-Z0-9]*\b` (case-insensitive)
- paths `scratch/`, `tools/package/`, `state/refresh-verify`, `/home/`, `orchestration/`, `strategy/`, `dockets/`
- tooling names reported separately: `deepseek`, `mimo`, `longcat`, `step-5-preview`, `keyring`

## Control (positive-control requirement)

Plant a mixed-case file in `scratch/ucasessweep1/` containing every pattern in mixed case, confirm the
grep returns non-zero on it, and state this in the report. A zero count is only meaningful with a proven
non-zero control.

## Deliverable

`strategy/CASE_SWEEP_REPORT.md`: per-pattern-per-surface counts, every hit with surface / file / line /
literal / one-line judgement, plus explicit answers to (1) is paper #3's published deposit affected,
(2) do the other two archives share the miss class, (3) are there hits in the manuscripts/LaTeX.

## Progress log (complete — 15 of 25 tool calls)

- [x] Read `AGENTS.md`; persist card + handoff first
- [x] Enumerate surfaces; fresh `tar -xzf` of all three archives into `scratch/ucasessweep1/extract/`
- [x] Positive control planted; 19/20 patterns non-zero; the one zero exposed a real defect in my own
      pattern (`zer0null` is digit-zero, control used letter o) — both spellings then searched, both zero
- [x] Case-insensitive sweep, occurrences + matching lines per pattern per surface
- [x] Per-hit detail: file, line, literal, judgement
- [x] `strategy/CASE_SWEEP_REPORT.md` written; handoff written; parent notified

## Result (short)

- **Paper #2 (`gated-read-batching`) still carries the target name**: `"answer": "DUVAL_HOSTED_LAYER_OK"`
  at `data/gated-read-rows.jsonl:9235` and `:9239` (uppercase, in the answer field), trace id
  `2026-09-28-trace-m0` at `:9195,:9196,:9198,:9200`, `CONSONANCE*` corpus names on 225 lines (G-23, open),
  build paths in `README.md:11,15`; tooling names (`deepseek` 9271 occurrences, `mimo-v2.6-flash`, a
  `DEEPSEEK_API_KEY` variable name in `results/GATED_READ_PROVENANCE.md:7`).
- **Paper #1 (public on Zenodo)**: no target name; 2 internal unit ids inside the archive at
  `encoder-crossover-190-released/CITATION.cff:30` (`UDOIBACK1`) and `:31` (`UCONCEPT1`), plus
  `SUPERSEDED-UNPACKED-TREE.md:3,24,25,35,38` (unit id + `scratch/` + `strategy/`) beside the archive.
- **Paper #3 (`replay-record-not-decision`)**: zero hits on every pattern, payload and fresh extraction;
  but its `CLAIMS.md:12–15` carries `state/refresh-verify/duval/...` four times.
- **Card disagreements recorded**: `scratch/uneutral10/package/` is paper #1's canonical tree, not paper
  #3's; the third sweep's miss is in paper #2; paper #3 has no DOI — the only DOI
  (`10.5281/zenodo.23463944`) is paper #1's.
- No repair, no rebuild, no git against any target, no writes outside the declared paths.
