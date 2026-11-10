# U-SPCC-21 — two degenerate row fields, and the scorecard that must not launder them

**Status:** done · **Live requests:** 0 · **Files:** `experiments/ptr-engine/longrun/run_longrun.py`,
`experiments/ptr-engine/longrun/score_longrun.py`,
`experiments/ptr-engine/longrun/tests/test_degenerate_fields.py` (new),
`experiments/ptr-engine/longrun/tests/test_arm_treatments.py`

## What was wrong (established by diagnosis, not re-derived here)

* `evicted` was initialised to `0` at `run_longrun.py:1453` and assigned **only** inside
  `if arm == "transcript-grow":` (`:1465–1481`). The masking arm never entered that branch, so every
  masking row carried `evicted: 0` — including turn 5, the turn its only fact was masked away
  (`masked_rows == 1`, `masked_entry == [{'ref': 'doc-fact-01@r1', 'since_turn': 1}]`).
* `expected_present` was computed from `reasoning_raw` (`:2581`), which is empty whenever thinking is
  off, so it read `False` on all 48 checkpoints including the 8 that answered correctly.

## What changed

### 1. `evicted` means what its name says, or it is null

`run_longrun.py:1453` now initialises `evicted` to `None`, not `0` (ABSENT ≠ 0). Assignments:

| arm | `evicted` |
|---|---|
| `transcript-grow` | unchanged: the FIFO/byte-wall count it already computed |
| `masking-no-fetch`, `bounded-context-fetch` | `masked_rows` — a masked entry **is** the eviction, they are the same event (`:1610`) |
| `transcript-compact`, `pointer-stable`, `lease-reopen`, `spcc` | `None` — no eviction measurement exists, and `0` would assert one nobody made |

### 2. `expected_present` is about the PROMPT

New helper `expected_value_in_prompt(prompt_text, expected)` (`:2112–2138`) returns
`(present | None, source)` with source ∈ `no-checkpoint`, `no-prompt-retained`,
`expected-non-numeric`, `prompt-digit-boundary`, `prompt-val-anchor`, `prompt-absent`.
Searches the rendered prompt with the digit-boundary guard `(?<![\d.])<expected>(?![\d.])` plus the
`VAL_<X> = <value>` binding anchor. `make_row` consumes the prompt from `extra["prompt_text"]`
(wired once at the `extras` literal `:3286`, overridden at the two digest call sites with the digest
request's own text). The response-side test still exists under its own name,
`expected_in_reasoning`, and still decides `answer_source`, `failed_turn` and `answer_verified`.
Every row now also carries `expected_present_source`.

### 3. Scorecard: four outcome counters beside an unchanged `checkpoint_accuracy`

`score_longrun.py::score_answer_contract_rows` gains `answered_correctly`, `abstained_after_mask`,
`answered_wrong`, `unparsed`, `checkpoint_accuracy` (`"%d/%d" % (answered_correctly, total)`),
`outcome_split_note` and `mask_turn_by_doc`. Masked-before-probe is decided from the arm's own
`masked_entry` rows (`mask_turn_by_doc`), joined to a checkpoint through
`_checkpoint_doc` (`tool_output:doc-fact-01@r1` → `doc-fact-01`) — no re-derivation of the window
and no trust in the formerly degenerate fields. An abstention after a mask is legitimate arm
behaviour and is **not** counted as correct; `checkpoint_accuracy` keeps correct/total.

## Evidence

### Re-score of the existing rows file (no model call)

`experiments/ptr-engine/measure/rows-tx03-masking-r1.jsonl` + `tasks-v7/TX-03.v1.json`:

```
SCORECARD {'checkpoint_accuracy': '8/48', 'answered_correctly': 8, 'abstained_after_mask': 40,
           'answered_wrong': 0, 'unparsed': 0, 'total': 48, 'abstained': 40, 'ungradeable': 0}
mask_turn_by_doc {'doc-fact-01': 5, 'doc-fact-02': 12, 'doc-fact-03': 21, 'doc-fact-04': 28,
                  'doc-fact-05': 49, 'doc-fact-06': 56, 'doc-fact-07': 65, 'doc-fact-08': 72}
```

### The writer on the real fixture, freshly rendered (no model call)

Replaying `Planner("masking-no-fetch", TX-03, dry_run=True)` over all 100 turns with the
answers recorded, then asking `expected_value_in_prompt` about every checkpoint turn's prompt:

```
d=2  True  prompt-digit-boundary   8     <- the eight pre-mask probes now carry the value
d=5  False prompt-absent           8
d=6  False prompt-absent           8
d=8  False prompt-absent           8
d=20 False prompt-absent           8
d=32 False prompt-absent           8
mismatches []
mask/evict turns [(5,1,1),(12,1,1),(21,1,1),(28,1,1),(49,1,1),(56,1,1),(65,1,1),(72,1,1)]   # (turn, masked_rows, evicted)
```

Zero mismatches against the arm's design. This is the permanent test
`test_every_rendered_prompt_of_the_fixture_splits_eight_true_forty_false`.

### Red → green (pre-fix copies of both modules restored from HEAD into `/tmp/rg`)

```
FAILED test_masking_turn_with_one_masked_row_stamps_evicted_one
  - AssertionError: turn 5 masked 1 tool-output entry but evicted=0
  - assert 0 == 1
FAILED test_d2_probe_with_the_value_in_the_prompt_stamps_true
  - AssertionError: prompt carries '3000' but expected_present=False
  - assert False is True
FAILED test_arm_without_an_eviction_concept_stamps_null_not_zero — assert 0 is None
FAILED test_no_checkpoint_stamps_null — assert False is None
FAILED test_masked_prompt_without_the_value_stamps_false — KeyError: 'expected_present_source'
FAILED test_no_retained_prompt_stamps_null_and_says_why — assert False is None
FAILED test_real_rows_file_outcome_split_is_eight_forty_zero_zero — KeyError: 'answered_correctly'
8 failed, 2 passed
```

After the fix the same file is `10 passed`.

## Retained

`evicted` is `null` on arms with no eviction concept, `masked_rows` on the masking arms (same event),
and still the FIFO/byte-wall count on `transcript-grow`. `expected_present` is `True`/`False` only
when a rendered prompt was searched, `null` with a machine-readable reason otherwise. The scorecard
reports 8 correct / 40 mask-abstentions / 0 wrong / 0 unparsed with `checkpoint_accuracy` unchanged
at `8/48`.
