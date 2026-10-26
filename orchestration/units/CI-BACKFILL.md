# CI-BACKFILL

**Purpose.** `state/config/best-config.json` carried `unc_ci` for O3 only; backfill O1/O2/O4 by
re-computing, from rows already on disk, the same interval O3 was measured with.

**Bound.** 15 tool calls (`used 13`). **Live requests: 0** — no GX10, no container, no `curl`.
No `ask_user_question` (automated session).

**Write paths.**
`tools/ci_backfill.py` · `state/config/best-config.json` (O1/O2/O4 `unc_ci`/`ci_source`/`ci_note`/
`ci_arm` + `evidence.ci_*` only) · `docs/serving-options/BEST-CONFIG.md` (§1 table + CI note, §5 row) ·
`orchestration/handoffs/CI-BACKFILL.json` · `orchestration/units/CI-BACKFILL.md`.

Not touched: any `hit`, `unc_per_turn`, `argv`, `config_sha256`, `n_rows`; O3's interval (verified
byte-identical by a `json.dumps(sort_keys=True)` comparison before and after the write); `papers/**`; tests.

## Step 1 — the method, quoted from `state/config/r2-vllm-fix-oh1.json`

```json
"counts": {"per_arm": {"R": {"n": 71, "hits": 66, "sum_prompt": 873868, "sum_cached": 775536,
  "hit": 0.887474996223686, "hit_ci": [0.8674588316203722, 0.9037336789165397],
  "mean_uncached": 1384.9577464788733,
  "unc_ci": [1235.2535211267605, 1532.1690140845071], ...}}}
```

That block gives the grouping (per arm), the statistic (`mean_uncached`) and the interval — but not the
estimator. **The script that produced it is not in this tree**: `orchestration/handoffs/R2-OPT-SETS.json`
says the CIs came from *"separate one-off python run against the file on disk"*. So the convention was
identified from the numbers instead of read from code:

| convention | interval re-derived from O3's own 71 R rows | residual vs on-disk |
|---|---|---|
| z (1.96·SE) | `[1238.0423627149, 1531.8731302429]` | `+2.79 / −0.30` |
| **t at df = 70 (2-sided α = 0.05)** | `[1235.4610660355, 1534.4544269223]` | `+0.21 / +2.29` |

Both residuals are small, but they bracket the on-disk value from *opposite* directions, and the t-rule
lands ~1.5% of a half-width away in each tail against the z-rule's `−0.30` undershoot on the upper bound.
t is adopted: it is also the correct small-sample rule for `n = 71`.

## Step 2/3 — `tools/ci_backfill.py`, and its stdout

```
O1	unc/turn=723.3919	unc_ci=[659.1645, 787.6193]	n=74	arms=4	excludes-0	rows=296	ea5728760540
O2	unc/turn=714.6901	unc_ci=[651.3088, 778.0715]	n=71	arms=4	excludes-0	rows=328	ca288efeea07
O4	unc/turn=2231.0282	unc_ci=[2131.7896, 2330.2668]	n=71	arms=4	excludes-0	rows=284	a606ca06a231
SELFTEST O3  n=71 mean=1384.9577464789
  ours      [1235.4610660355, 1534.4544269223]  t=1.994437
  on disk   [1235.2535211268, 1532.1690140845]
  residual  dl=+0.2075 tokens  dh=+2.2854 tokens (half-width 149.4967)
```

Filters are the card's, never widened: O1 `config_id=="S1" and budget_tokens==32768 and
phase=="battery"` → 296 rows (74/arm); O2 all rows → 328 = 4 arms × 71 battery turns **plus 44 grid
rows** (arm counts still 71 each, so the per-arm statistic is unaffected — recorded, not hidden);
O4 `config_id=="V1" and phase=="battery"` → 284 rows (71/arm).

## Step 4 — builder check

`CHECK setups identical to disk: False` — **and it was False before this card's writes, for a different
reason.** `tools/best_config_build.py` still *emits* `"unc_ci": None, "ci_source": "absent"` for O1/O2/O4
(mid-`build()`), so it can no longer agree with a backfilled file. The `hit`/`unc`/`grid`/`sha` lines it
prints are byte-identical to before; O3's block is unchanged (0-line diff). Making `--check` green again
requires editing the builder — outside this card's write paths, so it is reported, not done.

## Step 5 — doc

`docs/serving-options/BEST-CONFIG.md` §1 now carries an interval on all four rows, plus a note stating the
convention, that every interval lies strictly above zero, that **no** setup separates from its own A-arm
baseline (delta CIs straddle 0), and that no interval is degenerate.
