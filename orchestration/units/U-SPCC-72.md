# U-SPCC-72 — regenerate the three derived artefacts over the current corpus

## Why

`experiments/ptr-engine/longrun/tests/` was 6 failed / 925 passed. Four of the six
were corpus drift, not code defects: `measure/STOP-REASON.json`,
`measure/VERBOSITY.json` and `docs/VERBOSITY.md` were generated before today's
cells added rows files, so their recorded totals and corpus listing no longer
matched a fresh scan of `measure/rows-*.jsonl`.

## Generators (real, not hand edits)

| Artefact | Generator |
|---|---|
| `experiments/ptr-engine/measure/STOP-REASON.json` | `experiments/ptr-engine/tools/stop_reason_audit.py` (no args writes; `--check` compares totals against a fresh scan) |
| `experiments/ptr-engine/measure/VERBOSITY.json` | `experiments/ptr-engine/longrun/tests/test_verbosity.py` run as a script (`__main__` calls `build()` then `validate_report()`) |
| `docs/VERBOSITY.md` | same script — `build()` writes both `JSON_OUT` and `MD_OUT` |

Commands, from the repo root:

```
TMPDIR=/home/zer0null/tmp-pytest .venv/bin/python experiments/ptr-engine/tools/stop_reason_audit.py
TMPDIR=/home/zer0null/tmp-pytest .venv/bin/python experiments/ptr-engine/longrun/tests/test_verbosity.py
```

Both are offline: no endpoint, no cell re-run, no rows file written.

## Result

`stop_reason_audit.py` wrote `rows 10167, answered 8772, empty 1395,
empty-with-tokens 1377, reasoning-with-empty-content 1205`, causes
`{"no_answer_text_field": 31, "unrecorded_empty_content": 1352, "zero_tokens_no_content": 12}`.

`test_verbosity.py` wrote both artefacts, `cells=128 p95_ok=50 refused=75
decomp=36 fits=93`, `VERDICT confound_immaterial`, `VALIDATE_ERRORS []`.

Corpus row total: `wc -l experiments/ptr-engine/measure/rows-*.jsonl` → **10167**,
matching `STOP-REASON.json` `totals.rows`.

## Tests

The four corpus-drift tests now pass:

```
experiments/ptr-engine/longrun/tests/test_stop_reason.py::OnDiskArtefact::test_stop_reason_json_matches_a_fresh_scan
experiments/ptr-engine/longrun/tests/test_verbosity.py::test_every_rows_file_appears_with_its_sha
experiments/ptr-engine/longrun/tests/test_verbosity.py::test_recomputation_agrees_with_rows
experiments/ptr-engine/longrun/tests/test_verbosity.py::test_fabricated_mean_fails_recomputation
→ 4 passed in 1.31s
```

Full directory: `2 failed, 929 passed, 1 warning, 36 subtests passed in 45.72s`.

The two remaining reds are correctly red and were left untouched:

- `test_journal_lint.py::test_census_over_the_live_corpus_is_reported` — 319 real
  journal misses; authoring journals now would fabricate history.
- `test_request_ledger.py::TestRealCorpus::test_g_real_corpus_total_and_delta_from_466`
  — `spent=10167 > cap=4320 (over by 5847)`; a true over-budget fact awaiting an
  operator decision.

## Side effect handled

The full-directory run rewrote six `experiments/ptr-engine/state/previews/LR-01/*`
files with an emptied `INDEX` block. Those are test side effects, not this unit's
work; they were restored from `HEAD` (`git show HEAD:<path> > <path>`) so the
commit carries only the three artefacts.

## Commit

`a8031bd2d142f5e26c1e6a239cba23663d85670f` on `research/next-candidates-2026-10-24`,
pushed (`d9268db..a8031bd`). `git --no-optional-locks status --porcelain` empty.
