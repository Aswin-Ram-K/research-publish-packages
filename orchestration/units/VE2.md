# VE2 — verifier of E2 (`rep_refill-attribution`, G6)

**Status:** partial — every measurement reproduces, but the load-bearing deflation is **overstated**.
**Mode:** offline only; 0 live requests; `.occamy.lock` not acquired; 20 tool calls (bound 20).

## Verdict per check

1. **PASS — offline re-analysis.** Author `--analyse-only` re-run (with `CELL_DIR`/`ANALYSIS_PATH`
   redirected to `/tmp` so `analysis.json` was not rewritten) produced a payload **byte-identical** to
   `analysis.json` (`ALL-SAME True`, all keys, `n_rows=51`, rows sha `47980b49…`). Recomputing from
   `rows.jsonl`: t19–34 mean uncached **1658.9375** = 456.6875 new tail + 30.25 boundary + 1172.0
   re-prefill, **residual 0 on 16/16** (0 on all 37 steady turns). Printed precision 1,658.9 / 456.7 /
   30.2 / 1,172.0 matches; no drift.
2. **PASS, two precision notes.** 37/37 steady R turns have `prefix_identical=true` and
   `changed_msg_indices=[]`; 33/37 satisfy `cached == 64*floor(prompt_j/64)` for an earlier turn j
   (lag 1:7, 2:8, 3:10, 4:8), failures exactly t19,t20,t36,t37; skipped-trailing-message sum vs
   `re_prefill` max |mismatch| = **59** tokens (t11: 384 vs 443), 0/33 over 128; **81/81** `re_prefill`
   values (R/F/F2) are multiples of 64; `head_sha` is one value over all 40 R turns; `summary_shas`
   changes only at t18 (`[]→11b8…`) and t35 (`11b8…→a127…`); summary node est 188 sits before every cut
   (min cached 768).
3. **PASS.** (456.6875+1172.0)/1658.9375 = **0.98183**; 30.25/1658.9375 = **0.01823**; summary 0 →
   98.2 % tail / 1.8 % grid / 0 % summary.
4. **PASS — red→green.** Replacing `floor64(prompt_j)` with `prompt_j` gives **0/37** matches on the
   same rows, so the 33/37 identity fails without the 64-quantization. The identity is
   quantization-dependent, not incidental.
5. **FAIL — overstated.** F2 numbers are exact (t36–38 cached 2048/2048/2944, unc 455/919/450, mean 608
   = 444.33 tail + 14.33 boundary + 149.33 re-prefill; U15 F 458/922/453; R t36–40 re mean 1088; E2F
   cold cached 768/768/2048, re 1280/1728/896). But “depth is a cache-epoch property, **not** a
   fork-policy property” is not licensed (see below).
6. **PASS.** U15 R cached t19–23 = 768/768/1920/1920/2816 and t36–40 = 896/896/1792/1792/2688 match E2
   exactly (uncached −1/turn from the salt); U15 F t35–38 = 768/2048/2048/2944 match F2 exactly
   (uncached −3/turn). `client.py`, `runner.py`, `analyze.py` mtimes are 2026-10-20, before E2's
   2026-10-21 15:45–15:48 window; no `src/`, `tests/`, shared-module or other-cell write; no POST/lock.

## Check 5 adjudication — **overstated**

What the rows license: *F's shallow t36–38 reuse requires a warm pre-fold epoch; a cold-entry F run does
not reproduce it.* What they do **not** license: *the depth is epoch warmth, not the fork marker.*

- **Warm R is deep.** Same warm epoch, R re-prefill 1088 vs F2 149 (7.3×). If warmth alone set depth,
  warm R should be shallow too; the arm/policy still contributes. The fork marker is therefore not shown
  irrelevant.
- **Cold/warm differs in more than the marker.** E2F is live only from t30, so it lacks the t1–29
  request history as well as the warm prefix; no cold-R control exists. The missing history changes which
  earlier turn-end prefixes exist, i.e. the lag itself.
- **One seed per condition** (salts 2502/2503); run-to-run cache variance is unquantified.
- **“Reproduces R's depth 768/768/2048” is imprecise.** R's actual t36–38 cached are **896/896/1792**
  (unc 1385/1849/1380); E2F matches R's *deep-re-prefill magnitude* (re 1280/1728/896), not R's values.
- **F2 lag is not uniquely identified:** cached 2048 also equals `floor64(prompt_3)` and
  `floor64(prompt_18)`; turn lags vs j=35 are 1,2,1, not uniformly 1. The 149-token amount is solid.

Permitted wording: **“warm epoch necessary, arm difference still contributes — an interaction”**, not
“not the fork marker”.

## Corrections

- E2F cold (768/768/2048) is not numerically R's depth (896/896/1792) — magnitude only.
- Pre-fold turn lags are {1:7, 2:8, 3:1}: t10 is turn-lag 3; “lag 1–2 pre-fold” holds in message-skip
  units (t10 skips 2 messages), not turn units.
- “14 of 16 post-fold steady turns” covers t19–34 only; across all 21 post-fold steady turns the
  head+summary test is 17/21 (t36,t37 also short), though the summary node itself (est 188) is cached
  behind every cut (min cached 768).
- E2.md's `re_prefill` value list omits 384 and 1024 (both multiples of 64).

## Red→green

`cached == 64*floor(prompt_j)` → 33/37; `cached == prompt_j` → 0/37. The claim fails when the
quantization is removed, on the same rows.

## Containment

0 POSTs; lock never acquired. One transient `/tmp` analysis copy; a stray
`cells/E2/ve2_analysis_fresh.json.tmp` created by the first redirect was deleted — no E2 artifact content
changed (`analysis.json` sha unchanged, mtime 15:49).
