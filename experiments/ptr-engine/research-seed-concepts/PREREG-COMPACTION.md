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
(arm D) costs fewer normalised units per verified success than every method a production agent actually
ships: plain compaction (arm A), observation masking (arm B), retrieval over history (arm C), and FIFO
truncation (arm F). The mechanism is **two** things, and the second was measured after this
pre-registration's first draft:

1. **The summary call.** At real context length a `compact` fold pays one extra request reading the
   whole pre-fold prompt. Measured on eight real session transcripts: `pins` is **1.9–2.7× cheaper**
   than `compact` at equal prompt size, and the entire difference is the summary call
   (`docs/COMPACTION-CACHE-DESIGN.md` §2.6).
2. **The re-fetch** that lost information causes — 202 of 290 tool calls (69.7 %) re-read a range
   already read (§2.5).

The prefix re-prefill is **not** the mechanism: measured at 0.05 % of prompt tokens in the toy regime,
and small even at real length because the post-fold prompt is small.

### Design

One tool-enabled fixture at **real context length** (`LR-07.v5.json`, 200+ turns, `L0 ≈ 38 k`,
`window_tokens = 131072`), one model, temperature 0, seed 42. Fold at **70 % of the window**.

| Arm | Fold | Pins | Recency | Summary call | Retrieval |
|---|---|---|---|---|---|
| **A `compact`** | summarise the journal at 70 % window | none | no | **yes** | no |
| **B `mask`** | mask tool results older than 8 turns | none | no | no | no |
| **C `retrieval`** | drop the journal; retrieve top-k past turns per question | none | no | no | **yes** |
| **D `pins`** | drop the journal, record in PINS | PLAN + facts | no | no | no |
| **E `pins-recency`** | drop the journal, record in PINS | PLAN + facts | **ACTIVE at tail** | no | no |
| **F `none`** | FIFO truncate at the window | none | no | no | no |

Arm A is the industry default and the one to beat. Arm B is the strongest cheap alternative. Arm C is
the retrieval baseline; it needs its own instrument (a BM25 or embedding index over the journal) and is
the only arm that is not a pure prompt-layout change. Arm F is the cost ceiling. Arms D and E are the
design; E isolates the two-tier todo (`docs/COMPACTION-CACHE-DESIGN.md` §5.5) from the pins.

**Why the regime changed.** The first draft of this pre-registration used `LR-01.v5.json` (48 turns,
`L0 ≈ 760` tokens, `window_tokens = 65536`). A real session has `L0 ≈ 38,408` tokens, a median prompt
of 115,677 and a max of 221,711. At toy length the drop-journal saving is 6.38 %; at real length it is
the dominant lever. The regime change is recorded here because it was made **before** any E7 request,
on the strength of a 0-request replay, not after seeing a result.

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
2. **The pin API exists** (`pin`, `retire`, `pins`) and writes to the new `PINS` layer only. The API
   must implement the four rules §3.6/§5.2 added, because an arm that omits them is not the design
   under test:
   - `pin(kind, text, source=None)` writes `P<n>|kind|T<t>|text` — the **turn stamp** is mandatory;
   - a write that would push PINS past its token budget is **refused** and the overflow returned, never
     truncated;
   - a correction is a new pin carrying `supersedes P<n>`, never an edit;
   - text whose `source` is tool output is **sanitised** for zero-width and bidi control characters
     before it enters PINS.
   The kind set is `goal|decision|constraint|blocker|warning|fact|ref|fold` — a synthesis, not a
   published standard (§3.6).
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

   **Settled 2026-11-11: route (b).** The operator chose to build the pin arms on `pointer-stable` and
   port the layer compiler into it, leaving `spcc` untouched. `spcc` therefore keeps its current
   no-tool behaviour and is no longer an E7 arm; the arms are `compact`, `mask`, `retrieval`, `pins`,
   `pins-recency` and `none`, and the pin arms are `pointer-stable` variants. The port is the
   `RouteBPort` change: `PINS` added to `CompactionState`, `pin`/`retire`/`pins` with the four rules,
   the `PLAN` pin and `ACTIVE` line, and the arm registry updated.

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

