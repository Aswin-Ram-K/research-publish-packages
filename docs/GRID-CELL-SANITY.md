# GRID-CELL-SANITY — can a cell be analysed at all?

**Unit:** `GRID-CELL-SANITY` · **Scope:** the grid cells `RUN-A*` has put on disk
(`ad214412-c39c-4a47-afb1-2be328e03b1e`), plus every other `rows-cell-*.jsonl` in
`experiments/ptr-engine/measure/` · **Cost:** 0 inference requests, 0 network calls.

This report answers one question and refuses the next one. It says whether a cell's rows are
*structurally analysable* — attributable, attributed, stamped, guarded. It does **not** say what
the cell measured: no accuracy, no token comparison, no TTFT/tvs figure is computed here. That is
`V-TRANCHE-1`'s job and pre-empting it would contaminate it.

Machine-readable twin: [`GRID-CELL-SANITY.json`](../experiments/ptr-engine/measure/GRID-CELL-SANITY.json).

## Cells found on disk

| cell | scope | turns on disk | declared n | state | sha256 (snapshot) |
|---|---|---|---|---|---|
| `rows-cell-pointer-stable-20261026T182535Z.jsonl` | RUN-A* | 27 | 48 | **in progress** | `46afc892480ae1db…` |
| `rows-cell-pointer-stable-20261026T145758Z.jsonl` | pre-RUN-A* | 6 | — | legacy fragment | `5ac9dd992f5d8715…` |

The RUN-A* cell was still growing while this audit ran (10 → 14 → 20 → 26 → 27 rows observed).
Its `sha256` in the JSON is therefore a **snapshot**, flagged in the artefact by
`sha256_is_snapshot: true`; `turns_on_disk` moves until turn 48 lands. No partially flushed line
was seen — every line parsed — but the skip path is implemented and tested
(`test_partial_last_line_is_skipped`).

The pre-RUN-A* file is a six-row fragment from the v6-era schema: it carries no `claim`,
`fixture_id`, `model`, `endpoint`, `stop_reason` or `request_sha256`. It cannot be checked against
these seven rules at all, so each check is reported `not_applicable` with the measurement retained
(`schema_verdict` keeps what the naive read would have said). **It must never enter any analysis.**

## The seven checks

Verdicts below are for the RUN-A* cell at the emit snapshot (27/48 turns).

### 1. Row model — `pass`

26/27 turns each carry exactly one row, `kind="turn"`, and every one of them is the turn's initial
measurement (`row_measurement_source="turn-initial"`, `definition_fallback_turns=26`). Distinct
`request_sha256` (27) equals rows (27), `send_index` is `0` on every row and no digest value is
reused across turns. This cell ran with **no tool follow-ups**, so *sends == turns* trivially; the
`k+1 rows / k+1 sends / k distinct requests` case is exercised by the red test below, not by this
cell.

### 2. Provenance — `pass`

