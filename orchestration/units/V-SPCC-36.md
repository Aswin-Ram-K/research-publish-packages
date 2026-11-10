# V-SPCC-36 — longrun suite red-set audit: 1 real regression, 6 explained

## 0. State tested

```
git --no-optional-locks rev-parse HEAD
e18a587557bcdef71ff2cec82aae4dcccd96dc02
```

`git --no-optional-locks status --porcelain` before the run: 5 untracked entries
(`manifests/smoke-spcc-2026-11-10-spcc-r1.json`,
`manifests/smoke-spcc2-2026-11-10-spcc-r1.json`,
`measure/rows-smoke-spcc-2026-11-10.jsonl`,
`measure/rows-smoke-spcc2-2026-11-10.jsonl`,
`orchestration/handoffs/U-SPCC-26.json`). HEAD and the untracked count were
re-checked after the run: unchanged (`e18a587`, 5). The tree did not move under
the audit.

All three named commits are ancestors of HEAD:
`df1e2c0` yes, `997df58` yes, `d43fea7` yes.

## 1. The run

```
TMPDIR=/home/zer0null/tmp-pytest .venv/bin/python -m pytest \
  experiments/ptr-engine/longrun/tests -q --tb=short -rf
```

`7 failed, 850 passed, 1 warning, 31 subtests passed in 48.27s`.

The prior unit's "850 passed, 7 failed" is reproduced exactly. Its
classification of all seven as "pre-existing corpus/state drift" is **wrong for
one item**.

## 2. Classification table

| test id | classification | evidence | fails on parent `ba064ba`? |
|---|---|---|---|
| `test_layers_compiler.py::test_compaction` | **REGRESSION** (`df1e2c0`) | `tests/test_layers_compiler.py:90` asserts `any("summary" in ln.lower() for ln in state.index_lines)`. `ptr_engine/layers.py:234` now emits `marker = "[compacted: %d turns dropped at epoch %d]"`. No `summary` substring survives. Parent `ba064ba:experiments/ptr-engine/ptr_engine/layers.py:227` had `summary = "[summary: %d turns folded into epoch %d]"`. | **No** — passes on parent |
| `test_journal_lint.py::test_census_over_the_live_corpus_is_reported` | CORRECTLY-RED | 5 handoffs have no journal and are not in the frozen baseline: `orchestration/handoffs/{A1-AUTHOR,A2-FIX,A3-FIX,ACCFIX2,ACCRESCOPE}.json`; `orchestration/journals/<unit>.jsonl` MISSING for all five. Baseline `state/logs/journal-lint-baseline.json` frozen `2026-10-26T12:06:27-0500`, 1009 entries, none of the five present; the file is untracked (`git ls-files` → pathspec did not match). | Yes — `9fadcc9` (which added the five) is an ancestor of `ba064ba`; baseline unchanged |
| `test_request_ledger.py::TestRealCorpus::test_g_real_corpus_total_and_delta_from_466` | CORRECTLY-RED | `tests/test_request_ledger.py:305` asserts `proc.returncode == 0` for `--cap 4320`; tool exits 4: `OVER BUDGET: spent=8081 + would_spend=0 = 8081 > cap=4320 ... (over by 3761)`. Corpus is 8081 rows (`cat measure/rows-*.jsonl \| wc -l` = 8081). | Yes — corpus was 7969 rows at `ba064ba`, still > 4320 |
| `test_stop_reason.py::OnDiskArtefact::test_stop_reason_json_matches_a_fresh_scan` | CORPUS-DRIFT | `tools/stop_reason_audit.py --check`: on disk `rows=7969, answered_rows=6665`; rescan `rows=8081, answered_rows=6777`. Delta +112 rows = the three new rows files (100 + 6 + 6). `STOP-REASON.json` last regenerated in `9c2eceb`. | No — at `ba064ba` the corpus was 7969 and the artefact matched |
| `test_verbosity.py::test_every_rows_file_appears_with_its_sha` | CORPUS-DRIFT | `VERBOSITY.json` declares 93 corpus files; 96 on disk. Missing from report: `rows-e1-spcc-2026-11-10.jsonl`, `rows-smoke-spcc-2026-11-10.jsonl`, `rows-smoke-spcc2-2026-11-10.jsonl`. `VERBOSITY.json` last regenerated in `9c2eceb`. | No — the three files postdate `ba064ba` (`rows-e1-spcc` added in `e18a587`; the two smoke files are untracked) |
| `test_verbosity.py::test_recomputation_agrees_with_rows` | CORPUS-DRIFT | same three `rows file missing from corpus:` errors from `validate_report(VERBOSITY.json)` | No — same cause |
| `test_verbosity.py::test_fabricated_mean_fails_recomputation` | CORPUS-DRIFT | `assert validate_report(JSON_OUT) == [], "the real report must still pass"` fails on the same three missing rows files | No — same cause |

## 3. Counts

- REGRESSION: **1**
- CORPUS-DRIFT: **4**
- CORRECTLY-RED: **2**
- ENVIRONMENT: **0**

## 4. Verdict

**The red set is NOT entirely explained.** `test_layers_compiler.py::test_compaction`
is a real regression introduced by `df1e2c0` and must be fixed before any further
live run. The other six are genuine repo-state signals (2) or stale derived
artefacts over a corpus that grew by 112 rows (4), none caused by the three named
commits.

## 5. The fix (not applied — read-only unit)

`experiments/ptr-engine/longrun/tests/test_layers_compiler.py:90`

```python
assert any("summary" in ln.lower() for ln in state.index_lines)
```

should become

```python
assert any("compacted" in ln.lower() for ln in state.index_lines)
```

or, tighter and preferred, pin the exact marker for this fixture (24 journal
lines, epoch 0 → 1):

```python
assert "[compacted: 24 turns dropped at epoch 1]" in state.index_lines
```

`df1e2c0` added `tests/test_layers_compaction.py` (4 tests, all passing) which
pins the new behaviour; the old `test_layers_compiler.py` was simply not updated
in the same commit.

## 6. Notes

- `997df58` and `d43fea7` produced no failures. `test_spcc_arm.py`,
  `test_spcc_claim.py`, `test_spcc_delivery.py`, `test_claim_mode.py` and
  `test_cell.py` are all green.
- The two untracked `rows-smoke-spcc*` files are the concurrent E1 cell's
  working-tree output; they are part of the +112 row drift and will keep the
  verbosity/stop-reason artefacts stale until those artefacts are regenerated.
