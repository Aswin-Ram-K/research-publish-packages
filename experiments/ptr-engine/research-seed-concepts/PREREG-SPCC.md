# PREREG-SPCC — Serving × Context Programme experiments

Pre-registration: every hypothesis, design, controls, predicted outcome, falsifier and
budget ceiling is written here **before** the corresponding run. A later result may not
be reinterpreted against a changed prediction.

## Budget reconciliation (ledger authority)

Command run:
```
cd "/home/zer0null/research extractor" && .venv/bin/python -c "import sys,glob; sys.path.insert(0,'experiments/ptr-engine/tools'); import request_ledger as R; paths=sorted(glob.glob('experiments/ptr-engine/measure/rows-*.jsonl')); r=R.build_report(paths,12094,0,0); print(r['budget'])"
```
Output:
```
{'cap': 12094, 'reserve': 0, 'headroom': 12094, 'spent': 7869, 'spent_deduplicated': 7839, 'spent_raw': 7869, 'would_spend': 0, 'projected': 7869, 'projected_raw': 7869, 'projected_deduplicated': 7839, 'remaining': 4225, 'remaining_raw': 4225, 'remaining_deduplicated': 4255, 'within_budget': True}
```
- cap = 12094 (from `experiments/ptr-engine/longrun/cell.py` `PROJECT_QUOTA`)
- spent = 7869
- remaining = 4225
- 7869 + 4225 = 12094 (adds up; `build_report()["budget"]["spent"]` is the authority).

## Order and dependencies

Order is fixed **E1 → E2 → E3 → E4 → E5 → E6**; each experiment depends on the previous.
E1–E5 are each 200–500 requests. E6 costs GPU hours, not requests.
**E6 runs only after E1–E5, and only if E1 shows `spcc` is a real arm.**

---

## E1 — Does stable-prefix + append-only beat masking at equal information?

- **Hypothesis:** The stable-prefix + append-only journal compiler (`spcc`) matches or beats bounded fetch on single-fact recall and beats masking everywhere, while costing no more billed tokens than masking.
- **Design:** 48-checkpoint fixture; arms `spcc` vs `masking-no-fetch` vs `bounded-context-fetch`; temperature 0, seed 42.
- **Controls:** identical fixture, identical checkpoint set, identical seed/temperature; one answer per checkpoint; denominator guard active.
- **Predicted outcome (written before running):** `spcc` scores ≥ fetch on single-fact and > masking everywhere; billed tokens ≤ masking.
- **Falsifier:** `spcc` below fetch on single-fact, or `spcc` not strictly above masking on any checkpoint class, or billed tokens above masking.
- **Budget ceiling (requests):** 200–500.

### Deviation note — 2026-11-10, instrument observation before E1 ran

Measured against the real module, before any E1 request was spent: `compile_prompt`
drops the journal at `COMPACT_EVERY = 24` and retains only a marker line; no
content survives the fold (`ptr_engine/layers.py:226-231`). A fact introduced at
turn 1 is present in the prompt at turns 1–23 and absent from turn 24 onward.

Consequence for the prediction above, stated as a prediction about the outcome:
E1's prediction that `spcc` beats masking **everywhere** is expected to FAIL on
any probe taken after the first compaction following that fact's introduction,
and the falsifier ("`spcc` not strictly above masking on any checkpoint class")
is expected to fire there. That is a result E1 will produce, not a reason to
soften the claim.

The prediction and falsifier above remain binding and unedited. This note
records an instrument property discovered before the run, not a post-hoc
revision of the hypothesis.

### Deviation note — 2026-11-10, measured noise floor

Measured after E1 ran, from two runs of the **same** arm on **byte-identical** prompts
(`experiments/ptr-engine/measure/rows-e1-spcc-2026-11-10.jsonl`, commit `e18a587`, vs the
`spcc` rows of `experiments/ptr-engine/measure/rows-e1-final-2026-11-10.jsonl`, commit
`e4692f8`): `prompt_sha256` and `prompt_tokens` are equal at all 100 turns, and the answers
still differ at 6 of them. Two of the six are scored checkpoints — T57
`cp.TX-03.f06.d5` and T60 `cp.TX-03.f06.d8` — so the same treatment scored 20/48 and 22/48
in two runs.

**Temperature 0 plus seed 42 is not a reproducibility contract on
`http://192.168.2.168:8012/v1`.** The measured band is:

- per-turn flip rate **6/100 (6 %)**; per-scored-checkpoint flip rate **2/48 (4.2 %)**
- run-to-run spread on the headline metric **±2/48 = ±4.2 percentage points**
- a 2-checkpoint gap is **1.41 sd** of a two-run difference (two-sided p ≈ 0.16)

Consequence for the design above: **`reps=1` is underpowered by construction.** At 48
checkpoints and the measured checkpoint flip rate, 80 % power to resolve a 2-checkpoint
difference needs **4 reps** (1,200 requests for 3 arms × 100 turns); using the more
conservative turn-level rate it needs **6 reps** (1,800 requests). E1 ran at `reps=1`
(300 requests), so every E1 arm-to-arm difference smaller than ~4 pp is inside the noise
band and is not evidence of a treatment effect.

