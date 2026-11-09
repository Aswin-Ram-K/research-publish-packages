# GRID-REPORT-ERA-GUARD — a pooled number cannot be printed across provenances

**Unit:** `U-GRID-ERA-GUARD` (card `059b2049`, execution `b19daa1b`) · **Target:** `experiments/ptr-engine/tools/run_grid_report.py`
**Origin:** `V-GRID-REPORT` (exec `c3280e05`) returned `emitter_unsound`. Attempt 4 ("two eras mixed, v7 vs v8") exited 0 and **printed a number it should not have**: H2 `ratio **2.5000**` and TVS `100800.0`, with `refusals=[]`.

## 1. The defect, precisely

`build_report()` clusters the included cells by declared provenance (`cluster_cells` →
`row_provenance.same_provenance` over `PROVENANCE_LOAD_BEARING = (fixture_sha256, model,
thinking, tools_mode)`) and uses those clusters for **H1 only**. H2, TVS and verbosity were
fed the *global* `included_rows` / `per_arm_all`:

```python
h2 = h2_block(included_rows, per_arm_all, paths_arm_all)          # pooled over every cell
tvs, tvs_reason = tvs_block(included_rows, ...)                   # pooled over every cell
verbosity = verbosity_block(per_arm_all, paths_arm_all)           # pooled over every cell
```

So H1 said "two grids, no interval pools across grids" while H2 summed both grids into one
mean and one ratio. Era A rows are **degeneration-confounded** (`GRID-SHAPE-TOOLS`: 46/48
turns invite a source read the tools-off runs could not satisfy); era B is the first
comparable grid. A number pooled across them is not a measurement — it is the `5/92` vs
`5/43` error again.

## 2. The fix — the gate is at the pooling layer, before any number is computed

`mixed_provenance(clusters)` decides whether the included cells may be pooled at all:

* **`len(clusters) > 1`** → not poolable (the cells disagree on a load-bearing field).
* **one cluster, but a load-bearing field is `unknown`** → not poolable. `unknown` is never
  evidence of agreement — the same rule `epochs_never_pooled` already states for grids.

When the gate closes, H2/TVS/verbosity are built as **refusals, not numbers**:

| term | pooled (agreement) | mixed (refusal) |
|---|---|---|
| H2 | per-arm means, both limbs, ratio + sign | `per_arm: []`, `comparison.verdict = refused_mixed_era`, no ratio |
| TVS | certified value | `"UNDEFINED"`, reason prefixed `refused_mixed_era:` |
| verbosity | per-arm means and `n` | `per_arm: []`, `refusal = refused_mixed_era` |

and one `refusals[]` row **per provenance present** names the era, the cells, the
introducing cell/arm and the disagreeing declared fields:

> `refused_mixed_era`: era `era_b_tools_on` grids over cells `rows-cell-pointer-stable-v7.jsonl`,
> `rows-cell-transcript-grow-v7.jsonl` (introduced by `rows-cell-pointer-stable-v7.jsonl`, arm
> `pointer-stable`) declare fixture_sha256 `7777777777777777` / fixture_id `LR-01.v7` /
> tools_mode `read_file`, which does not agree with another grid on this report — H2, TVS and
> verbosity print no mean, interval, ratio, accuracy or n

H1 is untouched: each grid still prints its own `n`, `r`, `n_eff` and interval, because those
cells *do* agree. The guard refuses **pooling**, not measuring.

## 3. What the fix reproduced

Attempt 4 rebuilt as four cells (C+A at `fixture_sha256` v7, C+A at v8, 70 turns each, all
`usable_for: [h1, h2]`). With the gate neutralised the old line returns verbatim:

```
Both limbs, C−A: cache-inclusive ratio **2.5000** (sign +1, pass=False), uncached ratio **2.7852** (sign +1, pass=False) → **h2_failed**.
```

With the gate in place:

```
**`refused_mixed_era`** — these included cells do not share one provenance, so the pooled terms H2, TVS and verbosity would sum across eras -- no mean, interval, ratio, accuracy or n is printed for them. ...
```

(the attacker's `TVS 100800.0` half is not re-derivable — their synthetic `grade_v5` document
is gone with `/tmp/vgfinal`; feeding *any* grade document to a mixed run now yields
`tvs = "UNDEFINED"` with the `refused_mixed_era` reason, which is the same gate.)

## 4. Tests

`experiments/ptr-engine/tests/test_grid_report_era_guard.py` (7 tests, synthetic tmp dirs only):

| # | case | assertion |
|---|---|---|
| 1 | two fixture versions, same tools mode | `h2.comparison.verdict == refused_mixed_era`, `h2.per_arm == []`, TVS `UNDEFINED`, verbosity `per_arm == []`, no `Both limbs` and no `tokens through turn` in the markdown |
| 2 | era A (tools off) + era B (tools on) | refuses, both era names in the refusal text |
| 3 | two single-era rows files **concatenated** on disk | refuses (the merged file's `fixture_sha256` becomes `unknown`), no ratio printed |
| 4 | one era, four cells, two arms | **still adjudicable**, `n=120` per arm, the licensed ratio still prints — the guard does not refuse everything |
| 5 | mixed input | H1 still splits into two grids and no grid inherits the other era's `n_raw` |
| 6 | refusal text | names all four cells, `fixture_sha256`, `fixture_id` `LR-01.v7`/`LR-01.v8`, era, introducing cell |
| 7 | red→green | neuter `mixed_provenance` → the pooled `Both limbs, C−A` line comes back |

Red (before the gate existed): `5 failed, 2 passed`, including
`AttributeError: <module 'run_grid_report'> has no attribute 'mixed_provenance'` and
`assert len([]) >= 2` on the refusal rows. Green (after): `7 passed`, and the pre-existing
suite `test_run_grid_report.py` is `13 passed` — no threshold moved, no other refusal lost.

## 5. Reproduce

```bash
bash -lc '/usr/bin/python3 -m pytest "/home/zer0null/reserach extarctor/experiments/ptr-engine/tests/test_grid_report_era_guard.py" "/home/zer0null/reserach extarctor/experiments/ptr-engine/tests/test_run_grid_report.py" -q'
```

## 6. Scope limits (named, not papered over)

* **H3 still reads the grade document, not the rows.** A mixed run with a grade supplied
  prints H3's `x/12` from that document. H3's population is the grader's cells, not the
  pooled rows, but if a mixed-era grade is ever supplied this needs its own guard.
* **Attempt 5 is untouched.** A grid with `n_eff < 60` still prints its arm p95 interval
  (`V-GRID-REPORT` F2). That is a different card: it is not a provenance question, and this
  card's write scope is era mixing.
* **Era identity is `era_of(tools_mode)` + the load-bearing signature.** Two grids with the
  same era label but different `fixture_sha256` are still two provenances, and are refused.