Every row carries all nine fields: `arm=pointer-stable`, `model=occamy-1.0-NVFP4`,
`endpoint=http://192.168.2.168:8012/v1`, `fixture_id=LR-01.v8-treatments-reachable`,
`harness_sha256=c45418022a6a818b…`, `max_tokens=4096`, `thinking=off`, `tools_mode=off`.
`fixture_sha256` is the **v8** value `0804b51575cce3454a1c628a9a2447a01856321e67ac3fd1ff8c9baa48467641`.
No v7/v5 digest appears in any v8-era cell, so there is **no STOP-level provenance finding** here.
(The digest is the runner's arm-variant digest, `fixture_id` is the v8 fixture; they agree.)

### 3. Claim stamp — `pass`

`claim=H2` and `comparison_eligible=true` on all rows, matching the `.claim.json` twin
(`mode=hypothesis`, `resolver=claim_mode.resolve_claim`, n=48 from `p4-001.gates.json` G3).
A `claim=none` cell has a refusal path in the analyser and a red test: it is never pooled.

### 4. Cache attribution — `pass`

`cached_tokens` is present on **27/27** rows, `token_source` is
`usage.prompt_tokens;usage.prompt_tokens_details.cached_tokens` on 27/27, and
`cached_source=prompt_tokens_details`, `engine=sglang`. Rows where `cached_tokens is None`: **0**.
This is the vLLM-`prompt_tokens_details` path and it is live, not a genuine absence.

### 5. Stop reasons — `pass`, with one flagged truncation

Census at the final rescan: `stop` 25, `length` 1, `runaway_turn` 1, `unknown` 0 — all values inside `client.STOP_REASONS` (10 values, parsed offline from `experiments/ptr-engine/longrun/client.py:105`). The `runaway_turn` row is turn 27: wall_ms=115331.241, failed_turn=True, timing_usable=False — the runner's own runaway guard fired and recorded the exclusion in the row, exactly as check 7 requires.

The `length` row is **turn 3**: `max_tokens=4096`, `completion_tokens=4096`, `content_tokens=3999`,
`truncated=true` — a genuine truncation, not a finish-token artefact. It is **recorded as excluded
in the row itself** (`failed_turn=true`, `timing_usable=false`), so downstream analyses drop it by
reading the row, not by re-reading a log. That is the shape `RECORD-STOP-REASON` exists to give:
this was a `group by`, not an archaeological dig.

### 6. Treatments — `not_applicable`, and this is the one real gap

`pointer-stable` has **no row-level treatment marker**. The treatment is the frozen index prefix,
computed as `prefix_sha256` in `run_longrun.py:1125-1126` and **never written to a row**: the row
carries `evicted` (grow's marker), `digest_at`/`kind="digest"` (compact's) and `lease`
(lease-reopen's) but not `prefix_sha256`. So this cell cannot prove from its own rows that the arm's
treatment fired. `evicted` is 0, `digest_at` is null, `lease` is null — all correct for this arm,
all useless as evidence *for* it.

What can be said: 27/27 rows have `cached_tokens > 0`, and the value plateaus at 4736 from turn 6
onwards, which is consistent with a live stable prefix — but consistency is not proof, and this
unit does not upgrade a proxy into a verdict. **`pointer-stable` cells are unfalsifiable about their
own treatment from rows alone; the runner should stamp `prefix_sha256` on the row.** Until then any
claim that "pointer-stable's treatment fired" rests on the fixture and the runner source, not on
the cell.

For the other three arms the predicate is decided from rows alone (`evicted>0`, `kind=="digest"`
or `digest_at`, `lease>=2`), and a zero count over the full horizon is a `fail` that forces
`usable_for: []` — with a red test proving the analyser reports it.

### 7. Wall guardrails — `pass`

Max `wall_ms` = **115,331.241** (the runaway turn), under the 180,000 ms cap; 0 turns over cap. Turn-3 exclusion is recorded in the row (`timing_usable=false`, `failed_turn=true`), not
only in a log. p50 `wall_ms` at the snapshot = **2,454.212** — reported because check 7 asks for it
explicitly; it is a guardrail descriptor for a runaway turn, not an outcome statistic, and nothing
else in this artefact is a central-tendency figure.

## Verdict

`usable_for: []` for both cells on disk, for two different reasons:

* the RUN-A* cell is **incomplete** (27/48) — pooling it now would pool a truncated cell, so the
  conservative call is to wait for turn 48 and re-run `python tests/test_grid_cell_sanity.py --emit`;
* the pre-RUN-A* fragment is **out of scope and schema-incapable** — it must never enter any
  analysis.

So: **not every cell on disk is analysable today.** The RUN-A* cell is clean on six of seven checks
and merely unfinished — it becomes `usable_for: [h1_pooled, h2, h3]` the moment it completes and
still passes; the six-row legacy fragment must not enter any analysis, ever.

## Read-only proof

`GRID-CELL-SANITY.json` carries `read_only_proof`: every file the audit read — `client.py`, both row
files, the gates twin, the claim twin, `ARM-TREATMENTS.json`, the fixture — hashed before and after
the analysis pass in the same process, with `unchanged: true` and identical `before`/`after` digests.
No row, grade, manifest, gate file, `cell.py`, `run_longrun.py`, `PARM-1*` or fixture was written.

## Tests

`python3 -m unittest tests.test_grid_cell_sanity` — 7 tests, all green. The red cases feed
hand-made cells that must be refused:

| test | what it feeds | expected |
|---|---|---|
| `test_red_duplicate_request_sha256` | two turns sharing one `request_sha256` | `row_model: fail`, `usable_for: []` |
| `test_red_zero_treatment_marker` | `transcript-grow` with `evicted=0` throughout | `treatments: fail`, `usable_for: []` |
| `test_red_v8_era_cell_with_v7_sha` | v8 `fixture_id`, non-v8 digest | `provenance: fail`, `stop_level: true` |
| `test_red_length_row_not_excluded` | `length` row without an exclusion flag | `stop_reasons: fail` (and `pass` once flagged) |
| `test_claim_none_is_refused` | `claim="none"` | `claim_stamp: fail`, `usable_for: []` |
| `test_partial_last_line_is_skipped` | a half-flushed final line | line skipped, turn counted |

Reproduce the artefact: `python3 tests/test_grid_cell_sanity.py --emit`.
