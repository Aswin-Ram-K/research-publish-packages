# LOST-FIXTURE — what one missing fixture digest costs the record

**Unit:** `LOST-FIXTURE` · **Date:** 2026-10-26 · **Live requests: 0** · **Network: none**
**Mode:** read-only on rows, fixtures, grade documents and published reports. This unit wrote only
[this page](docs/LOST-FIXTURE.md), [`measure/LOST-FIXTURE.json`](experiments/ptr-engine/measure/LOST-FIXTURE.json),
[`state/logs/lost-fixture-baseline.json`](state/logs/lost-fixture-baseline.json) and
[`longrun/experiments/ptr-engine/longrun/tests/test_lost_fixture.py`](experiments/ptr-engine/longrun/tests/test_lost_fixture.py).

**The digest:**

```
72c3832d95f9c7966b4358eda10fa2882775a416ee8a663d57b1c871ed19c44d
```

No file on disk hashes to it. `FIXTURE-GENERATIONS` called it `lost`; this page measures what that costs.
It is **recorded, not repaired**. Nothing was deleted, renamed, re-stamped or reconstructed.

---

## 1. The rows, proved from the rows

The field that carries the digest is **`fixture_sha256`** on row-provenance-era rows. Scanning every
`.jsonl` in the workspace, exactly **three** files contain that string:

| rows file | lines | rows pinning `72c3832d…` |
|---|---:|---:|
| `experiments/ptr-engine/measure/rows-longrun-2026-10-26.jsonl` | 192 | **192** |
| `experiments/ptr-engine/measure/rows-longrun-2026-10-26-policy.jsonl` | 40 | **40** |
| `experiments/ptr-engine/measure/rows-longrun-2026-10-26-fix.jsonl` | 29 | **27** |
| **total** | **261** | **259** |

**The ledger's `261` is a line count, not a row count.** The three files hold 261 lines, but two lines in
`rows-longrun-2026-10-26-fix.jsonl` do **not** carry the lost digest:

- line 28 — `fix-arm-lr01-transcript-grow-r1`, `transcript-grow`, turn 11, ts `2026-10-26T09:38:16.450Z`,
  `fixture_sha256` = `b7e303a65f200e7b3dfd339cf3c6a1f3b4e684e57ca271e74f8f5539a348a500` (v1, on disk);
- line 29 — same run/arm, turn 12, ts `2026-10-26T09:39:20.637Z`, same `b7e303a6…` digest.

So the correct population is **259 rows**, and the finding is **one run (`fix-arm-lr01-transcript-grow-r1`)
is split across two fixture digests**: 10 rows pin the lost digest, 2 rows pin the surviving v1 file. That
split is itself a provenance defect, independent of the loss.

### Files, grids, arms, turn ranges, dates

| grid | rows file | lost rows / lines | arms | turns | row-`ts` window |
|---|---|---|---:|---:|---|
| **G1 `stage1`** | `rows-longrun-2026-10-26.jsonl` | **192 / 192** | 4 — `lease-reopen`, `pointer-stable`, `transcript-compact`, `transcript-grow` (48 each) | 1–48 | `2026-10-26T07:26:41.810Z` → `07:39:07.122Z` |
| **G2 `smoke-rp`** | `rows-longrun-2026-10-26-policy.jsonl` | **40 / 40** | 4 (3 rows each except `transcript-grow`=31, which adds the 28-row `arm-rp` run) | 1–28 | `2026-10-26T08:09:52.830Z` → `11:52:48.974Z` |
| **G3 `fix-smoke`** | `rows-longrun-2026-10-26-fix.jsonl` | **27 / 29** | 4 | 1–10 | `2026-10-26T08:00:05.779Z` → `09:19:33.737Z` |

Sixteen distinct `run_id`s account for the 259 rows: 4 × `stage1-lr01-*-r1` (48 each), 4 ×
`smoke-rp-20261026T0310Z-*-r1` (3 each), 4 × `fix-smoke-lr01-*-r1` (3 each), `fix-smoke2-lr01-*-r1`
(3+2), `fix-arm-lr01-transcript-grow-r1` (10), `arm-rp-20261026T0335Z-transcript-grow-r1` (28). All rows:
`task_id=LR-01`, `engine=sglang`, `kind=turn`, `rep=1`, `checkpoint=null`, `is_checkpoint=false`.
Dates are one day: `2026-10-26`.

### The second finding — manifests name a surviving file with a different digest

