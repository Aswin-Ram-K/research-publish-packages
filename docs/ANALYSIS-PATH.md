# The post-grid analysis path — offline rehearsal

**Unit:** `ANALYSIS-PATH-DRYRUN` · **requests spent:** 0 · **generated:** 2026-10-26T~14:00-05:00
**Question:** rehearse the analysis that runs *after* the 10-cell / 480-turn / ≈720-request grid, on rows
that already exist, so its first real run is not on an 8-hour tranche.

`V-TRANCHE-1` passed with this disclosure: *"the post-grid analysis path (analyze() over real rows) is
exercised only on synthetic rows; its first real run is the re-run of this card."* This document is the
rehearsal. **`gap` below is a finding, not a failure of this unit — no gap was fixed here.**

## Inputs used (read-only)

| role | file | sha256 |
|---|---|---|
| era A abandoned cell (27 rows) | `measure/rows-cell-pointer-stable-20261026T182535Z.jsonl` | `46afc892480ae1dbe4b20d13fd4dacb983653a9f0a04b6a42a6283b3c55ca3b1` |
| era B shape stand-in (tools-on) | `measure/rows-longrun-v6-tools.jsonl` (72 rows, 48 turn + 24 tool-followup) | `1e78d75f259afbe0406643825941a65b4773b4342b847698005ad5908b3e531e` |
| era B shape stand-in | `measure/rows-longrun-v5-tools.jsonl` | `586b66f27939bd05e09d8b48dad745a5fa268c3f31103695746df3e3f8443cb5` |
| multi-arm stand-in (4 arms × 48) | `measure/rows-longrun-2026-10-26.jsonl` | — |
| instruments | `longrun/analyze_stats.py` `8b829ca4…`; `tools/tokens_to_verified.py` `d4cca36c…`; `tools/verify_tranche1.py` `0cf96b03…`; `measure/TVS.json` `70be4028…`; `measure/GRID-CELL-SANITY.json` `46dd6d21…`; `measure/GRID-SHAPE.json` `02cb7933…` | |

