# PREREG-COMPACTION — E7: does pinning beat summarising at the compaction boundary?

Pre-registration. Every hypothesis, design, control, predicted outcome, falsifier and budget ceiling
below is written **before** the corresponding run. A later result may not be reinterpreted against a
changed prediction.

This experiment is **E7** in the SPCC programme. It does not edit E1–E6; their predictions and
falsifiers remain binding. The design it tests is `docs/COMPACTION-CACHE-DESIGN.md`.

## Budget reconciliation (ledger authority)

Command run 2026-11-11:
```
cd "/home/zer0null/research extractor" && .venv/bin/python -c "import sys,glob; sys.path.insert(0,'experiments/ptr-engine/tools'); import request_ledger as R; paths=sorted(glob.glob('experiments/ptr-engine/measure/rows-*.jsonl')); r=R.build_report(paths,12094,0,0); print(r['budget'])"
```
Output:
```
files 103
{'cap': 12094, 'reserve': 0, 'headroom': 12094, 'spent': 10167, 'spent_deduplicated': 10137, 'spent_raw': 10167, 'would_spend': 0, 'projected': 10167, 'projected_raw': 10167, 'projected_deduplicated': 10137, 'remaining': 1927, 'remaining_raw': 1927, 'remaining_deduplicated': 1957, 'within_budget': True}
```
- cap = 12,094 (`experiments/ptr-engine/longrun/cell.py` `PROJECT_QUOTA`)
- spent = 10,167 over 103 `rows-*.jsonl` files
- remaining = **1,927**
- 10,167 + 1,927 = 12,094 (adds up; `build_report()["budget"]["spent"]` is the authority).

**E7 is gated.** `experiments/ptr-engine/tools/request_ledger.py --write --cap 4320` exits 4 with
`OVER BUDGET: spent=10167 + would_spend=0 = 10167 > cap=4320 - reserve=0 = 4320 (over by 5847)`, so the
launcher refuses to start. E7 cannot run until the operator settles the cap decision
(`docs/STATE.md` §6 item 1). The pre-registration is written now so the run is not designed after its
result is known.

---

## E7 — Does pinning beat summarising at the compaction boundary?

### Hypothesis

At equal verified accuracy, a fold that **drops the journal and keeps an append-only pinned layer**
(arm B) costs fewer normalised units per verified success than (a) the current fold that drops the
journal and keeps nothing (arm A), and (b) a fold that **summarises** the journal into the prefix
(arm C). The mechanism is not the prefix re-prefill — measured at 0.05 % of prompt tokens — but the
**re-fetch** that lost information causes.

### Design

One tool-enabled fixture, one model, temperature 0, seed 42, 100 turns per rep.

| Arm | Fold | Pins | Summary call | Marker location |
|---|---|---|---|---|
| **A `spcc`** (control) | drop journal at `COMPACT_EVERY` | none | no | L1 (inside prefix) |
| **B `pinned-compact`** | drop journal on window pressure | L1 append-only | no | L4 (tail) |
| **C `pinned-summary`** | drop journal on window pressure | L1 append-only | **yes** | L4 (tail) |
| **D `no-compact`** | never | none | no | — |

Arm A is the existing `spcc` arm unchanged. Arm D is the existing `transcript-grow` arm. Arms B and C
are new and must be added to `ARMS` in `experiments/ptr-engine/longrun/run_longrun.py:74`.

### Controls

- Identical fixture, identical checkpoint set, identical seed and temperature across arms.
- One answer per checkpoint; the denominator guard stays active.
- `/flush_cache` before every cell, so no arm inherits another's prefix.
- Distinct rewrite per rep, so a rep is not a cache replay of the previous one.
- `cached_tokens` read from the response's cache-details field; an absent field is `null` and makes the
  cost an **upper bound**, never a zero.
- The pin set is **identical** across B and C for the same checkpoint, so the only difference is the
  summary call.

### Primary metric

`cost_units_per_verified_success` at `(c = 0.00, o = 3)`, where

```
cost_units = billed_in × 1.0 + cached_in × c + out × o
```

reported at every `(c, o)` in `c ∈ {0.00, 0.10, 0.25}`, `o ∈ {1, 3, 5}`. A ranking that flips inside
that grid is reported as **not robust**, not as a win.