The prediction, falsifier, controls and budget ceiling above remain binding and unedited.
This note records a property of the serving stack measured after the run, not a post-hoc
revision of the hypothesis, and it does not license re-reading E1's result against a
changed prediction.

**Open decision (operator, not this note):** whether E1's ceiling of 200–500 requests and
its `reps=1` shape are amended to admit a powered design. The arithmetic is that a
powered E1 costs 1,200–1,800 requests against a live ledger headroom of 3,682, so it
fits, but it is 2.4–3.6× the preregistered ceiling. Amending the ceiling or the rep count
is an operator decision and is **not** made here.

## E2 — What does compaction cost?

- **Hypothesis:** Larger compaction interval lowers rewrite cost with no accuracy loss until the interval exceeds the distance at which facts stop being refetched.
- **Design:** `COMPACT_EVERY ∈ {12, 24, 48}` on the same 48-checkpoint fixture and arm.
- **Controls:** identical fixture and model; only the compaction interval varies; compaction never fires mid-turn.
- **Predicted outcome (written before running):** cost falls with larger C, accuracy flat until C exceeds the distance at which facts stop being refetched.
- **Falsifier:** cost does not fall monotonically, or accuracy drops before the predicted distance.
- **Budget ceiling (requests):** 200–500.

## E3 — Is the distance cliff presence or position?

- **Hypothesis:** The observed distance cliff is a property of position, not of eviction (body present).
- **Design:** fact present at distances {2, 8, 20, 32, 64}, no eviction, both arms.
- **Controls:** body retained (no masking), identical fixture otherwise.
- **Predicted outcome (written before running):** if the cliff persists with the body present it is position; if it vanishes it was eviction — this decides how the headline may be stated.
- **Falsifier:** neither outcome is clean (mixed cliff) — would require re-running with finer distance grid.
- **Budget ceiling (requests):** 200–500.

## E4 — Which model can hold the format?

- **Hypothesis:** Nemotron Nano matches or exceeds occamy on contract-level scoring; all three models stay below the fetch ceiling on aggregation.
- **Design:** Nemotron Nano vs occamy-1.0 vs qwen3.5-9b on the same 48 checkpoints.
- **Controls:** identical fixture, identical prompts, identical seed/temperature.
- **Predicted outcome (written before running):** Nemotron ≥ occamy on contract-level, all three below fetch-ceiling on aggregation.
- **Falsifier:** Nemotron below occamy on contract-level (then keep occamy as measurement model).
- **Budget ceiling (requests):** 200–500.

## E5 — Does the host tier pay for itself?

- **Hypothesis:** Enabling SGLang hierarchical cache raises cached fraction and lowers billed tokens without hurting latency.
- **Design:** HiCache off vs on at identical prompts and context.
- **Controls:** identical prompts, identical context, identical model; only the cache flag varies.
- **Predicted outcome (written before running):** on: cached fraction rises, billed tokens fall, latency flat or better.
- **Falsifier:** cached fraction does not rise, or billed tokens do not fall, or latency regresses.
- **Budget ceiling (requests):** 200–500.

## E6 — Can local post-training move the fetch arm?

- **Hypothesis:** One epoch of LoRA on generated pointer tasks yields a measurable contract-level gain on held-out checkpoints, or the training path is shelved.
- **Design:** LoRA Nano on generated pointer tasks, 1 epoch, evaluate on held-out checkpoints.
- **Controls:** held-out checkpoints disjoint from training; same grader as E1.
- **Predicted outcome (written before running):** measurable contract-level gain or the training path is shelved — a go/no-go, not a success claim.
- **Falsifier:** no measurable gain → shelve training path.
- **Budget ceiling (requests):** GPU hours, not requests.

---

## Blocked inputs

- **E4** needs Nemotron weights on the remote host (remote writes blocked pending authorisation — see `serving/REMOTE-ROOT.md`). Unblocks when: operator authorisation text recorded verbatim in `serving/REMOTE-ROOT.md`.
- **E6** needs the same authorisation plus GPU time. Unblocks when: authorisation recorded AND Nano LoRA fits under the 60 GB cgroup cap (`cgroup_peak_gb + unaccounted_gb ≤ 60`).
- **E5** needs the relaunched SGLang with `--enable-hierarchical-cache`. Unblocks when: `curl -s localhost:8012/get_server_info | jq '.enable_hierarchical_cache'` returns `true`.

## Rules

- No payload-to-savings inference; billed tokens only, from the server's cache report.
- `ABSENT ≠ 0`.
- No cross-build comparison.
- Every cell records `fixture_sha256`, generation and `prefix_sha256`.
- E6 runs only after E1–E5 and only if E1 shows `spcc` is a real arm.
path: "/home/zer0null/research extractor/experiments/ptr-engine/research-seed-concepts/PREREG-SPCC.md"