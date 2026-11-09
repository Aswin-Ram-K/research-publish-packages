# FIT-GAP-CENSUS — the 21 appended rows, corrected and sourced

**Unit:** `C8-CENSUS-FIX-V2` · **Inputs:** `experiments/miss-law/rows.jsonl`, `experiments/miss-law/law_fit.json`,
`experiments/miss-law/agg.py` · offline, zero live requests, no board mutation.

**Why a new file rather than a rewrite.** The path the original unit named,
`experiments/miss-law/FIT-GAP.md`, is now a **tombstone** — it withdraws itself, forbids citation of
everything below its line 6, and names `experiments/miss-law/FIT-GAP-V2.md` as superseder, stating "no
fourth is attempted" (`experiments/miss-law/FIT-GAP.md:1-6`, sha256 `70bd26aaf7c1b74d1aa3434ed555373b88ffbf18d736d1e96dcb900c06a3c56c`).
Overwriting it would destroy that withdrawal ruling. `FIT-GAP-V2.md` partitions all 774 rows and re-adjudicates
the old counts, but it carries **no 21-row tail census**. This file supplies exactly that missing census and
changes nothing it supersedes. It is cited as the census; it is **not** a resurrection of `FIT-GAP.md`.

## 1. Denominator

| claim | value | source |
|---|---:|---|
| `rows.jsonl` line count | **774** | `experiments/miss-law/rows.jsonl` (whole file; `wc -l`) |
| `law_fit.json:n_rows` | **753** | `experiments/miss-law/law_fit.json:2` |
| `role == measure` | **387** | `experiments/miss-law/rows.jsonl` |
| `role == prime` | **383** | `experiments/miss-law/rows.jsonl` |
| control rows (`warm1`+`warm2`+`cold1`+`cold2`) | **4** | `experiments/miss-law/rows.jsonl` |
| rows carrying `L_app` | **387** | `experiments/miss-law/rows.jsonl` |
| `measure` rows lacking `L_app` | **0** | `experiments/miss-law/rows.jsonl` |
| appended tail (rows 754–774) | **21** | `experiments/miss-law/rows.jsonl:754` … `:774` |

`n_rows` is **not** a coverage count. It is a runtime file length,
`report = {"n_rows": len(rows)}` at `experiments/miss-law/agg.py:63`, serialised at
`experiments/miss-law/agg.py:142-143`. The fit therefore covers its own population exhaustively
(`387 measure` rows = `387` carrying `L_app`, so `387/387`), and 774 − 753 = 21 rows are appended *after*
the snapshot was written. The fit's coverage is unaffected; the **key** is misleading.

## 2. The 21 appended rows — one correction per row

Every row below is sourced to the exact line it was read from. `n_payload` is quoted from the row itself.
`phase`/`server`/`role` are the row's own fields. The correction for all 21 is the same class,
**SNAPSHOT-LAG** (not `DEFECT`): the row post-dates the aggregation snapshot; the row is sound, the
*artefact pair* (`law_fit.json` vs `rows.jsonl`) is stale.

| # | cell | server | phase | role | n_payload | source | correction |
|---:|---|---|---|---|---:|---|---|
| 754 | `res-8056-n64` | `vllm` | `residue` | `prime` | 64 | `experiments/miss-law/rows.jsonl:754` | SNAPSHOT-LAG — prime half of the appended residue pair |
| 755 | `res-8056-n64` | `vllm` | `residue` | `measure` | 64 | `experiments/miss-law/rows.jsonl:755` | SNAPSHOT-LAG — post-dates fit; part of the −5 `vllm` delta |
| 756 | `res-8056-n512` | `vllm` | `residue` | `prime` | 512 | `experiments/miss-law/rows.jsonl:756` | SNAPSHOT-LAG — prime half of the appended residue pair |
| 757 | `res-8056-n512` | `vllm` | `residue` | `measure` | 512 | `experiments/miss-law/rows.jsonl:757` | SNAPSHOT-LAG — post-dates fit; part of the −5 `vllm` delta |
| 758 | `res-8056-n512` | `vllm` | `residue` | `prime` | 512 | `experiments/miss-law/rows.jsonl:758` | SNAPSHOT-LAG — prime half of the appended residue pair |
| 759 | `res-8056-n512` | `vllm` | `residue` | `measure` | 512 | `experiments/miss-law/rows.jsonl:759` | SNAPSHOT-LAG — post-dates fit; part of the −5 `vllm` delta |
| 760 | `res-8056-n1056` | `vllm` | `residue` | `prime` | 1056 | `experiments/miss-law/rows.jsonl:760` | SNAPSHOT-LAG — prime half of the appended residue pair |
| 761 | `res-8056-n1056` | `vllm` | `residue` | `measure` | 1056 | `experiments/miss-law/rows.jsonl:761` | SNAPSHOT-LAG — post-dates fit; part of the −5 `vllm` delta |
| 762 | `res-8056-n1056` | `vllm` | `residue` | `prime` | 1056 | `experiments/miss-law/rows.jsonl:762` | SNAPSHOT-LAG — prime half of the appended residue pair |
| 763 | `res-8056-n1056` | `vllm` | `residue` | `measure` | 1056 | `experiments/miss-law/rows.jsonl:763` | SNAPSHOT-LAG — post-dates fit; part of the −5 `vllm` delta |
| 764 | `pos-2048` | `sglang` | `position` | `measure` | 1 | `experiments/miss-law/rows.jsonl:764` | SNAPSHOT-LAG — position control appended after fit |
| 765 | `pos-2049` | `sglang` | `position` | `measure` | 1 | `experiments/miss-law/rows.jsonl:765` | SNAPSHOT-LAG — position control appended after fit |
| 766 | `pos-4096` | `sglang` | `position` | `measure` | 1 | `experiments/miss-law/rows.jsonl:766` | SNAPSHOT-LAG — position control appended after fit |
| 767 | `pos-4097` | `sglang` | `position` | `measure` | 1 | `experiments/miss-law/rows.jsonl:767` | SNAPSHOT-LAG — position control appended after fit |
| 768 | `pos-6144` | `sglang` | `position` | `measure` | 1 | `experiments/miss-law/rows.jsonl:768` | SNAPSHOT-LAG — position control appended after fit |
| 769 | `pos-6145` | `sglang` | `position` | `measure` | 1 | `experiments/miss-law/rows.jsonl:769` | SNAPSHOT-LAG — position control appended after fit |
| 770 | `pos-7936` | `sglang` | `position` | `measure` | 1 | `experiments/miss-law/rows.jsonl:770` | SNAPSHOT-LAG — position control appended after fit |
| 771 | `pos-7937` | `sglang` | `position` | `measure` | 1 | `experiments/miss-law/rows.jsonl:771` | SNAPSHOT-LAG — position control appended after fit |
| 772 | `pos-7681` | `sglang` | `position` | `measure` | 1 | `experiments/miss-law/rows.jsonl:772` | SNAPSHOT-LAG — position control appended after fit |
| 773 | `pos-8000` | `sglang` | `position` | `measure` | 1 | `experiments/miss-law/rows.jsonl:773` | SNAPSHOT-LAG — position control appended after fit |
| 774 | `pos-8001` | `sglang` | `position` | `measure` | 1 | `experiments/miss-law/rows.jsonl:774` | SNAPSHOT-LAG — position control appended after fit |

