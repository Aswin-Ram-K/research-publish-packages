# UABSTRACT2 — attribution check on the arXiv abstract clause

**Purpose (single):** In `papers/encoder-crossover-190/submission/ABSTRACT_METADATA.txt`, rewrite ONLY the
clause that attributes 0.679 to the decision model, so it reads: the decision model reaches 0.668 against a
same-run baseline of 0.679. Hard bound: 6 tool calls.

**OUTCOME: FAILED — no edit made (do nothing else honoured; manuscript is read-only for this unit).**
Requested change contradicts the manuscript. `MANUSCRIPT.md:313` labels the same-run **0.6789**
`DECLARED PRIMARY BASELINE ... the paired McNemar partner; delta = -0.3316 (0.33)`; `:94` states
`best fine-tuned encoder head 0.3474 against a fine-tuned 4B decider at 0.6789 (auditable, paired) and
0.6684 (published, not re-scorable)`; `:319` makes **0.6684** the *secondary / robustness* figure;
`:341` prescribes exactly the current abstract clause (`the clause naming 0.6789 as declared primary and
0.6684 as secondary`). So 0.679 is already the decision model score and 0.668 is that same model's
published figure — there is no separate "same-run baseline" scored 0.679.

**Evidence:** before char count 1194 (raw 1195 with trailing newline); clause matched exactly 1 time
(asserted before any edit); abstract byte-identical after work (sha256 recorded in handoff run);
grep of MANUSCRIPT.md for `0.6684|0.6789|primary baseline` -> 39 matches; read MANUSCRIPT.md:305-346.

**Files never touched:** `papers/encoder-crossover-190/MANUSCRIPT.md`, `submission/main.tex`,
`submission/REFERENCES.bib`. Abstract file itself left unchanged.

**Write paths:** `papers/encoder-crossover-190/submission/ABSTRACT_METADATA.txt` (unchanged),
`orchestration/units/UABSTRACT2.md`, `orchestration/handoffs/UABSTRACT2.json`, `scratch/uabstract2/**`.
