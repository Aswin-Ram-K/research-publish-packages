# `encoder-crossover-190` — minimal reproducibility subset (EXP#12 / paper #3)

**The paper.** EXP#12, the *typed-channel comparison*: for a typed decision with 2–8 options, does a
fine-tuned encoder decision head reach or beat a **fine-tuned 4B** generative decider on the same held-out
190-case instrument — and does the encoder's native per-option distribution buy better calibration?

**The answer, as measured.** *No on both counts.* The best encoder head scores **0.3474** against the 4B's
**0.6684** (and the same-run reproduction **0.6789**) — barely above the 0.2911 chance floor and **below the
mandatory majority-class control (0.4526)**. Falsifiers **F1** (accuracy) and **F3** (calibration) fired, so
the experiment is **CLOSE**: the branch was closed unmerged. The published "a small encoder wins" evidence
compares encoders against *prompted* LLMs; it does not transfer to a fine-tuned comparison on this fixture.

**The policy this subset implements** (author decision 2026-10-15): papers are public (CC BY 4.0); every
paper ships a **minimal reproducibility subset** — fixture schema, the fixture, the evaluation harness and
the exact commands, and the pre-registered protocols. **Withheld: the agent-state kernel / runtime
implementation, and any model weights.** This is the publish-the-eval-harness / withhold-the-model norm.

---

## 1. Provenance and revisions

| | |
|---|---|
| Target repository | `/home/zer0null/Duval` — strictly read-only; no write, no commit, no state change |
| Target HEAD (before = after) | `907fa39da7ba8ecfbe6e976b7a4cddadea7ac36b` |
| Instrument | `evals/fixtures/reflex-decisions.ts`, 145,031 B, 190 cases + 1 interface match |
| Instrument sha256 | `076164ac53c2c1aac130953345c481f88b51f4d6fb93d465c7430308a99b4796` |
| Harness revision | closed branch `a5ef1b28a7baca7dc1094757106b6a6af2c2aaf8`, path `tools/typed-channel/` |
| Second labeller | workspace `experiments/second-labeller-190/` (unit UEXP) |

**A provenance caveat a reviewer must know.** The harness is **not on the target's trunk**: FT-12 closed the
branch unmerged, and its method was left behind at `a5ef1b2` while its evidence was harvested to trunk at
`docs/research/EXP#12-evidence/`. The harness files here were recovered **read-only from the git object
store** (`git cat-file blob a5ef1b2:tools/typed-channel/…`), never by checking out or touching the working
tree. `INTEGRITY.md` shows both hashes for every file.

## 2. Layout

```
fixture/       reflex-decisions.ts              190-case instrument, byte-identical to the target
               DECISION_CASE_SCHEMA.ts          DecisionKind + DecisionCase (target lines 53-75), the schema
harness/       tccommon.py, tcmodel.py           one renderer + shared metrics; the arm definitions
               export-fixture.ts, lint.ts       steps 1-2 (TypeScript; need a repo-shaped checkout)
               prepare.py, train.py, evaluate.py, analyze.py, defect-probe.py, collect.py
               README.md, LEAD-WIRING.md        the harness's own documentation
               data/                            corpus.json, train.jsonl, dev.jsonl, fixture-190.json,
                                                lint-report.json, manifest.json — the run's frozen inputs
preregistration/ EXP12-…-prereg.md               EXP#12 §1–§9, the frozen pre-registered protocol
results/       eval-{modernbert-base,deberta-v3-base,setfit-mpnet,majority-class,shuffled-label}.json
               baselines.json, REPORT.md, DEFECT-EVIDENCE.json
second-labeller/ RUN.json, EVIDENCE.md, metrics.json, disagreements.jsonl, PREREGISTRATION.md,
               parse_fixture.py, compare.py, labelsB.json, OWED_CORRECTIONS.md
```

## 3. What a reviewer can reproduce from this subset

1. **Instrument identity** — the fixture hashes to the digest frozen in the pre-registration; the sealed
   190 are the same cases the 4Bs were scored on.
2. **Every headline number** — the five per-arm sealed-190 records (`results/eval-*.json`) and the five
   dev-split records live inside them; `results/baselines.json` holds the re-scored controls.
3. **The paired analysis** — `harness/analyze.py` recomputes exact McNemar on discordant pairs, the
   **paired** MDE (M11), and the F1–F6 verdicts from those records.
4. **The fixture-reliability result** — `second-labeller/` re-parses the fixture and re-runs the comparison
   that produced `metrics.json` (agreement 0.9052631578947369, κ 0.9013584840356494, 18 route-B
   disagreements). **It is not inter-annotator agreement** — the second labeller is a model; that
   limitation is recorded verbatim in `metrics.json.limitation` and in `PREREGISTRATION.md` §0.

### Headline table (from `results/REPORT.md` / the EXP#12 resolution)

| Arm | Params | Fixture accuracy | ECE | ms/decision |
|---|---|---|---|---|
| `modernbert-base` | 149M | 0.3474 | 0.0994 | 12.37 |
| `deberta-v3-base` | 184M | 0.3474 | 0.1629 | 14.16 |
| `setfit-mpnet` | 109M | 0.2632 | 0.1536 | 11.96 |
| `majority-class` (control) | 0 | 0.4526 | 0.2026 | ~0.00 |
| `shuffled-label` (control) | 149M | 0.2316 | 0.0808 | 12.46 |
| chance floor (mean 1/k) | — | 0.2911 | — | — |
| `decider-4b` (baseline, from §3) | 4.66B | 0.6684 | — | — |
| `decider-4b`, same-run reproduction | 4.66B | 0.6789 | 0.0551 | 53.06 |

