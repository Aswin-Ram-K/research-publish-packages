# NEVER-ANSWERED-ROOT-2 — what the 63 actually are, read from the turn text

Re-issue of `NEVER-ANSWERED-ROOT` (which settled `partial` with no table). Population: the
**63 `never_answered` cells** of `QUALITY-REASON-MIX`'s primary T3 population, drawn from the
8 `rows-longrun-*.jsonl` grids. Every cell is re-read from its own rows file; the grade
document is used only as the list of cells and for the checkpoint truth (`truth[].expected`),
never as the reason.

Tool: `experiments/ptr-engine/tools/never_answered.py` (read-only; opens rows, fixtures and
grade documents for reading). Measure: `experiments/ptr-engine/measure/NEVER-ANSWERED-ROOT.json`.
`live_requests: 0`, `network: false`.

Method notes (why the buckets are trustworthy):

- The turn row is `per_turn[-1]` for `(arm, turn)` — the same "last row wins" rule as
  `grade_v5.grade_rows` (`by_turn = {turn: row}`). Using a mean or first row would hide the
  truncations.
- `cap_hit` is tested **before** the prose buckets, as the card's precedence requires. Two
  stage-1 rows (`rows-longrun-2026-10-26`, no `max_tokens` field, `completion_tokens == 128`)
  stop mid-sentence at exactly 128 tokens: `"…The default per-turn resolve budget is **1 ref** — this is derivable from …#L39,"`
  (287 chars, cut before the closing quote).
- `prose_asserts_value` requires a *stated* value: a leading bare numeral, or a numeral in a
  sentence with a copula (`is/are/=/defaults to/defines/counts…`), or a call expression
  (`self._x(` / `obj.m(`), after removing `#L39`, `lines 15–142`, `1680 B`, pointer handles,
  fenced code and `<tool_call>` blocks. Raw-numeral counts (below) are reported separately
  because most numerals in these turns are line references, not answers.

---

## Deliverable 1 — the 63-row table

Columns: `grid · arm · checkpoint · turn · completion_tokens/max_tokens · row_kind_set ·
content_chars · numerals present in the text (up to 5) · bucket`.

