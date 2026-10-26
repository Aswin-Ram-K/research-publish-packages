# W3-COLLECT — G0 gate, the 284-row battery and the grid probe for dense 9B on SGLang

**Status:** done. Offline analysis takes **0 requests**; the live phase took **328** of a 400 cap.

## Why this unit exists

`W3-LAUNCH` brought the dense 9B up on SGLang at `192.168.2.168:8017` (container `gx10-w3-dense9b`,
context **32768**, `--mem-fraction-static 0.08`) but collected nothing from it. The frozen
`DENSE-SGL` cell was launched at **context 65536 / mem-fraction 0.22**, so its 64k arm cannot be
reproduced on this instance. This unit collects the **32k band only** — the shared 2x2 schedule
(4 arms × 71 servable turns = **284 rows**) plus the grid/probe geometry — on the *measured*
launch, in its own directory, leaving `DENSE-SGL/rows.jsonl` untouched.

## Hard bound

400 requests. Spent: gate 2 + grid 30 + probe 12 + battery 284 = **328**; 72 headroom unused.
One lock (`.occamy.lock`) per phase, `lock_wait_s` 0.0 for every phase.

## G0 gate — why it is a gate and not a courtesy

`cached_tokens` lives inside `usage.prompt_tokens_details`. `meter.normalise_cache` maps **both**
`prompt_tokens_details: null` and a genuinely cold request to `0`, so an absent key is
indistinguishable from a cache miss *downstream*. The gate therefore requires the key to be
**present in the server's own usage object**, and every row in this cell stores `usage_raw`
verbatim plus `usage_source` (`prompt_tokens_details` / `usage.cached_tokens` / `absent`).

Measured: rep0 `prompt_tokens_details: null` (cold, 0), rep1 `{"cached_tokens": 3072}` on
`prompt_tokens 3131`. Key present → gate open. **0/328 rows have a missing usage object.**

## Headline numbers (32k band, all 4 arms)

| arm | rows | hit | uncached/turn | warm (turn≥5) |
|---|---:|---:|---:|---:|
| R summarise_in_place | 71 | 0.958773 | 702.27 | 697.45 |
| A append_note | 71 | 0.958038 | 714.69 | 710.73 |
| C none | 71 | 0.957410 | 725.31 | 722.10 |
| H hybrid | 71 | 0.958095 | 713.69 | 709.73 |
| **all** | **284** | **0.958079** | **713.99** | — |

Max depth reached **32,470** tokens; **1** cold turn per arm (turn 1, `cached_tokens` 0 by
construction); 70/71 turns hit.

**Against the frozen DENSE-SGL 32k band** (same schedule, same seeds, different launch):
mean_L identical at **17,031.74**, hit **0.958079 vs 0.956941**, unc/turn **713.99 vs 733.37**.

> **Do not print that as "19.4 tokens cheaper".** The per-turn delta is bimodal
> (turn 2: 461, turn 3: 957, turn 4: 521, turn 5: 958 …) — an even/odd rotation of ~450 / ~950
> with median **861** — so the arithmetic mean of that rotation is **not a stable statistic** and
> the 19.4-token difference is not attributable to the launch. Report "same band, same hit rate
> to 3 dp" and stop. The cause of the rotation is **unassigned** (newly open, §"Open").

## Cache geometry

- Hot `cached_tokens`: gcd **64**; **0** values not a multiple of 64; **92/280** odd multiples of
  64; **67.14 %** multiples of 128 — the same picture as the frozen cell (0.321 / 67.86 %).
- **Grid law holds exactly**: `cached(L) = L − (L mod 64)` on **all** 15 hot targets
  (L 72/76/71/129/130/131/193/194/195/257/258/259/513/514/515); every cold rep **0**.
- **Discrimination probe** (WIN-SGL's L 1102/1166/1230/1294): cached **1088/1152/1216/1280** —
  8/8 hot probe rows match the 64-law, **4/4 discriminating targets match 64, 0 match 128**.

## Open (must not be smoothed over)

1. **The ~450/~950 alternation** in per-turn uncached tokens, median 861, identical in shape
   across all four arms and present in the frozen cell too. Not explained by any row here.
2. **64k band not collected** — the instance serves `max_model_len 32768`; a 64k arm needs a
   restart at a larger fraction, and `WIN-SGL` measured that the production occamy container is
   the only thing that can be displaced for that. Operator decision, not taken here.

## Assumptions (recorded, per the no-questions rule)

1. Endpoint `192.168.2.168:8017` only, never `127.0.0.1` — enforced in code (`assert_port`).
2. 32k band is the deliverable because it is the only band the live instance can serve; the card's
   "284-row battery" matches 4×71 at budget 32768.
3. Grid targets: 13 boundary lengths (63…513) + the 4 WIN-SGL probe targets × 3 reps.
4. `config_id` is recorded as **P2** with a descriptive `config_sha256`, so these rows can never be
   pooled with `P1` (the frozen 65536-context launch) by a consumer that groups on config.
5. A duplicated `phase/arm/turn` key is refused by the runner, not silently appended.

## Deviation to disclose

A bootstrap run (04:26–04:30Z) wrote **284 rows** — 6 gate/grid, a grid phase that had not
finished, and **278 battery rows** — before a `SIGTERM`-like truncation: its exit code was **2**
with no exception printed, and rows are fsynced one at a time, so all 278 landed. The battery,
grid and gate phases were then **re-run from scratch** (grid made incremental first), and the
aborted rows are archived at
`experiments/context-cache/cells/W3-COLLECT-ABORT-bootstrap/rows.jsonl`. **No row in
`W3-COLLECT/rows.jsonl` comes from the aborted attempt**; the 3 first-failed gate rows from the
port/path bootstrap (no usage object, 404) are in that archive too.

## Teardown

`docker rm -f gx10-w3-dense9b` (exit 0); port 8017 has no listener. `gx10-occamy-nvfp4`
(StartedAt 04:07:15Z, user unit `active`) and `gx10-qwen9b` (StartedAt 03:44:19Z) are both
**running**, `/health` 200 on 8012 and 8014 — neither was stopped or restarted at any point.

## Files

`run_w3collect.py` (phases) · `w3collect_cell.py` (lock, raw-usage writer) ·
`analyze_w3collect.py` (offline) · `rows.jsonl` (328) · `analysis.json` ·
`logs/gate.json` `logs/grid-summary.json` `logs/probe-summary.json` `logs/battery-summary.json`
`logs/battery-plan-32768.json` `logs/battery-run.log` · `state/config/W3-COLLECT-{pre,post}.json`
