# VERSIONS.md — the SYS-OPT version log and the pre-registered ceiling rule

**Status:** **PRE-REGISTRATION ONLY.** This file is opened *before* any SYS-OPT cell exists. The
numbers that will fill it belong to card **`SYS-OPT`** (`733058c8`), which writes V1–V3 here. This unit
(`PRE-REG-SYSOPT`) writes the rule and nothing else: no rows, no scores, no verdict.

**Canonical sources.** Spec of record: `docs/PLAN.md`. Release shape, round protocol and change menu:
card `SYS-OPT` (`733058c8`). Thesis and the C0 baseline: card `FINAL-GOAL` (`a2b5ff2d`). Engine lever:
`papers/context-cache/CLAIMS.md` row **C63**.

---

## 0. PRE-REGISTRATION (written before any SYS-OPT measurement)

**This rule was written at `2026-10-24T08:40:15Z` (`date -u`), with zero SYS-OPT measurements on
disk** — `docs/prompt-system/` did not exist, `experiments/context-cache/cells/SYS-OPT/` did not exist,
no `state/sys-opt-*.json` existed, and no SYS-OPT row of any kind existed anywhere in this workspace.
The empty-state listing is recorded verbatim in `orchestration/handoffs/PRE-REG-SYSOPT.json`
(`evidence.empty_state`). The rule therefore cannot have been fitted to a result: there was none.

The freeze order is also the precedence order. If a later reading of this file suggests the thresholds
were chosen "after seeing the numbers", the timestamp in
`orchestration/handoffs/PRE-REG-SYSOPT.json` and the absence of any SYS-OPT cell before it are the
counter-evidence.

### 0.1 What this file deliberately does not contain

- No SYS-OPT rows, no per-arm means, no CIs, no quality rates, no verdict.
- No V0 values: the V0 pairing is *defined* in §9 but *filled in* by SYS-OPT from `R2-PROMPT` before
  round 1, because only that card may read the R2-PROMPT result as its baseline.
- No change to the thresholds in this file. They are copied from the SYS-OPT card, not re-derived:
  improvement needs **Δunc/turn CI excluding zero** and **hit gain ≥ 2.0 pp** on **both** models;
  regression fires at a **quality mismatch rise > 1.0 pp** on either model.

### 0.2 Measured anchors this rule must not contradict (context, not SYS-OPT data)

These are prior measurements quoted from the SYS-OPT card. They are **not** re-derived here, **not**
SYS-OPT rows, and not evidence for any version. They are recorded so that a later SYS-OPT number which
contradicts them is caught rather than absorbed.

| Anchor | Value (uncached tokens/turn) | Provenance |
|---|---|---|
| `PROMPT-O1` arm **A** | **529.2958** | `orchestration/handoffs/PROMPT-O1.json` (O1 setup, SGLang, occamy-1.0) |
| `PROMPT-O1` arm **C** | **547.0845** | same |
| `PROMPT-O1` arm **R** | **583.1408** | same |
| `PROMPT-O1` arm **H** | **961.9718** | same |
| `PROMPT-O1` arm **C0** | **709.8592** | same |
| `PROMPT-O2-EXTRA` arm **R** | **600.169**, with **A − R = −71.3** | `orchestration/handoffs/FIX-O2-CONFIG.json`, `orchestration/handoffs/CLAIM-HEALTH.json` |

Two standing caveats, recorded so no SYS-OPT round leans on them:

1. `PROMPT-O1`'s A/C/H/C0 arms were never re-run on a fresh salt; A = 529.2958 rests on the restored
   rows alone (see `orchestration/handoffs/ARMS-PARITY-WITHDRAW2.json`). Treat it as an anchor, not a
   reference measurement.
2. One sibling cell's R-arm reading is withdrawn as unexplained and is **not** usable as a reference
   (same handoff). If SYS-OPT's R/P0-family number sits far below 529–583, the instrument is suspect
   before the version is.

Any SYS-OPT number that lands wildly outside these ranges is an **instrument question first**, a
finding second. That ordering is pre-registered here so it cannot be reversed after the fact.

---

## 1. Scoring

### 1.1 Unit of observation