`c = 0.00` is the measured price on this endpoint, not an assumption: `billed_of`
(`experiments/ptr-engine/longrun/score_longrun.py:144-190`) computes
`billed_tokens = prompt_tokens − cached_tokens`, and over the 300 rows of
`rows-e2-turnover-2026-11-10.jsonl` the sums are prompt 476,697 / cached 431,680 (90.6 %) / billed
44,426. `c = 0.10` is the Anthropic/OpenAI cache-read multiplier, used as the portability case.

### Secondary metrics

`refetch_count` (tool calls that read material already present in the journal), `checkpoint_accuracy`,
`prefix_breaks`, `reprefill_tokens`, `compactions`, `pin_count`, `pin_tokens`, `summary_tokens`.

Use the repo's own field names: `cached_fraction_of_prompt` and `cached_fraction_of_accounted` from
`billing_block` (`score_longrun.py:192-315`). There is **no** field named `cached_fraction`; a test
asserts its absence.

### Predicted outcome (written before running)

1. **B ≤ A on cost** at equal accuracy. Margin small in tokens (the prefix rewrite is 0.05 % of prompt
   tokens) and large in re-fetches.
2. **C > B on cost.** The summary call plus the prefix rewrite costs more than the pins it replaces.
3. **C ≤ B on accuracy.** A summary is lossy; a pin is not.
4. **D has the highest prompt tokens and the lowest `refetch_count`.** It never loses anything; it is
   the cost ceiling.
5. **A has the highest `refetch_count`.** It loses the journal and keeps nothing.

### Falsifiers

- **B's `cost_units_per_verified_success` ≥ A's** → the pinning design does not pay, and
  `docs/COMPACTION-CACHE-DESIGN.md` §5.2 is wrong.
- **B's accuracy < A's beyond the noise band** (±4.2 pp, `PREREG-SPCC.md` §noise floor) → pinning costs
  quality.
- **C's accuracy > B's beyond the band** → summarising is worth it, and the design's "never summarise"
  rule (§5.3) is falsified.
- **`refetch_count` does not differ between A and B** → the claimed mechanism is not the one operating,
  and the result is a token-only comparison that §2.2 already shows is 1–6 %.

### Budget ceiling (requests)

Two stages, so a cost decision is not paid for at accuracy power:

| Stage | Arms | Reps | Turns | Requests | Decides |
|---|---|---:|---:|---:|---|
| 1 | A, B, C, D | 1 | 100 | **400** | the cost ranking |
| 2a | the two surviving arms | +1 | 100 | **200** | accuracy, first increment |
| 2b | the two surviving arms | +2 | 100 | **400** | accuracy, second increment |
| | | | | **1,000** | |

Stage 2 is split into two cells because the runner stops a cell at **500 real requests**
(`test_gate_arm_count.py`, `request_ceiling` `[200, 500]`); a single 600-request cell would be killed
mid-run and its rows would be a partial stamp. 1,000 requests fits the 1,927 headroom. **Stage 2 runs
only if stage 1 produces a cost separation larger than the sensitivity grid's flip threshold.** If
stage 1's ranking flips inside the grid, E7 stops at 400 requests and reports `not_adjudicable` — the
same verdict E1's gen-6 grid earned, and for the same reason.

### Instrument requirements before the first request

1. **Arms B and C exist and are registered** in `ARMS` (`run_longrun.py:74`), with `--tools` accepted.
   `experiments/ptr-engine/longrun/tests/test_matrix_audit.py:239-243` asserts the **exact** arm set, so
   it must be updated in the same change.
2. **The pin API exists** (`pin`, `retire`, `pins`) and writes to the new `PINS` layer only.
3. **The fold record is a pin in PINS**, and `prefix_sha256` is computed over `L0+PINS+L1`.
   `experiments/ptr-engine/longrun/tests/test_spcc_arm.py:118` asserts
   `set(lt) == {"L0","L1","L2","L3","L4"}` and must become `{"L0","PINS","L1","L2","L3","L4"}`.
   The record must **persist on every turn after the fold** — a record written to L3 (`work`) would
   vanish on the next turn and the agent would lose the knowledge that history was truncated.
4. **`refetch_count` is instrumented** — a tool call whose `path`+range is already present in the
   journal counts as a re-fetch. Without this the primary mechanism is unmeasured.
