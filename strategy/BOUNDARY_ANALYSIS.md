# UBOUND1 — Boundary analysis: what the released per-case records can and cannot discriminate

**Unit:** UBOUND1 (report-only measurement). **Mode:** re-analysis of stored labels only; no model trained, no fine-tune, no GPU run.
**Reproduction script (written by this unit):** `scratch/ubound1/perk_analysis.py` → `scratch/ubound1/perk_table.json`.
**Everything below is measured from the four released result directories, or is marked `UNVERIFIED`.**

---

## 1. What per-case data actually ships

### 1.1 File lists with byte sizes

Command: `for d in repro/encoder-crossover-190/results repro/encoder-crossover-190-SANITISED/results scratch/uneutral10/package/results scratch/urecut1/package/results; do ls -la "$d"; done`

| file | repo `repro/encoder-crossover-190/results/` | `…-SANITISED/results/` | `scratch/uneutral10/package/results/` | `scratch/urecut1/package/results/` |
|---|---|---|---|---|
| `DEFECT-EVIDENCE.json` | 3724 | 3724 | — | — |
| `REPORT.md` | 28231 | 28231 | 27811 | 27811 |
| `baselines.json` | 80853 | 80853 | 57360 | 58436 |
| `eval-deberta-v3-base.json` | 81140 | 81140 | 63159 | 66523 |
| `eval-majority-class.json` | 80082 | 80082 | 62168 | 65448 |
| `eval-modernbert-base.json` | 81268 | 81268 | 63109 | 66664 |
| `eval-setfit-mpnet.json` | 81476 | 81476 | 63351 | 66748 |
| `eval-shuffled-label.json` | 81453 | 81453 | 63339 | 66833 |

`repro/encoder-crossover-190/results/` and `repro/encoder-crossover-190-SANITISED/results/` are **byte-identical**: `md5sum` comparison returned `IDENTICAL` for all 8 files (`DEFECT-EVIDENCE.json`, `REPORT.md`, `baselines.json`, and the five `eval-*.json`).
`scratch/uneutral10` and `scratch/urecut1` differ in bytes from each other on all 7 shared files except `REPORT.md` (identical, 27811 bytes).

### 1.2 Per-case outcomes: they DO ship

Every arm file carries `perCase`, and every one has exactly **190** records. The fine-tuned decider's per-case rows also ship, inside `baselines.json` under `models["decider-4b-exp11-reproduction"].perCase` (190 rows).

Top-level keys of an `eval-*.json` (literal, `repro/encoder-crossover-190/results/eval-modernbert-base.json`):

```
['arm', 'modelId', 'licence', 'role', 'device', 'temperature', 'temperatureSource', 'fixtureReads',
 'accuracy', 'accuracy95CI', 'ece', 'brier', 'eceUncalibrated', 'brierUncalibrated', 'meanPChosen',
 'perKind', 'perClass', 'latencyMs', 'seconds', 'perCase', 'orderPermutationProbe']
```

Representative per-case record — **encoder / control arms** (`perCase[0]`, verbatim):

```json
{"id": "worker.class-001", "kind": "worker.class",
 "options": ["reasoner (propose only)", "editor (attached, writes)"],
 "goldIndex": 0, "gold": "reasoner (propose only)", "predIndex": 1,
 "predLabel": "editor (attached, writes)", "pChosen": 0.565426678360755, "correct": false}
```

Union of `perCase` keys over all 190 records / all 5 arms (repro): `['correct', 'gold', 'goldIndex', 'id', 'kind', 'options', 'pChosen', 'predIndex', 'predLabel']`.

Representative per-case record — **fine-tuned 4B decider** (`baselines.json` → `models["decider-4b-exp11-reproduction"].perCase[0]`, verbatim):

```json
{"id": "worker.class-001", "predLabel": "reasoner (propose only)",
 "gold": "reasoner (propose only)", "correct": true, "pChosen": 0.7894}
```

Decider rows carry **no `options` list and no `goldIndex`**, so per-case arity K has to be joined in from a fixture/encoder arm by `id`. That join has **0 misses** (190/190 ids match on all four packages). The decider's own recorded source is `docs/research/EXP#11-evidence/decider-rows.jsonl`; in the two neutralised packages it is `docs/research/P04-evidence/decider-rows.jsonl`.

### 1.3 The two neutralised packages are a label-neutralisation pair, not a second measurement

`uneutral10` / `urecut1` per-case records use redacted field names and neutralised ids:

```json
{"id": "N01-001", "kind": "K02", "options": ["G16 (propose only)", "G28 (G14, writes)"],
 "F01": 0, "F54": "R03 (R08, writes)", "F20": 1, "F49": 0.565426678360755, "correct": false}
```

