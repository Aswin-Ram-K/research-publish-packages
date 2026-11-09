# PROJECTION-CALIBRATION — a worst case is not a forecast

Unit `PROJECTION-CALIBRATION`. Zero inference requests: every figure below is re-derived
from row files already on disk, and every path is named.

## 1. The defect being corrected

`HARNESS-GUARDS` added a preflight projection in `experiments/ptr-engine/longrun/cell.py`:

```
projected_wall = projected_requests x --turn-wall-cap        (cap default 180 s)
refuse exit 8 when projected_wall > --max-wall              (default 3600 s)
```

Multiplying the request count by the **live abort threshold** projects the worst case, not
the expected case. Its own recorded consequence was
`projected_wall=8640s vs cap=3600s -> exit 8` for a 48-turn cell, and 10,800 s for the
operator's 60-turn comparison. A guard that refuses every real experiment gets disabled by
the next person — worse than no guard.

## 2. Measured per-turn wall — and how thin the evidence is

Measured wall is `wall_ms` (one-command cell rows) or `latency_s` (older measure rows);
rows carrying `error` are excluded, because an aborted turn is not evidence of a normal
turn. Percentiles are linear-interpolated.

### 2.1 The six live rows (thinking **auto**) — path named

`experiments/ptr-engine/measure/rows-cell-pointer-stable-20261026T145758Z.jsonl`
— **n = 6 usable rows**, thinking `auto`, `max_tokens = 4096`.

| metric | value |
|---|---|
| p50 turn wall | **129.1 s** |
| p90 turn wall | **427.7 s** |
| mean turn wall | **190.9 s** |
| Σwall / Σcompletion_tokens | **0.029 s/token** (29 ms per completion token) |

**Read this honestly:** six rows, one arm, one day, one engine. This is a set of anecdotes,
not a distribution. The p90 of six points is the fifth point — it carries no tail
information, and a two-hour runaway turn that the guard exists to catch would not appear in
it at all. It is quoted because it is the only live evidence of the thinking-on regime, not
because it is calibrated.

### 2.2 Pooled thinking on/auto

9 usable rows (the six above, `rows-pilot-thinking-2026-10-26.jsonl` n=1 thinking `on`, and
`rows-longrun-2026-10-26-fix.jsonl` n=2 thinking `auto`):

| metric | value |
|---|---|
| p50 | 218.2 s |
| p90 | 682.7 s |
| mean | 286.5 s |
| Σwall / Σcompletion_tokens | 0.0349 s/token |

### 2.3 Pooled thinking off/absent

960 usable rows across `rows-longrun-2026-10-26.jsonl` (192),
`rows-longrun-c-2026-10-26.jsonl` (192), `rows-longrun-v3-2026-10-26.jsonl` (96),
`rows-longrun-v4-2026-10-26.jsonl` (96), `rows-longrun-v4-tools-2026-10-26.jsonl` (68),
`rows-longrun-v5-tools.jsonl` (72), `rows-longrun-v6-tools.jsonl` (72),
`rows-longrun-2026-10-26-policy.jsonl` (40), `rows-equalinfo-2026-10-26.jsonl` (100),
`rows-longrun-2026-10-26-fix.jsonl` (27):

| metric | value |
|---|---|
| p50 | **2.9 s** |
| p90 | **38.1 s** |
| mean | 27.5 s |
| Σwall / Σcompletion_tokens | **0.0338 s/token** |

The wall/token ratio is stable at **~0.03 s per completion token** in every regime
(0.029–0.035 across all files). That is the physical fact behind the calibration: a
4096-token completion bound is ~0.03 × 4096 ≈ **123 s**, and a typical short turn is far
below it. The 180 s ceiling was never a per-turn expectation; it is an abort threshold.

Per-file detail (thinking off), p50 / p90 / mean in seconds:

| file | n | p50 | p90 | mean |
|---|---|---|---|---|
| `rows-longrun-2026-10-26.jsonl` | 192 | 3.6 | 3.6 | 3.4 |
| `rows-longrun-c-2026-10-26.jsonl` | 192 | 2.6 | 52.0 | 20.0 |
| `rows-longrun-v3-2026-10-26.jsonl` | 96 | 1.1 | 2.9 | 3.6 |
| `rows-longrun-v4-2026-10-26.jsonl` | 96 | 1.1 | 13.9 | 13.8 |
| `rows-longrun-v4-tools-2026-10-26.jsonl` | 68 | 2.7 | 5.5 | 4.6 |
| `rows-longrun-v5-tools.jsonl` | 72 | 1.7 | 7.3 | 5.0 |
| `rows-longrun-v6-tools.jsonl` | 72 | 2.1 | 8.0 | 5.1 |
| `rows-longrun-2026-10-26-policy.jsonl` | 40 | 345.9 | 596.4 | 332.7 |
| `rows-equalinfo-2026-10-26.jsonl` | 100 | 1.8 | 9.5 | 4.5 |

(`rows-baseline-2026-10-26.jsonl`, 105 rows, and `rows-live-2026-10-26.jsonl`, 27 rows,
carry no per-row wall field and are excluded rather than guessed at.)

