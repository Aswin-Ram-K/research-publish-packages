# Availability — `encoder-crossover-190` (paper #3 / EXP#12)

**One paragraph for a reviewer.** This paper is public under **CC BY 4.0** (author decision, 2026-10-15). It
ships a **minimal reproducibility subset** at `repro/encoder-crossover-190/`: the sealed 190-case decision
fixture and its schema; the verification tooling (`verify/recompute-claims.py`, and the second labeller's
`parse_fixture.py` and `compare.py`); the pre-registered protocols; the per-arm result records the claims rest
on, and the re-scored controls with their **per-case** rows; and the second-labeller evidence, with a
`README.md`. **Withheld by policy:** the **evaluation harness** — the model, training and evaluation code and
its frozen `data/` — plus the agent-state kernel / runtime implementation and all model weights (the three
arms are **public** Hugging Face checkpoints fetched at run time). A reader therefore **cannot retrain an
arm, cannot re-render the model inputs, and cannot re-run the evaluation pipeline**; what ships verifies the
recorded results, it does not regenerate them. The released artifacts are
**source-available under PolyForm Noncommercial 1.0.0** with an author-offered **paid commercial licence**; the
main repository stays fully proprietary and closed.

## What is released, and where

All paths below are under `repro/encoder-crossover-190/`.

| Released | Path |
|---|---|
| sealed 190-case fixture + schema | `fixture/reflex-decisions.ts` (sha256 `076164ac53c2c1aac130953345c481f88b51f4d6fb93d465c7430308a99b4796`), `fixture/DECISION_CASE_SCHEMA.ts` |
| verification tooling | `verify/recompute-claims.py`; `second-labeller/parse_fixture.py`; `second-labeller/compare.py` |
| evaluation harness (**withheld**) | `harness/` — 18 files (`tccommon.py`, `tcmodel.py`, the six Python steps, the two TypeScript steps, `data/`, `README.md`, `LEAD-WIRING.md`); not shipped |
| exact commands | `README.md`; `verify/run-verification.sh`; `papers/encoder-crossover-190/EVIDENCE_NOTES.md` |
| pre-registered protocols | `preregistration/EXP12-typed-channel-comparison-prereg.md`; `second-labeller/PREREGISTRATION.md` |
| results | `results/eval-{modernbert-base,deberta-v3-base,setfit-mpnet,majority-class,shuffled-label}.json`; `results/baselines.json` (per-case rows); `results/REPORT.md` — **§D1–D3 carry the defect / correction-chain write-up**; the standalone `results/DEFECT-EVIDENCE.json` probe is deliberately **not** part of the released set |
| second-labeller evidence | `second-labeller/{RUN.json,EVIDENCE.md,disagreements.jsonl,labelsB.json,compare.py,parse_fixture.py,OWED_CORRECTIONS.md}` |
| integrity / boundary record | `INTEGRITY.md`, `MANIFEST.json`, `EXCLUDED.md`, and the verification records under `verify/` |

**Declared primary baseline.** **0.6789** — auditable from `results/baselines.json`
(`.models["decider-4b-exp11-reproduction"].perCase`, 190 rows;
`.strata.instrument190.reproducesAt3dp = true`, `.strata.instrument190.absoluteDifference = 4.7e−05`).

**Harness provenance.** The EXP#12 harness is **not on the source repository's default branch**: recovered from
an unmerged development branch (name and commit withheld), and `tools/typed-channel/` does not exist on trunk. The 18 harness files were recovered **read-only** from the git
object store (`git cat-file blob`) and are **withheld** from the released artifact.

## What is withheld, and why

| Withheld | Why |
|---|---|
| **evaluation harness** (`harness/`) — model, training and evaluation code with its frozen `data/` | the release ships the fixture, the verification tooling and the cited result records; the harness itself is withheld |
| agent-state kernel / runtime implementation (`src/**`, `kernel/**`) | it is the system the measurement is *about*; the standing policy is "open paper, withheld implementation" |
| all model weights | frontier-lab norm — publish the eval harness, withhold the model; the three arms are **public** checkpoints fetched at run time (`answerdotai/ModernBERT-base`, Apache-2.0; `microsoft/deberta-v3-base`, MIT; `sentence-transformers/all-mpnet-base-v2`, Apache-2.0) |
| the source repository's 26-file evidence tree, traces, run artefacts, scratch trees, vendor code | not needed to re-run the measurement; `EXCLUDED.md` names the full boundary in **15 exclusion classes** |

Checking this paper's claims requires the **fixture, the verification tooling and the result records**. It does
**not** require the kernel, the weights, or the training pipeline — and because the harness is withheld,
**reproducing the measurement itself is not possible from the released material**.

## Licence

- **The paper's own text** is **CC BY 4.0** (author decision, 2026-10-15), as is the subset's **content** — the
  fixture and the paper's material.
- **Released artifacts are source-available under PolyForm Noncommercial 1.0.0** (instruments in
  `strategy/licence-templates/RELEASED-PIECE/`), with a **paid commercial licence offered by the author** for
  commercial use. The decision is recorded; the subset's code is no longer "undecided".
- **The main repository stays fully proprietary and closed.** The source repository's own `LICENSE` governs it
  and is **not** restated, copied, or resolved here.
