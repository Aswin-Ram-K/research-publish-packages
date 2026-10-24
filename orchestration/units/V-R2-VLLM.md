# V-R2-VLLM — recomputation transcript (independent verifier, not the author)

Offline, read-only on everything except the three declared outputs. **Zero live requests, no GX10, no ssh.**
Subject: `experiments/context-cache/cells/R2-VLLM-FIX/OH1/rows.jsonl` (70,271 B, 284 lines,
sha256 `895cf6d1847c0a7ba970e1c14dce862151ae732902fb17b2e98d438b57d883ec`).
Config record: `state/config/r2-vllm-fix-oh1.json` (author's record of `startup_fields`; the server's
`startup.txt` is **not** on disk). Author handoff: `orchestration/handoffs/POLL-VLLM.json`.

## 1. Claim-by-claim

| # | Author's claim | Recomputed from the raw rows | Verdict |
|---|---|---|---|
| 1 | 284 rows, 0 null `cached_tokens`, 0 non-200, sha256 `895cf6d1…3ec` | 284 rows / 70,271 B / sha256 **identical**; key present on 284/284; `http_status` 200 on 284/284; `truncated` False 284/284; `cached+uncached == prompt` 284/284 | **PASS, exact** |
| 2 | R 0.887475 [0.867459, 0.903734] / 1384.9577 [1235.2535, 1532.1690]; A 0.405844 / 1350.0141; C 0.493816 / 1158.6761; H (fourth arm) 0.360813 / 1528.1972 | hit = Σcached/Σprompt = **0.887475, 0.405844, 0.493816, 0.360813**; mean unc/turn = **1384.9577, 1350.0141, 1158.6761, 1528.1972** | **PASS, exact** (max point-estimate Δ 5×10⁻⁵ %) |
| 2b | the bootstrap 95 % CIs | endpoint-by-endpoint **not** reproduced: 14/16 endpoints differ >0.01 % (max 0.51 %, H unc lower 1366.5 vs 1359.7) | **PARTIAL** — see §5 |
| 3 | 120 rows observed `cached_tokens == 0` | **120** = A 40 + C 33 + H 42 + R 5 | **PASS, exact** |
| 4 | `--prefix-match-unit 16` changed nothing about the resolved block (`block_size 64`, resolved 2096) | resolved block 2096 is only *recorded* (no `startup.txt`); the **cache grid in the rows is 2112 = 2096 + 16**, not 2096 and not 16 | **FAIL as stated** — see §4 |

Point-estimate recomputation (`hit_sum` = Σcached/Σprompt; `hit_mean` = mean of per-turn ratios):

| arm | rows | hit (Σ/Σ) | hit (mean of ratios) | mean unc/turn | Σ prompt | Σ uncached |
|---|---|---|---|---|---|---|
| R | 71 | 0.887475 | 0.798444 | 1384.96 | 873,868 | 98,332 |
| A | 71 | 0.405844 | 0.284446 | 1350.01 | 161,323 | 95,851 |
| C | 71 | 0.493816 | 0.372008 | 1158.68 | 162,522 | 82,266 |
| H | 71 | 0.360813 | 0.255987 | 1528.20 | 169,750 | 108,502 |

## 2. Where the 120 zero-cached rows sit

The zeros are **not** scattered: they are the prefix-establishment phase at the **start of each arm**, and
its length differs by arm. There is no `turn 0` row in the file.

| arm | zero turns | count | first nonzero cached |
|---|---|---|---|
| R | 2–6 | 5 | turn 7 (2112) — turn 1 is a 432-token system-prefix hit, off the grid |
| A | 1–40 | 40 | turn 41 (2112) |
| C | 1–33 | 33 | turn 34 (2112) |
| H | 1–38, 41, 49, 57, 65 | 42 | turn 39 (2112); the four later zeros are periodic invalidations every 8 turns |

Total 120/284 = 42.3 %. The zeros with prompt length already ≥2096 (A t33–40, C t33, H t31–38 and
t41/49/57/65, R t6) prove these are **prefix-identity** misses, not short-prompt misses.

## 3. All-turn vs post-establishment ("steady") — the dilution

