# Research Extractor — context-cache study (v0.1)

This is a **sanitised, self-contained copy of the publishable parts** of a private research
workspace. It carries the context-cache experiments, the paper source, the tests, the
encoder-crossover reproduction package (already sanitised upstream), curated operations docs and
the configuration needed to read the study.

## Start here

| Path | What it is |
|---|---|
| `papers/context-cache/` | The live manuscript and its figures/data |
| `src/resextract/` | The extraction/comparison implementation |
| `tests/` | The test suite (`pytest`) |
| `experiments/context-cache/` | Per-cell measurement outputs (see `README.md` inside) |
| `repro/encoder-crossover-190-SANITISED/` | Self-contained reproduction package |
| `docs/` | Operations, acceptance and serving-option documentation |
| `MANIFEST.json` | sha256 for **every** shipped file, plus the sanitisation record |
| `NOTICE` | What was changed on the way out of the private workspace, and why |

Internal hosts and absolute paths were replaced by the literal placeholder `<workspace>` /
`serving-host`; `MANIFEST.json` records the per-file replacement counts.

## Licence

> This project is **source-available, not open source**. It is released under the **PolyForm
> Noncommercial License 1.0.0** — free to use, study, modify and redistribute for personal, hobby,
> research and other **noncommercial** purposes. **Any commercial use requires a paid commercial
> licence, obtained through the published repository's own issue tracker at
> <https://github.com/Aswin-Ram-K/research-publish-packages>** (see `COMMERCIAL.md`). No personal
> address is published. The Noncommercial licence
> does not cover commercial use; the reason is the licence's own qualifier, *"without any anticipated
> commercial application"*, read with its exhaustive list of permitted purposes — a business
> evaluating the software in order to buy falls outside all of them. That is an **inference from the
> quoted clause**, not a clause that names "evaluation": so there is no free commercial evaluation.
> **Academic, public-research, public-health, public-safety, environmental and government
> institutions are permitted users of this same licence**, not prospective licensees — it permits use
> by "any charitable organization, educational institution, public research organization, public
> safety or health organization, environmental protection organization, or government institution …
> regardless of the source of funding or obligations resulting from the funding." **Forks and
> published noncommercial modifications are welcome**; only *ideas* are considered for integration —
> code contributions and patches are not accepted or merged (`CONTRIBUTING.md`). Notice line, already
> filled: `Required Notice: Copyright 2026 Aswin-Ram-K`.

See [`LICENSE`](LICENSE) (PolyForm Noncommercial License 1.0.0),
[`COMMERCIAL.md`](COMMERCIAL.md) and [`CONTRIBUTING.md`](CONTRIBUTING.md).
Permission for the licence terms **supersedes** anything contradictory elsewhere in this tree.