### Deviation note 2 — 2026-11-11, the fold trigger as implemented

`docs/COMPACTION-CACHE-DESIGN.md` §5.3 specifies two triggers: "fold when the prompt reaches 70–80 % of
the model's window, **or when the journal exceeds a token budget — whichever comes first**". The
implementation has the first and not the second, and that is deliberate:

- **Window pressure is implemented** as `CompactionState.fold_at_tokens`, set by the pin arms to
  `FOLD_AT_FRACTION = 0.70 × fixture["window_tokens"]`. The compiler has no tokenizer, so the size is
  estimated from characters at `CHARS_PER_TOKEN = 3.122` (measured on the 871-turn session).
- **The turn interval is off** for the pin arms (`compact_every=None`). A 24-turn interval folds at
  ~69 k tokens on a 45 k-token `L0`, under the 91,750 threshold, so it would always win and the window
  trigger would be dead code. A caller that names an interval still gets it as a floor.
- **The journal budget is not a separate parameter.** The window trigger already bounds the journal at
  `0.70 × window − L0`; a separate budget smaller than that headroom would always fire first and make
  the window trigger dead code, which is the same trap in the other direction. If a later fixture has a
  small `L0` and a large window, the journal budget becomes meaningful and should be added then, with
  the headroom arithmetic recorded.

**Consequence for the run.** On `LR-07.v5.json` (`L0 ≈ 40.5 k`, window 131,072) the threshold is
**91,750 tokens**, so the journal may reach ~51 k before a fold. That is the intended real-session
behaviour: a fold is forced by the window filling, not by a turn count.

**A fixture gap this exposed, recorded because it would have silently voided the trigger.**
`LR-07.v5.json` as first built carries no `tool_outputs` bodies, so `add_delivery` is never called and
each journal line is only the question text (~45 tokens). Driving the real arm over all 220 turns, the
prompt reaches only **55,485 tokens at T220** — the threshold is never reached and the window fold never
fires. The fixture is real-length in `L0` but not in journal growth, and it is being rebuilt with the
real read bodies so the journal grows ~1,000 tokens per turn and the prompt crosses the threshold at
roughly T47. **E7 must not run on a fixture whose journal does not grow**, or the treatment under test
never fires and the result is vacuous.

### Deviation note 3 — 2026-11-11, the fold fraction is calibrated, not guessed

`FOLD_AT_FRACTION` was `0.70` and the fold fired at **67.1 %** of the window in real tokens, below
the design's 70 % floor. The cause is the estimator, not the fraction: the compiler has no tokenizer,
so it divides characters by `CHARS_PER_TOKEN = 3.122` (`ptr_engine/layers.py:185`), a constant measured
on a whole real prompt, which is prose-heavy. Delivered code bodies measure **3.93 chars/token** on
cl100k, so the estimate runs **5.5 % high** on a code-heavy journal.

`FOLD_AT_FRACTION = 0.739` (`0.70 × 1.055`) lands the fold at 70.0 % in real tokens. Measured on
`LR-07.v5.json` with the real tokenizer, 0 requests, five folds:

| fold | pre-fold real tokens | fraction of 131,072 |
|---|---|---|
| T41 | 92,056 | 0.702 |
| T79 | 91,655 | 0.699 |
| T119 | 92,098 | 0.703 |
| T161 | 93,135 | 0.711 |
| T201 | 92,776 | 0.708 |

Mean **0.705**, inside the design's 70–80 % band. Pinned by
`test_calibrated_fraction_lands_the_fold_in_the_design_band` in
`experiments/ptr-engine/longrun/tests/test_pinned_arm.py`, which is **red at `0.70`** (fractions
0.660–0.668, `assert 0.69 <= 0.6638` fails) and green at `0.739`.

**Re-derive this constant** if `CHARS_PER_TOKEN` changes or a fixture's content mix moves away from
code. It is a calibration against one measured bias, not a free parameter: the design's 70–80 % band is
the invariant, and the fraction is whatever makes the real-token fraction land there.