`uneutral10` neutralises option strings too; `urecut1` keeps the original option strings but uses the same `N…`/`K…`/`F…` coding. Measured: the **per-position `correct` flag sequence is identical to `repro` for all 5 arms in all 4 packages**, and the per-position K sequence is identical too (`per-position correct-flags identical to repro: {...all True...} | per-position K identical: True`). Aggregate check: `sum(bool(correct))` for `eval-modernbert-base.json` is 66 in `repro`, `uneutral10` and `urecut1` alike, and `accuracy` is `0.3473684210526316` in all four.

---

## 2. The gap stratified by the number of options K

Command: `python3 scratch/ubound1/perk_analysis.py` (literal output; `repro`, and identically for the other three directories).

```
===== repro {2: 33, 3: 27, 4: 76, 5: 54} cases 190 options 721
K n  modernbert deberta setfit majority shuffled decider gap  all_enc_below_maj
2 33 0.666667 0.575758 0.363636 0.666667 0.303030 0.848485 -0.181818 False
3 27 0.333333 0.333333 0.333333 0.555556 0.407407 0.703704 -0.370370 True
4 76 0.276316 0.328947 0.302632 0.434211 0.197368 0.684211 -0.355263 True
5 54 0.259259 0.240741 0.111111 0.296296 0.148148 0.555556 -0.296296 True
  wilson95 best-encoder(K): {2: [0.4961, 0.8025], 3: [0.1864, 0.5218], 4: [0.1884, 0.3858], 5: [0.1612, 0.3893]}
  wilson95 decider:        {2: [0.6908, 0.9335], 3: [0.5152, 0.8415], 4: [0.5730, 0.7777], 5: [0.4238, 0.6800]}
```

`perK tables identical across all four dirs: True`

- **K distribution matches the record exactly:** K=2 → 33 cases, K=3 → 27, K=4 → 76, K=5 → 54 = **190 cases / 721 options**, identical in all four packages. K is measured as `len(perCase[i].options)`.
- **The gap is non-monotone in K.** Best encoder minus decider: **−0.1818 (K=2), −0.3704 (K=3), −0.3553 (K=4), −0.2963 (K=5)** (cell counts: 22/33, 9+9/27, 21/76 setfit 23/76, 14/54). Widest at **K=3**, narrowest at **K=2**. It neither grows nor shrinks monotonically; the only clean contrast is K=2 vs K≥3.
- **Encoders sit below the majority-class control at K=3, 4 and 5 for all three heads; at K=2 they do not** — `modernbert` **ties** the control exactly (22/33 = 0.666667 both) and `deberta`/`setfit` are below it.
- The fine-tuned decider is **above the majority-class control at every K** (0.8485 / 0.7037 / 0.6842 / 0.5556 vs 0.6667 / 0.5556 / 0.4342 / 0.2963).
- Precision caveat, measured: Wilson 95% CIs at K=3 are ±0.17 wide (n=27); the K=3 vs K=4 gap difference (0.0151) is inside noise. Only the K=2-vs-K≥3 contrast is worth asserting.
- Confound already recorded by the manuscript: `papers/encoder-crossover-190/MANUSCRIPT.md:607-614` states accuracy tracks option arity for the two labellers "but the effect is confounded with kind", the 5-option stratum being dominated by `memory.admission` and `acquisition`.

---

## 3. What the released records can and cannot discriminate

### (a) Data scale / training signal — **not measured; cannot be settled from the release**
- Shipped training data (measured): `harness/data/train.jsonl` **800 rows** (K dist `{2:276, 3:220, 4:167, 5:121, 6:16}`; strata `revision` 600 + `H-A` 200) and `harness/data/dev.jsonl` **200 rows** (`H-B`); the sealed fixture is a separate 190. Sizes: train 2,205,127 B; dev 484,922 B; fixture-190.json 145,628 B; corpus.json 1,567,643 B.
- **No data-fraction or dose–response arms ship.** `baselines.json` `.models` has exactly three entries (`decider-4b-exp11-reproduction`, `imajev-4b-exp11`, `laya-typed-decisions`) and `.checks` has six reproduction checks; none varies training-set size.
- What would settle it: retrain the encoder heads on fractions of the 800-row corpus (e.g. 10/25/50/100 %) under `harness/train.py` and re-score the sealed 190 with `harness/evaluate.py`, or grow the corpus to BANKING77 order of magnitude. This is **re-training a model**, not re-analysis of stored labels — the stored labels record one trained model per arm and contain no scale dimension.