One row = one turn × one arm × one model, as produced by the SYS-OPT round protocol (§7). A row is
usable only if it carries `model`, `arm`, `turn`, `version`, `prompt_tokens`, `cached_tokens`,
`http_status` and `prefix_sha256`. Two integrity rules, both learned from the instrument:

- **`http_status != 200` is invalid**, not a miss. The row is excluded and counted; the arm is short.
- **`cached_tokens` absent or `null` is an instrument failure, not a hit and not a miss.** With the
  serving flag unset the key is absent, and it is never fabricated as `0` (see
  `orchestration/handoffs/R2-VLLM-DOCCHECK.json`). Such a row is excluded and counted. A zero that was
  *measured* (`cached_tokens == 0`) is a real miss and stays.

Per row: `unc = prompt_tokens − cached_tokens`; `hit = cached_tokens / prompt_tokens`.

### 1.2 Per model, per version

Each version is run through the same four tests P0–P3 (frozen from `R2-PROMPT`, unchanged all rounds)
at 71 turns each. Report, **per model**:

- **mean uncached tokens/turn**: per-arm mean over the 71 turns, then the unweighted mean of the four
  arm means (**version headline**); every per-arm mean is also printed;
- **hit fraction**: per-turn `cached/prompt`, averaged over turns, then unweighted over the four arms.
  The token-weighted pooled fraction is printed as a *diagnostic only*; it is never decisive;
- **95 % bootstrap CI over turns**: 10,000 resamples of the 71 turn indices, fixed seed `20261024`,
  percentile interval. Within a resample the four arms are read on the *same* resampled turn set
  (paired by turn), so the version headline and its CI agree in weighting;
- **quality mismatch rate**: 20 fixed questions per model, each asked in **P0 form and P1 form**
  (40 probes). A probe mismatches when the frozen programmatic grader marks it wrong. The question set
  and expected-answer keys are frozen by SYS-OPT in `state/sys-opt-quality.json` **before round 1**,
  with their sha256 recorded; the same set and grader are used for every version and both models.
  Report `mismatches / 40`, plus the two per-form rates.

If any arm has fewer than 71 usable rows on either model, the round is `invalid_round` (§7) and
produces no version judgement.

### 1.3 The C0 reference

`C0` = plain chat-style transcript (system prompt + verbatim conversation, no pointer index, no
structure, no placement policy). It is carried **per model per round**, 71 turns, scored by the same
estimator. C0 rows are **additional** to the 568 scored rows and C0 is **never** a version. The release
claim is **V_n / C0 on both models**, with V_n/C0 per model reported in `SYS-OPT-RESULTS.md`;
V_n/V0 is the internal comparison, not the headline.

---

## 2. IMPROVEMENT(v, v−1)

Sign convention: a cost improvement is a **negative** Δunc and a **positive** hit gain. A version is
said to improve on its predecessor **only if, on each model independently, both hold**:

1. **Δunc/turn = headline(v) − headline(v−1)**, computed as a paired bootstrap over turns (per-turn
   difference within each arm, then arm-averaged per resample), has a 95 % CI that **excludes zero**;
2. **hit gain = hit(v) − hit(v−1) ≥ 2.0 percentage points** (point estimate; the card attaches the CI
   requirement to Δunc, and this file does not move it to the hit term).

Outcomes, computed per model and then combined:

| per-model result | combined status |
|---|---|
| improves on **both** models | `improved_both` |
| improves on **exactly one** model | `one_sided` (§3) |
| improves on **neither** model | `no_signal` (§4) |

The per-model conditions are **not** pooled and not averaged: a model that fails condition 1 or 2 fails,
whatever the other model did. A version that improves cost on both models but fails the quality guard
is discarded, not adopted (§5).

---

## 3. ONE_SIDED

An improvement on exactly one model is **recorded, NOT adopted**.

- Status in `state/sys-opt-verdict.json`: `one_sided`, with the winning model, the failing model, both
  models' Δunc CIs and hit gains.
- The version is **not** added to the release chain and **not** published as "the version". It is a
  finding about the system, not a version of it: the design requirement is one prompt artefact plus a
  per-model serving config that works on **MoE and dense**.
- It may motivate a change in the next round **only if** a fixable cause is named (§4).

---

## 4. CEILING

