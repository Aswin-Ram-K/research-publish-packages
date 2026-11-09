# QUALITY-REASON-MIX — what does H3 actually measure?

**Unit:** `QUALITY-REASON-MIX` · **Offline:** 0 inference requests, 0 live runs ·
**Data:** 11 `grade_v5` documents (75 checkpoint cells, 11 grids, 4 arms) plus 8
superseded `grade_v4` documents, all already on disk under
`experiments/ptr-engine/measure/`.
**Machine-readable result:** [`measure/QUALITY-REASON-MIX.json`](../experiments/ptr-engine/measure/QUALITY-REASON-MIX.json)
**Generator:** [`tools/reason_mix.py`](../experiments/ptr-engine/tools/reason_mix.py) ·
**Tests:** [`measure/experiments/ptr-engine/measure/tests/test_reason_mix.py`](../experiments/ptr-engine/measure/tests/test_reason_mix.py) (12 passed)

---

## 1. The headline, in one table

Primary population: the 8 documents generated at/after `2026-10-26T15:56Z`
(Repair-T3 grader), real `rows-longrun-*.jsonl` grids only, **66 cells**.
Two demo-fixture documents and three pre-T3 documents are reported separately in
§5 — pooling them would confound a grader-version change with an arm difference.

| arm class | never_answered | answered_wrong_value | answered_right_but_rejected_by_contract | undecidable | unclassifiable | non-passes | passes |
|---|---|---|---|---|---|---|---|
| `pointer-stable` | **21** | **0** | 1 | 0 | 0 | 22 | 2 / 24 |
| other three arms | **42** | **0** | 0 | 0 | 0 | 42 | 0 / 42 |
| **TOTAL** | **63** | **0** | **1** | **0** | **0** | **66** | **2 / 66** |

Across **every** grade document on disk, all grids and both grader eras
(75 cells):

| arm class | never_answered | answered_wrong_value | contract | undecidable | unclassifiable | non-passes | passes |
|---|---|---|---|---|---|---|---|
| `pointer-stable` | 21 | **0** | 3 | 0 | 0 | 24 | 3 / 27 |
| other three arms | 42 | **0** | 0 | 0 | 0 | 42 | 6 / 48 |
| **TOTAL** | **63** | **0** | **3** | **0** | **0** | **66** | **9 / 75** |

All six non-pointer passes are the two **demo-fixture** documents
(`cell-transcript-grow-20261026T144452Z.grade-v5.json` over `/tmp/cell-demo-rows.jsonl`;
`cell-transcript-grow-20261026T144540Z.grade-v5.json` over `.cell-demo/rows.jsonl`) —
neither rows file still exists. On real grids `transcript-grow` is **0/18**.

### The percentage the unit card asked for

`bucket 3 / non-pointer non-passes` = **0 / 42 = 0.0 %**, against the 60 %
threshold in the card. **The threshold is NOT met**, so the card's conditional
sentence ("H3 compares contract compliance, not pointer mechanics") is *not*
licensed by the reason strings as written. The actual finding is different and is
stated in §4.

`bucket 2 / all non-passes` = **0 / 66 = 0.0 %**: **not one checkpoint failure in
the entire v5 corpus is a wrong value.**

---

## 2. What each pointer-stable success actually is

All three pointer passes are the **same checkpoint** and the **same answer text**:

| grid | checkpoint | `answer_raw` accepted | gate | document |
|---|---|---|---|---|
| `rows-longrun-v4-2026-10-26.jsonl` | `cp.0.t12` | `ANSWER: 64` | `num_equal` | `cell-longrun-v4-20261026T1556Z.grade-v5.json` |
| `rows-longrun-v4-tools-2026-10-26.jsonl` | `cp.0.t12` | `ANSWER: 64` | `num_equal` | `cell-longrun-v4-tools-20261026T1556Z.grade-v5.json` |
| `rows-longrun-v6-tools.jsonl` (pre-T3) | `cp.0.t12` | `ANSWER: 64` | `num_equal` | `cell-pointer-stable-20261026T145722Z.grade-v5.json` |

