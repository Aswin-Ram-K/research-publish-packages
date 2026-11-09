# PROVENANCE-REFUSAL — the comparison gate in `analyze_stats.py`

**Unit:** `WIRE-PROVENANCE-INTO-STATS` · **Depends on:** `ROW-PROVENANCE` (settled, handoff `status: done`)
**Date:** 2026-10-26 · **Offline:** zero inference requests, no network, no `git` writes.

## 1. What changed and where

`ROW-PROVENANCE` published `same_provenance(cell_a, cell_b) -> (bool, [differing])` and
deliberately did not wire it: a guard nobody calls is documentation. This unit wires it into
the file where the project's headline comparisons are computed.

| surface | line (after the change) | role |
|---|---|---|
| `analyze_stats.py:require_comparable()` | `:626` | THE gate. Calls `same_provenance`; raises `IncomparableProvenance` or returns the gate record. |
| `analyze_stats.py:compare()` | `:655` (gate at `:670`) | THE only comparison entry point. Gate runs **before** `statistic` is inspected. |
| `analyze_stats.py:analyze()` | `:779` | H3 (McNemar) **and** H1 (p50/p95) cross-arm numbers both dispatched through `compare()`. |
| `analyze_stats.py:provenance_cells()` | `:715` | arm → cell, via the same `row -> manifest -> cell` ladder `row_provenance.py` uses. |
| `analyze_stats.py:main()` | `:986` | `--assume-comparable`; per-arm provenance; override visibility in stdout and `--json`. |

The import is module-scope and **not** wrapped in `try/except`: if `row_provenance` moves, the
analyser fails to import rather than silently losing its guard.

## 2. The refusal text and the fields it carries

`analyze_stats.py:144` — class `IncomparableProvenance(RefusedTest)`, kind `"incomparable_provenance"`, carrying
`.kind`, `.differing`, `.a`, `.b`. Message shape:

```
incomparable_provenance <label>: refusing to compare two cells whose load-bearing provenance
differs on fixture_sha256, tools_mode -- fixture_sha256 ('0a07…b90848' vs 'unknown'),
tools_mode ('off' vs 'unknown'). No interval and no verdict is computed. Re-run with
--assume-comparable to override LOUDLY (the artefact then records provenance_override: true
and these fields).
```

Load-bearing fields (decided by `same_provenance`, not by this module):
`fixture_sha256`, `model`, `thinking`, `tools_mode`. `arm` is **not** one of them — the arm is
what a comparison is for. `endpoint` and `max_tokens` are not either.

Unknown behaviour: an unknown is **never** evidence of agreement. `unknown` vs `unknown`
refuses. Two cells that both merely failed to name `model` are not comparable.

## 3. The override is visible in the artefact

`--assume-comparable` is the only door. There is no environment variable, no config key, no
default-on path. When used:

* stdout carries `!! PROVENANCE OVERRIDE: --assume-comparable is ON …` and every overridden
  comparison line ends with `PROVENANCE OVERRIDE (assumed comparable over <fields>)`;
* `--json` carries `provenance_override: true`, `assume_comparable: true`,
  `provenance_override_differing: [<field names>]`, and per-comparison
  `provenance_override: true` + `incomparable_provenance.differing`.

Without the flag, `--json` carries `provenance_override: false` and
`incomparable_provenance_count`.

## 4. Provenance in every report row

Every arm block prints:

```
provenance <arm>: fixture_sha256=<12-hex> model=<model> thinking=<off|auto> tools_mode=<off|on:…>
```

and every comparison prints **both** sides:

```
provenance: fixture_sha256=<12> vs <12>  thinking=<a> vs <b>  tools_mode=<a> vs <b>  model=<a> vs <b>
```

so an interval can never be read apart from the pair it was computed under.

## 5. Thresholds — unchanged, by construction

`min_n_for(0.95) = 60` (`MIN_N=20`, `TAIL_MIN=3`), McNemar's `b + c >= 6`, `RESAMPLES=10000`,
`SEED=20261020`, `LEVEL=0.95`: **not touched**. `quantile_ci` and `mcnemar_exact` are unchanged
functions; `compare()` calls them. The quantile comparison adds **no estimator**: it prints
each arm's existing interval and an overlap flag, nothing else.

