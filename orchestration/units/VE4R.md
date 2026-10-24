# Unit VE4R — verification of E4R `rep3-probe`

**Status:** done (2026-10-21). **Verdict: PASS with two word-level corrections.** This unit is **not** the
author of E4R. **Scope:** offline only — 0 live requests, 0 POSTs, no `.occamy.lock` acquisition.
**Bound:** <=18 tool calls, <=15 min. **Actual:** 15 tool calls, ~9 min (16:13:42 -> ~16:22).

**Inputs read:** `AGENTS.md`; `orchestration/handoffs/{E4R,E4C,VE4}.json`; `orchestration/units/E4R.md`;
`experiments/context-cache/cells/E4R/{e4r_cell.py,e4r_rows.jsonl,e4r_report.json,e4r_run.json}`;
`cells/E4/*` (read-only, sha-pinned).

**Method:** every headline count re-derived from `e4r_rows.jsonl` with an independent predicate written in
this unit (not the author's `e4_analyze` path); sha256 checked; red->green by mutating a `/tmp` copy;
containment by mtime + pinned sha of the E4 inputs + shas of the shared modules.

## Checks

1. **PASS — rows and roles.** sha256 `05a59f28d169947fd959842ef482e07ec95fb2a96ac8405151e4aaf1920e09a7`
   == handoff. Roles `cal 8 / cold 46 / rep1 46 / rep2 40 / rep3 40` = 180 rows, all `status 200`.
   Cold `cached_tokens == 0` in **46/46**. Exact length in **46/46** trials (every row in a trial has
   `prompt_tokens == cell`). Trials: 1024x20, 1088x20, 1008x5, 1152x1. 180 rows = 8 cal probes + 172 sends
   = 180 requests (cap exactly).
2. **PASS — the load-bearing counts.** 1024: rep1 `0x20` -> rep2 `960x20` -> rep3 `960x20`. 1088: rep1
   `0x20` -> rep2 `1024x20` -> rep3 `1024x20`. Pooled rep-3: `L-64` **40/40**, `L` **0/40**, block tax 64
   **40/40** (field and recomputed `L - cached`), `rep3 == rep2` per trial **40/40**,
   `cached == 64*floor((L-1)/64)` 40/40. CP95 **[0.9119, 1.0]** = exact Clopper-Pearson `0.025**(1/40)`
   = 0.9119 (Wilson would be 0.9124; the `CP` label is correct). No flag/value mismatches; within-trial
   sha identical and salts unique per trial (46 distinct texts), so the repeats are byte-identical.
3. **PASS on values, one label correction.** Transient recovery **refuted**: 0/40 at `L` (CP95 upper
   0.0881). Worse **refuted**: no rep-3 row at 0 or `L-128` (rep-3 histograms are `{960:20, 1024:20}`).
   TTFT in the rows: rep1 231.442 / 278.87 ms, rep2 116.947 / 117.6, rep3 116.669 / 117.347, cold 232.524 /
   279.3 — the ~2x contrast is real, but the handoff's `1024_miss`/`1088_miss` values are the **rep-1**
   medians (same `cached == 0` regime), not the cold row; label only. **Label polarity defect:** the phrase
   "one-repeat lag" is used with opposite verdicts — `E4R.md:5`/`:53` use it as "recovers at rep-3" and say
   *refuted*, while `E4R.md:37` and `E4R.json one_repeat_lag_persists` use it as "incurred once at the first
   repeat, then persists" and say *confirmed*. The finding is the persistence reading (the rows support it);
   the label must be split, not the number changed.
4. **PASS — red->green.** One 1024 rep-3 flipped `960 -> 0` in a `/tmp` copy: `L-64` becomes **39/40**,
   claim predicate False, `rep3==rep2` 39/40. Flipped `960 -> L` (the transient-recovery value): eq-`L`
   becomes 1/40 and `L-64` 39/40, so "0/40 at L" also fails. Restored from the untouched file: **40/40
   True**, sha `05a59f28...` unchanged. The claim can go red.
5. **PASS — neighbours not inflated.** 1008 (mod 48), n=5: 5/5 `cached == 960` (= `64*floor(1007/64)`),
   block tax **48**, cold 0 5/5, no rep-2/3. 1152, **n=1**: cold 0, rep1 0 (full miss), no rep-2/3.
   Handoff lists `trials_per_cell` 1008:5 / 1152:1 and labels 1152 "spot check only, n=1"; the unit card
   prints n in the table and "spot check only, n=1, no rep-2/3". Neither is presented at par with n=20.
6. **RULING — "permanent" licensed only as bounded persistence.** The measured series for a multiple of 64
   is rep-1 `cached 0` (a full prefill, block tax `L`), rep-2 `L-64`, rep-3 `L-64` (40/40 each). So the
   shortfall does not decay after the first repeat, and it is not a one-repeat lag in the recovery sense.
   rep-4 is unreachable inside 180: 5 sends/trial x 40 trials = 200 > 180 (even one length alone is
   5x20 + calibration). Therefore "permanent" = "persists unchanged through repeat 3 (repeats 2-3 of 3
   measured)" — **not** "forever". Words that survive: "persistent steady-state ceiling"; "on repeat 3 it
   equals `L-64` in 40/40 boundary trials (CP95 lower 0.9119)"; "never `L` (0/40)"; "one full extra prefill
   at the first repeat"; "one-block tax on every later repeat measured". Word that must carry its scope:
   "permanent". And "(repeats 1-3)" is the measured **window**, not the tax-bearing repeats: rep-1's tax is
   `L`, the 64-tax is repeats 2-3 only. `E4R.md:57-58` already states this correctly; the JSON licensed
   sentence needs the same scope. Scope of the whole sentence: one endpoint / one model / one SGLang build,
   1024 and 1088 (both multiples, n=20 each); 1152 has rep-1 only (n=1), so there is one boundary length at
   rep-3, not two.
