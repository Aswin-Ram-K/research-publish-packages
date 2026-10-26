# Availability — `gated-read-batching`

> **Provenance of this paper, stated plainly.** This note rests on **one bounded measurement run**,
> dated **2026-09-30** (`released/gated-read-batching-released/results/GATED_READ_2026.md:3-9`, which
> also records the run branch `measure/gated-read`). It **carries no experiment number**: the string
> `EXP#` appears **zero** times in `MANUSCRIPT.md`, `CLAIMS.md`, `GAPS.md` and `REFS.md` (measured with
> `grep -c`). Where the companion notes in this workspace carry `EXP#7` and `EXP#12`, this one
> deliberately carries nothing — do not infer an identifier that does not exist. Its scope is the run's
> own recorded scope, one **decision model** (`deepseek-v4-flash`), one **corpus** (90 files) and one
> **task family** — locate a value stated in a file — over 20 tasks and 1,800 (task, file) pairs per
> configuration (`MANUSCRIPT.md` §6, "Scope of the measurement"; `MANUSCRIPT.md` §3.4).

**One paragraph for a reviewer.** This note is public under **CC BY 4.0**. It ships a **data-and-verification
deposit**, not a reproduction package: the **9,260 per-decision rows** the published numbers rest on, the run
report and run summary *as records*, the literature-provenance record, and a standard-library checker that
**re-derives every headline number from the shipped bytes**. **Withheld by policy:** the **harness**
(`tools/gated-read/bench.py`), the **task fixture** (`tools/gated-read/tasks.json`), the **90-file corpus**, the
**model service** that produced the decisions, the batching prompt template and parsing rules, and the
staged-extraction arm the note scopes out. A reader therefore **cannot regenerate a gate input, cannot rebuild
the gold labels, and cannot re-run the measurement**; what ships **verifies the recorded results, it does not
reproduce them**. The released artifacts are **source-available under PolyForm Noncommercial 1.0.0** with a
**paid commercial licence offered by the author**; the main project repository stays **proprietary and closed**.
**The deposit carries a persistent identifier: concept DOI `10.5281/zenodo.23483314`** — see "Persistent identifier" below.

## What is released

The single release artifact is `released/gated-read-batching-released.tar.gz` — **128,902 bytes**, sha256
`e2ceb554f319cb898221c655f1b64ba0e8a022e4e0ad9ffc3fda5fbecd464b24`, md5 `a7e81bf7c8ebe49da83e869a002be1b2`. Extracted it holds **12 files, 2,384,398
bytes**, under one top-level directory `gated-read-batching-released/`:

| Path in the archive | Bytes | What it is |
|---|---|---|
| `data/gated-read-rows.jsonl` | 2,267,742 | The **9,260 per-decision rows** the recomputation reads (9,260 lines). sha256 `184ab747e87f7d127005ce08316dcde640ae93e5278bb1bd57bf353e23d9c44f` |
| `results/gated-read-summary.json` | 4,278 | The aggregates the harness wrote (carries `prompt_tok_total: null` for `gate16_none` / `gate90_none` — `MANUSCRIPT.md` §6) |
| `results/GATED_READ_2026.md` | 23,591 | The **run report**, 340 lines, dated 2026-09-30 |
| `results/GATED_READ_PROVENANCE.md` | 31,562 | Literature provenance and the fetched URLs, 275 lines |
| `verify/recompute-claims.py` | 12,493 | **Re-derives every headline number from `data/` alone**; Python standard library only; no network, no GPU |
| `README.md` | 14,170 | Package documentation, including the recorded validity limitation |
| `README_DEPOSIT.md` | 10,105 | Deposit-level front matter (deposit metadata, not package content) |
| `LICENSE` | 6,601 | PolyForm Noncommercial License 1.0.0, unmodified, with the required notice |
| `COMMERCIAL.md` | 3,520 | The paid-commercial-licence terms and how to request one |
| `CONTRIBUTING.md` | 3,547 | Contribution terms |
| `CITATION.cff` | 2,139 | Deposit-level citation (deposit metadata, not package content) |
| `MANIFEST.json` | 4,650 | Integrity manifest: sha256 and size for the other 11 files |