## 6. Damage: the 8 within-grid comparable pairs of `LATENCY-REPORT.json`

Re-run of the existing report path, one grid per invocation (`--rows <grid file>`):

| grid | rows file | pairs | arm provenance (all arms identical) | survive | `incomparable_provenance` |
|---|---|---|---|---|---|
| G4 `RUN-C-V2` | `rows-longrun-c-2026-10-26.jsonl` | 6 | `fixture_sha256=0a07db1b14f3`, `model=occamy-1.0-NVFP4`, `thinking=off`, `tools_mode=off` | **6** | 0 |
| G5 `V3` | `rows-longrun-v3-2026-10-26.jsonl` | 1 | `fixture_sha256=07abab0bd902`, `model=occamy-1.0-NVFP4`, `thinking=off`, `tools_mode=off` | **1** | 0 |
| G6 `V4` | `rows-longrun-v4-2026-10-26.jsonl` | 1 | `fixture_sha256=5a5f8c4be202`, `model=occamy-1.0-NVFP4`, `thinking=off`, `tools_mode=off` | **1** | 0 |

**8 of 8 survive. 0 become `incomparable_provenance`.** No pair was lost, and no p50 number
moved: `0a07…` lease-reopen p50 = 134.96 ms [132.50, 136.98], pointer-stable = 167.02 ms
[163.26, 168.33], matching the `p50_a` / `p50_b` values already in `LATENCY-REPORT.json`.

What still refuses inside those grids is **pre-existing and unrelated to provenance**:
the p95 comparison at n=48 (6/6 in G4, 1/1 in V3, 1/1 in V4 — `n*(1-q)=2.4 < 3`, the 60-floor)
and McNemar at `b+c < 6` (6/6, 1/1, 1/1).

Why the pairs survive: all four arms of each grid were written into **one** rows file, and the
ladder resolves that file's manifest once, so every arm carries the same four load-bearing
values. The provenance difference between grids is real — G4 `0a07db1b14f3`, G5 `07abab0bd902`,
G6 `5a5f8c4be202`, G7 `a592a48ff3e5` + `tools_mode=on:read_file` — which is exactly why a
**cross-grid** comparison now refuses. Measured negative control:

```
analyze_stats.py --rows rows-longrun-c-2026-10-26.jsonl rows-longrun-v4-tools-2026-10-26.jsonl
  REFUSED (incomparable_provenance) … differs on fixture_sha256, tools_mode —
    fixture_sha256 ('0a07db1b14f30034902c23fe208e5717ad64856f31fe9dcfc1ab873bc2b90848' vs 'unknown'),
    tools_mode ('off' vs 'unknown')
```

## 7. `RUN-A*` — unaffected, and on what values

`RUN-A*` is the one grid in which H1 is adjudicated (`docs/PREREG-ARM-RUN.md` §3): fixture
`tasks-v5/runtime-v5/LR-01.v6.json`, served model `occamy-1.0-NVFP4`, `thinking = off`, all
four arms (`transcript-grow`, `transcript-compact`, `pointer-stable`, `lease-reopen`) in the
**same** grid with identical `fixture_sha256` and identical reasoning policy. Every load-bearing
field the gate compares is constant across those arms *by design*:

| field | RUN-A* value |
|---|---|
| `fixture_sha256` | whatever `LR-01.v6.json` hashes to at run time — one file, four arms, one hash (today: `ff89625df95d…`) |
| `model` | `occamy-1.0-NVFP4` |
| `thinking` | `off` |
| `tools_mode` | `off` (no tools declared in the H1 design; a tools grid would set `on:<csv>` for all arms equally) |

So the gate cannot bite there, **provided the four arms land in one grid written by one run**
(one manifest). Two honest caveats:

1. If the four RUN-A* arms were written into **separate** rows files whose manifests disagree on
   `tools_mode` (or anything load-bearing), the pair would refuse — and it would be right to.
2. Today's `LR-01.v6.json` hashes to `ff89625d…`, while the existing `rows-longrun-v6-tools.jsonl`
   rows record `5bf5f6393946…` (the v4 fixture bytes; "v6" there names the probe, not the fixture
   generation — confirmed by `ROW-PROVENANCE`). A future `RUN-A*` compared against those rows
   **will** refuse on `fixture_sha256`, and that refusal is the point: the fixture bytes differ.
   `RUN-A*`'s own H1/H2/H3 adjudication is not affected, because it compares its own arms to
   each other.