A round **declares the ceiling** when it returns either:

- `no_signal` — neither model meets both IMPROVEMENT conditions; or
- `one_sided` **with no fixable cause named**.

"A fixable cause named" is a written entry, made **before** the next round's changes are chosen, that
names (a) one lever from the change menu (§8) and (b) a measured row-level basis **on the failing
model** that the lever would act on. Naming a cause that only exists on the winning model, or naming a
lever with no measured basis, does not count.

On a ceiling the search **stops**:

- do not spend a spare round chasing noise — the round budget is three, and a ceiling at round 1 or 2 is
  the rule working, not a failure;
- publish the **best version** = the latest version adopted into the release chain (§2), or **V0** if
  none was adopted;
- write `closed_at_ceiling: true` and `ceiling_round: <n>` into `state/sys-opt-verdict.json`;
- record the ceiling line in `docs/prompt-system/SYS-OPT-RESULTS.md`;
- no further SYS-OPT round may run on this lineage without a `DECISIONS` entry naming the measured
  lever and the remaining headroom (`FINAL-GOAL` reopening rule).

**Terminal condition if no version is ever adopted.** If all three rounds are `no_signal`,
`one_sided`, or `discarded` (§5), the verdict still publishes V0 as the best version and sets
`closed_at_ceiling: true` with `ceiling_round` = the last round executed. The search closed at its
ceiling; that outcome is pre-registered here so it cannot later be presented as "no result".

---

## 5. REGRESSION

