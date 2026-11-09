# MODAL-ANSWER — what each era-A arm's most repeated string grades at the 12 declared checkpoints

**Unit:** `MODAL-ANSWER-ACCURACY` · **Date:** 2026-10-26 · **Live requests spent: 0** (offline, zero sockets).
**Artifact of record:** [`experiments/ptr-engine/measure/MODAL-ANSWER.json`](../experiments/ptr-engine/measure/MODAL-ANSWER.json).

## What this is not

- **Not a re-grade of any run.** No rows file, grades file or published number is read or modified; the grader is imported, not edited.
- **Not an accuracy denominator for H3.** A modal string graded at a turn it never appeared at is a *counterfactual*; it cannot enter `checkpoint_accuracy`.
- **Not a substitute for `checkpoint_accuracy`.** The grade owns `x/12`; this page only says what one repeated string would score if it were the arm's answer everywhere.

## Method (stated before measuring)

**1. How the modal answer is picked.** Only *turn rows* count (`kind` absent or `"turn"`; `kind == "tool-followup"` is excluded); text is normalised exactly as `ANSWER-DEGENERACY` did — strip, collapse every whitespace run to one space, case-fold — and the modal is the normalised string with the highest count of turns, ties broken by **earliest first occurrence in turn order**. **2. Which turns count.** Every encoded turn of the arm counts toward the frequency denominator (the arm's turn rows in that grid, not 12), including turns at which the string is not a checkpoint answer. **3. How it is graded.** For each of the 12 declared ids the modal string is parsed by `grade_v5.parse_answer_contract` and graded by `grade_v5.grade_cell` against `grade_v5.derive_truth(tasks-v5/runtime-v5/LR-01.v6.json)`; no contract rule is re-implemented and `grade_v5.py` is not modified.

**The counterfactual rule, stated plainly.** A modal answer graded at a checkpoint turn **it did not appear at** is a **counterfactual** and is labelled as such in Table B. Table A is the weaker *observed* claim: it grades the string the arm actually emitted at a turn that is a checkpoint turn in the v6 fixture — but every era-A rows file was produced against a **v2/v3/v4/v5 fixture** (its `fixture_sha256` differs from the v6 one), so even the observed cells answer a different question than the v6 checkpoint asks. This is the already-recorded id disagreement at `docs/PREREG-ARM-RUN.md:154-158`; it is why `docs/PREREG-ARM-RUN.md:159` says no existing row file can adjudicate H3.

**Population.** era A = tools **off**. Included: the 11 era-A rows files that carry a turn answer field (29 `(grid, arm)` groups, 889 turn rows). Excluded with reason: `rows-live-2026-10-26.jsonl` and `rows.jsonl` (no assistant-content field, repetition not computable), and the three `-tools` grids (era B: `read_file` serviced).

## Table A — observed (grid, arm): the modal string and where it occurs

| grid | arm | turns | non-empty | distinct | modal (one line) | x of turns | read-action text | truncation disclaimer |
|---|---|---|---|---|---|---|---|---|
| `baseline` | `C` | 24 | 24 | 11 | `k08` | 6 | no | no |
| `baseline` | `C0` | 24 | 24 | 13 | `Based on the text provided, here is a structured summary of the **Knowledge It…` | 3 | no | no |
| `baseline` | `R` | 57 | 36 | 8 | `OK` | 18 | no | no |
| `cell-pointer-stable/145758Z` | `pointer-stable` | 6 | 6 | 6 | `Based on the provided body of ’resolve.py’ (truncated at line 75), here are th…` | 1 | no | no |
| `cell-pointer-stable/182535Z` | `pointer-stable` | 27 | 27 | 27 | `I'll read the specified lines of resolve.py to identify the raise sites. ’’’ r…` | 1 | yes | no |
| `equalinfo` | `C0F` | 27 | 15 | 2 | `OK` | 9 | no | no |
| `equalinfo` | `C0FT` | 24 | 18 | 2 | `OK` | 15 | no | no |
| `equalinfo` | `R` | 49 | 28 | 7 | `OK` | 16 | no | no |
| `longrun-fix` | `lease-reopen` | 3 | 3 | 3 | `I'll read the specified file and line range. @knowledge:resolve.py@1` | 1 | yes | no |
| `longrun-fix` | `pointer-stable` | 3 | 3 | 3 | `I read the provided body of ’resolve.py’. Note: the body excerpt is **truncate…` | 1 | yes | yes |
| `longrun-fix` | `transcript-compact` | 5 | 5 | 5 | `Based on the pinned body of ’resolve.py’ (1680 B) in the working set, here are…` | 1 | no | yes |
| `longrun-fix` | `transcript-grow` | 18 | 18 | 18 | `I read the BODY of ’resolve.py’ provided in the working set. The displayed con…` | 1 | yes | yes |
| `longrun-policy` | `lease-reopen` | 3 | 3 | 3 | `I'll read the specified file and line range. <tool_call> <tool_call> <tool_cal…` | 1 | yes | no |
| `longrun-policy` | `pointer-stable` | 3 | 3 | 3 | `I have to flag an access issue first: the pinned body for ’resolve.py’ is **tr…` | 1 | yes | yes |
| `longrun-policy` | `transcript-compact` | 3 | 3 | 3 | `I can only report what I actually read in the displayed body of ’resolve.py’. …` | 1 | no | yes |
| `longrun-policy` | `transcript-grow` | 31 | 31 | 31 | `I'll read the specific lines from the file. <arg_key>command</arg_key><arg_val…` | 1 | yes | no |
| `longrun` | `lease-reopen` | 48 | 39 | 39 | `I'll read the specified file and line range. <tool_call> <tool_call> <tool_cal…` | 1 | yes | no |
| `longrun` | `pointer-stable` | 48 | 12 | 12 | `I'll start by reading the knowledge files to understand the context. <tool_cal…` | 1 | no | no |
| `longrun` | `transcript-compact` | 48 | 41 | 13 | `<tool_call><arg_key>read_file</arg_key> <arg_key>path</arg_key> <arg_key>ptr_e…` | 24 | yes | no |
| `longrun` | `transcript-grow` | 48 | 1 | 1 | `I` | 1 | no | no |
| `longrun-c` | `lease-reopen` | 48 | 48 | 46 | `I'll examine the existing test file and the scope resolution logic to add an a…` | 2 | no | no |
| `longrun-c` | `pointer-stable` | 48 | 48 | 48 | `I need to read the specified lines of resolve.py. ’’’python cat -n ptr_engine/…` | 1 | yes | no |
| `longrun-c` | `transcript-compact` | 48 | 48 | 9 | `I'll start by reading the full resolve.py to understand the current structure.…` | 16 | yes | no |
| `longrun-c` | `transcript-grow` | 48 | 48 | 33 | `I'll run the negative controls test and reconcile any shifted code. <details> …` | 7 | no | no |
| `longrun-v3` | `pointer-stable` | 48 | 48 | 46 | `I need to read lines 66–110 of resolve.py. ANSWER: NOT-AN-ANSWER` | 3 | yes | no |
| `longrun-v3` | `transcript-grow` | 48 | 48 | 10 | `I'll start by reading the specified lines of resolve.py. ANSWER: NOT-AN-ANSWER` | 13 | no | no |
| `longrun-v4` | `pointer-stable` | 48 | 48 | 45 | `I need to run the test first to see what fails. ANSWER: NOT-AN-ANSWER` | 2 | no | no |
| `longrun-v4` | `transcript-grow` | 48 | 48 | 4 | `I need to read the specified lines of resolve.py. ANSWER: NOT-AN-ANSWER` | 35 | yes | no |
| `pilot-thinking` | `transcript-grow` | 6 | 6 | 6 | `I’ll read the specified range of ’resolve.py’ before answering. @knowledge:res…` | 1 | yes | yes |

## Table B — COUNTERFACTUAL: every declared checkpoint graded against the modal string

Column order is the declared set `docs/PREREG-ARM-RUN.md:150-152`: `cp.3.t06` · `cp.4.t08` · `cp.0.t12` · `cp.5.t14` · `cp.6.t18` · `cp.7.t20` · `cp.1.t24` · `cp.8.t26` · `cp.9.t32` · `cp.10.t36` · `cp.11.t42` · `cp.2.t46`. `P` pass, `F` fail, `U` undecidable, `t` text-only. These grades apply the modal string to **all 12** ids whether or not it appeared at that turn — **counterfactual**.

| grid | arm | 06 | 08 | 12 | 14 | 18 | 20 | 24 | 26 | 32 | 36 | 42 | 46 | pass | undecidable reasons |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `baseline` | `C` | U | U | U | U | U | U | U | U | U | U | U | U | **0/12** | prose_only x12 |
| `baseline` | `C0` | U | U | U | U | U | U | U | U | U | U | U | U | **0/12** | prose_only x12 |
| `baseline` | `R` | U | U | U | U | U | U | U | U | U | U | U | U | **0/12** | prose_only x12 |
| `cell-pointer-stable/145758Z` | `pointer-stable` | U | U | U | U | U | U | U | U | U | U | U | U | **0/12** | prose_only x12 |
| `cell-pointer-stable/182535Z` | `pointer-stable` | U | U | U | U | U | U | U | U | U | U | U | U | **0/12** | prose_only x12 |
| `equalinfo` | `C0F` | U | U | U | U | U | U | U | U | U | U | U | U | **0/12** | prose_only x12 |
| `equalinfo` | `C0FT` | U | U | U | U | U | U | U | U | U | U | U | U | **0/12** | prose_only x12 |
| `equalinfo` | `R` | U | U | U | U | U | U | U | U | U | U | U | U | **0/12** | prose_only x12 |
| `longrun-fix` | `lease-reopen` | U | U | U | U | U | U | U | U | U | U | U | U | **0/12** | prose_only x12 |
| `longrun-fix` | `pointer-stable` | U | U | U | U | U | U | U | U | U | U | U | U | **0/12** | prose_only x12 |
| `longrun-fix` | `transcript-compact` | U | U | U | U | U | U | U | U | U | U | U | U | **0/12** | prose_only x12 |
| `longrun-fix` | `transcript-grow` | U | U | U | U | U | U | U | U | U | U | U | U | **0/12** | prose_only x12 |
| `longrun-policy` | `lease-reopen` | U | U | U | U | U | U | U | U | U | U | U | U | **0/12** | prose_only x12 |
| `longrun-policy` | `pointer-stable` | U | U | U | U | U | U | U | U | U | U | U | U | **0/12** | prose_only x12 |
| `longrun-policy` | `transcript-compact` | U | U | U | U | U | U | U | U | U | U | U | U | **0/12** | prose_only x12 |
| `longrun-policy` | `transcript-grow` | U | U | U | U | U | U | U | U | U | U | U | U | **0/12** | prose_only x12 |
| `longrun` | `lease-reopen` | U | U | U | U | U | U | U | U | U | U | U | U | **0/12** | prose_only x12 |
| `longrun` | `pointer-stable` | U | U | U | U | U | U | U | U | U | U | U | U | **0/12** | prose_only x12 |
| `longrun` | `transcript-compact` | U | U | U | U | U | U | U | U | U | U | U | U | **0/12** | prose_only x12 |
| `longrun` | `transcript-grow` | U | U | U | U | U | U | U | U | U | U | U | U | **0/12** | prose_only x12 |
| `longrun-c` | `lease-reopen` | U | U | U | U | U | U | U | U | U | U | U | U | **0/12** | prose_only x12 |
| `longrun-c` | `pointer-stable` | U | U | U | U | U | U | U | U | U | U | U | U | **0/12** | prose_only x12 |
| `longrun-c` | `transcript-compact` | U | U | U | U | U | U | U | U | U | U | U | U | **0/12** | prose_only x12 |
| `longrun-c` | `transcript-grow` | U | U | U | U | U | U | U | U | U | U | U | U | **0/12** | prose_only x12 |
| `longrun-v3` | `pointer-stable` | U | U | U | U | U | U | U | U | U | U | U | U | **0/12** | unparseable x12 |
| `longrun-v3` | `transcript-grow` | U | U | U | U | U | U | U | U | U | U | U | U | **0/12** | unparseable x12 |
| `longrun-v4` | `pointer-stable` | U | U | U | U | U | U | U | U | U | U | U | U | **0/12** | unparseable x12 |
| `longrun-v4` | `transcript-grow` | U | U | U | U | U | U | U | U | U | U | U | U | **0/12** | unparseable x12 |
| `pilot-thinking` | `transcript-grow` | U | U | U | U | U | U | U | U | U | U | U | U | **0/12** | prose_only x12 |

## Table C — observed: the arm at each checkpoint turn (`·` no turn row, `*` the answer IS the modal)

| grid | arm | 06 | 08 | 12 | 14 | 18 | 20 | 24 | 26 | 32 | 36 | 42 | 46 | P/F/U/missing | with modal |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `baseline` | `C` | · | · | · | · | · | · | · | · | · | · | · | · | 0/0/0/12 | 0 |
| `baseline` | `C0` | · | · | · | · | · | · | · | · | · | · | · | · | 0/0/0/12 | 0 |
| `baseline` | `R` | · | · | · | · | · | · | · | · | · | · | · | · | 0/0/0/12 | 0 |
| `cell-pointer-stable/145758Z` | `pointer-stable` | U | · | · | · | · | · | · | · | · | · | · | · | 0/0/1/11 | 0 |
| `cell-pointer-stable/182535Z` | `pointer-stable` | F | t | P | F | F | P | F | F | · | · | · | · | 2/5/0/4 | 0 |
| `equalinfo` | `C0F` | · | · | · | · | · | · | · | · | · | · | · | · | 0/0/0/12 | 0 |
| `equalinfo` | `C0FT` | · | · | · | · | · | · | · | · | · | · | · | · | 0/0/0/12 | 0 |
| `equalinfo` | `R` | · | · | · | · | · | · | · | · | · | · | · | · | 0/0/0/12 | 0 |
| `longrun-fix` | `lease-reopen` | · | · | · | · | · | · | · | · | · | · | · | · | 0/0/0/12 | 0 |
| `longrun-fix` | `pointer-stable` | · | · | · | · | · | · | · | · | · | · | · | · | 0/0/0/12 | 0 |
| `longrun-fix` | `transcript-compact` | · | · | · | · | · | · | · | · | · | · | · | · | 0/0/0/12 | 0 |
| `longrun-fix` | `transcript-grow` | U | U | U | · | · | · | · | · | · | · | · | · | 0/0/3/9 | 0 |
| `longrun-policy` | `lease-reopen` | · | · | · | · | · | · | · | · | · | · | · | · | 0/0/0/12 | 0 |
| `longrun-policy` | `pointer-stable` | · | · | · | · | · | · | · | · | · | · | · | · | 0/0/0/12 | 0 |
| `longrun-policy` | `transcript-compact` | · | · | · | · | · | · | · | · | · | · | · | · | 0/0/0/12 | 0 |
| `longrun-policy` | `transcript-grow` | U | U | U | U | U | U | U | U | · | · | · | · | 0/0/8/4 | 0 |
| `longrun` | `lease-reopen` | U | U | U | U | U | U | U | U | U | U | U | U | 0/0/12/0 | 0 |
| `longrun` | `pointer-stable` | U | U | U | U | U | U | U | U | U | U | U | U | 0/0/12/0 | 0 |
| `longrun` | `transcript-compact` | U | U | U* | U* | U | U | U* | U* | U | U* | U* | U* | 0/0/12/0 | 7 |
| `longrun` | `transcript-grow` | U | U | U | U | U | U* | U | U | U | U | U | U | 0/0/12/0 | 1 |
| `longrun-c` | `lease-reopen` | U | U | U | U | U | U | U | U | U | U | U | U | 0/0/12/0 | 0 |
| `longrun-c` | `pointer-stable` | U | U | U | U | U | U | U | U | U | U | U | U | 0/0/12/0 | 0 |
| `longrun-c` | `transcript-compact` | U* | U | U | U | U | U | U | U | U | U | U | U | 0/0/12/0 | 1 |
| `longrun-c` | `transcript-grow` | U | U | U | U | U | U | U | U | U | U | U | U | 0/0/12/0 | 0 |
| `longrun-v3` | `pointer-stable` | U | U | U | U | U | U | F | U | U | U | U | U | 0/1/11/0 | 0 |
| `longrun-v3` | `transcript-grow` | U* | U | U | U | U | U | U | U | U | U | U | U | 0/0/12/0 | 1 |
| `longrun-v4` | `pointer-stable` | U | U | P | U | U | U | U | U | U | U | U | U | 1/0/11/0 | 0 |
| `longrun-v4` | `transcript-grow` | U* | U* | U* | U* | U* | U* | U* | U* | U* | U* | U | U* | 0/0/12/0 | 11 |
| `pilot-thinking` | `transcript-grow` | · | · | · | · | · | · | · | · | · | · | · | · | 0/0/0/12 | 0 |

## The mechanism-vs-instruction answer, with numbers

**The modal string of `longrun-v4`/`transcript-grow` is `I need to read the specified lines of resolve.py. ANSWER: NOT-AN-ANSWER` (present in 35 of 48 turns and at 11 of 12 checkpoint turns), and it is correct at 0 of the 12 checkpoints — it grades `unparseable x12` at 12 of 12 — so repetition is not a route to correctness, and the repetition is an arm effect: the same fixture and the same instruction yield modal frequencies of 35 (`transcript-grow`) / 2 (`pointer-stable`) in one grid, so what moves repetition is the transcript treatment, not the instruction.**

- Across **all 29 era-A `(grid, arm)` groups**, the modal string passes **0 of 12** checkpoints (groups with any modal pass: 0). Every modal is prose, a tool-call envelope or a non-answer token; none is one of the four contract forms in a decidable way.
- The discriminator proposed at `docs/ANSWER-DEGENERACY.md:171-176` comes back **neither** branch: the instruction-effect branch required the modal string to pass exactly the three `NONE` items — it passes **0** of them in every group; the mechanism branch required the modal string to pass exactly where it equals the derived value — no modal string is even a contract answer.
- The arm effect is visible inside one grid: `rows-longrun-2026-10-26.jsonl` gives modal frequencies `pointer-stable 1`, `lease-reopen 1`, `transcript-grow 1`, `transcript-compact 24` over 48 turns each; `rows-longrun-v4-2026-10-26.jsonl` gives `pointer-stable 2`, `transcript-grow 35`. Identical instruction, different arm, different repetition.

## Is the modal a refusal to read sources?

**No blanket read-refusal.** No era-A modal asserts "I cannot access files". The repeated strings split into two shapes:

1. **A read action the era-A harness could not service** — e.g. `rows-longrun-2026-10-26.jsonl`/`transcript-compact`: `<tool_call><arg_key>read_file</arg_key> <arg_key>path</arg_key> <arg_k…` (x24 of 48), a `read_file` tool-call envelope emitted into a tools-off grid; `rows-longrun-c-2026-10-26.jsonl`/`pointer-stable`: `I need to read the specified lines of resolve.py. ’’’python cat -n ptr…` (x1).
2. **A deferral + explicit placeholder** — `rows-longrun-v4-2026-10-26.jsonl`/`transcript-grow`: `I need to read the specified lines of resolve.py. ANSWER: NOT-AN-ANSWER` (x35 of 48, and at 11 of 12 checkpoint turns). It declares it must read, then writes `ANSWER: NOT-AN-ANSWER`; `parse_answer_contract` reads the line and `grade_cell` returns `undecidable` / `unparseable`, because `NOT-AN-ANSWER` is none of `NUM`/`CALL`/`TEXT`/`NONE`.

**Six modals do carry access-limiting language** — all of them *truncation disclaimers* on grids that did receive a body (`rows-longrun-2026-10-26-fix.jsonl` x3, `-policy.jsonl` x2, `rows-pilot-thinking-2026-10-26.jsonl` x1, whose flag is a false positive: it is a read attempt): the working-set body of `resolve.py` is cut off mid-function, so the string says it can report only what it actually read. Those modals are x1 each and none is a checkpoint answer.

**The fixture line that invites a read** is the question's own derivation parenthetical: `experiments/ptr-engine/longrun/tasks-v5/runtime-v5/LR-01.v6.json:685` —

> `"question": "Checkpoint 1/12: What does resolve() call when it records a successful resolution, and which keyword arguments does it pass? (answer must be derivable from experiments/ptr-engine/ptr_engine/resolve.py#L159)"`

The same `(answer must be derivable from …)` parenthetical recurs at fixture lines **685, 695, 715, 725, 745, 755, 775, 785, 815, 835, 865, 885** — once per checkpoint. It asks for a fact that is not in the prompt body; only a read can supply it, and era A services no read.

## Consequence for the grid: can era B be compared to era A on quality?

**Not on quality.** era B (`--tools read_file`) services the read, so the era-A modal shape — "I need to read … `ANSWER: NOT-AN-ANSWER`" — loses its cause and should not survive; but it does not become *impossible* to emit, because `NOT-AN-ANSWER` is still an admissible string the model may write. What changes is the instrument, not the model: the same 12 checkpoints are answered with different evidence available, so an era-A `x/12` and an era-B `x/12` are not the same measurement and their difference cannot be attributed to the arm. The provenance gate already refuses this comparison (`docs/ANALYSIS-PATH.md:32`: `incomparable_provenance eraA-vs-eraB`), and this page adds no new measurement that would lift it.

## Contradictions checked, none edited

- `docs/ANSWER-DEGENERACY.md:19` says `transcript-compact` repeats its modal **16** times in `rows-longrun-c-2026-10-26.jsonl` — **agree** (x16, 9 distinct reproduced here from the same rows).
- `docs/ANSWER-DEGENERACY.md:171-176` proposes this very measurement and states both branches; running it returns **neither** (0/12 pass, 0 `NONE` passes). That is a refinement of an explicitly open question, not a disagreement with a measured number.
- `docs/ANSWER-DEGENERACY.md:159-161` illustrates a mechanism effect with "`cp.0.t12`'s single integer `64` answered correctly by all four arms"; that illustration is **not realised as stated** in era A: no era-A grid has four arms passing `cp.0.t12`, and the two era-A passes at that id are one-arm cells whose answer is not the modal (`rows-cell-pointer-stable-20261026T182535Z.jsonl` `ANSWER: NUM 64`; `rows-longrun-v4-2026-10-26.jsonl` `64 ANSWER: 64`). It was written as a hypothetical ("would require"), so nothing is edited; recorded here as `docs/ANSWER-DEGENERACY.md:159-161`.
- Observed passes at any checkpoint turn, all era A, none modal: 3 (`cell-pointer-stable/182535Z pointer-stable cp.0.t12 (num_equal); cell-pointer-stable/182535Z pointer-stable cp.7.t20 (none_confirmed_absent_in_source); longrun-v4 pointer-stable cp.0.t12 (num_equal)`).

## Files

- `experiments/ptr-engine/measure/MODAL-ANSWER.json` — per (grid, arm) modal text/frequency/occurrence turns, all 12 counterfactual grades with reason strings, all observed cells, excluded files with reasons.
- `docs/MODAL-ANSWER.md` — this page.
- Read only: the 11 era-A rows files, `experiments/ptr-engine/longrun/tasks-v5/runtime-v5/LR-01.v6.json`, `experiments/ptr-engine/longrun/grade_v5.py` (imported). Nothing written outside the two paths above.

## Carry-forward for `TURN-DEDUP-RECONCILE` (numbers only — the QUALITY record is not a write path of this unit)

The question that opened this unit asks for the **9-distinct-of-48** `transcript-compact` result to be carried into the
QUALITY record with both its `x/12` and its `NONE`-flagged decomposition. Both numbers now exist offline and are
repeated here so the next unit can append them without re-deriving anything:

- **Repetition:** `rows-longrun-c-2026-10-26.jsonl` / `transcript-compact` = **9 distinct normalised answers over 48 turns**, largest identical group **16** (reproduced by this unit's own count, and identical to `docs/ANSWER-DEGENERACY.md:19`).
- **`x/12` for that modal string:** **0 pass, 12 undecidable** (`prose_only` x12) — counterfactual, because that string does not appear at every checkpoint turn (it appears at 1 of 12; Table C).
- **`NONE` decomposition:** the three `NONE`-truth ids are `cp.5.t14`, `cp.7.t20`, `cp.11.t42`. The modal string answers **0 of 3** of them — it contains no `ANSWER: NONE`, so `grade_cell` returns `undecidable`/`prose_only`, not `none_confirmed_absent_in_source`. The two era-A `NONE` passes on record are concrete `ANSWER: NONE` strings in one-arm cells (`cell-pointer-stable/182535Z` at `cp.7.t20`), not any modal.
