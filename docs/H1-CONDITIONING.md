# H1 CONDITIONING — what the frozen p95 actually averages over, pre-registered

**Unit** `H1-CONDITIONING` · **dated (UTC)** `2026-10-26T17:14:00Z` · **requests: 0** ·
**rows read: 0** (none exist) · evidence [`H1-CONDITIONING.json`](../../experiments/ptr-engine/measure/H1-CONDITIONING.json) ·
guard [`test_h1_conditioning.py`](../../experiments/ptr-engine/longrun/tests/test_h1_conditioning.py) ·
inputs [`FIXTURE-TREATMENTS.json`](../../experiments/ptr-engine/measure/FIXTURE-TREATMENTS.json) (`ee91383c`).

This document fixes the *reading* of H1 **before the grid runs**. No number in it is a measurement; every
number is arithmetic over the frozen fixture's declared fire turns, or an `n`. The grid (`RUN-A*`,
~800 requests) remains held on `GATE-OPERAND-VALIDATION`; nothing here advances that.

PARM-1's frozen H1 compares `pointer-stable`'s p95 TTFT against `transcript-grow`'s, each over **all 48
turns per arm per rep**. The fixture says the four arms do not start treating the transcript at the same
turn: `pointer-stable` at **T2**, `transcript-grow` and `transcript-compact` at **T21**, `lease-reopen` at
**T23**. So the frozen statistic pools two regimes in the growth arms, and no two arms are compared at
equal treatment exposure.

## 1. The dilution arithmetic, from the fixture only

Fire turns, as declared by `FIXTURE-TREATMENTS.dry_run_turns` and re-derivable from row markers
(§5): grow **21** (`evicted>0`), compact **21** (`digest_at`), lease **23** (`lease>1`), pointer **2**
(`prefix_sha256` moves). A turn is *treated* when `turn >= first_fire_turn` — inclusive, because the
fixture's own per-rep counts are the inclusive ones (`48-21+1 = 28`, `48-23+1 = 26`, `48-2+1 = 47`).

| arm | first fire | untreated turns | treated turns | untreated frac / rep | untreated rows, 3 reps | treated rows, 3 reps |
|---|---|---|---|---|---|---|
| `transcript-grow` | **T21** | 1–20 → **20** | 21–48 → **28** | 20/48 = **0.4167** | 60 | 84 |
| `transcript-compact` | **T21** | 1–20 → **20** | 21–48 → **28** | 20/48 = **0.4167** | 60 | 84 |
| `lease-reopen` | **T23** | 1–22 → **22** | 23–48 → **26** | 22/48 = **0.4583** | 66 | 78 |
| `pointer-stable` | **T2** | 1 → **1** | 2–48 → **47** | 1/48 = **0.0208** | 3 | 141 |

So R-all's 144 rows per arm are, by arm: **84 treated + 60 untreated** (grow), **84 + 60** (compact),
**78 + 66** (lease), **141 + 3** (pointer). The comparison PARM-1 freezes is therefore *not* treated vs
treated: it is a sample that is 58 % treated against one that is 98 % treated, and the mixing ratio is
itself different between the two arms being compared.

**Why pooling is not a smoothing.** A q=0.95 order statistic is decided by the top `n·(1-q)` observations,
so the number of observations that can set the value is

```
n=48   : 48  × 0.05 = 2.4   < TAIL_MIN = 3   → per-rep p95 is INADMISSIBLE (that is why PARM-1 pools)
n=144  : 144 × 0.05 = 7.2                    → the top ~7 observations set p95   (rank span 132–142)
n=84   : 84  × 0.05 = 4.2                    → top ~4                            (rank span 77–84)
n=78   : 78  × 0.05 = 3.9                    → top ~4                            (rank span 71–78)
n=141  : 141 × 0.05 = 7.05                   → top ~7                            (rank span 130–140)
n=75   : 75  × 0.05 = 3.75                   → top ~4                            (rank span 68–75)
```

(`TAIL_MIN`, `MIN_N`, `rank_span`, `min_n_for` imported from
[`analyze_stats.py`](../../experiments/ptr-engine/longrun/analyze_stats.py:219-263); `min_n_for(0.95) = 60`.
No constant is copied here.)