A **quality mismatch rise > 1.0 pp on either model** (pooled over the 40 probes, versus the same
model's predecessor in the chain) **discards that round regardless of cost**.

- The round is recorded `discarded: quality_regression`, with both models' before/after rates and the
  probe-level diff, in `state/sys-opt-<v>.json` and in `SYS-OPT-RESULTS.md`.
- The version is **not** added to the release chain, however good its Δunc and hit gain.
- The discarded round is **not** a `no_signal` result: it decides nothing about the ceiling, and the
  remaining round(s) continue.
- A cost improvement and a quality regression in the same round are reported together; the cost number
  is not deleted, it is marked non-adoptable.

The guard runs on both models; a quality regression on one model discards the round even if the other
model is clean, for the same reason ONE_SIDED is not adopted: the release must work on both.

---

## 6. HEADROOM

Headroom may be claimed **only** when both hold:

1. the version improved on **both** models (§2), and
2. a **named unused lever** remains — a change-menu lever (§8) with a measured basis for expecting it
   to act on **both** models.

Headroom is a **reporting claim**, not a fourth round: the round budget stays at three. A release with
no named unused lever is reported as "no headroom claimed", not as "ceiling" unless §4 fired.

---

## 7. ROUND PROTOCOL (identical every round, so versions compare like with like)

Per round, **one card execution** — never three rounds in one turn:

- **2 models × 4 arms P0/P1/P2/P3 × 71 turns at 32768 = 568 scored rows.** Warm each arm before its
  measured turns.
- **Same prompt bytes on both models.** Assert byte-identity of the rendered prompt for every
  (arm, turn) pair and record both models' `prefix_sha256`; a mismatch is `invalid_round`, not a
  finding. Only `serving.moe` / `serving.dense` may differ.
- **`version` in every row**, in addition to the standard keys. One version per round: V1, V2, V3.
- **C0 carried per model per round** (71 × 2 = **142 reference rows**, additional to the 568), scored
  by §1.3. The headline release claim is V_n/C0 on both models.
- **20-question quality guard per model, in P0 and P1 form** (§1.2), same frozen set and grader every
  round.
- **Serving config per model** from `state/config/best-config.json`: MoE uses whichever of O1/O3 won,
  dense whichever of O2/O4 won; if the 9B never starts on SGLang, dense uses O4 and the handoff must
  say so. `config_id` and `config_sha256` are recorded per model per round.
- **Restores proven each round** before the round is called complete: `:8012` 200 with `occamy-1.0`,
  `max_model_len 131072`, the six baseline keys; `:8014` restored if it was touched.
- **`invalid_round`**: fewer than 71 usable rows on an arm/model, a prompt-byte mismatch, or an
  instrument failure (§1.1). It is reported as a failed execution, produces no version judgement, and
  may be re-run only inside the card's 90-tool-call / 1,800-request bound. It does not count as a
  version and does not consume a version number.

Per-round writes (SYS-OPT card): `experiments/context-cache/cells/SYS-OPT/**`,
`state/sys-opt-<v>.json`, `state/sys-opt-verdict.json`, `docs/prompt-system/SYS-OPT-RESULTS.md`,
`orchestration/handoffs/SYS-OPT*.json`. No `papers/**`, no `RUN.json`, no test edits, no edits to
`cells/R2-PROMPT/**`.

---

## 8. CHANGE MENU

At most **two changes per round**, each **traceable to a measured finding**. The six levers (from the
SYS-OPT card):

1. **Pointer index density** — fields, summary length, entry cap.
2. **Tail placement** — grid padding, 1 vs 2 blocks.
3. **Scaffold order / anchor marker.**
4. **Delta batching** — per-turn vs every *k*.
5. **Retrieval-hint wording.**
6. **Serving-side levers already proven in `R2-OPT-LOOP` only** — nothing else from the serving stack.

Traceability entry required for each change, written before the round runs:

| field | content |
|---|---|
| lever | 1–6 |
| measured finding | the cell + row digest + figure the change is derived from |
| prediction | expected direction of Δunc and hit, **and on which model** |
| falsification | what result would count as the prediction failing |

A change with no cited measured finding is **not allowed** in the round. A change whose prediction is
not observed is recorded as **falsified** in `SYS-OPT-RESULTS.md`, not silently dropped from the next
round's description. The same lever may not be "retried" without a new measured finding.

---

## 9. V0 definition

**V0 = the best-scoring arm + P2 pairing from `R2-PROMPT`, per model**, recorded separately per model
so rounds compare like with like (the MoE and dense pairings may differ; if they do, both are stated).
V0 has **no SYS-OPT measurement of its own**: its numbers are `R2-PROMPT`'s, cited with that provenance
and its row digests, never re-labelled as SYS-OPT rows. SYS-OPT fills V0 in **before round 1**, and the
fill is recorded in `docs/prompt-system/VERSIONS.md` and `state/sys-opt-v1.json` (as the v−1 baseline)
so the round-1 comparison is checkable.

This section is deliberately blank of values: writing them here would require reading the R2-PROMPT
result, which is SYS-OPT's job and would put a post-measurement number inside the pre-registration.

---

## 10. What would make us withdraw this rule

**One condition:** an independent verifier — not this unit, and not the unit that ran the round —
**proves a measurement error in the scoring pipeline itself**: rows that do not re-derive from their
pinned row files, `cached_tokens`/`prompt_tokens` accounting that does not reproduce, prompt bytes that
were not actually identical across models, or a quality grade that the frozen grader does not reproduce.

Only then may the rule be amended after round 1, and only in its **measurement** part. The decision
structure and its thresholds (CI-excludes-zero, 2.0 pp, 1.0 pp, one_sided-not-adopted, ceiling
semantics) are **not** amendable: they are the thing being protected.

An amendment is recorded as a dated block appended to this file, carrying the verifier's handoff path,
the sha256 of the affected rows, the exact text replaced, and the reason. **No amendment may
retroactively convert a recorded `no_signal` or `one_sided` into an adoption**, and no amendment may
add a round. A disappointing result, a better-looking arm, or a preference for a version is **not** a
condition for withdrawal; if those were enough, this file would not exist.

---

## 11. Freeze record

| | |
|---|---|
| written | `2026-10-24T08:40:15Z` (`date -u`, measured by `PRE-REG-SYSOPT`) |
| SYS-OPT cells on disk at that time | **none** (`experiments/context-cache/cells/SYS-OPT/` absent) |
| `state/sys-opt-*.json` on disk at that time | **none** |
| `docs/prompt-system/` before this file | **did not exist** |
| live requests used by this unit | **0** (no GX10, no model start, no network) |
| empty-state listing | `orchestration/handoffs/PRE-REG-SYSOPT.json` → `evidence.empty_state` |

**SYS-OPT writes V1–V3 into this file, below this line, in round order. It does not edit §0–§10.**

---

## Amendment A1 — 2026-10-24: tail policy, P2 withdrawal, V0 fill

**Appended, not edited in.** §11 freezes §§0–11 and forbids SYS-OPT from editing them; that freeze is the
evidentiary value of §0, so §§0–11 stay byte-identical to the frozen text and this amendment lives below
the line. Amended here are **card-level parameters only** — tail policy, candidate arm set, the lever-2
entry, and the §9 V0 *fill*. **Not amended, binding as written:** §§1–5 (scoring, IMPROVEMENT,
ONE_SIDED, CEILING, REGRESSION) — the CI-excludes-zero bar, the 2.0 pp hit bar, the 1.0 pp quality bar,
the three-round budget, and §1.3's C0 requirement (its disposition this round is A1.4).

**Authority, and its limit.** Operator instruction, 2026-10-24, received in this card's first turn, before
any SYS-OPT row existed (`experiments/context-cache/cells/SYS-OPT/` absent; no `state/sys-opt-*.json` on
disk). It is measurement-backed, but it is **not** a §10 amendment: §10 requires an *independent verifier*
to prove a measurement error, and no verifier has re-derived `P2-REPAD` yet. It is therefore recorded as
**provisional** (A1.7.3), and no ceiling or adoption decision may be drawn from it.

### A1.1 `tail_policy.pad_to = "none"` — grid padding is withdrawn

Measured on production occamy (`:8012`, SGLang, occamy-1.0) with the pad **precomputed** from the same-run
P1 row so each turn is sent once — `cells/P2-REPAD/rows.jsonl`, **213 rows**, sha256
`1e55300788daf62c01376486beee5f1174b2dc8c8c53b60d0b8900a8131a5f44`, `requests_sent == 1` on
**213/213**, `corrections_total 0`, 0 non-200:

| arm | n | unc/turn | bootstrap CI95 | hit |
|---|---|---|---|---|
| P0 (whole resend) | 71 | **541.0704** | [500.718, 581.704] | 0.9561 |
| P1 (pointer + append-only) | 70 numeric (+1 cold `unavailable`) | **528.6429** | [521.143, 536.271] | 0.7705 |
| P2 (P1 + grid pad) | 70 numeric (+1 cold `unavailable`) | **549.4857** | [542.171, 556.800] | 0.7704 |

Deltas: **P1/P0 −14.3429 [−57.429, +26.957] → NULL**; **P2/P0 +6.5000 [−35.457, +45.971] → NULL**;
**P2/P1 +20.8429 [+9.857, +31.486] → costs**. The cell verdict field is `padding_costs`; note that it rests
on **P2/P1**, not on P2/P0, which is null — "P2 costs +6.50 vs P0" is a point estimate whose CI covers
zero, and it must not be quoted as an established cost against P0.

Mechanism: pad paid **94.8873** tokens/turn, extra cached vs P1 **74.0571** (distribution 0×9 / +64×41 /
+128×20) → ~22 % of the pad recovered, ~78 % paid (net +20.84). Grid padding buys at most one 64-token page
per turn and pays 64–127 tokens for it.

**The earlier apparent win was a same-turn self-hit artefact, and it is withdrawn.** In `O3-P2-REPEAT`
(`cells/R2-PROMPT/O3-REPEAT/rows.jsonl`, 213 rows, sha256
`042c4fd57fa5aff8602e243dee9ea4b3a84ac226897055961c0274cef540881d`, 291 requests) **68/71** P2 rows were
the *second* send of a same-turn alignment correction (**70/71** in the original O3 cell), and the row
records only the corrected send, whose `cached_tokens` is the first send's prompt. The −51.5 % (and its
replication at −69.9 %) is **not a padding effect** and must not be cited.

