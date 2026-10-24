# UVERPAPERS — verifier: paper pipeline claims (A/B/C)

**Role:** independent verifier. Did not author any of the artifacts below.
**Hard bound:** 25 tool calls. Stop early if a claim cannot be settled.
**Read-only:** `/home/zer0null/Duval` untouched (no git commands against it).

## Claims under test

- **A** `tools/package/md2tex.py` is the single converter for both papers, registry-driven, and
  regenerates each shipped `main.tex` byte-for-byte. Shipped digests claimed:
  - `papers/encoder-crossover-190/submission/main.tex` sha256 `4efa575442b2878037d625bc604e2ae7aab7e1faf9d9515bd9c9747ebf28885a`
  - `papers/gated-read-batching/submission/main.tex` sha256 `a5d32dd7da1a2b9b920ffb9cb272749339edd954f9a1e63b11bb59df6d8886b4`
  Also: does the citation-integrity guard actually **fail**, or only print?
- **B** `MANUSCRIPT.md`: `UEXP`→`B` ×7, `UEXP2`→`B2` ×1, `UREFS`→`our` ×1; no internal label survives
  anywhere in manuscript or shipped LaTeX; no published number changed. Claimed evidence: numeric-literal
  multiset 819 tokens sha256 `a0762fd5a407cc75053bfe74aa7d9c8066da3913e1a703eec1bff048b60f15c0`,
  digit-run delta `{'190': 5, '2': 10}`, citation bookkeeping 13 `\bibitem` / 23 `\cite` / 13 keys /
  0 uncited / 0 unresolved.
- **C** 16 de-namings removed internal record names from the shipped LaTeX, while
  `docs/DECIDER_STACK_DECISION.md` was deliberately **kept** (14 occurrences) because it is the citation
  source for `source_decider_stack_2026`. Records that *should* still be named:
  `results/REPORT.md`, `second-labeller/EVIDENCE.md`, `PREREGISTRATION.md`, `README.md` — claimed present
  in `scratch/uneutral10/package` (29 files). Also: does `RELATED_WORK_NOTES.md` appear twice?
  (a prior unit could not reproduce it).

## Method

- All mutation/regen on **copies** under `scratch/uverpapers/`; touched files restored and proven.
- Red→green mandatory for ≥1 check.
- `pytest` run only with `--noconftest` (tests/conftest.py:19 imports an absent module).
- Verdict goes to `orchestration/handoffs/UVERPAPERS.json`; report to
  `strategy/VERIFICATION_REPORT_PAPERS.md`.

**Write paths:** `strategy/VERIFICATION_REPORT_PAPERS.md`, `orchestration/units/UVERPAPERS.md`,
`orchestration/handoffs/UVERPAPERS.json`, `scratch/uverpapers/**`.

**TASK AS OF THIS BLOCK:** card persisted; verification not yet begun.