`RUN-A*`'s n is also unaffected: H1 still needs the 60-floor (`reps >= 2` at 48 turns = 96 raw
turns); a `reps = 1` schedule is refused by the existing `InsufficientSamples` message, not by
provenance.

## 8. A defect found in the dependency (reported, not fixed)

`row_provenance.aggregate()` reports a field on which one file's rows disagree as `"mixed"`.
`client.is_provenance_known("mixed")` is **True**, so `same_provenance` treats two `"mixed"`
cells as **agreeing**:

```
>>> client.is_provenance_known("mixed")
True
>>> same_provenance({"fixture_sha256": "mixed"}, {"fixture_sha256": "mixed"})
(False, ['model', 'thinking', 'tools_mode'])     # fixture_sha256 NOT named as differing
```

A file whose rows cannot agree with itself would therefore pass the gate. `ROW-PROVENANCE`'s
handoff states the intended behaviour ("either side 'unknown' (or file-level 'mixed') ->
(False, [...])"); the code does not implement the `"mixed"` half.

Because `client.py` / `row_provenance.py` are read-only for this unit, `analyze_stats.py`
defends locally: `cell_provenance()` maps `"mixed"` to `"unknown"`, so a cell with no single
provenance has no known provenance and refuses. **Recommended follow-up card:** teach
`client.is_provenance_known` that `"mixed"` is unknown, and add `"mixed"` to the
`same_provenance` test matrix in `experiments/ptr-engine/longrun/tests/test_row_provenance.py`. Until then, any consumer other
than `analyze_stats.py` still has the hole.

## 9. Tests — `experiments/ptr-engine/longrun/tests/test_analyze_provenance.py`

| case | asserts |
|---|---|
| (a) | cells differing in `fixture_sha256` ⇒ `IncomparableProvenance` with `.differing == ["fixture_sha256"]`, message starting `incomparable_provenance`; CLI run prints no interval on the refused line and `--json` records `incomparable_provenance` for every pair |
| (b) | differing `thinking` ⇒ same refusal, `.differing == ["thinking"]`; CLI agrees |
| (c) | differing only in `arm`, same fixture ⇒ comparison proceeds, both intervals printed, `intervals_overlap` reported |
| (d) | `--assume-comparable` proceeds **and** records `provenance_override: true` + the differing fields in stdout and in `--json` |
| (e) | the same mismatched cells refuse on the **McNemar** statistic as on the quantile statistic — the gate precedes dispatch |
| (f) | red→green: the `require_comparable` call inside `compare()` is deleted in a temp copy, and case (a)'s assertion must go RED there |

Green: `17 passed` (9 new + the 8 pre-existing `test_analyze_stats.py` cases).

Red→green, measured in place:

```
$ python3 - <<'EOF'   # replace the gate call with a fabricated pass-through gate
...

$ python3 -m pytest experiments/ptr-engine/longrun/tests/test_analyze_provenance.py -q
E       AssertionError: compare() computed a comparison across two fixtures
FAILED experiments/ptr-engine/longrun/tests/test_analyze_provenance.py::test_a_differing_fixture_refuses_and_names_the_field
FAILED experiments/ptr-engine/longrun/tests/test_analyze_provenance.py::test_a_cli_prints_no_interval_for_the_refused_comparison
... 8 failed, 1 passed

$ # restore analyze_stats.py:670
$ python3 -m pytest experiments/ptr-engine/longrun/tests/test_analyze_provenance.py experiments/ptr-engine/longrun/tests/test_analyze_stats.py -q
17 passed in 0.56s
```

The removed line is `analyze_stats.py:670-671`:

```python
    gate = require_comparable(cell_a, cell_b,
                              assume_comparable=assume_comparable, label=label)
```

## 10. Hard rules honoured

No rows file, grade file, `LATENCY-REPORT.json`, `TVS.json`, `REQUEST-LEDGER.json`, `cell.py`,
`client.py` or `row_provenance.py` was edited. No statistic added, no threshold moved, no new
default that hides a refusal. `analyze()` records a refusal and keeps reporting the rest of the
grid (one refused pair does not abort a report); `compare()` itself still **raises**, so a
caller that wants a number cannot get one.
