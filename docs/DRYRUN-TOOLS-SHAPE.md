# DRYRUN-TOOLS-SHAPE — the tools-on launch rehearsed offline, all ten cells

**Verdict: `no_go`** — first broken item: **`harness_matches_c4541802`**. Everything else passed; nothing was sent.
**Unit:** `DRYRUN-TOOLS-SHAPE` · **Era:** tools-on v8 (era B) · **Requests:** 0 · **Network events:** 0 · **Live cells:** 0
**Measurement:** [`../experiments/ptr-engine/measure/DRYRUN-TOOLS-SHAPE.json`](../experiments/ptr-engine/measure/DRYRUN-TOOLS-SHAPE.json)
**Grid:** [`GRID-SHAPE.json`](../experiments/ptr-engine/measure/GRID-SHAPE.json) — ten cells, `tasks-v6/LR-01.v8.json`, 48 turns, `--thinking off`, H2, budget 67.

## 1. What the ten cells did

Each cell ran the driver's own recorded dry-run path:
`python3 experiments/ptr-engine/tools/run_a_star.py --cell N --tools read_file --dry-run --budget 67 --hypothesis H2 --fixture experiments/ptr-engine/longrun/tasks-v6/LR-01.v8.json`.
All ten: `rc=0`, `0 of 3 gate(s) would refuse`, `RUN-A DRY END cells=1 refused=0 requests=0`.

| cell | arm | G1 computed / limit | would_spend | G2 computed / limit | G3 | design_cap_tokens | net | rc |
|---|---|---|---|---|---|---|---|---|
| 1 | `pointer-stable` r1 | `1,173 requests` / `4,320 requests (cap 4,320 - reserve 0 - spent 1,101)` | 72 | `2880 s` / `2880 s (--max-wall)` | allow | `10616` (n=48) | 0 | 0 |
| 2 | `pointer-stable` r2 | `1,173 requests` / `4,320 requests (cap 4,320 - reserve 0 - spent 1,101)` | 72 | `2880 s` / `2880 s (--max-wall)` | allow | `10616` (n=48) | 0 | 0 |
| 3 | `pointer-stable` r3 | `1,173 requests` / `4,320 requests (cap 4,320 - reserve 0 - spent 1,101)` | 72 | `2880 s` / `2880 s (--max-wall)` | allow | `10616` (n=48) | 0 | 0 |
| 4 | `transcript-grow` r1 | `1,173 requests` / `4,320 requests (cap 4,320 - reserve 0 - spent 1,101)` | 72 | `2880 s` / `2880 s (--max-wall)` | allow | `10616` (n=48) | 0 | 0 |
| 5 | `transcript-grow` r2 | `1,173 requests` / `4,320 requests (cap 4,320 - reserve 0 - spent 1,101)` | 72 | `2880 s` / `2880 s (--max-wall)` | allow | `10616` (n=48) | 0 | 0 |
| 6 | `transcript-grow` r3 | `1,173 requests` / `4,320 requests (cap 4,320 - reserve 0 - spent 1,101)` | 72 | `2880 s` / `2880 s (--max-wall)` | allow | `10616` (n=48) | 0 | 0 |
| 7 | `transcript-compact` r1 | `1,173 requests` / `4,320 requests (cap 4,320 - reserve 0 - spent 1,101)` | 72 | `2880 s` / `2880 s (--max-wall)` | allow | `10616` (n=48) | 0 | 0 |
| 8 | `transcript-compact` r2 | `1,173 requests` / `4,320 requests (cap 4,320 - reserve 0 - spent 1,101)` | 72 | `2880 s` / `2880 s (--max-wall)` | allow | `10616` (n=48) | 0 | 0 |
| 9 | `lease-reopen` r1 | `1,173 requests` / `4,320 requests (cap 4,320 - reserve 0 - spent 1,101)` | 72 | `2880 s` / `2880 s (--max-wall)` | allow | `10616` (n=48) | 0 | 0 |
| 10 | `lease-reopen` r2 | `1,173 requests` / `4,320 requests (cap 4,320 - reserve 0 - spent 1,101)` | 72 | `2880 s` / `2880 s (--max-wall)` | allow | `10616` (n=48) | 0 | 0 |