| arm | all hit | steady hit | all mean unc | steady mean unc | mean prompt/turn |
|---|---|---|---|---|---|
| R (steady t7–71) | 0.887475 | **0.894910** | 1384.96 | 1400.32 | 12,308.0 |
| A (steady t41–71) | 0.405844 | **0.638652** | 1350.01 | 1194.97 | 2,272.2 |
| C (steady t34–71) | 0.493816 | **0.671975** | 1158.68 | 1030.97 | 2,289.0 |
| H (steady t39–71) | 0.360813 | **0.539815** (0.611886 excl. the 4 periodic zeros) | 1528.20 | 1582.21 (1339.62 excl. periodic) | 2390.8 |

The all-turn hit for A/C/H averages 40/33/38 zero-cached turns against R's 5: A's hit rises 57 % relative
once its own establishment phase is excluded, R's by 0.8 %. **The all-turn per-arm hit is not an arm
comparison.**

**Comparator.** Prompt length is not the same task cost: R sends 5.4× the prompt tokens per turn
(12,308 vs 2,272). C's hit (0.494) is *below* R's (0.887) yet C spends **fewer** uncached tokens per turn
(1,158.7 vs 1,385.0). Hit fraction rewards a long prompt; the paper should publish **mean uncached
tokens/turn** (prefill work) as the comparator, with Σprompt as the secondary context. By that comparator
the order is C < A < R < H (1,158.7 < 1,350.0 < 1,385.0 < 1,528.2), and it is stable in steady state
(C 1,031.0 < A 1,195.0 < R 1,400.3 < H 1,582.2).

## 4. Grid: the rows say 2112 = 2096 + 16, not "16-token alignment"

- nonzero cached values: 164, distinct 12 = {432} ∪ {2112·k, k = 1…11}.
- multiples of 16: **164/164**; of 64: **163/164**; of 192: 163/164; of 2096: **0/164**; of **2112: 163/164**.
- gcd over all 164 = 48 **only because of the single 432** (R turn 1, off-grid system prefix); gcd over the
  163 on-grid values = **2112**.
- 105/164 are exactly 2112; 146/164 equal `2112·floor(L/2096)`; the 17 remaining on-grid rows lag by exactly
  one 2112-block (R t13/19/25/31/37/38/43/44/50/56/62/63/68/69; H t69/70/71) — the same one-block-lag
  signature MOE-VLLM recorded.

So the 2096 grid is gone, but its replacement observable **in this file** is 2112 = 2096 + 16 (the recorded
`mamba_block_size` is 16), not an arbitrary 16-token boundary. The pure `L − L mod 16` law belongs to the
`R2-VLLM` grid probe, a different artefact. **The 16-token unit is observable only as the +16 offset; the
battery alone cannot show 16-token granularity.**

## 5. Bootstrap

Method: 71 turns resampled with replacement, 10,000 draws, seed 20251023, percentile 2.5/97.5; hit =
Σcached/Σprompt of the resampled rows, mean unc = mean of resampled `uncached_tokens`.

Point estimates reproduce exactly (above). CI endpoints do not:

| arm | author hit CI | recomputed hit CI (fresh `default_rng(20251023)`) | author unc CI | recomputed unc CI |
|---|---|---|---|---|
| R | [0.867459, 0.903734] | [0.867999, 0.904344] | [1235.2535, 1532.1690] | [1235.3, 1530.3] |
| A | [0.329005, 0.474841] | [0.328562, 0.474775] | [1218.7465, 1480.4648] | [1222.5, 1480.2] |
| C | [0.421381, 0.556251] | [0.424078, 0.556396] | [1030.2113, 1286.7746] | [1030.0, 1285.3] |
| H | [0.282298, 0.431194] | [0.281870, 0.431450] | [1359.6620, 1699.6197] | [1366.5, 1700.4] |

No scheme tested — `default_rng` / `RandomState`, arms processed R→A→C→H and A→C→H→R, sequential or paired —
reproduces the author's endpoints exactly. Max relative endpoint deviation 0.51 % (H unc lower), 14/16
endpoints >0.01 %. The seed alone is not a reproducible specification; the author's exact resampling code
(or a digest of it) would be needed to publish 4-dp CIs.

