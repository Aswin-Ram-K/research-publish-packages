# Validation roadmap — from what is measured to what would support the paper

**Scope.** The staged path that turns the flagship's available evidence into what its claims require.
It is a **plan**: nothing in it has been executed, no cell has been launched, no request has been sent,
and no endpoint, service, fixture or budget has been touched. `BOUNDARY-PREREG` remains unexecuted;
gen-7 remains unapproved.

**Two rules this roadmap obeys.**

1. **Estimates are protocol arithmetic, never quotes.** Every request count below is either recorded
   in an existing protocol (and cited) or labelled `[INFERENCE]` with its formula shown. No figure here
   is a price for a run.
2. **The ledger snapshot is history.** `experiments/ptr-engine/measure/REQUEST-LEDGER.json` reads
   **2,591 spent / 1,729 remaining of 4,320**, rebuilt 2026-10-28. It must be **re-reconciled at
   execution time**; if it cannot be rebuilt and the arithmetic shown, the budget is *unknown* and zero
   requests are sent.

**Approval gates, stated once and applying to every stage below.** A separate, written operator
decision is required before: **(a)** any live/paid request, **(b)** any cap increase above 4,320, **(c)**
any host or service change (server restart, `--mem-fraction-static`, crash-loop repair, systemd unit),
**(d)** any fixture or grader change (it mints a generation and/or invalidates prior quality rows), and
**(e)** executing `BOUNDARY-PREREG` (a separate registered candidate: 696 scheduled, ceiling 810,
registered 2026-10-26, never pooled with anything here). This document authorises none of them.

---

## Stage map

| stage | purpose | requests | gate to enter | what it can conclude |
|---|---|---:|---|---|
| **0** | make the instrument able to say yes and no | **0** | none | whether any quality number can be reported at all |
| **1** | close the law's own open cell, priced on both instruments | **≈9** | approval (a) | whether the 2-token rule is measurable, and how the two read fields differ on the same rows |
| **2** | prove the instrument: controls fire red, treatments activate | **36 of ≤60** (E1) and/or **≈185** (5-arm pilot) | approval (a) after stage 0 | an **instrument report**, not an arm comparison |
| **3** | the adjudicable comparative | **7,560** ⇒ `UNFUNDED` at 1,729 | approvals (a) **and (b)** | RQ3/RQ4 — non-inferiority and cost |
| **4** | optional closures | tens; ≈90 | approval (a) | multi-append extension; the manuscript's §6a window gap |

---

## Stage 0 — offline gates (0 requests)

Each is a gate: a failure **stops the stage** and voids the dependent arms before their first call.
Protocol references are to
[`research/next-candidates/consonance-bounded-context-evaluation.md`](../../../research/next-candidates/consonance-bounded-context-evaluation.md)
§3; the design/deliverable split is in
[`RESEARCH-BRIEF.md`](RESEARCH-BRIEF.md) §5–§7.