**There is no `analyze.py`.** The analysis instrument named in the unit card is `longrun/analyze_stats.py`
(the only other candidate, `longrun/analyze_longrun.py`, is an earlier long-run analyser and is not the
`analyze()` / `compare()` / `quantile_ci()` surface the grid's hypotheses run on). Named here so the
re-run does not look for a file that does not exist.

## Per-item results

| # | item | verdict | the evidence line |
|---|---|---|---|
| 1 | row selection `turn_latency_rows()` | **ok** | v6-tools 72 rows → **48 selected**, `dropped_followup=24`, `mode=fallback-turn`, zero `tool-followup` rows in the selection; multi-arm file 192 rows → 192, **n per arm = {transcript-grow 48, transcript-compact 48, pointer-stable 48, lease-reopen 48}** |
| 2 | p95 refusal at n=48 | **refuses_as_designed** | `refusing p95 at n=48: the 95% order-statistic span is ranks 43-48 (p89.6-p100.0) and n*(1-q)=2.4 < 3; minimum n for p95 is 60`; forced n=96 (two in-memory reps of the stand-in) → **p95 = 355.11 ms, n=96, [252.48, 416.60]**, rank span 88-96 |
| 3 | provenance refusal era A vs era B | **refuses_as_designed** | `incomparable_provenance eraA-vs-eraB: … differs on fixture_sha256, model, tools_mode … No interval and no verdict is computed.` (`0804b515…` vs `5bf5f639…`; `occamy-1.0-NVFP4` vs `unknown`; `off` vs `unknown`); `compare(statistic="quantile")` raised the same gate **before** looking at the statistic |
| 4 | `usable_for: []` exclusion | **gap** | `usable_for` appears in **no analyser**: the only `.py` producer is `tests/test_grid_cell_sanity.py:499` (`cell["usable_for"] = usable`), and the only readers are that test's own assertions (`:535-536`) and `docs/GRID-CELL-SANITY.md`. `analyze_stats.py --rows measure/rows-cell-pointer-stable-20261026T182535Z.jsonl` computed `ttft_p50 n=27 141.58ms [131.35, 166.38]` and `accuracy = 1/4` on the exact cell `GRID-CELL-SANITY` lists in `must_not_enter_analysis`, exit 0 |
| 5 | tv s / censoring | **gap** (censoring limb **ok**) | ok: `rows-longrun-v4-tools` → `tvs.turn=12, tokens=50847, requests_counted=12, cached_share=0.8807`; `rows-longrun-v3` → **`tvs: null, reason: "no_verified_success"`** (a censoring statement, never a mean, rule `TVS_CENSOR_AS_ZERO=False`). gap: TVS accepted a grade whose own `rows_file` is `measure/rows-longrun-v4-tools-2026-10-26.jsonl` while `--rows` was `rows-longrun-v6-tools.jsonl` and returned **`tvs.tokens=111994, requests_counted=20`** beside only `code_state.mid_cell_code_change=true` — no provenance refusal |
| 6 | H3 over 12 ids, 3 NONE flagged | **ok** | synthetic 12-id grade (labelled exercise): `x_of_12=8`, `x_of_9_substantive=6`, `none_passes=2`, `checkpoint_loss=3`, `mcnemar={discordant:6, floor:6, b:3, c:3, p:1.0, licensed:true}`; below the floor: `refusing McNemar: only 2 discordant pairs, below the frozen floor of 6`; direct `mcnemar_exact` at b=1,c=3 → `only 4 discordant pairs (b=1, c=3), and b+c < 6; the exact two-sided p is 0.62500 and the smallest attainable p at 4 discordant pairs is 0.12500` |
| 7 | the one-command path | **gap** | `grade_v5.py --fixture …/tasks-v6/LR-01.v8.json` exits **1** with `FileNotFoundError: 'experiments/ptr-engine/ptr_engine/resolve.py'` when run from `experiments/ptr-engine/`, and exits **0** from the repo root — the grade step is **cwd-sensitive**; `analyze_stats.py` exits 0 but would not exclude item 4's cells |

**7 items: 3 `ok` (#1, #6 and the censoring limb of #5), 2 `refuses_as_designed` (#2, #3), 3 `gap`
(#4, #5, #7).** #5 is `gap` because the item asks for the TVS path as a whole — its censoring limb passed
and its grade-identity limb did not; #1 is `ok` with the compound-case caveat stated below.

> **Dated caveat (2026-10-26) — `LATENCY-FIGURE-HONESTY`, item 4's `ttft_p50 n=27 141.58ms [131.35, 166.38]`:** `experiments/ptr-engine/measure/GRID-CELL-SANITY.json` stamps this cell `usable_for: []` (reason: *"cell in progress: 27/48 turns on disk — a statistic computed now would be from a truncated cell file"*); the 60-turn census that consumed that stamp is `orchestration/handoffs/TURN-CENSUS-60.json` (unit `TURN-CENSUS-60`): **0 of 15** rows files and **0 of 15** arm-by-file rows reach 60 usable turns, the largest is **48**, so `n=27` gives `27 x 0.05 = 1.35 < TAIL_MIN = 3` and no p95 can exist here.
>
> Rows file this figure was computed on: `experiments/ptr-engine/measure/rows-cell-pointer-stable-20261026T182535Z.jsonl`, sha256 `46afc892480ae1dbe4b20d13fd4dacb983653a9f0a04b6a42a6283b3c55ca3b1` (`wc -l` = 27).
>
> **What the number may still be used for:** nothing pooled and nothing comparative — it is one cell's legacy `kind='turn'` p50 (`definition_fallback: true`, see `docs/LATENCY-FALLBACK.md`), quoted only with its `n` and never beside another cell's value.

## The three gaps and their smallest repairs

**G1 — `usable_for: []` has no consumer (item 4).** `GRID-CELL-SANITY` writes `usable_for` and
`usable_reason` into `measure/GRID-CELL-SANITY.json` (`verdict.analysable_today: []`,
`must_not_enter_analysis: [both era A cells]`), and the grid card says "exclude by name". **Nothing at
analysis time reads that mark**; the only consumer is the test that wrote it. So a re-run that globs
`measure/rows-cell-*.jsonl` will silently pool an excluded cell — as the rehearsal just did, with exit 0.
*Smallest repair:* two halves, ~15 lines total, no threshold touched.
(a) have the cell writer stamp `usable_for` / `usable_reason` into its own
`longrun/manifests/<cell>.json` (the grid already writes per-cell manifests, so no new file class);
(b) in `analyze_stats.main()`, before selecting rows, read that manifest and, when `usable_for == []`,
print the cell by name and skip it — refused unless `--include-unusable` is passed. A sidecar read of
`measure/GRID-CELL-SANITY.json` is an acceptable cheaper variant, but it makes the analysis depend on a
*test* artefact, which is why the manifest is the smaller long-run repair.

**G2 — TVS trusts a foreign grade file (item 5).** `tokens_to_verified.py` reads `--grade` without checking
`grade["rows_file"]`, so a grade produced for one cell yields a number for another. `verify_tranche1.py`
already builds exactly the map that would catch this (`:240-264`, *"measure/cell-*.grade-v5.json ->
{rows_file basename: path}"*). *Smallest repair:* ~10 lines in `tokens_to_verified.py` — compare
`os.path.basename(grade.get("rows_file"))` to `os.path.basename(args.rows)` and refuse with a named reason
unless `--allow-foreign-grade` is passed.

**G3 — the grade step is cwd-sensitive (item 7).** The fixture's `src_path` values are repo-root-relative
(`experiments/ptr-engine/ptr_engine/resolve.py`), and `det_verify.parse_module` opens them as given. From
`experiments/ptr-engine/` the whole grade run dies on the first source file. *Smallest repair:* resolve
`src_path` against the repository root (`Path(__file__).resolve().parents[2]`) at the point
`grade_v5._tree_for` receives it — 2-3 lines — or, if the artefact is not to be edited, make
"run every command from the repo root" a hard precondition of the runbook below (it is written that way).

## The exact post-grid commands (`V-TRANCHE-1-RERUN`)

All paths repo-root-relative; **run every one from the repo root** (G3).

```bash
# 0. the grid itself (unchanged: one command per cell, as GRID-SHAPE.json:cells[].command)
python3 experiments/ptr-engine/tools/run_a_star.py --cell <N> --tools read_file --budget 67 \
        --hypothesis H2 --fixture experiments/ptr-engine/longrun/tasks-v6/LR-01.v8.json
# 1. grade each cell with the instrument of record (PER CELL; --out is the artefact)
python3 experiments/ptr-engine/longrun/grade_v5.py \
        --rows experiments/ptr-engine/measure/rows-cell-<CELL>.jsonl \
        --fixture experiments/ptr-engine/longrun/tasks-v6/LR-01.v8.json \
        --out experiments/ptr-engine/measure/cell-<CELL>.grade-v5.json
# 2. re-derive the analysability mark (writer = the sanity test; nothing else produces it)
python3 -m pytest experiments/ptr-engine/tests/test_grid_cell_sanity.py -q
# 3. the analysis (H1 p50/p95, H2, H3) — read the grade, do NOT pool across fixtures
python3 experiments/ptr-engine/longrun/analyze_stats.py \
        --rows experiments/ptr-engine/measure/rows-cell-<CELL>.jsonl \
        --grade experiments/ptr-engine/measure/cell-<CELL>.grade-v5.json \
        --json experiments/ptr-engine/measure/ANALYSIS-<...>.json
# 4. the H3 gate + TVS per arm on the declared grid
python3 experiments/ptr-engine/tools/verify_tranche1.py --check          # threshold drift first
python3 experiments/ptr-engine/tools/verify_tranche1.py --out experiments/ptr-engine/measure/TRANCHE-1.json
# 5. TVS over one cell (never --all across a mixed grid without G2 fixed)
python3 experiments/ptr-engine/tools/tokens_to_verified.py \
        --rows experiments/ptr-engine/measure/rows-cell-<CELL>.jsonl \
        --grade experiments/ptr-engine/measure/cell-<CELL>.grade-v5.json --arm <ARM>
```

Runnability **as measured today**, without editing anything:

| step | runnable? | how it was measured |
|---|---|---|
| 0 cell run | yes (dry-run gates already reported 0 requests) | `GRID-SHAPE.json` `dry_run_gates` |
| 1 grade_v5 | **yes, from the repo root only** — exit 0; exit 1 from `experiments/ptr-engine/` | ran both cwds on v6-tools rows |
| 2 sanity writer | yes (it is a pytest module; it rewrites `GRID-CELL-SANITY.json`) | read `tests/test_grid_cell_sanity.py:498-536` |
| 3 analyze_stats | yes — exit 0, but **will not exclude** G1's cells | ran on era A cell |
| 4 verify_tranche1 | not exercised within this unit's bound (`--check` and `--out` not run here) | — |
| 5 TVS | yes — exit 0, but **no `--rows`/grade identity check** (G2) | ran v4-tools and v6-tools |

## The shape limits of this rehearsal (stated, not hidden)

- No rows file on disk carries **both** multiple arms and `tool-followup` rows: the follow-up exclusion is
  proven on a single-arm tools-on file (v6-tools) and the per-arm count on a 4-arm tools-off file. The
  selector keys turns by `(_arm_of(row), rep, key)`, so the two properties compose — but the *compound*
  case is unproven until the grid's own tools-on cells exist. This is why item 1 is `ok` **with this
  caveat**, not proof.
- Item 3's refusal names three differing fields, not one: the v6-tools stand-in rows carry
  `model="unknown"` / `tools_mode="unknown"`. The grid's era caveat needs the `fixture_sha256` limb; that
  limb is proven, the *isolation* of it is not, because the stand-in is not provenance-stamped.
- Item 6 is exercised on a **synthetic, in-memory** grade (no row file written, per the write-path
  restriction), because no on-disk grade has 12 graded cells per arm with a licensed McNemar.
- Not exercised: `verify_tranche1.py --check/--out`, `tokens_to_verified.py --all`, H2's cache limbs.

## If the grid finished tonight, what fails first

**`grade_v5.py` fails first — with `FileNotFoundError: 'experiments/ptr-engine/ptr_engine/resolve.py'` if
the re-run starts anywhere but the repo root — and if it is started correctly, the first substantive
failure is the grade itself: on the era-B stand-in rows 11 of 12 checkpoints come back `undecidable`
(`prose_only` / `unparseable`), so `H3_MIN_DECIDABLE=8` is missed (decidable=1) and H3 is
`not_adjudicable` no matter how many requests the grid spent.**