Pooled: hit 0.718493, mean unc 1355.4613 (both exact); pooled hit CI [0.675860, 0.754692] vs author
[0.674601, 0.754672] (lower endpoint Δ 0.19 %).

## 6. Logs — absent, so the operational checks are unverified offline

`startup.txt`, `run.out.log`, `/tmp/r2oh1.log` are **not in the workspace** (`POLL-VLLM.md:4` records them as
GX10 paths). `experiments/context-cache/cells/R2-VLLM-FIX/OH1/` contains only `rows.jsonl`. Therefore:
`ARMS_IDENTICAL = 0 occurrences`, restart/mid-run errors, the warm-up before each arm, and the startup flags
are **not reproducible by this unit** (zero live requests is a hard rule).

What is on disk as corroboration (other units' records, not raw logs): `orchestration/handoffs/R2-VLLM.json:30`
records live `/metrics` `block_size="2096"`, `mamba_block_size="16"`, `prefix_match_unit="16"`;
`orchestration/handoffs/R2-VLLM-RERUN.json:76` records the launch proof `prefix_match_unit 16 / block_size 2096`.
No warm-up is evidenced anywhere: A/C/H **turn 1** returns `cached = 0`; only R turn 1 shows a 432-token hit.

## 7. Honesty audit of `POLL-VLLM.json`

**not_reproduced**
- 4-dp bootstrap CI endpoints (above); the point estimates and pooled point estimates are exact.
- `startup` fields — no `startup.txt` in the workspace; the config JSON is the author's transcript.
- `status` (STARTED / HEALTH=200 attempt=49 / DONE rc=0), `restore` (`:8012`/`:8014` probes, `StartedAt`), and
  `commands` (ssh/scp) — network claims, offline by rule.
- Pooled CI lower endpoint (0.674601 vs 0.675860).

**overstated**
- `grid`: "grid changed from 2096 to 16-token alignment" — the rows show **2112 = 2096 + 16** (163/164);
  the 16-grid is only an offset, not an observed 16-token boundary.
- `per_arm`: the hit column is an all-turn average over arm-specific establishment phases (40/33/38 vs 5 zero
  turns) and prompt lengths that differ 5.4×; at face value the arms are not comparable.
- `delta_vs_round1` CIs are this run's CIs shifted by a fixed Round-1 point (disclosed in `assumptions`), not
  a CI of the difference.

**unverified**
- `ARMS_IDENTICAL` 0 occurrences; any restart/error mid-run (no logs).
- Warm-up before each arm's first measured turn (no turn 0; A/C/H first turn cached = 0).
- Arm render semantics beyond the author's "four different policies" label (no per-arm byte map in the cell).
- 16-token granularity from *this* file (only 2112 is observable here).

## 8. Verdict

The arithmetic is honest and exactly reproducible: 284/284 rows, 0 nulls, 0 non-200, all four hit and
mean-uncached point estimates to the 6th decimal, and the 120-zero count. What does not survive is the
**interpretation**: the observable grid is 2112 = 2096 + 16 (not "16-token alignment"), the per-arm hit
comparison is diluted by arm-specific prefix-establishment phases, and hit fraction is the wrong comparator
when prompt length spans 5.4×. CIs are not reproducible from the stated seed, and the log-based operational
checks cannot be re-run offline. `overall = partial`; corrections are named in
`state/logs/v-r2-vllm-defects.json`. No paper file was edited.

## Commands run (each bounded, read-only)

```
sha256sum experiments/context-cache/cells/R2-VLLM-FIX/OH1/rows.jsonl
  -> 895cf6d1847c0a7ba970e1c14dce862151ae732902fb17b2e98d438b57d883ec
python3 - <<'PY'   # load rows; counts; per-arm hit/mean_unc/prompt; zero placement; gcd/moduli; bootstrap
PY
  -> rows 284; null 0; status {200:284}; zeros 120; gcd 48 / 2112 excl. 432; see §1–§5
python3 - <<'PY'   # 2112 law, distinct values, one-block lags
PY
  -> 163/164 multiples of 2112; distinct {432}∪{2112k}; 17 one-block lags
```