**No per-turn steady-state saving is licensed by this amendment.** The padding result is a cost; what
justifies the pointer layout is the branch-sharing result (A1.3), not a per-turn saving.

### A1.2 P2 is withdrawn as a candidate arm

`P2` is not run in any round of this lineage. It is not "retried later": §8 forbids retrying a lever without
a new measured finding, and A1.5 removes the lever itself.

### A1.3 V0 = P1, per model (the §9 fill)

Recorded separately per model, as §9 requires. Reason string, verbatim:
`"P2 withdrawn (padding_costs); P1 null-vs-P0 but is the layout required by the branch-sharing result"`.

| model | setup | `config_sha256` | V0 = P1 unc/turn | t-CI95 | hit | rows sha256 |
|---|---|---|---|---|---|---|
| MoE `occamy-1.0` | **O1** SGLang `:8012` (production) | `f2efaaac1559ebc0a706c5012715dacff6948058ee8e5c946d5d45c622880c67` | **522.71831** | [506.07, 539.37] | 0.770148 | `8d71a88f22310d59f6e63a1d43a0d6ed009c3dfe48de14d50f7a3d942c71db55` |
| dense `qwen3.5-9b` | **O2** SGLang `:8017` | `652ff99db16fb7fc90e2649955bf74dbcda4586ee1e13704290cf2b0bc9ab510` | **522.71831** | [506.07, 539.37] | 0.770148 | `1b8268d5b70f237cd68531033f1be716f92841b108a053ac333300411879197a` |

