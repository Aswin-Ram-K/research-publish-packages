# ULEDGER1 — de-duplicate the volatility out of PUBLICATION_CHECKLIST.md

**Status:** done (card skeleton written first, per unit contract)
**Bound:** 15 work tool calls; used 14 for the work + this report-back write.
**Write paths:** `strategy/PUBLICATION_CHECKLIST.md`, `orchestration/units/ULEDGER1.md`,
`orchestration/handoffs/ULEDGER1.json`, `scratch/uledger1/**` (scratch unused).

## Result
The checklist now carries **sequence and status only**. Artifact sizes and digests are not restated
anywhere in current text: §2.1 names the two owners (`submission-kit/README.md` for the upload files,
each package's `MANIFEST.json` for the released trees) and says why this file abstains; §2.2 is a
path-only table; §2.3 is the dated audit trail of everything removed.

## What was collapsed
| | old | new |
|---|---|---|
| §2 inventory | lines 17–219 | lines 17–175 (§2.1/§2.2/§2.3) |
| §3 steps | lines 222–295 | lines 177–252 |
| §4 blockers | lines 297–310 | lines 254–267 |
| §5 numbering | 312–326 | 269–283 |

* 142 path rows, each with bytes + sha256 = **284 values removed**.
* 3 `Release payload: N files, X bytes` byte totals removed (member counts 31 / 10 / 12 kept — measured).
* 37 sizes + 9 abbreviated digests removed from §3 evidence cells; 6 sizes + 10 abbreviated digests
  from §4.9/§4.10. **349 values total** (counting the copies, not distinct paths).
* Kept: 3 concept DOIs (19 occurrences), Zenodo record ids `23483304` / `23485733` / `23483315`,
  archive member counts, mtimes, every step, every blocker, every dated note.

## Measured findings
* **22 stale sizes** vs disk: 20 §2 rows plus two payload totals (replay 1,313,090 → 1,313,443 B;
  gated 2,383,883 → 2,384,398 B). Encoder payload (31 files / 856,779 B) re-measured exactly.
* **`:191`** named `papers/gated-read-batching/released/README.md` and claimed 1,340 B. Measured
  **14,170 B**, sha256 `a453041e21c7a4cda37e5ce5fbb718ec9ea92c28c94fc762dbddda402663a39d` — byte-identical
  to the archive member `README.md` the same section already listed. The row described the file it names;
  1,340 was a stale measurement of an earlier revision. No 1,340-byte file exists anywhere in that package
  (searched), so no third file could have been meant.
* Encoder and replay payload trees are **not extracted on disk** (only the `.tar.gz`); encoder's removal is
  documented in `released/SUPERSEDED-UNPACKED-TREE.md`, replay's is not. The old §2 payload tables listed 41
  paths that no longer exist as paths; §2.2 names the archive and its `MANIFEST.json` instead.

## Verified after edit
* §3 steps: 21 rows (7 × 3 papers), lines 183–217.
* §4 blockers: 4.1–4.10 at lines 258–267, none removed or softened; 4.9/4.10 now point at §2.3.
* No size or digest survives outside §2.3 except the two measurements §4.2 needs (line 259).