Paired McNemar, best head vs the same-run reproduction: **b = 27, c = 90, ψ = 0.616, Δ = −0.3316,
exact p = 4.167e−09, paired MDE 0.1595** — the harm is twice the MDE.

## 4. Exact commands

### (A) Instrument digest — 10 seconds, no dependencies

```bash
cd repro/encoder-crossover-190
sha256sum fixture/reflex-decisions.ts
# expect 076164ac53c2c1aac130953345c481f88b51f4d6fb93d465c7430308a99b4796
sha256sum harness/data/corpus.json
# expect c78681d6cf35bf23245bd24963c5fbdd6b3ea03e1bf74d1b3ddc5a49ca63fd66
```

### (B) Re-run the comparison — the Python pipeline (steps 3–8)

The environment the numbers were produced in: python 3.12, `torch 2.11.0+cu130`, `transformers 5.9.0`,
plus `scikit-learn` and `joblib`; measured on an NVIDIA GB10 (aarch64). CPU works but is slower.

```bash
cd repro/encoder-crossover-190/harness
python3 prepare.py        # verifies both digests, refuses on a fired F4 lint, renders train/dev.jsonl
python3 train.py --epochs 3
python3 evaluate.py       # opens the sealed 190 exactly once, after every arm is frozen
python3 analyze.py        # exact paired McNemar, paired MDE, F1–F6 verdicts
python3 defect-probe.py   # dev split only; never opens the fixture
python3 collect.py        # copies the small evidence into results/ and writes REPORT.md
```

### (B′) Steps 1–2, the two TypeScript steps (optional — see §5)

They expect a repo-shaped checkout (`<root>/evals/fixtures`, `<root>/tools/typed-channel`, `<root>/scripts`):

```bash
mkdir -p <root>/evals/fixtures <root>/tools
cp fixture/reflex-decisions.ts <root>/evals/fixtures/reflex-decisions.ts
cp -r harness <root>/tools/typed-channel
cd <root> && ./scripts/run.sh tools/typed-channel/export-fixture.ts   # asserts the digest before AND after
./scripts/run.sh tools/typed-channel/lint.ts --demo                   # F4 lint, both directions + seeded control
```

### (C) Re-run the second-labeller check

```bash
cd repro/encoder-crossover-190/second-labeller
cp ../fixture/reflex-decisions.ts ./reflex-decisions.sandbox.ts   # parse_fixture.py reads this exact name
sha256sum reflex-decisions.sandbox.ts ../fixture/reflex-decisions.ts
python3 parse_fixture.py    # writes cases.json, parse_summary.json, characterisation.json
python3 compare.py          # reads cases.json + labelsB*.json; rewrites disagreements.jsonl and metrics.json
```

`compare.py` **rewrites** `disagreements.jsonl` and `metrics.json` in place; hash them first if you want to
prove the shipped copies are this run's outputs.

## 5. Is the harness genuinely self-contained? **Partial — precisely:**

- **Runs, but not as a one-liner.** The six Python steps are runnable from `harness/` with its included
  `data/`; they import each other by bare module name and resolve paths relative to their own directory, so
  the working directory must be `harness/`.
- **Missing runner.** Steps 1–2 need the target's `scripts/run.sh` (a `tsx`/node TypeScript runner) and the
  repo's `package.json`/`node_modules`; none of those are in this subset. Their **outputs are included
  byte-identical** (`harness/data/fixture-190.json`, `harness/data/lint-report.json`), and `prepare.py`
  re-verifies the corpus digest, the F4 lint report and the exported JSON's shape (the instrument's own
  sha256 is asserted by `export-fixture.ts` and `lint.ts`), so the Python pipeline runs without them.
- **Missing runner (path shape).** `export-fixture.ts` imports `../../evals/fixtures/reflex-decisions.ts`;
  in this subset the fixture sits at `fixture/`, so steps 1–2 need the checkout layout shown in (B′).
- **Weights withheld by policy.** `train.py`/`evaluate.py` fetch three **public** checkpoints over the
  network at run time — `answerdotai/ModernBERT-base` (Apache-2.0), `microsoft/deberta-v3-base` (MIT),
  `sentence-transformers/all-mpnet-base-v2` (Apache-2.0). No weights are shipped here; no weights exist in
  the target either (its `out/` checkpoints are gitignored).
- **Not like-for-like hardware.** The encoder latencies were measured locally on the GB10 while the 4B
  figures come from a served stack — the F6 caveat, kept in the report.
- **Bit-exactness of the sealed scores** additionally depends on torch/transformers versions and device; the
  shipped records are the run of record.

## 6. Two inclusions beyond the unit card's list, and why

- `second-labeller/labelsB.json` — `compare.py` globs `labelsB*.json`; without it the check cannot re-run.
- `second-labeller/OWED_CORRECTIONS.md` — the experiment's own pending-corrections ledger; shipped so the
  evidence is not presented as unqualified.

## 7. What is deliberately absent

See [`EXCLUDED.md`](EXCLUDED.md): the agent-state kernel/runtime (`src/`, `kernel/`), model weights,
`traces/`, `runs/`, `tmp/`, `scratch/`, `archive/`, `node_modules/`, and the target's own `LICENSE`.
**No secret-shaped file was encountered** (scan recorded in `EXCLUDED.md`; the pattern hits zero paths).

## 8. Licence

**Not decided.** This subset carries no licence yet; read [`LICENCE_TODO.md`](LICENCE_TODO.md) before
publishing. The fixture's *content* is covered by the papers' CC BY 4.0 decision; the *code* licence for
this subset is an open author decision (unit UCODE1 is analysing options).

**Byte-integrity of every copy is recorded in [`INTEGRITY.md`](INTEGRITY.md); the machine-readable file
list with sha256, source path and size is [`MANIFEST.json`](MANIFEST.json).**
