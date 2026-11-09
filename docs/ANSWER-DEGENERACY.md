# ANSWER-DEGENERACY — repetition of answers per arm and per cell

**Unit:** `ANSWER-DEGENERACY-ERA-A` · **Date:** 2026-10-26 · **Live requests spent: 0** (offline, zero sockets).
**Artifact of record:** [`experiments/ptr-engine/measure/ANSWER-DEGENERACY.json`](../experiments/ptr-engine/measure/ANSWER-DEGENERACY.json) (per-turn values, per-cell rows, sha256 of each arm's sorted distinct-answer set).

## What this page is not

It is **not a quality score**, **not a replacement for `checkpoint_accuracy`**, and **not a re-grade**.
Nothing here reads a grade file, calls `grade_v5.py`, or changes a published number; no rows file is modified.
Counting the same answer twice says nothing about whether either answer is right — it says only that the
arms differ in *how many* different strings they emitted. `x/12` stays the grade's number; this page does not
produce an `x`.

## The repetition fact, plainly

In `experiments/ptr-engine/measure/rows-longrun-c-2026-10-26.jsonl` — 192 turn rows, **48 per arm** — the
normalised assistant answers are **48 / 46 / 33 / 9** distinct for `pointer-stable` / `lease-reopen` /
`transcript-grow` / `transcript-compact`. The worst group is `transcript-compact`: **9 distinct answers over
48 turns**, with one identical answer occupying **16** of them; `transcript-grow` repeats its modal answer **7**
times. Every one of those 192 turns carries non-empty content, so the 9 is not a missingness artefact.

## 1. Definition (stated before the computation)

- **Turn row:** a row whose `kind` is absent or `== "turn"`. Rows with `kind == "tool-followup"` are **not**
  turn rows and are excluded from every count below (they are counted separately in the JSON under `kinds`).
- **Non-empty:** the assistant text, normalised, is non-empty after `strip`.
- **Normalisation:** strip leading/trailing whitespace; collapse every run of whitespace (including newlines)
  to a single space; case-fold (Unicode lower). Nothing else.
- **Deliberately NOT normalised:** numerals (`64` ≠ `64.0` ≠ `sixty-four`), punctuation, code fences, markdown/XML
  tags, the `ANSWER:` prefix, and any content beyond whitespace and case. Two answers differing only in a cited
  numeral therefore count as **two distinct** answers — the counts are an upper bound on repetition, not a lower one.
- **Distinct normalised answers:** cardinality of the set of normalised non-empty answers in the group.
- **Largest identical-answer group:** the biggest set of turns in the group sharing one identical normalised answer.
- **Grid** = one rows file (one measured grid run). **Cell** = `(task_id, rep)` inside a grid; `(none)` when the file
  records neither (the older `answer_text` files carry no `task_id`).

## 2. Per file and per arm

| file | turn rows | content field | arm | turns | non-empty | distinct | largest group |
|---|---|---|---|---|---|---|---|
| `rows-baseline-2026-10-26.jsonl` | 105 | answer_text | `C` | 24 | 24 | 11 | 6 |
| `rows-baseline-2026-10-26.jsonl` | 105 | answer_text | `C0` | 24 | 24 | 13 | 3 |
| `rows-baseline-2026-10-26.jsonl` | 105 | answer_text | `R` | 57 | 36 | 8 | 18 |
| `rows-cell-pointer-stable-20261026T145758Z.jsonl` | 6 | content | `pointer-stable` | 6 | 6 | 6 | 1 |
| `rows-cell-pointer-stable-20261026T182535Z.jsonl` | 27 | content | `pointer-stable` | 27 | 27 | 27 | 1 |
| `rows-equalinfo-2026-10-26.jsonl` | 100 | answer_text | `C0F` | 27 | 15 | 2 | 9 |
| `rows-equalinfo-2026-10-26.jsonl` | 100 | answer_text | `C0FT` | 24 | 18 | 2 | 15 |
| `rows-equalinfo-2026-10-26.jsonl` | 100 | answer_text | `R` | 49 | 28 | 7 | 16 |
| `rows-live-2026-10-26.jsonl` | 27 | **none** | — | — | — | — | — |
| `rows-longrun-2026-10-26-fix.jsonl` | 29 | content | `lease-reopen` | 3 | 3 | 3 | 1 |
| `rows-longrun-2026-10-26-fix.jsonl` | 29 | content | `pointer-stable` | 3 | 3 | 3 | 1 |
| `rows-longrun-2026-10-26-fix.jsonl` | 29 | content | `transcript-compact` | 5 | 5 | 5 | 1 |
| `rows-longrun-2026-10-26-fix.jsonl` | 29 | content | `transcript-grow` | 18 | 18 | 18 | 1 |
| `rows-longrun-2026-10-26-policy.jsonl` | 40 | content | `lease-reopen` | 3 | 3 | 3 | 1 |
| `rows-longrun-2026-10-26-policy.jsonl` | 40 | content | `pointer-stable` | 3 | 3 | 3 | 1 |
| `rows-longrun-2026-10-26-policy.jsonl` | 40 | content | `transcript-compact` | 3 | 3 | 3 | 1 |
| `rows-longrun-2026-10-26-policy.jsonl` | 40 | content | `transcript-grow` | 31 | 31 | 31 | 1 |
| `rows-longrun-2026-10-26.jsonl` | 192 | content | `lease-reopen` | 48 | 39 | 39 | 1 |
| `rows-longrun-2026-10-26.jsonl` | 192 | content | `pointer-stable` | 48 | 12 | 12 | 1 |
| `rows-longrun-2026-10-26.jsonl` | 192 | content | `transcript-compact` | 48 | 41 | 13 | 24 |
| `rows-longrun-2026-10-26.jsonl` | 192 | content | `transcript-grow` | 48 | 1 | 1 | 1 |
| `rows-longrun-c-2026-10-26.jsonl` | 192 | content | `lease-reopen` | 48 | 48 | 46 | 2 |
| `rows-longrun-c-2026-10-26.jsonl` | 192 | content | `pointer-stable` | 48 | 48 | 48 | 1 |
| `rows-longrun-c-2026-10-26.jsonl` | 192 | content | `transcript-compact` | 48 | 48 | 9 | 16 |
| `rows-longrun-c-2026-10-26.jsonl` | 192 | content | `transcript-grow` | 48 | 48 | 33 | 7 |
| `rows-longrun-v3-2026-10-26.jsonl` | 96 | content | `pointer-stable` | 48 | 48 | 46 | 3 |
| `rows-longrun-v3-2026-10-26.jsonl` | 96 | content | `transcript-grow` | 48 | 48 | 10 | 13 |
| `rows-longrun-v4-2026-10-26.jsonl` | 96 | content | `pointer-stable` | 48 | 48 | 45 | 2 |
| `rows-longrun-v4-2026-10-26.jsonl` | 96 | content | `transcript-grow` | 48 | 48 | 4 | 35 |
| `rows-longrun-v4-tools-2026-10-26.jsonl` | 48 | content | `pointer-stable` | 48 | 48 | 47 | 2 |
| `rows-longrun-v5-tools.jsonl` | 48 | content | `pointer-stable` | 48 | 48 | 41 | 5 |
| `rows-longrun-v6-tools.jsonl` | 48 | content | `pointer-stable` | 48 | 48 | 42 | 5 |
| `rows-pilot-thinking-2026-10-26.jsonl` | 6 | content | `transcript-grow` | 6 | 6 | 6 | 1 |
| `rows.jsonl` | 49 | **none** | — | — | — | — | — |

Files with **no assistant-content field** (reported, not skipped):
- `rows-live-2026-10-26.jsonl` — no assistant-content field (neither `content` nor `answer_text`); repetition not computable; fields present: cached_reported, cached_source, cached_tokens, cell, client_elapsed_s, completion_tokens, endpoint, error, model, nonce_sha, prompt_tokens, rep
- `rows.jsonl` — no assistant-content field (neither `content` nor `answer_text`); repetition not computable; fields present: cell, nonce, observed_at, phase, prompt_tokens, rep, row, seq, system_tokens, template_framing, user_tokens

Per-cell rows (arm × `(task_id,rep)`), full table: `ANSWER-DEGENERACY.json` → `files[].per_cell`. Two cells in the
same grid can repeat differently: in `rows-equalinfo-2026-10-26.jsonl` arm `C0FT` each of the 3 cells holds
8 turns / 6 non-empty / 2 distinct / largest group 5, while arm `C0F` holds 9 / 5 / 2 / 3 — the repetition is
uniform across reps, so it is not a one-rep accident.

## 3. H3's checkpoint turns, per arm

Checkpoint turns are `{6, 8, 12, 14, 18, 20, 24, 26, 32, 36, 42, 46}` — the 12 declared ids
(`docs/PREREG-ARM-RUN.md:150-152`), censused NUM 5 · CALL 4 · NONE 3 (`docs/PARM-1-ERRATA.md:42-60`).
A turn is `any ANSWER` when a line matches `^\s*ANSWER:` ; `repeated` counts turns whose ANSWER string also
appears at another checkpoint turn of the same arm.

| grid | arm | checkpoint turns | any `ANSWER:` | of which substantive (9) | distinct answers | turns with a repeated answer |
|---|---|---|---|---|---|---|
| `rows-longrun-2026-10-26.jsonl` | `lease-reopen` | 12 | 0 | 0 | 1 | 0 |
| `rows-longrun-2026-10-26.jsonl` | `pointer-stable` | 12 | 0 | 0 | 1 | 0 |
| `rows-longrun-2026-10-26.jsonl` | `transcript-compact` | 12 | 0 | 0 | 1 | 0 |
| `rows-longrun-2026-10-26.jsonl` | `transcript-grow` | 12 | 0 | 0 | 1 | 0 |
| `rows-longrun-c-2026-10-26.jsonl` | `lease-reopen` | 12 | 0 | 0 | 1 | 0 |
| `rows-longrun-c-2026-10-26.jsonl` | `pointer-stable` | 12 | 0 | 0 | 1 | 0 |
| `rows-longrun-c-2026-10-26.jsonl` | `transcript-compact` | 12 | 0 | 0 | 1 | 0 |
| `rows-longrun-c-2026-10-26.jsonl` | `transcript-grow` | 12 | 0 | 0 | 1 | 0 |
| `rows-longrun-v3-2026-10-26.jsonl` | `pointer-stable` | 12 | 9 | 7 | 4 | 7 |
| `rows-longrun-v3-2026-10-26.jsonl` | `transcript-grow` | 12 | 12 | 9 | 1 | 12 |
| `rows-longrun-v4-2026-10-26.jsonl` | `pointer-stable` | 12 | 8 | 6 | 4 | 6 |
| `rows-longrun-v4-2026-10-26.jsonl` | `transcript-grow` | 12 | 12 | 9 | 1 | 12 |
| `rows-longrun-v4-tools-2026-10-26.jsonl` | `pointer-stable` | 12 | 4 | 3 | 3 | 3 |
| `rows-longrun-v5-tools.jsonl` | `pointer-stable` | 12 | 2 | 2 | 3 | 0 |
| `rows-longrun-v6-tools.jsonl` | `pointer-stable` | 12 | 4 | 4 | 5 | 0 |

Read three ways:

1. **In the adjudicating-shape grids on disk (`rows-longrun-2026-10-26.jsonl`, `rows-longrun-c-2026-10-26.jsonl`,
   4 arms × 12 checkpoint turns = 48 checkpoint turns each) the ANSWER line count is 0 in all 8 arm-grids.**
   H3's decidable denominator in those grids is therefore 0 of 12 — repetition there is *not* what zeroes the
   score; absence is. That matches `QUALITY-REASON-MIX` (63 of 66 checkpoint non-passes are 'no `ANSWER:` line').
2. **Where the marker exists (`rows-longrun-v3`, `rows-longrun-v4`, `v4-tools`, `v5-tools`, `v6-tools`), the
   repetition is total, not partial:** `rows-longrun-v3-2026-10-26.jsonl` arm `transcript-grow` emits an ANSWER
   line at **12 of 12** checkpoint turns and those 12 lines normalise to **1 distinct string** — the same answer
   12 times. `rows-longrun-v4-2026-10-26.jsonl` `transcript-grow`: 12 of 12, **1 distinct**, 12 repeated.
   `pointer-stable` in the same two grids: 9 and 8 ANSWER lines, 4 distinct strings each, 7 and 6 turns repeated.
3. So in the grids where H3 can even be computed, one arm answers the *same* string at every checkpoint while the
   other answers a *different* string at most of them — a difference of behaviour that no grade file records.

## 4. What `grade_v5` can and cannot distinguish

**Can.** It separates an absent answer from a wrong answer, and it does so with different verdicts and reasons
(`experiments/ptr-engine/longrun/grade_v5.py`):
- no `ANSWER:` line at all → `answer_parse_error = "no_answer_line"` (empty turn) or `"prose_only"` (prose, no
  contract line), both in `NON_ANSWER_ERRORS` → `verdict = "undecidable"`, `reason = ` the same string
  (`grade_v5.py:198-205`, `:595-607`), and `undecidable` is **outside** the decidable denominator (`:770-795`).
- a contract line that is present but wrong → `verdict = "fail"` with a value-comparison reason:
  `num_mismatch` (`:664`), `callee_mismatch` (`:671`), `kwarg_set_mismatch` (`:675`),
  `kwarg_value_mismatch:%s` (`:685`), `kind_mismatch:%s_expected` (`:650`), and `answer_not_contract:<err>`
  for malformed bodies (`:607`).
- a checkpoint whose row is absent → `verdict = "fail"`, `reason = "turn_missing"` (`:818`, counted separately as
  `missing` at `:793`).
**Cannot.** No reason string carries *the value* or *its history*: `num_mismatch` is emitted identically for a
wrong `64` and for the same wrong `64` at all twelve checkpoints, and identically again for twelve different wrong
numerals. There is no `repeated_answer`, no `modal_answer`, and no per-arm value census in any grade output —
the reasons are `num_mismatch` / `callee_mismatch` / `kwarg_*` / `kind_mismatch` / `answer_not_contract:*` /
`turn_missing` only. **Verified by grep:** `grade_v5.py` contains no reason token naming repetition, duplication,
or a previous turn. A page that says the arms 'answered the same wrong thing repeatedly' is therefore making a
claim no grade file on disk can support today, in either direction.

## 5. Contradictions checked, none edited

- `experiments/ptr-engine/measure/rows-longrun-c-2026-10-26.jsonl` vs
  `orchestration/handoffs/TURN-DEDUP-RECONCILE.json`: **agree** — 48 turns/arm and 48 / 46 / 33 / 9 distinct reproduce exactly.
- `experiments/ptr-engine/measure/ANSWER-DEGENERACY.md:53` (`{"marker_lines": 0, "turns": 48}`) vs my count on
  `rows-longrun-2026-10-26.jsonl`: **agree** — 0 ANSWER lines at checkpoint turns, 48 turns.
- `docs/MATRIX-COVERAGE.md:29` declares 4 checkpoint ids (`cp.0.t12`, `cp.1.t24`, `cp.2.t46`, `repair.t30`) while
  `docs/PREREG-ARM-RUN.md:150-152` declares 12 — a **pre-existing, already-recorded** disagreement
  (`docs/PARM-1-ERRATA.md:83-102`); this page uses the 12 and edits neither.
- **No contradiction found** between a computed count here and a published number; nothing was re-graded.

## 6. Mechanism or instruction? What would have to be true

A **mechanism effect** would require: (a) all four arms received an information-equivalent working set — the
answer *was* derivable in each — and (b) the repeated string is the **correct** value for the checkpoint it
repeats at, with the repetition varying by arm (e.g. `cp.0.t12`'s single integer `64` answered correctly by all
four arms, while `transcript-compact` gives that same `64` at all 48 turns because its context was truncated).
An **instruction effect** would require instead: (a) the fixture/system prompt narrows the admissible answer
space (a `NONE` item, a refusal rule such as 'never restate a fact you did not read'), and (b) the repeated
string is a **refusal or constant** that fails substantive checkpoints while passing the three NONE items —
the same string in every arm, indifferent to the treatment.
The numbers here are consistent with the second reading wherever the marker exists: `transcript-grow`'s single
repeated string at 12 of 12 checkpoint turns in both v3 and v4 is one string, not twelve values, and
`rows-longrun-c` has zero ANSWER lines — but this page does not settle which reading is true, because the
repeated strings were not graded.

**The one measurement that would separate them:** *modal-answer accuracy, per arm* — take each arm's largest
identical-answer group, grade that single string against all 12 declared checkpoints' own expected values
(offline, `parse_answer_contract` + `grade_cell` on the frozen fixture), and report `pass / fail / undecidable`
per checkpoint. If the modal string passes exactly where it equals the derived value and the passing sets differ by
arm, repetition is a context mechanism; if it passes exactly the 3 NONE items in every arm and nothing else, it is
an instruction effect. That measurement needs 0 requests and is **not** performed here (it would be a grade of a
grade, and this card is barred from re-grading).

## 7. Files

- `experiments/ptr-engine/measure/ANSWER-DEGENERACY.json` — counts, per-turn values, per-cell table, per-arm answer-set digests.
- `docs/ANSWER-DEGENERACY.md` — this page.
- rows read: **16** `experiments/ptr-engine/measure/rows*.jsonl` files, **1177** raw rows of which **1109** are turn rows, 0 unparseable (see `files[]` for
  each file's raw/turn row counts and whether it carries `content` / `answer_text` / neither) — 2 files carry no
  assistant-content field (`rows-live-2026-10-26.jsonl`, `rows.jsonl`), 2 carry `answer_text` instead of `content`
  (`rows-baseline-2026-10-26.jsonl`, `rows-equalinfo-2026-10-26.jsonl`), and 12 carry `content`.