**20 manifest files** under `experiments/ptr-engine/longrun/manifests/` pin the lost digest in
`fixture.sha256`, and **all 20 name `fixture.path` =
`/home/zer0null/reserach extarctor/experiments/ptr-engine/longrun/runtime/LR-01.json`**, whose bytes hash to
`b7e303a65f200e7b3dfd339cf3c6a1f3b4e684e57ca271e74f8f5539a348a500`. Every one of the 20 is therefore
internally inconsistent: it says "this run used the bytes at `runtime/LR-01.json`" **and** "the bytes were
`72c3832d…`". Both cannot be true. The two split rows in `rows-longrun-2026-10-26-fix.jsonl` are the only
rows that resolve to the path's actual digest.

This matters because it makes the loss **unrecoverable by inference as well as by bytes**: the path does
not identify what ran, and the digest identifies no file. `measure/ROW-PROVENANCE.json` records the same
run as `"fixture_sha256": "mixed"` with candidate list `["72c3832d…"]` and `provenance_complete: false`.

---

## 2. What the 259 rows can and cannot support

The rows are **complete measurement records of a run whose inputs are gone**. They can support:

- **arm identity** — `arm` is an explicit row field (`pointer-stable`, `transcript-grow`,
  `transcript-compact`, `lease-reopen`);
- **turn count and turn-index ordering** — `turn` runs 1..48 (G1) / 1..28 (G2) / 1..10 (G3) with no gaps
  within a run; `rep=1` throughout;
- **what the model emitted** — `content`, `content_sha256`, `completion_tokens`;
- **what was billed** — `prompt_tokens`, `cached_tokens`, `uncached_tokens`, `token_source`;
- **timing as measured** — `ttft_s`, `latency_s`, `ts`, `http_status`;
- **which digest the row claims** — `fixture_sha256`, and the manifest it claims — `run_manifest_sha256`.

They **cannot** support, because every one of these came from the fixture bytes:

| field that would have come from the fixture | what is now unverifiable |
|---|---|
| `turns` (the 48-turn plan) | **the task text** — what the model was asked at each turn; the rows contain answers to an unrecoverable prompt |
| `system_prompt` | the exact system instruction, including pointer/protocol rules |
| `checkpoints` (`id`, `answer_spec`, pinned source range, expected answer form) | **the checkpoint truths** — whether a checkpoint answer was correct cannot be re-derived, only re-read from a grade document produced under the same lost bytes |
| `objective`, `answer_budget`, `answer_marker` | the success contract those answers were graded against |
| manifest `fixture.wall_tokens` (e.g. `65536` on `stage1-lr01-transcript-grow-r1`) | **treatment parameter `wall_tokens`** |
| treatment config `lease_reopen_turns` | **treatment parameter `lease_reopen_turns`** — hence `lease` is `1` on 54 rows and `null` on 205, and the two are not verifiable as treatment differences |

**Per grid:**

- **G1 / `stage1`** — turn count, arm identity and 1..48 ordering are trustworthy from the rows. The run
  is still a valid *latency/usage* measurement; it is not a measurement of a known task. Its report cells
  publish **no TTFT**: `LATENCY-REPORT` records `REFUSED (n=0)` because the rows carry no `ttft_ms`, so
  the loss does not silently contaminate a published G1 latency number.
- **G2 / `smoke-rp`** — 40/40 rows lost. Only `transcript-grow` publishes a p50 (`8800.75 ms n=31`); that
  number is a real timing of an unknown task.
- **G3 / `fix-smoke`** — 27/29 rows lost; the two surviving-fixture rows are turns 11–12 of one arm, so
  the grid's 18 `transcript-grow` rows mix 10 lost-digest and 2 v1 rows. No G3 p50 is published (all
  refused for n<20), so this mix does not move a published latency figure — but it does mean G3 is not a
  single-fixture grid.

---

## 3. Published-figure dependency

Rule applied: **inputs** decide the label, no number is recomputed. `independent` = no input row pins the
lost digest; `partially-dependent` = some inputs do; `dependent` = every input row does.