**Verdict on the evidence:** the only rows that speak to the thinking-on regime are nine,
and their p90 (682.7 s) is above every ceiling in play. The calibration therefore defaults
to a deliberately conservative 60 s — above the p50 of every regime except thinking-on, far
below the 180 s abort threshold — and offers `--projected-from` for anyone who wants a
p90 from real rows of the same arm instead of a default.

## 3. What `cell.py` now does

```
projected_wall~ = projected_requests x --projected-turn-wall    (default 60 s)
                  OR projected_requests x p90(turn wall)        (--projected-from FILE)
worst_case       = projected_requests x --turn-wall-cap        (default 180 s, printed only)
refuse exit 8 when projected_wall~ > --max-wall                (default 3600 s)
```

The preflight line prints both, labelled:

```
turns=48 projected_requests=48 projected_wall~=2880s (cap-per-turn 180s -> worst case 8640s) cap=3600s projected-turn-wall=60.0s source=default
```

With `--projected-from experiments/ptr-engine/measure/rows-cell-pointer-stable-20261026T145758Z.jsonl`
the same cell projects `427.7 x 48 = 20530 s` and is refused — and the line names the file
it used (`source=p90 file=…`). `--turn-wall-cap` is untouched: `stage_run` still hands it to
`run_longrun.py`, and a live turn that reaches it is still aborted. The projection no longer
bills every turn at the abort threshold; it does not weaken the abort.

## 4. The arithmetic the decision needs

Times in seconds; `--max-wall` default 3600 s. `admitted` means `projected <= 3600`.

### 4.1 Default projection, 60 s/turn

| turns | × 60 s (projected) | × 180 s (worst case) | verdict under `--max-wall 3600` |
|---|---|---|---|
| 12 | **720** | 2 160 | **admitted** |
| 48 | **2 880** | 8 640 | **admitted** |
| 60 | **3 600** | 10 800 | **admitted** (equal to the cap, not past it) |

### 4.2 Measured p90, thinking off (38.1 s/turn; 960 rows, paths in §2.3)

| turns | × 38.1 s (projected) | × 180 s (worst case) | verdict |
|---|---|---|---|
| 12 | 457 | 2 160 | admitted |
| 48 | 1 829 | 8 640 | admitted |
| 60 | 2 286 | 10 800 | admitted |

### 4.3 Measured p90, the six live thinking-on rows (427.7 s/turn)

| turns | × 427.7 s | verdict |
|---|---|---|
| 12 | 5 132 | refused |
| 48 | 20 530 | refused |
| 60 | 25 662 | refused |

That column is the honest warning: if the thinking-on rows are representative, a 48-turn
cell needs `--max-wall` above 20 530 s and the 3600 s default is wrong for that regime —
not because the projection is too pessimistic, but because the run really is that long.

### 4.4 The two experiments on the table

| experiment | requests (serial) | projected at 60 s | projected at p90 38.1 s | projected at 180 s |
|---|---|---|---|---|
| 12-turn smoke | 12 | **720 s (12 min)** | 457 s (7.6 min) | 2 160 s |
| operator 4-arm × 60-turn × 3-rep | 720 | **43 200 s (12.0 h)** | 27 432 s (7.6 h) | 129 600 s (36 h) |

Per cell, the operator comparison is one arm at 60 turns × 3 reps = 180 requests =
**10 800 s at 60 s/turn**, which is still above the 3600 s default — as it must be, because
that cell is genuinely three hours by the calibration. The comparison is admitted per cell
by raising `--max-wall` (to ≥ 10 800 s), not by pretending the wall does not exist.

**One sentence the guard needs:** under `--max-wall 3600` the guard now admits the 12-turn
smoke (720 s) and the 48-turn cell (2 880 s) at the default 60 s projection, while still
refusing the same 48-turn cell at the 180 s worst case (8 640 s).

## 5. Tests

`experiments/ptr-engine/longrun/tests/test_projection_calibration.py` — 4/4 green, offline:

```
ok   (a) 48 turns x 60 s -> 2880 s -> admitted (calibrated default)
ok   (b) 48 turns x 180 s -> 8640 s -> exit 8 (guard intact)
ok   (c) --projected-from uses the file's p90 and names the file
ok   (d) --turn-wall-cap still aborts a live turn
4/4 projection-calibration checks passed
```

Red before the change: (a) refused with exit 8 at `projected_wall=8640s`, (b) is the
permanent red-side control (180 s is still the pre-fix arithmetic), (c) the flag did not
exist, (d) is the invariant the calibration must not weaken and passes before and after.

`experiments/ptr-engine/longrun/tests/test_guards.py` — re-run unchanged in behaviour,
6/6 GREEN. Its check (d) now asks for the old worst case explicitly
(`--projected-turn-wall 180`) and asserts `projected_wall~=8640s`, so the guard's own
exit-8 contract is pinned to the arithmetic it was written for rather than to the default.

## 6. Files

- `experiments/ptr-engine/longrun/cell.py` — `--projected-turn-wall`, `--projected-from`,
  `_p90`, `turn_walls_from_rows`, rewritten `stage_projection`.
- `experiments/ptr-engine/longrun/tests/test_projection_calibration.py` — the four checks.
- `experiments/ptr-engine/measure/PROJECTION.json` — the same measurement, machine-readable.
- `experiments/ptr-engine/longrun/tests/test_guards.py` — check (d) pinned to the 180 s
  worst case (test-only change; no guard behaviour changed).