### (b) Per-case named-option decision vs fixed label space — **documented as a property of BOTH arms; cannot separate the two arms**
- `repro/encoder-crossover-190/harness/tcmodel.py:13-30`, verbatim heading `WHY THE HEAD IS POINTWISE, AND NOT A FIXED LABEL LAYER`: *"the corpus has 34 distinct gold labels, the 190 fixture cases draw on 215 distinct option labels, and only 15 labels are shared (`data/manifest.json`, `labelTransfer`). A fixed `num_labels=N` output layer trained on the corpus cannot name 200 of the fixture's options at all"*, and *"each arm scores every (situation, candidate option) pair independently through `tccommon.render`, and the per-case distribution is the softmax over that case's options."* The per-case `options` array in every shipped record is that per-case option set.
- Consequence: **on this fixture the encoder is not a fixed-label-space classifier and the decider is not answering a different question** — both choose among the same per-case named options. Whatever separates this fixture from BANKING77 (§2.1 of the manuscript) is a property of the *task shape*, not of one arm being a fixed-space classifier. What the release does **not** contain: any arm trained with a fixed `num_labels=N` layer, so "would the encoder win if it were allowed a fixed label space?" is **UNVERIFIED** and would need re-training (and a label space that overlaps the fixture, which the shared-15-label count says does not exist).

### (c) K / label-space size — **measured only for K ∈ {2,3,4,5}; cannot explain the BANKING77 direction**
- Within K=2…5 the gap is non-monotone (§2), so K alone does not order the encoder/decider outcome even inside the measured range.
- BANKING77 has K=77 and the training corpus K dist tops out at 6. The release contains **no** observation at any K above 5, so any "the K explains it" reading is extrapolation from a 4-point, non-monotone curve with n=27…76 per point. Asserting otherwise would be unsupported by these records.

### (d) Option-order / position effects — **measured for the encoder arms and the majority control; NOT for the decider**
- Encoder arms: `orderPermutationProbe.predictionFlips = 0`, `maxAbsDeltaPChosen = 0.0`, `cases = 190`, note *"exploratory add-on (pre-registration §5.6); NOT folded into H1"*. This is expected by construction — `tcmodel.py:26-28`: *"the per-case distribution is permutation-equivariant, so the 'order sensitivity' contaminant … does not exist for this head."*
- Majority-class control: **58 flips / 190** (`eval-majority-class.json` `orderPermutationProbe.predictionFlips = 58`; corroborated by `results/DEFECT-EVIDENCE.json` `.passes.final.arms.majority-class.orderPermutationFlips = 58`).
- A **retained earlier pass** had flips of 138/142/101/81/135 (`.passes.pass1_buggy_order_probe`), attributed by the harness to a probe bug: `harness/evaluate.py:392` — *"flips on a permutation-equivariant head — a probe that was wrong, not a finding."*
- The **decider carries no order probe** in any of the four packages → its position sensitivity is **UNVERIFIED** here. `UNVERIFIED` also: whether the shipped probe genuinely permuted option texts (the JSON records only the outcome, not the permutation seed).
- So (d) cannot be adjudicated for the decider from the release; it would need either the decider re-served with permuted option orders (re-running a 4B served model, i.e. GPU + weights) or its stored rows re-emitted with an order probe.

---

## 4. What a short boundary paragraph could honestly assert — and could NOT

**COULD assert (each clause measured by this unit):**
1. All four released packages ship full **per-case** records — 190 rows for each of the five arms and for the fine-tuned 4B decider (the decider inside `baselines.json`), and the per-K table is **identical across all four packages**.
2. On this fixture the best fine-tuned encoder head loses to the fine-tuned decider at **every** K ∈ {2,3,4,5}; the headline 0.3474-vs-0.6789 gap is not the product of a single arity stratum.
3. At **K=2 the encoder heads are not below a fixed decision rule** — the best head ties the majority-class control exactly (22/33 = 0.666667) — whereas at K=3, 4 and 5 **all three** encoder heads are below that control.
4. The encoder-vs-decider gap is **non-monotone in K** (widest at K=3, narrowest at K=2), so "the encoder closes the gap as K shrinks" is not what these records show; what they show is a single K=2 stratum (n=33) where the encoder reaches the fixed rule and still trails the decider by 0.18.
5. Both arms are **per-case named-option scorers** on this fixture, and only 15 of the 215 fixture option labels are shared with the 34-label training corpus.
6. Option order: the encoder arms are order-equivariant (0/190 flips), the majority-class control is not (58/190), and the decider's order sensitivity is **not measured** in the release.