Provenance: `state/r2-prompt-matrix.json` (`cells.O1.arms.P1`, `cells.O2.arms.P1`), substrate
`state/config/best-config.json` sha256 `c5d11074c2a0d1ffe8a5a44e32380747e24dd2927517b8681eacc30a0b39c38d`.
The two values are **identical by construction, not by copying**: O1 and O2 share the qwen3 tokenizer and
both cache at page 64 (`R2-PROMPT-RESULTS.md` finding 6), so the dense number is a **replication** of the
MoE number and must never be presented as independent evidence about cache geometry.

Justifications that may be cited for the pointer layout — and no per-turn claim beyond them:

- **fan-out**: B/A **6.7443 [4.0454, 9.4432]** (A 20,328 vs B 123,256 uncached tokens; 8 fan-outs,
  64 branches) — `state/serving-brief.json` S08 / `recompute.py` C53.
- **plain chat**: C0−R **+126.7184** — `PROMPT-O1` arms C0 709.8592 / R 583.1408 (operator-quoted CI
  [47.9, 205.4]; **not reproduced** from the pins under the recorded recipes — see A1.6).
- **mid-edit control**: H−R **+378.8310** — `PROMPT-O1` arms H 961.9718 / R 583.1408 (operator-quoted CI
  [191.7, 514.9]; likewise not reproduced — A1.6).

### A1.4 Round arms: P0, P1, P3 — C0 not wired, not carried

§7's census becomes **2 models × 3 arms × 71 turns = 426 scored rows** (from 568). C0: §1.3 requires it
per model per round, but the round harness does not carry it — `cells/R2-PROMPT/prompt_r2prompt_cell.py:62`
is `ARMS = ("P0", "P1", "P2", "P3")` and the file contains **no** C0 arm; C0 exists only in the `R2-P1`
five-arm cell harness (R/A/C/H/C0). The operator's clause "C0 if already wired" therefore resolves to
**not carried**. Recorded deviation: a `V_n / C0` headline is **unavailable** on SYS-OPT rows, and the
C0−R anchor above is a `PROMPT-O1` reference, never a SYS-OPT row.

### A1.5 Change menu — lever 2 loses "grid padding"

Effective menu for every round of this lineage: (1) pointer index density — fields, summary length, entry
cap; (2) tail placement — **1 vs 2 trailing blocks only**; (3) scaffold order / anchor marker; (4) delta
batching; (5) retrieval-hint wording; (6) serving-side levers already proven in `R2-OPT-LOOP` only. Grid
padding is struck, not "available but discouraged".

### A1.6 Row-level corrections — the rows win

| instruction's value | pinned value | what happened |
|---|---|---|
| P1 521.20 unc/turn | **528.6429** | 521.143 is P1's bootstrap CI **lower bound**, not its mean |
| P2 541.75 unc/turn | **549.4857** | 541.75 is `R2-PROMPT`'s original O1 P2 — the value this amendment retires |
| P1/P0 −14.34 [−57.4, +27.0] | −14.3429 [−57.429, +26.957] | reproduces |
| P2/P0 +6.50 | +6.5000 [−35.457, +45.971] | reproduces |
| P2/P1 +20.84 | +20.8429 [+9.857, +31.486] | reproduces |