| # | gate | pass condition | source | owner decision needed? |
|---:|---|---|---|---|
| 0.1 | **positive control can pass** | a known-good log passes; a wrong-value log fails **on the value**; a missing-fact log fails **distinguishably**; the same log scores identically twice; a tampered fixture exits 2 | protocol §3.1; `longrun/QUALITY-POSITIVE-CONTROL.md` | **yes** — the fix is a fixture/grader change, explicitly "an owner decision, not a patch" |
| 0.2 | **≥12 decidable checkpoints, all gradeable** | 12/12 gradeable (today `grade_v5` grades 8 of 12; 4 need `NONE`/`call_at_line` branches) | protocol §3.2; `docs/CHECKPOINT-COVERAGE.md` | no (measurement + code) |
| 0.3 | **fixture wall priced from measured growth** | a dry run shows each treatment reaching its wall inside the horizon (gen-6's wall was priced from *declared* padding: 10,616 vs live base 5,628–6,139 at 41–98 tok/turn ⇒ 73–113 turns to wall > 48) | protocol §3.2 | **yes** — a fixture change mints a generation |
| 0.4 | **four fingerprints frozen** | model (id + revision/quantisation digest), tokenizer (files/hash + chat-template hash), renderer (content digest of module→bytes), engine (image digest + exact flags); placeholders are a hard stop | protocol §3.3 | no |
| 0.5 | **replicate identity** | unique `(arm, rep, cell, turn_index)`; `rep` in `run_id`; pre-analysis assertion that row count = cells × turns × reps | protocol §3.4 | no |
| 0.6 | **activation gating** | per arm, the declared predicate is non-zero on the cell's own rows (`evicted_turns > 0`, `digest_rows > 0`, `masked_rows > 0`, `fetch_rows > 0` and non-empty `retrieval_outcomes`, `oracle_injections > 0`); exclusion computed from the stamp, never by name | protocol §3.5 | no |
| 0.7 | **budget preflight** | ledger rebuilt, arithmetic printed per arm, caps set before the first call; unknown ⇒ zero requests | protocol §3.6 | no |
| 0.8 | **independent verifier assigned** | a process or person that ran none of the arms; fixture digest checked at score time; `score_longrun.py` already exits 2 on tamper and 3 on a stub | protocol §3.7 | no |
| 0.9 | **scorer can express a retrieval miss and an abstention** | `retrieval_miss` / `abstained_correctly` scorable, with a red→green control: a fabricated answer must **fail** the extension before an abstention can pass it (today a grep for `abstain\|retrieval_miss\|STALE\|REVOKED\|NOT_FOUND` returns 0 matches; the four check kinds are `artifact`/`fact`/`constraint`/`repair`) | protocol §7 | no |
| 0.10 | **prototype extension is offline-deterministic** | the alignment-aware append planner (2-token pad at residue 0/1), fetch batching by body tokens, retrieval-outcome vocabulary and deterministic resume each have unit tests; index digest reproduces across two processes and two roots | `RESEARCH-BRIEF.md` §5.2; `RECORD.md` §1 | no |
| 0.11 | **law package re-derived** | the residual table in [`README.md`](README.md) §Verifying reproduces (`sglang 301 {0: 218, …}`; `vllm 86 {−1056: 1, 0: 85}`) | `experiments/miss-law/rows.jsonl` | no |

**Fixture classes must stay honest.** Multi-hop retrieval and unavailable/stale/revoked sources are
**absent** from every authored fixture. They are recorded `UNAVAILABLE` / `NOT_OBSERVED` and are never
scored as success; no fixture is fabricated to fill them (protocol §3.8).

---

## Stage 1 — the law's own open cell (≈9 requests)

**Purpose.** Turn the 2-token rule from `INFERENCE` into a measurement, and settle what the two read
fields say about the *same* rows — the paper's most attackable paragraph today.

**Design** (recorded in `N1-residue-law.md`, "What it would take to finish"): on SGLang, prime
`P1 = 8000`; resend byte-identically; then three appends. Read each response on **both**
`usage.prompt_tokens_details.cached_tokens` and `POST /generate` `meta_info.cached_tokens`. Both
readings are recorded on the row; neither is converted into the other.

**Controls (must fire red first).** identical-repeat control (expect hit ≥ 0.9 of `P1`); never-sent
control (expect 0); append control (expect reuse ≥ `P1 − k`). A control that can only report "as
expected" is not run.

**Falsifiers.** The 2-token pad does not change the billed class on either reading; or the two fields
agree at residue 0 (in which case the C1 dispute is a field-semantics footnote — kill criterion K2).

**Stop rule.** If the identical or never-sent control is red twice, the endpoint is misconfigured:
stop, report `INVALID-INSTRUMENT`, spend nothing further.

**Requests:** ≈9 (recorded estimate). **Approval:** (a).

---

## Stage 2 — instrument pilots (descriptive only)

Two independent pilots; either may run first; neither yields a verdict.

### 2a. `E1-CACHE-BOUNDARY-SWEEP` — 36 of a ≤60 ceiling

**Question** (preserved from the handoff): how does reuse depend on *where* a rewrite lands, on this
engine and model? **Design:** one prompt skeleton; controls first (identical ×3, never-sent ×3,
append ×3, mismatched-tokenizer ×3), then a sweep at ≥8 rewrite offsets from tail to head, offsets in
tokenizer units and reported in tokens **and** bytes, 3 reps each, alternating order, one frozen build,
one container, serial. 36 requests used, 24 held for re-runs.

**Control thresholds:** identical → hit ≥ 0.9 of `P`; append → reuse ≥ `P − k`; never-sent → 0;
mismatched tokenizer → no reuse. **Falsifier:** reuse does not fall monotonically with earlier rewrite
offset (e.g. it depends on block alignment only) — then `rewrite_depth` is not a usable predictor and
the checkpoint cost model is replaced by whatever the data show. **Decision it buys:** whether a
checkpoint is priced per token or per boundary; dropping `rewrite_depth` is a *result*.
**Source:** protocol §4.

### 2b. Five-arm comparative pilot — ≈185 requests

**Purpose:** prove the instrument, not the design: one task, 30 turns, all five arms (A/B/C/D/E), one
rep. `30 × 4 + 60 = 180` turn requests + ~5 checkpoint/digest ≈ **185** (protocol §6.3). It yields
**no verdict** and no arm comparison; its output is an instrument report: controls fired red, treatments
activated, the scorer could express a retrieval miss and an abstention.

**Why it is separate from the comparative:** a one-rep run is descriptive by the workspace's own rule,
and the pilot's per-task sample at 30 turns is 1.

**Requests:** 36 (E1) and ≈185 (pilot), both recorded in the protocol. **Approval:** (a), only after
stage 0 passes.

---

## Stage 3 — the adjudicable comparative (7,560 requests ⇒ `UNFUNDED`)

**This is the measurement the paper's RQ3 needs, and it cannot be run on the current ledger.**

```
turns per arm per rep over all available cells = 6×10 + 6×30 + 3×60        =   420
four one-request arms (A, B, C, E)          = 4 × 420                     = 1,680 / rep
D at 2 requests per turn (fetch + answer)   = 2 × 420                     =   840 / rep
three reps                                  = 3 × (1,680 + 840)           = 7,560
remaining ledger (recorded 2026-10-28)                                    = 1,729
ratio at the design's own request shape                                   = 4.37×
```
*(all figures from protocol §6.3; the ratio 7,560 / 1,729 = 4.3725…)*

**Descoped shapes, priced with the same arithmetic** — presented so the operator sees the real choice,
not a menu of wishes `[INFERENCE: same cell counts and request shapes, fewer arms/reps]`:

| shape | arithmetic | total | vs 1,729 |
|---|---|---:|---|
| 5 arms × 3 reps (design) | 2,520 × 3 | **7,560** | 4.37× ⇒ `UNFUNDED` |
| 5 arms × 1 rep | 2,520 × 1 | **2,520** | 1.46× ⇒ still unfunded |
| 2 arms (A, D) × 3 reps | (420 + 840) × 3 | **3,780** | 2.19× ⇒ still unfunded |
| 5 arms × 1 rep, 30 turns only (3 tasks available? **no** — 6 tasks supply 30 turns) | — | this is the **pilot** in 2b | descriptive only |

**Reading:** no shape of the full comparative fits inside 1,729 remaining, and the honest alternatives
are the three the protocol already names — fund it by raising the cap, fund only the pilots, or fund
neither. A cap increase is **approval (b)** and belongs to the operator, not to a session.

**Design, if funded.** Arms and their controls are protocol §6 (A/B/C/D/E + the C0F equal-information
baseline as an additional comparison); horizons 10/30/60 with the 60-turn cell available on **3** tasks
only (LR-02 64, LR-05 72, LR-06 60; LR-01 48, LR-03 56, LR-04 40 cannot supply 60 turns ⇒
`UNAVAILABLE`, not imputed); 3 reps per task/arm; one fixture set and version, one frozen build, four
equal fingerprints, the same verifier and prompt-budget accounting.

**Controls, per arm (protocol §6):**

| arm | positive control | negative control | falsifier |
|---|---|---|---|
| A `full-transcript` | byte-identical repeat hits | never-sent prefix misses | none — baseline |
| B `transcript-compact` | digest fires (`digest_rows > 0`); post-digest uncached measurable | **no-op digest costs ≈ 0** | digest never repays within 20 steps |
| C `masking-no-fetch` | masking fires (`masked_rows > 0`); marker resolves to a pointer id | a masked fact cannot be answered ⇒ must abstain, never invent | no quality-preserving saving vs A |
| D `bounded-recoverable` | `fetch_rows > 0`; `OK` returns the pinned range byte-identically | missing ref → `NOT_FOUND`; revoked → `STALE_OR_REVOKED`; scope → `SCOPE_UNGRANTED` | not non-inferior on verified success **and** not lower in uncached work / time-to-verified-success at 60 turns |
| E `oracle-evidence` | injection counter > 0; same verifier | a fact outside its budget must also abstain; an answer with no injection is `INVALID-INSTRUMENT` | none — upper-bound diagnostic |

Plus the battery: identical-repeat cache control and append cache control for **every** arm; a holistic
positive control (fact present, fetch works, answer correct); a holistic negative control (fact absent
from the store ⇒ the arm must abstain). Each is run **red first** on a deliberately broken log.

**Independently verifiable quality measure.** `verified_success` from the same scorer for every arm,
with the stage-0.1 contract, the stage-0.2 12-checkpoint coverage, and the stage-0.9 abstention
extension; a verifier that authored none of the arms re-scores from frozen rows; `tokens_to_verified_success`
reported as `UNDEFINED` where the denominator is zero — never 0, never substituted.

**Measurements (per horizon and arm).** total and peak **logical** prompt tokens; uncached work where
observable (else `NOT_OBSERVED`); cache reads; fetch calls and fetch tokens; completion tokens;
storage/index size; rebuild cost; end-to-end wall time; time and tokens to verified success; quality;
abstention; forbidden-action results; per-turn and per-segment (pre-boundary / transition /
post-boundary) decomposition — **never arm means alone**.

**Statistical and adjudication requirements.**

1. **Paired, task-level differences** within one fixture and fingerprint set; no pooled arm means and no
   ratio of totals (the two estimators differ on the record: 6.744331504 vs 6.0633608815).
2. **Every interval names its method and n** — t-based with df stated, bootstrap with seed, or
   Clopper-Pearson for proportions. `df = 2` intervals are reported as such, never widened silently.
3. **No p95 below the floor.** `min_n_for(0.95) = 60`; gen-6 refused p95 at n = 48; `n_eff` is computed
   on the arm's own turn-ordered series (gen-6 measured 26.1356 against a floor of 60). A tail claim
   needs a separately budgeted run.
4. **No re-pinning after rows are seen.** A fixture, threshold or estimator that moves after the first
   call makes the run `retrospective:true` and it is labelled so.
5. **Non-results are first-class:** `UNDEFINED`, `UNAVAILABLE`, `NOT_OBSERVED`, `INVALID-INSTRUMENT`,
   `UNFUNDED`. None is replaced by a zero or a blank.
6. **No pooling across builds, generations or ledger epochs**; gen-6 and gen-7 never share a column.
7. **An ablation is required for the paper's mechanism claim (RQ4):** the comparative must include, or
   be followed by, a D-variant **without** the alignment-aware planner, so the append arithmetic's
   contribution is separated from the design's. Pricing that variant is part of the same request shape
   (it is a D arm: 2 req/turn) `[INFERENCE — it adds a sixth arm and must be re-priced before approval]`.

**Stop conditions (protocol §9, abridged to the ones that fire in practice).**

- the quality path cannot be made to say yes (stage 0.1) ⇒ **stop**; every arm void;
- any fingerprint missing, changed mid-run or a placeholder ⇒ stop;
- a treatment that did not fire ⇒ `INVALID-INSTRUMENT` for that cell, excluded by computed rule;
- replicate collapse or rows deduped across reps ⇒ stop the analysis, fix the key, new generation;
- an absent stamp admitted, or a cell hitting its cap mid-run counted as data ⇒ stop;
- a missing fixture class scored as success ⇒ stop;
- a control that cannot report the opposite, or a control run only green ⇒ stop;
- budget unreconciled ⇒ zero requests.

---

## Stage 4 — optional closures (not required for the paper)

| closure | why | requests | status |
|---|---|---:|---|
| **multi-append sweep** (2–3 points, fixed residues) | extends the law from one append to a short run — the paper's own scope limit | "tens" (`N1-residue-law.md`) | unscheduled; estimate only |
| **resting-window arm** for the manuscript's §6a | the only recorded fix for "arms rest on a shorter window by construction"; owned by `papers/context-cache/`, not by this seed | ≈**90** | not approved (`N4-finish-flagship.md`) |
| **independent `+B` re-derivation** | kill criterion K3 | 0 if derivable from existing rows; a small re-probe if not | recommended before any submission |
| **`BOUNDARY-PREREG`** | separately registered candidate (696 scheduled / 810 ceiling) | 696 | **never pooled** with anything here; approval (e) |

---

## What this roadmap does not do

- It does not launch gen-7 or re-run any gen-6 cell. Gen-7 is a separate decision (fixture v9, projected-
  request fix, rep identity) and its rows are non-poolable with gen 6.
- It does not touch `papers/`, the filed artefacts, the ledger, `BOUNDARY-PREREG`, or the shared model
  server.
- It does not convert any estimate into a result. Every number above is either recorded in a protocol
  with its formula, or labelled `[INFERENCE]`.
