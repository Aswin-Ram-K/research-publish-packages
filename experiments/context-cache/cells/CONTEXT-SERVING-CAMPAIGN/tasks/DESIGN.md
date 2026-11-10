# Task instrument V2 — family design

Supersedes V1 (kept at `tasks/superseded-v1/`). V1 had one family (running
numeric aggregate) for all eight instances; held-out H1-H4 were reworded
discovery clones, and no turn required recalling an exact masked body. V2 keeps
the `cs.grade/1` grader interface, the bwrap containment runner, and the
negative-mutant matrix, but changes the instance families and adds explicit
per-turn dependency metadata.

## Family map

| ID | Split | Family | Surface form | Answer keys |
|----|-------|--------|--------------|-------------|
| D1 | discovery | running_numeric_aggregate | signed observations, cumulative sum | `total` |
| D2 | discovery | running_numeric_aggregate | temperature observations, range + count | `range`, `count` |
| D3 | discovery | file_state_recall | edit events on string-valued keys; asks previous value | `previous` |
| D4 | discovery | file_state_recall | edit events on integer-valued keys; asks previous value | `previous` |
| H1 | heldout | multi_step_edit_application | append/replace/delete over a token list; report final sequence | `sequence` |
| H2 | heldout | multi_step_edit_application | append/insert/delete over a text buffer; report final buffer | `buffer` |
| H3 | heldout | constraint_precedence_resolution | early default + base-wins precedence rule; later override requests | `resolved`, `rule`, `base` |
| H4 | heldout | constraint_precedence_resolution | early priority-ranked constraints; later override requests | `resolved`, `assigned` |

Two families per split, two instances per family. Discovery and held-out family
names and answer-contract key sets are disjoint; `tests/test_campaign_tasks.py::
test_two_distinct_families_per_split` enforces that.

## Dependency counts

`requires_turns` records the source turns an expected answer actually needs.
"Early" means a required source turn strictly before the current turn and at
turn <= 6, i.e. inside the region a `mask_after=6` arm masks.

| ID | Turns | Early-dependent turns (count) | `expect_exact_body` turns | Reference pass |
|----|-------|-------------------------------|---------------------------|----------------|
| D1 | 12 | 2-12 (11) | 0 | yes |
| D2 | 12 | 2-12 (11) | 0 | yes |
| D3 | 12 | 4-9 (6) | 11 | yes |
| D4 | 12 | 4-9 (6) | 11 | yes |
| H1 | 12 | 2-12 (11) | 7 | yes |
| H2 | 12 | 2-12 (11) | 11 | yes |
| H3 | 12 | 7-12 (6) | 0 | yes |
| H4 | 12 | 7-12 (6) | 0 | yes |

Every instance has at least six turns whose answer depends on a masked-region
source, so arms C and D face a real tradeoff: they cannot answer those turns
from the visible tail alone and must recover the referenced body (or lose
quality). `test_dependency_count_at_least_six` asserts the count; a red proof
sets the mask boundary to 0 and the same assertion fails for D3/D4/H3/H4.

## Exact-body turns

`expect_exact_body: true` marks turns that only an exact retrieved body
resolves. D3/D4 ask for the verbatim previous value of a key (e.g.
`previous=alpha-4`); H1/H2 ask for the byte-exact final sequence/buffer. A gist
or summary that preserves topic but not the value cannot answer them.
`test_exact_body_turn_present` requires at least one such turn overall and at
least one with a non-numeric expected value.
`test_exact_body_not_in_current_event` additionally requires that the expected
value is absent from the current turn's event JSON, so the flagged turn cannot
be answered without the earlier body.

## Why held-out is not a reworded discovery clone

- **Different surface form.** Discovery is a single stream of observations
  (numeric aggregate) or one-key edit events (file-state recall). H1/H2 are
  stateful document edits where each turn changes a sequence/buffer and the
  answer is the accumulated final state. H3/H4 declare rules in early turns and
  ask for a resolved setting later; the answer is a precedence decision, not an
  arithmetic reduction.
- **Different answer contracts.** Discovery keys (`total`, `range`, `count`,
  `previous`) do not appear in held-out contracts (`sequence`, `buffer`,
  `resolved`, `rule`, `base`, `assigned`).
- **Different required reasoning.** Discovery needs aggregation or a single
  prior-value lookup. H1/H2 need ordered edit replay with position tracking.
  H3/H4 need earliest-turn evidence (precedence rule / priority ranking) applied
  to later requests, and the precedence evidence exists only in turns 1-6, so a
  model that keeps only recent turns cannot resolve the request.

## Determinism and seeds

All generators use `random.Random(seed)` only; no clock, network or environment
reads. V2 seeds are 2026110521-2026110528 (V1 used 2026110501-2026110508).
`tests/test_campaign_tasks.py::test_seed_determinism` regenerates twice and
compares serialized bytes, and checks the on-disk seed for D1/H4.
