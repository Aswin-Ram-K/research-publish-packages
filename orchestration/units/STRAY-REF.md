# Unit STRAY-REF — stop the stale scratch tree being cited as the package record

- Executed 2026-10-23, session `session-e44f4533-f39a-4436-ab92-a2b37c73a807`, card `c4b4f230-3df8-464e-a4ba-1a2dd19ad986`, execution `d7cd3371` (workspace-write, automated).
- Write paths: `tests/test_no_stray_package_refs.py` (new guard), `orchestration/handoffs/STRAY-REF.json`, `orchestration/units/STRAY-REF.md` (this file). No other file modified; plant was a NEW file removed afterwards (`tests/stray_ref_plant_STRAYREF.md`).

## What was found (sweep evidence)

- `scratch/uneutral10/package/second-labeller/RUN.json` begins `{"_experiment": "G46", "_unit": "G33", "status": "done", "_target_head": "907fa39da7ba8ecfbe6e976b7a4cddadea7ac36b", "_fixture_path_in_target": "P05", ...}` — a **2026-10-16 record of a different experiment/target**, not this package's record. The card's claim is confirmed by the file itself.
- `grep -rn "uneutral10" papers/ tests/ tools/ docs/ *.md` = 19 lines, 5 text files: `papers/encoder-crossover-190/released/SUPERSEDED-UNPACKED-TREE.md:35` (build-inputs row, HISTORICAL), `tests/test_package_tools.py:7,105` + `tests/test_build_wiring.py:7,10` (fixture/wiring pins of the 29-file payload tree), `tools/package/{regen_manifest.py:4,71,classify.py:10,_pkg.py:4,README.md×9}` (tool docs).
- Repo-wide (excluding `scratch/`, `.worktrees/`): 446 lines, nearly all `orchestration/units/*.md` historical unit cards — HISTORICAL by construction.
- `scratch/` cited in papers/ tests/ minus fixrunr2|probe|tmp = 51 lines; HISTORICAL (superseded-tree moves, past-fix attributions, RED-state notes) except three AUTHORITATIVE sites reported as follow-ups below.
- **Zero** lines in papers/ tests/ tools/ co-occur the tree path with a record artefact token — the guard's record-exemption table starts and stays **empty**.

## Guard design (`tests/test_no_stray_package_refs.py`)

1. RECORD-SOURCE rule: a scanned line citing `scratch/uneutral10` **together with** `RUN.json|run.json|EVIDENCE.md|rows.jsonl` fails unless listed in `RECORD_SOURCE_EXEMPTIONS` (empty by measurement — the poisoned form has no sanctioned site).
2. Any other citation must be classified in `CITATION_EXEMPTIONS` with a one-line reason (8 entries: 7 real files + SELF). Unclassified = fail naming `file:line` + the offending line.
3. `test_exemption_tables_have_no_stale_entries` fails on allowlist rot (entry whose file is gone or no longer cites the tree, or empty reason).
- Scan surface: `papers/ tests/ tools/`, suffixes `.py .md .json .sh .txt .toml .cfg .yml .yaml .bib`; `.pyc` excluded by suffix (bytecode, no text skipped). Line-scoped detection, documented as a known limit.
- The guard's own poisoned-path quotes are assembled from two halves (`SCRATCH_TOKEN` + `/package/second-` + `labeller/RUN.json`) so its source does not trip its scanner — no exemption granted to it for record-source lines.

## Red→green (step 4, hard rule)

- Green: `PYTHONPATH=src python3 -m pytest tests/test_no_stray_package_refs.py -q` → **3 passed**.
- RED: planted `| package record | ...scratch/uneutral10/package/second-labeller/RUN.json | the package chain |` in NEW `tests/stray_ref_plant_STRAYREF.md` → **1 failed**, message names `tests/stray_ref_plant_STRAYREF.md:1: treats the stale scratch tree's RUN RECORD as the package record (scratch/uneutral10 + record artefact) — that tree's RUN.json is experiment G46/unit G33 of 2026-10-16, not this package's record`.
- Restored (plant file removed): **3 passed**. No shared file was edited at any point.
- Non-regression: `PYTHONPATH=src python3 -m pytest tests/test_run_record_digests.py -q` → **5 passed** (before AND after).

## Follow-up candidates (classified, not fixed — out of this unit's write scope)

AUTHORITATIVE scratch citations needing a follow-up card (papers prose not editable here):
- `papers/encoder-crossover-190/MANUSCRIPT.md:141` + `CLAIMS.md:21-22` + `AVAILABILITY.md:36` — released paper names `scratch/urever2/verify_divergence.py` (and `scratch/udraft2/recompute_per_variant.py`) as the reproduction path.
- `papers/gated-read-batching/released/SUPERSEDED-UNPACKED.md:41` — imperative "built by `scratch/upkginstall7/build_archive.sh`; do not hand-zip in its place".
- `papers/tmlr/README.md:35` — `scratch/utex1/bin/tectonic -X compile main.tex` as the build command.