The truth is `DEFAULT_MAX_REFS = 64` at `experiments/ptr-engine/ptr_engine/resolve.py:39`.
So the only checkpoint any arm has ever passed is the one whose answer is a single
small integer, and it is the checkpoint with `required_anchors=[]`
(`anchor_census`, `cell-longrun-v4-20261026T1556Z.grade-v5.json`) — i.e. the one
place the metric does not ask for a symbol, an anchor, or a call. `cp.1.t24` (count
31) and `cp.2.t46` (the `_refuse` call) have **never** passed in any arm, in any
grid, in either grader era.

**Would the same answer text from a transcript arm also have passed?** Yes, and
this is not a guess:

1. The grader is **arm-blind by construction**. `grade_v5.grade_rows` groups rows
   by `row["arm"]` purely for bookkeeping; the verdict comes from
   `parse_answer_contract(row["content"])` and the fixture truth. Probed offline,
   in memory, no fixture or grader edit
   (`arm_blindness_probe` in the JSON): the same three answer texts fed under
   `pointer-stable` and under `transcript-grow` return **identical** `(verdict,
   reason)` triples — `identical_for_both_arms: true` for both the accepted and the
   rejected case.
2. It has already happened on disk. The two demo documents grade a
   **`transcript-grow`** arm on the very same fixture
   (`longrun/tasks-v5/runtime-v5/LR-01.v5.json`) at **3/3**, with
   `ANSWER: NUM 64` → `num_equal`, `ANSWER: NUM 31` → `num_equal`,
   `ANSWER: CALL ledger.record_refusal(code=error.code, scope=scope_name, serialized_ref=text)`
   → `call_equal`. A transcript arm passes every checkpoint of this fixture when it
   writes the contract form — including the two checkpoints pointer-stable has never
   reached.

**Consequence for H3:** the 2-of-12 margin (`docs/TVS.md:94`, frozen in
`docs/PREREG-ARM-RUN.md:99`) cannot be attributed to pointer mechanics, because
the identical answer text passes under either arm label.

---

## 3. The one cell where the right answer was rejected on shape

`rows-longrun-v6-tools.jsonl` / `pointer-stable` / `cp.2.t46`
(`cell-pointer-stable-20261026T145722Z.grade-v5.json`, verdict `fail`, reason
`answer_not_contract`, `answer_parse_error: not_a_contract_form`):

```
ANSWER: ledger.record_refusal(scope=scope_name, serialized_ref=text, code=error.code)
```

