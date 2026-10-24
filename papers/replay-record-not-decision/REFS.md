# REFS.md — the eight references added to paper #2, and exactly what was verified

**Rule enforced.** No citation was written from memory. Every entry in `REFERENCES.bib` below was
verified on **2026-10-16** by fetching the **arXiv abstract page** named in its `url` field with the
local web tools (one HTTP GET per page). The field taken from each page is named. Anything the page
did not carry (a venue, a page range) is left absent and the entry says so.

| # | key | Title (from page) | Authors (from page) | Venue/year taken from | Verified URL |
|---|---|---|---|---|---|
| 1 | `yuanNondeterminism` | Understanding and Mitigating Numerical Sources of Nondeterminism in LLM Inference | Yuan, Li, Ding, Xie, Li, Zhao, Wan, Shi, Hu, Liu (10) | no venue comment; Year 2025 from submission date 2025-06-11 | https://arxiv.org/abs/2506.09501 |
| 2 | `hendersonDeepRL` | Deep Reinforcement Learning that Matters | Henderson, Islam, Bachman, Pineau, Precup, Meger (6) | AAAI 2018 — from the page's comment field | https://arxiv.org/abs/1709.06560 |
| 3 | `bouthillierVariance` | Accounting for Variance in Machine Learning Benchmarks | Bouthillier et al. (17) | MLSys 2021 — page comment reads "Submitted to MLSys2021" | https://arxiv.org/abs/2103.03098 |
| 4 | `linBatchPrompt` | BatchPrompt: Accomplish more with less | Lin, Diesendruck, Du, Abraham (4) | no venue comment; Year 2023 from 2023-09-01 | https://arxiv.org/abs/2309.00384 |
| 5 | `liuAgentBench` | AgentBench: Evaluating LLMs as Agents | Liu et al. (22) | ICLR 2024 — page comment reads "Published in ICLR 2024" | https://arxiv.org/abs/2308.03688 |
| 6 | `yaoTauBench` | tau-bench: A Benchmark for Tool-Agent-User Interaction in Real-World Domains | Yao, Shinn, Razavi, Narasimhan (4) | no venue comment; Year 2024 from 2024-06-17 | https://arxiv.org/abs/2406.12045 |
| 7 | `dodgeShowYourWork` | Show Your Work: Improved Reporting of Experimental Results | Dodge, Gururangan, Card, Schwartz, Smith (5) | no venue comment; Year 2019 from 2019-09-06 | https://arxiv.org/abs/1909.03004 |
| 8 | `gebruDatasheets` | Datasheets for Datasets | Gebru, Morgenstern, Vecchione, Vaughan, Wallach, Daume III, Crawford (7) | CACM, 2021 — page comment reads "Published in CACM in December, 2021" | https://arxiv.org/abs/1803.09010 |

## Unresolved / deliberately NOT cited

* **arXiv 2605.20173**, the antecedent the manuscript names for *replay divergence*: it is quoted from
  the pre-registration record and was **not** fetched for this unit. It is **not** in
  `REFERENCES.bib`. The manuscript already states this in §1 and §6, and §1.1 repeats that no claim
  rests on it.
* **Pineau et al., NeurIPS 2019 Reproducibility Program report**: the identifier recalled for it was
  tested against the arXiv abstract page and did **not** resolve to that work, so no entry was
  created. A candidate left out rather than a fabricated one.
* **arXiv:2303.09586**: probed as a possible NLP-reproducibility review; the page is an unrelated
  computational-geometry paper, so it was dropped.
* Venues for #1, #4, #6, #7 are **not claimed** because the abstract pages do not carry one; the
  entries are arXiv preprints with a submission year. The bibliography is ASCII throughout; accented
  author names use LaTeX escapes.

## ASCII / format note

`REFERENCES.bib` is ASCII-only. `Ga{\"e}l` (Bouthillier et al.) and `Daum{\'e} III` (Gebru et al.)
are LaTeX escapes, matching `papers/encoder-crossover-190/REFERENCES.bib`. Titles cover protected
acronyms with braces (`{LLM}`, `{AgentBench}`); tau is escaped as `{$\tau$}`.