**Rebuilt 2026-10-19 for the concept-DOI back-fill.** `CITATION.cff` and `README_DEPOSIT.md` now carry
the concept DOI, so the archive bytes moved; the superseded release was **128,559 bytes**, sha256
`1e3b5781463772fecd8562cd2be20bed14488fa13761d5c8797fe7826f38827c`, md5 `5c0db7c9afedf5d47747c70e03e8a136` — that is the file published as version record `23483315`, kept here as
dated history. No data file, row, count or published number changed in the rebuild.

**The manifest was checked first-hand, not quoted.** Extracting the archive and re-hashing every listed path
returns `MANIFEST checked: 11 mismatches: none`. `MANIFEST.json` does not enumerate itself (a self-referential
sha256 is impossible), so `counts.files = 12` includes it while `counts.bytes_total = 2,379,748` excludes its
4,650 bytes; 2,379,748 + 4,650 = 2,384,398, the extracted tree size. `README_DEPOSIT.md` states the same
convention explicitly rather than leaving the 11-vs-12 discrepancy to be read as an error.

**The shipped rows are not byte-identical to the source tree they were cut from.** Six `answer` values (four R5
trace identifiers, two uppercase target-project sentinels) and one prose word in the run report were replaced
**at equal length** by neutral identifiers, so every byte count, line count and published number is unchanged.
The row-level rename is recorded as `GAPS.md` G-23 (now closed); the digests and superseded values are in
`CLAIMS.md` claim R.

## What is withheld, and why

| Withheld | Why |
|---|---|
| **The harness** (`tools/gated-read/bench.py`) and the **task fixture** (`tools/gated-read/tasks.json`) | the deposit ships the rows those tools produced and the checker that reads them; the instrument itself is withheld (`README_DEPOSIT.md`, "What this is not") |
| **The 90-file corpus** | not shipped in any form; the fixture lists 90 paths with **no size or hash fields**, so the fixture is not pinned by digest either |
| **The gate's inputs: batching prompt template, delimiter/index scheme, parsing rules** | implementation, withheld by design — `GAPS.md` G-05 states the protocol is described in the run report but the exact call is not reproducible from public material |
| **The decision-model service and the reasoner** (`deepseek-v4-flash` serving the gate; the reasoner is not central) | a hosted service was used; no model was trained, fine-tuned or shipped for this paper (`MANUSCRIPT.md`, "Compute and resources"). Model identity is stated because without it the numbers are not interpretable (`GAPS.md` G-20) |
| **The staged-extraction harness and the injection-exposure arm** | the end-to-end arm is **scoped out of the note** (`MANUSCRIPT.md` §6, "The removed arm"): at n = 20 per arm the accuracy differences are not statistically separable (sign tests p ≥ 0.219) and that harness "is not part of the design published here" |
| **The internal working records** — the claim trace, the gap register, the reference notes, the disclosure log | author-side working documents, not part of the release; the note cites them in its internal record only |

**Why the withdrawn "1.83 MB" is not recoverable from the release.** The run report's recorded corpus size is
withdrawn as unsupported: the fixture carries no sizes, and there is no byte record for the 2026-09-30 run date.
The note therefore states corpus size as a two-snapshot measurement — 2,426,190 B in the pinned snapshot tree,
2,886,664 B in the live tree (`MANUSCRIPT.md` §3.2, §6) — and those two numbers are **stated from the run report
only**; the checker does not recompute them, because neither the corpus nor `tasks.json` is present.

## What the released material lets a reader do — and what it does not

**It does.** From the extracted top directory, `python3 verify/recompute-claims.py` runs with the standard
library only and re-derives every headline number **from the shipped bytes**. Measured on the extracted archive
in this workspace: **`checks: 49   passed: 49   failed: 0`, `VERDICT: PASS -- every published number reproduced
from the shipped bytes`**, exit status **0**. It reports the per-`mode` `ptok`/`ctok` sums, the `tp`/`fp`/`fn`
counts, precision/recall/F1, admitted pairs, tokens per decision, row and error counts, the stored 120-pair gold
count, the 6.7 % base rate, and the sha256 of the shipped rows. Any `[FAIL]` makes it exit `1` and name the
claim that failed. A reader can therefore **confirm that the numbers printed in the paper are the numbers those
records imply**, and can recompute them independently.

