# tools/typed-channel — EXP#12, the typed-channel comparison

**Pre-registration (frozen, binding):** [`docs/research/experiments/EXP#12-typed-channel-comparison.md`](../../docs/research/experiments/EXP#12-typed-channel-comparison.md)

The one sentence this experiment exists for:

> For a typed decision with 2–8 options, does a fine-tuned encoder decision head reach or beat our 4B
> generative deciders on the same held-out instrument — and does its native per-option distribution
> buy better calibration?

This directory is the *entire* experiment. It is an experiment tree, never part of the runtime (the repository's own rule: nothing is promoted into the runtime by an experiment).

---

## Pipeline

Run in order. Steps 1–3 are offline and run anywhere; step 4 needs the three encoder checkpoints
(network) and a torch device.

```bash
# 1. freeze the sealed instrument to JSON, verifying its sha256 before AND after
./scripts/run.sh tools/typed-channel/export-fixture.ts

# 2. the F4 contamination lint, both directions, with its seeded-copy fired/silent control
./scripts/run.sh tools/typed-channel/lint.ts --demo

# 3. verify digests, assert the family split, render the examples
python3 tools/typed-channel/prepare.py

# 4. fit the three heads and the two controls (GPU strongly preferred; CPU works)
python3 tools/typed-channel/train.py --epochs 3

# 5. score every frozen arm on the sealed 190, ONCE
python3 tools/typed-channel/evaluate.py

# 6. paired McNemar + paired MDE + the F1–F6 verdicts
python3 tools/typed-channel/analyze.py

# 7. (instrument check) reproduce the SetFit scoring defect and its fix on the DEV split
python3 tools/typed-channel/defect-probe.py     # reads dev.jsonl only, never the fixture

# 8. copy the small committable evidence out of out/ and write the report
python3 tools/typed-channel/collect.py
```

`data/` holds the inputs and the split; `out/` holds the run's artefacts (gitignored: the checkpoints
are hundreds of MB); `results/` holds the small evidence that belongs in the tree.

## Files

| File | What it is |
|---|---|
| `tccommon.py` | the ONE renderer (`render`), the shared metrics (ECE, Brier, temperature), and the frozen digests. Train and eval both import it, so they cannot measure a formatting difference. |
| `tcmodel.py` | the arm definitions: `PointwiseScorer` (ModernBERT / DeBERTa-v3) and `LogisticPairHead` (the SetFit-style frozen encoder + logistic head), plus the licence record. |
| `export-fixture.ts` | imports `evals/fixtures/reflex-decisions.ts` (the source of truth, not a copy), asserts 190 cases and the sha256 before *and* after, writes `data/fixture-190.json`. |
| `lint.ts` | the EXP#11 8-gram contamination rule, ported verbatim, run in both directions against the real 800-row training split, plus `demonstrateLint` adapted to this experiment's two field vocabularies. |
| `prepare.py` | digest checks, the F4 refusal, the by-family split with the no-straddle assertion, and the rendered `train.jsonl` / `dev.jsonl`. |
| `train.py` | fits the arms. The epoch-1 checkpoint is saved *before* any selection; dev can move neither the operating point nor the eval. Never opens the fixture. |
| `evaluate.py` | opens the fixture exactly once, scores every frozen arm, measures accuracy / ECE / Brier / per-class / latency, and runs the exploratory order-permutation probe. |
| `analyze.py` | exact McNemar on discordant pairs, the paired MDE (and the unpaired one beside it, M11), and the F1–F6 verdicts. |
| `defect-probe.py` | reproduces the SetFit scoring defect and its fix over the 200 H-B development cases, so the claim in `results/NOTES-defects.md` D2 is a measurement rather than a transcript. Never reads the sealed fixture. |
| `collect.py` | copies the small evidence into `results/` and writes `results/REPORT.md`. |
| `results/` | the committable evidence: per-arm dev and sealed-190 records, the baseline re-scores, the paired analysis, `REPORT.md`, and `NOTES-defects.md`. |

## The design decisions this directory makes, and why

1. **The head is a pointwise option scorer, not a fixed label layer.** The corpus has 34 gold labels,
   the fixture draws on 215 option labels, and 15 are shared (`data/manifest.json` → `labelTransfer`).
   A fixed `num_labels=N` layer cannot name 200 of the fixture's options, so it would measure the
   vocabulary mismatch rather than the transfer. Each arm scores every `(situation, candidate option)`
   pair through `tccommon.render`, and the per-case distribution is the softmax over that case's
   options. This is what `DECIDER_TIER.md` §4 calls a *label-set classifier*.
2. **One situation slot.** A corpus row has `state` (facts) + `instructions` (rules); a fixture row has
   one `question` paragraph carrying both. So the corpus situation is `state + " " + instructions` and
   the fixture situation is `question` — the sides differ in content, not in structure. `criteria` is
   deliberately excluded: it is a label-keyed restatement of the rules that exists on one side only.
3. **The operating point is epoch 1, fixed in advance.** `--epochs` follows the dev curve for the
   report; it cannot move the checkpoint that is scored.
4. **The split is by family and asserted, not assumed.** 600 revision + 200 H-A train (170 families),
   200 H-B dev (40 unseen families), 0 families and 0 clans shared.
5. **The fixture is read once, in one process, after every arm is frozen.** `out/fixture-read-receipt.json`.

## Environment used

Trained and evaluated on the GX10 (`gx10-163b`, aarch64, NVIDIA GB10) in a venv created with
`--system-site-packages` over the host's python 3.12 + torch 2.11.0+cu130 + transformers 5.9.0, plus
`scikit-learn` and `joblib` installed into that venv only. The host's own environment was not modified.
See `results/REPORT.md` for the timings and for the CPU fallback note.