**COULD NOT assert (nothing in the release measures it):**
- Anything about K > 5, about a 77-class fixed label space, or about BANKING77-like regimes; no arm in the release has a fixed label layer or a label space larger than 6.
- That **data scale** explains the difference, in either direction: no data-fraction arms, no second corpus, no model trained at a different size.
- That the encoder would win (or keep losing) with more data, with a fixed label layer, or under a matched token budget.
- That the non-monotone K shape is causal rather than confounded with `kind` (already flagged at `MANUSCRIPT.md:607-614`).
- That the per-K differences beyond K=2-vs-K≥3 are statistically robust (n=27 at K=3; Wilson CIs overlap).
- That the decider is order-insensitive.
- Any claim that the external paper (Benayas/Sicilia/Mora-Cantallops, DOI `10.1007/s10579-024-09796-y`) is wrong; this unit did not fetch or re-check it and must not be read as doing so.

---

## 5. The decisive test for (a): infrastructure it would need, and what exists locally

**Test:** a data-fraction (learning-curve) sweep — train each encoder arm on 10/25/50/100 % of `harness/data/train.jsonl` and re-score the sealed 190 — is the one experiment that would separate "data scale / training signal" from "task shape". `UNVERIFIED` whether a fraction sweep alone would be decisive without also matching the decider's own training volume; that matching is not possible from the release (the decider's training set is not shipped).

| Requirement | Local status (measured) |
|---|---|
| Harness code | **PRESENT** — `repro/encoder-crossover-190/harness/`: `evaluate.py`, `train.py`, `tcmodel.py`, `tccommon.py`, `prepare.py`, `analyze.py`, `collect.py`, `defect-probe.py`, `README.md`, `LEAD-WIRING.md`, `export-fixture.ts`, `lint.ts`. **Note the release policy contradicts this:** `papers/encoder-crossover-190/AVAILABILITY.md:24,43-44` lists the harness as **withheld**; the files exist in this workspace under `repro/`. |
| Fixture + training data | **PRESENT** — `harness/data/train.jsonl` (800 rows, 2,205,127 B), `dev.jsonl` (200 rows, 484,922 B), `fixture-190.json` (145,628 B), `corpus.json` (1,567,643 B), `manifest.json`, `lint-report.json`. |
| GPU | **ABSENT** — `nvidia-smi --query-gpu=name,memory.total` → `NVIDIA-SMI has failed because it couldn't communicate with the NVIDIA driver.` The shipped `device` field says `cuda`, so the recorded runs were made on a different host. |
| Trained encoder checkpoints | **ABSENT** — no `*.safetensors` or `pytorch_model.bin` anywhere in the workspace (`find` returned none); `~/.cache/huggingface` does not exist. `repro/encoder-crossover-190/MANIFEST.json:3` — *"all model weights withheld"*. Base encoders could be fetched from HF (`answerdotai/ModernBERT-base` 149M Apache-2.0; `microsoft/deberta-v3-base` ~184M MIT; `sentence-transformers/all-mpnet-base-v2` 109M Apache-2.0). |
| Decider-4b (4.66B) | **Cannot be re-run or re-trained locally** — no weights, no GPU. Any matched-recipe decider arm is out of reach on this host. |

**Cost shape:** the encoder half is cheap in principle (≤800 training rows, three ≤184M arms, minutes each on one GPU) but it is **re-training a model**, and it needs a GPU plus base weights that are not on this host. The decider half — and any BANKING77-scale corpus — is not available at all: the release ships neither the decider's weights nor a larger corpus, and `MANUSCRIPT.md:838` records that the source repository's 26-file evidence tree is likewise not released.

---

## 6. Honesty register

- `UNVERIFIED`: whether the shipped order probe genuinely permuted option texts (only the outcome is serialised); the decider's order sensitivity; the decider's per-case option lists (not shipped — K joined by `id`); whether a fixed-label-space encoder arm would change the outcome; whether data scale is the operative variable; whether the neutralised packages' `F*` fields map to the same semantics as the repro fields (the mapping is inferred from position-identical `correct`/K sequences and identical aggregates, not from a published key).
- **Not checked:** the external paper. This unit did not fetch, read or re-score Benayas et al.; nothing here bears on its correctness.
- **Not located** (not "does not exist"): any data-fraction arm, any fixed-label-layer arm, any decider order probe, any `decider-4b` checkpoint. Absence in the four directories listed in the unit card is what was measured.
- No file outside `strategy/BOUNDARY_ANALYSIS.md`, `orchestration/units/UBOUND1.md`, `orchestration/handoffs/UBOUND1.json`, `scratch/ubound1/**` was written by this unit. No model was trained, fine-tuned or run. `/home/zer0null/Duval` was never touched and no `git` command was run against it.