| grid | arm | checkpoint | turn | ct/max | row_kind | chars | numerals | bucket |
|---|---|---|---|---|---|---|---|---|
| fix | lease-reopen | cp.0.t12 | 12 | —/— | none | 0 | — | turn_absent |
| fix | lease-reopen | cp.1.t24 | 24 | —/— | none | 0 | — | turn_absent |
| fix | lease-reopen | cp.2.t46 | 46 | —/— | none | 0 | — | turn_absent |
| fix | pointer-stable | cp.0.t12 | 12 | —/— | none | 0 | — | turn_absent |
| fix | pointer-stable | cp.1.t24 | 24 | —/— | none | 0 | — | turn_absent |
| fix | pointer-stable | cp.2.t46 | 46 | —/— | none | 0 | — | turn_absent |
| fix | transcript-compact | cp.0.t12 | 12 | —/— | none | 0 | — | turn_absent |
| fix | transcript-compact | cp.1.t24 | 24 | —/— | none | 0 | — | turn_absent |
| fix | transcript-compact | cp.2.t46 | 46 | —/— | none | 0 | — | turn_absent |
| fix | transcript-grow | cp.0.t12 | 12 | 1232/16384 | turn | 1195 | 39,1680 | prose_other |
| fix | transcript-grow | cp.1.t24 | 24 | —/— | none | 0 | — | turn_absent |
| fix | transcript-grow | cp.2.t46 | 46 | —/— | none | 0 | — | turn_absent |
| policy | lease-reopen | cp.0.t12 | 12 | —/— | none | 0 | — | turn_absent |
| policy | lease-reopen | cp.1.t24 | 24 | —/— | none | 0 | — | turn_absent |
| policy | lease-reopen | cp.2.t46 | 46 | —/— | none | 0 | — | turn_absent |
| policy | pointer-stable | cp.0.t12 | 12 | —/— | none | 0 | — | turn_absent |
| policy | pointer-stable | cp.1.t24 | 24 | —/— | none | 0 | — | turn_absent |
| policy | pointer-stable | cp.2.t46 | 46 | —/— | none | 0 | — | turn_absent |
| policy | transcript-compact | cp.0.t12 | 12 | —/— | none | 0 | — | turn_absent |
| policy | transcript-compact | cp.1.t24 | 24 | —/— | none | 0 | — | turn_absent |
| policy | transcript-compact | cp.2.t46 | 46 | —/— | none | 0 | — | turn_absent |
| policy | transcript-grow | cp.0.t12 | 12 | 16384/16384 | turn | 84934 | — | cap_hit |
| policy | transcript-grow | cp.1.t24 | 24 | 16384/16384 | turn | 85100 | — | cap_hit |
| policy | transcript-grow | cp.2.t46 | 46 | —/— | none | 0 | — | turn_absent |
| base | lease-reopen | cp.0.t12 | 12 | 128/— | turn | 287 | 1,1680,76243148 | cap_hit |
| base | lease-reopen | cp.1.t24 | 24 | 106/— | turn | 90 | — | prose_other |
| base | lease-reopen | cp.2.t46 | 46 | 128/— | turn | 47 | — | cap_hit |
| base | pointer-stable | cp.0.t12 | 12 | 57/— | turn | 96 | — | no_answer_no_prose |
| base | pointer-stable | cp.1.t24 | 24 | 128/— | turn | 0 | — | empty_completion |
| base | pointer-stable | cp.2.t46 | 46 | 128/— | turn | 0 | — | empty_completion |
| base | transcript-compact | cp.0.t12 | 12 | 106/— | turn | 243 | — | no_answer_no_prose |
| base | transcript-compact | cp.1.t24 | 24 | 106/— | turn | 243 | — | no_answer_no_prose |
| base | transcript-compact | cp.2.t46 | 46 | 117/— | turn | 243 | — | no_answer_no_prose |
| base | transcript-grow | cp.0.t12 | 12 | 128/— | turn | 0 | — | empty_completion |
| base | transcript-grow | cp.1.t24 | 24 | 128/— | turn | 0 | — | empty_completion |
| base | transcript-grow | cp.2.t46 | 46 | 128/— | turn | 0 | — | empty_completion |
| c | lease-reopen | cp.0.t12 | 12 | 5/4096 | turn | 4 | 2000 | prose_asserts_value |
| c | lease-reopen | cp.1.t24 | 24 | 90/4096 | turn | 267 | 15,142 | prose_other |
| c | lease-reopen | cp.2.t46 | 46 | 44/4096 | turn | 143 | — | prose_asserts_value |
| c | pointer-stable | cp.0.t12 | 12 | 156/4096 | turn | 650 | 39,1680 | prose_other |
| c | pointer-stable | cp.1.t24 | 24 | 54/4096 | turn | 196 | 7,15,142 | prose_asserts_value |
| c | pointer-stable | cp.2.t46 | 46 | 19/4096 | turn | 77 | — | prose_asserts_value |
| c | transcript-compact | cp.0.t12 | 12 | 35/4096 | turn | 134 | — | prose_other |
| c | transcript-compact | cp.1.t24 | 24 | 38/4096 | turn | 141 | — | prose_other |
| c | transcript-compact | cp.2.t46 | 46 | 35/4096 | turn | 134 | — | prose_other |
| c | transcript-grow | cp.0.t12 | 12 | 339/4096 | turn | 1297 | 1,2,30 | prose_other |
| c | transcript-grow | cp.1.t24 | 24 | 769/4096 | turn | 2803 | 12 | prose_other |
| c | transcript-grow | cp.2.t46 | 46 | 131/4096 | turn | 422 | — | prose_other |
| v3 | pointer-stable | cp.0.t12 | 12 | 40/4096 | turn | 150 | 39 | prose_other |
| v3 | pointer-stable | cp.2.t46 | 46 | 54/4096 | turn | 183 | 66,71 | prose_other |
| v3 | transcript-grow | cp.0.t12 | 12 | 21/4096 | turn | 67 | — | prose_other |
| v3 | transcript-grow | cp.1.t24 | 24 | 23/4096 | turn | 71 | — | prose_other |
| v3 | transcript-grow | cp.2.t46 | 46 | 22/4096 | turn | 58 | — | prose_other |
| v4 | pointer-stable | cp.1.t24 | 24 | 36/4096 | turn | 139 | — | prose_other |
| v4 | pointer-stable | cp.2.t46 | 46 | 73/4096 | turn | 242 | 66,71,2629 | prose_other |
| v4 | transcript-grow | cp.0.t12 | 12 | 22/4096 | turn | 72 | — | prose_other |
| v4 | transcript-grow | cp.1.t24 | 24 | 22/4096 | turn | 72 | — | prose_other |
| v4 | transcript-grow | cp.2.t46 | 46 | 22/4096 | turn | 72 | — | prose_other |
| v4-tools | pointer-stable | cp.1.t24 | 24 | 55/4096 | turn | 225 | — | prose_other |
| v4-tools | pointer-stable | cp.2.t46 | 46 | 32/4096 | turn | 101 | 66,71 | no_answer_no_prose |
| v5-tools | pointer-stable | cp.0.t12 | 12 | 56/4096 | turn | 214 | 35,45 | prose_other |
| v5-tools | pointer-stable | cp.1.t24 | 24 | 54/4096 | turn | 197 | 15,250 | prose_other |
| v5-tools | pointer-stable | cp.2.t46 | 46 | 55/4096 | turn | 170 | 66,71 | prose_other |