**It does not.** This is a **verification** capability, not a **reproduction** one:

- **The measurement cannot be re-run.** No harness, no fixture, no corpus, no model service. Nothing in the
  archive can produce another gate decision.
- **The gold labels cannot be rebuilt.** The paper's §3.2 describes the harness recomputing gold from the bytes
  on every run; the raw record does not support that. Re-deriving the gold set from corpus content under the
  rule the fixture states yields **127 gold pairs in the pinned snapshot tree and 130 in the live tree, against
  120 stored**; 10 of the 12 stored-only pairs are a single file, `AGENTS.md`. The **120-pair gold count**, the
  **6.7 % base rate** and **every precision, recall, F1 and accuracy figure** are therefore obtained from
  *recorded verdicts*, not reproduced from the fixture. The batching comparison is not endangered — all five
  configurations share the same stored labels — but the numbers describe label-consistent behaviour rather than
  an independently reproducible fixture (`GAPS.md` G-25; package `README.md`).
- **Two checks are labelled `RUN-REPORT-ONLY` and are not manuscript claims**: the 15.279× selfselect/stage_route
  prompt-token ratio and the exposure `0/20` for `stage_route`. §6 scopes that arm out of the note; they are
  re-derived because the package was contracted to, and **a reader must not read them as published numbers**.
- **Corpus-scale and literature numbers are not recomputed** — 90 files and the two snapshot byte counts come
  from the run report, and the batching literature is not in the package.

**The distinction in one line:** a reader can re-derive each published number *from stored records* and cannot
re-run the measurement, re-render an input, or regenerate a single decision. Verification yes; reproduction no.

## Licence

- **The paper's own text** is **CC BY 4.0** (author decision, 2026-10-15).
- **The released artifacts** — everything in the archive — are **source-available under the PolyForm
  Noncommercial License 1.0.0** (`LICENSE`, unmodified, with the required notice "Copyright 2026
  Aswin-Ram-K"; `CITATION.cff` declares `license: PolyForm-Noncommercial-1.0.0`), with a **paid commercial
  licence offered directly by the author** (`COMMERCIAL.md`). The noncommercial licence covers no commercial use
  and grants no commercial right; `COMMERCIAL.md` states that this follows from the scope of the grant and its
  `No Other Rights` clause, and labels that reading as an inference from those clauses rather than as a quoted
  prohibition.
- **The main project repository stays fully proprietary and closed.** Nothing in the deposit is a grant of rights
  in it, and the terms grant **no rights in the withheld harness**.

## Persistent identifier

**Persistent identifier: concept DOI `10.5281/zenodo.23483314`.** The deposit is published on Zenodo under that DOI: version
record `23483315`, published 2026-10-19, resource type `dataset`, licence `polyform-noncommercial-1.0.0`,
language unset, and the shipped file `gated-read-batching-released.tar.gz` is the file that record serves.
The **concept** DOI is cited deliberately: it always resolves to the latest version of this deposit, whereas a
version DOI dies at the next version. `CITATION.cff` carries the `doi` field with that concept DOI, and
`README_DEPOSIT.md` states the same identifier.

**Superseded wording, dated 2026-10-19 and kept as dated history.** Until the record was published this
section read: *"No DOI has been minted for this deposit, and none is claimed here. `CITATION.cff` carries no
`doi` field by design — its own comment records that the field is omitted 'rather than left as a placeholder
so nothing here names an identifier that does not resolve', and that Zenodo assigns one on publication and the
author adds it there afterwards. `README_DEPOSIT.md` states the same. A DOI will be added when the deposit is
published; this document does not promise, predict or guess the identifier."* Those statements were true when
written and are now false; they are retained rather than overwritten, as this workspace keeps superseded
wording as dated history.
