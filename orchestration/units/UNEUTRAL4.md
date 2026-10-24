# UNEUTRAL4 — independent verification of C′ + report on C′ measurement

**Status:** done.
**Predecessor:** UNEUTRAL3 (died before writing its report; its card/handoff are deliberately left untouched
as the record of the failed unit — its `next_unit_hint` points at `strategy/CPRIME_MEASUREMENT.md`, which did
not exist until this unit wrote it).
**Purpose (one):** independently verify or contradict UNEUTRAL3's C′ claims (`tree-pinned` → `tree-stripped` →
`tree-bij`) and write the owed deliverable `strategy/CPRIME_MEASUREMENT.md`.
**Hard bound:** ≤35 tool calls. Used: 30 (28 productive + 2 reads). No bound hit.
**Declared write paths (only these were written):**
- `scratch/uneutral4/**`
- `strategy/CPRIME_MEASUREMENT.md`
- `orchestration/units/UNEUTRAL4.md`
- `orchestration/handoffs/UNEUTRAL4.json`

Nothing under `scratch/uneutral3/**` was modified (tooling was run in place only where it writes into the
tree's own `second-labeller/` sandbox outputs; all my measurement copies live under `scratch/uneutral4/`).
The live tree `repro/encoder-crossover-190-SANITISED/` was never modified; `papers/**` untouched;
`/home/zer0null/Duval` untouched; `orchestration/units/UBUILD1.build.sh` never run;
`/home/zer0null/research-publish-packages` never written. The tag↔original map M was never written to disk
or logged by me.

## What was done

1. Copied the three trees verbatim to `scratch/uneutral4/t/{pinned,stripped,bij}` and re-ran every diagnostic
   (`bash scratch/uneutral3/run_diags.sh <tag> <copy>`, plus `verify/recompute-claims.py`) on all three.
2. Re-ran the census with the only scanner that exists (`scratch/uneutral2/census2.py`, ids from
   `scratch/uagnostic1/census.tsv` col 2) on all three trees.
3. Re-measured bytes (`wc -c`, per-tree `find -printf '%s'` sums, per-field JSONL sums).
4. Re-derived the consumed/dead field list by reading read-sites in `harness/train.py`, `harness/tccommon.py`,
   `harness/prepare.py`, `harness/evaluate.py`, `harness/analyze.py` and grepping for stripped-field readers.
5. Re-ran JSONL parseability, `parse_fixture.py`, `compare.py`, `recompute-claims.py`, `compileall`.
6. Wrote `scratch/uneutral4/floor.py` (case-insensitive, decoded-value + key walk) to split residual
   occurrences into inside-stimulus / outside-values / JSON-keys; wrote `scratch/uneutral4/bij_det.py`
   (DST-parametrized copy of `bij.py`) to test bijection determinism and reproduce `tree-bij` byte-for-byte.
7. Counted fixture questions containing a real live-kind token (23/190 word-boundary — reproduced).
8. Verified the tutorial's trap: `recompute-claims.py` prints `ALL CLAIM NUMBERS PRESERVED: True` even on the
   tree whose digest moved.

## Headline findings

- **Reproduced [U3≡U4]:** strip moves no number (byte saving −2,062,152 B; all metrics + fixture digest
  identical); pinned census 26,344/99; stripped census 9,247/99; 23/190 fixture questions carry a real kind
  token; the bijection moves the fixture-correctness digest but no metric.
- **Contradicted [U3✗U4]:** bij census claim `8,213 / 99` → measured `5,384 / 95`. On-disk `tree-bij` and my
  two fresh rebuilds all give that; the claim's build (`rt/bij`) is a superseded 20:06 build.
- **Contradicted [U3✗U4]:** bij digest claim `30b75581…` → measured `c7696edc0e71d83faafc2e489925788e0f36c6af94913674f8953718352c9a55`
  for the on-disk tree and both rebuilds. The phenomenon (digest moves) is reproduced; the value is not.
- **New:** the pinned census overcounts by ~36%: 9,531 raw-line hits are `"\nKind"`/`"\nCandidate"`/
  `"\nSituation"` escape artifacts matched as `nKind`/`nCandidate`/`nSituation`; the decoded-value walk gives
  pinned 16,813 vs raw-line 26,344.
- **New:** the irreducible floor is 2,171 occurrences of 30 distinct identifiers **inside the model's
  stimulus** (`question`/`options`/`situation`), identical in all three trees. Zero project vocabulary is
  **not** reachable while keeping the published numbers.
- **New:** `prepare.py` refuses (exit 2, corpus digest 58b09a3c… vs frozen c78681d6…) in pinned too — the
  refusal is pin-induced and pre-existing, not caused by the strip; the released tree cannot regenerate its
  own JSONL. `KIND_ALIAS` already resolves 0/9 corpus kinds in pinned, so the bijection adds no new alias break.
- **Verdict:** ship `tree-stripped`; `tree-bij` is measured-but-not-shipped (two-vocabulary artifact: renamed
  data vs pinned tooling; +38,534 B saved = 1.24%).
- **Field audit:** the strip's dead-field list is correct; read-sites for every kept field are in the report.

## Artifacts (all under `scratch/uneutral4/` unless stated)

`audit.py`, `floor.py`, `residual-floor.txt`, `census-rerun-{pinned,stripped,bij}.txt`, `bij_det.py`,
`bij_run1/`, `bij-run2/`, `t/{pinned,stripped,bij}/`, `prepare-stripped.out`,
`strategy/CPRIME_MEASUREMENT.md` (323 lines, 21,748 B, sha256 `13d0712ebecf77a086747115fcda7e21d989642aa8a001e5c17d7e015f338dcb`).

## UNVERIFIED

No model was run (torch/transformers untested); "numbers preserved" covers metric recomputation and stored-
label diagnostics only. The claimed bij census/digest have no on-disk source. `gen-pinned.log` records no
command line for the pinned build. `prepare.py` regeneration never completed (refuses in every tree). The
pinned raw-line surplus is attributed by arithmetic + spot-check, not enumerated line by line. `train.py`/
`evaluate.py` were compiled and read, not executed. No exhaustive on-disk search for a leaked map M.