7. **PASS — containment.** E4R wrote only `cells/E4R/**` (6 files, mtimes 16:11:57-16:12:46),
   `units/E4R.md`, `handoffs/E4R.json`. E4 inputs are byte-identical to E4C's pinned shas
   (`e4_rows.jsonl 5f10b316...`, `e4_report.json f3a341c3...`), mtimes 15:45-15:49. Shared
   `client.py/analyze.py/runner.py` mtimes 2026-10-20 (shas recorded in the handoff). `.occamy.lock`
   mtime 16:07:58 predates E4R's 16:11:57 start, so E4R acquired `flock` without writing; one acquisition,
   `lock_wait_s 0.0` in `e4r_run.json`, `flock`/`unlock` at `e4r_cell.py:482`/`:497`. `VERDICTS.md` had
   **0** `E4R`/`VE4R` lines before this append (its 16:14:03 mtime is a concurrent unit's entry, after
   E4R finished 16:12:46). Progress JSONL goes to `$DSH_PROGRESS_DIR` (harness temp), not the workspace.

## What I could not verify
Lock held continuously across all 180 sends (no per-send acquire timestamps; only `lock_wait_s 0.0` + the
code pair); rep-4+; rep-2/3 at 1008 and 1152; the mechanism (G13, `cached_tokens` is server accounting).

## Corrections (word-level, no number changes)
- Split the "one-repeat lag" label: persistence reading confirmed (`E4R.md:37`, `E4R.json`); recovery
  reading refuted (`E4R.md:53`). Rewrite `:53` as "one-repeat lag *as recovery* is refuted".
- Scope "permanent" in the JSON licensed sentence to "persists through repeat 3 (repeats 2-3 of 3
  measured)" and read "(repeats 1-3)" as the window, tax on repeats 2-3.
- Rename `1024_miss`/`1088_miss` to `1024_rep1`/`1088_rep1` (or add the cold medians 232.524/279.3).