**Bucket totals (63 = 21+5+4+0+0+4+24+5):**

| bucket | n | share |
|---|---|---|
| turn_absent | 21 | 33.3% |
| empty_completion | 5 | 7.9% |
| cap_hit | 4 | 6.3% |
| reasoning_only | 0 | 0.0% |
| tool_loop | 0 | 0.0% |
| prose_asserts_value | 4 | 6.3% |
| prose_other | 24 | 38.1% |
| no_answer_no_prose | 5 | 7.9% |

**Per arm (63 cells are not spread evenly — arms ran in different grids):**

| arm | turn_absent | empty | cap_hit | prose_asserts_value | prose_other | no_answer | total |
|---|---|---|---|---|---|---|---|
| lease-reopen | 6 | 0 | 2 | 2 | 2 | 0 | 12 |
| pointer-stable | 6 | 2 | 0 | 2 | 9 | 2 | 21 |
| transcript-compact | 6 | 0 | 0 | 0 | 3 | 3 | 12 |
| transcript-grow | 3 | 3 | 2 | 0 | 10 | 0 | 18 |

**Per grid:**

| grid | turn_absent | empty | cap_hit | prose_asserts_value | prose_other | no_answer | total |
|---|---|---|---|---|---|---|---|
| fix | 11 | 0 | 0 | 0 | 1 | 0 | 12 |
| policy | 10 | 0 | 2 | 0 | 0 | 0 | 12 |
| base | 0 | 5 | 2 | 0 | 1 | 4 | 12 |
| c | 0 | 0 | 0 | 4 | 8 | 0 | 12 |
| v3 | 0 | 0 | 0 | 0 | 5 | 0 | 5 |
| v4 | 0 | 0 | 0 | 0 | 5 | 0 | 5 |
| v4-tools | 0 | 0 | 0 | 0 | 1 | 1 | 2 |
| v5-tools | 0 | 0 | 0 | 0 | 3 | 0 | 3 |

**Cells that state a value, and whether it is right.** 4 cells are `prose_asserts_value`;
**3 assert a WRONG value and 1 asserts the RIGHT one**:

| grid · arm · cp | asserted (as written) | truth | verdict | fragment (chars) |
|---|---|---|---|---|
| c · lease-reopen · cp.0.t12 | `2000` | 64 | **wrong** | `"2000"` (4) |
| c · pointer-stable · cp.1.t24 | `7` | 31 | **wrong** | `"7 … totaling seven distinct \`Ptr*\` error classes."` (196) |
| c · lease-reopen · cp.2.t46 | call `self._reject` | `ledger.record_refusal(…)` | **wrong** | `"_refuse calls \`self._reject\` and passes the \`reason\` string. …"` (143) |
| c · pointer-stable · cp.2.t46 | call `ledger.record_refusal` | same callee | **right** | `"ledger.record_refusal(scope=scope_name, serialized_ref=text, code=error.code)"` (77) |

**Plus one `cap_hit` cell that states a wrong value** — `base · lease-reopen · cp.0.t12`:
`"…The default per-turn resolve budget is **1 ref** …"` (287 chars, cut at 128 tokens), asserted
`1` vs truth `64` → wrong. And **one prose cell asserts a qualitative wrong claim**:
`c · pointer-stable · cp.0.t12` (650 chars) — `"…the budget parameter defaults to \`None\`
(unbounded)…"` where the truth is `DEFAULT_MAX_REFS = 64`.

