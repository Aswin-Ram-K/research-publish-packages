# Research Publish Packages

The author's **public code + paper store**: one directory per research package, each carrying its manuscript,
its sanitised code and its evaluation evidence together.

**Status: private for now.** Nothing here is announced or published yet; this is the repository being prepared
as the public-facing one.

This repository is **separate from, and unrelated to, the private working repository**. It has a **fresh
history**: no commit, blob or branch is carried over from anywhere, so its history cannot be walked back to
private work.

## Packages

| package | what it is | licence |
|---|---|---|
| [`packages/exp12-encoder-crossover/`](packages/exp12-encoder-crossover/) | EXP#12 / paper #3 — a fine-tuned small-encoder head measured against a fine-tuned 4B generative decider on a sealed typed-single-label decision fixture of 190 cases, with its majority-class and shuffled-label controls, its train↔fixture leak criterion, its frozen pre-registration and its second-labeller evidence. | code **PolyForm NC 1.0.0** · paper text **CC BY 4.0** |

## What each package contains

Each package carries its own data, evidence and verification tools, so a reader can tell a claim from its
evidence from the instruments that produced it:

- **`fixture/`** — the sealed decision instrument (`fixture-190.json`), its case schema and the
  fixture-export source.
- **`results/`** — the evaluation evidence: per-arm outputs, baselines, the report and the defect evidence.
- **`second-labeller/`** — the independent re-labelling: blinded cases, labels, metrics, run record,
  disagreement ledger and evidence write-up.
- **`verify/`** — `recompute-claims.py`, which recomputes every claim number from the bytes in this package.
- **`preregistration/`** — the frozen pre-registration.

This package is **data + verification tools only**: the harness that produced the results is deliberately
withheld. `MANIFEST.json` records the package's own file set and digests.

## What is deliberately NOT here

- **The private implementation.** No kernel, broker, scope or layer source; no private branch or leak commit
  identifiers; no absolute paths from the private side. What ships is the sanitised data and verification
  surface, never the as-audited original and never the harness.
- **Process and audit-trail documents.** Internal sanitisation/disclosure reports, licence analyses, change
  logs, verifier-correction notes, exclusion inventories and commercial-in-confidence inventories are excluded
  on purpose: they name the private repository and are internal working paper, not scholarly output.
- **Withheld fixture fields.** Per-case review rationales, the namespace value on each case, and the fixture's
  mechanism comments are withheld — keys kept, values emptied — so the schema and every measured number are
  unchanged. The residuals that redaction cannot remove are reported, with file and line, by the package's
  exclusion gate; see [the package README](packages/exp12-encoder-crossover/README.md).
- **Working directories.** No file from `journal/`, `jobs/`, `dockets/`, `state/`, `orchestration/` or
  `strategy/` is included. `journal/` in particular is **excluded pending an explicit author decision**.
- **Any history, any remote, any push.** Fresh history; no remote is configured.

