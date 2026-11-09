# UNIT PROSE-VALUE-METRIC

**Purpose.** Compute the quality number a reader would have assumed, as a SECOND metric: read an
asserted answer out of a turn's prose as well as out of the `ANSWER:` contract line, and show how
many frozen non-passes change. Offline, zero requests, no grid re-run.

**Why.** `grade_v5` reads only `^ANSWER:`. A turn that states the answer in prose is filed
`prose_only` -> `never_answered` -> scored "no answer", so `checkpoint_accuracy` is a format-
compliance number wherever the model wrote prose. `NEVER-ANSWERED-ROOT` proved 5 of the 63
never-answered cells state a value (4 wrong, 1 right); this unit turns that into a per-cell column.

**Deliverables.**
1. `experiments/ptr-engine/tools/asserted_value.py` — widened extractor `(value, form, span)`,
   12 forms, 8 documented rejection rules, plus the offline 66-cell recompute driver.
2. `experiments/ptr-engine/measure/PROSE-VALUE-METRIC.json` — 66 cells keyed `grid, arm, checkpoint`
   with `source_sha256` + `rows_sha256` per document, frozen verdict, widened value and
   `match|mismatch|no_value`. `checkpoint_accuracy` untouched.
3. `docs/PROSE-VALUE-METRIC.md` — delta table per arm and overall with BOTH denominators, the six
   changed cells quoted verbatim with exact char counts, and the PARM-1 errata drafted UNAPPLIED.
4. `experiments/ptr-engine/longrun/tests/test_asserted_value.py` — 13 tests, red->green proven.

**Result.** 66 cells / 2 frozen passes / 64 frozen non-passes (63 of them the `never_answered`
set). Of the 64 non-passes, **6 assert a value: 4 wrong, 2 right**. No frozen pass total changes.
The frozen number measures contract compliance — answer production through the required channel —
not pointer mechanics.

**Bound.** <=24 tool calls, 0 requests. Used 22. No grade document, fixture, grader or PARM-1 file
was edited; new files only.