The load-bearing consequence, as arithmetic rather than prose: a distribution switch at T21 moves **20 of
48** rows, i.e. **41.7 %** of the sample, out of the untreated regime and into the treated one. The p95 at
n=48 needs only **2.4** rows (`ceil`-effectively 3, rank 43–48). At n=144 the tail needs **7.2** rows, and
the untreated prefix supplies **60**. Since 60 ≫ 7.2, the tail is not *diluted* by the prefix — the prefix
can supply **100 % of the tail** whenever the untreated regime's latencies are the slower ones, and 0 % when
they are the faster ones. The mixture does not average the regimes; **it decides which regime owns the
tail**, and which one that is cannot be known before the rows exist. That is precisely why this is
pre-registration and not analysis.

A second, independent asymmetry: the four arms' treated windows do not start at the same index
(T2 / T21 / T21 / T23), so a p95 taken over turns 1–48 compares arms at **different treatment exposures**
(grow and compact: up to 28 treated turns; lease: 26; pointer: 47). Even "the same 48 turns" is not the
same treatment.

## 2. The three readings — fixed now, each fully specified

All three are callable transforms over the **same** row population: `kind == "turn"` rows with a finite
`ttft_ms` (null/absent dropped and counted, never coerced to 0 — `analyze_stats`' rule). Fields read:
`ttft_ms`, `kind`, `turn`, `arm`, and — to *verify* the fire turn in the rows rather than trust the
fixture — `evicted` / `digest_at` / `lease` / `prefix_sha256`.

| reading | status | selector (exact name, `test_h1_conditioning.py`) | population | n / rep / arm | **n at 3 reps** | clears `min_n_for(0.95)=60`? |
|---|---|---|---|---|---|---|
| **R-all** | PARM-1 frozen, primary | `select_r_all(rows, fire_turn=None)` | every completed turn | 48 | **144 all four arms** | **yes** |
| **R-post** | pre-registered secondary | `select_r_post(rows, fire_turn)` → `turn >= fire_turn` | that arm's own treated regime | 28 / 28 / 26 / 47 | **84 / 84 / 78 / 141** | **yes** |
| **R-common** | pre-registered secondary | `select_r_common(rows, fire_turn=None)` → `turn > 23` | common treated window, all arms | 25 | **75 all four arms** | **yes** |

Fire turns themselves are re-derived per arm by `infer_fire_turn(rows, arm)` (markers: `evicted`,
`digest_at`, `lease`, `prefix_sha256`), so a reading never depends on a hard-coded constant:
`select_r_post` **raises `ValueError`** if handed no derived fire turn.

Two honest limits, stated now so they cannot be discovered later as spin:

- **R-common equalises the window's index range, not exposure duration.** Turns 24–48 are treated for
  every arm, but for `pointer-stable` this throws away 22 treated turns (T2–T23) and keeps 25 of its 47;
  for `lease-reopen` it keeps 25 of 26. R-common is the reading that is *commensurable* across arms; it is
  not the reading that gives each arm equal treatment time.
- **R-post's n differ per arm** (84/84/78/141), so an R-post comparison of `pointer-stable` vs
  `transcript-grow` compares n=141 with n=84. Both clear 60; neither is the same sample size.

Only these three readings exist. Anything else — a trimmed prefix, a matched-turn pair, a
change-point estimate — is **not** registered and may not be reported as evidence for H1.

## 3. The decision rule (written before any number exists)

Frozen at `2026-10-26T17:14:00Z`, before any `rows-runA-*` file exists:

1. **R-all is the frozen claim and is reported always**, whether it separates the arms or not. It is H1.
2. **R-post and R-common are pre-registered secondary readings.** They may be reported as evidence, must
   carry their own n and intervals, and **may never be called "H1 confirmed"** — the words "H1 confirmed"
   belong to R-all alone.
3. **If R-all and R-common disagree in direction** (one puts `pointer-stable`'s p95 lower, the other
   higher), that disagreement **is itself the finding** and must be published as such, with **both**
   intervals and **both** n. It may not be resolved by preferring one reading.
4. **Forbidden:** choosing the reading after seeing the intervals; testing more than these three; dropping
   a reading because it is inconvenient; reporting any of the three without its n.

**The reading was fixed before the grid ran.** This paragraph, its timestamp, and the JSON record are the
evidence of that ordering; a later edit that reorders which reading is primary is not a clarification, it
is a different pre-registration.

## 4. The PARM-1 consequence — errata **proposal only, not applied**

If — and only if — R-common is ever to become a *claim* rather than a secondary reading, PARM-1 needs an
additive, digest-checked errata (the pattern `docs/PARM-1-ERRATA.md` set: thresholds byte-unchanged, new
claim named, frozen body hash untouched). Exact proposed text:

> ### E-H1C — a second registered H1 claim on the common treated window
>
> **Claim.** `CP-H1-COMMON`: on the common treated window `turn > 23`, `pointer-stable`'s p95 TTFT is below
> `transcript-grow`'s.
> **Statistic.** `analyze_stats.quantile_ci(values, 0.95)` on the `ttft_ms` of the selected rows; the two
> arms' 95 % intervals must be **disjoint**, the same disjointness rule PARM-1 fixes for H1.
> **Population.** `kind == "turn"`, finite `ttft_ms`, `turn > 23`, per arm per rep; 25 rows per arm per rep,
> **n = 75 per arm** at 3 reps.
> **Admissibility.** `n = 75 ≥ min_n_for(0.95) = 60`; `75 × 0.05 = 3.75 ≥ TAIL_MIN = 3`.
> **Direction.** `pointer-stable` p95 **<** `transcript-grow` p95, i.e. the same direction as H1.
> **Precedence, unchanged.** `R-all` (all 48 turns) **remains the primary H1 claim**; `CP-H1-COMMON` is
> additional, and a disagreement between them is reported as a disagreement, never resolved by preference.
> **No threshold is touched.** `n ≥ 60`, disjointness, and every PARM-1 number stay byte-identical.

**Verdict on the errata: drafted, not applied, and not yet warranted.** Reason: PARM-1 is frozen and this
unit has no rows; applying an errata now would pre-authorise a second claim before the data that would
justify it exists, and would tempt exactly the post-hoc reading switch §3 forbids. Apply it only if the
grid produces an R-all/R-common direction disagreement *and* the team decides the treated-window number is
the one to publish as a claim — at which point the text above is ready, digest-checked, and additive.

## 5. The guard that makes the pre-registration bite

`python3 -m pytest experiments/ptr-engine/longrun/tests/test_h1_conditioning.py -q` — **10 passed**, offline,
fixture-only, 0 requests. It fails if:

1. **a selector is not derivable from rows alone** — `test_selectors_read_only_row_fields` feeds rows that
   carry *only* `ROW_FIELDS` and asserts each selector's n; `test_r_post_follows_the_rows_not_a_constant`
   moves the marker from T21 to T23 and requires R-post's n to move 28 → 26;
2. **a reading's n at 3 reps is below 60 while carried as a claim** — `check_reading()` raises
   `AssertionError` for any `is_claim` reading under `min_n_for(0.95)`, and `test_pre_registered_n_at_three_reps`
   pins 144 / 84 / 78 / 141 / 75;
3. **the fixture's fire turns differ from what the rows show** — a synthetic 48-turn sample per arm
   (`synth_rows`, 6 rows per regime is enough: `test_six_rows_per_regime_is_enough`) must reproduce T21/T21/T23/T2
   via `infer_fire_turn`.

**Red→green.** `test_red_selector_ignoring_turn` substitutes the mutant
`lambda rows, fire_turn: _usable(rows)` (a selector that ignores `turn` and returns all 48 rows) and requires
`AssertionError` for every arm — 28 ≠ 48, 26 ≠ 48, 47 ≠ 48; the real selectors pass
(`test_green_real_selector`). A second mutant, `test_red_underfloor_claim`, promotes R-common to a claim at
1 rep (n=25 < 60) and requires the underfloor refusal.

## 6. What this does not decide

Plainly: **this document does not decide whether the treatment matters at all, in which direction, or
whether the grid is affordable.** It contains no latency, no interval over real data, and no verdict — only
turn arithmetic and an `n` table. It cannot say whether pooling mixes the regimes *in the direction that
flatters or penalises* any arm, because that depends on values that do not exist yet. Nor does it move the
gate: `RUN-A*` remains held on `GATE-OPERAND-VALIDATION`, the operand validation is not advanced here, and
the ~800 requests stay unspent. The only thing this pre-registration buys is that, when the rows arrive, the
reading is already on the record and cannot be chosen after the intervals are visible.

**Board line.** Does H1's frozen statistic measure the treatment or a mixture of regimes? **Undecidable from
the fixture alone** — the fixture fixes *which* turns are treated (so the mixture ratios 20/48, 20/48, 22/48,
1/48 are certain), but not whether the untreated regime is slower or faster, so it cannot say whether the
mixed tail is owned by treated or untreated rows. **R-common** is the reading that answers it, because it
restricts every arm to `turn > 23`, where all four treatments are already firing.