So of 63 never-answered cells: **5 state an answer in prose; 4 of those 5 are wrong; 1 is right.**

Numerals: **15 of the 33 cells that have a row carry some numeral; 0 of 63 contains `64`** — the
same fact `V-REASON-MIX` found on `prose_only`, confirmed independently here.

---

## Deliverable 2 — the discriminator

**(i) Rows-file era (stage-1 128-token cap vs post-cap).** The era is readable from the row
itself: the stage-1 runner (`rows-longrun-2026-10-26.jsonl`) wrote **no `max_tokens` field** and
200 of its turns stopped at `completion_tokens == 128`; every later grid records `max_tokens`
(4096 or 16384).

| era | turn_absent | empty | cap_hit | prose_asserts_value | prose_other | no_answer | total |
|---|---|---|---|---|---|---|---|
| stage1_128_cap | 0 | 5 | 2 | 0 | 1 | 4 | 12 |
| post_128_cap | 21 | 0 | 2 | 4 | 23 | 1 | 51 |

All 12 stage-1 cells sit in one grid (`base`), and that grid's rows are the *only* ones with
`""` completions (5 empty) and mid-sentence 128-token stops (2). The post-cap `cap_hit` pair is
different: `policy · transcript-grow` emits `<tool_call>open` every 25 chars until 16384
tokens (84934 and 85100 chars) — a tool loop that the runner correctly truncated, not a budget
starved answer.