Per cell G1 detail (cell.py's own `eval_gate_ledger`, `--fetch-followup-allowance 24`): `spent 1101 · would_spend 72 · projected 1173 · cap 4320 · headroom 4320`.

## 2. The shim — proven by execution, not by a comment

`A.ensure_shim()` (the driver's own function) wrote `/tmp/grid-shape-shim/runner_read_file.py`
(sha256 `c800706ef770fa0c`). Its whole effect is two statements:

```python
sys.argv = [REAL] + sys.argv[1:] + ["--tools", "read_file"]
runpy.run_path(REAL, run_name="__main__")
```

Executed directly against the frozen runner with `--dry-run` (no model turn, no socket). The runner argv actually observed
(at-exit capture of `sys.argv` in the shim's own process):

```
  /home/zer0null/reserach extarctor/experiments/ptr-engine/longrun/run_longrun.py
  --dry-run
  --fixture
  experiments/ptr-engine/longrun/tasks-v6/LR-01.v8.json
  --arms
  pointer-stable
  --reps
  1
  --rows
  /tmp/rows-probe.jsonl
  --turn-wall-cap
  180.0
  --runaway-turns
  2
  --thinking
  off
  --base-url
  http://192.168.2.168:8012/v1
  --claim-mode
  H2
  --tools
  read_file
```

- runner argv **contains `--tools read_file`** — yes, as the final two elements.
- runner argv **does not contain `--fetch-followup-allowance 24`**, and must not: that flag exists only in `cell.py`
  (`cell.py:1882`, G1 accounting). `run_longrun.py` has no such argument, so appending it would make argparse exit 2.
  The runner's structural pool is the constant `TOOL_FETCH_ROUNDS_PER_ARM = 24` (`run_longrun.py:2228`) — exactly what
  cell.py prices (`would_spend=72 = 48 turns + 24`). The two numbers agree by construction; the card's item 2a named the
  wrong argv.
- The runner accepted the channel: `tool_channel=read_file fetch_rounds_cap=24 (per arm) fetch_rounds_cap_per_turn=3 serve_from_prompt=True max_calls_per_turn=2 fetch_requests_in_this_preview=0 (no model turn offline)`
  and `would_send_total=48`.
- The shim does **not** move the harness pin: `HARNESS_FILES` digests `HERE/run_longrun.py` (`cell.py:128-134`), not
  `RUNNER`. It does have two benign side effects: `_runner_arms()` (`cell.py:233-243`) reads the shim and finds no `ARMS`,
  so the preflight arm-membership check silently passes; and the shim's `assert sys.argv[1:2] == ["--dry-run"] or True`
  is a tautology that asserts nothing.

**The rehearsal of record could not have shown this.** `cell.py --dry-run` returns at `cell.py:2009`, *before*
`stage_run` (`cell.py:1548`), so the driver's dry-run never launches the runner and never touches the shim. The shim had
to be executed on its own, which is what the block above is.

## 3. `harness_sha256` — CHANGED. This is the no-go.

- recorded by `GRID-SHAPE-TOOLS`: **`c4541802…`** ([`GRID-SHAPE.json`](../experiments/ptr-engine/measure/GRID-SHAPE.json), [`docs/GRID-SHAPE.md`](GRID-SHAPE.md), the ten `dryrun2-t2-*` manifests)
- observed by this rehearsal, before and after all ten cells: **`b45177379e99a05da385a956d90c12cd392322a3ec1471f3a2ce80120d5fe452`**
- moved against `TRANCH1-DRYRUN-2`'s `pins_before`: **`run_longrun.py`** (`29445320…` → `0d581d1f…`) and **`cell.py`** (`e24e867b…` → `c29a9fb3…`); `client.py`, `grade_v5.py`, `analyze_stats.py`, `det_v_verify.py` and the fixture are unchanged.
- on-disk mtimes: `run_longrun.py` `2026-10-26T18:45:18Z`, `cell.py` `2026-10-26T18:46:09Z` — both inside this unit's own window.
- `git --no-optional-locks status --porcelain` on the two: `M experiments/ptr-engine/longrun/run_longrun.py | ?? experiments/ptr-engine/longrun/cell.py`; `run_longrun.py` also carries a large
  uncommitted diff against `HEAD f17663d1fed0162a7dc3c5a0a58d372c710974c3` (`experiments/ptr-engine/longrun/run_longrun.py | 1519 +++++++++++++++++++++---- |  1 file changed, 1295 insertions(+), 224 deletions(-)`).

This unit made no edits to either file (its write paths are the five listed below). Whatever moved them, the pin the
grid was priced and labelled against no longer describes the tree the tranche would run on — and that is a STOP, not a
rehearsal detail. `design_cap_tokens` still reads **10,616** on every arm (never the top-level 3,838), so the v8 per-arm
wall is intact; it is the pin that is not.

## 4. The three gates, per cell

- **G1** `1,173 requests` — every cell: `spent 1101 · would_spend 72 · projected 1173 · cap 4320 · remaining 4320`.
- **G2** `2880 s` — every cell: `computed 2880 s vs limit 2880 s (--max-wall)`, ratio 1.0000, source `artefact-mode`.
- **G3** `allow` — every cell: `n=48 ≥ 1` for `H2`.
- **G3 still refuses H1 at n=48**: in-process `eval_gate_prereg` with `--hypothesis H1` → `ok=False`,
  `computed=n=48`, `limit=n >= 60`. The gate was not driven live and was not edited.

## 5. Zero traffic

`sitecustomize.py` + `sys.addaudithook` on `socket.*`, `urllib.*`, `http.client` around all ten driver invocations and
the shim launch: **0 network events** (only `subprocess.Popen` events, i.e. the driver's own ten `cell.py` spawns).
`unshare -n` is unavailable on this host: `unshare -n true` → **rc=1** (`unshare: unshare failed: Operation not permitted`) — recorded as a failure, not skipped.
Every cell also printed its own `0 requests sent, no endpoint contacted`.

## 6. The canary is callable

`experiments/ptr-engine/tools/tranche_canary.py` imports; `--help` → rc 0. Dry call on the **existing stopped cell's**
rows (`experiments/ptr-engine/measure/rows-cell-pointer-stable-20261026T182535Z.jsonl`, sha256 unchanged before/after) with `N=2`:
`the verdict was not called live` — result `"shape_unknown"`, trigger `no_parseable_answer`, `exit_code 2`. It is callable and it answers; its answer
on a 2-turn window is "unknown, not a pass", which is the honest verdict for that window.

## 7. One sentence

**At 8h cell 1 would have launched against a `harness_sha256` that no longer describes the tree, through a shim nobody
had ever executed — a broken append or `runpy` hop would have surfaced on the first live turn, and stop rule 7 makes
that a grid-fatal stop after one cell, with the first 48 turns of the tranche spent on a launch that could not be
trusted.**
