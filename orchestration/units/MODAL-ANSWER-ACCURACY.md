# UNIT `MODAL-ANSWER-ACCURACY` — modal answer graded at the 12 declared checkpoints (offline)

**Status:** done · **Bound:** 24 tool calls (used 24) · **Requests:** 0 (offline, zero sockets) · **Date:** 2026-10-26

## Purpose
Grade each era-A arm's **modal** (most frequent) answer against the 12 declared checkpoints with `grade_v5`'s own
functions, and settle whether repetition is an **instruction effect** or an **arm effect**.

## Method (stated before measuring)
1. **Modal pick:** turn rows only (`kind` absent or `"turn"`; `tool-followup` excluded); normalise = strip + collapse
   whitespace runs + case-fold; modal = highest count of `turns`; ties broken by earliest first occurrence in turn order.
2. **Which turns count:** every encoded turn of the arm (denominator = the arm's turn rows in that grid, not 12).
3. **Grading:** `grade_v5.parse_answer_contract` → `grade_v5.grade_cell` vs `grade_v5.derive_truth(LR-01.v6.json)` for
   each of the 12 ids. No contract rule re-implemented; `grade_v5.py` imported only.
4. **Counterfactual rule:** a modal graded at a checkpoint turn it did not appear at is a **counterfactual** and is
   labelled so (Table B of the page). "Observed" (Table C) = the string actually emitted at that turn; even that is
   question-mismatched, because every era-A file ran a v2/v3/v4/v5 fixture, not v6 (`docs/PREREG-ARM-RUN.md:154-158`).

## Population
11 era-A (tools-off) rows files → **29 (grid, arm) groups / 1,109 turn rows**. Excluded: `rows-live-2026-10-26.jsonl`
and `rows.jsonl` (no assistant-content field), and the three `-tools` grids (era B).

## Results
- **Counterfactual: the modal string passes 0 of 12 checkpoints in all 29 groups** (`prose_only` or `unparseable`).
  No group passes any `NONE` item either (0 of 3).
- **Observed:** only 3 checkpoint passes exist in era A, all in one-arm cells, none of them the modal
  (`cell-pointer-stable/182535Z` `cp.0.t12` num_equal, `cp.7.t20` none_confirmed_absent_in_source;
  `longrun-v4` pointer-stable `cp.0.t12` num_equal).
- Headline: `rows-longrun-v4-2026-10-26.jsonl` / `transcript-grow` modal = `I need to read the specified lines of
  resolve.py. ANSWER: NOT-AN-ANSWER`, **x35 of 48**, at **11 of 12** checkpoint turns, **0 pass / 12 undecidable**
  (`unparseable`).
- **Arm effect, not instruction effect:** one fixture, one instruction per grid, modal frequencies 1/1/1/24
  (`rows-longrun-2026-10-26.jsonl`) and 2/35 (`rows-longrun-v4-2026-10-26.jsonl`). Repetition tracks the transcript
  treatment. The `docs/ANSWER-DEGENERACY.md:171-176` discriminator returns neither stated branch (0/12 pass, 0 `NONE`).
- **Read-refusal?** No blanket "cannot access files" refusal. Modals are (a) `read_file` tool-call envelopes the
  tools-off era could not service, or (b) a deferral + `ANSWER: NOT-AN-ANSWER` placeholder. Six x1 truncation
  disclaimers exist on grids that received a (truncated) body. The inviting fixture line is
  `experiments/ptr-engine/longrun/tasks-v5/runtime-v5/LR-01.v6.json:685` — "(answer must be derivable from
  experiments/ptr-engine/ptr_engine/resolve.py#L159)"; the same parenthetical recurs at 695, 715, 725, 745, 755,
  775, 785, 815, 835, 865, 885.
- **Era-B comparability:** no quality comparison is possible. `--tools read_file` services the read (removing the
  modal's cause, though not making the string impossible), so the instrument—not the arm—changes; the provenance gate
  already refuses eraA-vs-eraB (`docs/ANALYSIS-PATH.md:32`).

## Contradictions
None edited. `docs/ANSWER-DEGENERACY.md:19` (x16) agrees. `:171-176` refined (open question answered as "neither").
`:159-161`'s illustrative "64 answered correctly by all four arms" is not realised in era A (two one-arm passes, neither modal).

## Write paths
`experiments/ptr-engine/measure/MODAL-ANSWER.json` · `docs/MODAL-ANSWER.md` · `orchestration/units/MODAL-ANSWER-ACCURACY.md` ·
`orchestration/handoffs/MODAL-ANSWER-ACCURACY.json` · `orchestration/journals/MODAL-ANSWER-ACCURACY.jsonl`
