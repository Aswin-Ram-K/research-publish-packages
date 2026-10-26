# C8-CENSUS-FIX — corrected composition census of the C8 21-row tail

**Purpose (one).** Correct the composition table and class name in `experiments/miss-law/FIT-GAP.md`. Bound: 10 tool calls; one file corrected.
**Write paths:** `experiments/miss-law/FIT-GAP.md`, `orchestration/units/C8-CENSUS-FIX.md`, `orchestration/handoffs/C8-CENSUS-FIX.json`.

**What was wrong.** §3 profiled the 10 `residue` rows as "all `measure`, `sglang`, `n_payload == 1`" — the *position* group's profile copied onto the residue group — and its `role != measure` line read **0**.

**Corrected composition (last 21 lines of `rows.jsonl`, recomputed per row):**

| group | n | server | role | `n_payload` |
|---|---:|---|---|---|
| `phase == residue` | 10 | `vllm` | **5 `prime` + 5 `measure`** | 64 ×2 · 512 ×4 · 1056 ×4 |
| `phase == position` | 11 | `sglang` | `measure` | 1 |
| `role != measure` | **5** | — | **`prime`** | — |

No `residue` key exists on any tail row; `error: null` on all 21. Counts kept unmodified: 774 = 383 `prime` + 387 `measure` + 4 controls; `n_rows` 753; the 387/387 fit-completeness check. The −5 `vllm` `n_residue_rows` delta (73 snapshot vs 78 in file) *is* the 5 `vllm` residue rows of the lag.

**Class.** `DEFECT` → **SNAPSHOT-LAG** (21 rows, unchanged). OUTLIER 0 / LAW GAP 0 retained.
**C8 consequence.** **NARROWED** (not closed): a snapshot lag is a bookkeeping fact about when the fit was aggregated, not a contradiction in the law — the surviving item is a documentation defect in the artefact pair.

**Command (reproducible, from workspace root):**

```bash
python3 -c "
import json,collections
rows=[json.loads(l) for l in open('experiments/miss-law/rows.jsonl') if l.strip()]
k=lambda r:(r.get('phase'),r.get('server'),r.get('role'),str(r.get('n_payload')))
print(len(rows),dict(collections.Counter(r.get('role') for r in rows[-21:])))
for a,b in sorted(collections.Counter(k(r) for r in rows[-21:]).items(),key=lambda x:-x[1]): print(b,a)"
```

**Assumption recorded.** The unit brief supplies `residue: None`; no `residue` key exists on the tail rows, so the table renders it literally as `None` (harvested-from-`r.get('residue')`) without coalescing it to the JSON `null`.