## 3. Corrected composition (derived from §2, not copied)

| group | n | server | role | `n_payload` |
|---|---:|---|---|---|
| `phase == residue` | **10** | `vllm` | **5 `prime` + 5 `measure`** | 64 ×2 · 512 ×4 · 1056 ×4 |
| `phase == position` | **11** | `sglang` | `measure` | 1 ×11 |
| `role != measure` | **5** | — | **`prime`** | — |

This is the correction the withdrawn file got wrong: it profiled all ten residue rows as `measure`
(`experiments/miss-law/FIT-GAP.md:29`, withdrawn) and read `role != measure` as **0**. Measured, the
residue tail is **half prime** and `role != measure` is **5**. No `residue` key exists on any tail row, and
`error` is `null` on all 21.

## 4. The non-circular test, re-run

`n_residue_rows` is `len(rs_res)` where `rs_res` is drawn from `rs_all = meas(rows, server)`
(`experiments/miss-law/agg.py:67,69,107`) and `meas()` keeps `role == "measure"` with no error
(`experiments/miss-law/agg.py:27-35`). So the declared residue count is a **measure-only** residue count, and
the prediction is `onfile − intail == n_residue_rows`:

| server | declared | on file | in tail | onfile − intail | match |
|---|---:|---:|---:|---:|---|
| `sglang` | 232 | 232 | 0 | **232** | **yes** |
| `vllm` | 73 | 78 | 5 | **73** | **yes** |

Declared values: `experiments/miss-law/law_fit.json:43` (`sglang.n_residue_rows: 232`) and
`experiments/miss-law/law_fit.json:152` (`vllm.n_residue_rows: 73`). On-file values are recomputed from
`experiments/miss-law/rows.jsonl` under the same predicate. The exactly-five row `vllm` shortfall **is** the
five `vllm` residue `measure` rows of the tail; `sglang`'s residue tail is zero because its 11 appended rows
are `position`, a different phase. The test can fail and does not.

## 5. Ruling

- **OUTLIER 0** and **LAW GAP 0** retained: no tail row is an avalanche turn, all 16 tail `measure` rows sit
  inside `meas()`, and the residue clause's null-cache silence is the priming cell, not a gap.
- **`DEFECT` 21 → `SNAPSHOT-LAG` 21**: a bookkeeping fact about when the fit was aggregated, not a
  contradiction in the law.
- **C8 consequence: NARROWED, not closed.** The surviving item is a documentation defect in the artefact pair
  — a runtime-length key published as if it were a coverage count, and `experiments/miss-law/LAW.md:3`
  recording `764` rows (`753 + 11` position controls) where the file holds **774**, omitting the ten `vllm`
  residue rows of this tail.

## 6. Reproduce every number

```bash
wc -l experiments/miss-law/rows.jsonl                                  # 774
python3 -c "import json;print(json.load(open('experiments/miss-law/law_fit.json'))['n_rows'])"  # 753
python3 experiments/ptr-engine/tools/c8_census_check.py               # exit 0 = every citation resolves
```

The checker `experiments/ptr-engine/tools/c8_census_check.py` parses §2 and §1, re-reads every cited line of
`rows.jsonl`, and exits non-zero on any unresolved citation, field mismatch, wrong row count, or drifted total.
It is the gate on this document, not a spot-check.