The **same content** was graded **`ok` (pass)** by `grade_v4`
(`rows-longrun-v6-tools.grade-v4.json`, `found_excerpt` contains the same line and
the prose "`_refuse` calls `ledger.record_refusal` … passing `scope=scope_name`,
`serialized_ref=text`, and `code=error.code`"). The callee and all three kwargs are
right. It failed v5 only because the line does not carry the `CALL` prefix the
`ANSWER-CONTRACT v1` form list requires (`contract.forms` in that document).

That is a textbook `answered_right_but_rejected_by_contract` cell in the pointer
arm — the single clearest instance of the mechanism the unit card was testing for.
It is also the **only** v4-pass → v5-fail demotion in the corpus
(`cells_demoted_v4_pass_to_v5_fail`, length 1).

---

## 4. Verdict on H3

**H3 as frozen does not compare pointer mechanics, and — on the reason strings as
written — it does not compare contract compliance either: it compares answer
production.** 63 of 66 non-passes (95.5 %) are `never_answered`; 0 of 66 are wrong
values; 1 of 66 is a contract rejection. The metric's whole dynamic range is "did
this arm emit a gradable `ANSWER:` line at the declared turn", and its only
observed positive is one integer checkpoint reached by brute plausibility.

Two facts make this the *reported* verdict rather than an artefact of naming:

- **Bucket 2 is empty, not sparse.** Zero `num_mismatch`/`callee_mismatch`/
  `missing_anchor` cells exist in the v5 corpus. A metric that never records a
  wrong value cannot be measuring whether the pointer resolved the *right object*:
  wrong-object failure would land in bucket 2 and bucket 2 never fires.
- **The v4 documents show what v5 lost.** v4 graded the same grids with content
  scanning rather than a contract line, and in matched cells it recorded bucket-2
  reasons that v5 relabels as non-answers
  (`v4_vs_v5_cross_tab`, paired on identical `(grid, arm, checkpoint)`):
  `number_wrong:*` → v5 `prose_only` **7** cells,
  `missing_anchor:ledger` → v5 `prose_only` **4**,
  `value_not_in_concluding_position` → v5 `prose_only` **4** and `no_answer_line` **3**,
  `number_wrong:7` → v5 `answer_not_contract:multiple_answer_lines` **1**.
  So 8 cells the v4 grader could see a value in are `never_answered` under v5. The
  contract seam did not create wrong answers; it converted *readable-but-unformatted*
  content into *no answer at all*. That is the format sensitivity the card
  hypothesised — it is real, it is latent in the `never_answered` bucket, and it is
  invisible to a percentage computed over reason strings.

Caveat recorded rather than smoothed: those v4 reasons assert "a number that is not
the expected value appears somewhere in the content", not "the model answered X".
They are evidence that content was present and readable, not evidence of an answer
attempt. This analysis therefore does **not** move those 8 cells to bucket 2; it
reports that v5 cannot distinguish them from silence.

---

## 5. Population accounting (what was excluded and why)

| population | cells | source documents | why separate |
|---|---|---|---|
| primary (T3 era, real grids) | 66 | the 8 `cell-*T1556Z.grade-v5.json` documents | generated after Repair T3 |
| pre-T3, real grids | 3 | `cell-pointer-stable-20261026T145722Z.grade-v5.json` | generated `2026-10-26T14:57:22Z`, before the T3 boundary; its reasons `answer_not_contract` (bare) and parse error `not_a_contract_form` are **not producible by the on-disk `grade_v5.py`** (see §6) |
| demo fixtures | 6 | the two `cell-transcript-grow-*` documents | their rows files (`/tmp/cell-demo-rows.jsonl`, `.cell-demo/rows.jsonl`) no longer exist; used only as the "does a transcript arm pass" witness in §2 |
| v4-only checkpoints (`acc.n3b`, `repair.t30`) | excluded | all `rows-*.grade-v4.json` | not v5 checkpoint cells |

`grade_v4` is used *only* for the paired cross-tab in §4 and the demotion in §3. No
v4 document is treated as a current measurement.

Duplicate detection: 75 cells, 0 duplicate `(grid, arm, checkpoint_id)` keys — the
narrow `cell-pointer-stable-*` and `cell-transcript-grow-*` documents cover grids not
otherwise graded by a v5 document, so each cell appears exactly once.

---

## 6. Recorded gap (not fixed here — no grader edit was made)

`cell-pointer-stable-20261026T145722Z.grade-v5.json` was produced by a grader that
no longer exists on disk. Its `cp.2.t46` cell carries
`answer_parse_error: "not_a_contract_form"` and `reason: "answer_not_contract"`,
but `experiments/ptr-engine/longrun/grade_v5.py` contains no string
`not_a_contract_form` at all (grep: 0 hits), and its `grade_cell` emits
`answer_not_contract:<err>` with a suffix for non-`NON_ANSWER_ERRORS` errors. The
on-disk grader applied to that row's content returns `unparseable`. The cell is
tabulated as its document records it (`answered_right_but_rejected_by_contract`,
flagged `reason_disagreement_cells`), and the sensitivity is: even if that one cell
were moved to `never_answered`, the primary table changes by 1 in one cell and
**no conclusion in §4 moves** (bucket 3 for non-pointer arms stays 0/42).

The one cell whose `reason` contradicts its own `answer_parse_error`
(`answer_not_contract` vs `no_answer_line`, grid `rows-longrun-v6-tools.jsonl`,
arm `pointer-stable`, checkpoint `cp.1.t24`) also sits in that pre-T3 document.

---

## 7. The smallest change that would make the metric mechanism-bearing — named, not made

**Choose: publish a per-arm `answered_ratio` beside every accuracy.**
`answered_ratio = gradable answers / declared checkpoints`, taken from the same
`grade_v5.decidable_population` call that already produces `passed`/`failed`, so it
costs one derived number per arm and no re-run, no new requests, and no grader
change. It makes the H3 comparison falsifiable in one line: an arm at `2/12`
accuracy with `2/12` answered is a *conversion* question, while an arm at `2/12`
with `9/12` answered is a *mechanics* question — and today every published accuracy
number silently mixes the two.

Rejected, with reasons:

- *`contract_adherence` pre-check as a separate column* — it would only label the
  `answered_not_contract` cells. On this corpus that column is **1 cell of 66**,
  while the confound lives in the 63 `never_answered` cells (§4), so it would
  measure the small effect and miss the large one.
- *Requiring a passed practice checkpoint first* — it changes the run protocol, so
  it costs a re-run of the grid (the 792-request question all over again) and is not
  the smallest change.

**Changing H3's frozen 2-of-12 margin requires a `PARM-1` errata, not a rewrite** —
precedent `PARM-1-ERRATA` (`67e4cd7f`), recorded in
[`docs/PARM-1-ERRATA.md`](PARM-1-ERRATA.md). Nothing in this unit edits the frozen
margin, the preregistration, or any published document.

---

## 8. Mapping rules used (auditable without this document)

Classified strictly from the grader's own `reason` string, quoted verbatim in every
row of `measure/QUALITY-REASON-MIX.json`. Head-matched on the `:` suffix.

| bucket | reasons |
|---|---|
| `never_answered` | `turn_missing`, `prose_only`, `no_answer_line`, `empty_answer`, `empty_text`, `empty_num`, `marker_missing`, `marker_without_value`, `preamble_only`, `truncated_without_value` |
| `answered_wrong_value` | `number_wrong:*`, `missing_anchor:*`, `keyword_missing`, `callee_mismatch`, `keyword_mismatch`, `value_not_in_concluding_position` |
| `answered_right_but_rejected_by_contract` | `answer_not_contract`, `answer_not_contract:multiple_answer_lines`, `not_a_contract_form`, `multiple_answer_lines`, `row_fields_disagree_with_content`, and `unparseable` **only when `answer_raw` is not the no-answer sentinel** |
| `undecidable` | a cell with no verdict at all (`pass: null`), or `unverifiable` |
| `other:<name>` | `refused_while_knowable`, `repair_not_acknowledged` |
| `unclassifiable` | any reason not in this table — reported with the reason, never guessed. **Count in this corpus: 0.** |

The `unparseable` sentinel rule is the one judgement call, and it is why the card's
literal reading of bucket 3 would overstate contract sensitivity: 9 of the 12
`unparseable`/`answer_not_contract` cells carry `answer_raw == "ANSWER: NOT-AN-ANSWER"`,
the runner's no-answer placeholder — that is silence, not a right answer in a wrong
shape. Under the card's literal reading (all `unparseable` → bucket 3) bucket 3
becomes **12 of 66** non-passes and non-pointer bucket 3 becomes
**6 of 42 = 14.3 %** (`sensitivity_literal_unparseable_bucket3` in the JSON,
`threshold_met: false`), still far below the 60 % threshold. Both readings are in
the JSON; the conclusion in §4 is unchanged under both — `never_answered` stays
dominant at 54/66 = 81.8 % even in that reading.
