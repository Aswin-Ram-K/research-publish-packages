# U-SPCC-38 — fix the stale compaction assertion, regenerate the two derived artefacts

Status: done. Head tested: `e18a587` (branch `research/next-candidates-2026-10-24`).

## 1. The stale assertion

`experiments/ptr-engine/longrun/tests/test_layers_compiler.py:90` asserted
`any("summary" in ln.lower() for ln in state.index_lines)`. Commit `df1e2c0` replaced the
marker at `experiments/ptr-engine/ptr_engine/layers.py:234` with
`"[compacted: %d turns dropped at epoch %d]"` precisely because the old
`"[summary: %d turns folded into epoch %d]"` claimed a summary that did not exist. The test
still pinned the removed word, so it failed on a correct change.

The rewrite does not re-pin the word `compacted` (that would move the same incidental-wording
dependency one word over). It tests the behaviour, at
`experiments/ptr-engine/longrun/tests/test_layers_compiler.py:84,91-102`:

- `before = list(state.index_lines)` captured before the compile;
- `len(state.index_lines) == len(before) + 1` — the fold appends exactly one line;
- `marker = state.index_lines[-1]` is bracketed (`startswith("[") and endswith("]")`);
- `"summary" not in marker.lower()` — the honesty property that motivated `df1e2c0`, kept;
- `str(len(journal)) in marker` — the marker names the number of turns dropped (24).

The pre-existing assertions (`compactions == 1`, `epoch == 1`, `journal == []`, the two
`_idx()` lines still present, `out.epoch`/`out.compactions`) are untouched, so nothing is
duplicated.

Red at HEAD:

```
>       assert any("summary" in ln.lower() for ln in state.index_lines)
E       assert False
experiments/ptr-engine/longrun/tests/test_layers_compiler.py:90: AssertionError
1 failed, 4 passed in 0.03s
```

Green after:

```
.....                                                                    [100%]
5 passed in 0.03s
```

## 2. The derived artefacts

Both regenerated with their own generators, never by hand:

- `experiments/ptr-engine/tools/stop_reason_audit.py` → `experiments/ptr-engine/measure/STOP-REASON.json`
- `experiments/ptr-engine/longrun/tests/test_verbosity.py` (`build()`) → `experiments/ptr-engine/measure/VERBOSITY.json` and its companion `docs/VERBOSITY.md`

| artefact | before | after |
|---|---|---|
| `STOP-REASON.json` rows | 7,969 | 8,081 |
| `STOP-REASON.json` answered_rows | 6,665 | 6,777 |
| `VERBOSITY.json` corpus files | 93 | 96 |
| `VERBOSITY.json` rows_total | 7,969 | 8,081 |
| `VERBOSITY.json` completed turns | 6,122 | 6,234 |

The +112 rows are `rows-e1-spcc-2026-11-10.jsonl` (100, tracked in `e18a587`) plus the two
smoke files `rows-smoke-spcc-2026-11-10.jsonl` and `rows-smoke-spcc2-2026-11-10.jsonl`
(6 each). The two smoke files were untracked; they are committed with this unit because
`VERBOSITY.json` declares the corpus it was computed over and
`test_verbosity.py::test_every_rows_file_appears_with_its_sha` compares that declaration
against the on-disk corpus — committing the artefact without them would ship a report that
fails on a fresh checkout.

`STOP-REASON.json` cause counts are unchanged (`no_answer_text_field` 31,
`unrecorded_empty_content` 1261, `zero_tokens_no_content` 12) and
`completion_tokens_spent_on_empty_content` stays 111,608: the 112 new rows are all answered,
so they move `rows` and `answered_rows` only. `VERBOSITY.json` verdict is unchanged
(`confound_immaterial`, 86.7% of the TTFT gap survives completion-length normalisation).

## 3. Suite

```
TMPDIR=/home/zer0null/tmp-pytest .venv/bin/python -m pytest experiments/ptr-engine/longrun/tests -q --tb=no -rf
2 failed, 860 passed, 1 warning, 31 subtests passed in 46.30s
```

Remaining failures, both correctly red and untouched:

- `test_journal_lint.py::test_census_over_the_live_corpus_is_reported` — five journal-less
  handoffs (`A1-AUTHOR`, `A2-FIX`, `A3-FIX`, `ACCFIX2`, `ACCRESCOPE`) outside the frozen
  baseline.
- `test_request_ledger.py::TestRealCorpus::test_g_real_corpus_total_and_delta_from_466` —
  `OVER BUDGET: spent=8081 + would_spend=0 = 8081 > cap=4320 - reserve=0 = 4320 (over by 3761)`.

`state/logs/journal-lint-baseline.json` was not re-frozen and no budget cap was changed.

`tools/doc_check.py` exits 0.