The two absolute means are the load-bearing error: quoting 541.75 would restore the withdrawn artefact
value, and quoting 521.20 would understate V0 by 7.4 tokens/turn on the MoE. The four deltas stand.

The two quoted CI bounds in A1.3 do **not** reproduce here: from `PROMPT-O1`'s 71 turns, a percentile
bootstrap (10,000 resamples, seed `20261020`, paired by turn) gives C0−R [61.99, 191.32] and H−R
[172.17, 608.39]; a paired t(70) interval gives [59.75, 193.69] and [155.26, 602.40]. The point estimates
reproduce exactly. Until a verifier pins the recipe behind [47.9, 205.4] and [191.7, 514.9], those bounds
are **operator-stated, not re-derived**, and the *point* estimates are what may be cited.

### A1.7 Round 1 is blocked on A1.7.1–.3 (all recorded before any live request)

1. **Estimator.** §1.2 defines the version headline as the *unweighted mean of the four arm means*. P2 is
   gone and V0 is a single arm, so `IMPROVEMENT(V1, V0)` is not like-for-like as written. Two defensible
   mappings, both measurement-part changes that need an explicit record: headline = **P1 arm only**
   (like-for-like with V0), or headline = **unweighted mean of the three measured arms** (literal §1.2
   minus P2). **Pending operator decision** — the choice moves every reported number, and the ceiling test
   reads that number.
2. **V1's change.** §§7–8 allow at most two changes per round, each traceable to a measured finding and
   written *before* the round runs. None is named yet. A round with no change is not a version; a round
   with an invented change is not allowed (§8).
3. **Quality set.** `state/sys-opt-quality.json` does not exist; §1.2 freezes the 20 questions, the answer
   keys and the grader, with their sha256, before round 1.
4. **Verifier.** §10's condition for amending the measurement part is unmet (A1, authority).
5. **C0.** A1.4.

**Live requests used by this amendment: 0. Lock not acquired. No SYS-OPT cell exists.**

---

## Amendment A2 — `2026-10-24T11:53:53Z`: §1.2 headline resolved, V1's change, quality set frozen

Appended below the freeze line for the same reason as A1: §11 forbids editing §§0–11, so §§0–11 stay
byte-identical and every round-level decision lives here. Written **before the first SYS-OPT row**:
`experiments/context-cache/cells/SYS-OPT/rows-moe.jsonl` and `rows-dense.jsonl` did not exist at this
timestamp, and no SYS-OPT request had been sent.

This amendment resolves A1.7.1 and fills A1.7.2–.3. It does **not** touch the pre-registered decision
structure (CI-excludes-zero, 2.0 pp, 1.0 pp, one_sided-not-adopted, ceiling semantics), which binds.

### A2.1 §1.2 — the version headline is the **P1 arm alone, per model** (A1.7.1, answered)

The round-1 driver resolved A1.7.1 from measured evidence, not preference:

- V0 is a **single arm** (§9 as filled by A1.3: V0 = P1), so an arm-mean headline would compare one
  arm of V0 against three arms of V1 — not like-for-like;
- `P2` is **withdrawn** (A1.2), so "the four arm means" no longer exists;
- `P3` is a **mid-edit negative control** (one earlier index line rewritten at turn 40). Averaging a
  control into the headline would report the control as part of the product.

Therefore: **headline = P1 arm mean, per model.** P0 and P3 are reported beside it as references and
are **never** averaged into the headline or into any delta. `IMPROVEMENT(v, v−1)` is computed on the P1
mean against P1's predecessor value, per model, exactly as §2 requires.

### A2.2 §8 traceability — V1's one change: **lever 1, pointer index density**