5. **The cache-details field is proven present.** ✅ **Already satisfied**: 298 of 300 rows in
   `rows-e2-turnover-2026-11-10.jsonl` carry `cached_reported=True` with
   `cached_source='prompt_tokens_details'`, so `--enable-cache-report` is on for the live server.
6. **`arm_cd.py` and `ptr_engine/layers.py` are added to `HARNESS_FILES`** (`cell.py:130-136`). They are
   **not** in it today — the tuple holds only `run_longrun.py`, `client.py`, `grade_v5.py`,
   `analyze_stats.py`, `tools/det_verify.py` — so an edit to the arm or the compiler mid-run would not
   change the harness digest and the run would not be invalidated. E7 changes both files; without this
   the run's own provenance is unverifiable.
7. **The preview-write hazard is closed** (`docs/STATE.md` §6 item 13): `cell.py:411` builds the live
   argv without `--preview-root`, so every live cell overwrites tracked
   `experiments/ptr-engine/state/previews/<task>/<arm>/turn-*.json`. E7 must not run until the live
   path writes to a run-scoped directory under gitignored `state/`.
8. **The 500-request brake is respected.** `test_gate_arm_count.py` records a `request_ceiling` of
   `[200, 500]` and a cell is stopped at **500 real requests**, not admitted on a prediction. Stage 1
   (4 arms × 100 turns × 1 rep = 400) fits. **Stage 2 (2 arms × 100 × 3 = 600) does not** — it must be
   split into two cells of 300, or the brake raised by the operator.
9. **`spcc` must be made tool-capable, or arms B and C must be built on another arm.** This is the
   blocker that would have wasted stage 1. `run_longrun.py:3919` services tool calls only for arms
   **not in** `(arm_cd.ARM_C, arm_cd.ARM_D, arm_cd.ARM_SPCC)` — so **`spcc` does not service tool calls
   today**, and `arm_requires_tools` (`run_longrun.py:3367-3369`) returns True only for `ARM_D`. The
   only tool-enabled rows in the corpus come from `pointer-stable`
   (`rows-longrun-v5-tools.jsonl`: 72 rows, all `arm: pointer-stable`, 48 `turn` + 24 `tool-followup`).
   Since arms B and C are `spcc` variants and `refetch_count` is E7's primary mechanism, **E7 cannot
   measure its own hypothesis until `spcc` services tools**. Two routes, and the choice is the
   operator's because it changes what `spcc` is:
   - **(a)** remove `ARM_SPCC` from the exclusion at `run_longrun.py:3919` and add it to
     `arm_requires_tools`, so `spcc` gains the tool channel. Small change; makes `spcc` a superset of
     `pointer-stable`'s mechanism.
   - **(b)** build arms B and C on `pointer-stable` and port the layer compiler into it. Larger change;
     keeps `spcc` as it is.

   Route (a) is recommended: it is one line plus a predicate, and it keeps the layer compiler as the
   single place a fold is defined.

### Deviation note — 2026-11-11, instrument properties measured before E7 ran

Measured offline against the real compiler, 0 requests:

- The fold marker lands **inside** the hashed prefix (`ptr_engine/layers.py:247-257` appends to
  `state.index_lines`; `prefix_text = "\n\n".join([l0, l1])` at `:282-283`), so every fold changes
  `prefix_sha256`. The re-prefill it forces is **86 tokens over 100 turns = 0.05 %** of 156,390 prompt
  tokens, because the post-fold prompt is small.
- The drop-journal saving is **6.38 %** of prompt tokens at L0 = 1,515, **1.73 %** at 6,060, **0.88 %**
  at 12,120. The absolute saving is constant; its share collapses as the fixed prefix grows.
- Pinning 200 tokens for 100 turns costs **187.6 %** of that saving at every L0 scale.

Consequence for the predictions above, stated as a prediction about the outcome: prediction 1's
**token** component is expected to be near-zero, and the whole of prediction 1 rests on the
**re-fetch** component. If `refetch_count` turns out not to differ between A and B, prediction 1 fails
and the falsifier fires. That is a result E7 will produce, not a reason to soften the claim.

The predictions and falsifiers above remain binding and unedited. This note records instrument
properties discovered before the run, not a post-hoc revision of the hypothesis.