**(ii) Fixture contract (was `ANSWER:` required, read from each row's `fixture_sha256`).**
`rows-longrun-c-2026-10-26.jsonl`'s rows carry the sha256 of `tasks-v2/runtime-v2/LR-01.v2.json`,
whose fixture declares **`answer_marker: null`** — `^ANSWER:` was inert in that grid. Every
other grid's rows carry a v3/v4 fixture sha whose `answer_marker.required` is `true`.

| contract | prose_asserts_value | prose_other | no_answer | empty | cap_hit | turn_absent | total |
|---|---|---|---|---|---|---|---|
| marker not required (v2, grid `c`) | 4 | 8 | 0 | 0 | 0 | 0 | 12 |
| marker required (v3/v4/v4-tools/v5-tools) | 0 | 13 | 2 | 0 | 0 | 0 | 15 |
| fixture sha not on disk (fix/policy/base) | 0 | 2 | 4 | 5 | 4 | 21 | 36 |

**All 4 prose answers come from the one grid where the marker was not required.** Where the
marker was required, prose answers are 0/15 — the contract suppresses prose answers instead of
grading them.

**(iii) Arm, within one grid and one era.** Only grid `c` (post-cap, marker-not-required) has
all four arms, so it is the only place an arm effect can be seen at all:

| arm | cells | stated an answer (prose) | wrong | right | narration/tool only |
|---|---|---|---|---|---|
| pointer-stable | 3 | 2 | 1 | 1 | 1 |
| lease-reopen | 3 | 1 | 1 | 0 | 2 |
| transcript-compact | 3 | 0 | 0 | 0 | 3 |
| transcript-grow | 3 | 1 | 0 | 0 | 2 |

Every other grid runs 1–2 arms, so no other within-grid comparison exists. `fix` and `policy`
are entirely `turn_absent`/`cap_hit`: those grids ran 29 and 40 rows, not 192, and never reached
turns 12/24/46 for most arms — a harness/grid-scale fact, not an arm fact.

**Verdict, one sentence.** The wall is a **harness-epoch and contract artefact, not an arm
property**: 21/63 cells are turns the grid never ran, 12/63 are the stage-1 128-token era (5
empty completions, 2 mid-sentence 128-token stops, 4 tool-call-only, 1 narration), 4/63 are
tool-call spam truncated at 16384, and only 4/63 state an answer — all 4 in the single grid whose
fixture never required an `ANSWER:` line — so H3 **cannot** separate arms from this corpus: the
only within-era comparison has 3 cells per arm, and 18 of the 21 pointer-stable cells are
non-answers that differ in no arm-dependent way.

---

## Deliverable 3 — the `grade_v4` / `grade_v5` seam

The card's "8 matched cells" is **not reproducible**: matching a v4 grade document to a v5 cell
by `basename(rows_file) + arm + checkpoint`, **23** cells have a v4 check, and **17** of them are
cells where `grade_v4` read a value and `grade_v5` calls the turn `prose_only`. (17 is also what
`QUALITY-REASON-MIX`'s own `v4_vs_v5_cross_tab` sums to: 4+4+2+2+1+1+1+1+1.) I rule on all 17.

**Regression — 6 cells where v4 read a genuinely stated value that v5 discards:**

- `c · lease-reopen · cp.0.t12` — v4 `number_wrong:2000`, fragment `"2000"` (4 chars). A bare
  wrong answer; v5 files it as no-answer.
- `c · pointer-stable · cp.1.t24` — v4 `number_wrong:7`, fragment
  `"7 … Evidence: … totaling seven distinct \`Ptr*\` error classes."` (196 chars). Wrong (truth
  31), but *gradable*.
- `c · pointer-stable · cp.2.t46` — v4 `missing_anchor:raising`, fragment
  `"ledger.record_refusal(scope=scope_name, serialized_ref=text, code=error.code)"` (77 chars),
  the **exact correct call**. v5 rejects it only because the line lacks `ANSWER: CALL `.
- `c · transcript-grow · cp.2.t46` — v4 `missing_anchor:raising`; the prose
  `"…_refuse_ calls \`ledger.record_refusal\`. It passes four arguments…"` (422 chars) names the
  right callee.
- `c · lease-reopen · cp.2.t46` — v4 `missing_anchor:ledger`; prose asserts
  `"_refuse calls \`self._reject\`…"` (143 chars) — a wrong call, but a stated one.
- `base · lease-reopen · cp.0.t12` — v4 `number_wrong:1`; fragment
  `"…The default per-turn resolve budget is **1 ref** …"` (287 chars). v4 called it wrong (it
  is wrong) and v5 throws that judgement away. Caveat: the row is a 128-token truncation, so
  "no answer" is defensible here too.

**Correct tightening — 11 cells where v4's "value" was never an answer:**

- `base · pointer-stable · cp.0.t12`, `base · transcript-compact · cp.0.t12`, `.cp.1.t24`,
  `.cp.2.t46` — v4 `value_not_in_concluding_position`/`missing_anchor:ledger` on text that is
  only `<tool_call>` markup (e.g. `"<tool_call>…<arg_key>read_file</arg_key>…"`), i.e. the value
  appeared inside a tool call, never in an answer.
- `base · lease-reopen · cp.2.t46` — v4 `missing_anchor:ledger` on
  `"I'll check the knowledge base for the resolve"` (47 chars, cut at 128).
- `c · pointer-stable · cp.0.t12` — v4 `number_wrong:39`; the "39" is `…#L39` inside
  `"…the default per-turn resolve budget …"` (650 chars) with no numeric answer.
- `c · lease-reopen · cp.1.t24` — v4 `number_wrong:15`; "15" comes from `"…lines 15-142…"`
  (267 chars) in a read instruction.
- `c · transcript-compact · cp.2.t46` — `"I'll read the specified file and line range."` (134
  chars) + a `pathlib` code fence; no answer.
- `c · transcript-grow · cp.0.t12` — v4 `value_not_in_concluding_position`; the `64` sits inside
  the pasted `resolve()` body in a `<details>` block, not in prose.
- `c · transcript-grow · cp.1.t24` — v4 `number_wrong:12`; "12" is `#L142`-adjacent noise in
  `"I need to read errors.py L15–L142 …"` (2803 chars).
- `fix · transcript-grow · cp.0.t12` — v4 `number_wrong:39`; `"…\`resolve.py\` (1680 B)…"`
  (1195 chars) — 39 is a line reference, 1680 a byte size; the turn is a disclosure that it
  could not read line 39.

**Ruling: mixed, and the split is the finding.** v5's tightening is *correct* on 11/17 cells
(where v4 was reading line numbers, byte sizes, or values buried in tool calls / pasted code) and
a *regression* on 6/17 (where v4 had a stated, gradable value). So published quality moved for
two reasons at once: the judge got stricter about what counts as an answer, and it got stricter
than the contract requires — prose that states an exact correct call is now unscored. **The seam
is not a clean tightening.**

---

## Deliverable 4 — what would make H3 measure correctness

1. Require, in the contract, a machine-findable answer **anywhere in the turn**: a declared
   `answer_spans` rule that also accepts (a) a leading bare numeral, and (b) a prose line whose
   only assertion is a `<callee>(<kw>=<value>…)` call — i.e. treat `^ANSWER:` as optional
   formatting, not as the answer channel.
2. Record `asserted_value` on every turn (numeral in an asserting sentence, or a call
   expression), independent of whether the turn also has an `ANSWER:` line.
3. Grade `asserted_value` against the checkpoint truth with the existing comparators
   (`num_equal` / `call_equal`), so a wrong value lands in bucket 2 (`answered_wrong_value`)
   rather than in no-answer.
4. Do **not** count numerals that are line references, byte sizes, or inside tool-call/code
   spans — that is exactly the `grade_v4` failure (`number_wrong:39` for `#L39`).
5. Keep `ANSWER:`-less prose that asserts nothing in a separate `prose_unanswered` bucket, so
   compliance is still visible without being conflated with correctness.
6. Recompute — not re-run — all 66 cells: the rows already contain every turn; re-grade with the
   widened extractor over the same `rows_file`+`arm`+`turn`, and republish accuracy as
   `pass / fail / prose_unanswered / no_turn` with the two denominators stated.
7. Recompute the v4/v5 cross-tab afterwards; the 6 regressions above become `fail` (5 wrong) or
   `pass` (1 right) and the "0 wrong values" claim disappears.
8. Report the arm split only within one grid × era × contract cell (here: grid `c`, 3 cells per
   arm), and label any cross-arm number computed on 63 cells as **not arm-attributable**.
9. Freeze the new extractor with a test containing the 6 regression fragments as fixtures, so a
   future tightening shows up as a measure diff, not as a silent quality drop.

---

## The honest sentence

**H3 in this corpus measures answer *production* — not correctness and not pointer mechanics:**
21/63 cells are turns never run, 12/63 carry the stage-1 128-token cap signature (5 empty, 2
mid-sentence stops, 4 tool-call-only, 1 narration), 4/63 are 16384-token tool-call spam, 24/63
are narration with no asserted value, and only 4/63 state an answer at all (3 wrong, 1 right),
all four in the one grid whose fixture never required an `ANSWER:` line — so the 63 "never
answered" cells say nothing about arm quality.

---

## Deliverable 5 — cells whose bucket contradicts the grader's reason string

The buckets above are read from the rows; the grade document says something else for some cells.
Two classes, kept apart because only the first is a true disagreement.

**Hard contradictions — the grader's reason names a *cause* the row disproves (4 cells, all
`prose_only` → `cap_hit`):**

| grid | arm | checkpoint | grader reason | row bucket | content chars | what the row shows |
|---|---|---|---|---|---|---|
| `rows-longrun-2026-10-26.jsonl` | lease-reopen | cp.0.t12 | `prose_only` | `cap_hit` | 287 | 128-token stage-1 stop mid-word (`…deriveable from …#L39,`) |
| `rows-longrun-2026-10-26.jsonl` | lease-reopen | cp.2.t46 | `prose_only` | `cap_hit` | 47 | 128-token stage-1 stop (`"I'll check the knowledge base for the resolve"`) |
| `rows-longrun-2026-10-26-policy.jsonl` | transcript-grow | cp.0.t12 | `prose_only` | `cap_hit` | 84934 | `16384/16384`, truncated, `<tool_call>open` repeated — tool-call spam |
| `rows-longrun-2026-10-26-policy.jsonl` | transcript-grow | cp.1.t24 | `prose_only` | `cap_hit` | 85100 | same, `16384/16384`, truncated |

`prose_only` asserts "there was prose, no `ANSWER:` line"; on these four turns the completion was
*cut* by the token budget before any answer could be written (two of them at the historical
128-token stage-1 cap, which the row records only as `completion_tokens == 128` with **no
`max_tokens` field**). Calling a budget cut "prose only" hides the harness cause.

**Coarsening, not a contradiction (5 cells, `no_answer_line` on `empty_completion`):** the five
empty `base` rows (`pointer-stable` cp.1.t24, cp.2.t46; `transcript-grow` cp.0.t12, cp.1.t24,
cp.2.t46) do have no answer line — because they have no content (`completion_tokens == 0`). The
grader's string is true but useless: it files "the model returned nothing" under the same label
as "the model wrote prose without the marker".

**Reproducibility:** re-running `python3 experiments/ptr-engine/tools/never_answered.py --json
/tmp/na-root-check.json` reproduces the on-disk `NEVER-ANSWERED-ROOT.json` exactly —
`rows` identical for all 63 cells, `exit=0`, `live_requests: 0`.