| field | content |
|---|---|
| change | `pointer_block.quote_tokens: 0 → 40` — every pointer index entry gains a 40-token verbatim head of its span (`cells/SYS-OPT/sysopt_r1.py`, `QUOTE_CHARS = 160` at the observed ~4 chars/token) |
| measured finding | `cells/R2-PROMPT/O3-REPEAT/quality.json` (sha256 `a4623b11e05dbfeadd460ed99f48d5cf2c2c2a48204fdf6909b0d3d2d59a3f9f`): **20/20** questions show a first-32-token mismatch between the P0 and P1 forms on O1 (same 20/20 in the O3 cell). The mechanism is answer **form**: P0 quotes span text (`fact[003] …`), P1 states length + `sha8` (`1196 … 471d8e55`) — **the hashes verify** (t003 → `471d8e55` reproduces), so this is not degradation; the fixable part is the missing quotable text |
| prediction | P1-form quality mismatch falls **≥ 20 pp on both models** (the index now carries the span head the question asks for), with Δunc/turn no worse than **+45** tokens/turn |
| falsification | **revert** if the P1-form mismatch falls **< 10 pp** on either model, or if Δunc/turn **rises above +45** on either model. Recorded as falsified in `SYS-OPT-R1B-RESULTS.md`, not silently dropped |

No other change this round: `tail_policy.pad_to = "none"` (A1.1), one trailing block, scaffold order and
anchor marker unchanged, delta batching per-turn, retrieval-hint wording unchanged, and **no serving
lever touched** (lever 6 unused).

### A2.3 §1.2 quality set — frozen, with digests

`state/sys-opt-quality.json`, **file sha256 `57b043cb1a4fafc6830390ed1779b7f1a1b5491578f9354d89272ebc4b854c0b`**,
content sha256 `8b21b3562d78acd1abe6e76edfd5efbcca65f4af0ea8eea14759ae431d23ba2a`, written
`2026-10-24T11:53:25Z`, 20 questions + expected keys + grader, before any row.

The grader is **correctness**, not form divergence (the R2-PROMPT `quality.json` metric compared P0 and
P1 answers token-by-token and so measured *form*). A probe mismatches when the answer omits the delta's
`sha8` prefix **or** omits a quoted ≥30-character contiguous run of the delta's flattened head. Each
question is asked in **P0 form and P1 form** on each model (40 probes/model, 80 total).

**Before** values are graded from the **pinned V0 completions already on disk** — the P1-form first-32
token windows in `cells/R2-PROMPT/O1/quality.json` and `O4/quality.json` — with the same grader, at zero
new requests. The window is a recorded limitation: a span quote appearing only after token 32 would be
missed, but in both pinned files the answers open with either the quote (P0) or the length+`sha8` (P1).

### A2.4 Serving per model, and the dense V0 re-pin

| model | endpoint | config | `config_sha256` | why |
|---|---|---|---|---|
| MoE `occamy-1.0` | SGLang `:8012/` (production) | **O1** | `f2efaaac1559ebc0a706c5012715dacff6948058ee8e5c946d5d45c622880c67` | production, untouched |
| dense `qwen3.5-9b` | vLLM `:8014/` | **O4** | `163a5db6b4c432e2a2ea17ffd6c44e336ed12af6eff39dce96be854032d77cb4` | `:8017` (O2, SGLang 9B) answered **nothing** at `11:53Z`; the card names `:8014` as the dense endpoint ("already up") |

Consequence, recorded because it changes the dense baseline: **dense V0 is re-pinned to O4/P1**
— `cells/R2-PROMPT/O4/rows.jsonl` (sha256 `23547e3a9611d0b5591f1b55726e854a607e9360fb123527b2b6c38ad25d4aab`),
P1 arm — because a Δunc must be measured on the endpoint that serves the round. The O2 pin of A1.3
(522.71831) is **retained as a cross-engine reference only**; it is not the dense delta basis, and no
number here may be quoted as if dense still ran on SGLang. MoE V0 is unchanged: O1/P1
(`cells/R2-PROMPT/O1/rows.jsonl`, sha256 `8d71a88f22310d59f6e63a1d43a0d6ed009c3dfe48de14d50f7a3d942c71db55`).

### A2.5 Round 1 census and bound

2 models × **3 arms** (P0, P1, P3) × 71 turns = **426 scored rows**; 40 quality probes/model = 80. The
card's own bound (500 live requests) is **already exceeded by its own mandated census** (426 + 80 = 506),
so the bound is treated as a guardrail against runaway, not as a licence to drop a pre-registered
measurement: no P2 calibration, no variants, no dry-run cells, cold retries capped at 3. Actual request
count is recorded in `orchestration/handoffs/SYS-OPT-R1B.json`.