| publication | figure / cell | dependency | what is affected |
|---|---|---|---|
| `docs/LATENCY-REPORT.md` | G1 all four p50/p95 | **dependent** (192/192 rows lost) | refused `n=0`, no published value; n-counts are dependent |
| | G2 `transcript-grow` p50 `8800.75 [3204.15, 10377.45] n=31` | **dependent** (31/31 lost) | the only published G2 number |
| | G2 other three arms | **dependent** (9/9 lost) | refused at n=3 |
| | G3 all four arms | **partially-dependent** (27/29 = 93.1%) | refused at n=3/3/5/18 |
| | G4–G10 (incl. the 2 published p95s in G8/G9) | **independent** | files pin `967cef03…` / v3/v4-tools/v5-tools/v6-tools survivors |
| `measure/LATENCY-REPORT.json` | same cells, machine twin | same verdicts | `grid_rule = (fixture_sha256, tools, harness era, arm)` makes the loss visible in the key |
| `measure/QUALITY-ERAS.json` | era census / `3/25` current-grader headline | **partially-dependent** | the three lost files are in its row population; per-cell share not recomputed |
| `measure/ACCURACY-RECOMPUTED.json` | `5/43` and `3/25` headlines, REC records | **partially-dependent** | it names the three lost files 14 times across its records |
| `measure/TVS-CENSORED.json` | the 3 quotable TVS events (`48 347`, `50 847`, `111 994`) | **independent** | events are `pointer-stable` v4/v4-tools/v6-tools, all surviving fixtures |
| | `n_censored = 20`, `declared_pairs = 23` | **partially-dependent** (12/23 pairs = 52.2% come from lost files) | the censoring census |
| `docs/PARM-1-ERRATA.md` | E1–E5, 12 checkpoint ids, 9+3 NONE split | **independent** | derives from `LR-01.v7.json` (`42b4df00…8392`), not from rows |
| `docs/OPERATOR-BRIEF.md` | G4 four-arm p50 table; per-arm quality; 2 published p95s | **independent** | rows are `rows-longrun-c-2026-10-26.jsonl` etc. |
| | overall quality `5/43 = 11.6%` | **partially-dependent** | its 92-cell population includes G1–G3 cells graded from lost rows |

**Note on labeling.** The latency report itself already writes G2 as `fixture v2 72c3832d` and G3 as
`MIXED v2 72c3832d(27)+b7e303a6(2)`. `FIXTURE-GENERATIONS` calls the lost bytes a **v1-lineage** variant,
not v2. The report's `v2` label is therefore a second, smaller mislabel: the digest is right, the
generation name is not. This unit records it rather than editing the published report.

---

## 4. The consequence, once, unhedged

**The operator's comparison is not affected.** The grid will run on `LR-01.v8.json`
(`0804b51575cc…`) and will be read within-grid; the arms the operator compares (the G4 four-arm p50 table,
and the G8/G9 p95s) come from surviving fixtures, so no number the operator will read is made weaker by
this loss.

**The historical record is weaker in one place.** The weakest claim in `OPERATOR-BRIEF` is the overall
quality headline **`5/43 = 11.6%`** (and its `3/25` current-grader twin): part of its graded population
ran under bytes whose task text and checkpoint truths can no longer be re-read, so the denominator is
correct as arithmetic and unverifiable as a statement about a known task. The strongest surviving
historical numbers are the G4 p50s and the G8/G9 p95s, which pin files that still hash as claimed.

---

## 5. Machine-readable register

[`measure/LOST-FIXTURE.json`](experiments/ptr-engine/measure/LOST-FIXTURE.json) carries: the full lost
digest, `recoverable: false` with the reason, all **259** row identities as `file:line`, the affected
grids/arms/turn ranges/dates, the field-level consequence, the 20 manifests whose `path` names
`b7e303a6…`, the two split rows, and the per-publication dependency table above.

---

## 6. The guard

[`longrun/experiments/ptr-engine/longrun/tests/test_lost_fixture.py`](experiments/ptr-engine/longrun/tests/test_lost_fixture.py) walks the
live rows corpus, builds the set of digests of every on-disk file carrying
`schema: consonance.longrun-fixture/1`, and fails on any row whose `fixture_sha256` has no matching file —
**forward-only**, because the 259 known misses are frozen in
[`state/logs/lost-fixture-baseline.json`](state/logs/lost-fixture-baseline.json). Existing misses pass; a
new one fails.

```
python3 -m pytest experiments/ptr-engine/longrun/tests/test_lost_fixture.py -q
```

Before (empty baseline): **259 misses**. After (frozen baseline): **0 new misses, 259 baselined**. Red
test: removing one baseline entry makes the rule fail on that row again.

The guard does **not** attempt reconstruction and does **not** treat `b7e303a6…` as the answer — that
would silently restamp 20 manifests and 259 rows.
