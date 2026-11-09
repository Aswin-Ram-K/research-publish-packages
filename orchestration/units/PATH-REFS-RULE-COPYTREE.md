# PATH-REFS-RULE-COPYTREE

Status: done. Unit card, persisted by the unit.

## Objective
Fix the resolver's candidate set rather than adding citations: a same-basename hit that is a
byte-identical copy in a duplicated tree is not an addressable alternate, so it must not be a
candidate.

## Bound
24 tool calls; offline, zero requests; no `ask_user_question`.

## Write paths
`path_refs.py`, `path_refs_resolve.py`, `test_path_refs_candidates.py`,
`test_path_refs_resolve.py`, `measure/PATH-REFS-COPYTREE.json`, this card,
the handoff, the journal.

## Method
1. Characterise the artefact class by evidence (digest, not dirname): candidate count and
   sha256 per citation.
2. Implement the smallest rule in the guard and state it in one sentence in the docstring.
3. A/B re-census in one process (rule on vs off) to remove concurrent drift from the
   comparison, plus the guard's own `--check` for key stability.
4. Three tests: artefact becomes `missing`; genuine duplicate stays ambiguous; an `ok`
   citation stays `ok`.

## Result
`wrong_dir` 636 -> 450, `missing` 266 -> 452, `ok`/`ignored` untouched by the rule,
`wrong_dir + missing = 902` = baselined keys, `0 new`. Tests 8 passed.
